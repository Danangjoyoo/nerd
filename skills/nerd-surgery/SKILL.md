---
name: nerd-surgery
description: Use when code, integrations, automation, infrastructure, or runtime behavior is broken, unexpected, inconsistent, or probably misimplemented and the user wants diagnosis, root-cause analysis, or repair.
---

# Nerd Surgery

## Inheritance

Use `nerd-smart` first and reuse its approved Focus Record. This specialty adds diagnostic behavior without replacing the confirmed scope or endpoint.

Read [references/systematic-debugging.md](references/systematic-debugging.md) before diagnosis. At an execute endpoint, also read [references/test-first-repair.md](references/test-first-repair.md) before mutation and [references/verification.md](references/verification.md) before any success claim.

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

Never describe an attempt as resolved without fresh proof.
