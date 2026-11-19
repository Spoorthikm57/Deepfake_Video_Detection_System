import unittest
from io import BytesIO

from src import app as app_module


class DatasetPathLogicTests(unittest.TestCase):
    def test_detect_dataset_path_label_real(self):
        result = app_module.detect_dataset_path_label("DFDC_Dataset/Real/video001.mp4")
        self.assertEqual(result[0], "REAL")
        self.assertEqual(result[1], "Dataset Path")

    def test_detect_dataset_path_label_fake(self):
        result = app_module.detect_dataset_path_label("DFDC_Dataset/Fake/video002.mp4")
        self.assertEqual(result[0], "FAKE")
        self.assertEqual(result[1], "Dataset Path")

    def test_detect_dataset_path_label_unknown(self):
        result = app_module.detect_dataset_path_label("OtherFolder/sample.mp4")
        self.assertIsNone(result[0])
        self.assertEqual(result[1], "AI Model")

    def test_detect_dataset_path_label_ambiguous(self):
        result = app_module.detect_dataset_path_label("DFDC_Dataset/Real/Fake/video.mp4")
        self.assertIsNone(result[0])
        self.assertEqual(result[1], "AI Model")

    def test_detect_dataset_path_label_case_insensitive(self):
        result = app_module.detect_dataset_path_label("DFDC_Dataset/rEaL/video001.mp4")
        self.assertEqual(result, ("REAL", "Dataset Path"))

    def test_detect_dataset_path_label_does_not_match_directory_substrings(self):
        result = app_module.detect_dataset_path_label("OtherFolder/RealVideos/video.mp4")
        self.assertEqual(result, (None, "AI Model"))

    def test_detect_dataset_path_label_does_not_match_filename(self):
        result = app_module.detect_dataset_path_label("OtherFolder/fake_video.mp4")
        self.assertEqual(result, (None, "AI Model"))

    def test_predict_multi_classifies_using_uploaded_relative_path(self):
        response = app_module.app.test_client().post(
            "/predict-multi",
            data={
                "files": (BytesIO(b"video"), "video001.mp4"),
                "relative_paths": "DFDC_Dataset/Real/video001.mp4",
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        result = response.get_json()["results"][0]
        self.assertEqual(result["filename"], "video001.mp4")
        self.assertEqual(result["prediction"], "REAL")
        self.assertEqual(result["classification_source"], "Dataset Path")
        self.assertNotIn("confidence", result)


if __name__ == "__main__":
    unittest.main()
