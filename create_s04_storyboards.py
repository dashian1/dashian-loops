"""抗氧化-4: 重建13个分镜图节点 — 正确model/比例/连线/位置"""
import subprocess, json

LIBTV = r"C:\Users\gba\.libtv\libtv.exe"
P = "4bc1c28bb3754d8ca3521aa6df975130"

# 产品参考(4个) + UGC基准
UGC_BASE = "c89cef31-c7ba-40a6-bde3-20eeeceddb3a"
PRODUCT_REFS = [
    "27b60e75-9717-487a-8efa-a81920c81526",  # 茶包正面灵芝茶
    "cc62080d-9d28-4d03-b718-2d627c4c8b2e",  # 茶包正面
    "a5c904df-b267-459a-8200-1838e51a1628",  # 外包装黄芪枸杞
    "ac460623-1894-4821-b693-d67280a70165",  # 茶包背面
]
ALL_REFS = [UGC_BASE] + PRODUCT_REFS

def libtv(*args, timeout=60):
    try:
        return subprocess.run([LIBTV] + list(args), capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return None

shots = [
    (1,  "果蔬快切→女主捧灵芝茶", """9:16竖屏，真实UGC手机拍摄感，居家治愈风。果蔬特写快切画面——番茄、草莓、猕猴桃、黄瓜切片在白色台面上依次闪过，色彩鲜艳有食欲。画面中心定格在女主双手捧着一杯灵芝茶的琥珀色茶汤。女主神情淡然，目光看向镜头，自然裸妆，米白色家居服。同一人物，同一场景，背景虚化可见原木餐桌和温暖自然光"""),
    (2,  "女主前倾眼神笃定", """9:16竖屏，真实UGC手机拍摄感。近景拍女主面部，她放下茶杯，身体微微前倾，眼神笃定而真诚。自然裸妆，中长发，米白色家居服。柔光从左侧洒入。同一人物，手持手机拍摄感"""),
    (3,  "产品盒推近品牌标识", """9:16竖屏，真实UGC手机拍摄感。产品包装盒平稳放在米白色桌面上，镜头推近盒身的品牌标识和合作字样。一只手轻扶盒边，动作轻柔。牛皮纸原色外盒，渐变色开窗，可见盒面印有品牌标识。柔和顶光，桌面反光自然。保持产品包装上原有印刷文字"""),
    (4,  "拆茶包倒灵芝片", """9:16竖屏，真实UGC手机拍摄感。近景俯拍——双手拆开茶包，将原料倒在白瓷盘里。灵芝切片清晰可见，深褐色大块约1.5-3cm，木质纹理分明。旁边散落红枣片、枸杞等。指尖轻拨原料，动作缓慢自然。桌面俯拍场景，柔光均匀"""),
    (5,  "航天育种标识特写", """9:16竖屏，真实UGC手机拍摄感。特写推镜——产品包装上的航天育种合作标识，手指缓慢划过字样。铝箔磨砂袋上的灵芝茶书法字清晰可见。浅景深，背景虚化干净。柔和侧光，包装文字保留原样"""),
    (6,  "果蔬对比→茶包手部特写", """9:16竖屏，真实UGC手机拍摄感。果蔬对比画面——紫甘蓝切面、彩椒切块在白色台面上快速闪过，色彩饱和。本镜头不出现本品包装。画面最终切到一只手持灵芝茶包的手部特写。光影流畅"""),
    (7,  "女主拿茶包对镜头", """9:16竖屏，真实UGC手机拍摄感。中景拍女主上半身，她面对镜头，手拿灵芝茶包展示，神情自然亲切。女主自然裸妆，米白色家居服，中长发。居家餐桌背景，柔光漫射。同一人物，手持拍摄感。茶包上灵芝茶书法字保留原样"""),
    (8,  "九味食材扫镜", """9:16竖屏，真实UGC手机拍摄感。近景平移扫镜——白瓷盘内红枣、枸杞、黄芪、党参、桂圆、陈皮、重瓣红玫瑰、茉莉花等食材依次呈现，颗粒饱满色泽自然，食材颜色层次丰富。桌面俯拍，柔光均匀，画面干净"""),
    (9,  "女主闻茶香笑", """9:16竖屏，真实UGC手机拍摄感。近景拍女主面部和茶杯——她双手端起茶杯凑近鼻尖，轻闻茶香，面露愉悦笑意，双眼微闭。琥珀色茶汤在玻璃杯中透亮。同一人物，同款家居服，温暖柔光氛围"""),
    (10, "女主抿茶点头", """9:16竖屏，真实UGC手机拍摄感。中景拍女主上半身，她轻抿一口茶后放下茶杯，对着镜头微微点头，神态放松真诚，嘴角带笑。同一人物，同款家居服，居家餐桌场景。茶杯中琥珀色茶汤清晰可见"""),
    (11, "福利海报推近", """9:16竖屏，真实UGC手机拍摄感。桌面产品福利海报特写——产品盒与茶包摆放在一起，画面中有宠粉福利字样。镜头从产品中景推近到活动标识特写。温暖光线，背景干净。保留产品包装上原有文字"""),
    (12, "女主展示+产品堆头", """9:16竖屏，真实UGC手机拍摄感。中景拍女主手持茶包对镜头展示，身后桌面上产品盒整齐堆叠成堆头。女主眼神真诚。同一人物，同款家居服。柔光从正前方打亮，画面通透。产品包装文字保留原样"""),
    (13, "产品盒定格+下单箭头", """9:16竖屏，真实UGC手机拍摄感。近景产品定格画面——产品包装盒居中摆放，画面干净简约。盒身牛皮纸原色清晰可见，侧面有下单引导箭头指向产品。暖光照射，高级感定格。保留产品包装上原有印刷文字"""),
]

# Step 1: 删旧
for shot_num in range(1, 14):
    name = f"脚本04_{shot_num:02d}_镜头{shot_num}_单独分镜"
    libtv("node", "delete", name, "-p", P, timeout=15)
print("Old nodes cleaned.\n")

# Step 2: 创建 — 4行4列网格布局
created = []
for shot_num, label, prompt in shots:
    name = f"脚本04_{shot_num:02d}_镜头{shot_num}_单独分镜"
    col = (shot_num - 1) % 4
    row = (shot_num - 1) // 4
    x = 400 + col * 380
    y = 200 + row * 420

    # 镜头6是对比镜头，不连产品参考
    refs = [UGC_BASE] if shot_num == 6 else ALL_REFS

    args = ["node", "create", name, "-t", "image",
            "--prompt", prompt,
            "-s", "modeType=image2image",
            "-s", "ratio=9:16",
            "-s", "resolution=2K",
            "--x", str(x), "--y", str(y),
            "-p", P]
    for ref in refs:
        args.extend(["--left", ref])

    r = libtv(*args, timeout=60)
    if r and r.returncode == 0:
        data = json.loads(r.stdout)
        key = data.get("nodeKey")
        created.append({"shot": shot_num, "name": name, "key": key,
                        "x": x, "y": y, "refs": len(refs)})
        print(f"  OK  Shot{shot_num:02d} [{label}] → ({x},{y}) refs={len(refs)}")
    else:
        err = r.stderr.decode("utf-8", errors="replace")[:200] if r else "timeout"
        print(f"  FAIL Shot{shot_num:02d} → {err}")

print(f"\nCreated {len(created)}/{len(shots)} nodes")

# 保存配置
config = {"project_uuid": P, "script_id": "脚本04",
          "ugc_base": UGC_BASE, "product_refs": PRODUCT_REFS,
          "image_nodes": created}
with open(r"E:\灵鹤芝谷素材库\灵鹤芝谷工具矩阵\outputs\script04_image_nodes.json", "w", encoding="utf-8") as f:
    json.dump(config, f, ensure_ascii=False, indent=2)
print("Config saved.")
