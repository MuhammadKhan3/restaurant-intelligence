"""Auto-label bootstrap: pre-generates YOLO-format person labels from a video
using the currently deployed model, so a human only has to correct mistakes
instead of labeling from scratch.

Not part of the running service -- a one-off data-prep tool for fine-tuning.
Output layout matches what Ultralytics training expects:

    <output>/images/<split>/<video-stem>_<frame>.jpg
    <output>/labels/<split>/<video-stem>_<frame>.txt   (class x_center y_center width height, normalized)
    <output>/data.yaml

Usage:
    uv run python scripts/auto_label.py "data/sample video.mp4" --every 15 --max-frames 40
"""

import argparse
from pathlib import Path

import cv2
import yaml

from app.detection.model_loader import YOLOModelLoader
from app.detection.person_detector import PersonDetector

PERSON_CLASS_INDEX = 0  # single-class dataset: just "person"


def sample_frames(video_path: str, every: int, max_frames: int) -> list[tuple[int, "cv2.typing.MatLike"]]:
    cap = cv2.VideoCapture(video_path)
    frames = []
    index = 0
    while len(frames) < max_frames:
        success, frame = cap.read()
        if not success:
            break
        if index % every == 0:
            frames.append((index, frame))
        index += 1
    cap.release()
    return frames


def to_yolo_label(bbox: tuple[int, int, int, int], width: int, height: int) -> str:
    x1, y1, x2, y2 = bbox
    x_center = ((x1 + x2) / 2) / width
    y_center = ((y1 + y2) / 2) / height
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f"{PERSON_CLASS_INDEX} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video_path")
    parser.add_argument("--every", type=int, default=15, help="Sample every Nth frame")
    parser.add_argument("--max-frames", type=int, default=40)
    parser.add_argument("--confidence-threshold", type=float, default=0.4)
    parser.add_argument("--yolo-model", default="yolov8n.pt")
    parser.add_argument("--output", default="data/auto_labeled")
    parser.add_argument("--split", default="train", choices=["train", "val"])
    args = parser.parse_args()

    output = Path(args.output)
    images_dir = output / "images" / args.split
    labels_dir = output / "labels" / args.split
    images_dir.mkdir(parents=True, exist_ok=True)
    labels_dir.mkdir(parents=True, exist_ok=True)

    loader = YOLOModelLoader(args.yolo_model)
    detector = PersonDetector(loader, confidence_threshold=args.confidence_threshold)

    video_stem = Path(args.video_path).stem.replace(" ", "_")
    frames = sample_frames(args.video_path, args.every, args.max_frames)

    total_boxes = 0
    for frame_index, frame in frames:
        detections = detector.detect(frame)
        height, width = frame.shape[:2]

        stem = f"{video_stem}_{frame_index:06d}"
        cv2.imwrite(str(images_dir / f"{stem}.jpg"), frame)

        lines = [to_yolo_label(d.bbox, width, height) for d in detections]
        (labels_dir / f"{stem}.txt").write_text("\n".join(lines), encoding="utf-8")
        total_boxes += len(lines)

        print(f"frame {frame_index}: {len(detections)} box(es) -> {stem}")

    data_yaml = output / "data.yaml"
    if not data_yaml.exists():
        data_yaml.write_text(
            yaml.safe_dump(
                {
                    "path": str(output.resolve()),
                    "train": "images/train",
                    "val": "images/val",
                    "names": {0: "person"},
                }
            ),
            encoding="utf-8",
        )

    print()
    print(f"Wrote {len(frames)} frames, {total_boxes} auto-generated boxes, to {output}/")
    print("These are a STARTING POINT -- review/correct them in a labeling tool before training.")


if __name__ == "__main__":
    main()
