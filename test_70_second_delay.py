#!/usr/bin/env python3
"""
Quick test script to verify the 70-second delay and path-based classification logic.
"""
import requests
import time
import json

BASE_URL = "http://127.0.0.1:5000"

def test_path_classification():
    print("Testing path-based classification with 70-second delay...")
    
    # Create a dummy video file for upload
    dummy_video_content = b"dummy video content for testing"
    
    # Test case 1: Path with 'real'
    print("\n=== Test Case 1: Path containing 'real' ===")
    files = {'files': ('test_video.mp4', dummy_video_content, 'video/mp4')}
    data = {'filePath': '/path/to/real/video.mp4'}
    
    start_time = time.time()
    try:
        response = requests.post(f"{BASE_URL}/predict-multi", files=files, data=data, timeout=120)
        end_time = time.time()
        
        if response.status_code == 200:
            result = response.json()
            duration = end_time - start_time
            print(f"✅ Request completed in {duration:.1f} seconds")
            print(f"📊 Result: {json.dumps(result, indent=2)}")
            
            if 60 < duration < 80:  # Should be around 70 seconds
                print("✅ Delay timing is correct (around 70 seconds)")
            else:
                print(f"⚠️  Unexpected timing: {duration:.1f} seconds (expected ~70)")
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_path_classification()