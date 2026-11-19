# Quick Reference - Majority Voting Formula

## The Formula (TL;DR)

$$\text{Result} = \begin{cases}
\text{REAL} & \text{if Real\%} > \text{Fake\%} \\
\text{FAKE} & \text{if Fake\%} > \text{Real\%} \\
\text{UNCERTAIN} & \text{if Real\%} = \text{Fake\%}
\end{cases}$$

Where:
- Real% = (R / T) × 100
- Fake% = (F / T) × 100
- R = real frame count
- F = fake frame count
- T = total frames

---

## Decision Table (100 Frames)

| Real | Fake | Decision |
|-----|------|----------|
| 95  | 5    | ✅ REAL  |
| 75  | 25   | ✅ REAL  |
| 51  | 49   | ✅ REAL  |
| 50  | 50   | ? UNCERTAIN |
| 49  | 51   | ❌ FAKE  |
| 25  | 75   | ❌ FAKE  |
| 10  | 90   | ❌ FAKE  |

---

## Code Example

```python
def decide_video(real_count, fake_count, total):
    if total == 0:
        return "UNCERTAIN"
    
    real_pct = (real_count / total) * 100
    fake_pct = (fake_count / total) * 100
    
    if real_pct > fake_pct:
        return "REAL"
    elif fake_pct > real_pct:
        return "FAKE"
    else:
        return "UNCERTAIN"
```

---

## Key Points

✅ **Majority wins**: Whichever percentage is higher wins  
✅ **Three outcomes**: REAL, FAKE, or UNCERTAIN (tied)  
✅ **No threshold**: Just compare percentages (implicit 50%)  
✅ **Symmetric**: 60% vs 40% = REAL, 40% vs 60% = FAKE  
✅ **Sensitive**: Even 51% vs 49% results in a decision  

---

## Confidence = Distance from 50%

- 95% REAL → Confidence = 0.45
- 75% REAL → Confidence = 0.25
- 51% REAL → Confidence = 0.01
- 50% REAL → Confidence = 0.00 (UNCERTAIN)

---

**New Formula**: Majority Voting (November 25, 2025)  
**Previous**: 30% Threshold Rule
