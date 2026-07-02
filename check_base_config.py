import subprocess, json

LIBTV = r"C:\Users\gba\.libtv\libtv.exe"
P = "4bc1c28bb3754d8ca3521aa6df975130"

# Check how the 24组 base was configured
r = subprocess.run([LIBTV, "node", "567873f5-7e05-4e8f-b714-97b5d65db302", "-p", P],
                   capture_output=True, timeout=15)
data = json.loads(r.stdout)
params = data.get("data", {}).get("params", {})

print("=== 24组基准图完整配置 ===")
print(f"modeType: {params.get('modeType')}")
print(f"model: {params.get('model')}")
print(f"prompt (first 500): {params.get('prompt','')[:500]}")
print(f"\nsettings: {json.dumps(params.get('settings',{}), ensure_ascii=False, indent=2)}")
print(f"\nimageList ({len(params.get('imageList',[]))} items):")
for img in params.get("imageList", []):
    print(f"  {img.get('nodeName')} ({img.get('nodeId')})")
print(f"\nurls: {data.get('data',{}).get('url',[])}")
