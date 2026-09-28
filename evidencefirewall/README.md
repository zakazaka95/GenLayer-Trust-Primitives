# EvidenceFirewall

EvidenceFirewall is an onchain admissibility gate for agents and Intelligent Contracts that consume arbitrary public web content. A requester locks an exact purpose, evidence standard and one to three public URLs before any interpretation occurs. Independent GenLayer validators then fetch the same sources and classify each one as clean, out of scope or carrying instruction-like content that could manipulate an AI evaluator.

## Why it matters

Autonomous systems increasingly use webpages, tickets, repositories and uploaded reports as evidence. Those sources are data, but they can contain sentences such as “ignore the policy,” “send the key,” or “call this tool.” Passing that content directly into an agent creates a prompt-injection boundary. EvidenceFirewall turns the boundary into a reusable, consensus-sealed receipt that downstream contracts can require before releasing funds or authority.

## State and decisions

- `OPEN` — purpose and exact source list are locked.
- `RETRYABLE` — at least one source was unavailable or exceeded the inspection limit; up to three attempts are allowed.
- `ADMISSIBLE` — every source is relevant and non-directive. Only this receipt has `release_allowed: true`.
- `QUARANTINED` — at least one source contains instruction-like content.
- `OUT_OF_SCOPE` — evidence is readable but does not satisfy the locked purpose.
- `UNREADABLE_FINAL` — three accepted attempts could not read a complete evidence set.

## Consensus design

The leader fetches each URL, records the HTTP status, complete body byte count, SHA-256 digest and truncation flag, and asks the model for fixed per-source enums. The contract derives the aggregate decision deterministically. Every validator independently refetches the locked URLs, re-runs the classification and rebuilds the complete receipt. Consensus accepts only byte-for-byte canonical equality of the consequential payload. A validator therefore rejects a leader that changes a digest, URL, status, risk code or release flag even if the top-level verdict remains the same.

Source text is explicitly delimited as untrusted data. The model is forbidden from following embedded instructions, opening additional URLs, using tools or revealing secrets.

## Public methods

- `open_screen(purpose, evidence_requirements, urls_json) -> int`
- `evaluate_screen(screen_id) -> dict`
- `get_screen(screen_id) -> str`
- `get_receipt(screen_id, attempt) -> dict`
- `get_recent_screens(limit) -> list`
- `get_stats() -> dict`

`urls_json` is a JSON array such as `["https://example.org/evidence"]`.

## Limits

This contract identifies evidence-admissibility risk; it does not prove that clean evidence is true, safe or complete. A downstream application must still adjudicate the claim itself. Sources are capped at 12 KB each, three URLs and three attempts.

## Files

- `EvidenceFirewall.py` — Studio Next contract.
- `test_evidencefirewall.py` — seven local lifecycle and tamper tests.
- `STUDIO-TEST.md` — deploy and live-call walkthrough.
- `SUBMISSION.md` — Portal-ready title and description.
