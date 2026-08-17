# Docker and Docker Compose Diagnosis

## Use

- Use when Docker Engine, a container boundary, or Compose owns the symptom.
- Pair with one diagnosis type and only the failing app, data, or infra stack.
- Diagnose only; apply the parent confidence gate and stop before repair.

## Capture

- Versions: Docker CLI, Engine/API, Compose, runtime; host OS and architecture.
- Target: `docker context show`, daemon endpoint, local/remote/rootless/Desktop mode.
- Identity: container ID, image ID/digest and platform, project/service, revision, incident window.
- Lifecycle: create/start/finish times, exit code/signal, OOM state, restarts, health transitions.
- Compose inputs: working/project directory and name, ordered `-f` files, `--env-file`, profiles.
- Record the exact creating command and interpolation-source **names**; tags/names are mutable identity.

## Diagnose

1. **Verify the target.** Run `docker context show` and `docker version`; stop on context, daemon, project, container, or authorization uncertainty. Treat `docker info` as sensitive.
2. **Build a bounded timeline.** Use `docker container ls -a`, targeted `docker container inspect --format`, `docker container logs --since ... --tail ... --timestamps`, and time-bounded filtered events.
   - Inspect = configured/runtime state; logs = process output; events = daemon lifecycle. Do not conflate them.
3. **Find the first failed boundary.** Separate image resolution, create/start, entrypoint/command, runtime, healthcheck, shutdown/signal, restart policy, mount/filesystem, network/DNS/port, limits, logging driver, and app failure.
   - `exited`, `restarting`, and `unhealthy` are symptoms, not causes.
4. **Verify image and process provenance.** Compare digest/platform, build metadata, `Entrypoint`/`Cmd`, working directory, user, executed process, environment **names**, labels, ports, mounts, and deployment revision. Do not build or pull.
5. **Inspect isolation.** Compare host/container architecture, mount source/type/options, path, UID/GID, permissions, cgroup limits, PID/signals, DNS, networks/aliases, bindings, and dependency endpoints.
   - Use targeted `docker stats --no-stream` or `docker top` only when authorized and necessary.
6. **Resolve Compose locally with the exact inputs.** Use `docker compose config --quiet`; bound structure with `config --services`, `--profiles`, `--images`, `--networks`, or `--volumes`.
   - Avoid full rendered config and `config --environment`; interpolation may expose secrets.
7. **Compare model with runtime.** Use bounded `docker compose ps -a`, `images`, and service logs; match project labels/config hash, image, command, health, networks, volumes, and replicas.
   - Account for merge order, project-name and environment precedence, profiles, and paths relative to the first Compose file.
8. **Check readiness.** `depends_on` ordering alone does not prove readiness; compare conditions, healthchecks, startup timing, retries, and the first failed connection.
9. **Classify and stop.** Report the first failed boundary, immutable provenance, direct evidence, ruled-out adjacent layer, and missing confirmation.

## Guardrails

- Treat Docker socket and remote-daemon access as privileged; require explicit authorization for non-local or production inspection.
- Keep queries narrow and read-only; bound time, objects, fields, and log volume.
- Redact environment values, labels, mounts, paths, logs, registry details, addresses, and app data.
- Never build, pull, push, create, run, exec, debug, copy, start, stop, restart, kill, pause, update, rename, remove, prune, commit, or mutate Docker resources, contexts, builders, or daemon configuration.
- With Compose, never use `up`, `down`, `create`, `start`, `stop`, `restart`, `run`, `exec`, `watch`, `pull`, `build`, `scale`, or removal commands; dry-run output does not make mutation safe.
- Stop before Dockerfile, Compose, image, resource, data, configuration, or deployment changes.

Official anchors:

- [Container inspect](https://docs.docker.com/reference/cli/docker/container/inspect/)
- [Compose config](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Compose startup order](https://docs.docker.com/compose/how-tos/startup-order/)
