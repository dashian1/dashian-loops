import subprocess, json

LIBTV = r"%USERPROFILE%\.libtv\libtv.exe"
P = "4bc1c28bb3754d8ca3521aa6df975130"

# Check existing script01 image node for full config
r = subprocess.run([LIBTV, "node", "efad5e13-4b5b-4413-ad64-b6e0f96d0e88", "-p", P], capture_output=True, timeout=15)
data = json.loads(r.stdout)
params = data.get("data", {}).get("params", {})
settings = params.get("settings", {})

print("=== modeType ===")
print(params.get("modeType"))
print("=== settings ===")
print(json.dumps(settings, indent=2, ensure_ascii=False))
print("=== imageList ===")
for img in params.get("imageList", []):
    print(f"  {img.get('nodeName')} ({img.get('nodeId')})")
print("=== prompt (first 200) ===")
print(params.get("prompt", "")[:200])
