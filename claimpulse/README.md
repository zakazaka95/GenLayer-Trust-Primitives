# ClaimPulse

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

For every attestation, the leader records each locked URL's status, byte count, digest and truncation state, then returns a fixed decision and reason code. Validators independently refetch the sources and reconstruct the entire canonical receipt. Any changed source digest, URL, status, revision, prior receipt hash, decision or reason rejects the candidate.

Every accepted attempt is stored under `(claim_id, revision)`. Each receipt commits to the previous receipt hash, producing an auditable evidence history. `is_usable` is deterministic: the record must be `ACTIVE`, unexpired, and most recently supported or reconfirmed.

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

ClaimPulse proves only what the locked public sources support at each accepted observation. It is not a universal truth or safety oracle. Source authority and evidence standard must be scoped carefully by the requester.

## Files

- `ClaimPulse.py` — Studio Next contract.
- `test_claimpulse.py` — eight lifecycle, expiry, chain and tamper tests.
- `STUDIO-TEST.md` — deploy and live-call walkthrough.
- `SUBMISSION.md` — Portal-ready title and description.
