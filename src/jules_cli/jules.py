#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess
import urllib.request
import urllib.error
import urllib.parse
import shutil
from typing import List, Dict, Optional

API_BASE = "https://jules.googleapis.com/v1alpha"

def get_api_key():
    key = os.environ.get("JULES_API_KEY")
    if not key:
        print("Error: JULES_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)
    return key

def api_request(method, endpoint, data=None):
    api_key = get_api_key()
    url = f"{API_BASE}/{endpoint}"
    if '?' in url:
        url += f"&key={api_key}" # Some google APIs accept key param, but header is safer

    # But documentation says X-Goog-Api-Key header.
    headers = {
        "X-Goog-Api-Key": api_key,
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, headers=headers, method=method)
    if data:
        req.data = json.dumps(data).encode('utf-8')

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        try:
            print(e.read().decode('utf-8'), file=sys.stderr)
        except:
            pass
        sys.exit(1)

def check_fzf():
    if not shutil.which("fzf"):
        print("Error: fzf is not installed or not in PATH.", file=sys.stderr)
        sys.exit(1)

def fzf_select(items: List[str], prompt="Select: ", preview=None) -> Optional[str]:
    # items is a list of strings
    cmd = ['fzf', '--prompt', prompt, '--height', '40%', '--reverse', '--cycle']
    if preview:
        cmd.extend(['--preview', preview])

    fzf = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=None # Allow stderr to pass through for interactive UI
    )
    input_str = "\n".join(items).encode('utf-8')
    stdout, stderr = fzf.communicate(input=input_str)

    if fzf.returncode == 0:
        return stdout.decode('utf-8').strip()
    return None

def format_session_line(s):
    sid = s.get('name', '').split('/')[-1]
    title = s.get('title', 'No Title')
    status = "Active" # Placeholder, API doesn't seem to show status in list easily?
    return f"{sid}\t{title}"

def list_sessions():
    response = api_request("GET", "sessions?pageSize=50")
    sessions = response.get("sessions", [])
    if not sessions:
        print("No sessions found.")
        return

    lines = [format_session_line(s) for s in sessions]

    while True:
        selected = fzf_select(lines, prompt="Select Session (ESC to quit): ")
        if not selected:
            break

        sid = selected.split('\t')[0]
        view_session(sid)

def print_activity(act):
    orig = act.get('originator', 'unknown')
    timestamp = act.get('createTime', '')
    print(f"[{orig.upper()}] {timestamp}")

    if 'progressUpdated' in act:
        pu = act['progressUpdated']
        print(f"  Title: {pu.get('title')}")
        if pu.get('description'):
            print(f"  Description: {pu.get('description')}")
    elif 'planGenerated' in act:
        print("  Plan Generated")
        steps = act['planGenerated'].get('plan', {}).get('steps', [])
        for step in steps:
            print(f"    - {step.get('title')}")
    elif 'bashOutput' in act: # Artifacts
         pass # Handled in artifacts

    if 'artifacts' in act:
        for art in act['artifacts']:
            if 'bashOutput' in art:
                bo = art['bashOutput']
                print(f"  > Command: {bo.get('command', '').strip()}")
                print(f"  > Output: {bo.get('output', '').strip()[:200]}...") # Truncate
            elif 'changeSet' in art:
                print("  > Change Set Created")

    print("-" * 40)

def view_session(sid):
    while True:
        session = api_request("GET", f"sessions/{sid}")
        # Clear screen? Maybe not.
        print(f"\nSession: {session.get('title')} ({sid})")
        print(f"Prompt: {session.get('prompt')}")

        options = ["List Activities", "Send Message", "Refresh", "Back"]
        sel = fzf_select(options, prompt=f"Action ({sid}): ")

        if not sel or sel == "Back":
            break
        elif sel == "List Activities":
            list_activities(sid)
        elif sel == "Send Message":
            send_message(sid)
        elif sel == "Refresh":
            continue

def list_activities(sid):
    response = api_request("GET", f"sessions/{sid}/activities?pageSize=50")
    activities = response.get("activities", [])

    # We can pipe these to a pager or just print them.
    # Since we are using fzf for menu, maybe print and wait?
    # Or use fzf to browse activities?

    activity_lines = []
    for act in activities:
        orig = act.get('originator', 'UNK')
        kind = "Unknown"
        if 'progressUpdated' in act: kind = "Progress"
        elif 'planGenerated' in act: kind = "Plan"
        elif 'planApproved' in act: kind = "Approved"

        summary = ""
        if 'progressUpdated' in act:
            summary = act['progressUpdated'].get('title', '')

        aid = act.get('name', '').split('/')[-1]
        activity_lines.append(f"{aid}\t[{orig}] {kind}: {summary}")

    while True:
        sel = fzf_select(activity_lines, prompt="View Activity (ESC to back): ")
        if not sel:
            break
        aid = sel.split('\t')[0]
        # Find the full activity object
        full_act = next((a for a in activities if a.get('name', '').endswith(aid)), None)
        if full_act:
            print("\n" + "="*50)
            print(json.dumps(full_act, indent=2))
            print("="*50 + "\n")
            input("Press Enter to continue...")

def send_message(sid):
    print("\nEnter your message (Ctrl+D to finish):")
    try:
        lines = sys.stdin.readlines()
    except KeyboardInterrupt:
        return

    prompt = "".join(lines).strip()
    if not prompt:
        return

    data = {"prompt": prompt}
    print("Sending...")
    api_request("POST", f"sessions/{sid}:sendMessage", data)
    print("Message sent.")

def create_session():
    # List sources
    response = api_request("GET", "sources")
    sources = response.get("sources", [])
    if not sources:
        print("No sources found.")
        return

    source_lines = [f"{s['name']}\t{s.get('githubRepo', {}).get('repo', 'unknown')}" for s in sources]
    selected_src = fzf_select(source_lines, prompt="Select Source: ")
    if not selected_src:
        return
    source_name = selected_src.split('\t')[0]

    try:
        title = input("Session Title: ")
        prompt = input("Initial Prompt: ")
    except KeyboardInterrupt:
        return

    if not title or not prompt:
        print("Cancelled.")
        return

    payload = {
        "prompt": prompt,
        "title": title,
        "sourceContext": {
            "source": source_name,
            "githubRepoContext": {
                "startingBranch": "main"
            }
        }
    }

    resp = api_request("POST", "sessions", payload)
    print("Session created.")
    sid = resp.get('id')
    if not sid:
        sid = resp.get('name', '').split('/')[-1]

    view_session(sid)

def main():
    check_fzf()
    parser = argparse.ArgumentParser(description="Jules CLI")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List sessions")
    subparsers.add_parser("create", help="Create session")
    view_parser = subparsers.add_parser("view", help="View session")
    view_parser.add_argument("session_id", help="Session ID")

    args = parser.parse_args()

    try:
        if args.command == "list" or args.command is None:
            list_sessions()
        elif args.command == "create":
            create_session()
        elif args.command == "view":
            view_session(args.session_id)
    except KeyboardInterrupt:
        print("\nExiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
