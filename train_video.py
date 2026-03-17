import argparse
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime


def run(cmd):
    print(">>>", " ".join(shlex.quote(c) for c in cmd))
    subprocess.run(cmd, check=True)


def sanitize_name(text: str) -> str:
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip())
    return name.strip("._-") or "video_job"


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Video -> COLMAP -> Gaussian Splatting trainer")
    parser.add_argument(
        "--video",
        default="data/video_jobs/input.mp4",
        help="Path to input video file.",
    )
    parser.add_argument(
        "--name",
        default="",
        help="Job name. Defaults to video filename stem.",
    )
    parser.add_argument(
        "--jobs_root",
        default="data/video_jobs",
        help="Root folder for per-video scene jobs.",
    )
    parser.add_argument(
        "--output_root",
        default="output",
        help="Root folder for trained model outputs.",
    )
    parser.add_argument("--fps", type=float, default=2.0, help="Frame sampling FPS.")
    parser.add_argument("--iterations", type=int, default=3000, help="Train iterations for quick run.")
    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.abspath(os.path.join(root, args.video))
    if not os.path.isfile(video_path):
        print(f"Video not found: {video_path}")
        sys.exit(1)

    default_name = os.path.splitext(os.path.basename(video_path))[0]
    job_name = sanitize_name(args.name if args.name else default_name)
    jobs_root = os.path.abspath(os.path.join(root, args.jobs_root))
    output_root = os.path.abspath(os.path.join(root, args.output_root))

    job_dir = os.path.join(jobs_root, job_name)
    scene_path = os.path.join(job_dir, "scene")
    input_path = os.path.join(scene_path, "input")
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(input_path, exist_ok=True)

    for fname in os.listdir(input_path):
        if fname.lower().endswith((".jpg", ".jpeg", ".png")):
            os.remove(os.path.join(input_path, fname))

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            "-qscale:v",
            "1",
            "-qmin",
            "1",
            "-vf",
            f"fps={args.fps}",
            os.path.join(input_path, "%04d.jpg"),
        ]
    )

    run(
        [
            sys.executable,
            os.path.join(root, "convert.py"),
            "-s",
            scene_path,
            "--colmap_executable",
            "colmap",
            "--no_gpu",
        ]
    )

    run(
        [
            sys.executable,
            os.path.join(root, "train.py"),
            "-s",
            scene_path,
            "-m",
            os.path.join(
                output_root,
                f"{job_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_it{args.iterations}",
            ),
            "--iterations",
            str(args.iterations),
        ]
    )

    print("\nDone.")
    print(f"Video: {video_path}")
    print(f"Job:   {job_name}")
    print(f"Scene: {scene_path}")
