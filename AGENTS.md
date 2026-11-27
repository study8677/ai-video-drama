# AI 短剧创作工作区（MiniMax-H3 流水线）

本工作区用于将**小说、故事或一句话创意**转化为可直接运行在 Google Colab A100（`stable-diffusion.cpp` + `MiniMax-H3-GGUF`）上的**多集连贯中文有声短剧**。

## 核心工作流

当用户提供小说原文、故事梗概或短剧创意时，优先读取并严格遵循本工作区技能：
- `.agents/skills/minimax-drama-generator/SKILL.md`

### 标准产出目录

每个短剧项目独立存放在 `projects/<项目名>/` 下，必须包含：
1. `01_剧本.md`：核心梗、人物弧线、分集大纲与微短剧剧本
2. `02_角色与场景资产.md`：固定角色代号（`S1/S2/S3...`）、固定英文外貌/穿搭锚点、固定英文声线锚点、场景与道具锚点
3. `03_分镜脚本.md`：按 ~5 秒（124 帧 @ 24fps）切分的逐镜分镜表（含中文剧情、尾帧锚点、衔接模式、完整 MiniMax-H3 三段式 Prompt）
4. `episodes.json`：经 `scripts/validate_and_export.py` 校验通过的可执行剧本包，可直接喂给 `colab/run_from_json_cell.py` 批量出片

## 质量红线

- 每个 Shot（~5.17 秒）最多 **1~2 句简短中文台词（总计不超过 22 个汉字）**，防止语速过快或口型崩坏。
- 同场景连续镜头必须启用 `use_prev_last_frame: true` 并在 Prompt 开头声明 `<Picture 1>` 衔接；**切换新地点或大时间跳跃时必须设为 `false`**，避免上一场背景强行残留。
- 所有角色在每个出场镜头的英文外貌词与声线描述必须与 `02_角色与场景资产.md` 保持一致。
- 生成 `episodes.json` 后，必须运行 `python3 scripts/validate_and_export.py <episodes.json>` 做格式与字数质检。
