# Release procedure

Suggested repository name: `SKILLED`

Suggested description:

> Astra plans and reviews; native GPT-5.6 Sol xhigh implements, tests, and debugs through the user's Codex subscription.

Before release:

1. Run the full offline suite.
2. Run the live read-only doctor on a supported Codex environment.
3. Review `rg -n -i "deepseek|openrouter|codex router|api[_ -]?key" .` and confirm
   any hit is historical, negative, or a test fixture.
4. Review docs and validation claims against actual evidence.
5. Regenerate and check `MANIFEST.sha256`.
6. Build the deterministic ZIP with `python -B scripts/release.py --zip`.

The release script does not commit, push, upload, or publish.
