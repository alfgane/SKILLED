# Contributing

Keep changes focused on the Astra → native Sol xhigh → Astra workflow, Work Order
quality, installer safety, or evidence. Reuse existing utilities, avoid new
dependencies, and preserve user configuration and unrelated work.

Run:

```sh
python -B -m unittest discover -s tests -v
python -B scripts/release.py --check
```

Behavior changes need tests that exercise outcomes, including failure paths.
Label live app-server checks separately from offline fixtures. Do not commit auth,
account data, local config, receipts, backups, private logs, or task content.
