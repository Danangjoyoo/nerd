# Terraform Review

- **Use:** Terraform/OpenTofu boundary; preserve versions, locks, backend,
  workspace, variables, providers, and target environment.
- **Level 1:** Check format-validation mode, types, null/unknowns, sensitive data,
  stable keys, aliases, addresses, moves, lifecycle, ordering, and replacements.
- **Level 2:** Match module, naming, tags, constraints, variables, outputs, and
  policy; test identity, replacement, permissions, network, and recovery.
- **Level 3:** Check module/state boundaries, provider ownership, dependency
  direction, cross-stack coupling, duplicated policy, and unstable addresses.
- **Proof:** Prefer offline checks; plan only with authorized credentials/refresh.
- **Escalate:** Destroy/replace, exposure, secret leak, state instability, data
  loss, stranded resource, or blocked delivery.
- **Avoid:** Apply, import, state move/unlock, destroy, lock rewrite, and formatting.

