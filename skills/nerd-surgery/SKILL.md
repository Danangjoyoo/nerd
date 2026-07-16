---
name: nerd-surgery
description: Use when code, integrations, automation, infrastructure, or runtime behavior is broken, unexpected, inconsistent, or probably misimplemented and the user wants diagnosis, root-cause analysis, or repair.
---

# Nerd Surgery

## Inheritance

Use `nerd-smart` first and consume its resolved Focus Record. A Focus Record is resolved only when all four fields are explicit, the endpoint is **Diagnose** or **Execute**, and no material ambiguity remains. Do not investigate or repair before the record is resolved.

Use the Focus Record as the base diagnostic frame. Treat any user-suggested cause as a hypothesis, not evidence. This specialty adds diagnostic behavior without replacing the confirmed scope or endpoint.

Read [references/systematic-debugging.md](references/systematic-debugging.md) before diagnosis. At an execute endpoint, also read [references/test-first-repair.md](references/test-first-repair.md) before mutation and [references/verification.md](references/verification.md) before any success claim.

Check Generic Diagnostic Mappings first against the observed symptom. Pick the single closest row when it offers the next discriminating check; use a sharper evidence-led check when one already exists. Do not combine rows. Mappings select evidence; they never establish cause.

## Generic Diagnostic Mappings

| # | Signal | First discriminating check | Confirmation evidence |
| --- | --- | --- | --- |
| **1** | Deterministic wrong output | Minimize the failing input and trace the first incorrect boundary. | The controlled input repeatedly fails at that boundary. |
| **2** | Intermittent or flaky | Repeat while recording seed, time, order, load, and concurrency. | One controlled factor changes the failure rate. |
| **3** | Crash or exception | Capture the smallest triggering input and first relevant stack frame. | The same path fails before correction and survives after. |
| **4** | Hang or timeout | Find the last completed boundary and inspect task, thread, or process state. | A faithful reproducer completes after the correction. |
| **5** | Performance regression | Compare the same workload and profile against a known baseline. | The hotspot is measured and the target threshold recovers. |
| **6** | State or data corruption | Trace reads, writes, and transformations against one invariant. | The invariant fails before correction and holds after. |
| **7** | Integration or API failure | Capture sanitized request, response, auth, serialization, and retry signals. | A boundary test reproduces the exact failure. |
| **8** | Build, compile, or type failure | Start from the first causal diagnostic with the exact toolchain and configuration. | The minimal target passes with the same toolchain. |
| **9** | Environment or configuration mismatch | Diff effective runtime, configuration, and dependencies between working and failing setups. | Aligning one differing factor toggles the failure. |
| **10** | Visual or UI mismatch | Capture screenshot, viewport, DOM/state, events, and relevant network activity. | The interaction reproduces before and visual or behavior proof passes after. |

## Surgery Discipline

Use this loop internally. Update the Case Record only when evidence or the active hypothesis changes.

| Step | Rule |
| --- | --- |
| **Focus** | Consume the resolved Focus Record as the base diagnostic frame. Treat a user-suggested cause as a hypothesis, not evidence. |
| **Observe** | Capture the user inputs and symptom, including expected versus observed behavior. Reproduce it when possible; otherwise preserve the evidence gap. |
| **Map** | Check Generic Diagnostic Mappings first and select at most one row to sharpen the next check. |
| **Experiment** | State one active hypothesis and design the smallest discriminating experiment that changes one variable. |
| **Analyze** | Compare predicted and observed signals. Classify the result as **Supported**, **Rejected**, or **Inconclusive**. |
| **Iterate** | When rejected or inconclusive, update the evidence and repeat from Observe. When supported, seek direct causal confirmation before prescribing change. |

When user confirmation is required, follow Nerd Smart's Confirmation Style: ask one short, sharp question; offer two or three mutually exclusive options; put the recommended option first with one brief reason. Ask only when the answer changes the experiment, authorization, or confirmed scope.

## Diagnostic Contract

Act as the Doctor: establish cause before prescribing change.

- A diagnose endpoint stops at findings and prescription; an execute endpoint may continue into repair.
- If the endpoint is ambiguous, recommend diagnosis-only and ask once.
- Diagnosis must not block an explicitly requested repair. After one evidence pass and one Uncertainty Check, make the smallest reversible attempt.
- Classify the cause as **Confirmed**, **Probable**, or **Unknown**. Confirmed requires direct causal evidence.
- Keep one active hypothesis. Track at most three plausible hypotheses internally and expose alternatives only when they change the next check.
- A repair under Probable or Unknown remains an attempt until fresh proof confirms it.

## Gather Discriminating Evidence

Use existing evidence first, then choose the highest-signal, lowest-friction check:

- Visual symptom: inspect or request a screenshot.
- Operational symptom: use an available authenticated integration or request a relevant link. Never request a secret in chat.
- Behavioral ambiguity: ask one question at a time.
- Missing integration: request sanitized logs or secure setup.

Update the Case Record only when evidence or the active hypothesis changes. If evidence points to another source, issue one scoped Source Request. Prefer a local checkout; ask for access setup, never credentials.

For **Probable** or **Unknown**, show exactly one Uncertainty Check. If the user chooses repair, record the accepted uncertainty and proceed without another gate.

## Verify With an Experiment

Before repair, show the Verification Experiment and run it when the environment can faithfully exercise the cause:

1. Check repository-native tests, runtimes, containers, and already-authorized integrations.
2. Create the smallest faithful reproducer in the repository language.
3. Observe inputs, outputs, logs, and assertions before the change.
4. Apply one approved correction and repeat the same signals.
5. Keep a useful regression test; remove temporary harnesses with no lasting value.

Prefer local execution. Remote writes, deployment, production access, SSH/tunneling, or database assertions require concise approval. If proof is unavailable, state the evidence gap and do not claim resolution.

## Correction Discipline

At an execute endpoint, corrections remain experiments. Treat every correction as one hypothesis test. Change one causal variable and repeat the same reproducer; never stack speculative fixes.

- After the first failed correction, record what it disproved and return to Surgery Discipline.
- After the second failed correction, stop changing code and complete an Architecture Check.
- Do not attempt a third correction until the user approves the revised direction.

## Records

**Case Record**
- **Symptom:** [Observed versus expected]
- **Evidence:** [Current strongest evidence]
- **Active hypothesis:** [Most likely explanation]
- **Next check:** [One discriminating action or question]

**Diagnosis**
- **Root cause:** [Confirmed cause]
- **Evidence:** [What confirms it]
- **Prescription:** [Smallest correction]
- **Verification:** [How success will be proven]

**Uncertainty Check**
- **Status:** [Probable or Unknown]
- **Reason:** [One sharp sentence]
- **Recommendation:** [Continue diagnosis or attempt repair]
- **Choose:** Continue diagnosing / attempt repair

**Source Request**
- **Why:** [Causal reason this source may contain the fault]
- **Need:** [Local directory or remote repository]
- **Access:** [Existing authenticated integration or local checkout]
- **Scope:** [Specific component or path]

**Verification Experiment**
- **Hypothesis:** [Cause and why the correction should work]
- **Reproducer:** [Minimal test, script, or app]
- **Environment:** [Local runtime, container, cluster, or integration]
- **Signals:** [Inputs, outputs, logs, and assertions]
- **Expected:** [Failure before correction and success after]
- **Access:** [Ready, approval required, or unavailable]

**Architecture Check**
- **Failed corrections:** [Two attempted causes]
- **New evidence:** [What the failures revealed]
- **Suspected boundary:** [Component, dependency, or architectural assumption]
- **Recommendation:** [Continue diagnosis or revise architecture]

Never describe an attempt as resolved without fresh proof.
