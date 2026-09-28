import copy
import importlib.util
import json
import pathlib
import sys
import types
import unittest


class UserError(Exception):
    pass


class u64(int):
    pass


class Address(str):
    pass


class TreeMap(dict):
    pass


class _Write:
    def __call__(self, function):
        return function


class _Public:
    write = _Write()

    @staticmethod
    def view(function):
        return function


class _Message:
    sender_address = Address("0x" + ("1" * 40))


class _Return:
    def __init__(self, calldata):
        self.calldata = calldata


class _Response:
    def __init__(self, body, status=200):
        self.status_code = status
        self.body = body.encode("utf-8") if isinstance(body, str) else body


class _Web:
    pages = {}

    def request(self, url, method="GET"):
        status, body = self.pages.get(url, (404, ""))
        return _Response(body, status)


class _Nondet:
    web = _Web()
    output = None

    def exec_prompt(self, _prompt, response_format=None):
        if response_format != "json" or self.output is None:
            raise AssertionError("prompt output was not configured")
        return copy.deepcopy(self.output)


class _VM:
    UserError = UserError
    Return = _Return
    mutator = None

    @staticmethod
    def run_nondet_default(leader_fn, validator_fn):
        candidate = leader_fn()
        if _VM.mutator is not None:
            candidate = _VM.mutator(copy.deepcopy(candidate))
        if not validator_fn(_Return(candidate)):
            raise AssertionError("validator rejected leader receipt")
        return candidate


def _load_module():
    fake = types.ModuleType("genlayer")
    fake.contract = types.SimpleNamespace(Contract=object)
    fake.storage = types.SimpleNamespace(TreeMap=TreeMap)
    fake.public = _Public()
    fake.message = _Message()
    fake.nondet = _Nondet()
    fake.vm = _VM()
    fake_types = types.ModuleType("genlayer.types")
    fake_types.u64 = u64
    fake_types.Address = Address
    fake_types.__all__ = ["u64", "Address"]
    sys.modules["genlayer"] = fake
    sys.modules["genlayer.types"] = fake_types
    source = pathlib.Path(__file__).with_name("ClaimPulse.py")
    spec = importlib.util.spec_from_file_location("claim_pulse_contract", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cp = _load_module()
URL = "https://example.org/current-policy"


class ClaimPulseTests(unittest.TestCase):
    def setUp(self):
        self.now = 2_000_000_000
        cp._now_ts = lambda: self.now
        cp.gl.nondet.web.pages = {URL: (200, "The public policy remains active for all listed regions.")}
        cp.gl.nondet.output = {"decision": "SUPPORTED", "reason_code": "DIRECT_SUPPORT"}
        _VM.mutator = None
        self.contract = cp.ClaimPulse()
        self.contract.claims = TreeMap()
        self.contract.receipts = TreeMap()

    def open(self, lease=600):
        return self.contract.open_claim(
            "The published service policy is active in all listed regions.",
            "The official policy page must directly state the current scope.",
            json.dumps([URL]),
            lease,
        )

    def attest(self):
        claim_id = self.open()
        receipt = self.contract.attest_claim(claim_id)
        return claim_id, receipt

    def test_supported_claim_receives_bounded_usable_lease(self):
        claim_id, receipt = self.attest()
        record = json.loads(self.contract.get_claim(claim_id))
        self.assertEqual(receipt["decision"], "SUPPORTED")
        self.assertEqual(record["status"], "ACTIVE")
        self.assertTrue(record["currently_usable"])
        self.assertEqual(record["valid_until"], self.now + 600)

    def test_unsupported_baseline_is_rejected(self):
        claim_id = self.open()
        cp.gl.nondet.output = {"decision": "UNSUPPORTED", "reason_code": "PARTIAL_SUPPORT"}
        self.contract.attest_claim(claim_id)
        self.assertEqual(json.loads(self.contract.get_claim(claim_id))["status"], "REJECTED")

    def test_expired_claim_is_not_usable_without_mutating_state(self):
        claim_id, _ = self.attest()
        self.now += 601
        self.assertFalse(self.contract.is_usable(claim_id))

    def test_still_valid_recheck_renews_and_chains_receipt(self):
        claim_id, first = self.attest()
        first_hash = cp._hash_text(cp._canonical(first))
        self.now += 61
        cp.gl.nondet.output = {"decision": "STILL_VALID", "reason_code": "EVIDENCE_UNCHANGED"}
        second = self.contract.recheck_claim(claim_id)
        record = json.loads(self.contract.get_claim(claim_id))
        self.assertEqual(second["previous_receipt_hash"], first_hash)
        self.assertEqual(record["revision"], 2)
        self.assertEqual(record["valid_until"], self.now + 600)

    def test_narrowed_scope_invalidates_original_claim(self):
        claim_id, _ = self.attest()
        self.now += 61
        cp.gl.nondet.output = {"decision": "NARROWED", "reason_code": "SCOPE_REDUCED"}
        self.contract.recheck_claim(claim_id)
        record = json.loads(self.contract.get_claim(claim_id))
        self.assertEqual(record["status"], "INVALIDATED")
        self.assertFalse(record["currently_usable"])

    def test_unreadable_baseline_is_bounded(self):
        claim_id = self.open()
        cp.gl.nondet.web.pages[URL] = (503, "")
        for expected in ["BASELINE_RETRYABLE", "BASELINE_RETRYABLE", "UNREADABLE_FINAL"]:
            self.contract.attest_claim(claim_id)
            self.assertEqual(json.loads(self.contract.get_claim(claim_id))["status"], expected)
            self.now += 61

    def test_validator_binds_every_source_digest(self):
        claim_id = self.open()

        def tamper(receipt):
            receipt["sources"][0]["sha256"] = "f" * 64
            return receipt

        _VM.mutator = tamper
        with self.assertRaises(AssertionError):
            self.contract.attest_claim(claim_id)

    def test_private_sources_are_rejected(self):
        with self.assertRaises(UserError):
            self.contract.open_claim(
                "This claim is objectively verifiable from a public source.",
                "The source must directly support every material fact.",
                json.dumps(["https://127.0.0.1/private"]),
                600,
            )


if __name__ == "__main__":
    unittest.main()
