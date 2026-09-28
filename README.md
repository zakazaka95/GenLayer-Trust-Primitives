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
| EvidenceFirewall | [`0x060F659eE6d44cDcaC8e677242B3Ac28102b0526`](https://explorer-studio-next.genlayer.com/address/0x060F659eE6d44cDcaC8e677242B3Ac28102b0526) | [`0x7b75e826…`](https://explorer-studio-next.genlayer.com/tx/0x7b75e826d58085f672016f78451b6c91dc35f5f89fc8e0bf420e82fb956232b3) |
| ClaimPulse | [`0x6B3D79834618Da27029833f75863AC2B77b2E754`](https://explorer-studio-next.genlayer.com/address/0x6B3D79834618Da27029833f75863AC2B77b2E754) | [`0xfb5318ed…`](https://explorer-studio-next.genlayer.com/tx/0xfb5318ed5b0a657b122206a4724ea3f52d03a8bac84d8fb1a2edeed6bbea2db3) |

The two ideas were checked against the current GenLayer Project Explorer using direct keyword searches. No direct `EvidenceFirewall`, prompt-injection evidence gate, claim-freshness lease or supersession primitive was found. This is a collision check, not a claim that no unpublished contract anywhere uses related concepts.

## Layout

- `evidencefirewall/` — contract, tests, deployment walkthrough and submission copy.
- `claimpulse/` — contract, tests, deployment walkthrough and submission copy.

## Local verification

```text
python -m unittest evidencefirewall/test_evidencefirewall.py claimpulse/test_claimpulse.py
```

Expected result: `Ran 15 tests ... OK`.
