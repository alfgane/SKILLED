# Troubleshooting

## Codex CLI or app-server cannot be inspected

Confirm `codex` is on PATH and current enough to provide `app-server`,
`account/read`, `model/list`, and `features list`. SKILLED does not install or
upgrade Codex.

## ChatGPT login is required

The installer rejects `account.type = apiKey` and a missing account. Run
`codex login` using ChatGPT, then retry. Do not paste credentials into chat.

## Sol or xhigh is unavailable

Availability comes from the current account's app-server catalog. The exact
`gpt-5.6-sol` entry must advertise `xhigh`. Update Codex or resolve account/workspace
model access. Do not rename another model or lower reasoning to bypass preflight.

## External provider override is rejected

The effective config/profile cannot select a nonnative `model_provider` or set
`openai_base_url`; either could route the child away from the ChatGPT subscription.
SKILLED reports the setting class without printing URLs or credentials and never
edits it automatically.

## Native agents are disabled

`codex features list` must report `multi_agent ... true`, and `[agents].enabled`
must not be false. Repair/update the environment or change your own configuration
deliberately; the installer does not override it.

## Role or skill is missing after installation

Confirm apply completed, then fully quit/reopen Codex. Expected files are
`~/.agents/skills/skilled/SKILL.md` and
`$CODEX_HOME/agents/skilled_sol_worker.toml`.

If the current task reports `unknown agent_type 'skilled_sol_worker'`, its agent
registry may predate the installation. This does not prove that a fresh Desktop
process will also miss the role. Continue the current Work Order through the
documented native fallback: omit `agent_type`, explicitly request
`gpt-5.6-sol` / `xhigh`, and use `fork_turns = "none"` or a positive bounded turn
count. Do not use a built-in fixed-model role or `codex exec`.

## Existing package files conflict

The installer refuses differing package-owned files unless `--replace` is used.
Review the existing files first. Replacement is backed up in the receipt.

## Undo refuses

An installed file changed after installation or a backup no longer matches the
receipt. Preserve the newer edit and reconcile manually; guarded undo will not
overwrite it.
