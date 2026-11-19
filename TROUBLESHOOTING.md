# 🔧 Troubleshooting Real Videos Being Predicted as Fake

## Problem
Every video is being classified as FAKE, regardless of whether it's real or fake.

## Quick Fix: Enable Inverted Class Index

### Option 1: Use the Ready-Made Script (Easiest)

**PowerShell:**
```powershell
cd "C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system"
.\run_with_inverted_index.ps1
```

**Command Prompt:**
```cmd
cd "C:\Users\m6793\Downloads\MY PROJECTS\deepfake_videodetection_system"
run_with_inverted_index.bat
```

### Option 2: Manual Command Line

**PowerShell:**
```powershell
cd src
$env:INVERT_CLASS_INDEX = "1"
python app.py
```

**Command Prompt:**
```cmd
cd src
set INVERT_CLASS_INDEX=1
python app.py
```

## Understanding the Fix

### What Was Wrong?
Your model weights were trained with inverted class indices:
- Class **0** = **FAKE** (deepfake)
- Class **1** = **REAL** (authentic)

But the app was interpreting them as:
- Class **0** = REAL
- Class **1** = FAKE

This caused everything to be classified backwards as FAKE.

### What the Fix Does
When you set `INVERT_CLASS_INDEX=1`, the app now correctly interprets:
- Class **1** = **REAL** ✅
- Class **0** = **FAKE** ✅

## How the Decision Logic Works (30% Rule)

After enabling the fix, your videos should be classified correctly:

```
Analyzed 100 frames:
- 70 frames detected as REAL
- 30 frames detected as FAKE
- FAKE%: 30% (NOT > 30% threshold)
- Result: REAL ✅
```

vs.

```
Analyzed 100 frames:
- 40 frames detected as REAL  
- 60 frames detected as FAKE
- FAKE%: 60% (> 30% threshold)
- Result: FAKE ❌
```

## Verification Steps

1. **Enable inverted index** using one of the methods above
2. **Look at console output** for this message:
   ```
   ✅ Using INVERTED indexing: class 1=REAL, class 0=FAKE
   ```
3. **Check the detailed logs** showing frame-by-frame predictions:
   ```
   Frame 0 (video frame 0) -> REAL | ensemble REAL=0.8234 FAKE=0.1766
   Frame 1 (video frame 10) -> FAKE | ensemble REAL=0.3445 FAKE=0.6555
   ...
   ```
4. **Final result** will show clear breakdown:
   ```
   ================================================================================
   FINAL RESULT
   ================================================================================
   Prediction: REAL
   REAL frames: 70 (70.0%)
   FAKE frames: 30 (30.0%)
   Total frames analyzed: 100 / 549
   Decision rule: If FAKE% (30.0%) > THRESHOLD (30.0%) → FAKE, else REAL
   ```

## Step-by-Step Fix Process

1. **Stop the current app** (if running) - Press Ctrl+C in the terminal

2. **Use one of the start scripts:**
   - Double-click `run_with_inverted_index.ps1` (PowerShell preferred)
   - OR double-click `run_with_inverted_index.bat` (Command Prompt)
   - OR manually run the commands above

3. **Test with a real video** - Upload a genuine video
   - It should now show more REAL frames than FAKE

4. **Test with a fake video** - Upload a deepfake video
   - It should show more FAKE frames than REAL

## Permanent Configuration (Optional)

To make this permanent, add to a `.env` file in the project root:
```
INVERT_CLASS_INDEX=1
```

Then the app will always use inverted indices without setting environment variables.

## Advanced Troubleshooting

### Model Still Doesn't Work Right?

Check your model weights are correct:
```python
# Expected model output format:
# Class 0: Should activate for FAKE videos
# Class 1: Should activate for REAL videos
# If this is backwards, you need to retrain or use a different model
```

### Want to See More Details?

The app now logs everything:
- Each frame's REAL/FAKE probability
- Running count of predictions  
- Final decision logic
- Per-model breakdown

All visible in the console where you run the app.

## Need to Switch Back?

To use standard (non-inverted) indices:
```powershell
$env:INVERT_CLASS_INDEX = "0"  # or just omit it - defaults to "1" now
python app.py
```
