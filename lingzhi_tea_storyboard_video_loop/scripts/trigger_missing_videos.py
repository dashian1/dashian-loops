import importlib.util
import sys
from pathlib import Path

RUNNER_PATH = Path(__file__).with_name("run_antioxidant_two_batch.py")

spec = importlib.util.spec_from_file_location("runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def task_sort_key(name):
    if name.startswith("script"):
        return (0, int(name.replace("script", "")))
    return (1, name)


def target_tasks():
    requested = [x.strip() for x in sys.argv[1:] if x.strip()]
    if requested:
        return requested
    return sorted([name for name in runner.TASKS if name.startswith("script")], key=task_sort_key)


def missing_video_items(task_name):
    rows = runner.read_rows(runner.TASKS[task_name]["source_xlsx"])
    state = runner.load_state().get("tasks", {}).get(task_name, {})
    missing = []
    for row in rows:
        shot = int(row["shot"])
        item = state.get(str(shot), {})
        node = item.get("video_node")
        if not node:
            continue
        try:
            status = runner.video_status(node)
        except Exception as exc:
            missing.append((task_name, shot, node, f"status-error:{str(exc)[:160]}"))
            continue
        if status.get("url_count", 0) >= 1:
            continue
        if status.get("loading") or status.get("status") == 1:
            print(f"[running] {task_name}:{shot} {node}", flush=True)
            continue
        missing.append((task_name, shot, node, "not-ready"))
    return missing


def trigger_one(task_name, shot, node, reason):
    print(f"[trigger] {task_name}:{shot} {node} reason={reason}", flush=True)
    try:
        runner.run_allow_created([runner.LIBTV, "node", "-p", runner.PROJECT_UUID, node, "-r"], timeout=1200)
    except Exception as exc:
        message = str(exc)
        print(f"[trigger-error] {task_name}:{shot} {message[:1000]}", flush=True)
        return message
    print(f"[triggered] {task_name}:{shot} {node}", flush=True)
    return "triggered"


def main():
    runner.run([runner.LIBTV, "project", "use", runner.PROJECT_UUID], timeout=60)
    items = []
    for task in target_tasks():
        items.extend(missing_video_items(task))

    print(f"[missing-count] {len(items)}", flush=True)
    for task_name, shot, node, reason in items:
        status_text = trigger_one(task_name, shot, node, reason)
        if "1200000136" in status_text or "算力不足" in status_text:
            print("[stop] LibTV capacity is insufficient. Stop retrying and rerun later.", flush=True)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
