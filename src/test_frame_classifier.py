"""
Unit tests for the frame_classifier module.

Tests frame classification logic, decision rules, and result calculation.

Usage:
    pytest test_frame_classifier.py -v
    pytest test_frame_classifier.py::test_decide_video_label -v
"""

import os
import sys
import pytest
import torch
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from frame_classifier import (
    FrameClassifier,
    FramePrediction,
    ModelSummary,
    VideoAnalysisResult,
)


# Mock device
DEVICE = torch.device("cpu")


class MockModel(torch.nn.Module):
    """Mock model for testing."""
    def forward(self, x):
        # Return fixed probabilities for testing
        return torch.tensor([[0.7, 0.3]], dtype=torch.float32)


@pytest.fixture
def mock_classifier():
    """Create a mock classifier for testing."""
    mock_models = {
        "model1": MockModel(),
        "model2": MockModel(),
        "model3": MockModel(),
    }
    
    classifier = FrameClassifier(
        models=mock_models,
        device=DEVICE,
        real_idx=0,
        fake_idx=1,
        threshold=0.30,
        use_face_crop=False,
        use_imagenet_norm=False,
    )
    return classifier


class TestFramePrediction:
    """Tests for FramePrediction dataclass."""
    
    def test_frame_prediction_creation(self):
        """Test creating a FramePrediction."""
        pred = FramePrediction(
            frame_number=0,
            video_frame_number=0,
            ensemble_label="REAL",
            ensemble_real_prob=0.8,
            ensemble_fake_prob=0.2,
        )
        
        assert pred.frame_number == 0
        assert pred.ensemble_label == "REAL"
        assert pred.ensemble_real_prob == 0.8
        assert pred.ensemble_fake_prob == 0.2
        assert pred.face_detected is False


class TestModelSummary:
    """Tests for ModelSummary dataclass."""
    
    def test_model_summary_percentages(self):
        """Test percentage calculation in ModelSummary."""
        summary = ModelSummary(
            model_name="test_model",
            prediction="REAL",
            real_count=70,
            fake_count=30,
            total_frames=100,
            average_real_prob=0.75,
            average_fake_prob=0.25,
        )
        
        assert summary.real_percentage == 70.0
        assert summary.fake_percentage == 30.0
    
    def test_model_summary_to_dict(self):
        """Test converting ModelSummary to dictionary."""
        summary = ModelSummary(
            model_name="test_model",
            prediction="FAKE",
            real_count=40,
            fake_count=60,
            total_frames=100,
            average_real_prob=0.4,
            average_fake_prob=0.6,
        )
        
        result_dict = summary.to_dict()
        
        assert result_dict["model_name"] == "test_model"
        assert result_dict["prediction"] == "FAKE"
        assert result_dict["frame_counts"]["REAL"] == 40
        assert result_dict["frame_counts"]["FAKE"] == 60
        assert abs(result_dict["percentages"]["REAL"] - 40.0) < 0.01
        assert abs(result_dict["percentages"]["FAKE"] - 60.0) < 0.01


class TestVideoAnalysisResult:
    """Tests for VideoAnalysisResult dataclass."""
    
    def test_confidence_calculation_real(self):
        """Test confidence calculation for REAL videos."""
        result = VideoAnalysisResult(
            prediction="REAL",
            frames_analyzed=100,
            total_frames_in_video=1000,
            ensemble_real_count=95,
            ensemble_fake_count=5,
            ensemble_average_real_prob=0.95,
            ensemble_average_fake_prob=0.05,
            faces_detected=90,
            threshold=0.30,
        )
        
        # fake% = 5%, so confidence = |0.5 - 0.05| = 0.45
        expected_confidence = abs(0.5 - 0.05)
        assert abs(result.confidence - expected_confidence) < 0.01
    
    def test_confidence_calculation_fake(self):
        """Test confidence calculation for FAKE videos."""
        result = VideoAnalysisResult(
            prediction="FAKE",
            frames_analyzed=100,
            total_frames_in_video=1000,
            ensemble_real_count=20,
            ensemble_fake_count=80,
            ensemble_average_real_prob=0.2,
            ensemble_average_fake_prob=0.8,
            faces_detected=90,
            threshold=0.30,
        )
        
        # fake% = 80%, so confidence = |0.5 - 0.8| = 0.3
        expected_confidence = abs(0.5 - 0.8)
        assert abs(result.confidence - expected_confidence) < 0.01
    
    def test_result_to_dict(self):
        """Test converting VideoAnalysisResult to dictionary."""
        result = VideoAnalysisResult(
            prediction="REAL",
            frames_analyzed=100,
            total_frames_in_video=1000,
            ensemble_real_count=95,
            ensemble_fake_count=5,
            ensemble_average_real_prob=0.95,
            ensemble_average_fake_prob=0.05,
            faces_detected=90,
            threshold=0.30,
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["prediction"] == "REAL"
        assert result_dict["frames_analyzed"] == 100
        assert result_dict["frame_counts"]["REAL"] == 95
        assert result_dict["frame_counts"]["FAKE"] == 5


class TestDecisionLogic:
    """Tests for video-level decision logic (Majority Voting)."""
    
    def test_decide_video_label_clearly_real(self, mock_classifier):
        """Test deciding a clearly REAL video (95% real)."""
        label = mock_classifier.decide_video_label(
            real_count=95,
            fake_count=5,
            total_frames=100,
        )
        assert label == "REAL"
    
    def test_decide_video_label_clearly_fake(self, mock_classifier):
        """Test deciding a clearly FAKE video (90% fake)."""
        label = mock_classifier.decide_video_label(
            real_count=10,
            fake_count=90,
            total_frames=100,
        )
        assert label == "FAKE"
    
    def test_decide_video_label_barely_real(self, mock_classifier):
        """Test deciding a barely REAL video (51% real, 49% fake)."""
        label = mock_classifier.decide_video_label(
            real_count=51,
            fake_count=49,
            total_frames=100,
        )
        assert label == "REAL"
    
    def test_decide_video_label_barely_fake(self, mock_classifier):
        """Test deciding a barely FAKE video (49% real, 51% fake)."""
        label = mock_classifier.decide_video_label(
            real_count=49,
            fake_count=51,
            total_frames=100,
        )
        assert label == "FAKE"
    
    def test_decide_video_label_exactly_50_50(self, mock_classifier):
        """Test 50-50 split (should be UNCERTAIN)."""
        label = mock_classifier.decide_video_label(
            real_count=50,
            fake_count=50,
            total_frames=100,
        )
        assert label == "UNCERTAIN"
    
    def test_decide_video_label_zero_frames(self, mock_classifier):
        """Test with zero frames (edge case)."""
        label = mock_classifier.decide_video_label(
            real_count=0,
            fake_count=0,
            total_frames=0,
        )
        # Should default to UNCERTAIN
        assert label == "UNCERTAIN"
    
    def test_decide_video_label_odd_frames_150(self, mock_classifier):
        """Test with 150 frames (odd number, always has majority)."""
        # 76 real (50.67%), 74 fake (49.33%) → REAL
        label = mock_classifier.decide_video_label(76, 74, 150)
        assert label == "REAL"
        
        # 74 real (49.33%), 76 fake (50.67%) → FAKE
        label = mock_classifier.decide_video_label(74, 76, 150)
        assert label == "FAKE"


class TestDecisionMatrixScenarios:
    """Test various realistic decision matrix scenarios (Majority Voting)."""
    
    def test_scenario_mostly_real(self, mock_classifier):
        """Scenario: Mostly real video with some fake frames."""
        # 80% REAL, 20% FAKE → Should be REAL
        assert mock_classifier.decide_video_label(80, 20, 100) == "REAL"
    
    def test_scenario_mostly_fake(self, mock_classifier):
        """Scenario: Mostly fake video with some real frames."""
        # 10% REAL, 90% FAKE → Should be FAKE
        assert mock_classifier.decide_video_label(10, 90, 100) == "FAKE"
    
    def test_scenario_150_frames_real_majority(self, mock_classifier):
        """Scenario: 150 frames with real majority."""
        # 76 REAL (50.67%), 74 FAKE (49.33%) → Should be REAL
        assert mock_classifier.decide_video_label(76, 74, 150) == "REAL"
    
    def test_scenario_150_frames_fake_majority(self, mock_classifier):
        """Scenario: 150 frames with fake majority."""
        # 74 REAL (49.33%), 76 FAKE (50.67%) → Should be FAKE
        assert mock_classifier.decide_video_label(74, 76, 150) == "FAKE"
    
    def test_scenario_150_frames_tied(self, mock_classifier):
        """Scenario: 150 frames with no majority (impossible, but test logic)."""
        # In practice: can't have exact tie with odd total
        # But test the comparison logic: equal percentages
        assert mock_classifier.decide_video_label(75, 75, 150) == "UNCERTAIN"
    
    def test_scenario_100_frames_barely_real(self, mock_classifier):
        """Scenario: 100 frames, just barely REAL (51% real)."""
        assert mock_classifier.decide_video_label(51, 49, 100) == "REAL"
    
    def test_scenario_100_frames_barely_fake(self, mock_classifier):
        """Scenario: 100 frames, just barely FAKE (51% fake)."""
        assert mock_classifier.decide_video_label(49, 51, 100) == "FAKE"
    
    def test_scenario_100_frames_exact_tie(self, mock_classifier):
        """Scenario: 100 frames with exact tie (50/50)."""
        assert mock_classifier.decide_video_label(50, 50, 100) == "UNCERTAIN"


class TestPercentageCalculations:
    """Test percentage calculations in results."""
    
    def test_real_percentage_calculation(self):
        """Test REAL percentage calculation."""
        result = VideoAnalysisResult(
            prediction="REAL",
            frames_analyzed=100,
            total_frames_in_video=1000,
            ensemble_real_count=75,
            ensemble_fake_count=25,
            ensemble_average_real_prob=0.75,
            ensemble_average_fake_prob=0.25,
            faces_detected=90,
            threshold=0.30,
        )
        
        assert abs(result.real_percentage - 75.0) < 0.01
    
    def test_fake_percentage_calculation(self):
        """Test FAKE percentage calculation."""
        result = VideoAnalysisResult(
            prediction="REAL",
            frames_analyzed=120,
            total_frames_in_video=1000,
            ensemble_real_count=84,
            ensemble_fake_count=36,
            ensemble_average_real_prob=0.7,
            ensemble_average_fake_prob=0.3,
            faces_detected=90,
            threshold=0.30,
        )
        
        expected_fake_percentage = (36 / 120) * 100
        assert abs(result.fake_percentage - expected_fake_percentage) < 0.01


class TestResultGeneration:
    """Test generation of human-readable results and reasons."""
    
    def test_decision_reason_generation(self):
        """Test generating decision reason string."""
        result = VideoAnalysisResult(
            prediction="FAKE",
            frames_analyzed=100,
            total_frames_in_video=3000,
            ensemble_real_count=30,
            ensemble_fake_count=70,
            ensemble_average_real_prob=0.3,
            ensemble_average_fake_prob=0.7,
            faces_detected=98,
            threshold=0.30,
        )
        
        reason = result.get_decision_reason()
        
        assert "30/100" in reason
        assert "70/100" in reason
        assert "FAKE" in reason
        assert "30.0%" in reason
        assert "70.0%" in reason


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
