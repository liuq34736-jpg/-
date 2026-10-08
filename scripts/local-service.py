"""Hidden service supervisor started by Windows WMI, outside the caller's job.

No production imports, credential reads, dependency downloads or AI calls.
"""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def service_command(root, service, node_path):
    if service == "backend":
        return [str(root / ".venv/Scripts/python.exe"), "-X", "utf8", "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", "8765", "--no-access-log"], root
    if service == "frontend":
        return [node_path, str(root / "frontend/node_modules/vite/bin/vite.js"), "--host", "127.0.0.1", "--port", "5173", "--strictPort"], root / "frontend"
    raise ValueError("unknown local service")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("service", choices=("backend", "frontend"))
    parser.add_argument("--instance-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{32}", args.instance_id):
        raise SystemExit(2)
    root = Path(__file__).resolve().parents[1]
    runtime = root / "runtime"
    toolchain = json.loads((runtime / "toolchain.json").read_text(encoding="utf-8-sig"))
    command, working_dir = service_command(root, args.service, toolchain["node_path"])
    state_file = runtime / f"service-{args.service}.json"
    state = {"root": str(root), "service": args.service, "instance_id": args.instance_id, "launcher_pid": os.getpid(), "child_pid": None, "status": "starting"}

    def save_state():
        temporary = state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        temporary.replace(state_file)

    with (runtime / f"{args.service}.out.log").open("a", encoding="utf-8") as output, (runtime / f"{args.service}.err.log").open("a", encoding="utf-8") as error:
        startup_info = subprocess.STARTUPINFO()
        startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup_info.wShowWindow = subprocess.SW_HIDE
        child = subprocess.Popen(command, cwd=working_dir, stdout=output, stderr=error, startupinfo=startup_info, creationflags=subprocess.CREATE_NO_WINDOW)
        state.update(child_pid=child.pid, status="running")
        save_state()
        state.update(status="exited", exit_code=child.wait())
        save_state()


if __name__ == "__main__":
    main()
