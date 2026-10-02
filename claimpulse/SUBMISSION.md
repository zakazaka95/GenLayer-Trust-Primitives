# Portal submission

## Title

ClaimPulse — Expiring Consensus Leases for Time-Sensitive Public Claims

## Notes / Description

ClaimPulse gives changing public claims an expiring consensus lease. A requester locks a claim, evidence standard, up to three HTTPS sources and a lease duration. Validators attest SUPPORTED or UNSUPPORTED, then rechecks return STILL_VALID, NARROWED, SUPERSEDED or CONTRADICTED. Only STILL_VALID renews the lease; integrations call is_usable to reject expired or invalidated claims. v1.1.0 supplies every accepted source byte in both phases or fails closed as UNREADABLE without issuing or extending a lease. The complete prompt is budgeted, never silently sliced. Validators independently refetch evidence and require exact canonical equality of the full receipt, including digests, URLs, status, source/prompt truncation, inspected bytes, prompt hash, decision and prior receipt hash. Accepted revisions form an onchain history. Bounded retries do not extend validity. 21 local tests cover lifecycle, three maximum-sized sources, tail contradictions, budget boundaries, UTF-8 and receipt tampering.

## Suggested evidence

1. Public repository file for `ClaimPulse.py`.
2. Public repository file for `test_claimpulse.py`.
3. Studio Next contract address.
4. Accepted `open_claim` and `attest_claim` transactions.
5. Accepted `recheck_claim` transaction showing a chained receipt.
