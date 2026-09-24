# Validation evidence

SKILLED is based on upstream commit `bcc7f9ea` and replaces the provider-specific
execution seam while retaining Work Orders, Astra acceptance, atomic installation,
backup, guarded undo, structural plan validation, and deterministic packaging.

## Architecture map

| Concern | Upstream | SKILLED |
| --- | --- | --- |
| Planning and acceptance | Astra skill/policy/templates | Preserved and clarified |
| Worker | `astra_flash_builder` | `skilled_sol_worker` |
| Model/effort | Router catalog route/default effort | Custom agent pins `gpt-5.6-sol` / `xhigh` |
| Authentication | External provider credentials | Native `account/read` requires `chatgpt` |
| Catalog | Configured `model_catalog_json` | App-server `model/list(includeHidden: true)` |
| Dispatch | Native subagent role | Native subagent role |
| Result | Report + actual diff + Astra review | Preserved |
| Correction | Batched, fixed default ceiling | Batched without an invented universal ceiling |

The removed ceiling matters because the user's required stopping condition is a
correct, reviewed implementation. A fixed package-wide correction count could
force an incomplete stop even while a useful in-scope recovery remains. The
preferred shape remains one substantial run and one batched correction when that
is enough.

## What offline tests prove

- native account/model/effort response validation;
- rejection of API-key auth, missing Sol, missing xhigh, disabled agents, and
  effective external provider/base URL overrides;
- generated role TOML selects the exact worker and effort;
- no provider, Router, or API-key field enters installed artifacts;
- executable run-record validation covers Work Order completeness, successful
  completion, failure propagation/resume, acceptance evidence, batched correction,
  and mandatory final-diff review;
- dry-run safety, config preservation, atomic rollback, guarded undo, collision
  and symlink defenses, policy preservation, plan validation, and release inventory.

Offline fixtures do not make inference calls. A live read-only doctor verifies the
current machine's account, feature, and model catalog and reports
`capability_preflight_verified: true`. It always reports
`desktop_worker_delegation_verified: false` because app-server inspection is not
a worker run. A native Codex Desktop delegation is required to prove end-to-end
worker completion and output quality.

## Codex Desktop native delegation smoke

On 2026-09-24, a Codex Desktop task used the native `collaboration.spawn_agent`
surface with `model: gpt-5.6-sol` and `reasoning_effort: xhigh`. The child task was
`/root/desktop_sol_smoke`, working in the isolated scratch repository
`work/smoke-target` from baseline commit `b7d3882`.

The worker received one Work Order and needed no correction pass. It implemented a
monthly account report across four files:

- `README.md`
- `ledger/cli.py`
- `ledger/report.py`
- `tests/test_ledger.py`

The worker reported 6/6 passing unit tests. It also ran the sample application's
own CLI:

```text
python -m ledger.cli monthly data/sample.csv 2026-09
{"acme": 3800, "bee": 2300}
```

That command exercised the scratch Python application; it was not `codex exec`.
No Codex CLI worker was used for this Desktop smoke. Astra independently inspected
the actual four-file diff and reran the six tests successfully.

This is direct evidence that the Codex Desktop native spawn surface accepted the
requested Sol model and xhigh effort and completed a reviewed worker delegation.
External provider traffic was not packet-captured, so this record does not claim
network-level routing proof.

The installed `$skilled` skill and `skilled_sol_worker` custom role have not yet
been tested for discovery and automatic loading in a fresh Codex Desktop task after
an app restart. That installed-path smoke remains a separate release validation
step.

## Future task evidence records

For later useful tasks, record the host-observed worker model/effort, working
directory, task/thread identifier, actual diff, command exits, correction packages,
and Astra's acceptance decision. Do not publish private account or repository data.
