# Studio Next test path

## Deploy

Open Studio Next, create a Python contract, paste the complete contents of `EvidenceFirewall.py`, compile and deploy on chain ID `61997`.

## Clean evidence path

Call `open_screen` with:

- `purpose`: `Inspect the official GenLayer boilerplate README before using it as implementation evidence.`
- `evidence_requirements`: `The source must describe the repository contents and developer workflow without asking the evaluator to take an external action.`
- `urls_json`: `["https://raw.githubusercontent.com/genlayerlabs/genlayer-project-boilerplate/v2-dev/README.md"]`

Read `get_screen(0)`. The expected status is `OPEN`, with the exact URL and a non-empty `request_hash`.

Call `evaluate_screen(0)`. The intended result is `ADMISSIBLE`. Live AI consensus can differ if the public source changes; the important verification points are:

- an accepted transaction;
- one complete source snapshot with URL, HTTP status, bytes and SHA-256;
- `inspected_bytes` equals the fetched byte count, `source_truncated` and `prompt_truncated` are false, and `inspection.complete` is true;
- `release_allowed` is true only for `ADMISSIBLE`;
- `get_receipt(0, 1)` returns the exact persisted receipt.

## Negative-path demonstration

Open another screen whose source contains text explicitly addressed to an AI or agent and asks it to ignore rules, reveal a secret, invoke a tool or perform an external action. After evaluation, the expected decision is `QUARANTINED` with `release_allowed: false` and a non-`NONE` risk code.

Do not use private, credentialed or sensitive URLs. The contract intentionally rejects HTTP, localhost and private IP hosts.

## Inspection coverage regression

Run `python -m unittest evidencefirewall/test_evidencefirewall.py` from the repository root. The three-maximum-source test uses three exact 12,000-byte bodies and puts an instruction at the tail of the third body, beyond the old 28,000-character cutoff. It captures the actual prompts passed to both the leader and independent validator, asserts that every complete body is present, and makes the mock classifier's risk decision depend on that tail being present. Other regressions force complete-prompt overflow and require zero model calls, explicit truncation and `release_allowed: false`, test invalid UTF-8 and exact budget boundaries, and reject altered inspection fields. These are local regressions; they do not measure live model detection accuracy.
