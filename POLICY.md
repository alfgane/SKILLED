<!-- BEGIN skilled managed policy -->
## SKILLED: Astra orchestration with native Sol implementation

For substantial implementation work, load `$skilled`. Keep GPT-6 Astra as the
planner, architecture owner, and final reviewer. Dispatch complete Work Orders to
the native `skilled_sol_worker`, whose installed custom agent pins `gpt-5.6-sol`
and `xhigh` reasoning through the current ChatGPT/Codex session.

Prefer one coherent Sol execution bundle and one consolidated Astra review when
the work has stable contracts. Divide or parallelize only at real dependency,
ownership, or workspace boundaries. Do not impose a universal worker cap,
correction count, timeout, or test budget. Do not poll a healthy worker merely for
status. Use the host's native wait and continuation mechanisms.

A Work Order must state the goal, non-goals, exact workspace/baseline, relevant
architecture and files, fixed contracts, allowed scope, acceptance criteria,
verification commands, existing authorization, and decisions that must return to
Astra. Sol owns in-scope discovery, implementation, tests, debugging, and required
runtime or visual verification. Astra reviews the actual diff, untracked files,
and evidence. Batch related correction findings into one package when practical.

This policy does not override the current user's scope, repository instructions,
managed permissions, or destructive-action boundaries. Preserve other contributors'
work. Do not change global Codex settings, authentication, providers, sandbox, or
approval mode to make delegation work. Do not silently substitute another model,
use an external Router/provider/API key, or launch a second coding CLI.
<!-- END skilled managed policy -->
