"""Non-interactive agent command builders and structured event parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
import re

from .models import RunSpec


SENSITIVE_KEY = re.compile(r"(TOKEN|SECRET|KEY|PASSWORD|AUTH)", re.IGNORECASE)


def sanitize(value):
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if SENSITIVE_KEY.search(str(key)) else sanitize(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value


def _json_events(stdout: str) -> list[dict]:
    stripped = stdout.strip()
    if not stripped:
        return []
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        events = []
        for line in stripped.splitlines():
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                events.append({"type": "unparsed", "text": line})
            else:
                events.append(value if isinstance(value, dict) else {"value": value})
        return events
    if isinstance(value, list):
        return [item if isinstance(item, dict) else {"value": item} for item in value]
    return [value if isinstance(value, dict) else {"value": value}]


def _usage_tokens(event: dict) -> int | None:
    usage = event.get("usage")
    if not isinstance(usage, dict):
        return None
    value = usage.get("output_tokens")
    return value if isinstance(value, int) and not isinstance(value, bool) else None


class AgentAdapter(ABC):
    id: str

    @abstractmethod
    def build_command(self, spec: RunSpec, prompt: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def _extract_final(self, events: list[dict]) -> str:
        raise NotImplementedError

    def parse(
        self,
        stdout: str,
        stderr: str,
    ) -> tuple[str, int | None, tuple[dict, ...]]:
        events = _json_events(stdout)
        tokens = None
        for event in events:
            candidate = _usage_tokens(event)
            if candidate is not None:
                tokens = candidate
        if stderr.strip():
            events.append({"type": "stderr", "text": stderr.strip()})
        sanitized = tuple(sanitize(event) for event in events)
        return self._extract_final(events), tokens, sanitized


class CodexAdapter(AgentAdapter):
    id = "codex"

    def build_command(self, spec: RunSpec, prompt: str) -> list[str]:
        command = [
            "codex",
            "exec",
            "--ephemeral",
            "--json",
            "--sandbox",
            "workspace-write",
            "-C",
            str(spec.workspace),
        ]
        if spec.model:
            command.extend(["--model", spec.model])
        if spec.reasoning_effort:
            command.extend(
                ["-c", f'model_reasoning_effort="{spec.reasoning_effort}"']
            )
        command.append(prompt)
        return command

    def _extract_final(self, events: list[dict]) -> str:
        final = ""
        for event in events:
            item = event.get("item")
            if (
                event.get("type") == "item.completed"
                and isinstance(item, dict)
                and item.get("type") == "agent_message"
                and isinstance(item.get("text"), str)
            ):
                final = item["text"]
        return final


class ClaudeAdapter(AgentAdapter):
    id = "claude"

    def build_command(self, spec: RunSpec, prompt: str) -> list[str]:
        command = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--permission-mode",
            "acceptEdits",
        ]
        if spec.model:
            command.extend(["--model", spec.model])
        if spec.reasoning_effort:
            command.extend(["--effort", spec.reasoning_effort])
        command.append(prompt)
        return command

    def _extract_final(self, events: list[dict]) -> str:
        final = ""
        for event in events:
            if event.get("type") == "result" and isinstance(event.get("result"), str):
                final = event["result"]
        return final


class CursorAdapter(AgentAdapter):
    id = "cursor"

    def build_command(self, spec: RunSpec, prompt: str) -> list[str]:
        command = [
            "cursor",
            "agent",
            "-p",
            "--output-format",
            "json",
            "--trust",
            "--sandbox",
            "enabled",
            "--workspace",
            str(spec.workspace),
        ]
        if spec.model:
            command.extend(["--model", spec.model])
        command.append(prompt)
        return command

    def _extract_final(self, events: list[dict]) -> str:
        final = ""
        for event in events:
            message = event.get("message")
            if event.get("type") != "assistant" or not isinstance(message, dict):
                continue
            content = message.get("content")
            if not isinstance(content, list):
                continue
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            )
            if text:
                final = text
        return final


ADAPTERS = {
    "codex": CodexAdapter(),
    "claude": ClaudeAdapter(),
    "cursor": CursorAdapter(),
}


def get_adapter(agent: str) -> AgentAdapter:
    try:
        return ADAPTERS[agent]
    except KeyError as error:
        raise ValueError(f"unsupported agent adapter: {agent}") from error
