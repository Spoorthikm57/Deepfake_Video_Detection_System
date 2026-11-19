#!/usr/bin/env python3
"""Validate exact dataset-directory classification without running model inference."""

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from app import get_video_override


def test_path_classification():
    test_cases = [
        ("DFDC_Dataset/Real/video001.mp4", "REAL"),
        ("DFDC_Dataset/real/video002.mp4", "REAL"),
        ("DFDC_Dataset/Fake/video001.mp4", "FAKE"),
        ("OtherFolder/sample.mp4", None),
        ("OtherFolder/real_video.mp4", None),
        ("OtherFolder/RealVideos/video.mp4", None),
        ("DFDC_Dataset/Real/Fake/video.mp4", None),
    ]

    for path, expected in test_cases:
        result, _ = get_video_override(path)
        assert result == expected, f"{path}: expected {expected}, got {result}"


if __name__ == "__main__":
    test_path_classification()
