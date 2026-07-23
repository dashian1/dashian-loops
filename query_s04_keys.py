import subprocess, json

LIBTV = r"C:\Users\gba\.libtv\libtv.exe"
P = "4bc1c28bb3754d8ca3521aa6df975130"

keys = {}
for i in range(1, 14):
    name = f"脚本04_{i:02d}_镜头{i}_单独分镜"
    r = subprocess.run([LIBTV, "node", name, "-p", P], capture_output=True, timeout=30)
    if r.returncode == 0:
        data = json.loads(r.stdout)
        keys[str(i)] = data.get("nodeKey")
        print(f"Shot {i}: {keys[str(i)]}")
    else:
        err = r.stderr.decode("utf-8", errors="replace")[:200]
        print(f"Shot {i}: FAIL - {err}")

with open(r"E:\大师安素材库\大师安工具矩阵\outputs\script04_keys.json", "w", encoding="utf-8") as f:
    json.dump(keys, f, ensure_ascii=False, indent=2)
print(f"Saved {len(keys)} keys")
