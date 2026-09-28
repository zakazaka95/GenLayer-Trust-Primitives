# Studio Next test path

## Deploy

Open Studio Next, create a Python contract, paste the complete contents of `ClaimPulse.py`, compile and deploy on chain ID `61997`.

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

## Recheck path

After at least sixty seconds, call `recheck_claim(0)`. If the official README still supports the full claim, the intended result is `STILL_VALID` and the lease is renewed. Confirm:

- revision increments to `2`;
- receipt 2 commits to receipt 1 through `previous_receipt_hash`;
- `valid_until` advances from the recheck time;
- any `NARROWED`, `SUPERSEDED` or `CONTRADICTED` decision changes the record to `INVALIDATED` instead of silently rewriting the original claim.
