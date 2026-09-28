# Portal submission

## Title

EvidenceFirewall — Consensus-Sealed Prompt-Injection Gate for Public Evidence

## Notes / Description

EvidenceFirewall is a reusable admissibility primitive for agents and contracts consuming public web evidence. A requester locks an exact purpose, evidence standard and up to three HTTPS sources before interpretation. Independent GenLayer validators fetch the content and classify each source as CLEAN, OUT_OF_SCOPE or INJECTION_RISK, with fixed risk codes for prompt overrides, secret requests, tool control, identity manipulation and external actions. The contract deterministically derives ADMISSIBLE, QUARANTINED, OUT_OF_SCOPE or UNREADABLE. Only ADMISSIBLE sets release_allowed=true. Validators independently rebuild the complete canonical receipt, binding every URL, HTTP status, byte count, digest, truncation flag, classification and risk code. Receipts are stored per attempt; unreadable evidence has bounded retries and finality. Source text is treated as untrusted data, never instructions. Tests cover clean, malicious, irrelevant, unreadable, private-host and tampered-receipt paths.

## Suggested evidence

1. Public repository file for `EvidenceFirewall.py`.
2. Public repository file for `test_evidencefirewall.py`.
3. Studio Next contract address.
4. Accepted `open_screen` transaction.
5. Accepted `evaluate_screen` transaction and `get_receipt` result.
