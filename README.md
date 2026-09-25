# SKILLED

**Astra plans and reviews. GPT-5.6 Sol xhigh implements, tests, and debugs.**

SKILLED packages **Astra OP**, a native Codex Desktop skill for substantial
software work. Its display name is **Astra OP** and its invocation is
`$astra-op`. It keeps GPT-6 Astra responsible for scope, architecture, acceptance, and consolidated
review, then dispatches one complete Work Order to GPT-5.6 Sol with xhigh
reasoning. It prefers the installed named role and has a native Desktop fallback
that explicitly requests the same model and effort.

```text
Astra: inspect → decide contracts → write Work Order
                         ↓
Sol xhigh: discover in scope → implement → test → debug → report
                         ↓
Astra: inspect diff + evidence → accept or send one batched correction package
```

The worker runs through Codex Desktop's native subagent surface and the user's
current ChatGPT login. The package never uses `codex exec` or another CLI to run
the worker. There is no Router, provider URL, API key, proxy, external worker CLI,
or separate API billing configuration in this package.

## What the fork preserves

- Astra remains the orchestrator and final reviewer.
- Work Orders carry goal, scope, relevant files, architecture, fixed contracts,
  acceptance criteria, checks, exclusions, permissions, and escalation points.
- Sol receives a substantial implementation bundle, owns its internal test/fix
  loop, and returns a patch plus evidence.
- The named custom role is preferred. If the current Desktop task does not expose
  it, the same Work Order is sent through a native spawn with no fixed agent type
  and explicit `gpt-5.6-sol` / `xhigh` parameters.
- Astra reviews actual changed files and test output, not the worker summary alone.
- Related review findings are batched into a correction package.
- Installation is previewable, atomic, backed up, and guarded on undo.

SKILLED does not impose a universal worker count, correction count, task duration,
or test budget. Astra chooses the execution shape from the approved plan, real
workspace isolation, dependencies, and risk. The normal cost-saving shape remains
one coherent Sol run followed by one consolidated Astra review.

## Requirements

1. Python 3.11 or newer.
2. Codex Desktop with native agents enabled.
3. The Codex backend executable available to the installer for read-only
   capability inspection.
4. A native ChatGPT login in that Codex environment.
5. `gpt-5.6-sol` returned by `codex app-server` `model/list`.
6. `xhigh` listed in that model's `supportedReasoningEfforts`.
7. GPT-6 Astra selected for the parent task.

The installer verifies items 2–6 without making an inference request. For this
preflight only, it starts the backend executable's `codex app-server`, calls
`account/read` and `model/list`, and runs `codex features list` for the native
multi-agent feature. These are read-only capability checks; the executable is
not the worker execution environment. Worker execution stays inside Codex
Desktop. The installer never reads or asks for an API key.

## Install

Run from the repository root:

```sh
python -B -m unittest discover -s tests -v
python -B install.py
python -B install.py --apply
```

The first installer command is a dry run. Apply writes only:

| Location | Content |
| --- | --- |
| `~/.agents/skills/astra-op/` | Skill, references, templates, doctor, validator, and generated `runtime.json` |
| `$CODEX_HOME/agents/skilled_sol_worker.toml` | Native custom agent pinned to `gpt-5.6-sol` + `xhigh` |
| `$CODEX_HOME/AGENTS.md` or nonempty `AGENTS.override.md` | Marked SKILLED policy block |
| `$CODEX_HOME/skilled-install-backups/` | Before-images and guarded undo receipt |

`config.toml`, authentication, global subagent defaults, root model, permissions,
and sandbox settings are not changed. The installed role inherits the parent turn's
permissions and sandbox.

For a nondefault location, pass `--home` and `--codex-home`. The app-server check
runs against that `CODEX_HOME`. Use `--no-policy` for a skill/role-only install.
Use `--replace` only after reviewing an existing package-owned file.

If upgrading from an installation of `$skilled`, use its original undo receipt
to remove that skill first. The new installer does not silently remove a
previously installed skill.

Undo uses the exact receipt printed by apply:

```sh
python -B install.py --undo C:\path\to\receipt.json
python -B install.py --undo C:\path\to\receipt.json --apply
```

Undo stops if an installed file changed afterward, so later user edits are not
overwritten.

## Use

Fully quit and reopen Codex after installation, select Astra as the parent, then:

```text
$astra-op Implement the approved design in docs/plan.md. Create one complete Work
Order for Sol xhigh, let it implement and run its test/fix loop, then review the
actual diff and evidence in one consolidated pass.
```

Run the doctor at any time:

```sh
python -B skill/astra-op/scripts/doctor.py
```

Validate an optional machine-readable Work Order/result/review record with:

```sh
python -B skill/astra-op/scripts/validate_run.py path/to/run-record.json
```

A passing doctor proves only the read-only installer preflight: native ChatGPT
authentication, native-agent availability, and the model/effort catalog entry.
Its report sets `capability_preflight_verified` to true and
`desktop_worker_delegation_verified` to false. Only a completed native worker run
inside Codex Desktop can establish the latter. The first real Desktop task should
retain the dispatch path, request parameters, any separately host-observed child
model/effort, and final diff/test evidence in its review record. Requesting a
model does not by itself prove which model the host ran.

## Validation and release

- [Architecture and runtime evidence](docs/VALIDATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Workflow measurement guidance](docs/BENCHMARK.md)
- [Release procedure](docs/RELEASE.md)

Build or check the deterministic inventory:

```sh
python -B scripts/release.py
python -B scripts/release.py --check
python -B scripts/release.py --zip
```

This fork is based on `ethanplusai/astra-flash-orchestrator` at commit
`bcc7f9eaee051126c0ce821a55194d0b20425b22`. See [SOURCES.md](SOURCES.md).
