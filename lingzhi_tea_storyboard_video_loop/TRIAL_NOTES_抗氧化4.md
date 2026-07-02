# 抗氧化4试跑记录

日期：2026-06-23

输入文件：

```text
C:\Users\gba\Downloads\新灵芝茶拍摄脚本分镜-抗氧化-4.xlsx
```

正确产品：

```text
灵芝黄芪枸杞茶
```

正确参考图：

```text
outputs/灵芝茶24组_分镜图片视频流程/00_产品图解压/外包装/黄芪枸杞.png
outputs/灵芝茶24组_分镜图片视频流程/00_产品图解压/茶包背面透明图/黄芪枸杞.png
产品图/茶包正面.png
```

本次已踩坑：

1. 误用了 `五芝茶.png` 外包装。
   - 处理：已从试跑组解绑。
   - 沉淀规则：每次跑前必须确认产品全名，不沿用历史项目产品图。

2. 误以为 `抗氧化-4` 是 10 个镜头。
   - 实际：Excel 第 3-15 行，共 13 个镜头。
   - 沉淀规则：必须读取 Excel 到最后一行，以实际镜头数为准。

3. `libtv group <group> -p <project>` 没按预期作用到目标项目。
   - 表现：上传返回成功，但目标组查询为空。
   - 处理：先执行 `libtv project use 4bc1c28bb3754d8ca3521aa6df975130`，再做 group 绑定。
   - 沉淀规则：操作 group 前必须先绑定当前目录项目，再查 group。

4. PowerShell 内联中文 prompt 变成 `????`。
   - 表现：基准图节点 prompt 读回全是问号。
   - 处理：该基准图作废；改为 UTF-8 Python 脚本生成 prompt 并调用 CLI。
   - 沉淀规则：不要用 PowerShell 内联中文长 prompt。

5. 带产品参考图入边时，图片节点必须设置 `modeType=image2image`。
   - 表现：LibTV 报“图片生成节点须为图生图模式”。
   - 处理：创建图片节点时加 `-s modeType=image2image`。

6. UTF-8 Python 调 CLI 后，中文产品名仍可能在 LibTV 节点里变成 mojibake。
   - 表现：英文 prompt 正常，但 `灵芝黄芪枸杞茶` 读回成 `��֥...`。
   - 处理：该基准图不继续作为批量分镜依据；下一轮改用英文/拼音产品描述 `Lingzhi Huangqi Gouqi Tea`，包装中文靠参考图锁定。
   - 沉淀规则：生产跑图发给 LibTV 的 prompt 主体用英文，创建后读回检查 `????` 和 `��`。

当前试跑组：

```text
项目：灵芝茶24组全量分镜视频_0622
project_uuid：4bc1c28bb3754d8ca3521aa6df975130
group：抗氧化4_loop试跑_0622
group_id：5212a505-5586-4399-a94b-3df197a01758
```

当前正确产品参考节点：

```text
外包装黄芪枸杞：a5c904df-b267-459a-8200-1838e51a1628
茶包背面黄芪枸杞：ac460623-1894-4821-b693-d67280a70165
茶包正面灵芝茶：27b60e75-9717-487a-8efa-a81920c81526
```

试跑脚本：

```text
outputs/抗氧化4_loop试跑_0623/run_antioxidant4_trial.py
```
