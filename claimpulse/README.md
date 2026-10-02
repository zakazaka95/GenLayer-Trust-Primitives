# ClaimPulse

Current deployment: [ClaimPulse v1.1.0 on Studio Next](https://explorer-studio-next.genlayer.com/address/0x2C8043e7A6ac53f595F8d597796Ac1cde4f93A97). [Accepted deployment transaction](https://explorer-studio-next.genlayer.com/tx/0x1ed12c7798a01a10de8d78b3ec05a220649f9119aea52a7e0625c8e3d65e5e4f). The complete Explorer source matches this tracked source after line-ending normalization. The earlier v1.0.0 address is superseded.

ClaimPulse is a reusable freshness lease for public claims. It answers a problem ordinary oracles usually ignore: a claim can be correct when accepted and wrong later. A requester locks the claim, its evidence standard, one to three public sources and a lease duration. GenLayer validators attest the baseline, then later rechecks can renew the lease or seal that the claim was narrowed, superseded or contradicted.

## Why it matters

Agents act on changing policies, eligibility rules, product terms, service availability and public commitments. A permanent boolean is unsafe for those facts. ClaimPulse makes validity explicitly temporary. Downstream contracts can call `is_usable` and refuse an expired or invalidated claim without pretending the original receipt remains current forever.

## Lifecycle

- `OPEN` — the exact claim, evidence standard, sources and lease are locked.
- `BASELINE_RETRYABLE` / `UNREADABLE_FINAL` — bounded source-read recovery.
- `ACTIVE` — the baseline was directly supported and the lease has not expired.
- `REJECTED` — the baseline was not fully supported.
- `INVALIDATED` — a recheck found the claim narrowed, superseded or contradicted.

Baseline decisions are `SUPPORTED` and `UNSUPPORTED`. Recheck decisions are `STILL_VALID`, `NARROWED`, `SUPERSEDED` and `CONTRADICTED`. Only `STILL_VALID` extends `valid_until`.

## Consensus and receipt chain

For every attestation, the leader records each locked URL's status, byte count, digest and inspection coverage, then returns a fixed decision and reason code. Validators independently refetch the sources and reconstruct the entire canonical receipt. Any changed source digest, URL, status, coverage field, prompt metadata, revision, prior receipt hash, decision or reason rejects the candidate.

Every accepted attempt is stored under `(claim_id, revision)`. Each receipt commits to the previous receipt hash, producing an auditable evidence history. `is_usable` is deterministic: the record must be `ACTIVE`, unexpired, and most recently supported or reconfirmed.

## v1.1.0 inspection coverage correction

The original combined-source cutoff could silently omit part of source 3 when three 12,000-byte sources were supplied. v1.1.0 removes all evidence slicing in both baseline and recheck paths. The complete constructed prompt, including claim, evidence standard, URLs, phase rules and delimiters, must fit a 40,000-character budget. Otherwise the model is not called and the receipt is `UNREADABLE` with `PROMPT_BUDGET_EXCEEDED`.

Each v2 source snapshot binds `source_truncated`, `prompt_truncated`, `inspected_bytes` and the aggregate `truncated` flag. Complete model input has `inspected_bytes == bytes` for every source. Any unreadable source or over-budget prompt records zero inspected bytes for all sources. The receipt also binds the prompt character count, budget, SHA-256 and complete-coverage status. These fields describe supplied model input, not a guarantee of model attention or decision accuracy. Invalid UTF-8 is rejected without changing the fetched byte count or digest.

An incomplete baseline cannot issue a lease. An incomplete recheck cannot renew one; the previous supported lease retains only its original expiry. Tests exercise both phases with three maximum-sized sources and a contradiction at the end of source 3, prompt-budget boundaries, escaped request overflow and coverage-field tampering.

## Public methods

- `open_claim(claim_text, evidence_standard, urls_json, lease_seconds) -> int`
- `attest_claim(claim_id) -> dict`
- `recheck_claim(claim_id) -> dict`
- `get_claim(claim_id) -> str`
- `is_usable(claim_id) -> bool`
- `get_receipt(claim_id, revision) -> dict`
- `get_recent_claims(limit) -> list`
- `get_stats() -> dict`

Leases range from five minutes to thirty days. Rechecks are separated by at least sixty seconds.

## Limits

ClaimPulse proves only what the locked public sources support at each accepted observation. It is not a universal truth or safety oracle. Source authority and evidence standard must be scoped carefully by the requester. Sources are limited to three URLs and 12,000 bytes each; the complete prompt is limited to 40,000 characters. An `ACTIVE` status alone is not sufficient: integrations must call `is_usable` to check expiry.

## Files

- `ClaimPulse.py` — Studio Next contract.
- `test_claimpulse.py` — 21 lifecycle, expiry, chain, inspection-coverage and tamper tests, including 16 coverage-metadata tampering subcases across baseline and recheck.
- `STUDIO-TEST.md` — deploy and live-call walkthrough.
- `SUBMISSION.md` — Portal-ready title and description.
