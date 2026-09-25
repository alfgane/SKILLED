# Workflow measurement

The upstream DeepSeek/API price comparison does not describe SKILLED and has been
removed. SKILLED uses the user's native Codex/ChatGPT session, so external-provider
per-token pricing is not an applicable package claim.

Measure a real Astra → Sol → Astra task with:

- task size and acceptance criteria;
- requested parent/worker model and effort, plus separately host-observed values
  when the host exposes them;
- worker dispatch path (`custom_role` or `explicit_model_fallback`);
- Astra turns before dispatch and during review;
- Sol execution/correction turns;
- actual changed implementation/test lines, with generated content excluded;
- commands, exits, runtime/visual evidence, and final review decision;
- any external provider traffic observed (expected: none introduced by SKILLED).

Compare tasks only when their scope and risk are similar. Do not infer savings or
quality from task counts, wall time, model names, or a catalog entry alone.
