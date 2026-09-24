# Astra review and correction

Worker completion means ready for review. Compare the actual workspace with the
captured baseline, including untracked files and pre-existing edits. Do not use the
worker's summary as a substitute for the patch.

Review in one consolidated pass:

- Map each acceptance criterion to implementation and evidence.
- Confirm contracts, failure behavior, compatibility, and stated non-goals.
- Identify missing behavior, placeholders, work outside scope, and regressions.
- Assess logic, security, authorization, concurrency, cleanup, error handling,
  dependency changes, and test quality.
- Read actual command exits and salient output; distinguish passed, failed, and
  unverified checks.
- Run targeted independent verification where evidence is absent or integration
  creates a plausible risk.

The review decision is `accepted`, `changes_requested`, or `blocked`. When changes
are needed, batch related file-specific findings and expected results into one
correction package when practical. Continue with the same worker so it retains the
implementation context. Re-review the affected diff and checks. The number of
correction passes follows real unresolved findings; SKILLED does not set a fixed
count.
