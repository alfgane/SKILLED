# Changelog

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
