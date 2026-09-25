#!/usr/bin/env python3
"""Read-only capability inspection for the native Codex runtime."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
from typing import Callable

if sys.version_info < (3, 11):
    raise SystemExit("Python 3.11+ is required. No packages or settings were changed.")
import tomllib

WORKER_MODEL = "gpt-5.6-sol"
WORKER_EFFORT = "xhigh"
ROLE = "skilled_sol_worker"
SKILL = "astra-op"

AGENT_SCALAR_SETTINGS = frozenset({
    "enabled",
    "default_subagent_model",
    "default_subagent_reasoning_effort",
    "interrupt_message",
    "max_concurrent_threads_per_session",
    "max_threads",
    "max_depth",
    "job_max_runtime_seconds",
})


class SetupError(ValueError):
    """An actionable setup problem whose message contains no account secrets."""


def read_toml(path: Path) -> dict:
    try:
        with path.open("rb") as stream:
            return tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SetupError(f"Cannot read valid TOML from {path.name} ({type(exc).__name__}).") from None


def merge_tables(base: dict, overlay: dict) -> dict:
    result = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_tables(result[key], value)
        else:
            result[key] = value
    return result


def inspect_config(codex_home: Path, profile: str | None = None) -> tuple[dict, dict[str, str | None], list[str], str | None]:
    """Inspect only settings that can disable native agents; never rewrite config."""
    config_path = codex_home / "config.toml"
    if not config_path.exists():
        if profile:
            raise SetupError("A profile was requested but config.toml does not exist.")
        return {}, {str(config_path): None}, ["No config.toml exists; Codex defaults will be used."], None
    if config_path.is_symlink():
        raise SetupError("Refusing to inspect a symlinked config.toml.")
    config = read_toml(config_path)
    hashes = {str(config_path): hashlib.sha256(config_path.read_bytes()).hexdigest()}
    selected = profile if profile is not None else config.get("profile")
    warnings: list[str] = []
    if selected:
        if not isinstance(selected, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", selected):
            raise SetupError("Unsupported profile name; inspect the active profile manually.")
        standalone = codex_home / f"{selected}.config.toml"
        legacy = config.get("profiles", {}).get(selected)
        if standalone.exists() and legacy is not None:
            raise SetupError("Both standalone and legacy profile definitions exist; resolve that ambiguity first.")
        if standalone.exists():
            if standalone.is_symlink():
                raise SetupError("Refusing to inspect a symlinked profile configuration.")
            config = merge_tables(config, read_toml(standalone))
            hashes[str(standalone)] = hashlib.sha256(standalone.read_bytes()).hexdigest()
        elif isinstance(legacy, dict):
            config = merge_tables(config, legacy)
            warnings.append("A legacy inline profile was inspected; confirm the current Codex client applies it.")
        else:
            raise SetupError("The selected profile is not available as a readable configuration file.")
    agents = config.get("agents", {})
    if not isinstance(agents, dict):
        raise SetupError("The existing [agents] setting is not a TOML table.")
    misplaced = sorted(
        key for key, value in agents.items()
        if key not in AGENT_SCALAR_SETTINGS and not isinstance(value, dict)
    )
    if misplaced:
        raise SetupError(
            "Scalar setting(s) that Codex would parse as malformed agent roles were found under [agents]: "
            + ", ".join(misplaced)
            + ". Reconcile config.toml before installing; SKILLED will not rewrite it."
        )
    if agents.get("enabled") is False:
        raise SetupError("Native agents are disabled by [agents].enabled = false. SKILLED will not override it.")
    if "default_subagent_model" in agents or "default_subagent_reasoning_effort" in agents:
        warnings.append("Global subagent defaults are preserved; the named SKILLED role overrides its own model and effort.")
    provider = config.get("model_provider")
    if provider not in (None, "openai"):
        raise SetupError("The effective profile selects an external model_provider. SKILLED requires native ChatGPT routing.")
    if config.get("openai_base_url"):
        raise SetupError("The effective profile sets openai_base_url. Remove that external route before using native SKILLED.")
    return config, hashes, warnings, selected


class AppServerClient:
    """Small JSONL client for stable, read-only app-server methods."""

    def __init__(self, codex_binary: str, codex_home: Path, response_timeout: float = 30.0):
        self.codex_binary = codex_binary
        self.codex_home = codex_home
        self.response_timeout = response_timeout
        self.process: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[dict] = queue.Queue()

    def __enter__(self) -> "AppServerClient":
        env = os.environ.copy()
        env["CODEX_HOME"] = str(self.codex_home)
        try:
            self.process = subprocess.Popen(
                [self.codex_binary, "app-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=env,
            )
        except OSError as exc:
            raise SetupError(f"Cannot start `codex app-server` ({type(exc).__name__}).") from None
        assert self.process.stdout is not None
        threading.Thread(target=self._read, args=(self.process.stdout,), daemon=True).start()
        try:
            self.request(1, "initialize", {
                "clientInfo": {"name": "skilled_installer", "title": "SKILLED installer", "version": "2.1.0"}
            })
            self.notify("initialized", {})
        except BaseException:
            self._stop()
            raise
        return self

    def __exit__(self, *_args: object) -> None:
        self._stop()

    def _stop(self) -> None:
        if self.process is None:
            return
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=3)

    def _read(self, stream: object) -> None:
        for line in stream:  # type: ignore[union-attr]
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, TypeError):
                continue
            if isinstance(value, dict):
                self.messages.put(value)

    def _send(self, value: dict) -> None:
        if self.process is None or self.process.stdin is None or self.process.poll() is not None:
            raise SetupError("Codex app-server exited before capability inspection completed.")
        try:
            self.process.stdin.write(json.dumps(value) + "\n")
            self.process.stdin.flush()
        except OSError as exc:
            raise SetupError(f"Cannot communicate with Codex app-server ({type(exc).__name__}).") from None

    def notify(self, method: str, params: dict) -> None:
        self._send({"method": method, "params": params})

    def request(self, request_id: int, method: str, params: dict | None = None) -> dict:
        payload: dict[str, object] = {"method": method, "id": request_id}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        while True:
            try:
                message = self.messages.get(timeout=self.response_timeout)
            except queue.Empty:
                raise SetupError(f"Codex app-server did not answer {method} in time.") from None
            if message.get("id") != request_id:
                continue
            if "error" in message:
                raise SetupError(f"Codex app-server rejected {method}; update or repair Codex, then retry.")
            result = message.get("result")
            if not isinstance(result, dict):
                raise SetupError(f"Codex app-server returned an invalid {method} response.")
            return result


def effort_names(model: dict) -> list[str]:
    values = model.get("supportedReasoningEfforts", [])
    if not isinstance(values, list):
        return []
    return [
        item.get("reasoningEffort")
        for item in values
        if isinstance(item, dict) and isinstance(item.get("reasoningEffort"), str)
    ]


def validate_capabilities(account_result: dict, models: list[dict]) -> dict:
    account = account_result.get("account")
    account_type = account.get("type") if isinstance(account, dict) else None
    if account_type != "chatgpt":
        if account_type == "apiKey":
            raise SetupError("Codex is authenticated with an API key. Sign in with ChatGPT so SKILLED uses the subscription session.")
        raise SetupError("No native ChatGPT login is active in this Codex environment. Run `codex login`, then retry.")
    matches = [
        item for item in models
        if isinstance(item, dict) and (item.get("model") == WORKER_MODEL or item.get("id") == WORKER_MODEL)
    ]
    if len(matches) != 1:
        raise SetupError(f"Codex model/list did not return exactly one {WORKER_MODEL} entry for this ChatGPT account.")
    efforts = effort_names(matches[0])
    if WORKER_EFFORT not in efforts:
        available = ", ".join(efforts) if efforts else "none reported"
        raise SetupError(f"{WORKER_MODEL} does not advertise {WORKER_EFFORT} reasoning (reported: {available}).")
    return {
        "authentication": "ChatGPT subscription",
        "worker_model": WORKER_MODEL,
        "worker_effort": WORKER_EFFORT,
        "worker_display_name": matches[0].get("displayName") or WORKER_MODEL,
        "worker_hidden": bool(matches[0].get("hidden", False)),
    }


def query_app_server(codex_binary: str, codex_home: Path) -> dict:
    with AppServerClient(codex_binary, codex_home) as client:
        account = client.request(2, "account/read", {"refreshToken": False})
        models: list[dict] = []
        cursor: str | None = None
        seen_cursors: set[str] = set()
        page = 0
        while True:
            params: dict[str, object] = {"limit": 100, "includeHidden": True}
            if cursor:
                params["cursor"] = cursor
            result = client.request(10 + page, "model/list", params)
            data = result.get("data")
            if not isinstance(data, list):
                raise SetupError("Codex app-server returned an invalid model/list page.")
            models.extend(item for item in data if isinstance(item, dict))
            next_cursor = result.get("nextCursor")
            if next_cursor is None:
                break
            if not isinstance(next_cursor, str) or not next_cursor:
                raise SetupError("Codex app-server returned an invalid model/list cursor.")
            if next_cursor in seen_cursors:
                raise SetupError("Codex app-server repeated a model/list cursor.")
            seen_cursors.add(next_cursor)
            cursor = next_cursor
            page += 1
    return validate_capabilities(account, models)


def check_multi_agent(codex_binary: str, codex_home: Path) -> None:
    env = os.environ.copy()
    env["CODEX_HOME"] = str(codex_home)
    try:
        result = subprocess.run(
            [codex_binary, "features", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SetupError(f"Cannot inspect Codex native-agent support ({type(exc).__name__}).") from None
    if result.returncode != 0:
        raise SetupError("`codex features list` failed; repair or update Codex before installing SKILLED.")
    enabled = any(re.fullmatch(r"multi_agent\s+\S+\s+true", line.strip()) for line in result.stdout.splitlines())
    if not enabled:
        raise SetupError("This Codex build does not report the native multi_agent feature as enabled.")


def inspect(
    home: Path,
    codex_home: Path,
    codex_binary: str = "codex",
    profile: str | None = None,
    capability_probe: Callable[[str, Path], dict] = query_app_server,
    agent_probe: Callable[[str, Path], None] = check_multi_agent,
) -> dict:
    """Return a redacted native capability report without making inference calls."""
    del home
    resolved = shutil.which(codex_binary) if Path(codex_binary).name == codex_binary else codex_binary
    if not resolved or not Path(resolved).exists():
        raise SetupError("Codex CLI was not found. Install/update Codex and ensure `codex` is on PATH.")
    config, input_hashes, warnings, selected = inspect_config(codex_home, profile)
    agent_probe(str(resolved), codex_home)
    native = capability_probe(str(resolved), codex_home)
    root_model = config.get("model")
    if root_model and root_model != "gpt-6-astra":
        warnings.append("config.toml does not select gpt-6-astra; confirm Astra is selected in the parent session before use.")
    return {
        "status": "native-capability-preflight-ready",
        "capability_preflight_verified": True,
        "desktop_worker_delegation_verified": False,
        "inference_request_made": False,
        "native_agents": True,
        "catalog_source": "codex app-server model/list",
        "authentication": native["authentication"],
        "root_model_observed": root_model,
        "profile_inspected": selected,
        "worker_model": native["worker_model"],
        "worker_effort": native["worker_effort"],
        "worker_display_name": native["worker_display_name"],
        "worker_hidden": native["worker_hidden"],
        "custom_agent": ROLE,
        "input_hashes": input_hashes,
        "warnings": warnings,
    }


def default_locations(home_arg: str | None = None, codex_home_arg: str | None = None) -> tuple[Path, Path]:
    home = Path(home_arg).expanduser().resolve() if home_arg else Path.home().resolve()
    codex_home = Path(codex_home_arg or os.environ.get("CODEX_HOME", str(home / ".codex"))).expanduser().absolute()
    return home, codex_home
