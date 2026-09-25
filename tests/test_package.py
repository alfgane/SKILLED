from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skill" / "astra-op" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(ROOT))

import install
import native_codex
from native_codex import (
    ROLE,
    SKILL,
    WORKER_EFFORT,
    WORKER_MODEL,
    SetupError,
    check_multi_agent,
    inspect,
    inspect_config,
    query_app_server,
    validate_capabilities,
)
from validate_plan import PlanError, validate
from validate_run import RunError, validate as validate_run


def native_result() -> dict:
    return {
        "authentication": "ChatGPT subscription",
        "worker_model": WORKER_MODEL,
        "worker_effort": WORKER_EFFORT,
        "worker_display_name": "GPT-5.6 Sol",
        "worker_hidden": False,
    }


def fake_capability(_binary: str, _home: Path) -> dict:
    return native_result()


def fake_agents(_binary: str, _home: Path) -> None:
    return None


class NativeCapabilityTests(unittest.TestCase):
    def model(self, efforts=("low", "xhigh")) -> dict:
        return {
            "id": WORKER_MODEL,
            "model": WORKER_MODEL,
            "displayName": "GPT-5.6 Sol",
            "supportedReasoningEfforts": [{"reasoningEffort": value} for value in efforts],
        }

    def test_chatgpt_sol_xhigh_is_accepted(self):
        result = validate_capabilities({"account": {"type": "chatgpt", "email": "private@example.test"}}, [self.model()])
        self.assertEqual(result["worker_model"], WORKER_MODEL)
        self.assertEqual(result["worker_effort"], "xhigh")
        self.assertNotIn("email", result)

    def test_api_key_auth_is_rejected(self):
        with self.assertRaisesRegex(SetupError, "API key"):
            validate_capabilities({"account": {"type": "apiKey"}}, [self.model()])

    def test_missing_chatgpt_login_is_rejected(self):
        with self.assertRaisesRegex(SetupError, "ChatGPT login"):
            validate_capabilities({"account": None}, [self.model()])

    def test_missing_or_duplicate_sol_is_rejected(self):
        with self.assertRaisesRegex(SetupError, "exactly one"):
            validate_capabilities({"account": {"type": "chatgpt"}}, [])
        with self.assertRaisesRegex(SetupError, "exactly one"):
            validate_capabilities({"account": {"type": "chatgpt"}}, [self.model(), self.model()])

    def test_missing_xhigh_is_rejected(self):
        with self.assertRaisesRegex(SetupError, "does not advertise xhigh"):
            validate_capabilities({"account": {"type": "chatgpt"}}, [self.model(("high", "max"))])

    def test_model_field_can_identify_entry(self):
        model = self.model()
        model["id"] = "catalog-row-id"
        self.assertEqual(validate_capabilities({"account": {"type": "chatgpt"}}, [model])["worker_model"], WORKER_MODEL)

    def test_app_server_probe_uses_account_and_paginated_model_list(self):
        calls = []

        class FakeClient:
            def __init__(self, *_args):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                pass

            def request(self, request_id, method, params=None):
                calls.append((request_id, method, params))
                if method == "account/read":
                    return {"account": {"type": "chatgpt", "email": "do-not-store@example.test"}}
                if request_id == 10:
                    return {"data": [{"model": "other"}], "nextCursor": "next"}
                return {"data": [NativeCapabilityTests().model()], "nextCursor": None}

        with patch.object(native_codex, "AppServerClient", FakeClient):
            result = query_app_server("codex", Path("."))
        self.assertEqual(result["worker_effort"], "xhigh")
        self.assertEqual(calls[0][1:], ("account/read", {"refreshToken": False}))
        self.assertEqual(calls[1][2], {"limit": 100, "includeHidden": True})
        self.assertEqual(calls[2][2]["cursor"], "next")

    def test_multi_agent_feature_must_be_enabled(self):
        ok = subprocess.CompletedProcess([], 0, "multi_agent  stable  true\n", "")
        with patch.object(native_codex.subprocess, "run", return_value=ok):
            check_multi_agent(sys.executable, Path("."))
        off = subprocess.CompletedProcess([], 0, "multi_agent  stable  false\n", "")
        with patch.object(native_codex.subprocess, "run", return_value=off):
            with self.assertRaisesRegex(SetupError, "does not report"):
                check_multi_agent(sys.executable, Path("."))


class ConfigInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.codex = Path(self.temp.name) / ".codex"
        self.codex.mkdir()
        self.config = self.codex / "config.toml"
        self.config.write_text('model = "gpt-6-astra"\nmodel_reasoning_effort = "low"\n')

    def tearDown(self):
        self.temp.cleanup()

    def test_native_config_and_missing_config_are_supported(self):
        config, hashes, warnings, profile = inspect_config(self.codex)
        self.assertEqual(config["model"], "gpt-6-astra")
        self.assertIn(str(self.config), hashes)
        self.assertIsNone(profile)
        self.config.unlink()
        self.assertEqual(inspect_config(self.codex)[0], {})

    def test_external_provider_and_base_url_are_rejected_without_echoing_values(self):
        for line in ('model_provider = "private-provider"\n', 'openai_base_url = "https://secret.invalid/v1"\n'):
            with self.subTest(line=line):
                self.config.write_text(line)
                with self.assertRaises(SetupError) as raised:
                    inspect_config(self.codex)
                self.assertNotIn("secret.invalid", str(raised.exception))
                self.assertNotIn("private-provider", str(raised.exception))

    def test_disabled_agents_are_rejected(self):
        self.config.write_text('[agents]\nenabled = false\n')
        with self.assertRaisesRegex(SetupError, "disabled"):
            inspect_config(self.codex)

    def test_valid_agent_defaults_are_preserved(self):
        self.config.write_text(
            'model = "gpt-6-astra"\n[agents]\n'
            'default_subagent_model = "other"\n'
            'default_subagent_reasoning_effort = "medium"\n'
            '[agents.reviewer]\ndescription = "review"\n'
        )
        config, _hashes, warnings, _profile = inspect_config(self.codex)
        self.assertEqual(config["agents"]["default_subagent_model"], "other")
        self.assertTrue(warnings)

    def test_absorbed_scalar_is_rejected(self):
        self.config.write_text('[agents]\nopenai_base_url = "https://secret.invalid"\n')
        with self.assertRaisesRegex(SetupError, "malformed agent roles") as raised:
            inspect_config(self.codex)
        self.assertNotIn("secret.invalid", str(raised.exception))

    def test_standalone_and_legacy_profiles_are_inspected(self):
        self.config.write_text('model = "gpt-6-astra"\nprofile = "work"\n')
        profile = self.codex / "work.config.toml"
        profile.write_text('model_reasoning_effort = "high"\n')
        config, hashes, _warnings, selected = inspect_config(self.codex)
        self.assertEqual(config["model_reasoning_effort"], "high")
        self.assertIn(str(profile), hashes)
        self.assertEqual(selected, "work")
        profile.unlink()
        self.config.write_text('[profiles.work]\nmodel_reasoning_effort = "max"\n')
        self.assertEqual(inspect_config(self.codex, "work")[0]["model_reasoning_effort"], "max")

    def test_ambiguous_profile_is_rejected(self):
        self.config.write_text('[profiles.work]\nmodel = "gpt-6-astra"\n')
        (self.codex / "work.config.toml").write_text('model = "gpt-6-astra"\n')
        with self.assertRaisesRegex(SetupError, "Both standalone and legacy"):
            inspect_config(self.codex, "work")

    def test_symlinked_config_is_refused_when_supported(self):
        target = self.codex / "real-config.toml"
        target.write_text(self.config.read_text())
        self.config.unlink()
        try:
            self.config.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaisesRegex(SetupError, "symlinked config"):
            inspect_config(self.codex)

    def test_inspect_combines_config_and_native_capabilities_without_writes(self):
        original = self.config.read_bytes()
        report = inspect(
            Path(self.temp.name), self.codex, sys.executable,
            capability_probe=fake_capability, agent_probe=fake_agents,
        )
        self.assertEqual(report["status"], "native-capability-preflight-ready")
        self.assertTrue(report["capability_preflight_verified"])
        self.assertFalse(report["desktop_worker_delegation_verified"])
        self.assertNotIn("runtime_verified", report)
        self.assertEqual(report["worker_model"], WORKER_MODEL)
        self.assertEqual(report["worker_effort"], WORKER_EFFORT)
        self.assertEqual(self.config.read_bytes(), original)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.home = Path(self.temp.name).resolve()
        self.codex = self.home / ".codex"
        self.codex.mkdir()
        self.config = self.codex / "config.toml"
        self.config.write_text('# Preserve comments\nmodel = "gpt-6-astra"\n')
        self.policy = self.codex / "AGENTS.md"
        self.policy.write_text("# Existing instructions\nKeep this note.\n")
        self.original_config = self.config.read_bytes()
        self.original_policy = self.policy.read_bytes()
        self.report = inspect(
            self.home, self.codex, sys.executable,
            capability_probe=fake_capability, agent_probe=fake_agents,
        )

    def tearDown(self):
        self.temp.cleanup()

    def changes(self, replace=False, policy=True):
        return install.plan_changes(self.home, self.codex, self.report, policy, replace)

    def test_astra_op_is_the_installed_skill_identity(self):
        self.assertEqual(SKILL, "astra-op")
        source = ROOT / "skill" / SKILL
        self.assertIn("name: astra-op", (source / "SKILL.md").read_text())
        metadata = (source / "agents" / "openai.yaml").read_text()
        self.assertIn('display_name: "Astra OP"', metadata)
        self.assertIn("$astra-op", metadata)
        paths = [change["path"] for change in self.changes()]
        self.assertTrue(any(path == self.home / ".agents" / "skills" / "astra-op" / "SKILL.md" for path in paths))
        self.assertFalse(any("skilled" in path.parts for path in paths))

    def apply(self):
        return install.apply_changes(self.changes(), self.codex, self.report["input_hashes"])

    def test_generated_role_pins_sol_xhigh_and_inherits_permissions(self):
        changes = self.changes()
        role_change = next(item for item in changes if item["path"].name == f"{ROLE}.toml")
        role = tomllib.loads(role_change["after"].decode())
        self.assertEqual(role["name"], ROLE)
        self.assertEqual(role["model"], "gpt-5.6-sol")
        self.assertEqual(role["model_reasoning_effort"], "xhigh")
        self.assertNotIn("model_provider", role)
        self.assertNotIn("sandbox_mode", role)
        self.assertNotIn("agents", role)

    def test_runtime_binding_has_no_router_provider_or_key(self):
        change = next(item for item in self.changes() if item["path"].name == "runtime.json")
        binding = json.loads(change["after"])
        self.assertEqual(binding["worker_model"], WORKER_MODEL)
        self.assertEqual(binding["worker_effort"], WORKER_EFFORT)
        lowered = change["after"].lower()
        self.assertNotIn(b"router", lowered)
        self.assertNotIn(b"api_key", lowered)
        self.assertNotIn(b"provider", lowered)

    def test_apply_preserves_config_and_unrelated_policy(self):
        receipt = self.apply()
        self.assertIsNotNone(receipt)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertTrue(self.policy.read_bytes().startswith(self.original_policy))
        role = tomllib.loads((self.codex / "agents" / f"{ROLE}.toml").read_text())
        self.assertEqual((role["model"], role["model_reasoning_effort"]), (WORKER_MODEL, WORKER_EFFORT))
        self.assertTrue((self.home / ".agents" / "skills" / SKILL / "SKILL.md").exists())

    def test_no_policy_install_leaves_instructions_untouched(self):
        changes = self.changes(policy=False)
        self.assertFalse(any(item["path"] == self.policy for item in changes))
        install.apply_changes(changes, self.codex, self.report["input_hashes"])
        self.assertEqual(self.policy.read_bytes(), self.original_policy)

    def test_dry_run_main_changes_nothing(self):
        before = {str(p): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        output = io.StringIO()
        argv = ["install.py", "--home", str(self.home), "--codex-home", str(self.codex)]
        with patch.object(sys, "argv", argv), patch.object(install, "inspect", return_value=self.report), redirect_stdout(output):
            self.assertEqual(install.main(), 0)
        after = {str(p): p.read_bytes() for p in self.home.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertIn("Preview only", output.getvalue())

    def test_existing_foreign_content_requires_replace(self):
        folder = self.home / ".agents" / "skills" / SKILL
        folder.mkdir(parents=True)
        (folder / "SKILL.md").write_text("user content\n")
        with self.assertRaises(SetupError):
            self.changes()
        self.assertTrue(self.changes(replace=True))

    def test_override_policy_is_used_when_nonempty(self):
        override = self.codex / "AGENTS.override.md"
        override.write_text("# Override\n")
        changes = self.changes()
        self.assertTrue(any(item["path"] == override for item in changes))
        self.assertFalse(any(item["path"] == self.policy for item in changes))

    def test_apply_rollback_restores_completed_writes(self):
        changes = self.changes()
        target = changes[1]["path"]
        real = install.atomic_write
        fired = False

        def fail_once(path, data, mode=0o600):
            nonlocal fired
            if path == target and not fired:
                fired = True
                raise OSError("synthetic failure")
            return real(path, data, mode)

        with patch.object(install, "atomic_write", side_effect=fail_once):
            with self.assertRaises(OSError):
                install.apply_changes(changes, self.codex, self.report["input_hashes"])
        for item in changes:
            self.assertEqual(install.contents(item["path"]), item["before"])
        self.assertEqual(self.config.read_bytes(), self.original_config)

    def test_config_changed_after_preflight_is_rejected(self):
        self.config.write_text(self.config.read_text() + "# later edit\n")
        with self.assertRaisesRegex(SetupError, "configuration changed"):
            install.apply_changes(self.changes(), self.codex, self.report["input_hashes"])

    def test_config_created_after_missing_config_preflight_is_rejected(self):
        self.config.unlink()
        report = inspect(
            self.home, self.codex, sys.executable,
            capability_probe=fake_capability, agent_probe=fake_agents,
        )
        changes = install.plan_changes(self.home, self.codex, report, True, False)
        self.config.write_text('model_provider = "external"\n')
        with self.assertRaisesRegex(SetupError, "configuration changed"):
            install.apply_changes(changes, self.codex, report["input_hashes"])

    def test_undo_restores_original_policy_and_removes_package(self):
        receipt = self.apply()
        with redirect_stdout(io.StringIO()):
            install.undo(receipt, self.home, self.codex, True)
        self.assertEqual(self.policy.read_bytes(), self.original_policy)
        self.assertEqual(self.config.read_bytes(), self.original_config)
        self.assertFalse((self.codex / "agents" / f"{ROLE}.toml").exists())
        self.assertFalse((self.home / ".agents" / "skills" / SKILL).exists())

    def test_undo_refuses_later_user_edit(self):
        receipt = self.apply()
        self.policy.write_text(self.policy.read_text() + "Later user note.\n")
        with self.assertRaisesRegex(SetupError, "changed after installation"):
            install.undo(receipt, self.home, self.codex, True)
        self.assertIn("Later user note", self.policy.read_text())

    def test_receipt_outside_backup_root_is_rejected(self):
        receipt = self.apply()
        copied = self.codex / "receipt.json"
        copied.write_bytes(receipt.read_bytes())
        with self.assertRaisesRegex(SetupError, "must be inside"):
            install.undo(copied, self.home, self.codex, True)

    def test_symlink_destination_is_refused_when_supported(self):
        external = self.home / "external"
        external.mkdir()
        try:
            (self.home / ".agents").symlink_to(external, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaisesRegex(SetupError, "symlink"):
            self.changes()


class PolicyAndWorkflowTests(unittest.TestCase):
    def record(self) -> dict:
        criterion = "Behavior matches the approved contract"
        return {
            "schema_version": 2,
            "work_order": {
                "id": "T1", "goal": "Implement behavior", "workspace": "C:/repo",
                "baseline": "abc123 clean", "architecture": "Use the existing service boundary",
                "contracts": ["Keep public API stable"], "allowed_paths": ["src/", "tests/"],
                "acceptance": [criterion], "tests": ["python -m unittest"],
                "out_of_scope": ["Deployment"], "escalate_if": ["Public API must change"],
            },
            "dispatch": {
                "path": "custom_role", "agent_type": "skilled_sol_worker",
                "requested_model": "gpt-5.6-sol", "requested_reasoning_effort": "xhigh",
                "fork_turns": "all", "fallback_reason": "not_applicable",
                "observed_model": "unverified", "observed_reasoning_effort": "unverified",
            },
            "worker_result": {
                "task_id": "T1", "status": "ready_for_review", "changed_files": ["src/a.py"],
                "checks": [{"command": "python -m unittest", "exit_code": 0, "result": "passed"}],
                "acceptance_results": [{"criterion": criterion, "status": "pass", "evidence": "test A"}],
                "failures": [], "resume_action": "none",
            },
            "review": {
                "task_id": "T1", "diff_reviewed": True, "decision": "accepted",
                "findings": [], "correction_package": [],
            },
        }

    def test_policy_merge_preserves_crlf_and_unrelated_text(self):
        block = install.BEGIN + b"\nnew\n" + install.END + b"\n"
        old = b"prefix\r\n" + install.BEGIN + b"\r\nold\r\n" + install.END + b"\r\nsuffix\r\n"
        updated = install.managed_policy(old, block)
        self.assertTrue(updated.startswith(b"prefix\r\n"))
        self.assertTrue(updated.endswith(b"suffix\r\n"))
        self.assertEqual(updated.count(install.BEGIN), 1)

    def test_malformed_policy_markers_are_rejected(self):
        with self.assertRaises(SetupError):
            install.managed_policy(install.BEGIN, b"new")

    def test_work_order_covers_worker_success_and_failure_contracts(self):
        brief = (ROOT / "skill" / "astra-op" / "templates" / "task-brief.md").read_text()
        report = (ROOT / "skill" / "astra-op" / "templates" / "task-report.md").read_text()
        for required in ("Goal and non-goals", "Relevant architecture and files", "Fixed contracts", "Acceptance criteria", "Verification"):
            self.assertIn(required, brief)
        for status in ("ready_for_review", "blocked", "failed"):
            self.assertIn(status, report)
        self.assertIn("resume action", report.lower())

    def test_correction_and_final_diff_review_are_explicit(self):
        skill = (ROOT / "skill" / "astra-op" / "SKILL.md").read_text()
        review = (ROOT / "skill" / "astra-op" / "references" / "review.md").read_text()
        self.assertIn("correction package", skill)
        self.assertIn("same worker", skill)
        self.assertRegex(skill, r"actual changed\s+and untracked files")
        self.assertIn("captured baseline", review)
        self.assertIn("accepted", review)

    def test_no_hard_worker_or_correction_cap_in_workflow(self):
        text = "\n".join((ROOT / name).read_text() for name in (
            "POLICY.md", "skill/astra-op/SKILL.md", "skill/astra-op/references/execution.md",
            "skill/astra-op/references/review.md",
        ))
        self.assertNotIn("at most one correction", text.lower())
        self.assertNotIn("max_workers", text)
        self.assertIn("does not set a fixed", text)

    def test_successful_worker_completion_and_acceptance_contract(self):
        result = validate_run(self.record())
        self.assertEqual(result["dispatch_path"], "custom_role")
        self.assertFalse(result["model_observed"])
        self.assertFalse(result["reasoning_effort_observed"])
        self.assertEqual(result["worker_status"], "ready_for_review")
        self.assertEqual(result["review_decision"], "accepted")

    def test_explicit_model_fallback_omits_fixed_role_and_records_route(self):
        record = self.record()
        record["dispatch"].update({
            "path": "explicit_model_fallback", "agent_type": "omitted",
            "fork_turns": "none", "fallback_reason": "unknown agent_type skilled_sol_worker",
            "observed_model": "gpt-5.6-sol", "observed_reasoning_effort": "xhigh",
        })
        result = validate_run(record)
        self.assertEqual(result["dispatch_path"], "explicit_model_fallback")
        self.assertTrue(result["model_observed"])
        self.assertTrue(result["reasoning_effort_observed"])

    def test_explicit_model_fallback_rejects_fixed_role_or_full_history(self):
        record = self.record()
        record["dispatch"].update({
            "path": "explicit_model_fallback", "agent_type": "executor",
            "fork_turns": "none", "fallback_reason": "custom role unavailable",
        })
        with self.assertRaisesRegex(RunError, "omit agent_type"):
            validate_run(record)
        record["dispatch"]["agent_type"] = "omitted"
        record["dispatch"]["fork_turns"] = "all"
        with self.assertRaisesRegex(RunError, "fork_turns"):
            validate_run(record)

    def test_dispatch_requires_exact_sol_xhigh_request(self):
        record = self.record()
        record["dispatch"]["requested_model"] = "gpt-5.6-luna"
        with self.assertRaisesRegex(RunError, "gpt-5.6-sol"):
            validate_run(record)
        record = self.record()
        record["dispatch"]["requested_reasoning_effort"] = "high"
        with self.assertRaisesRegex(RunError, "xhigh"):
            validate_run(record)

    def test_worker_failure_is_propagated_with_resume_action(self):
        record = self.record()
        record["worker_result"].update({
            "status": "failed", "failures": ["test process could not start"],
            "resume_action": "repair the test environment and continue the same task",
        })
        record["worker_result"]["acceptance_results"][0]["status"] = "unverified"
        record["review"].update({"decision": "blocked", "findings": ["environment failure"]})
        self.assertEqual(validate_run(record)["worker_status"], "failed")
        record["worker_result"]["failures"] = []
        with self.assertRaisesRegex(RunError, "propagate"):
            validate_run(record)

    def test_correction_package_and_diff_review_are_enforced(self):
        record = self.record()
        record["worker_result"]["acceptance_results"][0]["status"] = "fail"
        record["review"].update({
            "decision": "changes_requested", "findings": ["boundary case missing"],
            "correction_package": ["Add the missing boundary test and fix the implementation"],
        })
        self.assertEqual(validate_run(record)["corrections_recorded"], 1)
        record["review"]["correction_package"] = []
        with self.assertRaisesRegex(RunError, "correction_package"):
            validate_run(record)
        record = self.record()
        record["review"]["diff_reviewed"] = False
        with self.assertRaisesRegex(RunError, "actual diff"):
            validate_run(record)

    def test_acceptance_cannot_hide_failed_or_unverified_result(self):
        record = self.record()
        record["worker_result"]["acceptance_results"][0]["status"] = "unverified"
        with self.assertRaisesRegex(RunError, "cannot accept"):
            validate_run(record)


class PlanTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT / "examples" / "invoice-filter"
        self.plan = json.loads((self.root / "plan.json").read_text())

    def test_example_is_valid_schema_2(self):
        result = validate(self.plan, self.root)
        self.assertEqual(result["status"], "structure-valid")
        self.assertNotIn("max_flash_workers", result)

    def test_old_fixed_worker_cap_is_rejected(self):
        self.plan["max_flash_workers"] = 1
        with self.assertRaisesRegex(PlanError, "Fixed worker caps"):
            validate(self.plan, self.root)

    def test_placeholder_missing_brief_and_unbounded_paths_are_rejected(self):
        changed = copy.deepcopy(self.plan)
        changed["tasks"][0]["acceptance"] = ["TODO"]
        with self.assertRaises(PlanError):
            validate(changed, self.root)
        changed = copy.deepcopy(self.plan)
        changed["tasks"][0]["brief"] = "missing.md"
        with self.assertRaises(PlanError):
            validate(changed, self.root)
        for value in (".", "../outside", "/absolute", "src/**", ".git/config"):
            changed = copy.deepcopy(self.plan)
            changed["tasks"][0]["allowed_paths"] = [value]
            with self.assertRaises(PlanError):
                validate(changed, self.root)

    def add_task(self, task_id: str, path: str) -> dict:
        task = copy.deepcopy(self.plan["tasks"][0])
        task["id"] = task_id
        task["allowed_paths"] = [path]
        self.plan["tasks"].append(task)
        return task

    def test_parallel_group_has_no_arbitrary_count_cap(self):
        self.add_task("T2", "src/two.py")
        self.add_task("T3", "src/three.py")
        for task in self.plan["tasks"]:
            task["parallel_group"] = "G1"
        self.assertEqual(validate(self.plan, self.root)["tasks"], 3)

    def test_parallel_overlap_and_dependencies_are_rejected(self):
        second = self.add_task("T2", "src/invoices")
        for task in self.plan["tasks"]:
            task["parallel_group"] = "G1"
        with self.assertRaisesRegex(PlanError, "overlapping"):
            validate(self.plan, self.root)
        second["allowed_paths"] = ["src/other.py"]
        second["depends_on"] = ["T1"]
        with self.assertRaisesRegex(PlanError, "dependent"):
            validate(self.plan, self.root)

    def test_dependency_cycle_and_duplicate_ids_are_rejected(self):
        second = self.add_task("T2", "src/two.py")
        second["depends_on"] = ["T1"]
        self.plan["tasks"][0]["depends_on"] = ["T2"]
        with self.assertRaisesRegex(PlanError, "cycle"):
            validate(self.plan, self.root)
        self.plan = json.loads((self.root / "plan.json").read_text())
        self.add_task("T1", "src/two.py")
        with self.assertRaisesRegex(PlanError, "duplicate"):
            validate(self.plan, self.root)

    def test_sensitive_implementation_can_be_specified_for_sol(self):
        self.plan["tasks"][0]["risk"] = "sensitive"
        self.assertEqual(validate(self.plan, self.root)["status"], "structure-valid")


if __name__ == "__main__":
    unittest.main()
