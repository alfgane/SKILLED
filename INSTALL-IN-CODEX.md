# Install SKILLED using Codex

Give Codex this repository path and the prompt below:

```text
Install SKILLED from this repository.

Read README.md, install.py, POLICY.md, and WORKER-INSTRUCTIONS.md. Run the
offline tests, then run install.py as a dry run. Review the destinations and,
if they match the documented scope, apply with install.py --apply.

Use the existing native ChatGPT login. The installer must verify account/read,
model/list for gpt-5.6-sol with xhigh, and native multi-agent availability.
Do not add or request an API key, Router, proxy, provider URL, external worker
CLI, or separate runtime. Do not make an inference request during installation.

Preserve config.toml, authentication, root model/effort, global subagent defaults,
sandbox, permissions, and unrelated instructions byte-for-byte. Do not change
settings to make preflight pass. Install only the astra-op skill, the native
skilled_sol_worker role, and the marked policy block. Retain the undo receipt.

Run the installed doctor. Report installed paths, native model/effort evidence,
test results, preserved files, undo receipt, and any runtime limitation. Do not
launch a worker, commit, push, deploy, or publish during setup.
```
