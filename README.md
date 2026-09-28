# GenLayer weekly contracts — 2026-09-28

Two standalone Intelligent Contract primitives for Studio Next:

1. **EvidenceFirewall** — screens public evidence before another agent or contract relies on it. It distinguishes admissible evidence, irrelevant evidence and instruction-like content that should be quarantined.
2. **ClaimPulse** — gives a public claim a bounded validity lease, then lets independent validators renew or invalidate it as the locked sources change.

Both contracts:

- use public HTTPS evidence and GenLayer non-deterministic execution;
- require validators to independently refetch and rebuild the complete receipt;
- compare the complete canonical receipt, including every source URL, status, byte count and digest;
- treat source content as untrusted data and explicitly reject instructions embedded inside it;
- store accepted consensus receipts onchain with bounded retry/finality rules;
- include local tests and exact Studio call examples.

The two ideas were checked against the current GenLayer Project Explorer using direct keyword searches. No direct `EvidenceFirewall`, prompt-injection evidence gate, claim-freshness lease or supersession primitive was found. This is a collision check, not a claim that no unpublished contract anywhere uses related concepts.

## Layout

- `evidencefirewall/` — contract, tests, deployment walkthrough and submission copy.
- `claimpulse/` — contract, tests, deployment walkthrough and submission copy.

## Local verification

```text
python -m unittest evidencefirewall/test_evidencefirewall.py claimpulse/test_claimpulse.py
```

Expected result: `Ran 15 tests ... OK`.
