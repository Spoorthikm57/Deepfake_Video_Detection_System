# Final Result Formula - Majority Voting System

## Overview

The video classification now uses a **majority voting system** based on frame classification percentages, rather than a fixed threshold.

---

## Mathematical Formula

### Given Variables
- **T** = Total number of extracted frames
- **R** = Number of frames classified as REAL
- **F** = Number of frames classified as FAKE

### Calculate Percentages

$$\text{Real\%} = \frac{R}{T} \times 100$$

$$\text{Fake\%} = \frac{F}{T} \times 100$$

### Final Decision Rule

$$\text{Result} = \begin{cases}
\text{REAL} & \text{if } \text{Real\%} > \text{Fake\%} \\
\text{FAKE} & \text{if } \text{Fake\%} > \text{Real\%} \\
\text{UNCERTAIN} & \text{if } \text{Real\%} = \text{Fake\%}
\end{cases}$$

---

## Decision Logic

### Case 1: REAL Decision
**Condition**: Real% > Fake%

**Meaning**: More frames classified as REAL than FAKE

**Example**:
- Total frames (T) = 100
- Real frames (R) = 75 → Real% = 75%
- Fake frames (F) = 25 → Fake% = 25%
- Decision: **REAL** ✅ (75% > 25%)

### Case 2: FAKE Decision
**Condition**: Fake% > Real%

**Meaning**: More frames classified as FAKE than REAL

**Example**:
- Total frames (T) = 100
- Real frames (R) = 30 → Real% = 30%
- Fake frames (F) = 70 → Fake% = 70%
- Decision: **FAKE** ❌ (70% > 30%)

### Case 3: UNCERTAIN Decision
**Condition**: Real% = Fake%

**Meaning**: Equal number of REAL and FAKE frames (tie)

**Example**:
- Total frames (T) = 100
- Real frames (R) = 50 → Real% = 50%
- Fake frames (F) = 50 → Fake% = 50%
- Decision: **UNCERTAIN** ? (50% = 50%)

---

## Decision Matrix

| Real Frames | Fake Frames | Total | Real % | Fake % | Decision | Reason |
|---|---|---|---|---|---|---|
| 95 | 5 | 100 | 95% | 5% | **REAL** ✅ | 95% > 5% |
| 75 | 25 | 100 | 75% | 25% | **REAL** ✅ | 75% > 25% |
| 51 | 49 | 100 | 51% | 49% | **REAL** ✅ | 51% > 49% |
| 50 | 50 | 100 | 50% | 50% | **UNCERTAIN** ? | 50% = 50% |
| 49 | 51 | 100 | 49% | 51% | **FAKE** ❌ | 51% > 49% |
| 25 | 75 | 100 | 25% | 75% | **FAKE** ❌ | 75% > 25% |
| 10 | 90 | 100 | 10% | 90% | **FAKE** ❌ | 90% > 10% |

---

## Key Characteristics

### Majority Rule
The system simply compares percentages:
- **Majority of frames** are classified as a particular type → That type wins
- **Equal split** → Uncertain

### Sensitivity
- **Very sensitive to frame distribution**: Even a single frame difference changes the outcome
- For 100 frames: 51 Real, 49 Fake → REAL
- For 100 frames: 50 Real, 50 Fake → UNCERTAIN
- For 100 frames: 49 Real, 51 Fake → FAKE

### Edge Cases
1. **Empty video (0 frames)**: Returns UNCERTAIN
2. **Single frame**: Always either REAL or FAKE (never UNCERTAIN)
3. **Even number of frames**: Can result in UNCERTAIN (perfect tie)
4. **Odd number of frames**: Always has a majority (never UNCERTAIN)

---

## Comparison with Threshold System

### Old System (30% Threshold)
```
If (FAKE / Total) > 0.30 → FAKE
Else → REAL
```
- Fixed threshold at 30%
- Could classify as REAL even if 49% were FAKE
- Two possible outcomes: REAL or FAKE

### New System (Majority Voting)
```
If Real% > Fake% → REAL
If Fake% > Real% → FAKE
If Real% = Fake% → UNCERTAIN
```
- Dynamic comparison (50% implicit threshold)
- More balanced assessment
- Three possible outcomes: REAL, FAKE, or UNCERTAIN

---

## Confidence Score

The confidence is calculated based on distance from 50%:

$$\text{Confidence} = \left|0.5 - \frac{\text{Decision\%}}{100}\right|$$

### Examples:
- 95% REAL, 5% FAKE → Confidence = |0.5 - 0.05| = 0.45
- 75% REAL, 25% FAKE → Confidence = |0.5 - 0.25| = 0.25
- 51% REAL, 49% FAKE → Confidence = |0.5 - 0.49| = 0.01
- 50% REAL, 50% FAKE → Confidence = 0.0 (UNCERTAIN, no confidence)

### Confidence Range
- **1.0**: Impossible (would mean 0% or 100%)
- **0.5**: Highest possible (100% vs 0%)
- **0.0**: Minimum (50% vs 50%, UNCERTAIN)

---

## Implementation Example

### Python Code
```python
def decide_video_label(real_count, fake_count, total_frames):
    if total_frames == 0:
        return "UNCERTAIN"
    
    real_percentage = (real_count / total_frames) * 100
    fake_percentage = (fake_count / total_frames) * 100
    
    if real_percentage > fake_percentage:
        return "REAL"
    elif fake_percentage > real_percentage:
        return "FAKE"
    else:
        return "UNCERTAIN"
```

### Usage
```python
# Example 1: Clearly real
result = decide_video_label(80, 20, 100)  # Returns "REAL"

# Example 2: Clearly fake
result = decide_video_label(20, 80, 100)  # Returns "FAKE"

# Example 3: Uncertain
result = decide_video_label(50, 50, 100)  # Returns "UNCERTAIN"

# Example 4: Barely real
result = decide_video_label(51, 49, 100)  # Returns "REAL"
```

---

## When to Use Each Decision

### REAL ✅
- Use when: **Real frames > Fake frames**
- Confidence: Higher when percentage difference is larger
- Example: 80% real, 20% fake → High confidence REAL
- Example: 51% real, 49% fake → Low confidence REAL

### FAKE ❌
- Use when: **Fake frames > Real frames**
- Confidence: Higher when percentage difference is larger
- Example: 10% real, 90% fake → High confidence FAKE
- Example: 49% real, 51% fake → Low confidence FAKE

### UNCERTAIN ?
- Use when: **Real frames = Fake frames**
- Confidence: Always 0.0 (no confidence)
- Recommendation: Requires human review or re-analysis
- Example: 50 real, 50 fake frames

---

## Frame Count Examples

### Scenario: 100 Total Frames

| Real | Fake | Real% | Fake% | Decision |
|-----|------|-------|-------|----------|
| 100 | 0    | 100%  | 0%    | REAL ✅  |
| 90  | 10   | 90%   | 10%   | REAL ✅  |
| 75  | 25   | 75%   | 25%   | REAL ✅  |
| 60  | 40   | 60%   | 40%   | REAL ✅  |
| 51  | 49   | 51%   | 49%   | REAL ✅  |
| 50  | 50   | 50%   | 50%   | UNCERTAIN ? |
| 49  | 51   | 49%   | 51%   | FAKE ❌  |
| 40  | 60   | 40%   | 60%   | FAKE ❌  |
| 25  | 75   | 25%   | 75%   | FAKE ❌  |
| 10  | 90   | 10%   | 90%   | FAKE ❌  |
| 0   | 100  | 0%    | 100%  | FAKE ❌  |

### Scenario: 150 Total Frames

| Real | Fake | Real% | Fake% | Decision |
|-----|------|-------|-------|----------|
| 100 | 50   | 66.7% | 33.3% | REAL ✅  |
| 76  | 74   | 50.7% | 49.3% | REAL ✅  |
| 75  | 75   | 50%   | 50%   | UNCERTAIN ? |
| 74  | 76   | 49.3% | 50.7% | FAKE ❌  |
| 50  | 100  | 33.3% | 66.7% | FAKE ❌  |

---

## Mathematical Properties

### Symmetry
The decision is perfectly symmetric around 50%:
- 60% Real ↔ 40% Fake → REAL
- 40% Real ↔ 60% Fake → FAKE

### No Dead Zone
Unlike threshold systems, there is no "comfortable zone":
- Every 1% shift matters
- 50.1% vs 49.9% results in different decisions

### Tied Frames Impossible (Usually)
With odd total frames, a tie is impossible:
- 101 frames: Must have 51+ of one type (unless 50/51 split, but that's 49.5% vs 50.5%)
- 100 frames: Exactly 50/50 tie is possible

---

## API Response Structure

The results include detailed information:

```json
{
  "prediction": "REAL",
  "confidence": 0.25,
  "frames_analyzed": 100,
  "frame_counts": {
    "REAL": 75,
    "FAKE": 25
  },
  "percentages": {
    "REAL": 75.0,
    "FAKE": 25.0
  },
  "decision_reason": "Real% (75.0%) > Fake% (25.0%) → REAL",
  "average_probabilities": {
    "REAL": 0.78,
    "FAKE": 0.22
  }
}
```

---

## Summary

| Aspect | Description |
|--------|-------------|
| **Rule** | Majority voting: compare Real% vs Fake% |
| **Outcomes** | 3 possibilities: REAL, FAKE, UNCERTAIN |
| **Threshold** | Implicit 50% (no explicit threshold) |
| **Tie Handling** | Returns UNCERTAIN |
| **Confidence** | Distance from 50% boundary |
| **Best For** | Balanced assessment without bias |

---

**Updated**: November 25, 2025  
**Formula Version**: 2.0 (Majority Voting)  
**Previous Version**: 1.0 (30% Threshold)
