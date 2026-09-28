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
        if method != "GET":
            raise AssertionError("only GET is expected")
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
    source = pathlib.Path(__file__).with_name("EvidenceFirewall.py")
    spec = importlib.util.spec_from_file_location("evidence_firewall_contract", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ef = _load_module()
URL_A = "https://example.org/evidence-a"
URL_B = "https://example.org/evidence-b"


class EvidenceFirewallTests(unittest.TestCase):
    def setUp(self):
        self.now = 2_000_000_000
        ef._now_ts = lambda: self.now
        ef.gl.nondet.web.pages = {
            URL_A: (200, "Published audit record with an immutable digest."),
            URL_B: (200, "Release metadata for the same artifact."),
        }
        ef.gl.nondet.output = {
            "sources": [
                {"index": 0, "classification": "CLEAN", "risk_code": "NONE"},
                {"index": 1, "classification": "CLEAN", "risk_code": "NONE"},
            ]
        }
        _VM.mutator = None
        self.contract = ef.EvidenceFirewall()
        self.contract.screens = TreeMap()
        self.contract.receipts = TreeMap()

    def open(self):
        return self.contract.open_screen(
            "Verify a release artifact before an autonomous payout.",
            "Sources must identify the artifact and its published digest.",
            json.dumps([URL_A, URL_B]),
        )

    def test_open_locks_purpose_sources_and_request_hash(self):
        screen_id = self.open()
        record = json.loads(self.contract.get_screen(screen_id))
        self.assertEqual(record["status"], "OPEN")
        self.assertEqual(record["urls"], [URL_A, URL_B])
        self.assertEqual(len(record["request_hash"]), 64)

    def test_clean_sources_are_admissible(self):
        screen_id = self.open()
        receipt = self.contract.evaluate_screen(screen_id)
        self.assertEqual(receipt["decision"], "ADMISSIBLE")
        self.assertTrue(receipt["release_allowed"])
        self.assertEqual(len(receipt["sources"]), 2)
        self.assertEqual(self.contract.get_receipt(screen_id, 1), receipt)
        self.assertEqual(self.contract.get_stats()["admissible"], 1)

    def test_instruction_like_source_is_quarantined(self):
        screen_id = self.open()
        ef.gl.nondet.output["sources"][1] = {
            "index": 1,
            "classification": "INJECTION_RISK",
            "risk_code": "TOOL_CONTROL",
        }
        receipt = self.contract.evaluate_screen(screen_id)
        self.assertEqual(receipt["decision"], "QUARANTINED")
        self.assertFalse(receipt["release_allowed"])

    def test_irrelevant_source_is_out_of_scope(self):
        screen_id = self.open()
        ef.gl.nondet.output["sources"][0] = {
            "index": 0,
            "classification": "OUT_OF_SCOPE",
            "risk_code": "NONE",
        }
        self.assertEqual(
            self.contract.evaluate_screen(screen_id)["decision"],
            "OUT_OF_SCOPE",
        )

    def test_unreadable_is_retryable_then_final(self):
        screen_id = self.open()
        ef.gl.nondet.web.pages[URL_A] = (503, "")
        for expected in ["RETRYABLE", "RETRYABLE", "UNREADABLE_FINAL"]:
            self.contract.evaluate_screen(screen_id)
            record = json.loads(self.contract.get_screen(screen_id))
            self.assertEqual(record["status"], expected)
            self.now += 61

    def test_validator_binds_complete_receipt(self):
        screen_id = self.open()

        def tamper(receipt):
            receipt["sources"][0]["sha256"] = "0" * 64
            return receipt

        _VM.mutator = tamper
        with self.assertRaises(AssertionError):
            self.contract.evaluate_screen(screen_id)

    def test_private_urls_are_rejected(self):
        for url in ["https://localhost/a", "https://127.0.0.1/a", "https://192.168.1.1/a"]:
            with self.assertRaises(UserError):
                self.contract.open_screen(
                    "Verify a public release before autonomous settlement.",
                    "The source must identify the release and digest.",
                    json.dumps([url]),
                )


if __name__ == "__main__":
    unittest.main()
