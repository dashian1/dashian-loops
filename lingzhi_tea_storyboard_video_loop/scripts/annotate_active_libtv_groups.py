import importlib.util
import json
import subprocess
from pathlib import Path


LIBTV = r"C:\Users\gba\.libtv\libtv.exe"
PROJECT_UUID = "4bc1c28bb3754d8ca3521aa6df975130"
RUNNER_PATH = Path(r"E:\灵鹤芝谷素材库\灵鹤芝谷工具矩阵\loops\lingzhi_tea_storyboard_video_loop\scripts\run_antioxidant_two_batch.py")

spec = importlib.util.spec_from_file_location("runner", RUNNER_PATH)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


TASK_NOTES = {
    "script20": {
        "group": "script20_loop_0623",
        "note": "待处理：LibTV已完成3/6，缺镜头3、5、6。已切到 Seedance 2.0 Fast VIP / 480p，但卡算力。继续跑前先确认算力；赶交付优先小云雀补跑。",
    },
    "script21": {
        "group": "script21_loop_0623",
        "note": "待处理：LibTV视频0/6。图片已完成6/6，视频节点已建 Fast / 480p，但卡算力。继续跑前先确认算力；赶交付优先小云雀补跑。",
    },
    "script22": {
        "group": "script22_loop_0623",
        "note": "待处理：LibTV视频0/7。图片已完成7/7，视频节点已建 Fast / 480p，但卡算力。继续跑前先确认算力；赶交付优先小云雀补跑。",
    },
    "script23": {
        "group": "script23_loop_0623",
        "note": "待处理：LibTV视频0/9。图片已完成9/9，视频节点已建 Fast / 480p，但卡算力。继续跑前先确认算力；赶交付优先小云雀补跑。",
    },
    "script24": {
        "group": "script24_loop_0623",
        "note": "已交付：LibTV视频0/9不是交付缺失。脚本24已通过小云雀补跑9/9并生成飞书表，不要重复追LibTV，除非用户明确要求回填LibTV画布。",
    },
}


def run(cmd):
    proc = subprocess.run(
        cmd,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        shell=False,
        timeout=300,
    )
    if proc.returncode != 0:
        raise RuntimeError(" ".join(cmd) + "\n" + proc.stdout + "\n" + proc.stderr)
    return proc.stdout


def first_json(text):
    start = text.find("{")
    if start < 0:
        raise ValueError(text[:1000])
    return json.loads(text[start:])


def node_list(group):
    return first_json(run([LIBTV, "node", "list", "-g", group])).get("nodes", [])


def create_or_update_text(group, name, content):
    for node in node_list(group):
        if node.get("name") == name:
            run(
                [
                    LIBTV,
                    "node",
                    node["id"],
                    "-g",
                    group,
                    "-u",
                    "content=" + json.dumps([content], ensure_ascii=False),
                    "-u",
                    "contentWidth=780",
                ]
            )
            print(f"[updated] {group} / {name}", flush=True)
            return
    run(
        [
            LIBTV,
            "node",
            "--x",
            "80",
            "--y",
            "80",
            "create",
            name,
            "-t",
            "text",
            "-g",
            group,
            "-u",
            "content=" + json.dumps([content], ensure_ascii=False),
            "-u",
            "contentWidth=780",
        ]
    )
    print(f"[created] {group} / {name}", flush=True)


def computed_status(task_name):
    state = runner.load_state()
    rows = runner.read_rows(runner.TASKS[task_name]["source_xlsx"])
    shots = state.get("tasks", {}).get(task_name, {})
    lines = []
    for row in rows:
        shot = str(row["shot"])
        item = shots.get(shot, {})
        image_ready = (item.get("image_status") or {}).get("url_count", 0) >= 1
        video_ready = (item.get("video_status") or {}).get("url_count", 0) >= 1
        ext_ready = bool(item.get("external_video_path"))
        mark = "完成" if video_ready else ("外部完成" if ext_ready else "缺视频")
        lines.append(f"镜头{int(shot):02d}: 图={'有' if image_ready else '缺'} / LibTV视频={'有' if video_ready else '缺'} / {mark}")
    return "\n".join(lines)


def main():
    run([LIBTV, "project", "use", PROJECT_UUID])
    for task, cfg in TASK_NOTES.items():
        content = cfg["note"] + "\n\n" + computed_status(task)
        create_or_update_text(cfg["group"], "00_本组状态_先看这里", content)


if __name__ == "__main__":
    main()
