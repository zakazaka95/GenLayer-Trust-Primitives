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
    prompts = []

    def exec_prompt(self, _prompt, response_format=None):
        if response_format != "json" or self.output is None:
            raise AssertionError("prompt output was not configured")
        self.prompts.append(_prompt)
        raw = self.output(_prompt) if callable(self.output) else self.output
        return copy.deepcopy(raw)


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
THREE_URLS = [f"https://example.org/policy-{index}" for index in range(3)]
TAIL_CONTRADICTION = "CURRENT_POLICY_CONTRADICTS_ALL_REGIONS_CLAIM"


class ClaimPulseTests(unittest.TestCase):
    def setUp(self):
        self.now = 2_000_000_000
        cp._now_ts = lambda: self.now
        cp.gl.nondet.web.pages = {URL: (200, "The public policy remains active for all listed regions.")}
        cp.gl.nondet.output = {"decision": "SUPPORTED", "reason_code": "DIRECT_SUPPORT"}
        cp.gl.nondet.prompts = []
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

    def open_three_maximum_sources(self, claim_text=None, evidence_standard=None):
        cp.gl.nondet.web.pages = {
            url: (200, chr(ord("a") + index) * cp.MAX_SOURCE_BYTES)
            for index, url in enumerate(THREE_URLS)
        }
        claim_id = self.contract.open_claim(
            claim_text or "The current policy applies in all of the listed regions.",
            evidence_standard or "Every policy source must support the complete regional scope.",
            json.dumps(THREE_URLS),
            600,
        )
        return claim_id

    def put_contradiction_at_third_source_tail(self):
        self.assertLess(len(TAIL_CONTRADICTION), cp.MAX_SOURCE_BYTES)
        cp.gl.nondet.web.pages[THREE_URLS[2]] = (
            200,
            ("c" * (cp.MAX_SOURCE_BYTES - len(TAIL_CONTRADICTION))) + TAIL_CONTRADICTION,
        )

    def assert_complete_inspection(self, receipt):
        self.assertEqual(receipt["schema"], "claim-pulse-receipt-v2")
        inspection = receipt["inspection"]
        self.assertTrue(inspection["complete"])
        self.assertEqual(inspection["max_prompt_chars"], cp.MAX_TOTAL_PROMPT_CHARS)
        self.assertLessEqual(inspection["prompt_chars"], inspection["max_prompt_chars"])
        self.assertEqual(len(cp.gl.nondet.prompts), 2)
        for prompt in cp.gl.nondet.prompts:
            self.assertEqual(inspection["prompt_chars"], len(prompt))
            self.assertEqual(inspection["prompt_sha256"], cp._hash_text(prompt))
        for source in receipt["sources"]:
            self.assertFalse(source["source_truncated"])
            self.assertFalse(source["prompt_truncated"])
            self.assertFalse(source["truncated"])
            self.assertEqual(source["inspected_bytes"], source["bytes"])
            original_body = cp.gl.nondet.web.pages[source["url"]][1]
            body_text = original_body.decode("utf-8") if isinstance(original_body, bytes) else original_body
            for prompt in cp.gl.nondet.prompts:
                self.assertIn(body_text, prompt)

    def assert_uninspected(self, receipt):
        self.assertEqual(receipt["decision"], "UNREADABLE")
        self.assertFalse(receipt["inspection"]["complete"])
        self.assertEqual(cp.gl.nondet.prompts, [])
        for source in receipt["sources"]:
            self.assertEqual(source["inspected_bytes"], 0)

    def with_prompt_budget(self, maximum, action):
        original = cp.MAX_TOTAL_PROMPT_CHARS
        try:
            cp.MAX_TOTAL_PROMPT_CHARS = maximum
            return action()
        finally:
            cp.MAX_TOTAL_PROMPT_CHARS = original

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

    def test_three_maximum_sources_inspect_third_tail_before_baseline_verdict(self):
        claim_id = self.open_three_maximum_sources()
        self.put_contradiction_at_third_source_tail()
        cp.gl.nondet.output = lambda prompt: (
            {"decision": "UNSUPPORTED", "reason_code": "CONTRADICTED"}
            if TAIL_CONTRADICTION in prompt
            else {"decision": "SUPPORTED", "reason_code": "DIRECT_SUPPORT"}
        )

        receipt = self.contract.attest_claim(claim_id)

        self.assertEqual(receipt["decision"], "UNSUPPORTED")
        self.assertEqual(receipt["sources"][2]["bytes"], 12_000)
        self.assert_complete_inspection(receipt)
        self.assertTrue(all(TAIL_CONTRADICTION in prompt for prompt in cp.gl.nondet.prompts))
        self.assertEqual(json.loads(self.contract.get_claim(claim_id))["status"], "REJECTED")
        self.assertFalse(self.contract.is_usable(claim_id))

    def test_three_maximum_sources_inspect_third_tail_before_recheck_verdict(self):
        claim_id = self.open_three_maximum_sources()
        self.contract.attest_claim(claim_id)
        self.now += 61
        cp.gl.nondet.prompts = []
        self.put_contradiction_at_third_source_tail()
        cp.gl.nondet.output = lambda prompt: (
            {"decision": "CONTRADICTED", "reason_code": "CURRENT_EVIDENCE_CONTRADICTS_CLAIM"}
            if TAIL_CONTRADICTION in prompt
            else {"decision": "STILL_VALID", "reason_code": "EVIDENCE_UNCHANGED"}
        )

        receipt = self.contract.recheck_claim(claim_id)

        self.assertEqual(receipt["decision"], "CONTRADICTED")
        self.assert_complete_inspection(receipt)
        self.assertTrue(all(TAIL_CONTRADICTION in prompt for prompt in cp.gl.nondet.prompts))
        self.assertEqual(json.loads(self.contract.get_claim(claim_id))["status"], "INVALIDATED")
        self.assertFalse(self.contract.is_usable(claim_id))

    def test_total_prompt_overflow_fails_baseline_without_partial_inspection(self):
        claim_id = self.open_three_maximum_sources()
        receipt = self.with_prompt_budget(28_000, lambda: self.contract.attest_claim(claim_id))

        self.assert_uninspected(receipt)
        self.assertEqual(receipt["reason_code"], "PROMPT_BUDGET_EXCEEDED")
        self.assertEqual(receipt["inspection"]["max_prompt_chars"], 28_000)
        self.assertGreater(receipt["inspection"]["prompt_chars"], 28_000)
        for source in receipt["sources"]:
            self.assertFalse(source["source_truncated"])
            self.assertTrue(source["prompt_truncated"])
            self.assertTrue(source["truncated"])
        record = json.loads(self.contract.get_claim(claim_id))
        self.assertEqual(record["status"], "BASELINE_RETRYABLE")
        self.assertEqual(record["valid_until"], 0)
        self.assertFalse(record["currently_usable"])

    def test_total_prompt_overflow_recheck_does_not_renew_previous_lease(self):
        claim_id = self.open_three_maximum_sources()
        self.contract.attest_claim(claim_id)
        original = json.loads(self.contract.get_claim(claim_id))
        self.now += 61
        cp.gl.nondet.prompts = []
        cp.gl.nondet.output = {"decision": "STILL_VALID", "reason_code": "EVIDENCE_UNCHANGED"}

        receipt = self.with_prompt_budget(28_000, lambda: self.contract.recheck_claim(claim_id))

        self.assert_uninspected(receipt)
        self.assertEqual(receipt["reason_code"], "PROMPT_BUDGET_EXCEEDED")
        current = json.loads(self.contract.get_claim(claim_id))
        self.assertEqual(current["valid_until"], original["valid_until"])
        self.assertEqual(current["last_checked_at"], original["last_checked_at"])
        self.assertEqual(current["last_decision"], original["last_decision"])
        self.assertEqual(current["check_state"], "RETRYABLE")
        self.assertEqual(current["recheck_attempts"], 1)
        self.now = original["valid_until"] + 1
        self.assertFalse(self.contract.is_usable(claim_id))

    def test_exact_total_prompt_budget_is_accepted(self):
        claim_id = self.open()
        claim = json.loads(self.contract.get_claim(claim_id))
        prompt = cp._prompt(claim, [cp._fetch_source(URL)], "BASELINE")

        receipt = self.with_prompt_budget(len(prompt), lambda: self.contract.attest_claim(claim_id))

        self.assertEqual(receipt["decision"], "SUPPORTED")
        self.assertTrue(receipt["inspection"]["complete"])
        self.assertEqual(receipt["inspection"]["prompt_chars"], len(prompt))
        self.assertEqual(receipt["inspection"]["max_prompt_chars"], len(prompt))
        self.assertEqual(cp.gl.nondet.prompts, [prompt, prompt])

    def test_one_character_over_total_prompt_budget_is_unreadable(self):
        claim_id = self.open()
        claim = json.loads(self.contract.get_claim(claim_id))
        prompt = cp._prompt(claim, [cp._fetch_source(URL)], "BASELINE")

        receipt = self.with_prompt_budget(len(prompt) - 1, lambda: self.contract.attest_claim(claim_id))

        self.assert_uninspected(receipt)
        self.assertEqual(receipt["reason_code"], "PROMPT_BUDGET_EXCEEDED")
        self.assertEqual(receipt["inspection"]["prompt_chars"], len(prompt))
        self.assertEqual(receipt["inspection"]["prompt_sha256"], cp._hash_text(prompt))

    def test_escaped_maximum_fields_are_included_in_total_prompt_budget(self):
        claim_id = self.open_three_maximum_sources(
            claim_text="\U0001f600" * 800,
            evidence_standard="\U0001f600" * 800,
        )
        claim = json.loads(self.contract.get_claim(claim_id))
        sources = [cp._fetch_source(url) for url in THREE_URLS]
        prompt = cp._prompt(claim, sources, "BASELINE")
        self.assertGreater(len(prompt), cp.MAX_TOTAL_PROMPT_CHARS)

        receipt = self.contract.attest_claim(claim_id)

        self.assert_uninspected(receipt)
        self.assertEqual(receipt["reason_code"], "PROMPT_BUDGET_EXCEEDED")
        self.assertEqual(receipt["inspection"]["prompt_chars"], len(prompt))
        self.assertEqual(receipt["inspection"]["prompt_sha256"], cp._hash_text(prompt))

    def test_invalid_utf8_is_unreadable_without_model_call(self):
        claim_id = self.open()
        cp.gl.nondet.web.pages[URL] = (200, b"apparently supportive text\xff")

        receipt = self.contract.attest_claim(claim_id)

        self.assert_uninspected(receipt)
        self.assertTrue(receipt["sources"][0]["error"])
        self.assertFalse(receipt["sources"][0]["source_truncated"])

    def test_invalid_utf8_recheck_does_not_renew_lease(self):
        claim_id, _ = self.attest()
        original = json.loads(self.contract.get_claim(claim_id))
        self.now += 61
        cp.gl.nondet.prompts = []
        cp.gl.nondet.web.pages[URL] = (200, b"apparently supportive text\xff")

        receipt = self.contract.recheck_claim(claim_id)

        self.assert_uninspected(receipt)
        record = json.loads(self.contract.get_claim(claim_id))
        self.assertEqual(record["valid_until"], original["valid_until"])
        self.assertEqual(record["last_checked_at"], original["last_checked_at"])
        self.assertEqual(record["check_state"], "RETRYABLE")

    def test_oversized_source_records_truncation_and_skips_model(self):
        claim_id = self.open()
        cp.gl.nondet.web.pages[URL] = (200, "a" * (cp.MAX_SOURCE_BYTES + 1))

        receipt = self.contract.attest_claim(claim_id)

        self.assert_uninspected(receipt)
        source = receipt["sources"][0]
        self.assertEqual(source["bytes"], cp.MAX_SOURCE_BYTES + 1)
        self.assertTrue(source["source_truncated"])
        self.assertTrue(source["truncated"])

    def test_fetch_failure_is_unreadable_without_model_call(self):
        claim_id = self.open()
        cp.gl.nondet.web.pages[URL] = (503, "temporarily unavailable")

        receipt = self.contract.attest_claim(claim_id)

        self.assert_uninspected(receipt)
        self.assertEqual(receipt["sources"][0]["status"], 503)

    def assert_coverage_tampering_rejected(self, phase):
        fields = [
            ("inspection", "complete", False),
            ("inspection", "prompt_chars", 1),
            ("inspection", "max_prompt_chars", 1),
            ("inspection", "prompt_sha256", "f" * 64),
            ("source", "source_truncated", True),
            ("source", "prompt_truncated", True),
            ("source", "truncated", True),
            ("source", "inspected_bytes", 0),
        ]
        for location, key, value in fields:
            with self.subTest(phase=phase, location=location, field=key):
                self.setUp()
                claim_id = self.open()
                if phase == "RECHECK":
                    self.contract.attest_claim(claim_id)
                    self.now += 61
                    cp.gl.nondet.output = {"decision": "STILL_VALID", "reason_code": "EVIDENCE_UNCHANGED"}
                before = self.contract.get_claim(claim_id)

                def tamper(receipt, location=location, key=key, value=value):
                    if location == "inspection":
                        receipt["inspection"][key] = value
                    else:
                        receipt["sources"][0][key] = value
                        # A self-consistent snapshot hash must not excuse altered coverage.
                        receipt["source_snapshot_hash"] = cp._hash_text(cp._canonical(receipt["sources"]))
                    return receipt

                _VM.mutator = tamper
                action = self.contract.attest_claim if phase == "BASELINE" else self.contract.recheck_claim
                with self.assertRaises(AssertionError):
                    action(claim_id)
                self.assertEqual(self.contract.get_claim(claim_id), before)

    def test_baseline_validator_binds_all_inspection_metadata(self):
        self.assert_coverage_tampering_rejected("BASELINE")

    def test_recheck_validator_binds_all_inspection_metadata(self):
        self.assert_coverage_tampering_rejected("RECHECK")


if __name__ == "__main__":
    unittest.main()
