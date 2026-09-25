---
name: skilled
description: Use GPT-6 Astra to plan and review substantial software work while a native GPT-5.6 Sol xhigh custom agent implements, tests, and debugs one complete Work Order. Use for bounded multi-file builds, features, migrations, and refactors. Skip simple direct edits and plan-only requests.
---

# SKILLED: Astra → Sol xhigh → Astra

Use only Codex Desktop native subagents. Prefer the installed
`skilled_sol_worker` role, which pins `gpt-5.6-sol` with
`model_reasoning_effort = "xhigh"`. If Desktop does not expose that role, use the
native fallback defined below. Do not invoke `codex exec`, a Router, API key,
external provider, or separate worker CLI.

## 1. Orient

Read repository guidance, the request, current Git/workspace state, and any existing
design. Preserve pre-existing changes. Keep a trivial edit in the parent session.
For substantial implementation, state what Astra will decide and what Sol will own.

## 2. Check the native runtime

Read `runtime.json` and `references/routing.md`. Run `scripts/doctor.py` against
the same `CODEX_HOME` when current capability evidence is absent or may have
changed. Confirm the parent is Astra and determine whether the named worker role
is exposed to the current Desktop task. A catalog check proves availability and
effort support; it does not prove role discovery or task completion.

## 3. Decide architecture and acceptance

Read `references/planning.md`. Reuse an approved plan. Otherwise, Astra resolves
material product and architecture choices, interfaces, failure behavior, risks,
and measurable acceptance criteria before delegation. Ask the user only when a
material unresolved choice cannot be derived from the repository or request.

## 4. Write a complete Work Order

Use `templates/task-brief.md`. Include goal, non-goals, workspace, baseline,
relevant files and architecture, contracts that must remain stable, allowed
changes, acceptance criteria, checks, existing authorization, and decisions that
must return to Astra. Bundle internal discovery, implementation, tests, debugging,
and runtime/visual verification. Do not split work into tiny status steps.

Use `templates/plan.json` and `scripts/validate_plan.py` when a machine-readable
multi-phase plan helps. The schema models dependencies and workspace overlap; it
does not impose a fixed worker count or correction limit.

For a machine-checkable handoff/review record, fill `templates/run-record.json`
and run `scripts/validate_run.py <record>`. This validates success, failure
propagation, acceptance coverage, actual-diff review, and correction packaging;
it does not execute the worker or decide whether the evidence is true.

## 5. Dispatch and wait

Read `references/execution.md`. First spawn the installed `skilled_sol_worker`
through the native Desktop subagent tool without model overrides. If the tool
rejects that role as unknown or unavailable, retry the same complete Work Order
through a native spawn with `agent_type` omitted, `model = "gpt-5.6-sol"`,
`reasoning_effort = "xhigh"`, and `fork_turns = "none"` or a positive bounded
turn count. Do not use a built-in fixed-model role for this fallback. Record which
dispatch path was used and distinguish requested parameters from host-observed
model evidence. Let the child complete its internal test/fix loop. Do not overlap
edits in child-owned paths or poll a healthy run. Continue or message the same
child when the host returns a bounded wait or Astra resolves a blocker.

## 6. Review the real result

Read `references/review.md`. Treat the worker report as a claim. Inspect all actual changed
and untracked files against the captured baseline. Map acceptance criteria
to code and evidence; check out-of-scope changes, regressions, test quality,
security, and reliability. Run targeted independent checks where evidence is
missing or integration creates new risk.

Accept when the implementation and evidence satisfy the Work Order. Otherwise,
batch the concrete findings into one correction package and send it to the same worker
when practical. Continue until accepted or an external decision/blocker is
identified; do not enforce an invented correction count.

## 7. Finish

Integrate only within the user's existing Git and production authorization. Record
the dispatch path and parameters, any host-observed child model/effort, changed
files, checks, review decision, corrections, and remaining limits. Never report a
requested model as observed evidence or infer savings from task count or elapsed
time.
