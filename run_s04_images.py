import subprocess, json, time

LIBTV = r"%USERPROFILE%\.libtv\libtv.exe"
P = "4bc1c28bb3754d8ca3521aa6df975130"

with open(r"E:\大师安素材库\大师安工具矩阵\outputs\script04_image_nodes.json", encoding="utf-8") as f:
    config = json.load(f)

nodes = config["image_nodes"]
print(f"Triggering {len(nodes)} image nodes...")

# Trigger all — timeout is expected
for n in nodes:
    try:
        subprocess.run([LIBTV, "node", n["key"], "--run", "-p", P],
                       capture_output=True, timeout=15)
    except subprocess.TimeoutExpired:
        pass
    print(f"  Shot{n['shot']:02d}: submitted")

# Wait and check
print("\nWaiting 15s then checking status...")
time.sleep(15)

for n in nodes:
    try:
        r = subprocess.run([LIBTV, "node", n["key"], "-p", P],
                           capture_output=True, timeout=10)
        d = json.loads(r.stdout)
        s = d.get("taskInfo", {})
        url_count = len(d.get("data", {}).get("content", []) or [])
        print(f"  Shot{n['shot']:02d}: status={s.get('status')} progress={s.get('progressPercent')}% urls={url_count}")
    except Exception as e:
        print(f"  Shot{n['shot']:02d}: error - {e}")
