# Behavioral Memory: Durable Recovery

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Behavioral Memory router](index.md) and load it only for its named trigger.

## Ledger Integration and Recovery

Apply this section only when the selected profile requires S2/S3. S0/S1 keeps
no duplicate durable Loop ledger; Nerd Memory still persists its own proposal
state under its independent contract.

Record memory-to-loop transitions as factual events, for example:

```text
MEMORY_BASELINE_COMMITTED
MEMORY_PROPOSAL_PENDING
MEMORY_CONFLICT_OBSERVED
MEMORY_PROPOSAL_CONSUMED
BEHAVIOR_CONTRACT_BOUND
BEHAVIOR_CONTRACT_REVISED
USER_GUIDANCE_OBSERVED
MEMORY_BINDING_STALE
ROUTING_BOUND
ROUTING_PROFILE_ACTIVATED
ROUTING_PROFILE_REPEATED
ROUTING_PROFILE_SATISFIED
ROUTING_COMPLETED
ROUTING_BLOCKED
```

Recommended event payloads contain stable IDs and hashes, never secrets:

```yaml
event_type: BEHAVIOR_CONTRACT_BOUND
root_episode_id: episode-...
loop_id: loop-...
loop_contract_revision: 3
proposal_id: proposal-...
proposal_hash: sha256:...
endpoint_hash: sha256:...
pattern_revisions:
  - pattern_id: pattern-...
    revision: 4
context_hash: sha256:...
consumed_at: 2026-08-10T00:00:00Z
```

Do not record:

- plaintext grant tokens;
- reusable confirmation or denial references;
- raw prompts or transcripts;
- pattern evidence text copied from Nerd Memory;
- secrets or sensitive values; or
- a false `memory_confirmed` event before atomic consumption succeeds.

Crash recovery rules:

- A committed `BEHAVIOR_CONTRACT_BOUND` plus its canonical effective endpoint
  is sufficient to resume the task contract.
- A committed routing cursor resumes the same chain/profile index after its
  proposal reference, chain/registry/authority hashes, expected revision,
  bounds, status/active-iteration/last-event coherence, and full remaining
  chain preflight pass. Validate that the event/index/revision tuple is
  reachable from the initial bound cursor; a syntactically valid cursor cannot
  skip earlier profiles. Never infer advancement from an agent message or
  uncommitted attempt; reconcile an ambiguous effect before repeat. Advance
  only from an authenticated receipt bound to the exact proposal, active
  iteration, profile/index/hash, `VERIFIED` outcome, declared guard evidence,
  and hash of the matching committed iteration reference/event/revision.
- A pending proposal remains a human checkpoint; do not synthesize its phrase
  or assume it was accepted.
- A confirmed-but-unconsumed proposal must be reconciled through Nerd Memory;
  never guess whether its grant was used.
- A consumed grant is not reusable. Resume from the loop contract rather than
  calling `consume` again.
- If the loop ledger and memory runtime disagree, stop the affected path,
  inspect both committed records, and prefer no memory influence until the
  inconsistency is resolved.
