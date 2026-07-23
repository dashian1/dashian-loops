import json
import subprocess
from pathlib import Path


LIBTV = r"C:\Users\gba\.libtv\libtv.exe"
PROJECT_UUID = "4bc1c28bb3754d8ca3521aa6df975130"
STATE_PATH = Path(r"E:\大师安素材库\大师安工具矩阵\outputs\批量脚本视频任务_0623\antioxidant_two_run_state.json")


MASTER_GROUP = "00_总控_当前工作台_0629"
ACTIVE_GROUP = "01_待处理_LibTV卡算力_脚本20-23"
DELIVERED_GROUP = "02_已交付_LibTV批量组"
EXTERNAL_GROUP = "03_外部补跑_小云雀"
ARCHIVE_GROUP = "90_历史单独分镜图_归档"
STAGE_GROUPS = ["00_产品参考", "01_脚本拆分", "02_人物场景基准", "04_视频节点", "05_下载整理"]

DELIVERED_TASKS = [
    "抗氧化1_loop跑批_0623",
    "抗氧化4_loop跑批_0623",
    "script02_loop_0623",
    "script03_loop_0623",
    "script04_loop_0623",
    "script05_loop_0623",
    "script06_loop_0623",
    "script07_loop_0623",
    "script08_loop_0623",
    "script09_loop_0623",
    "script10_loop_0623",
    "script11_loop_0623",
    "script12_loop_0623",
    "script13_loop_0623",
    "script14_loop_0623",
    "script15_loop_0623",
    "script16_loop_0623",
    "script17_loop_0623",
    "script18_loop_0623",
    "script19_loop_0623",
]

ACTIVE_TASKS = [
    "script20_loop_0623",
    "script21_loop_0623",
    "script22_loop_0623",
    "script23_loop_0623",
]

EXTERNAL_TASKS = [
    "script24_loop_0623",
]


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


def groups():
    return {g["name"]: g for g in first_json(run([LIBTV, "group", "list"]))["groups"]}


def ensure_group(name, parent=None):
    existing = groups()
    if name in existing:
        return existing[name]["groupNodeKey"]
    cmd = [LIBTV, "group", "create", name]
    if parent:
        cmd.extend(["-g", parent])
    data = first_json(run(cmd))
    return data.get("groupNodeKey") or data.get("nodeKey") or data.get("newNodeKey")


def query_group(name):
    return first_json(run([LIBTV, "group", name]))


def create_text_node(name, content, parent):
    node_list = first_json(run([LIBTV, "node", "list", "-g", parent]))
    for node in node_list.get("nodes", []):
        if node.get("name") == name:
            run([LIBTV, "node", node["id"], "-g", parent, "-u", "content=" + json.dumps([content], ensure_ascii=False)])
            print(f"[updated-text] {name}", flush=True)
            return node["id"]
    data = first_json(
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
                parent,
                "-u",
                "content=" + json.dumps([content], ensure_ascii=False),
                "-u",
                "contentWidth=900",
            ]
        )
    )
    print(f"[created-text] {name}", flush=True)
    return data.get("newNodeKey") or data.get("nodeKey") or data.get("id")


def status_summary():
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    tasks = state.get("tasks", {})
    lines = [
        "灵芝茶24组全量分镜视频_0622 | 当前画布工作台",
        "",
        "交付口径：一个脚本一个飞书表格；视频链接必须是飞书 file 预览链接。",
        "视频参数：480p；不要字幕；口播不改写；真实时长写模型参数。",
        "",
        "已交付：抗氧化1、抗氧化4、脚本02-19、脚本06、脚本24（小云雀补跑）。",
        "LibTV剩余卡算力：脚本20缺3个，脚本21缺6个，脚本22缺7个，脚本23缺9个。",
        "脚本24：LibTV视频0/9，但小云雀已完成9/9并交付，不要重复追LibTV。",
        "",
        "分组说明：",
        "01_待处理_LibTV卡算力_脚本20-23：只放后续要盯的LibTV任务。",
        "02_已交付_LibTV批量组：已完成批量组，除非返修不要动。",
        "03_外部补跑_小云雀：外部补跑记录。",
        "90_历史单独分镜图_归档：旧的单独图片组，默认不作为主流程入口。",
    ]
    for task_name in ["script20", "script21", "script22", "script23", "script24"]:
        shots = tasks.get(task_name, {})
        ready = 0
        total = len(shots)
        for item in shots.values():
            st = item.get("video_status") or {}
            if st.get("url_count", 0) >= 1:
                ready += 1
        lines.append(f"{task_name}: LibTV video {ready}/{total}")
    return "\n".join(lines)


def main():
    run([LIBTV, "project", "use", PROJECT_UUID])
    ensure_group(MASTER_GROUP)
    all_group_names = set(groups().keys())
    archive_groups = sorted(name for name in all_group_names if name.startswith("脚本") and name.endswith("_单独分镜图"))
    ensure_group(ACTIVE_GROUP, MASTER_GROUP)
    ensure_group(DELIVERED_GROUP, MASTER_GROUP)
    ensure_group(EXTERNAL_GROUP, MASTER_GROUP)
    ensure_group(ARCHIVE_GROUP, MASTER_GROUP)
    ensure_group("04_流程固定入口", MASTER_GROUP)
    create_text_node("00_状态看板_不要删", status_summary(), MASTER_GROUP)
    create_text_node("待处理组清单", "\n".join(ACTIVE_TASKS), ACTIVE_GROUP)
    create_text_node("已交付组清单", "\n".join(DELIVERED_TASKS), DELIVERED_GROUP)
    create_text_node("小云雀补跑清单", "\n".join(EXTERNAL_TASKS), EXTERNAL_GROUP)
    create_text_node("历史单独分镜组清单", "\n".join(archive_groups), ARCHIVE_GROUP)
    create_text_node("固定流程入口清单", "\n".join(STAGE_GROUPS), "04_流程固定入口")
    print("[done] canvas control groups and status board ensured", flush=True)


if __name__ == "__main__":
    main()
