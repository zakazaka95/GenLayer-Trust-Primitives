# Portal submission

## Title

ClaimPulse — Expiring Consensus Leases for Time-Sensitive Public Claims

## Notes / Description

ClaimPulse is a reusable freshness primitive for public facts that can change after acceptance. A requester locks a scoped claim, evidence standard, up to three HTTPS sources and a five-minute-to-thirty-day validity lease. GenLayer validators first decide whether the baseline is fully SUPPORTED. Rechecks classify it as STILL_VALID, NARROWED, SUPERSEDED or CONTRADICTED; only STILL_VALID renews the lease. Downstream contracts call is_usable to reject expired or invalidated claims instead of treating an old receipt as permanent truth. Every validator independently refetches the locked sources and rebuilds the complete canonical receipt, binding URL, status, bytes, SHA-256, truncation state, revision, prior receipt hash, decision and reason. Accepted attempts form an onchain hash-chained history. Unreadable sources use bounded retries without extending validity. Tests cover support, rejection, expiry, renewal, narrowing, unreadable finality, private hosts and receipt tampering.

## Suggested evidence

1. Public repository file for `ClaimPulse.py`.
2. Public repository file for `test_claimpulse.py`.
3. Studio Next contract address.
4. Accepted `open_claim` and `attest_claim` transactions.
5. Accepted `recheck_claim` transaction showing a chained receipt.
