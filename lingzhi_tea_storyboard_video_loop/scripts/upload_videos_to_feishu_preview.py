import concurrent.futures
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import importlib.util

RUNNER_PATH = Path(r"E:\大师安素材库\大师安工具矩阵\loops\lingzhi_tea_storyboard_video_loop\scripts\run_antioxidant_two_batch.py")
DELIVERY_ROOT = Path(r"E:\大师安素材库\大师安工具矩阵\outputs\批量脚本视频任务_0623\delivery_by_script")
LINK_STATE = DELIVERY_ROOT / "feishu_sheet_links.json"
VIDEO_STATE = DELIVERY_ROOT / "feishu_video_file_links.json"
FOLDER_STATE = DELIVERY_ROOT / "feishu_video_folder.json"
LARK_CLI = r"C:\Users\gba\.workbuddy\binaries\node\versions\22.22.2\lark-cli.cmd"

spec = importlib.util.spec_from_file_location("runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def run(cmd, cwd=None, input_text=None, timeout=900):
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        shell=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout + "\n" + proc.stderr)
    return proc.stdout


def first_json(text):
    start = text.find("{")
    if start < 0:
        raise ValueError(text[:1000])
    depth = 0
    in_str = False
    esc = False
    for i, ch in enumerate(text[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
    raise ValueError("unbalanced json")


def load_json(path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def ensure_folder():
    state = load_json(FOLDER_STATE, {})
    if state.get("folder_token"):
        return state["folder_token"]
    out = run(
        [
            LARK_CLI,
            "drive",
            "+create-folder",
            "--name",
            "灵芝黄芪枸杞茶_视频交付_0624",
            "--as",
            "user",
            "--format",
            "json",
        ],
        timeout=120,
    )
    data = first_json(out).get("data", {})
    state = {"folder_token": data["folder_token"], "url": data.get("url", "")}
    save_json(FOLDER_STATE, state)
    return state["folder_token"]


def set_file_permission(token):
    data = {
        "link_share_entity": "tenant_readable",
        "share_entity": "same_tenant",
        "security_entity": "anyone_can_view",
    }
    run(
        [
            LARK_CLI,
            "drive",
            "permission.public",
            "patch",
            "--token",
            token,
            "--type",
            "file",
            "--data",
            "-",
            "--as",
            "user",
            "--yes",
            "--format",
            "json",
        ],
        input_text=json.dumps(data, ensure_ascii=False),
        timeout=120,
    )


def upload_one(task, shot, path, folder_token):
    key = f"{task}:{shot}"
    out = run(
        [
            LARK_CLI,
            "drive",
            "+upload",
            "--file",
            f".\\{path.name}",
            "--name",
            path.name,
            "--folder-token",
            folder_token,
            "--as",
            "user",
            "--format",
            "json",
        ],
        cwd=path.parent,
        timeout=900,
    )
    data = first_json(out).get("data", {})
    token = data.get("file_token")
    url = data.get("url") or (f"https://ucnscwivbsrz.feishu.cn/file/{token}" if token else "")
    if not token or not url:
        raise RuntimeError(f"upload result missing token/url for {path}")
    try:
        set_file_permission(token)
    except Exception as exc:
        print(f"[file-permission-error] {key} {str(exc)[:160]}", flush=True)
    return key, {"token": token, "url": url, "file": path.name}


def workbook_sheet_name(token):
    out = run(
        [
            LARK_CLI,
            "sheets",
            "+workbook-info",
            "--spreadsheet-token",
            token,
            "--as",
            "user",
            "--format",
            "json",
        ],
        timeout=120,
    )
    info = first_json(out)
    return info["data"]["sheets"][0].get("sheet_name") or info["data"]["sheets"][0].get("title") or "storyboard"


def patch_sheet(task, sheet_token, rows, video_links):
    sheet_name = workbook_sheet_name(sheet_token)
    cells = []
    start_row = None
    end_row = None
    for row_num, shot in rows:
        key = f"{task}:{shot}"
        item = video_links.get(key)
        if not item:
            continue
        if start_row is None:
            start_row = row_num
        end_row = row_num
        cells.append([{"rich_text": [{"type": "link", "text": "查看视频", "link": item["url"]}]}])
    if start_row is None:
        return 0
    run(
        [
            LARK_CLI,
            "sheets",
            "+cells-set",
            "--spreadsheet-token",
            sheet_token,
            "--sheet-name",
            sheet_name,
            "--range",
            f"K{start_row}:K{end_row}",
            "--cells",
            "-",
            "--as",
            "user",
            "--format",
            "json",
        ],
        input_text=json.dumps(cells, ensure_ascii=False),
        timeout=180,
    )
    return len(cells)


def task_rows(task):
    cfg = runner.TASKS[task]
    rows = runner.read_rows(cfg["source_xlsx"])
    out = []
    for idx, row in enumerate(rows, start=2):
        out.append((idx, int(row["shot"])))
    return out


def video_path(task, shot):
    return DELIVERY_ROOT / task / "videos" / f"{task}_shot{shot:02d}.mp4"


def main():
    links = load_json(LINK_STATE, {})
    video_links = load_json(VIDEO_STATE, {})
    folder_token = ensure_folder()
    requested = sys.argv[1:]
    tasks = requested or list(links.keys())

    upload_jobs = []
    for task in tasks:
        if task not in links:
            continue
        for _, shot in task_rows(task):
            key = f"{task}:{shot}"
            if key in video_links and video_links[key].get("url"):
                continue
            path = video_path(task, shot)
            if path.exists() and path.stat().st_size > 0:
                upload_jobs.append((task, shot, path))

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(upload_one, task, shot, path, folder_token) for task, shot, path in upload_jobs]
        for fut in concurrent.futures.as_completed(futures):
            key, item = fut.result()
            video_links[key] = item
            save_json(VIDEO_STATE, video_links)
            print(f"[uploaded] {key} {item['url']}", flush=True)
            time.sleep(0.2)

    patched = {}
    for task in tasks:
        info = links.get(task)
        if not info:
            continue
        rows = task_rows(task)
        count = patch_sheet(task, info["token"], rows, video_links)
        if count:
            patched[task] = count
            print(f"[patched-sheet] {task} videos={count}", flush=True)

    print("[summary]", json.dumps(patched, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
