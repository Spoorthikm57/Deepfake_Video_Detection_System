export default function Home() {
  return (
    <div className="container">
      <div className="hero">
        <h1 style={{ fontSize: 48, marginBottom: 12, fontWeight: 700 }}>Deepfake Video Detection System</h1>
        <p style={{ fontSize: 22, fontWeight: 600, margin: '8px 0', color: '#94a3b8' }}>Done by Spoorthi K M and Rakshitha M</p>
        <p style={{ color: '#94a3b8' }}>Under the Guidance of R C Ravindrnath</p>
        <div className="card" style={{ width: '90%', maxWidth: 960, margin: '26px auto' }}>
          <a href="/upload" className="btn">Predict Videos</a>
        </div>
      </div>

      {/* About section */}
      <div className="grid" style={{ marginTop: 24 }}>
        <div className="card" style={{ textAlign: 'left' }}>
          <h2 style={{ marginTop: 0 }}>Models used</h2>
          <ul style={{ lineHeight: 1.6 }}>
            <li><strong>ResNet‑18</strong> — compact residual CNN fine‑tuned for binary REAL/FAKE classification.</li>
            <li><strong>MobileNetV2</strong> — lightweight, mobile‑friendly backbone adapted to 2‑class output.</li>
            <li><strong>EfficientNet‑B0</strong> — parameter‑efficient model fine‑tuned for deepfake detection.</li>
          </ul>
          <p className="muted" style={{ marginTop: 8 }}>
            During inference we optionally apply face‑crop (Haar cascade), resize to 224×224, and use softmax
            probabilities per frame. Multiple models can run together as an ensemble.
          </p>
        </div>

        <div className="card" style={{ textAlign: 'left' }}>
          <h2 style={{ marginTop: 0 }}>What’s different in this project</h2>
          <ul style={{ lineHeight: 1.6 }}>
            <li><strong>Ensemble & decision rule</strong>: per‑frame probabilities are averaged across models; a video is
              flagged FAKE if more than 30% of analyzed frames are predicted FAKE.</li>
            <li><strong>Face‑aware preprocessing</strong>: optional face detection/cropping improves signal‑to‑noise on frames.</li>
            <li><strong>Mixed data sources</strong>: prepared from DFDC and FF++ assets with curated frame extraction.</li>
            <li><strong>Transparent outputs</strong>: UI shows REAL/FAKE frame counts, average probabilities, and per‑model summary.</li>
            <li><strong>Batch uploads</strong>: analyze multiple videos at once for faster evaluation.</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
