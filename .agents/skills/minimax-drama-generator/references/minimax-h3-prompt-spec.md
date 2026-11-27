# MiniMax-H3 提示词与 JSON 工程规范

本规范完全对齐 `stable-diffusion.cpp`（`sd-cli -M vid_gen`）运行 `unsloth/MiniMax-H3-GGUF` 的实测最佳实践。

---

## 一、三段式 Prompt 强制结构

每个镜头的 `prompt` 字段**必须**包含以下三个段落（使用英文描述画面与声音，中文仅出现在 `<d>[Chinese] ... </d>` 对白标签和招牌/文字道具中）：

### 模式 A：新场景首镜（`use_prev_last_frame: false`）

```text
integrated_multimodal_description: [Shot 1] <画风前缀>, <景别与构图> at <场景固定英文锚点> during <时间与光线>. <角色1固定英文外貌+服装 (S1)> <动作状态>. <角色2固定英文外貌+服装 (S2)> <动作状态>. <说话人动作与情绪>, and says in a <说话人固定英文声线 (S1/S2)>: <d>[Chinese] 简短中文台词 </d> <说完后的反应动作、对方表情变化、运镜收尾与尾帧定格状态>.

overall_soundscape: <环境底噪>, <关键动作拟音>, <人声呼吸/倒吸气等细节>.

non_diegetic_music: <配乐乐器、风格、节奏与情绪走向>.
```

### 模式 B：同场景尾帧链式衔接（`use_prev_last_frame: true`）

第一行**必须原样包含** `<Picture 1>` 参考指令，并与正文空一行：

```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] <画风前缀>, continuing seamlessly from <Picture 1> at <场景固定英文锚点>. <紧接上一镜尾帧的运镜与动作延续>. <角色1 (S1)> ... says in a <固定英文声线 (S1)>: <d>[Chinese] 简短中文台词 </d> <结尾反应与新尾帧定格状态>.

overall_soundscape: <与画面强绑定的动作拟音 + 延续的环境音>.

non_diegetic_music: <承接上一镜并推进情绪的配乐>.
```

---

## 二、核心一致性约束（铁律）

1. **说话人标签锁定**：
   - 在角色外貌后和声线描述后都标注同一代号：`(S1)`、`(S2)`、`(S3)`。
   - 同一角色在全剧所有镜头中的年龄、发型、衣服颜色、声线形容词必须保持一致，不可前镜 `white T-shirt` 后镜写成 `white shirt`。
2. **中文字幕/口型标签规范**：
   - 格式严格为 `<d>[Chinese] 台词内容 </d>`（注意方括号和大小写）。
   - 如果镜头为纯动作/无台词空镜，可省略 `<d>` 标签，但在 `overall_soundscape` 中强化动作音效与环境音。
   - **字数红线**：124 帧（5.17 秒）内，所有 `<d>` 标签中的中文字符（不含标点）合计建议 **8~18 字**，硬上限 **24 字**。
3. **画面文字规范**：
   - 如场景中有招牌、信纸文字（如 `"不伤心水果摊"`），用英文双引号包住简短中文（≤ 6 字），且避免镜头快速晃动导致文字畸变。
4. **切场规则（何时设为 `false`）**：
   - 同一地点连续发生 → `use_prev_last_frame: true`（无缝延续光影、站位、服装）。
   - 切换地点（如从街头切到办公室）、闪回、或角色换装 → `use_prev_last_frame: false`。
   - 切场后拼接时，Colab 脚本会自动识别 `use_prev_last_frame == false`，**不裁切**该镜头的开头 `0.042s`。

---

## 三、`episodes.json` 标准 Schema

`episodes.json` 是连接剧本生成与 Colab `sd-cli` 批量渲染的唯一数据契约：

```json
{
  "project_name": "卖水果不伤心",
  "project_slug": "fruit_drama",
  "style_prefix": "Live-action, cinematic Chinese urban short-drama style",
  "video_config": {
    "width": 864,
    "height": 480,
    "fps": 24,
    "video_frames": 124,
    "steps": 20,
    "cfg_scale": 1.0,
    "sampling_method": "euler"
  },
  "characters": [
    {
      "code": "S1",
      "name": "陈默",
      "appearance_en": "a handsome 26-year-old Chinese man with neat short black hair, wearing a clean white T-shirt and a dark green canvas apron",
      "voice_en": "a warm, calm, slightly amused Chinese baritone voice"
    }
  ],
  "shots": [
    {
      "id": "ep01_s01",
      "episode": 1,
      "shot_index": 1,
      "title": "第1集 镜1：街头羞辱",
      "scene_id": "LOC1",
      "seed": 101,
      "use_prev_last_frame": false,
      "init_image": null,
      "summary_zh": "红裙拜金女在夕阳水果摊前嘲讽男主落魄卖水果，男主平静抬眼微笑。",
      "dialogue_zh": "S2：哟，落魄到卖水果，真让人伤心啊！",
      "end_frame_anchor_zh": "两人隔着水果摊对视，男主双手停在车厘子上，嘴角挂着平静微笑。",
      "prompt": "integrated_multimodal_description: [Shot 1] ..."
    }
  ]
}
```

### 字段说明
- `id`：唯一镜头 ID（建议 `ep01_s01` 格式，文件名直接复用）。
- `use_prev_last_frame`：`true` 表示自动取上一镜尾帧作为 `-i`；`false` 表示新开场景。
- `init_image`：可选。当 `use_prev_last_frame: false` 且你希望用自己准备的首帧图开场时，填入图片路径（否则填 `null` 走纯文生 T2VA）。
- `video_config`：可按需微调，单镜也可以通过可选字段覆盖 `video_frames`（例如高潮特写用 `97` 帧 ≈ 4 秒，长对白用 `145` 帧 ≈ 6 秒，需满足 `4k+1` 或模型支持帧数，默认 `124` 为实测稳定值）。
