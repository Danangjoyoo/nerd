# Docker and Docker Compose Review

- **Use:** Dockerfile/image/Compose boundary; preserve platform, versions, image
  provenance, file order, profiles, context, and runtime environment.
- **Level 1:** Check context/ignore, stages, base image, `ARG`/`ENV`, copies,
  user, entrypoint, signals, secrets, permissions, mounts, ports, and health.
- **Level 2:** Match image, user, label, health, logging, network, and volume
  conventions; test builds, profiles, merges, shutdown, and artifact contents.
- **Level 3:** Check build/runtime separation, state ownership, mutable tags,
  host coupling, circular readiness, duplicated policy, and mixed lifecycles.
- **Proof:** Prefer source and offline resolved-model checks with secrets hidden.
- **Escalate:** Credential leak, platform mismatch, volume loss, broken shutdown,
  or reliable startup/availability failure.
- **Avoid:** Build, pull, push, run, exec, mutate, prune, and layer-count opinions.

