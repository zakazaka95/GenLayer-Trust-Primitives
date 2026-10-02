# Studio Next test path

## Deploy

Open Studio Next, create a Python contract, paste the complete contents of `ClaimPulse.py`, compile and deploy on chain ID `61997`.

Call `get_stats` and confirm `contract_version: 1.1.0`, `receipt_schema: claim-pulse-receipt-v2`, `max_source_bytes: 12000` and `max_total_prompt_chars: 40000`.

## Baseline path

Call `open_claim` with:

- `claim_text`: `The GenLayer project boilerplate includes an Intelligent Contract with web access and LLM integration, direct-mode tests and a Next.js frontend.`
- `evidence_standard`: `The official repository README must directly list each component in the claim.`
- `urls_json`: `["https://raw.githubusercontent.com/genlayerlabs/genlayer-project-boilerplate/v2-dev/README.md"]`
- `lease_seconds`: `600`

Read `get_claim(0)`. It should be `OPEN` and include the exact source, lease and `claim_hash`.

Call `attest_claim(0)`. The intended result is `SUPPORTED`, making the claim `ACTIVE` for ten minutes. Confirm:

- `is_usable(0)` is true before `valid_until`;
- `get_receipt(0, 1)` returns the complete baseline receipt;
- the receipt contains the exact source digest and an empty `previous_receipt_hash`.
- `inspection.complete` is true, `inspection.prompt_chars <= inspection.max_prompt_chars`, and every source has `inspected_bytes == bytes` with both cutoff flags false.

## Recheck path

After at least sixty seconds, call `recheck_claim(0)`. If the official README still supports the full claim, the intended result is `STILL_VALID` and the lease is renewed. Confirm:

- revision increments to `2`;
- receipt 2 commits to receipt 1 through `previous_receipt_hash`;
- `valid_until` advances from the recheck time;
- any `NARROWED`, `SUPERSEDED` or `CONTRADICTED` decision changes the record to `INVALIDATED` instead of silently rewriting the original claim.

## Inspection regression tests

Run `python -m unittest claimpulse/test_claimpulse.py` from the repository root. The 21 tests cover three 12,000-byte sources with a contradiction at the end of source 3 for both phases, exact prompt-budget and one-character-over boundaries, escaped-field overflow, invalid UTF-8, oversized responses and tampering with coverage metadata. A forced over-budget baseline issues no lease; a forced over-budget recheck leaves the previous expiry unchanged.

Local tests use a controlled classifier to prove input coverage, receipt binding and state transitions. They do not benchmark live model judgment. The live path above separately checks deployment and accepted consensus behavior against the evidence available at the time of the call.
