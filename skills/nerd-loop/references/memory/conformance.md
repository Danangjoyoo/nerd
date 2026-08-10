# Behavioral Memory: Conformance

This chunk inherits [the Nerd Loop Runtime Contract](../runtime-contract.md). Enter through [the Behavioral Memory router](index.md) and load it only for its named trigger.

## Failure Modes

Avoid these designs:

- **Retrieve every iteration:** creates repeated interruptions, context drift,
  and false independent evidence.
- **Transcript memory:** stores excess sensitive and adversarial content while
  blurring direct guidance with external text.
- **Memory as permission:** turns a prior preference into present action
  authority.
- **Memory as proof:** treats a remembered result or passing historical test as
  evidence that the current DoD passed.
- **Self-reinforcement:** converts the loop's own plan, success, or reflection
  into a stronger user preference.
- **Episode inflation:** counts retries, child loops, summaries, or parallel
  agents as independent user support.
- **Silent nearest match:** forces a behavioral route despite scope mismatch or
  no exact trigger.
- **Auto-promotion:** lets frequency activate an inert candidate.
- **Grant persistence:** stores or replays the one-use token during recovery.
- **Cross-workspace fallback:** leaks one project's behavior into another.
- **Agent-majority conflict resolution:** lets several agents vote away an
  authoritative disagreement.
- **Valid-prefix routing:** activates profile zero before proving every later
  profile exists and is allowed, causing a partial remembered route.
- **Boolean route completion:** advances a routing cursor from caller assertions
  instead of an authenticated proposal/profile/iteration/guard receipt whose
  hashed commit identity comes from the bound effect journal.
- **Blind cross-field composition:** accepts a remembered action or verifier
  that contradicts a current boundary merely because it populates another
  endpoint field.
- **Schema guessing:** silently maps or drops a runtime pattern type that is
  absent from the loaded Nerd Memory contract.
- **Memory-maintenance detour:** interrupts an active task to review candidates
  that have no bearing on its current endpoint.
## Integration Definition of Done

Nerd Loop and Nerd Memory are correctly composed only when all of these hold:

- a memory-blind endpoint exists before retrieval;
- the runtime and loaded memory contract agree before any pattern influences
  the loop;
- disabled and no-match memory take a non-blocking fast path;
- every memory-derived material field stops at one exact proposal gate;
- incompatible cross-field effects are resolved before proposal confirmation;
- the runtime contract's canonical authority order is preserved, including the
  distinction between mandatory and advisory checked-in material;
- one consumed proposal initializes one versioned root Behavior Contract;
- ordinary iterations and crash recovery do not re-query or re-consume memory;
- independent goals have separate episodes, while retries and internal child
  loops do not inflate support;
- all seven pattern types compile to the correct loop concerns without becoming
  authority or completion proof;
- routing profiles remain ordered and atomic, every profile passes full-chain
  preflight against the current authenticated registry and explicit
  agent-bound authority map before activation, cursor state is coherent, and
  advancement requires an authenticated guard receipt without lowering a
  profile floor;
- automatic verification always uses fresh current-state evidence;
- only minimal direct-user guidance or correction becomes eligible memory
  evidence;
- plans, results, tests, summaries, and agent output cannot self-reinforce;
- memory provenance, not tokens or transcripts, is bound to selected Loop
  state and committed only for S2/S3;
- concurrent memory transitions have one coordinator and deterministic runtime
  serialization; and
- material contract changes, conflicts, promotion, splitting, and forgetting
  retain their required human checkpoints.
