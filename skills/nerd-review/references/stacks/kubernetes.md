# Kubernetes Review

- **Use:** Kubernetes/Helm/Kustomize boundary; preserve API/cluster version,
  namespace, controller, admission, and overlay.
- **Level 1:** Check rendered schema, names, selectors, labels, ports, references,
  mounts, identity, probes, lifecycle, rollout, resources, and security context.
- **Level 2:** Match naming, policy, probes, resources, and overlays; test render,
  schema, selectors, ports, configuration, and rollback; update runbooks.
- **Level 3:** Check controller/state ownership, cross-namespace coupling,
  readiness cycles, bottlenecks, availability, and template/overlay drift.
- **Proof:** Prefer repository render/validation against explicit target version.
- **Escalate:** Traffic loss, unavailable workload, data loss, privilege/secret
  exposure, rollout break, or predictable exhaustion.
- **Avoid:** Live apply/diff, secret reads, hooks, and naming-only findings.

