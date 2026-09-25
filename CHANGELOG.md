# Changelog

## 2.1.0 - 2026-09-25

- Name the installed skill **Astra OP** in Codex Desktop and invoke it as
  `$astra-op`. The GitHub fork and release package remain named SKILLED.
- Keep the native `skilled_sol_worker` role and its Sol xhigh configuration.
- Remove the previous `$skilled` installation before installing this release
  so only the requested skill name appears in Desktop.

## 2.0.1 - 2026-09-25

- Prefer the installed `skilled_sol_worker` role, then fall back to a Codex
  Desktop native spawn with no fixed agent type and explicit
  `gpt-5.6-sol` / `xhigh` parameters when the role is unavailable.
- Require non-full-history `fork_turns` for the explicit-model fallback and
  record the dispatch path, fallback reason, request parameters, and separately
  observed model evidence in workflow schema 2.
- Correct the earlier Desktop smoke record: it proves a native reviewed
  delegation, while the effective model remained unobserved.
- Record a successful no-role Desktop fallback probe while keeping its effective
  runtime model and effort explicitly unverified.
- Document that an unknown role in an already-running task does not establish
  fresh-process discovery behavior.

## 2.0.0 - 2026-09-24

- Fork the worker seam from DeepSeek/Router routes to the native Codex custom
  agent `skilled_sol_worker` pinned to `gpt-5.6-sol` with `xhigh` reasoning.
- Verify ChatGPT authentication, native multi-agent support, and model/effort
  availability through Codex app-server and CLI capabilities without inference.
- Label that result as capability preflight and explicitly keep Desktop worker
  delegation unverified until a native Codex Desktop run completes.
- Reject effective external provider/base URL overrides and preserve config/auth.
- Rename the installed skill to `$skilled` and generated binding to `runtime.json`.
- Preserve atomic installation, backups, guarded undo, policy merging, Work Orders,
  structural plan validation, final diff review, and deterministic packaging.
- Remove the inherited fixed worker and correction ceilings. Dependency,
  workspace, risk, and actual review findings now determine continuation while
  the preferred workflow remains one substantial Sol run and batched review.
- Remove stale external-provider pricing and benchmark claims.
