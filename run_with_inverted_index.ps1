# PowerShell script to run the app with inverted class indices

# Activate virtual environment
& ".\.venv\Scripts\Activate.ps1"

# Set inverted class index (model predicts class 1=REAL, class 0=FAKE)
$env:INVERT_CLASS_INDEX = "1"

# Show current configuration
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CONFIGURATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "INVERT_CLASS_INDEX: $env:INVERT_CLASS_INDEX" -ForegroundColor Green
Write-Host "This means:" -ForegroundColor Yellow
Write-Host "  - Class 1 → REAL (authentic)" -ForegroundColor Green
Write-Host "  - Class 0 → FAKE (deepfake)" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start the app
cd src
python app.py
