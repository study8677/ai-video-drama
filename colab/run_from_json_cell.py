# ==============================================================================
# Colab Cell 6 升级版：读取 episodes.json 全自动批量生成 MiniMax-H3 连贯短剧
#
# 使用方法：
#   1. 先正常执行你 Colab 的 Cell 1~3（环境检测、编译 sd-cli、下载量化权重）
#   2. 将本地生成的 episodes.json 上传到 Colab（例如 /content/episodes.json）
#   3. 将本文件代码完整粘贴到 Colab Cell 6，修改下方 JSON_PATH 后运行即可
#
# 新增特性：
#   - 断点续跑（SKIP_EXISTING=True 时已生成的镜头自动跳过）
#   - 单镜头改 seed 定向重绘（设置 ONLY_IDS = ["ep01_s03"] 即可只重跑该镜）
#   - 智能跨场拼接（仅对 use_prev_last_frame=True 衔接镜裁掉首帧 0.042s，切场镜不裁）
#   - 自动按分集导出单集 MP4 + 全剧完整 MP4 + 首尾帧连贯性故事板
# ==============================================================================

import json
import os
import subprocess
import time
from collections import defaultdict
from pathlib import Path
from PIL import Image
from IPython.display import display, Image as IPImage, Video, HTML

# ===== 用户配置区 =====
JSON_PATH = Path("/content/episodes.json")     # 上传的剧本 JSON 路径
SD_CLI = "/content/stable-diffusion.cpp/build/bin/sd-cli"
MODELS = "/content/models/minimax_h3"
SKIP_EXISTING = True                           # True=已生成镜头自动跳过（断点续跑）
ONLY_IDS = []                                  # 留空=跑全部；填 ["ep01_s03"] 可强制只重绘指定镜头
# ======================

assert JSON_PATH.exists(), f"请先上传 episodes.json 到 {JSON_PATH}"
project = json.loads(JSON_PATH.read_text(encoding="utf-8"))

PROJECT_NAME = project["project_name"]
PROJECT_SLUG = project["project_slug"]
VCFG = project.get("video_config", {})
SHOTS = project["shots"]

OUT_DIR = Path(f"/content/outputs/{PROJECT_SLUG}")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_first_last_frames(mp4_path: Path, first_png: Path, last_png: Path):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4_path),
        "-vf", "select=eq(n\\,0)", "-vframes", "1", str(first_png)
    ], check=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-sseof", "-0.08", "-i", str(mp4_path),
        "-update", "1", "-frames:v", "1", str(last_png)
    ], check=True)
    assert last_png.exists(), f"Failed to extract last frame for {mp4_path}"


def run_shot(shot: dict, prev_last_frame: Path | None):
    sid = shot["id"]
    avi_path = OUT_DIR / f"{sid}.avi"
    mp4_path = OUT_DIR / f"{sid}.mp4"
    first_png = OUT_DIR / f"{sid}_first.png"
    last_png = OUT_DIR / f"{sid}_last.png"

    force_regen = sid in ONLY_IDS
    if ONLY_IDS and not force_regen:
        assert mp4_path.exists(), f"ONLY_IDS 模式下缺少已有镜头 {mp4_path}，请先跑完全量或补齐前置镜头"
        if not first_png.exists() or not last_png.exists():
            extract_first_last_frames(mp4_path, first_png, last_png)
        print(f"[{sid}] 复用已有镜头: {mp4_path}", flush=True)
        return mp4_path, first_png, last_png, 0.0

    if SKIP_EXISTING and not force_regen and mp4_path.exists() and mp4_path.stat().st_size > 10_000:
        if not first_png.exists() or not last_png.exists():
            extract_first_last_frames(mp4_path, first_png, last_png)
        print(f"[{sid}] 断点跳过（已存在）: {mp4_path}", flush=True)
        return mp4_path, first_png, last_png, 0.0

    width = str(shot.get("width", VCFG.get("width", 864)))
    height = str(shot.get("height", VCFG.get("height", 480)))
    fps = str(shot.get("fps", VCFG.get("fps", 24)))
    frames = str(shot.get("video_frames", VCFG.get("video_frames", 124)))
    steps = str(shot.get("steps", VCFG.get("steps", 20)))
    cfg_scale = str(shot.get("cfg_scale", VCFG.get("cfg_scale", 1.0)))
    sampler = str(shot.get("sampling_method", VCFG.get("sampling_method", "euler")))

    cmd = [
        SD_CLI,
        "-M", "vid_gen",
        "--diffusion-model", f"{MODELS}/minimax_h3_fl2va_pruned-Q4_K.gguf",
        "--llm", f"{MODELS}/qwen3vl_32b_minimax_h3-Q4_K_M.gguf",
        "--vae", f"{MODELS}/vae/minimax_h3_video_vae_fp16.safetensors",
        "--audio-vae", f"{MODELS}/vae/minimax_h3_audio_vae_fp32.safetensors",
        "-p", shot["prompt"],
        "--cfg-scale", cfg_scale,
        "-W", width,
        "-H", height,
        "--fps", fps,
        "--video-frames", frames,
        "--steps", steps,
        "--sampling-method", sampler,
        "--rng", "cpu",
        "--seed", str(shot["seed"]),
        "--flash-attn", "off,diffusion=on",
        "--offload-to-cpu",
        "-o", str(avi_path),
        "-v",
    ]

    ref_img = None
    if shot.get("use_prev_last_frame") and prev_last_frame is not None:
        ref_img = prev_last_frame
    elif shot.get("init_image"):
        ref_img = Path(shot["init_image"])
        assert ref_img.exists(), f"[{sid}] 指定的 init_image 不存在: {ref_img}"

    if ref_img is not None:
        cmd.extend(["-i", str(ref_img)])

    mode_str = f"I2VA({ref_img.name})" if ref_img else "T2VA(新场景)"
    print(f"\n{'='*64}\n>>> 生成 {shot['title']} ({sid}) | {mode_str} | seed={shot['seed']}\n{'='*64}", flush=True)

    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    for line in proc.stdout:
        if any(k in line for k in ["sampling", "completed", "error", "Error", "ERROR", "save result", "1/20", "10/20", "20/20", "condition graph"]):
            print(f"[{sid}] {line}", end="", flush=True)
    ret = proc.wait()
    elapsed = time.time() - t0
    print(f"[{sid}] sd-cli exit={ret} in {elapsed:.1f}s", flush=True)
    assert ret == 0 and avi_path.exists(), f"{sid} 生成失败!"

    # 转码为 H.264 + 32kHz 立体声 AAC MP4
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(avi_path),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-ar", "32000", "-ac", "2", "-b:a", "192k",
        str(mp4_path)
    ], check=True)

    extract_first_last_frames(mp4_path, first_png, last_png)
    return mp4_path, first_png, last_png, elapsed


def concat_shots(shot_records: list[dict], output_mp4: Path, fps: int = 24):
    """智能拼接：仅对 I2VA 尾帧衔接镜头裁去 1 帧(1/fps 秒)消除衔接定格，切场镜保留完整首帧"""
    trim_sec = round(1.0 / fps, 3)  # 24fps -> 0.042s
    inputs = []
    filters = []
    concat_inputs = []

    for i, rec in enumerate(shot_records):
        inputs.extend(["-i", rec["mp4"]])
        need_trim = (i > 0) and rec.get("use_prev_last_frame", False)
        if need_trim:
            filters.append(f"[{i}:v]trim=start={trim_sec},setpts=PTS-STARTPTS[v{i}];[{i}:a]atrim=start={trim_sec},asetpts=PTS-STARTPTS[a{i}]")
        else:
            filters.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}];[{i}:a]asetpts=PTS-STARTPTS[a{i}]")
        concat_inputs.append(f"[v{i}][a{i}]")

    filter_complex = ";".join(filters) + f";{''.join(concat_inputs)}concat=n={len(shot_records)}:v=1:a=1[v][a]"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-c:a", "aac", "-ar", "32000", "-ac", "2", "-b:a", "192k",
        str(output_mp4)
    ], check=True)


# ===== 主执行循环 =====
t_all = time.time()
prev_last = None
results = []

for shot in SHOTS:
    mp4_p, first_p, last_p, dur_s = run_shot(shot, prev_last)
    prev_last = last_p
    results.append({
        "id": shot["id"],
        "episode": shot.get("episode", 1),
        "title": shot["title"],
        "use_prev_last_frame": bool(shot.get("use_prev_last_frame", False)),
        "mp4": str(mp4_p),
        "first": str(first_p),
        "last": str(last_p),
        "gen_sec": round(dur_s, 1),
    })
    (OUT_DIR / "progress.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

fps_val = int(VCFG.get("fps", 24))

# 若有多集，先分别导出单集 MP4
by_ep = defaultdict(list)
for r in results:
    by_ep[r["episode"]].append(r)

if len(by_ep) > 1:
    for ep_num, ep_recs in sorted(by_ep.items()):
        ep_out = OUT_DIR / f"{PROJECT_SLUG}_ep{ep_num:02d}.mp4"
        concat_shots(ep_recs, ep_out, fps=fps_val)
        print(f"📦 单集导出: {ep_out}", flush=True)

# 拼接全剧完整 MP4
full_mp4 = OUT_DIR / f"{PROJECT_SLUG}_full.mp4"
concat_shots(results, full_mp4, fps=fps_val)

# 制作首尾帧连贯性故事板（每行一镜：左=首帧，右=尾帧）
thumb_w, thumb_h = 432, 240
board = Image.new("RGB", (thumb_w * 2, thumb_h * len(results)), (20, 20, 24))
for row, r in enumerate(results):
    im_f = Image.open(r["first"]).resize((thumb_w, thumb_h))
    im_l = Image.open(r["last"]).resize((thumb_w, thumb_h))
    board.paste(im_f, (0, row * thumb_h))
    board.paste(im_l, (thumb_w, row * thumb_h))
board_path = OUT_DIR / f"{PROJECT_SLUG}_storyboard.png"
board.save(board_path)

info = subprocess.check_output([
    "ffprobe", "-v", "error",
    "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height,sample_rate,channels",
    "-of", "default=noprint_wrappers=1", str(full_mp4)
]).decode()

print(f"\n=== 《{PROJECT_NAME}》全部完成 ({time.time()-t_all:.1f}s) ===\n{info}\n输出文件: {full_mp4}", flush=True)

display(HTML(f"<h3>🎬 《{PROJECT_NAME}》完整连贯短剧（共 {len(results)} 镜 + 原生中文立体声）</h3>"))
display(Video(str(full_mp4), embed=True, width=760))
display(HTML("<h4>📸 逐镜首帧（左）→ 尾帧（右）连贯性故事板</h4>"))
display(IPImage(filename=str(board_path)))
