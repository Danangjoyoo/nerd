"""Offline native MCP projection inspection; a loopback fixture, never inference.

The empty private home has no copied credentials. An allowlisted environment
contains a synthetic key and the only model provider is a localhost fixture.
The fixture emits discovery/call/answer protocol events, never model output.
No Context database is opened; context_recall returns a fixed synthetic value.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import threading

from deployable_response import json_bytes, mcp_result


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL = "offline-context-response-projection-v2"
PROMPT = "Offline protocol fixture. Discover context_recall and request its fixed synthetic observation, then finish."
CALL_ID = "call_offline_context_projection"
ERROR_CALL_ID = "call_offline_context_overflow"
SEARCH_ID = "call_offline_context_search"
PAYLOAD = {"status": "ok", "context_id": "ctx_" + "a" * 39,
           "value": 'WIRE_MARKER 日本語 "quotes" \\ backslash\nnewline',
           "authority": "untrusted_context", "created": False}
ERROR_PAYLOAD = {"status": "overflow", "context_id": "ctx_" + "a" * 39, "records": [],
                 "conflicts": [], "overflow": True, "authority": "untrusted_context", "created": False}


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else json_bytes(value)).hexdigest()


def write_json(path, value):
    path.write_bytes(json_bytes(value) + b"\n")


def tool_definition():
    return {"name": "context_recall", "description": "Return the fixed offline projection fixture.",
            "inputSchema": {"type": "object", "properties": {"overflow": {"type": "boolean"}},
                            "required": ["overflow"], "additionalProperties": False},
            "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}}


def serve(journal_path, instream=None, outstream=None):
    instream, outstream = instream or sys.stdin, outstream or sys.stdout
    with Path(journal_path).open("a") as journal:
        for line in instream:
            request = json.loads(line)
            journal.write(json.dumps({"direction": "request", "message": request}) + "\n")
            journal.flush()
            if "id" not in request:
                continue
            method = request.get("method")
            if method == "initialize":
                result = {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                          "serverInfo": {"name": "offline-response-fixture", "version": "1"}}
            elif method == "tools/list":
                result = {"tools": [tool_definition()]}
            elif method == "tools/call":
                params = request.get("params", {})
                arguments = params.get("arguments", {})
                if params.get("name") != "context_recall" or set(arguments) != {"overflow"} or type(arguments["overflow"]) is not bool:
                    raise ValueError("unexpected fixture operation")
                result = mcp_result(ERROR_PAYLOAD if arguments["overflow"] else PAYLOAD)
            elif method == "ping":
                result = {}
            else:
                raise ValueError("unexpected fixture method")
            response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
            journal.write(json.dumps({"direction": "response", "message": response}) + "\n")
            journal.flush()
            outstream.write(json.dumps(response) + "\n")
            outstream.flush()


def scripted_output(request):
    items = request.get("input", [])
    observed = {item.get("call_id") for item in items if item.get("type") == "function_call_output"}
    if {CALL_ID, ERROR_CALL_ID} <= observed:
        return [{"type": "message", "id": "msg_fixture_done", "role": "assistant", "status": "completed",
                 "content": [{"type": "output_text", "text": "Offline fixture complete.", "annotations": []}]}]
    for item in items:
        if item.get("type") == "tool_search_output" and item.get("call_id") == SEARCH_ID:
            for namespace in item.get("tools", []):
                if namespace.get("type") == "namespace":
                    for tool in namespace.get("tools", []):
                        if tool.get("name") == "context_recall":
                            return [{"type": "function_call", "id": "fc_fixture_" + str(error), "call_id": identifier,
                                     "name": "context_recall", "namespace": namespace["name"],
                                     "arguments": json.dumps({"overflow": error})}
                                    for identifier, error in ((CALL_ID, False), (ERROR_CALL_ID, True))]
            raise ValueError("native search did not return the fixed fixture tool")
    actual_prompt = any(PROMPT in part.get("text", "") for item in items
                        for part in item.get("content", []) if isinstance(part, dict))
    if not actual_prompt:  # A native warm-up/request unrelated to the scripted turn.
        return []
    return [{"type": "tool_search_call", "id": "ts_fixture", "execution": "client", "call_id": SEARCH_ID,
             "status": "completed", "arguments": {"query": "context_recall", "limit": 1}}]


def sse_response(request):
    output = scripted_output(request)
    response = {"id": "resp_fixture", "object": "response", "created_at": 1, "status": "completed",
                "model": request.get("model", "gpt-5.4-mini"), "output": output,
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}}
    events = []
    for index, item in enumerate(output):
        for suffix in ("added", "done"):
            events.append({"type": "response.output_item." + suffix, "output_index": index, "item": item})
    events.append({"type": "response.completed", "response": response})
    return b"".join(("event: " + event["type"] + "\ndata: " + json.dumps(event) + "\n\n").encode() for event in events)


def isolated_environment(runtime):
    environment = {key: os.environ[key] for key in ("PATH", "LANG", "LC_ALL", "TERM") if key in os.environ}
    for key, directory in {"HOME": "home", "CODEX_HOME": "codex-home", "XDG_CONFIG_HOME": "xdg",
                           "XDG_CACHE_HOME": "cache", "XDG_DATA_HOME": "data", "TMPDIR": "tmp"}.items():
        target = runtime / directory
        target.mkdir(exist_ok=True, mode=0o700)
        environment[key] = str(target)
    environment["OFFLINE_SYNTHETIC_KEY"] = "offline-not-a-real-credential"
    return environment


def command_for(workspace, journal, endpoint):
    command = ["codex", "exec", "--ephemeral", "--json", "--sandbox", "workspace-write", "-C", str(workspace),
               "--ignore-user-config", "--ignore-rules", "--model", "gpt-5.4-mini", "--strict-config"]
    config = {"model_reasoning_effort": "low", "approval_policy": "never",
              "mcp_servers.response-fixture.command": sys.executable,
              "mcp_servers.response-fixture.args": [str(Path(__file__).resolve()), "serve", "--journal", str(journal)],
              "model_provider": "offline", "model_providers.offline.name": "Offline loopback fixture",
              "model_providers.offline.base_url": endpoint + "/v1",
              "model_providers.offline.env_key": "OFFLINE_SYNTHETIC_KEY",
              "model_providers.offline.requires_openai_auth": False,
              "model_providers.offline.wire_api": "responses", "features.enable_request_compression": False}
    for key, value in config.items():
        command.extend(["-c", key + "=" + json.dumps(value)])
    return [*command, PROMPT]


def run(output):
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    sources = {name: sha((HERE / name).read_bytes()) for name in ("response_wire_probe.py", "deployable_response.py", "structured.py")}
    for name in sources:
        target = output / "source-snapshot" / name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(HERE / name, target)
    requests, errors = [], []

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_POST(self):
            try:
                if self.path != "/v1/responses":
                    raise ValueError("unexpected loopback endpoint")
                body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
                request = json.loads(body)
                requests.append({"path": self.path, "body": request, "body_sha256": sha(body)})
                if len(requests) > 8:
                    raise ValueError("bounded protocol request count exceeded")
                payload = sse_response(request)
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as error:
                errors.append(type(error).__name__ + ": " + str(error))
                self.send_error(400)

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        with tempfile.TemporaryDirectory(prefix="context-response-offline-") as directory:
            runtime = Path(directory)
            workspace = runtime / "workspace"
            workspace.mkdir()
            subprocess.run(["git", "init", "-q", str(workspace)], check=True)
            environment = isolated_environment(runtime)
            journal = runtime / "mcp.jsonl"
            command = command_for(workspace, journal, f"http://127.0.0.1:{server.server_port}")
            version = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=True).stdout.strip()
            process = subprocess.Popen(command, cwd=workspace, env=environment, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
            aborted = None
            try:
                stdout, stderr = process.communicate(timeout=30)
            except BaseException as error:
                aborted = type(error).__name__
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            raw = {"protocol": PROTOCOL, "client_version": version, "command": command,
                   "exit_code": process.returncode, "aborted": aborted, "stdout": stdout, "stderr": stderr,
                   "requests": requests, "errors": errors,
                   "mcp": [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else [],
                   "synthetic_auth_only": True, "auth_files_copied": False, "live_model_requests": 0}
    finally:
        server.shutdown()
        server.server_close()
    write_json(output / "raw.json", raw)
    projected = [item for entry in requests for item in entry["body"].get("input", [])
                 if item.get("type") == "function_call_output" and item.get("call_id") in {CALL_ID, ERROR_CALL_ID}]
    write_json(output / "projection.json", {"items": projected, "canonical_item_bytes": [len(json_bytes(item)) for item in projected],
                                           "canonical_mcp_result_bytes": len(json_bytes(mcp_result(PAYLOAD))),
                                           "live_model_requests": 0})
    if sources != {name: sha((HERE / name).read_bytes()) for name in sources}:
        raise RuntimeError("source changed during offline inspection")
    manifest = {"protocol": PROTOCOL, "client_version": version, "sources": sources, "live_model_requests": 0,
                "limitations": ["Synthetic HTTP Responses provider, not authenticated model inference.",
                                "No measured tokens, billing, quality, latency, or cross-client claims.",
                                "Projection is observed for this installed native client and fixed response only."],
                "files": {str(path.relative_to(output)): sha(path.read_bytes()) for path in output.rglob("*") if path.is_file()}}
    write_json(output / "manifest.json", manifest)
    print(json.dumps({"output": str(output), "manifest_sha256": sha((output / "manifest.json").read_bytes()),
                      "projection_count": len(projected), "errors": errors, "live_model_requests": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["serve", "run"])
    parser.add_argument("--journal", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.operation == "serve":
        serve(args.journal)
    else:
        run(args.output or ROOT / "benchmarks/results/nerd-context" / ("response-wire-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")))
