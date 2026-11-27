# AI 短剧剧本与分镜工作流（MiniMax-H3 版）

借鉴 `Seedance2-Storyboard-Generator` 的 **“文 → 资 → 视 → 剪”** 轻量工程化思路，针对本地 **Colab A100 + `stable-diffusion.cpp` + `MiniMax-H3-GGUF`** 原生音画一体生成流水线深度适配。

## 目录结构

```text
ai_video/
├── AGENTS.md                                      # Agent 自动工作流指引
├── .agents/skills/minimax-drama-generator/        # 专属编剧 & 分镜生成 Skill
│   ├── SKILL.md                                   # 完整创作流程与模板
│   └── references/
│       ├── drama-writing-guide.md                 # 小说改短剧、黄金3秒、冲突与留钩指南
│       ├── minimax-h3-prompt-spec.md              # MiniMax-H3 三段式 Prompt & JSON 规范
│       └── camera-and-sound-lexicon.md            # 运镜、光影、音效与配乐中英词库
├── scripts/
│   └── validate_and_export.py                     # 校验 episodes.json 并自动补全/生成分镜预览 Markdown
├── colab/
│   └── run_from_json_cell.py                      # 替换 Colab Cell 6：读取 episodes.json 批量生成与拼接
└── projects/
    └── demo_fruit_drama/                          # 基于《卖水果不伤心》整理的标准示例项目
```

## 快速使用（3 步出片）

### 第 1 步：丢小说或创意，生成剧本与分镜
直接把小说章节、故事梗概发给 AI，并说明你的偏好（视觉风格、画幅比例、预计总时长/集数）。AI 会按 `SKILL.md` 引导你确认大纲，并在 `projects/<剧名>/` 下生成：
- `01_剧本.md`
- `02_角色与场景资产.md`
- `03_分镜脚本.md`
- `episodes.json`

### 第 2 步：本地一键质检
```bash
python3 scripts/validate_and_export.py projects/<剧名>/episodes.json --sync-md
```
脚本会自动检查：
- MiniMax-H3 三段式标签是否完整（`integrated_multimodal_description` / `overall_soundscape` / `non_diegetic_music`）
- 首尾帧衔接模式（`use_prev_last_frame`）与 `<Picture 1>` 声明是否一致
- 中文台词标签 `<d>[Chinese] ... </d>` 字数是否超标（避免 5 秒内念不完）
- 参数合法性（宽高、帧数、seed、角色代号）

### 第 3 步：放进 Colab A100 批量出片
1. 将 `projects/<剧名>/episodes.json` 上传到 Colab（如 `/content/episodes.json`）或挂载到 Google Drive。
2. 用 [run_from_json_cell.py](colab/run_from_json_cell.py) 的代码替换你 Colab 的 Cell 6，修改顶部 `JSON_PATH` 后运行：
   - 支持**断点续跑**（已生成的镜头自动跳过）；
   - 支持**指定单镜重绘**（改 `ONLY_IDS = ["ep02_s01"]` 或调整 `seed` 重跑，不影响其他镜头）；
   - 自动按 `use_prev_last_frame` 智能决定是否裁去衔接首帧 `0.042s`，音画同步拼接成完整 MP4 并输出首尾帧连贯性故事板。
