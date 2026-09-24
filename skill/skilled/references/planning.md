# Planning and Work Orders

Astra decides the architecture before delegation. Reuse an approved design when
one exists. Otherwise, establish the smallest stable contract that lets Sol own a
substantial implementation run without repeatedly returning for routine choices.

A complete Work Order contains:

1. Goal and user-visible outcome.
2. Non-goals and boundaries.
3. Exact workspace and captured baseline, including pre-existing changes.
4. Relevant files, architecture, data flow, and neighboring patterns.
5. Fixed interfaces, compatibility requirements, and failure semantics.
6. Allowed changes and systems that remain outside scope.
7. Checkable acceptance criteria, including negative and boundary behavior.
8. Commands and runtime/visual checks that produce evidence.
9. Existing authorization for Git, network, dependency, or production actions.
10. Decisions that must return to Astra rather than be invented by the worker.

Make one bundle large enough to include internal discovery, code, tests, fixes, and
verification. Split only where dependencies, workspace ownership, acceptance, or a
material unresolved contract require it. Parallel groups are valid only when their
workspaces and writable scopes are genuinely independent.

The optional JSON plan validates structure. It does not decide how many workers to
run, limit corrections, approve commands, or prove the design is correct.
