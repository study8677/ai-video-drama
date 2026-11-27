---
name: minimax-drama-generator
description: 将小说、故事或一句话创意转化为适配 MiniMax-H3（Colab A100 + stable-diffusion.cpp）的多集连贯中文有声短剧剧本、角色与场景资产库、逐5秒分镜脚本及可执行 episodes.json。当用户提供小说原文、故事大纲、要求改编短剧、编写分镜提示词或导出 Colab 剧本包时激活。
---

# MiniMax-H3 短剧剧本与分镜生成器

融合“文 → 资 → 视 → 剪”四段式短剧工业化流程与 MiniMax-H3 原生音画一体特性，把小说/故事高效拆解为**每镜 ~5.17 秒（124 帧 @ 24fps）、首尾帧链式衔接、自带中文口型对白与立体声音效配乐**的完整短剧工程。

## 必读参考规范

在开始写剧本和分镜前，按阶段查阅以下参考文件：
- **编剧与小说改编**：`references/drama-writing-guide.md`
- **MiniMax-H3 提示词与 JSON 规范**：`references/minimax-h3-prompt-spec.md`
- **运镜、光影与声音中英词库**：`references/camera-and-sound-lexicon.md`

---

## 标准执行流程（6 步）

### Step 1：吃透小说/素材 & 确认制作参数

收到用户提供的小说或故事后，先快速提炼：
- 主角与核心对手（控制在 **2~4 个核心人物**，避免单镜头人物过多导致脸崩）
- 最强爽点 / 反转 / 情绪爆点（短剧删繁就简，保留高冲突名场面）
- 主场景数量（建议每集聚焦 **1~2 个核心场景**，最大化利用首尾帧衔接保连贯）

向用户确认以下 5 项参数（若用户说“你定/按默认”，直接采用括号内默认值）：
1. **视觉风格**（默认：`Live-action, cinematic Chinese urban short-drama style` 电影感真人短剧；可选古装武侠、赛博朋克、新中式水墨动漫等）
2. **画幅分辨率**（默认：`864x480` 横屏 16:9，与 A100 Colab 实测一致；如需竖屏抖音风可设为 `480x864`）
3. **总集数与单集镜头数**（默认：每集 4 个连续 Shot ≈ 20 秒；可按小说篇幅规划 1~5 集）
4. **情感基调**（如：反转爽剧 / 悬疑惊悚 / 甜宠轻喜 / 虐恋复仇 / 热血武侠）
5. **项目文件夹名**（英文或拼音简写，用于 `projects/<project_slug>/`）

---

### Step 2：产出大纲与《01_剧本.md》（先确认再写分镜）

遵循 `references/drama-writing-guide.md`：
- 严格执行 **黄金 3 秒 + 冲突前置 + 情绪拉扯 + 阶段反转 + 结尾留钩**；
- 先向用户呈现 **一句话卖点 + 人物小传 + 分集/分镜剧情大纲**；
- 经用户确认（或用户要求一步到位直接生成）后，写入 `projects/<project_slug>/01_剧本.md`。

---

### Step 3：锁定《02_角色与场景资产.md》（防漂移核心）

MiniMax-H3 的跨镜头视觉与音色一致性高度依赖**重复且稳定的英文锚点描述**。必须为所有出场角色、场景和关键道具建立唯一编号与固定英文锚点：

| 类型 | 编号规则 | 必填内容 |
| :--- | :--- | :--- |
| **角色** | `S1`, `S2`, `S3`... | 中文名、角色定位、**固定英文外貌+服装词**（不可随镜头随意更改）、**固定英文声线词**（年龄+性别+情绪+音色，如 `warm, calm Chinese baritone voice`） |
| **场景** | `LOC1`, `LOC2`... | 地点、时间段、光线色调、**固定英文环境与标志物描述**（如招牌文字、陈设细节） |
| **道具** | `PROP1`, `PROP2`... | 关键道具固定英文描述（颜色、材质、大小） |

写入 `projects/<project_slug>/02_角色与场景资产.md`。

---

### Step 4：逐 5 秒切分并生成《03_分镜脚本.md》

将剧本拆解为连续的 ~5.17 秒（124 帧 @ 24fps）镜头，严格遵守 `references/minimax-h3-prompt-spec.md`：

1. **单镜信息密度约束**：
   - 每个 Shot 只完成 **1 个核心节拍**（压迫 / 反击 / 突发事件 / 揭示 / 反转）；
   - 中文对白 `<d>[Chinese] ... </d>` 总字数严格控制在 **8~20 个汉字**（最多不超过 24 字），保证 5 秒内吐字清晰、留有表演气口；
   - 严禁在同一 Shot 内塞入 3 个以上复杂连贯动作或多次大幅景别切换。
2. **智能衔接策略（关键）**：
   - **同场景连续动作** → `use_prev_last_frame: true`，Prompt 第一行**必须**写：
     `For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.`
   - **第一镜 / 切换新场景 / 大幅时间跳跃** → `use_prev_last_frame: false`，Prompt **不可**出现 `<Picture 1>`，需完整重新锚定场景与角色外观。
3. **尾帧锚点（End-Frame Anchor）**：
   - 在每个 Shot 的描述末尾，显式写出镜头结束瞬间的定格画面（人物站位、视线方向、手势、表情），下一镜开头直接顺着这个姿势继续演，衔接最自然。
4. **完整三段式结构**：
   - `integrated_multimodal_description: [Shot 1] ...`
   - `overall_soundscape: ...`
   - `non_diegetic_music: ...`

写入 `projects/<project_slug>/03_分镜脚本.md`。

---

### Step 5：导出 `episodes.json` 并执行自动质检

将所有镜头按标准 Schema 写入 `projects/<project_slug>/episodes.json`，然后**必须**在终端执行校验脚本：

```bash
python3 scripts/validate_and_export.py projects/<project_slug>/episodes.json
```

若校验脚本报任何 `ERROR`（如缺少三段式字段、`<Picture 1>` 与 `use_prev_last_frame` 冲突、台词超长、角色代号未对齐），**必须全部修复并重新校验通过**后才算完成。

---

### Step 6：交付与迭代支持

向用户汇报：
- 生成的 4 个文件链接；
- 总镜头数、预计总时长与预估 A100 生成耗时（约 3.5~4 分钟/镜）；
- 提醒用户：在 Colab 跑完初版后，如某一镜口型或动作不满意，只需修改 `episodes.json` 中该镜的 `seed` 或微调 `prompt`，在 Colab 设置 `ONLY_IDS = ["ep02_s02"]` 即可单独重绘并自动重新拼接全片。
