# 🎭 Deepfake Video Detection System

## 📌 Overview

The **Deepfake Video Detection System** is an AI-powered web application designed to identify manipulated or AI-generated videos by analyzing visual patterns and facial information within video frames.

With the advancement of artificial intelligence, deepfake technology can create highly realistic videos by replacing faces, modifying facial expressions, or generating synthetic visual content. These manipulated videos can be used for misinformation, identity fraud, and other malicious purposes.

This project aims to provide an automated solution for detecting deepfake videos using deep learning and computer vision techniques.
s
The system processes an uploaded video, extracts relevant frames, analyzes facial features, and uses a trained deep learning model to determine whether the video is likely to be **REAL** or **FAKE**.

---

## 🎯 Problem Statement

Deepfake videos are becoming increasingly realistic, making it difficult for humans to distinguish genuine videos from manipulated content.

Traditional manual verification methods are time-consuming and unreliable, especially when dealing with large amounts of video data.

The objective of this project is to develop an automated deepfake detection system that uses deep learning techniques to analyze video frames and identify potential manipulation.

---

## 💡 Proposed Solution

The proposed system combines deep learning and computer vision techniques to detect manipulated videos.

The application allows users to upload a video through a web interface. The uploaded video is processed by the backend, where frames are extracted and analyzed using a deep learning model.

The model examines visual patterns and facial features to identify inconsistencies that may indicate manipulation.

Based on the analysis, the system generates a prediction indicating whether the video is classified as **REAL** or **FAKE**.

---

## 🚀 Key Features

- 📹 Upload video files for deepfake detection
- 🎞️ Extract and process video frames
- 🧠 Deep learning-based video analysis
- 👤 Facial feature and visual pattern analysis
- 🔍 Detection of potential manipulated content
- 📊 Real or Fake classification results
- 🌐 Interactive web-based user interface
- ⚡ Automated video processing and prediction
- 🔗 Frontend and backend integration

---

## 🧠 Model Architecture

The system uses a hybrid deep learning approach for deepfake detection.

The architecture combines the strengths of convolutional neural networks for spatial feature extraction and temporal analysis for understanding patterns across video frames.

### 1. Video Frame Extraction

The uploaded video is processed using computer vision techniques.

Frames are extracted from the video to convert the video into a sequence of images that can be analyzed by the deep learning model.

### 2. Spatial Feature Extraction

The extracted frames are analyzed using a CNN-based architecture.

The model learns visual features such as:

- Facial characteristics
- Texture patterns
- Visual inconsistencies
- Face manipulation artifacts
- Spatial information within individual frames

The project uses a hybrid ResNet–MobileNet architecture to extract and analyze visual features.

### 3. Temporal Analysis

Video frames contain information not only individually but also in their sequence.

Temporal analysis helps examine patterns across multiple frames and identify inconsistencies that may occur during facial manipulation.

### 4. Deep Learning Classification

The extracted features are processed by the trained model to generate a prediction.

The system classifies the uploaded video into one of the following categories:

- **REAL** – The video is classified as authentic.
- **FAKE** – The video is classified as potentially manipulated or deepfake-generated.

---

## 🔄 System Workflow

```text
                 User
                  |
                  v
          Upload Video
                  |
                  v
       React Web Application
                  |
                  v
          Backend API
                  |
                  v
       Video Processing Module
                  |
                  v
          Frame Extraction
                  |
                  v
       Deep Learning Model
      (ResNet + MobileNet)
                  |
                  v
       Feature Extraction
                  |
                  v
        Temporal Analysis
                  |
                  v
        Classification Model
                  |
                  v
         REAL / FAKE Result
                  |
                  v
       Display Result to User



## ⚙️ Installation and Setup

### Prerequisites

Make sure the following software is installed:

- Python 3.8 or above
- Node.js
- npm
- Git

### 1. Backend Setup

Navigate to the backend directory:

```bash
cd backend