# Portal submission

## Title

EvidenceFirewall — Consensus-Sealed Prompt-Injection Gate for Public Evidence

## Notes / Description

EvidenceFirewall v1.1.0 screens public evidence before agents or contracts use it. Requests lock a purpose, evidence standard and up to three HTTPS URLs. Independent GenLayer validators fetch and classify each source as CLEAN, OUT_OF_SCOPE or INJECTION_RISK; only ADMISSIBLE permits release. The inspection correction removes all prompt slicing and checks the complete prompt against a 40,000-character budget. Every accepted source is supplied in full, or the result fails closed as UNREADABLE without a classifier call. Receipts bind source bytes, digest, inspected_bytes, source_truncated, prompt_truncated, classifications and complete prompt metadata. Validators independently rebuild the entire canonical receipt. Bounded retries preserve attempt history. Tests cover three 12,000-byte sources with an injection at the tail of source 3, budget overflow, invalid UTF-8, exact boundaries and tampered coverage. The submitted Explorer deployment matches the tracked corrected source.

## Suggested evidence

1. Public repository file for `EvidenceFirewall.py`.
2. Public repository file for `test_evidencefirewall.py`.
3. Studio Next contract address.
4. Accepted `open_screen` transaction.
5. Accepted `evaluate_screen` transaction and `get_receipt` result.
