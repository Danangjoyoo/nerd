# Terraform Diagnosis

## Scope and Provenance

- Use for the Terraform boundary; pair with one parent diagnosis type.
- Record exact wrapper/CLI, `terraform version`, root module, cwd, CI/wrapper version, and failing phase.
- Capture `required_version`, provider constraints, `.terraform.lock.hcl` selections/checksums, and module sources/versions.
- Capture backend type and non-secret key, active `terraform workspace show`, and CLI-versus-HCP workspace identity; never switch workspaces.
- Record variable precedence, loaded variable-file names, provider aliases, account/project/region/endpoint, and credential-source names—not values.
- Compare only runs with matching CLI, lockfile, modules, backend, workspace, variables, and provider versions.
- Treat `terraform` below as the repository-approved wrapper or the exact recorded binary.

## Diagnose

1. **Anchor.** Capture the first causal diagnostic, full resource/module address, expected result, exact sanitized command, exit status, and phase.
2. **Check configuration.** Run `terraform fmt -check -diff`; inspect affected `terraform`, provider, module, variable, local, resource, `moved`, and `import` blocks. Formatting proves style only.
3. **Validate.** In an initialized directory, run `terraform validate`; it checks syntax/internal consistency—not variables, state, credentials, APIs, or remote objects.
4. **Gate initialization.** Prefer existing artifacts and caches.
   - If authorized for downloads, provider execution, and disposable output, run `TF_DATA_DIR=<dir> terraform init -backend=false -input=false -lockfile=readonly`.
   - Validate with the same `TF_DATA_DIR`; never update the lockfile to make diagnosis pass.
5. **Trace the model.**
   - Inspect references and module inputs/outputs; use `terraform providers`, then `terraform graph` for disputed edges.
   - Use `terraform providers schema -json` only in a trusted initialized environment; retain only relevant sanitized fields.
6. **Inspect addresses/state carefully.** With authorization for the exact backend/workspace, use read-only `terraform state list` or `terraform state show <address>` only when state identity/value is the discriminator; state output is sensitive.
7. **Gate plans.** Prefer an existing saved run/plan. A new plan requires approval for backend access, workspace, credentials, provider/API reads, data sources, locking, and local cache; avoid `-out` unless a secured artifact is required.
   - `terraform plan -refresh=false -input=false`: emphasize configuration versus prior state; it can still access backend, lock state, invoke providers, and read data sources.
   - `terraform plan -refresh-only -input=false`: emphasize prior state versus provider-read remote objects; it performs remote reads and must never be applied.
   - Normal plan: combined evidence; it does not alone separate configuration intent, state, remote drift, or provider normalization.
8. **Classify and stop.** Apply the parent **Confirmed / Probable / Unknown** gate; name the first causal boundary and any missing discriminator. Diagnose only.

## Signals

- **Parse/type:** first diagnostic, source span, core version, validation, locked provider schema; separate language errors from schema rejection.
- **Module/unknown value:** input type/nullability/validation, caller, module version, output path, plan-time versus apply-time value; unknown is not drift.
- **Address/dependency:** full address, stable `count`/`for_each` keys, references, `depends_on`, graph edge; file order proves nothing.
- **Provider/plugin:** source/version/checksum, platform, protocol/install diagnostics, alias inheritance, schema field; distinguish wrong schema from install/provider failure.
- **Backend/workspace:** backend key, initialization metadata, active CLI/HCP workspace, run identity; never mutate routing to test a theory.
- **Unexpected diff:** compare configuration → state and state → remote object; inspect lifecycle, computed fields, and normalization before calling drift.
- **Move/import/replace:** `moved`/`import` blocks, old/new addresses, identity, lifecycle, and replacement reason; observe only.
- **API/auth:** sanitized provider diagnostic, identity source, scope, endpoint/region/account, expiry, network, and rate-limit evidence.

## Guardrails

- Read-only and offline-first: prefer configuration, lockfiles, existing diagnostics, saved plans, and cached evidence.
- Never run `apply`, `destroy`, `import`, `refresh`, `taint`, `force-unlock`, workspace mutation, backend migration/reconfiguration, `state mv/rm/push`, or any state/config/lockfile mutation.
- Treat `init` as local mutation plus possible network/credential use; treat plan, refresh, provider, API, and state reads as remote-sensitive and potentially locking.
- Never bypass locks or use targeting to manufacture a clean plan. Report an unauthorized evidence gap.
- Never print, commit, or broadly retain state, plan, generated JSON, provider debug logs, environment values, or credentials; `terraform show -json` may expose plaintext secrets.
- Never replay remote changes. Recommend—but do not perform—the smallest correction after cause classification.

## Official Anchors

- [Terraform CLI](https://developer.hashicorp.com/terraform/cli) · [State](https://developer.hashicorp.com/terraform/language/state) · [Plan](https://developer.hashicorp.com/terraform/cli/commands/plan)
