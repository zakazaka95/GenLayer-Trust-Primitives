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

## Studio Next deployments

| Contract | Address | Deployment transaction |
|---|---|---|
| EvidenceFirewall v1.1.0 | [`0x7e55675951b145B10439AD4AbF219aE51037E35a`](https://explorer-studio-next.genlayer.com/address/0x7e55675951b145B10439AD4AbF219aE51037E35a) | [`0x5eeb226e…`](https://explorer-studio-next.genlayer.com/tx/0x5eeb226e6aa06c729a91bad3a10ac7cf02e4a9ca863d2ba93a702877f6282b66) |
| ClaimPulse v1.1.0 | [`0x2C8043e7A6ac53f595F8d597796Ac1cde4f93A97`](https://explorer-studio-next.genlayer.com/address/0x2C8043e7A6ac53f595F8d597796Ac1cde4f93A97) | [`0x1ed12c77…`](https://explorer-studio-next.genlayer.com/tx/0x1ed12c7798a01a10de8d78b3ec05a220649f9119aea52a7e0625c8e3d65e5e4f) |

The EvidenceFirewall v1.0.0 deployment at `0x060F659eE6d44cDcaC8e677242B3Ac28102b0526` is superseded by v1.1.0 above; it still contains the old prompt cutoff. The corrected deployment's complete Explorer source was compared with the tracked `EvidenceFirewall.py` and matched after normalizing line endings and trimming surrounding whitespace. Its normalized source SHA-256 is `1bc1d6dcbbfde0a51413fc9b46843ab34cf8d15aee96af8ecaf8721f0158aaaa`.

The ClaimPulse v1.0.0 deployment at `0x6B3D79834618Da27029833f75863AC2B77b2E754` is likewise superseded. Its v1.1.0 deployment was accepted on October 2, 2026; `get_stats` reports receipt schema v2 and the 40,000-character complete-prompt budget. The full Explorer source matched the tracked `ClaimPulse.py` after the same normalization. Its normalized source SHA-256 is `b8c40ecf190f9cf6257d2c9c543a197afb053ddbe8c1e720687952481f921096`.

The two ideas were checked against the current GenLayer Project Explorer using direct keyword searches. No direct `EvidenceFirewall`, prompt-injection evidence gate, claim-freshness lease or supersession primitive was found. This is a collision check, not a claim that no unpublished contract anywhere uses related concepts.

## Layout

- `evidencefirewall/` — contract, tests, deployment walkthrough and submission copy.
- `claimpulse/` — contract, tests, deployment walkthrough and submission copy.

## Local verification

```text
python -m unittest evidencefirewall/test_evidencefirewall.py claimpulse/test_claimpulse.py
```

Expected result: `Ran 38 tests ... OK`.

EvidenceFirewall v1.1.0 corrects the inspection cutoff reported in review. See [the coverage correction and regression tests](evidencefirewall/README.md#v110-inspection-coverage-correction) for the full prompt budget, explicit inspection fields and fail-closed behavior.

ClaimPulse v1.1.0 applies the same coverage correction to both baseline and recheck. See [the complete-input lease rules and regression tests](claimpulse/README.md#v110-inspection-coverage-correction).
