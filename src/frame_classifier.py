"""
Frame Classification Module for Deepfake Video Detection

This module provides reusable components for:
1. Frame extraction and preprocessing
2. Per-frame inference with ensemble models
3. Video-level decision logic based on frame counts
4. Detailed result reporting with per-model summaries

Usage Example:
    from frame_classifier import FrameClassifier
    
    classifier = FrameClassifier(
        models=loaded_models,
        device=device,
        real_idx=0,
        fake_idx=1,
        threshold=0.30,
        use_face_crop=False
    )
    
    result = classifier.analyze_video("path/to/video.mp4")
    print(f"Prediction: {result['prediction']}")
    print(f"Confidence: {result['confidence']:.2%}")
"""

import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
import torch
import cv2
from PIL import Image
from torchvision import transforms

logger = logging.getLogger(__name__)


@dataclass
class FramePrediction:
    """Result of classifying a single frame."""
    frame_number: int
    video_frame_number: int
    ensemble_label: str
    ensemble_real_prob: float
    ensemble_fake_prob: float
    per_model_labels: Dict[str, str] = field(default_factory=dict)
    per_model_probs: Dict[str, Dict[str, float]] = field(default_factory=dict)
    face_detected: bool = False


@dataclass
class ModelSummary:
    """Summary statistics for a single model."""
    model_name: str
    prediction: str  # "REAL" or "FAKE"
    real_count: int
    fake_count: int
    total_frames: int
    average_real_prob: float
    average_fake_prob: float
    
    @property
    def real_percentage(self) -> float:
        """Percentage of frames classified as REAL."""
        return (self.real_count / self.total_frames * 100) if self.total_frames > 0 else 0.0
    
    @property
    def fake_percentage(self) -> float:
        """Percentage of frames classified as FAKE."""
        return (self.fake_count / self.total_frames * 100) if self.total_frames > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "model_name": self.model_name,
            "prediction": self.prediction,
            "frame_counts": {"REAL": self.real_count, "FAKE": self.fake_count},
            "percentages": {"REAL": self.real_percentage, "FAKE": self.fake_percentage},
            "average_probabilities": {"REAL": self.average_real_prob, "FAKE": self.average_fake_prob},
            "reason": (
                f"REAL frames: {self.real_count}/{self.total_frames} ({self.real_percentage:.1f}%), "
                f"FAKE frames: {self.fake_count}/{self.total_frames} ({self.fake_percentage:.1f}%)."
            ),
        }


@dataclass
class VideoAnalysisResult:
    """Complete result of analyzing a video."""
    prediction: str  # "REAL" or "FAKE"
    frames_analyzed: int
    total_frames_in_video: int
    ensemble_real_count: int
    ensemble_fake_count: int
    ensemble_average_real_prob: float
    ensemble_average_fake_prob: float
    faces_detected: int
    threshold: float
    per_model_summaries: Dict[str, ModelSummary] = field(default_factory=dict)
    frame_predictions: List[FramePrediction] = field(default_factory=list)
    error: Optional[str] = None
    
    @property
    def real_percentage(self) -> float:
        """Percentage of ensemble frames classified as REAL."""
        total = self.frames_analyzed
        return (self.ensemble_real_count / total * 100) if total > 0 else 0.0
    
    @property
    def fake_percentage(self) -> float:
        """Percentage of ensemble frames classified as FAKE."""
        total = self.frames_analyzed
        return (self.ensemble_fake_count / total * 100) if total > 0 else 0.0
    
    @property
    def confidence(self) -> float:
        """
        Confidence score for the prediction (0.0 to 1.0).
        For REAL/FAKE: distance from 50% decision boundary.
        For UNCERTAIN: 0.0 (no confidence when tied).
        """
        if self.prediction == "UNCERTAIN":
            return 0.0  # No confidence for tied predictions
        elif self.prediction == "REAL":
            return abs(0.5 - (self.fake_percentage / 100.0))
        else:  # FAKE
            return abs(0.5 - (self.real_percentage / 100.0))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "prediction": self.prediction,
            "confidence": self.confidence,
            "frames_analyzed": self.frames_analyzed,
            "total_frames_in_video": self.total_frames_in_video,
            "frame_counts": {
                "REAL": self.ensemble_real_count,
                "FAKE": self.ensemble_fake_count,
            },
            "percentages": {
                "REAL": self.real_percentage,
                "FAKE": self.fake_percentage,
            },
            "average_probabilities": {
                "REAL": self.ensemble_average_real_prob,
                "FAKE": self.ensemble_average_fake_prob,
            },
            "faces_detected": self.faces_detected,
            "threshold": self.threshold,
            "decision_reason": self.get_decision_reason(),
            "per_model_summaries": {
                name: summary.to_dict()
                for name, summary in self.per_model_summaries.items()
            },
            "error": self.error,
        }
    
    def get_decision_reason(self) -> str:
        """Generate human-readable decision explanation."""
        return (
            f"REAL frames: {self.ensemble_real_count}/{self.frames_analyzed} ({self.real_percentage:.1f}%), "
            f"FAKE frames: {self.ensemble_fake_count}/{self.frames_analyzed} ({self.fake_percentage:.1f}%). "
            f"Decision rule: If FAKE% ({self.fake_percentage:.1f}%) > Threshold ({self.threshold*100:.1f}%) → FAKE, else REAL. "
            f"Result: {self.prediction}"
        )


class FrameClassifier:
    """
    Classifies video frames and determines video authenticity.
    
    Attributes:
        models: Dictionary of PyTorch models {model_name: model}
        device: PyTorch device (cuda or cpu)
        real_idx: Class index for REAL (typically 0)
        fake_idx: Class index for FAKE (typically 1)
        threshold: FAKE percentage threshold for video classification (default 0.30)
        use_face_crop: Whether to crop faces before inference
        face_cascade: OpenCV Haar cascade for face detection
        transform: Image preprocessing pipeline
    """
    
    def __init__(
        self,
        models: Dict,
        device: torch.device,
        real_idx: int = 0,
        fake_idx: int = 1,
        threshold: float = 0.30,
        use_face_crop: bool = False,
        use_imagenet_norm: bool = False,
    ):
        """
        Initialize the frame classifier.
        
        Args:
            models: Dict of {model_name: model_instance}
            device: torch.device to run inference on
            real_idx: Index of REAL class in model output
            fake_idx: Index of FAKE class in model output
            threshold: FAKE % threshold for marking video as FAKE
            use_face_crop: Enable face detection and cropping
            use_imagenet_norm: Apply ImageNet normalization
        """
        self.models = models
        self.device = device
        self.real_idx = real_idx
        self.fake_idx = fake_idx
        self.threshold = threshold
        self.use_face_crop = use_face_crop
        
        # Setup face detector if enabled
        self.face_cascade = None
        if use_face_crop:
            try:
                cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
                self.face_cascade = cv2.CascadeClassifier(cascade_path)
                if self.face_cascade.empty():
                    logger.warning("Failed to load Haar cascade; disabling face crop")
                    self.use_face_crop = False
                else:
                    logger.info("Face detection enabled")
            except Exception as e:
                logger.warning("Face detection init failed: %s", e)
                self.use_face_crop = False
        
        # Setup image preprocessing
        if use_imagenet_norm:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            logger.info("Using ImageNet normalization")
        else:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
            ])
    
    def crop_face(self, frame: cv2.Mat) -> Optional[cv2.Mat]:
        """
        Extract largest detected face from frame with margin.
        
        Args:
            frame: OpenCV frame (BGR format)
        
        Returns:
            Face crop region or None if no face detected
        """
        if not self.use_face_crop or self.face_cascade is None:
            return None
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60)
            )
            
            if len(faces) == 0:
                return None
            
            # Select largest face
            x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
            
            # Add 15% margin
            pad = int(0.15 * max(w, h))
            x0 = max(0, x - pad)
            y0 = max(0, y - pad)
            x1 = min(frame.shape[1], x + w + pad)
            y1 = min(frame.shape[0], y + h + pad)
            
            return frame[y0:y1, x0:x1]
        except Exception as e:
            logger.warning("Face crop failed: %s", e)
            return None
    
    def preprocess_frame(self, frame: cv2.Mat) -> torch.Tensor:
        """
        Convert and preprocess frame to model input tensor.
        
        Args:
            frame: OpenCV frame (BGR format)
        
        Returns:
            PyTorch tensor of shape [1, 3, 224, 224]
        """
        # Crop face if enabled
        roi = self.crop_face(frame)
        if roi is not None and roi.size > 0:
            frame = roi
        
        # Convert BGR to RGB and to PIL Image
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        # Apply preprocessing transforms
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        return tensor
    
    def classify_frame(
        self,
        frame: cv2.Mat,
        frame_number: int,
        video_frame_number: int,
    ) -> Tuple[FramePrediction, bool]:
        """
        Classify a single frame using ensemble of models.
        
        Args:
            frame: OpenCV frame to classify
            frame_number: Processed frame index
            video_frame_number: Original video frame index
        
        Returns:
            Tuple of (FramePrediction, face_detected_bool)
        """
        face_detected = False
        if self.use_face_crop and self.face_cascade is not None:
            face_detected = self.crop_face(frame) is not None
        
        # Preprocess frame
        tensor = self.preprocess_frame(frame)
        
        per_frame_probs = []
        per_model_labels = {}
        per_model_probs_dict = {}
        
        # Run inference on each model
        with torch.no_grad():
            for model_name, model in self.models.items():
                outputs = model(tensor)
                probs = torch.softmax(outputs, dim=1)[0].detach().cpu()
                
                per_frame_probs.append(probs)
                
                pred_idx = int(torch.argmax(probs).item())
                label = "REAL" if pred_idx == self.real_idx else "FAKE"
                per_model_labels[model_name] = label
                per_model_probs_dict[model_name] = {
                    "REAL": float(probs[self.real_idx]),
                    "FAKE": float(probs[self.fake_idx]),
                }
        
        # Ensemble as mean of probabilities
        ensemble_probs = torch.stack(per_frame_probs, dim=0).mean(dim=0)
        ensemble_idx = int(torch.argmax(ensemble_probs).item())
        ensemble_label = "REAL" if ensemble_idx == self.real_idx else "FAKE"
        
        prediction = FramePrediction(
            frame_number=frame_number,
            video_frame_number=video_frame_number,
            ensemble_label=ensemble_label,
            ensemble_real_prob=float(ensemble_probs[self.real_idx]),
            ensemble_fake_prob=float(ensemble_probs[self.fake_idx]),
            per_model_labels=per_model_labels,
            per_model_probs=per_model_probs_dict,
            face_detected=face_detected,
        )
        
        return prediction, face_detected
    
    def decide_video_label(
        self,
        real_count: int,
        fake_count: int,
        total_frames: int,
    ) -> str:
        """
        Determine if video is REAL or FAKE based on frame counts using 30% threshold rule.
        
        Decision Rule (30% Threshold):
            Fake% = (F / T) × 100
            
            If Fake% > 30% → FAKE ✗
            If Fake% ≤ 30% → REAL ✓
        
        Args:
            real_count: Number of frames classified as REAL (R)
            fake_count: Number of frames classified as FAKE (F)
            total_frames: Total frames analyzed (T)
        
        Returns:
            "REAL" or "FAKE"
        """
        if total_frames == 0:
            return "REAL"  # Default to REAL if no frames processed
        
        real_percentage = (real_count / total_frames) * 100
        fake_percentage = (fake_count / total_frames) * 100
        threshold_percentage = self.threshold * 100  # Convert to percentage
        
        logger.info(
            "Decision: Real=%d (%.1f%%), Fake=%d (%.1f%%), Threshold=%.1f%%",
            real_count,
            real_percentage,
            fake_count,
            fake_percentage,
            threshold_percentage,
        )
        
        # 30% threshold rule: if fake% > 30% -> FAKE, else REAL
        if fake_percentage > threshold_percentage:
            logger.info("Result: FAKE (%.1f%% > %.1f%% threshold)", fake_percentage, threshold_percentage)
            return "FAKE"
        else:
            logger.info("Result: REAL (%.1f%% ≤ %.1f%% threshold)", fake_percentage, threshold_percentage)
            return "REAL"
    
    def analyze_video(self, video_path: str) -> VideoAnalysisResult:
        """
        Analyze all frames in a video and determine authenticity.
        
        Args:
            video_path: Path to video file
        
        Returns:
            VideoAnalysisResult with detailed frame and model summaries
        """
        logger.info("Analyzing video: %s", video_path)
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            error_msg = f"Cannot open video: {video_path}"
            logger.error(error_msg)
            return VideoAnalysisResult(
                prediction="ERROR",
                frames_analyzed=0,
                total_frames_in_video=0,
                ensemble_real_count=0,
                ensemble_fake_count=0,
                ensemble_average_real_prob=0.0,
                ensemble_average_fake_prob=0.0,
                faces_detected=0,
                threshold=self.threshold,
                error=error_msg,
            )
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        logger.info("Video: total_frames=%d, fps=%.2f", total_frames, fps if fps else 0)
        
        # Calculate sampling rate to get ~100 frames
        frame_sample_rate = max(1, total_frames // 100)
        logger.info("Sampling every %d frame(s) to analyze ~100 frames", frame_sample_rate)
        
        # Accumulators
        processed = 0
        frame_count = 0
        faces_detected = 0
        
        # Per-model accumulators
        model_sum_probs = {name: torch.zeros(2, dtype=torch.float32) for name in self.models.keys()}
        model_real = {name: 0 for name in self.models.keys()}
        model_fake = {name: 0 for name in self.models.keys()}
        
        # Ensemble accumulators
        ensemble_sum_probs = torch.zeros(2, dtype=torch.float32)
        ensemble_real = 0
        ensemble_fake = 0
        frame_predictions = []
        
        # Sample logging every ~10% of processed frames
        sample_every = max(1, 30 // 10)
        
        # Process frames
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Apply sampling
            if frame_count % frame_sample_rate != 0:
                frame_count += 1
                continue
            
            # Classify frame
            prediction, face_detected = self.classify_frame(frame, processed, frame_count)
            frame_predictions.append(prediction)
            
            if face_detected:
                faces_detected += 1
            
            # Update ensemble accumulators
            if prediction.ensemble_label == "REAL":
                ensemble_real += 1
            else:
                ensemble_fake += 1
            
            ensemble_probs = torch.tensor([
                prediction.ensemble_real_prob,
                prediction.ensemble_fake_prob,
            ])
            ensemble_sum_probs += ensemble_probs
            
            # Update per-model accumulators
            for model_name in self.models.keys():
                model_label = prediction.per_model_labels[model_name]
                if model_label == "REAL":
                    model_real[model_name] += 1
                else:
                    model_fake[model_name] += 1
                
                model_probs = torch.tensor([
                    prediction.per_model_probs[model_name]["REAL"],
                    prediction.per_model_probs[model_name]["FAKE"],
                ])
                model_sum_probs[model_name] += model_probs
            
            # Sample debug logging
            if processed % sample_every == 0:
                logger.info(
                    "Frame %d (video %d): %s | Ensemble REAL=%.4f FAKE=%.4f | Face=%s",
                    processed,
                    frame_count,
                    prediction.ensemble_label,
                    prediction.ensemble_real_prob,
                    prediction.ensemble_fake_prob,
                    "yes" if face_detected else "no",
                )
            
            processed += 1
            frame_count += 1
        
        cap.release()
        
        if processed == 0:
            error_msg = "Could not extract frames from video"
            logger.error(error_msg)
            return VideoAnalysisResult(
                prediction="ERROR",
                frames_analyzed=0,
                total_frames_in_video=total_frames,
                ensemble_real_count=0,
                ensemble_fake_count=0,
                ensemble_average_real_prob=0.0,
                ensemble_average_fake_prob=0.0,
                faces_detected=0,
                threshold=self.threshold,
                error=error_msg,
            )
        
        # Compute averages
        ensemble_avg_probs = ensemble_sum_probs / processed
        
        # Generate per-model summaries
        per_model_summaries = {}
        for name in self.models.keys():
            avg_probs = model_sum_probs[name] / processed
            real_c = model_real[name]
            fake_c = model_fake[name]
            label = self.decide_video_label(real_c, fake_c, processed)
            
            per_model_summaries[name] = ModelSummary(
                model_name=name,
                prediction=label,
                real_count=real_c,
                fake_count=fake_c,
                total_frames=processed,
                average_real_prob=float(avg_probs[self.real_idx]),
                average_fake_prob=float(avg_probs[self.fake_idx]),
            )
        
        # Final ensemble decision
        final_label = self.decide_video_label(ensemble_real, ensemble_fake, processed)
        
        real_percentage = (ensemble_real / processed * 100) if processed > 0 else 0
        fake_percentage = (ensemble_fake / processed * 100) if processed > 0 else 0
        
        # Log results
        logger.info("=" * 80)
        logger.info("FINAL RESULT")
        logger.info("=" * 80)
        logger.info("Prediction: %s", final_label)
        logger.info("REAL frames: %d (%.1f%%)", ensemble_real, real_percentage)
        logger.info("FAKE frames: %d (%.1f%%)", ensemble_fake, fake_percentage)
        logger.info("Total frames analyzed: %d / %d", processed, total_frames)
        logger.info("Decision rule: Real%% (%.1f%%) vs Fake%% (%.1f%%) → %s",
                    real_percentage, fake_percentage, final_label)
        logger.info("Average probs: REAL=%.4f, FAKE=%.4f",
                    float(ensemble_avg_probs[self.real_idx]),
                    float(ensemble_avg_probs[self.fake_idx]))
        logger.info("=" * 80)
        
        # Create result
        result = VideoAnalysisResult(
            prediction=final_label,
            frames_analyzed=processed,
            total_frames_in_video=total_frames,
            ensemble_real_count=ensemble_real,
            ensemble_fake_count=ensemble_fake,
            ensemble_average_real_prob=float(ensemble_avg_probs[self.real_idx]),
            ensemble_average_fake_prob=float(ensemble_avg_probs[self.fake_idx]),
            faces_detected=faces_detected,
            threshold=self.threshold,
            per_model_summaries=per_model_summaries,
            frame_predictions=frame_predictions,
        )
        
        return result
