#!/usr/bin/env python3
"""
MiniMax-H3 短剧 episodes.json 质检与分镜同步工具

用法:
  python3 scripts/validate_and_export.py projects/demo_fruit_drama/episodes.json
  python3 scripts/validate_and_export.py projects/demo_fruit_drama/episodes.json --sync-md
"""

import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED_TOP_KEYS = ["project_name", "project_slug", "style_prefix", "video_config", "characters", "shots"]
REQUIRED_SHOT_KEYS = ["id", "episode", "shot_index", "title", "scene_id", "seed", "use_prev_last_frame", "prompt"]

PICTURE_REF_LINE = "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced."
DIALOGUE_PATTERN = re.compile(r"<d>\s*\[Chinese\]\s*(.*?)\s*</d>", re.DOTALL)
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff]")
SPEAKER_PATTERN = re.compile(r"\((S\d+)\)")


def count_cjk(text: str) -> int:
    return len(CJK_PATTERN.findall(text))


def validate_project(data: dict) -> tuple[list[str], list[str], list[dict]]:
    errors: list[str] = []
    warnings: list[str] = []
    rows: list[dict] = []

    for k in REQUIRED_TOP_KEYS:
        if k not in data:
            errors.append(f"缺少顶层必填字段: {k}")
    if errors:
        return errors, warnings, rows

    vcfg = data["video_config"]
    fps = vcfg.get("fps", 24)
    default_frames = vcfg.get("video_frames", 124)
    width = vcfg.get("width", 864)
    height = vcfg.get("height", 480)
    if width % 16 != 0 or height % 16 != 0:
        warnings.append(f"分辨率 {width}x{height} 不是 16 的倍数，可能影响部分模型对齐")

    char_codes = {c.get("code") for c in data.get("characters", []) if c.get("code")}
    if not char_codes:
        warnings.append("characters 列表为空，建议定义 S1/S2 等角色外貌与声线锚点")

    shots = data.get("shots", [])
    if not shots:
        errors.append("shots 列表不能为空")
        return errors, warnings, rows

    seen_ids = set()
    prev_scene = None

    for idx, shot in enumerate(shots):
        sid = shot.get("id", f"<missing_id_{idx}>")
        for k in REQUIRED_SHOT_KEYS:
            if k not in shot:
                errors.append(f"[{sid}] 缺少必填字段: {k}")

        if sid in seen_ids:
            errors.append(f"[{sid}] 镜头 ID 重复")
        seen_ids.add(sid)

        use_prev = bool(shot.get("use_prev_last_frame", False))
        init_img = shot.get("init_image")
        prompt = shot.get("prompt", "")
        scene_id = shot.get("scene_id", "")
        frames = shot.get("video_frames", default_frames)
        dur_sec = frames / fps

        # 1. 首镜衔接逻辑
        if idx == 0 and use_prev:
            errors.append(f"[{sid}] 第 1 个镜头不能设置 use_prev_last_frame=true")

        # 2. 跨场景切换检查
        if idx > 0 and scene_id and prev_scene and scene_id != prev_scene and use_prev:
            warnings.append(
                f"[{sid}] 场景从 {prev_scene} 切换到 {scene_id}，但 use_prev_last_frame=true，可能导致旧场景残留，请确认是否应设为 false"
            )
        prev_scene = scene_id

        # 3. <Picture 1> 声明一致性
        has_pic_ref = "<Picture 1>" in prompt
        expects_pic = use_prev or bool(init_img)
        if expects_pic and not has_pic_ref:
            errors.append(
                f"[{sid}] 启用了首帧参考(use_prev_last_frame={use_prev}, init_image={init_img})，但 prompt 中缺少 <Picture 1> 参考声明"
            )
        if expects_pic and not prompt.lstrip().startswith("For the target video, at 0.00 seconds into the target video, <Picture 1>"):
            warnings.append(f"[{sid}] 建议将标准首帧声明放在 prompt 第一行: {PICTURE_REF_LINE}")
        if not expects_pic and has_pic_ref:
            errors.append(f"[{sid}] 未启用首帧参考，但 prompt 中出现了 <Picture 1>，会误导模型")

        # 4. MiniMax-H3 三段式结构检查
        for section in ("integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"):
            if section not in prompt:
                errors.append(f"[{sid}] prompt 缺少 MiniMax-H3 必备段落: {section}")

        if "[Shot 1]" not in prompt:
            warnings.append(f"[{sid}] 建议在 integrated_multimodal_description: 后保留 [Shot 1] 标记")

        # 5. 中文台词标签与字数检查
        dialogues = DIALOGUE_PATTERN.findall(prompt)
        if "<d>" in prompt and not dialogues:
            errors.append(f"[{sid}] 检测到 <d> 标签但格式不符合 <d>[Chinese] ... </d>")
        total_cjk = sum(count_cjk(d) for d in dialogues)
        max_recommended = int(round(dur_sec * 3.8))  # ~20 字 / 5.17s
        hard_limit = int(round(dur_sec * 4.7))       # ~24 字 / 5.17s
        if total_cjk > hard_limit:
            errors.append(f"[{sid}] 台词中文共 {total_cjk} 字，超过 {dur_sec:.1f}s 硬上限({hard_limit}字)，极易语速过快或截断")
        elif total_cjk > max_recommended:
            warnings.append(f"[{sid}] 台词中文共 {total_cjk} 字，略高于推荐值({max_recommended}字)，建议精简以留出表演气口")

        # 6. 角色代号一致性检查
        used_speakers = sorted(set(SPEAKER_PATTERN.findall(prompt)))
        for sp in used_speakers:
            if char_codes and sp not in char_codes:
                warnings.append(f"[{sid}] prompt 中使用了未在 characters 定义的角色代号: {sp}")

        rows.append({
            "id": sid,
            "ep": shot.get("episode"),
            "title": shot.get("title", ""),
            "scene": scene_id,
            "mode": "I2VA(尾帧)" if use_prev else ("I2VA(首图)" if init_img else "T2VA(新场)"),
            "dur": dur_sec,
            "cjk": total_cjk,
            "speakers": ",".join(used_speakers) or "-",
            "seed": shot.get("seed"),
        })

    return errors, warnings, rows


def render_storyboard_md(data: dict) -> str:
    vcfg = data["video_config"]
    fps = vcfg.get("fps", 24)
    default_frames = vcfg.get("video_frames", 124)

    lines = [
        f"# 《{data['project_name']}》逐镜分镜脚本（MiniMax-H3）",
        "",
        f"- **视觉风格**：`{data['style_prefix']}`",
        f"- **视频参数**：`{vcfg.get('width', 864)}x{vcfg.get('height', 480)}` · `{fps} fps` · 默认 `{default_frames}` 帧（约 `{default_frames/fps:.2f}s/镜`）",
        f"- **总镜头数**：{len(data['shots'])} 镜（预计总成片约 `{sum(s.get('video_frames', default_frames)/fps for s in data['shots']):.1f}s`）",
        "",
        "## 分镜总览表",
        "",
        "| 镜头 ID | 标题 | 场景 | 衔接模式 | Seed | 说话人 | 台词预览 |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :--- |",
    ]

    for s in data["shots"]:
        mode = "I2VA(尾帧衔接)" if s.get("use_prev_last_frame") else ("I2VA(指定首图)" if s.get("init_image") else "T2VA(新场开镜)")
        sp = ",".join(sorted(set(SPEAKER_PATTERN.findall(s.get("prompt", ""))))) or "-"
        dlg = s.get("dialogue_zh") or " / ".join(DIALOGUE_PATTERN.findall(s.get("prompt", ""))) or "（无台词）"
        lines.append(f"| `{s['id']}` | {s['title']} | `{s.get('scene_id', '-')}` | {mode} | `{s['seed']}` | {sp} | {dlg} |")

    lines.extend(["", "---", ""])

    for s in data["shots"]:
        mode = "I2VA 链式衔接上一镜尾帧" if s.get("use_prev_last_frame") else ("I2VA 指定首帧图" if s.get("init_image") else "T2VA 新场景开镜")
        lines.extend([
            f"## {s['id']}｜{s['title']}",
            "",
            f"- **场景**：`{s.get('scene_id', '-')}` ｜ **衔接模式**：{mode} ｜ **Seed**：`{s['seed']}`",
            f"- **画面概要**：{s.get('summary_zh', '—')}",
            f"- **中文台词**：{s.get('dialogue_zh', '—')}",
            f"- **尾帧锚点**：{s.get('end_frame_anchor_zh', '—')}",
            "",
            "```text",
            s["prompt"].strip(),
            "```",
            "",
        ])

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="校验 MiniMax-H3 短剧 episodes.json 并可选同步 03_分镜脚本.md")
    parser.add_argument("json_path", type=Path, help="episodes.json 文件路径")
    parser.add_argument("--sync-md", action="store_true", help="将校验后的分镜同步覆写到同目录的 03_分镜脚本.md")
    args = parser.parse_args()

    if not args.json_path.exists():
        print(f"❌ 找不到文件: {args.json_path}", file=sys.stderr)
        sys.exit(1)

    with args.json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    errors, warnings, rows = validate_project(data)

    print(f"\n🎬 项目: 《{data.get('project_name', '未命名')}》 ({args.json_path})")
    print("-" * 88)
    print(f"{'ID':<10} {'场景':<6} {'模式':<12} {'时长':<6} {'字数':<5} {'Seed':<6} {'角色':<10} {'标题'}")
    print("-" * 88)
    total_dur = 0.0
    for r in rows:
        total_dur += r["dur"]
        print(f"{r['id']:<10} {r['scene']:<6} {r['mode']:<12} {r['dur']:<5.2f}s {r['cjk']:<5} {str(r['seed']):<6} {r['speakers']:<10} {r['title']}")
    print("-" * 88)
    print(f"总镜头数: {len(rows)} 镜 | 预计总时长: ~{total_dur:.1f}s | A100 预计渲染耗时: ~{len(rows)*3.5:.0f}~{len(rows)*4.5:.0f} 分钟\n")

    if warnings:
        print(f"⚠️  警告 ({len(warnings)} 条):")
        for w in warnings:
            print(f"  - {w}")
        print()

    if errors:
        print(f"❌ 校验失败 ({len(errors)} 条错误，请修复后再提交 Colab):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print("✅ 质检全部通过！可直接上传至 Colab 运行。")

    if args.sync_md:
        md_path = args.json_path.parent / "03_分镜脚本.md"
        md_path.write_text(render_storyboard_md(data), encoding="utf-8")
        print(f"📝 已同步更新分镜文档: {md_path}")


if __name__ == "__main__":
    main()
