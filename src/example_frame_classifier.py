"""
Example usage of the FrameClassifier module.

This script demonstrates how to use the frame_classifier module
to analyze videos and get frame-level classifications.

Usage:
    python example_frame_classifier.py --video path/to/video.mp4
    
    python example_frame_classifier.py --video path/to/video.mp4 \
        --enable-face-crop \
        --enable-imagenet-norm \
        --threshold 0.35
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import torch
import torch.nn as nn
from torchvision import models

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from frame_classifier import FrameClassifier

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("example_frame_classifier")


def build_model(model_name: str, num_classes: int = 2, device: torch.device = None) -> nn.Module:
    """Build a pretrained model with 2 output classes."""
    if model_name == "resnet18":
        m = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        m.fc = nn.Linear(m.fc.in_features, num_classes)
    elif model_name == "mobilenetv2":
        m = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, num_classes)
    elif model_name == "efficientnetb0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, num_classes)
    else:
        raise ValueError(f"Unknown model: {model_name}")
    
    if device:
        m = m.to(device)
    m.eval()
    return m


def load_models(device: torch.device):
    """Load or create models."""
    logger.info("Loading models...")
    models_dict = {}
    
    # Try to load from weights, fallback to pretrained
    model_names = ["mobilenetv2", "efficientnetb0", "resnet18"]
    
    for name in model_names:
        try:
            m = build_model(name, device=device)
            models_dict[name] = m
            logger.info("Loaded %s", name)
        except Exception as e:
            logger.warning("Failed to load %s: %s", name, e)
    
    if not models_dict:
        logger.error("Could not load any models")
        sys.exit(1)
    
    return models_dict


def analyze_video_example(video_path: str, args):
    """Analyze a video using the FrameClassifier."""
    
    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)
    
    # Load models
    models_dict = load_models(device)
    
    # Create classifier
    classifier = FrameClassifier(
        models=models_dict,
        device=device,
        real_idx=0,
        fake_idx=1,
        threshold=args.threshold,
        use_face_crop=args.enable_face_crop,
        use_imagenet_norm=args.enable_imagenet_norm,
    )
    
    # Analyze video
    logger.info("Analyzing video: %s", video_path)
    result = classifier.analyze_video(video_path)
    
    return result


def print_result(result):
    """Pretty-print the analysis result."""
    print("\n" + "=" * 80)
    print("DEEPFAKE DETECTION RESULT")
    print("=" * 80)
    
    if result.error:
        print(f"❌ ERROR: {result.error}")
        return
    
    # Main prediction
    icon = "🚨" if result.prediction == "FAKE" else "✅"
    print(f"\n{icon} PREDICTION: {result.prediction}")
    print(f"   Confidence: {result.confidence:.1%}")
    
    # Frame counts
    print(f"\n📊 Frame Analysis:")
    print(f"   REAL frames: {result.ensemble_real_count}/{result.frames_analyzed} ({result.real_percentage:.1f}%)")
    print(f"   FAKE frames: {result.ensemble_fake_count}/{result.frames_analyzed} ({result.fake_percentage:.1f}%)")
    print(f"   Faces detected: {result.faces_detected}")
    
    # Probabilities
    print(f"\n📈 Average Probabilities:")
    print(f"   REAL: {result.ensemble_average_real_prob:.4f}")
    print(f"   FAKE: {result.ensemble_average_fake_prob:.4f}")
    
    # Decision logic
    print(f"\n🔍 Decision Logic:")
    print(f"   Threshold: {result.threshold*100:.1f}%")
    print(f"   Fake%: {result.fake_percentage:.1f}%")
    if result.fake_percentage > result.threshold * 100:
        print(f"   → {result.fake_percentage:.1f}% > {result.threshold*100:.1f}% → FAKE ✗")
    else:
        print(f"   → {result.fake_percentage:.1f}% ≤ {result.threshold*100:.1f}% → REAL ✓")
    
    # Per-model summaries
    print(f"\n🤖 Per-Model Summaries:")
    for model_name, summary in result.per_model_summaries.items():
        print(f"\n   {model_name}:")
        print(f"      Prediction: {summary.prediction}")
        print(f"      REAL: {summary.real_count}/{summary.total_frames} ({summary.real_percentage:.1f}%)")
        print(f"      FAKE: {summary.fake_count}/{summary.total_frames} ({summary.fake_percentage:.1f}%)")
        print(f"      Avg Probs: REAL={summary.average_real_prob:.4f}, FAKE={summary.average_fake_prob:.4f}")
    
    # Video info
    print(f"\n📹 Video Info:")
    print(f"   Frames analyzed: {result.frames_analyzed}")
    print(f"   Total frames: {result.total_frames_in_video}")
    print(f"   Sample rate: 1/{result.total_frames_in_video // result.frames_analyzed if result.frames_analyzed > 0 else 1}")
    
    print("\n" + "=" * 80 + "\n")


def save_result_json(result, output_path: str):
    """Save result as JSON."""
    result_dict = result.to_dict()
    with open(output_path, 'w') as f:
        json.dump(result_dict, f, indent=2)
    logger.info("Result saved to: %s", output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Analyze a video for deepfakes using frame classification"
    )
    parser.add_argument(
        "--video",
        type=str,
        required=True,
        help="Path to video file"
    )
    parser.add_argument(
        "--enable-face-crop",
        action="store_true",
        help="Enable face detection and cropping"
    )
    parser.add_argument(
        "--enable-imagenet-norm",
        action="store_true",
        help="Apply ImageNet normalization"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.30,
        help="FAKE frame percentage threshold (default: 0.30)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Save result as JSON to this file"
    )
    
    args = parser.parse_args()
    
    # Validate video file
    if not os.path.exists(args.video):
        logger.error("Video file not found: %s", args.video)
        sys.exit(1)
    
    # Analyze video
    result = analyze_video_example(args.video, args)
    
    # Print result
    print_result(result)
    
    # Save JSON if requested
    if args.output:
        save_result_json(result, args.output)


if __name__ == "__main__":
    main()
