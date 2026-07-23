import importlib.util
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


RUNNER_PATH = Path(r"E:\大师安素材库\大师安工具矩阵\loops\lingzhi_tea_storyboard_video_loop\scripts\run_antioxidant_two_batch.py")
DELIVERY_ROOT = Path(r"E:\大师安素材库\大师安工具矩阵\outputs\批量脚本视频任务_0623\delivery_by_script")
API_BASE = "https://xyq.jianying.com/api/biz/v1"
VIDEO_MODEL = "seedance2.0_fast_vision"

spec = importlib.util.spec_from_file_location("runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def load_json(path, default):
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if text.strip():
            return json.loads(text)
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    tmp = path.with_suffix(path.suffix + ".tmp")
    urllib.request.urlretrieve(url, tmp)
    tmp.replace(path)


def api_headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }


def check_ret(resp):
    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError(f"non-json response {resp.status_code}: {resp.text[:500]}") from exc
    if resp.status_code >= 400:
        raise RuntimeError(f"http {resp.status_code}: {json.dumps(data, ensure_ascii=False)[:1000]}")
    if str(data.get("ret")) != "0":
        raise RuntimeError(f"api ret={data.get('ret')} errmsg={data.get('errmsg')} log_id={data.get('log_id')}")
    return data


def upload_file(api_key, path):
    with path.open("rb") as fh:
        resp = requests.post(
            f"{API_BASE}/skill/upload_file",
            headers=api_headers(api_key),
            files={"file": (path.name, fh, "image/png")},
            timeout=180,
        )
    data = check_ret(resp)
    asset_id = (data.get("data") or {}).get("pippit_asset_id")
    if not asset_id:
        raise RuntimeError(f"upload missing pippit_asset_id: {json.dumps(data, ensure_ascii=False)[:1000]}")
    return asset_id


def submit_video(api_key, message, asset_id, duration):
    payload = {
        "message": message,
        "asset_ids": [asset_id],
        "general_agent_settings": {
            "ratio": 3,
            "duration_start": int(duration),
            "duration_end": int(duration),
            "show_subtitle": False,
            "video_model": VIDEO_MODEL,
            "resolution": "480p",
            "video_resolution": "480p",
        },
    }
    headers = api_headers(api_key)
    headers["Content-Type"] = "application/json"
    resp = requests.post(
        f"{API_BASE}/agent/submit_marketing_run",
        headers=headers,
        json=payload,
        timeout=180,
    )
    data = check_ret(resp)
    run = ((data.get("data") or {}).get("run") or {})
    run_id = run.get("run_id")
    thread_id = run.get("thread_id")
    if not run_id or not thread_id:
        raise RuntimeError(f"submit missing run/thread: {json.dumps(data, ensure_ascii=False)[:1000]}")
    return {
        "run_id": run_id,
        "thread_id": thread_id,
        "state": run.get("state"),
        "web_thread_link": (data.get("data") or {}).get("web_thread_link", ""),
    }


def query_video(api_key, thread_id, run_id):
    headers = api_headers(api_key)
    headers["Content-Type"] = "application/json"
    resp = requests.post(
        f"{API_BASE}/agent/query_generate_video_result",
        headers=headers,
        json={"thread_id": thread_id, "run_id": run_id},
        timeout=120,
    )
    data = check_ret(resp)
    return data.get("data") or {}


def local_image_path(task_name, shot):
    return DELIVERY_ROOT / task_name / "images" / f"{task_name}_shot{shot:02d}.png"


def local_video_path(task_name, shot):
    return DELIVERY_ROOT / task_name / "videos" / f"{task_name}_shot{shot:02d}.mp4"


def build_message(task_name, row, duration):
    base_prompt = runner.video_prompt(row, duration)
    return (
        f"根据上传的分镜图生成{duration}秒竖屏9:16单镜头UGC视频，只生成这一个镜头，不要合成整条。"
        "严格保持上传图片中的人物、产品、桌面、场景和构图连续性。"
        "动作必须匹配脚本描述，运镜必须是自然手机手持UGC运镜。"
        "不要字幕，不要标题，不要角标，不要贴纸文案，不要水印。"
        f"口播原文必须完整自然说完，不改写、不删减、不换词：{row.get('line', '')}\n"
        f"镜头要求：{base_prompt}"
    )


def prepare_jobs(task_name):
    cfg = runner.TASKS[task_name]
    rows = runner.read_rows(cfg["source_xlsx"])
    state = runner.load_state()
    shots = state.get("tasks", {}).get(task_name, {})
    jobs = []
    for row in rows:
        shot = int(row["shot"])
        item = shots.get(str(shot), {})
        image_node = item.get("image_node")
        if not image_node:
            raise RuntimeError(f"{task_name} shot{shot:02d} missing image_node")
        image_status = runner.image_status(image_node)
        image_url = image_status.get("url") or ""
        if not image_url:
            raise RuntimeError(f"{task_name} shot{shot:02d} image is not ready")
        duration = int(item.get("duration") or runner.estimate_duration(row["line"], row["time"]))
        duration = max(4, min(15, duration))
        image_path = local_image_path(task_name, shot)
        download(image_url, image_path)
        item["image_status"] = image_status
        jobs.append(
            {
                "shot": shot,
                "row": row,
                "duration": duration,
                "image_url": image_url,
                "image_path": str(image_path),
                "message": build_message(task_name, row, duration),
            }
        )
    runner.save_state(state)
    return jobs


def submit_one(api_key, task_name, job, sidecar_path, sidecar):
    shot_key = str(job["shot"])
    item = sidecar.setdefault("tasks", {}).setdefault(shot_key, {})
    if item.get("run_id") and item.get("thread_id") and item.get("run_state") not in {4, 5, "4", "5"}:
        return f"[skip-submit] {task_name} shot{job['shot']:02d}"
    asset_id = item.get("asset_id")
    if not asset_id:
        asset_id = upload_file(api_key, Path(job["image_path"]))
        item["asset_id"] = asset_id
        item["uploaded_at"] = int(time.time())
        save_json(sidecar_path, sidecar)
    result = submit_video(api_key, job["message"], asset_id, job["duration"])
    item.update(result)
    item.update(
        {
            "run_state": result.get("state", 1),
            "duration": job["duration"],
            "image_url": job["image_url"],
            "image_path": job["image_path"],
            "submitted_at": int(time.time()),
        }
    )
    save_json(sidecar_path, sidecar)
    return f"[submitted] {task_name} shot{job['shot']:02d} duration={job['duration']} run={result['run_id']}"


def update_main_state(task_name, shot, values):
    state = runner.load_state()
    item = state.setdefault("tasks", {}).setdefault(task_name, {}).setdefault(str(shot), {})
    item.update(values)
    runner.save_state(state)


def submit_missing(api_key, task_name, jobs, sidecar_path, sidecar, workers):
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(submit_one, api_key, task_name, job, sidecar_path, sidecar) for job in jobs]
        for fut in as_completed(futures):
            print(fut.result(), flush=True)


def poll_and_download(api_key, task_name, sidecar_path, sidecar, max_minutes):
    deadline = time.time() + max_minutes * 60
    while True:
        ready = 0
        tasks = sidecar.setdefault("tasks", {})
        for shot_key, item in sorted(tasks.items(), key=lambda x: int(x[0])):
            shot = int(shot_key)
            path = local_video_path(task_name, shot)
            if path.exists() and path.stat().st_size > 0:
                ready += 1
                continue
            if not item.get("thread_id") or not item.get("run_id"):
                continue
            data = query_video(api_key, item["thread_id"], item["run_id"])
            run_state = data.get("run_state")
            item["run_state"] = run_state
            item["query"] = data
            item["updated_at"] = int(time.time())
            video_urls = data.get("video_urls") or []
            if str(run_state) == "3" and video_urls:
                url = video_urls[0]
                item["video_url"] = url
                download(url, path)
                item["local_path"] = str(path)
                ready += 1
                update_main_state(
                    task_name,
                    shot,
                    {
                        "external_video_provider": "xiaoyunque",
                        "external_video_task_id": item["run_id"],
                        "external_video_url": url,
                        "external_video_path": str(path),
                        "external_video_status": {"url_count": 1, "url": url, "status": "succeeded"},
                    },
                )
                print(f"[downloaded] {task_name} shot{shot:02d}", flush=True)
            elif str(run_state) in {"4", "5"}:
                print(f"[failed] {task_name} shot{shot:02d} {data.get('fail_reason')}", flush=True)
            save_json(sidecar_path, sidecar)
            time.sleep(0.2)
        print(f"[poll] {task_name} ready {ready}/{len(tasks)}", flush=True)
        if ready == len(tasks) and tasks:
            return True
        if time.time() >= deadline:
            return False
        time.sleep(30)


def main():
    task_name = sys.argv[1] if len(sys.argv) > 1 else "script24"
    workers = int(os.getenv("XIAOYUNQUE_WORKERS", "4"))
    max_minutes = int(os.getenv("XIAOYUNQUE_MAX_MINUTES", "180"))
    api_key = os.getenv("XIAOYUNQUE_API_KEY")
    if not api_key:
        raise RuntimeError("XIAOYUNQUE_API_KEY is required")
    sidecar_path = DELIVERY_ROOT / task_name / "xiaoyunque_tasks.json"
    sidecar = load_json(
        sidecar_path,
        {"task": task_name, "api_base": API_BASE, "video_model": VIDEO_MODEL, "tasks": {}},
    )
    sidecar["api_base"] = API_BASE
    sidecar["video_model"] = VIDEO_MODEL
    jobs = prepare_jobs(task_name)
    submit_missing(api_key, task_name, jobs, sidecar_path, sidecar, workers)
    ok = poll_and_download(api_key, task_name, sidecar_path, sidecar, max_minutes)
    if not ok:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
