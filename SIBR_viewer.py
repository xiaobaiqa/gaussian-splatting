from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "output"


def find_latest_output_model(output_dir: Path) -> Path | None:
    if not output_dir.exists():
        return None
    candidates = [p for p in output_dir.iterdir() if p.is_dir()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def find_sibr_executable(root: Path) -> tuple[Path | None, Path | None]:
    candidates = [
        root.parent / "sibr_core_gaussian" / "install" / "bin" / "SIBR_gaussianViewer_app",
        root / "external" / "viewers" / "bin" / "SIBR_gaussianViewer_app.exe",
        root / "external" / "viewers" / "bin" / "SIBR_gaussianViewer_app",
        root / "SIBR_viewers" / "install" / "bin" / "SIBR_gaussianViewer_app",
    ]
    for exe in candidates:
        if exe.exists():
            return exe, exe.parent
    return None, None


def find_render_and_gt(model_path: Path) -> tuple[Path | None, Path | None]:
    ours_dirs = sorted(model_path.glob("*/ours_*"))
    for ours in ours_dirs:
        render_dir = ours / "renders"
        gt_dir = ours / "gt"
        if render_dir.exists() and gt_dir.exists():
            return render_dir, gt_dir
    return None, None


def build_comparison_video(render_dir: Path, gt_dir: Path, out_video: Path) -> bool:
    ffmpeg = "ffmpeg"
    render_glob = str(render_dir / "*.png")
    gt_glob = str(gt_dir / "*.png")
    cmd = [
        ffmpeg,
        "-y",
        "-pattern_type",
        "glob",
        "-i",
        render_glob,
        "-pattern_type",
        "glob",
        "-i",
        gt_glob,
        "-filter_complex",
        "hstack=inputs=2,pad=ceil(iw/2)*2:ceil(ih/2)*2",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(out_video),
    ]
    try:
        subprocess.run(cmd, check=True, cwd=ROOT)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def run() -> int:
    parser = argparse.ArgumentParser(description="View gaussian-splatting result.")
    parser.add_argument(
        "--model_path",
        type=str,
        default="",
        help="Path to output model folder (default: latest folder under ./output).",
    )
    args = parser.parse_args()

    model_path = Path(args.model_path).resolve() if args.model_path else find_latest_output_model(OUTPUT_DIR)
    if model_path is None or not model_path.exists():
        print("No valid model path found. Please pass --model_path.")
        return 1

    exe, run_path = find_sibr_executable(ROOT)
    if exe is not None and run_path is not None:
        print(f"Launching SIBR viewer: {exe}")
        print(f"Model path: {model_path}")
        subprocess.run([str(exe), "-m", str(model_path)], cwd=run_path, check=False)
        return 0

    print("SIBR_gaussianViewer_app not found. Falling back to render-vs-gt preview video.")
    render_dir, gt_dir = find_render_and_gt(model_path)
    if render_dir is None or gt_dir is None:
        print(f"No renders/gt folder found under: {model_path}")
        print("Expected structure: <model>/<scene>/ours_xxx/{renders,gt}")
        return 2

    out_video = model_path / "render_vs_gt_preview.mp4"
    ok = build_comparison_video(render_dir, gt_dir, out_video)
    if ok and out_video.exists():
        print(f"Preview video generated: {out_video}")
        return 0

    print("Failed to build preview video (check ffmpeg).")
    print(f"Renders dir: {render_dir}")
    print(f"GT dir: {gt_dir}")
    return 3


if __name__ == "__main__":
    raise SystemExit(run())
