# Execution and workspace ownership

Capture the repository root, branch/HEAD when Git exists, tracked and staged diffs,
and untracked-file inventory before dispatch. Do not stash, reset, commit, or copy
private files merely to create a baseline. Tell Sol exactly which pre-existing
changes are visible and which paths it owns.

Spawn `skilled_sol_worker` through the host's native agent tool and provide the full
Work Order plus exact working directory. Do not pass an explicit model or effort
override; the installed role owns `gpt-5.6-sol` and `xhigh`. Use the same workspace
when the worker must see uncommitted changes. A new Git worktree starts from a Git
commit and does not contain the parent's uncommitted state.

While Sol owns a path, Astra and other writers do not edit it. A separate agent
thread is not workspace isolation. Before parallel dispatch, verify independent
writable scopes, dependencies, generated outputs, lockfiles, schemas, ports, and
process state. Choose concurrency from those facts and the approved plan rather
than a package-wide cap.

Let Sol perform its internal discover/code/test/debug loop. Use native wait and
continuation tools. A bounded wait returning without completion is a reason to
continue waiting, not proof of failure. Send a targeted update when Astra resolves
a real blocker. Preserve a checkpoint when a host turn boundary interrupts work.

Sol returns `ready_for_review`, `blocked`, or `failed`. A blocked/failed result must
include the last concrete failure and next recovery action. Astra decides whether
to fix the contract/environment, continue the same worker, or revise the plan.

Git operations, deployment, publication, credentials, and production mutations
follow the user's existing authorization. SKILLED adds no authorization.
