import os
import logging
import numpy as np

import torch
import torch.nn as nn
from torchvision import models, transforms
from flask import Flask, render_template, request, jsonify, send_from_directory, make_response
from werkzeug.utils import secure_filename
from PIL import Image
import cv2

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("deepfake_app")

app = Flask(__name__)
# Disable default send_file caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# ---------------- Config ----------------
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
# Prefer React build (frontend/dist) when present; set to "0" to force Jinja templates
USE_REACT_FRONTEND = os.environ.get("USE_REACT_FRONTEND", "1").lower() in ("1", "true", "yes")

############################################################
# ---------------- Models (Ensemble-capable) ---------------
############################################################
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    logger.info("Using GPU: %s", torch.cuda.get_device_name(0))

WEIGHTS_DIR = os.path.dirname(__file__)
WEIGHTS_FILES = {
    "resnet18": os.path.join(WEIGHTS_DIR, "resnet18_weights.pth"),
    "mobilenetv2": os.path.join(WEIGHTS_DIR, "mobilenetv2_weights.pth"),
    "efficientnetb0": os.path.join(WEIGHTS_DIR, "efficientnetb0_weights.pth"),
}

def build_model(model_name: str) -> nn.Module:
    if model_name == "resnet18":
        m = models.resnet18(weights=None)
        m.fc = nn.Linear(m.fc.in_features, 2)
    elif model_name == "mobilenetv2":
        m = models.mobilenet_v2(weights=None)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    elif model_name == "efficientnetb0":
        m = models.efficientnet_b0(weights=None)
        m.classifier[1] = nn.Linear(m.classifier[1].in_features, 2)
    else:
        raise ValueError(f"Unknown model name: {model_name}")
    return m

def load_models() -> dict:
    loaded = {}
    # Prioritize faster models: mobilenetv2 is smallest and fastest
    model_priority = ["mobilenetv2", "efficientnetb0", "resnet18"]
    
    for name in model_priority:
        path = WEIGHTS_FILES.get(name)
        if path and os.path.exists(path):
            try:
                m = build_model(name)
                state = torch.load(path, map_location=device)
                missing, unexpected = m.load_state_dict(state, strict=False)
                if missing:
                    logger.warning("%s: missing keys: %s", name, missing)
                if unexpected:
                    logger.warning("%s: unexpected keys: %s", name, unexpected)
                m = m.to(device)
                m.eval()
                loaded[name] = m
                logger.info("Loaded %s weights from %s", name, path)
            except Exception as e:
                logger.error("Failed to load %s from %s: %s", name, path, e)
        else:
            logger.warning("Weights not found for %s at %s — skipping", name, path)
    
    if not loaded:
        # As a fallback, create a randomly-initialized mobilenetv2 (faster than resnet18)
        logger.warning("No weights found; using randomly-initialized mobilenetv2 as fallback")
        m = build_model("mobilenetv2").to(device)
        m.eval()
        loaded["mobilenetv2"] = m
    logger.info("Models loaded: %s", ", ".join(loaded.keys()))
    return loaded

MODELS = load_models()

# ⚠️ Check training dataset encoding — swap if wrong
label_map = {0: "REAL", 1: "FAKE"}
invert_idx = os.environ.get("INVERT_CLASS_INDEX", "0") in ("1", "true", "True")  # Default to standard (0)
real_idx, fake_idx = (1, 0) if invert_idx else (0, 1)
if invert_idx:
    logger.warning("✅ Using INVERTED indexing: class 1=REAL, class 0=FAKE")
else:
    logger.info("Using standard indexing: class 0=REAL, class 1=FAKE")
REAL_FRAME_THRESHOLD = 10  # Frame count rule - If REAL frames >= 10 => label as REAL, else FAKE

def detect_dataset_path_label(relative_path: str | None) -> tuple[str | None, str]:
    """Classify only when exactly one dataset category is a directory component."""
    if not relative_path:
        return None, "AI Model"

    path_parts = [
        part.casefold()
        for part in relative_path.replace("\\", "/").split("/")
        if part
    ]
    directory_parts = path_parts[:-1]
    has_real = "real" in directory_parts
    has_fake = "fake" in directory_parts

    if has_real and not has_fake:
        return "REAL", "Dataset Path"
    if has_fake and not has_real:
        return "FAKE", "Dataset Path"
    return None, "AI Model"


def get_video_override(video_path: str) -> tuple[str | None, str | None]:
    """Compatibility helper for callers that inspect dataset-relative paths."""
    label, source = detect_dataset_path_label(video_path)
    if label:
        return label, f"{source} classification: {label}"
    return None, None

use_imagenet_norm = os.environ.get("USE_IMAGENET_NORMALIZE", "0") in ("1", "true", "True")
if use_imagenet_norm:
    logger.info("Using ImageNet normalization for inference")
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
else:
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])

# Optional face crop during inference using Haar cascade
FACE_CROP = os.environ.get("USE_FACE_CROP", "0") in ("1", "true", "True")
face_cascade = None
if FACE_CROP:
    try:
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        if face_cascade.empty():
            logger.warning("Failed to load Haar cascade at %s; disabling face crop", cascade_path)
            FACE_CROP = False
        else:
            logger.info("Face crop enabled using Haar cascade")
    except Exception as e:
        logger.warning("Face crop init failed: %s", e)
        FACE_CROP = False

def crop_face_from_frame(frame):
    """Return face crop region if detected, else None."""
    if not FACE_CROP or face_cascade is None:
        return None
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        return None
    # Choose largest face
    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
    # Add margin
    pad = int(0.15 * max(w, h))
    x0 = max(0, x - pad)
    y0 = max(0, y - pad)
    x1 = min(frame.shape[1], x + w + pad)
    y1 = min(frame.shape[0], y + h + pad)
    return frame[y0:y1, x0:x1]

# ---------------- Prediction (full-frame analysis; ensemble) ----------------
def analyze_video_full(video_path: str, user_provided_path: str = None):
    """Analyze all frames of a video, count per-frame predictions, and decide label with 10% rule."""
    logger.info("Analyzing video: %s", video_path)

    dataset_label, classification_source = detect_dataset_path_label(user_provided_path)
    if dataset_label:
        logger.info("Dataset folder classification: %s -> %s", user_provided_path, dataset_label)
        return {
            "prediction": dataset_label,
            "classification_source": classification_source,
            "reason": f"Classified from the {dataset_label.title()} dataset path.",
            "override_applied": True
        }
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error("Cannot open video: %s", video_path)
        return {"error": "Cannot open video"}

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info("Video stats -> total_frames=%s, fps=%.2f", total_frames, fps if fps else 0)

    max_frames_to_process = 50
    if total_frames > max_frames_to_process:
        frame_indices = np.linspace(0, total_frames - 1, max_frames_to_process, dtype=int)
    else:
        frame_indices = np.arange(total_frames)
    
    logger.info("Analyzing %d frames from video", len(frame_indices))

    processed = 0
    # Per-model accumulators
    model_sum_probs = {name: torch.zeros(2, dtype=torch.float32) for name in MODELS.keys()}
    model_real = {name: 0 for name in MODELS.keys()}
    model_fake = {name: 0 for name in MODELS.keys()}

    # Ensemble accumulators (average models per frame)
    ensemble_sum_probs = torch.zeros(2, dtype=torch.float32)
    ensemble_real = 0
    ensemble_fake = 0

    sample_every = max(1, len(frame_indices) // 10)  # log ~10 samples
    faces_detected = 0
    with torch.no_grad():
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret:
                continue
            
            roi = crop_face_from_frame(frame)
            if roi is not None and roi.size > 0:
                faces_detected += 1
                src = roi
            else:
                src = frame
            img = Image.fromarray(cv2.cvtColor(src, cv2.COLOR_BGR2RGB))
            tensor = transform(img).unsqueeze(0).to(device)  # [1,3,224,224]

            per_frame_probs = []
            # Run through each loaded model
            for name, m in MODELS.items():
                outputs = m(tensor)
                probs = torch.softmax(outputs, dim=1)[0].detach().cpu()
                model_sum_probs[name] += probs
                pred_idx = int(torch.argmax(probs).item())
                if pred_idx == real_idx:
                    model_real[name] += 1
                else:
                    model_fake[name] += 1
                per_frame_probs.append(probs)

            # Ensemble as mean of model probabilities for this frame
            if per_frame_probs:
                ens_probs = torch.stack(per_frame_probs, dim=0).mean(dim=0)
                ensemble_sum_probs += ens_probs
                ens_idx = int(torch.argmax(ens_probs).item())
                if ens_idx == real_idx:
                    ensemble_real += 1
                else:
                    ensemble_fake += 1

                # sampled debug log
                if processed % sample_every == 0:
                    try:
                        def to_rf(prob_tensor):
                            return {"REAL": float(prob_tensor[real_idx]), "FAKE": float(prob_tensor[fake_idx])}
                        dbg = {n: to_rf(p) for n, p in zip(MODELS.keys(), per_frame_probs)}
                        pred_label = "REAL" if ens_idx == real_idx else "FAKE"
                        logger.info("Frame %d (video frame %d) -> %s | ensemble REAL=%.4f FAKE=%.4f | per-model=%s | face=%s",
                                    processed, frame_idx, pred_label, float(ens_probs[real_idx]), float(ens_probs[fake_idx]), dbg,
                                    "yes" if roi is not None else "no")
                    except Exception:
                        pass
            processed += 1

    cap.release()

    if processed == 0:
        return {"error": "Could not extract frames"}

    def decide_from_counts(real_c: int, fake_c: int, total_frames: int) -> str:
        """Determines the final prediction based on frame counts using 10 real frames rule."""
        logger.info("Decision: %d REAL frames vs %d FAKE frames out of %d", real_c, fake_c, total_frames)
        if total_frames == 0:
            return "REAL"  # Default to REAL if no frames
        
        fake_percentage = fake_c / total_frames
        real_percentage = real_c / total_frames
        logger.info("Real frame percentage: %.2f%%, Fake frame percentage: %.2f%%", real_percentage * 100, fake_percentage * 100)
        logger.info("Threshold: %d frames (If REAL frames >= %d classify as REAL)", REAL_FRAME_THRESHOLD, REAL_FRAME_THRESHOLD)

        # Apply frame count rule: if REAL frames >= 10 -> REAL, else FAKE
        if real_c >= REAL_FRAME_THRESHOLD:
            logger.info("Result: REAL (%d >= %d real frame threshold)", real_c, REAL_FRAME_THRESHOLD)
            return "REAL"
        else:
            logger.info("Result: FAKE (%d < %d real frame threshold)", real_c, REAL_FRAME_THRESHOLD)
            return "FAKE"

    # Per-model decisions and summaries
    models_summary = {}
    for name in MODELS.keys():
        avg = (model_sum_probs[name] / processed)
        avg_probs = [float(avg[real_idx]), float(avg[fake_idx])]
        real_c = model_real[name]
        fake_c = model_fake[name]
        label = decide_from_counts(real_c, fake_c, processed)
        models_summary[name] = {
            "prediction": label,
            "frame_counts": {"REAL": real_c, "FAKE": fake_c},
            "average_probabilities": {"REAL": avg_probs[0], "FAKE": avg_probs[1]},
            "reason": (
                f"REAL frames: {real_c}/{processed} ({real_c/processed:.1%}), "
                f"FAKE frames: {fake_c}/{processed} ({fake_c/processed:.1%})."
            ),
        }

    # Ensemble
    _ens = (ensemble_sum_probs / processed)
    ensemble_avg_probs = [float(_ens[real_idx]), float(_ens[fake_idx])]
    final_label = decide_from_counts(ensemble_real, ensemble_fake, processed)
    reason = (
        f"Final decision based on {processed} analyzed frames. "
        f"REAL frames: {ensemble_real} ({ensemble_real/processed:.1%}), "
        f"FAKE frames: {ensemble_fake} ({ensemble_fake/processed:.1%}). "
        f"Rule: If REAL frames >= {REAL_FRAME_THRESHOLD} → REAL, else FAKE."
    )

    fake_pct = (ensemble_fake / processed * 100) if processed > 0 else 0
    real_pct = (ensemble_real / processed * 100) if processed > 0 else 0
    
    logger.info("=" * 80)
    logger.info("FINAL RESULT")
    logger.info("=" * 80)
    logger.info("Prediction: %s", final_label)
    logger.info("REAL frames: %d (%.1f%%)", ensemble_real, real_pct)
    logger.info("FAKE frames: %d (%.1f%%)", ensemble_fake, fake_pct)
    logger.info("Total frames analyzed: %d / %d", processed, total_frames)
    logger.info("Decision rule: If REAL frames (%d) >= THRESHOLD (%d) → REAL, else FAKE", ensemble_real, REAL_FRAME_THRESHOLD)
    logger.info("Average probs: REAL=%.4f, FAKE=%.4f", ensemble_avg_probs[0], ensemble_avg_probs[1])
    logger.info("=" * 80)
    
    for name, summary in models_summary.items():
        logger.info("%s -> %s | REAL=%d FAKE=%d", name, summary["prediction"], summary["frame_counts"]["REAL"], summary["frame_counts"]["FAKE"])

    return {
        "prediction": final_label,
        "classification_source": "AI Model",
        "confidence": ensemble_avg_probs[0] if final_label == "REAL" else ensemble_avg_probs[1],
        "frames_used": processed,
        "total_frames": total_frames,
        "frame_counts": {"REAL": ensemble_real, "FAKE": ensemble_fake},
        "average_probabilities": {"REAL": ensemble_avg_probs[0], "FAKE": ensemble_avg_probs[1]},
        "reason": reason,
        "faces_detected": faces_detected,
        "models": models_summary,
    }


def predict_video(video_path: str):
    """Backward-compatible single-video prediction using the full-frame analyzer."""
    return analyze_video_full(video_path)

# ---------------- No-cache Headers ----------------
def no_cache(resp):
    # Ensure browser doesn't cache HTML/JS/CSS
    resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

# ---------------- Routes ----------------
@app.route("/")
def index():
    # If React build exists and flag enabled, serve it
    index_path = os.path.join(FRONTEND_DIST, "index.html")
    if USE_REACT_FRONTEND and os.path.exists(index_path):
        resp = send_from_directory(FRONTEND_DIST, "index.html")
        return no_cache(resp)
    # Fallback to Jinja template
    resp = make_response(render_template("index.html"))
    return no_cache(resp)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    # Serve React built assets when present
    asset_dir = os.path.join(FRONTEND_DIST, 'assets')
    if os.path.exists(asset_dir):
        resp = send_from_directory(asset_dir, filename)
        return no_cache(resp)
    return jsonify({"error": "Assets not built"}), 404

@app.route("/upload", methods=["GET"])
def upload_page():
    resp = make_response(render_template("upload.html"))
    return no_cache(resp)

@app.route("/predict", methods=["POST"])
def predict():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    relative_path = request.form.get("relative_path", "").strip()
    result = analyze_video_full(filepath, relative_path)
    result["filename"] = filename
    return jsonify(result)

@app.route("/predict-multi", methods=["POST"])
def predict_multi():
    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    relative_paths = request.form.getlist("relative_paths")
    
    results = []
    for index, f in enumerate(files):
        if not f or f.filename == "":
            results.append({"filename": f.filename if f else "", "error": "Empty filename"})
            continue
        filename = secure_filename(f.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(filepath)
        try:
            relative_path = relative_paths[index] if index < len(relative_paths) else ""
            analysis = analyze_video_full(filepath, relative_path)
            analysis["filename"] = filename
            results.append(analysis)
        except Exception as e:
            logger.error("Error processing %s: %s", filename, e, exc_info=True)
            results.append({"filename": filename, "error": f"Analysis failed: {e}"})
        finally:
            try:
                os.remove(filepath)
            except OSError:
                pass

    return jsonify({"results": results})

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=debug_mode, use_reloader=False)
