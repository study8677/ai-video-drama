<div align="center">

# 🎬 AI Video Drama · MiniMax-H3 原生音画一体短剧流水线

**把小说、故事或一句话创意，一键转化为可直接跑在 Colab A100 上的连贯中文有声 AI 短剧**

*文 → 资 → 视 → 剪｜本地零 GPU 编导与质检 · 云端 `MiniMax-H3-GGUF` 首尾帧链式续演 · 自动剪辑成片*

<p>
  <a href="https://github.com/study8677/ai-video-drama/stargazers"><img src="https://img.shields.io/github/stars/study8677/ai-video-drama?style=for-the-badge&logo=github&color=f59e0b" alt="GitHub Stars"></a>
  <img src="https://img.shields.io/badge/Model-MiniMax--H3--GGUF-6366f1?style=for-the-badge" alt="MiniMax-H3">
  <img src="https://img.shields.io/badge/Engine-stable--diffusion.cpp-0ea5e9?style=for-the-badge" alt="stable-diffusion.cpp">
  <img src="https://img.shields.io/badge/Runtime-Colab%20A100-f97316?style=for-the-badge&logo=googlecolab&logoColor=white" alt="Colab A100">
  <img src="https://img.shields.io/badge/Projects-8%20Ready--to--Run-10b981?style=for-the-badge" alt="8 Projects">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-3b82f6?style=for-the-badge" alt="MIT License"></a>
</p>

<p>
  <a href="#-为什么选择这套流水线">核心亮点</a> ·
  <a href="#-整体架构">整体架构</a> ·
  <a href="#-内置-8-部即跑短剧工程">内置剧目</a> ·
  <a href="#-3-步极速出片">3步出片</a> ·
  <a href="#-prompt-与数据契约示例">数据契约</a> ·
  <a href="#-项目目录">项目目录</a>
</p>

</div>

---

## ✨ 为什么选择这套流水线？

传统 AI 短剧制作需要反复横跳：**抽卡生图 → 图生视频 → 单独配 TTS → 对口型 → 找拟音/BGM → 剪映手工对齐**，不仅人物容易“换镜变脸”，而且每次改一句台词就得整条重剪。

本项目借鉴 `Seedance2-Storyboard-Generator` 的 **“文 → 资 → 视 → 剪”** 工程化思想，专为 **`stable-diffusion.cpp` (`sd-cli`) + `MiniMax-H3-GGUF` 原生音画一体模型** 打造了一套 **以 `episodes.json` 为核心契约** 的全自动短剧流水线：

| 痛点 | 本项目解决方案 |
| :--- | :--- |
| **口型、拟音、配乐割裂** | 采用 MiniMax-H3 原生三段式 Prompt（画面动作 + 中文口型 `<d>[Chinese]</d>` + 环境拟音 + 背景配乐），单镜 ~5.17 秒一次生成立体声成片 |
| **跨镜头脸崩、换装、变声** | **三重防漂移锁**：固定角色资产卡（`S1/S2` 英文外貌+声线锚点）+ 尾帧定格描写 + `use_prev_last_frame` 物理尾帧链式传图（I2VA） |
| **切场时上一幕背景残留** | 严格区分同场景续演（`use_prev_last_frame: true` + `<Picture 1>`）与跨场新开（`false`），拼接时仅对衔接镜智能裁去 `0.042s` 去重帧 |
| **A100 跑完 1 小时才发现写错** | 零依赖本地质检脚本 `validate_and_export.py`，提交 GPU 前自动拦截三段式缺漏、切场冲突、中文台词超字数（防 5 秒念不完） |
| **单镜不满意被迫整部重跑** | Colab 脚本原生支持 **断点续跑**（`SKIP_EXISTING`）与 **单镜改 Seed 定向重绘**（`ONLY_IDS = ["ep02_s03"]`），改完自动重拼全剧 |
| **写分镜与英文 Prompt 门槛高** | 内置开箱即用的 **AI Agent Skill**（`minimax-drama-generator`）+ 抖音爆款编剧 Prompt + 运镜光影音效英文词库，丢进小说自动产出全套工程 |

---

## 🏗️ 整体架构

**创作与算力彻底解耦**：本地无需任何 GPU，完成剧本创作、资产锁定与静态质检；云端 Colab A100 作为无状态渲染节点，拉取 `episodes.json` 自动出片。

```mermaid
flowchart LR
    A["🧠 Agent 编排与规范层<br/>AGENTS.md · SKILL.md<br/>抖音爆款编剧 Prompt · 词库"] --> B["📦 标准单剧工程包<br/>01_剧本 · 02_角色场景资产<br/>03_分镜脚本 · episodes.json"]
    B --> C["🛡️ 本地质检与同步门禁<br/>validate_and_export.py<br/>三段式 / 字数 / 切场 / 角色校验"]
    C -->|质检通过| D["⚡ Colab A100 推理引擎<br/>sd-cli + MiniMax-H3-GGUF<br/>T2VA 开场 / I2VA 尾帧链式续演"]
    D --> E["🎞️ 自动剪辑与验收<br/>ffmpeg 智能去重帧拼接<br/>单集 MP4 · 全剧 MP4 · 首尾帧故事板"]
```

---

## 🍿 内置 8 部即跑短剧工程

仓库已内置 **1 部横屏标准示例** + **7 部 100% 海外公版冷门名著本土化魔改竖屏抖音爆款短剧**（原著作者均已逝世 98~133 年，零版权风险，全部经 `validate_and_export.py` 零报错零警告通过）。完整剧目说明见 [projects/INDEX.md](projects/INDEX.md)：

| 编号 | 剧名 & 高能反转 | 题材 / 画幅 | 规格 | 工程直达 |
| :---: | :--- | :---: | :---: | :---: |
| **Demo** | **《卖水果不伤心》**<br>拜金前女友嘲讽男主摆摊卖水果，劳斯莱斯管家当场鞠躬揭晓千亿果园继承人身份 | 反转爽剧 · 16:9 横屏 | 4 镜 (~21s) | [剧本](projects/demo_fruit_drama/01_剧本.md) · [JSON](projects/demo_fruit_drama/episodes.json) |
| **EP01** | **《亡妻的“99元A货”竟值1180万》**<br>典当亡妻“拼夕夕假包”验出千万真顶奢，改娶清白老实妻后反而在豪宅崩溃怀念亡妻 | 人性伦理 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep01_fake_luxury_bag/01_剧本.md) · [JSON](projects/ep01_fake_luxury_bag/episodes.json) |
| **EP02** | **《百亿死对头困死货梯，门外竟是共同杀手》**<br>80 亿商战死对头困梯 68 小时血手印和解，撬门闯入的竟是二人各自买凶雇来的同一伙杀手 | 都市悬疑 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep02_elevator_interlopers/01_剧本.md) · [JSON](projects/ep02_elevator_interlopers/episodes.json) |
| **EP03** | **《装傻保洁阿姨，半小时逼疯恶意裁员HR总监》**<br>12 亿新资方女董穿保洁服暗访，一哭二闹逼疯冷血 HR 自掏 5 万跪求离开，反手亮身份开除 | 职场爽剧 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep03_harmless_cleaner/01_剧本.md) · [JSON](projects/ep03_harmless_cleaner/episodes.json) |
| **EP04** | **《暴雨民宿三个陌生人，我竟帮通缉犯抓了无辜者》**<br>暴雨夜众人联手抓了吓跑的瘦子，天亮特警破门：整晚温柔倒姜茶的灰衣大哥才是 A 级逃犯 | 暴雪山庄 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep04_three_strangers_rain/01_剧本.md) · [JSON](projects/ep04_three_strangers_rain/episodes.json) |
| **EP05** | **《控制狂老公空难身亡，我独享30亿狂欢59分钟后门开了》**<br>砸碎定位镯换红裙狂欢 59 分钟，改签生还的老公推门冷笑，她心梗离世反上热搜“喜极而亡” | 暗黑伦理 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep05_one_hour_freedom/01_剧本.md) · [JSON](projects/ep05_one_hour_freedom/episodes.json) |
| **EP06** | **《绑架欠薪黑心老板独子，三天后我倒贴20万求他领走》**<br>讨薪程序员绑走 8 岁熊孩子反被折磨到倒贴 20 万求爹领走，次日娃偷按爹指纹转回百万 | 荒诞喜剧 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep06_red_chief_ransom/01_剧本.md) · [JSON](projects/ep06_red_chief_ransom/episodes.json) |
| **EP07** | **《被黑心老板逼跳28楼，我绝地反杀赢回千万，法医却说那是坠楼前0.3秒的幻觉》**<br>奇迹抓外机逃生、送仇人入狱、拥抱妻子瞬间白光炸裂——一切皆为 0.3 秒幻觉，死攥 U 盘终成绝杀 | 烧脑悬疑 · 9:16 竖屏 | 12 镜 (~62s) | [剧本](projects/ep07_rooftop_zero_three_sec/01_剧本.md) · [JSON](projects/ep07_rooftop_zero_three_sec/episodes.json) |

---

## 🚀 3 步极速出片

### 第 1 步：用 AI Agent 生成新剧（或直接选用内置 8 部剧）

使用支持 `AGENTS.md` / Agent Skills 的工具（如 **Antigravity / Cursor / Claude Code**）打开本仓库，直接丢给 AI 一段小说、故事梗概或一句话脑洞：

> 示例指令：`帮我把这篇小说改写成 3 集竖屏抖音反转短剧，按 minimax-drama-generator 规范输出到 projects/my_new_drama/`

AI 会严格按照 [SKILL.md](.agents/skills/minimax-drama-generator/SKILL.md) 自动产出标准四件套：
`01_剧本.md` · `02_角色与场景资产.md` · `03_分镜脚本.md` · `episodes.json`。

### 第 2 步：本地一键质检 & 文档同步

无需 GPU，使用 Python 3 标准库即可完成全项门禁校验，并把 `episodes.json` 同步渲染到可读分镜表 `03_分镜脚本.md`：

```bash
# 单部剧质检并同步分镜 Markdown
python3 scripts/validate_and_export.py projects/ep01_fake_luxury_bag/episodes.json --sync-md

# 一键全库 8 部剧批量质检
for f in projects/*/episodes.json; do
  python3 scripts/validate_and_export.py "$f"
done
```

质检脚本会自动校验：
- ✅ MiniMax-H3 三段式段落完整（`integrated_multimodal_description` / `overall_soundscape` / `non_diegetic_music`）
- ✅ `use_prev_last_frame` 开关与 `<Picture 1>` 首帧引用指令双向对齐、跨场景切换防残留警告
- ✅ `<d>[Chinese] ... </d>` 中文字数时长门禁（按 5.17s 推荐 ≤ 20 字、硬上限 24 字，防止语速崩坏）
- ✅ 角色代号 `(S1/S2/S3)` 与资产表一致、分辨率为 16 倍数

### 第 3 步：Colab A100 一键批量生成与无缝拼接

在已准备好 `stable-diffusion.cpp`（`sd-cli`）和 `MiniMax-H3-GGUF` 权重的 Colab A100 Notebook 中：

```bash
!git clone https://github.com/study8677/ai-video-drama.git /content/ai-video-drama
```

然后把 [colab/run_from_json_cell.py](colab/run_from_json_cell.py) 的代码粘贴到执行 Cell，将 `JSON_PATH` 指向任意剧目的 `episodes.json` 运行即可：

```python
JSON_PATH = Path("/content/ai-video-drama/projects/ep01_fake_luxury_bag/episodes.json")
SKIP_EXISTING = True       # 断点续跑：已生成的镜头自动跳过
ONLY_IDS = []              # 单镜精修：填 ["ep02_s03"] 改完 seed 即可只重绘这一镜
```

运行完成后自动在 `/content/outputs/<project_slug>/` 输出：
- 🎬 每集独立成片 `*_ep01.mp4`、`*_ep02.mp4` ...
- 🎬 全剧完整音画同步成片 `*_full.mp4`（H.264 + 32kHz 立体声 AAC）
- 🖼️ 逐镜「左首帧 → 右尾帧」连贯性验收故事板 `*_storyboard.png`

---

## 🧩 Prompt 与数据契约示例

<details>
<summary><b>点击展开查看 <code>episodes.json</code> 与 MiniMax-H3 三段式 Prompt 结构</b></summary>

```json
{
  "project_name": "亡妻的99元A货竟值1180万",
  "project_slug": "ep01_fake_luxury_bag",
  "style_prefix": "Modern Chinese urban suspense webtoon anime style, semi-realistic cel shading, dramatic chiaroscuro lighting",
  "video_config": {
    "width": 480,
    "height": 864,
    "fps": 24,
    "video_frames": 124,
    "steps": 20,
    "cfg_scale": 1.0,
    "sampling_method": "euler"
  },
  "characters": [
    {
      "code": "S1",
      "name": "周明",
      "appearance_en": "a 32-year-old Chinese man with tired sharp eyes, dark circles, wearing a worn charcoal grey jacket",
      "voice_en": "a gritty, weary, emotionally tense 30-year-old Chinese male baritone voice"
    }
  ],
  "shots": [
    {
      "id": "ep01_s02",
      "episode": 1,
      "shot_index": 2,
      "title": "第1集 镜2：拼夕夕A货反驳",
      "scene_id": "LOC1",
      "seed": 1102,
      "use_prev_last_frame": true,
      "init_image": null,
      "prompt": "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.\n\nintegrated_multimodal_description: [Shot 1] ... says in a gritty, weary Chinese male baritone voice (S1): <d>[Chinese] 别讹我！这是亡妻九十九块买的假包！</d> ...\n\noverall_soundscape: Palm slapping nervously on the glass counter, faint hum of the spotlight.\n\nnon_diegetic_music: Rising tense violin harmonics over a steady dark heartbeat pulse."
    }
  ]
}
```

</details>

---

## 📂 项目目录

```text
ai-video-drama/
├── AGENTS.md                                      # AI Agent 自动工作流规则与质量红线
├── README.md                                      # 项目总览与快速上手指南
├── LICENSE                                        # MIT 开源协议
├── .agents/skills/minimax-drama-generator/        # 专属编剧 & MiniMax-H3 分镜生成 Skill
│   ├── SKILL.md                                   # 6 步标准化创作工作流
│   └── references/
│       ├── drama-writing-guide.md                 # 小说瘦身、黄金3秒、四拍结构与口型台词铁律
│       ├── minimax-h3-prompt-spec.md              # MiniMax-H3 三段式 Prompt & JSON Schema 规范
│       └── camera-and-sound-lexicon.md            # 画风、运镜、光影、拟音与配乐英文词库
├── prompts/
│   └── douyin_drama_screenwriter.md               # 海外公版名著本土化魔改 · 抖音爆款总编剧提示词
├── scripts/
│   └── validate_and_export.py                     # 零依赖 episodes.json 质检与分镜同步工具
├── colab/
│   └── run_from_json_cell.py                      # Colab A100 批量推理、断点续跑、智能拼接与故事板脚本
└── projects/
    ├── INDEX.md                                   # 剧目总索引与批量校验指引
    ├── demo_fruit_drama/                          # 16:9 横屏标准示例：《卖水果不伤心》
    └── ep01_* ~ ep07_*/                           # 7 部 9:16 竖屏抖音爆款短剧标准四件套工程
```

---

## 🤝 参与贡献 & 交流

欢迎提交 PR 分享你的：
- 🆕 原创或公版改编的 `projects/<新剧>/` 完整短剧工程包（请确保先通过 `validate_and_export.py` 校验）
- 🎨 更多经过 MiniMax-H3 实测高响应的画风前缀、运镜与音效词库
- ⚙️ 面向不同显存/量化权重或新一代原生音画模型的推理脚本适配

如果这套流水线帮你省下了大量抽卡和剪辑时间，欢迎点一颗 ⭐ **Star** 支持！

## 📄 License

本项目基于 [MIT License](LICENSE) 开源。内置 7 部改编剧目均取材自作者逝世超 98 年的世界公版文学母题并已完成 100% 现代本土化再创作。
