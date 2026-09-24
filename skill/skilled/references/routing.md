# Native Codex routing

SKILLED uses a standalone custom agent at
`$CODEX_HOME/agents/skilled_sol_worker.toml`:

```toml
name = "skilled_sol_worker"
model = "gpt-5.6-sol"
model_reasoning_effort = "xhigh"
```

Codex custom-agent settings take precedence for that spawned session. Sandbox,
approval, and other session settings inherit from the parent because SKILLED does
not override them.

The installer opens one read-only `codex app-server` connection, performs the
required `initialize` handshake, then calls:

- `account/read` with `refreshToken: false`; `account.type` must be `chatgpt`;
- paginated `model/list` with `includeHidden: true`; the exact model must exist and
  list `xhigh` in `supportedReasoningEfforts`.

It also requires `multi_agent ... true` from `codex features list` and refuses an
effective `model_provider`/`openai_base_url` that would bypass native ChatGPT
routing. No inference endpoint is called. No account identifiers, email, tokens,
or credential content are printed or stored.

`runtime.json` records only the selected model, effort, role, catalog source,
authentication class, and inspected profile. The doctor report names this result
`native-capability-preflight-ready`, sets `capability_preflight_verified` to true,
and keeps `desktop_worker_delegation_verified` false. Neither the binding nor the
doctor claims that a worker ran. For a real Codex Desktop task, retain the
host-observed child model and effort plus its changed files and test evidence.

If the named role is unavailable after install, fully restart Codex. Do not work
around it with an external CLI, provider, or API key.

Before dispatch in a target repository, inspect its project `.codex/config.toml`
and applicable managed overrides for an external provider or base URL that could
replace native routing. The personal installer cannot prove every future project's
configuration.
