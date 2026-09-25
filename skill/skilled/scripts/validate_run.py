#!/usr/bin/env python3
"""Validate a SKILLED Work Order, worker result, and Astra review record."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


class RunError(ValueError):
    pass


def mapping(value: object, label: str) -> dict:
    if not isinstance(value, dict):
        raise RunError(f"{label} must be an object.")
    return value


def text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise RunError(f"{label} must be a nonempty string.")
    return value


def strings(value: object, label: str, *, allow_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not allow_empty):
        raise RunError(f"{label} must be {'a' if not allow_empty else 'an'} list of strings.")
    if not all(isinstance(item, str) and item.strip() for item in value):
        raise RunError(f"{label} contains an empty or non-string value.")
    return value


def validate(payload: object) -> dict:
    root = mapping(payload, "run record")
    if root.get("schema_version") != 2:
        raise RunError("Expected schema_version 2.")

    order = mapping(root.get("work_order"), "work_order")
    task_id = text(order.get("id"), "work_order.id")
    for key in ("goal", "workspace", "baseline", "architecture"):
        text(order.get(key), f"work_order.{key}")
    for key in ("contracts", "allowed_paths", "acceptance", "tests", "out_of_scope", "escalate_if"):
        strings(order.get(key), f"work_order.{key}")

    dispatch = mapping(root.get("dispatch"), "dispatch")
    dispatch_path = dispatch.get("path")
    if dispatch_path not in {"custom_role", "explicit_model_fallback"}:
        raise RunError("dispatch.path must be custom_role or explicit_model_fallback.")
    if dispatch.get("requested_model") != "gpt-5.6-sol":
        raise RunError("dispatch.requested_model must be gpt-5.6-sol.")
    if dispatch.get("requested_reasoning_effort") != "xhigh":
        raise RunError("dispatch.requested_reasoning_effort must be xhigh.")
    fork_turns = text(dispatch.get("fork_turns"), "dispatch.fork_turns")
    agent_type = dispatch.get("agent_type")
    fallback_reason = text(dispatch.get("fallback_reason"), "dispatch.fallback_reason")
    if dispatch_path == "custom_role":
        if agent_type != "skilled_sol_worker":
            raise RunError("The custom_role path must use skilled_sol_worker.")
        if fallback_reason != "not_applicable":
            raise RunError("The custom_role path must mark fallback_reason as not_applicable.")
    else:
        if agent_type != "omitted":
            raise RunError("The explicit_model_fallback path must omit agent_type.")
        if fork_turns == "all" or not (fork_turns == "none" or re.fullmatch(r"[1-9][0-9]*", fork_turns)):
            raise RunError("The explicit_model_fallback path requires fork_turns none or a positive turn count.")
        if fallback_reason == "not_applicable":
            raise RunError("The explicit_model_fallback path must record why the custom role was unavailable.")
    observed_model = text(dispatch.get("observed_model"), "dispatch.observed_model")
    observed_effort = text(dispatch.get("observed_reasoning_effort"), "dispatch.observed_reasoning_effort")

    worker = mapping(root.get("worker_result"), "worker_result")
    if text(worker.get("task_id"), "worker_result.task_id") != task_id:
        raise RunError("worker_result.task_id does not match the Work Order.")
    status = worker.get("status")
    if status not in {"ready_for_review", "blocked", "failed"}:
        raise RunError("worker_result.status is invalid.")
    strings(worker.get("changed_files"), "worker_result.changed_files", allow_empty=True)
    checks = worker.get("checks")
    if not isinstance(checks, list):
        raise RunError("worker_result.checks must be a list.")
    for index, check_value in enumerate(checks):
        check = mapping(check_value, f"worker_result.checks[{index}]")
        text(check.get("command"), f"worker_result.checks[{index}].command")
        if type(check.get("exit_code")) is not int:
            raise RunError(f"worker_result.checks[{index}].exit_code must be an integer.")
        text(check.get("result"), f"worker_result.checks[{index}].result")
    acceptance = worker.get("acceptance_results")
    if not isinstance(acceptance, list):
        raise RunError("worker_result.acceptance_results must be a list.")
    expected = set(order["acceptance"])
    observed: set[str] = set()
    states: list[str] = []
    for index, item_value in enumerate(acceptance):
        item = mapping(item_value, f"worker_result.acceptance_results[{index}]")
        criterion = text(item.get("criterion"), f"worker_result.acceptance_results[{index}].criterion")
        if criterion in observed:
            raise RunError("worker_result contains a duplicate acceptance criterion.")
        observed.add(criterion)
        state = item.get("status")
        if state not in {"pass", "fail", "unverified"}:
            raise RunError("An acceptance result has an invalid status.")
        states.append(state)
        text(item.get("evidence"), f"worker_result.acceptance_results[{index}].evidence")
    if observed != expected:
        raise RunError("worker_result must report every Work Order acceptance criterion exactly once.")
    strings(worker.get("failures"), "worker_result.failures", allow_empty=True)
    resume_action = worker.get("resume_action")
    if status in {"blocked", "failed"}:
        if not worker["failures"]:
            raise RunError("A blocked or failed worker result must propagate at least one failure.")
        text(resume_action, "worker_result.resume_action")

    review = mapping(root.get("review"), "review")
    if text(review.get("task_id"), "review.task_id") != task_id:
        raise RunError("review.task_id does not match the Work Order.")
    if review.get("diff_reviewed") is not True:
        raise RunError("Astra must review the actual diff before recording a decision.")
    decision = review.get("decision")
    if decision not in {"accepted", "changes_requested", "blocked"}:
        raise RunError("review.decision is invalid.")
    strings(review.get("findings"), "review.findings", allow_empty=True)
    correction = strings(review.get("correction_package"), "review.correction_package", allow_empty=True)
    if decision == "accepted" and (status != "ready_for_review" or any(value != "pass" for value in states)):
        raise RunError("Astra cannot accept a worker result with failed or unverified acceptance criteria.")
    if decision == "changes_requested" and not correction:
        raise RunError("changes_requested requires a batched correction_package.")

    return {
        "status": "workflow-contract-valid",
        "task_id": task_id,
        "dispatch_path": dispatch_path,
        "model_observed": observed_model == "gpt-5.6-sol",
        "reasoning_effort_observed": observed_effort == "xhigh",
        "worker_status": status,
        "review_decision": decision,
        "checks_recorded": len(checks),
        "corrections_recorded": len(correction),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(json.loads(args.record.read_text(encoding="utf-8"))), indent=2))
        return 0
    except (OSError, json.JSONDecodeError, RunError) as exc:
        print(f"RUN RECORD INVALID: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
