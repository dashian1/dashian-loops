import importlib.util
import sys
import time
from pathlib import Path

RUNNER_PATH = Path(__file__).with_name("run_antioxidant_two_batch.py")
FAST_MODEL = "Seedance 2.0 Fast VIP"

spec = importlib.util.spec_from_file_location("runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def task_sort_key(name):
    if name.startswith("script"):
        return (0, int(name.replace("script", "")))
    return (1, name)


def selected_tasks():
    args = [x.strip() for x in sys.argv[1:] if x.strip() and not x.startswith("--")]
    if args:
        return args
    return sorted([name for name in runner.TASKS if name.startswith("script")], key=task_sort_key)


def create_only():
    return "--create-only" in sys.argv


def missing_shots(task_name):
    rows = runner.read_rows(runner.TASKS[task_name]["source_xlsx"])
    state = runner.load_state().get("tasks", {}).get(task_name, {})
    out = []
    for row in rows:
        shot = int(row["shot"])
        item = state.get(str(shot), {})
        if item.get("video_model") == FAST_MODEL:
            continue
        node = item.get("video_node")
        if not node:
            out.append((row, "missing-video-node"))
            continue
        try:
            st = runner.video_status(node)
            if st.get("url_count", 0) < 1 and not st.get("loading"):
                out.append((row, "not-ready"))
        except Exception as exc:
            out.append((row, f"status-error:{str(exc)[:120]}"))
    return out


def create_fast_video(task_name, row, reason):
    shot = int(row["shot"])
    shot_key = str(shot)
    state = runner.load_state()
    item = state["tasks"].setdefault(task_name, {}).setdefault(shot_key, {})
    image_node = item.get("image_node")
    if not image_node:
        raise RuntimeError(f"{task_name}:{shot} missing image node")
    image_status = runner.image_status(image_node)
    if image_status.get("url_count", 0) < 1:
        raise RuntimeError(f"{task_name}:{shot} image not ready")

    old_video = item.get("video_node")
    duration = int(item.get("duration") or runner.estimate_duration(row["line"], row["time"]))
    name = f"{task_name}_shot{shot:02d}_video_fast_{int(time.time())}"
    cmd = [
        runner.LIBTV,
        "node",
        "create",
        name,
        "-t",
        "video",
        "--prompt",
        runner.video_prompt(row, duration),
        "-s",
        f"model={FAST_MODEL}",
        "-s",
        "modeType=singleImage2video",
        "-s",
        "ratio=9:16",
        "-s",
        "resolution=480p",
        "-s",
        f"duration={duration}",
        "-s",
        "enableSound=on",
        "--left",
        image_node,
    ]
    out = runner.run_allow_created(cmd, timeout=300)
    data = runner.first_json(out)
    node_id = (
        data.get("newNodeKey")
        or data.get("nodeKey")
        or data.get("data", {}).get("nodeKey")
        or data.get("id")
        or data.get("reactFlowNode", {}).get("id")
        or data.get("data", {}).get("key")
    )
    if not node_id:
        raise RuntimeError(f"could not parse new node id for {task_name}:{shot}: {out[:1000]}")

    runner.run_allow_created([runner.LIBTV, "group", runner.TASKS[task_name]["group_id"], "--node", node_id], timeout=120)
    runner.update_shot_state(
        task_name,
        shot_key,
        {
            "video_node": node_id,
            "duration": duration,
            "video_model": FAST_MODEL,
            "old_video_node": old_video,
            "rebuild_reason": reason,
        },
    )
    print(f"[created-fast] {task_name}:{shot} old={old_video} new={node_id} duration={duration}", flush=True)
    return node_id


def trigger_fast(task_name, row, node_id):
    shot = int(row["shot"])
    try:
        runner.run_allow_created([runner.LIBTV, "node", "-p", runner.PROJECT_UUID, node_id, "-r"], timeout=20)
        print(f"[triggered-fast] {task_name}:{shot} {node_id}", flush=True)
        return True
    except Exception as exc:
        message = str(exc)
        print(f"[trigger-fast-error] {task_name}:{shot} {message[:1000]}", flush=True)
        if "1200000136" in message or "算力不足" in message:
            print("[stop] LibTV capacity is insufficient even on fast model. Rerun later.", flush=True)
            raise SystemExit(2)
        print(f"[queued-or-check-later] {task_name}:{shot} {node_id}", flush=True)
        return False


def main():
    runner.run([runner.LIBTV, "project", "use", runner.PROJECT_UUID], timeout=60)
    work = []
    for task in selected_tasks():
        for row, reason in missing_shots(task):
            work.append((task, row, reason))
    print(f"[missing-to-rebuild] {len(work)}", flush=True)

    only_create = create_only()
    for task, row, reason in work:
        node_id = create_fast_video(task, row, reason)
        if not only_create:
            trigger_fast(task, row, node_id)
        time.sleep(0.8)


if __name__ == "__main__":
    main()
