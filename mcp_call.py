#!/usr/bin/env python3
"""Minimal streamable-HTTP MCP client to call a single tool on the vSphere MCP server.
Usage: python3 mcp_call.py <tool_name> [json_args]"
"""
import sys, json, uuid
import requests

ENDPOINT = "http://127.0.0.1:8010/mcp"
HDR = {"Content-Type": "application/json",
       "Accept": "application/json, text/event-stream"}
MCPVER = "2025-03-26"

def parse_sse(text):
    messages = []
    cur_type, cur_data = None, []
    for line in text.splitlines():
        if line.startswith("event:"):
            cur_type = line.split(":", 1)[1].strip()
        elif line.startswith("data:"):
            cur_data.append(line.split(":", 1)[1].strip())
        elif line == "" and cur_type is not None:
            messages.append((cur_type, "\n".join(cur_data)))
            cur_type, cur_data = None, []
    if cur_type is not None:
        messages.append((cur_type, "\n".join(cur_data)))
    return messages

def parse_result(text):
    # returns the id and result/error of the LAST message
    out = None
    for etype, edata in parse_sse(text):
        try:
            j = json.loads(edata)
        except Exception:
            continue
        if "result" in j or "error" in j:
            out = j
    return out

def main():
    tool = sys.argv[1] if len(sys.argv) > 1 else "list_vms"
    raw_args = sys.argv[2] if len(sys.argv) > 2 else "{}"
    args = json.loads(raw_args)

    s = requests.Session()
    # 1. initialize
    r = s.post(ENDPOINT, headers=HDR, data=json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": MCPVER, "capabilities": {},
                   "clientInfo": {"name": "probe", "version": "1.0"}}}))
    sid = r.headers.get("mcp-session-id")
    init = parse_result(r.text)
    if not init or "result" not in init:
        print("INIT FAILED:", r.status_code, r.text[:500]); sys.exit(1)
    if sid:
        HDR["mcp-session-id"] = sid
    # 2. initialized notification
    s.post(ENDPOINT, headers=HDR, data=json.dumps({
        "jsonrpc": "2.0", "method": "notifications/initialized"}))
    # 3. tools/call
    r = s.post(ENDPOINT, headers=HDR, data=json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": tool, "arguments": args}}))
    res = parse_result(r.text)
    if res is None:
        print("NO RESULT. HTTP", r.status_code); print(r.text[:500]); sys.exit(1)
    if "error" in res:
        print("TOOL ERROR:", json.dumps(res["error"])); sys.exit(1)
    content = res["result"].get("content", [])
    text = "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
    print(text if text else json.dumps(res["result"], indent=2)[:2000])

if __name__ == "__main__":
    main()