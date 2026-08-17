# Kubernetes Diagnosis

## Provenance / Scope

- Use when Kubernetes is the smallest failing boundary; pair with one diagnosis type.
- Record UTC window, explicit context/cluster/namespace, kind/name/UID, generation/observed generation, owner chain, Pod/container/node, image/imageID, rollout revision, desired/observed state, and affected replicas.
- Stop on uncertain context, namespace, UID, resource, or authorization; names alone are mutable identity.
- Diagnose from existing API state, events, logs, metrics, and approved telemetry; apply the parent confidence gate and stop before repair.

## Diagnose

1. **Verify target and capabilities.** Run:
   - `kubectl config current-context`
   - `kubectl --context <context> config view --minify -o jsonpath='{.contexts[0].context.cluster}{" namespace="}{.contexts[0].context.namespace}{"\n"}'`
   - `kubectl --context <context> version`
   - Client/server versions, installed APIs, metrics, plugins, resource fields, and command availability vary; use only supported reads.
   - Pin identity with `kubectl --context <context> -n <namespace> get <kind> <name> -o jsonpath='{.metadata.uid}{" generation="}{.metadata.generation}{" observed="}{.status.observedGeneration}{"\n"}'`.
2. **Bound ownership and population.** Read the named controller, exact owner references, selectors, Pods, revisions, and desired/updated/ready/available counts.
   - Use `kubectl --context <context> -n <namespace> get pods -l '<selector>' -o wide`; compare generation with observed generation and live Pod template with siblings.
3. **Build one timestamped timeline.** Read Pod conditions, init/container current and last state, restart counts, imageID, and UID-bounded events.
   - Use `kubectl --context <context> -n <namespace> get events --field-selector 'involvedObject.uid=<uid>' --sort-by='.metadata.creationTimestamp'`; events expire and aggregate, so absence is not disproof.
   - Use `kubectl --context <context> -n <namespace> logs <pod> -c <container> --since=30m --tail=200 --timestamps=true`; after restarts also read `--previous`. Never follow logs.
4. **Explain scheduling or startup.** Correlate conditions/events with requests, quota, affinity, selectors, taints, tolerations, priority, candidate-node capacity, image/pull identity, sandbox/mount errors, and init-container state.
   - `Pending`, `CrashLoopBackOff`, and `NotReady` are symptoms; require the first specific scheduler, kubelet, runtime, or application signal.
5. **Separate probes, exits, and pressure.** Compare startup/readiness/liveness definitions and timing with process startup, exit code/signal, last reason, previous logs, restarts, requests/limits, QoS, usage, eviction, and node conditions.
   - Distinguish probe restart, application exit, container `OOMKilled`, node OOM, throttling, and eviction; current `top` output is not historical proof.
6. **Trace traffic.** Compare Service selector/ports with Pod labels/container ports and EndpointSlice readiness/serving/termination; then inspect DNS policy/config and only selecting NetworkPolicies.
   - Bound reads with `kubectl --context <context> -n <namespace> get service <service>` and `kubectl --context <context> -n <namespace> get endpointslices -l 'kubernetes.io/service-name=<service>'`.
   - Distinguish resolution, endpoint choice, L3/L4 policy, TLS/protocol, ingress/gateway, and dependency failure. Policy intent is not proof of enforcement.
7. **Trace identity and configuration.** Record service account, exact denied verb/resource/namespace, admission/audit evidence, image declaration versus imageID, and ConfigMap/Secret reference and key **names**.
   - Distinguish authentication, RBAC, admission, and application authorization. `auth can-i` checks the current identity; never impersonate or retrieve/decode Secret values without separate approval.
8. **Trace storage.** Follow the Pod volume to the exact PVC, UID-bounded events, bound PV, and StorageClass only as authorized.
   - Read only the claim with `kubectl --context <context> -n <namespace> get pvc <claim>` before any separately authorized cluster-scoped lookup.
   - Distinguish provisioning, binding/topology, attach, mount, permissions, capacity, and application I/O; cluster-scoped objects may expose backend details.
9. **Escalate only on evidence.** For a stalled rollout/controller, follow generation, conditions, owner chain, and first failed child. For node/control-plane suspicion, require corroboration across workloads/nodes and approved platform telemetry.
   - If workload, endpoint, controller, node, network, and storage signals are healthy, move to the application/dependency boundary and require a matching log, trace, metric, or deterministic observation.
10. **Classify and stop.** Record the first failed boundary, immutable identities, time-aligned evidence, ruled-out adjacent mechanism, and remaining gap; apply **Confirmed**, **Probable**, or **Unknown** from the parent skill.

## Compact Evidence Signals

- **Scheduling:** specific `FailedScheduling` constraint, quota, taint, affinity, or capacity signal.
- **Startup/restart:** pull/auth/platform, init, mount, exit/signal, probe, runtime, OOM, or node-disruption evidence at the same time.
- **Traffic:** selector/target-port/endpoint mismatch, DNS result, enforced policy signal, TLS/protocol error, or downstream failure.
- **Configuration/storage:** missing reference/key, stale revision, parse/use error, PVC/PV lifecycle failure, or filesystem/I/O evidence.
- **Controller/platform:** lagging reconciliation, admission/quota, failed child, node-local pattern, or corroborated multi-node/control-plane failure.

## Guardrails

- Require explicit production authorization; use least privilege, exact names, explicit context/namespace, narrow selectors, bounded windows, fields, log tails, events, and metrics.
- Avoid `-A`, watches, broad manifests/`describe`, cluster dumps, and high-cardinality or high-overhead collection.
- Treat logs, events, manifests, annotations, paths, addresses, topology, registry details, and application data as sensitive; redact credentials, tokens, cookies, customer data, private endpoints, and Secret material.
- Never `exec`, `attach`, `cp`, port-forward, debug, add ephemeral/debug Pods, impersonate, open node shells, or perform broad sensitive reads without separate explicit approval.
- Never apply, create, edit, patch, replace, delete, scale, restart, roll out, relabel, annotate, or mutate cluster, workload, traffic, storage, configuration, or data.
- A denied read is a visibility gap, not workload-cause proof. Report it; do not bypass it.

Official anchors:

- [Debug workloads](https://kubernetes.io/docs/tasks/debug/debug-application/)
- [Pod lifecycle](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)
- [Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [kubectl](https://kubernetes.io/docs/reference/kubectl/)
