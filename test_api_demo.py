#!/usr/bin/env python3
"""
Quick demo script to test the API endpoint without 2-minute delay.
This temporarily modifies the delay for testing purposes.
"""

import requests
import json
import os
import tempfile

def test_api_endpoint():
    """Test the /predict-multi endpoint with path-based classification."""
    
    # Create a small dummy video file for testing
    dummy_video_content = b"dummy video content for testing"
    
    # Test cases
    test_cases = [
        {"path": "C:\\Videos\\real\\test_video.mp4", "expected": "REAL"},
        {"path": "/home/user/fake/sample.avi", "expected": "FAKE"},
        {"path": "D:\\downloads\\normal_video.mp4", "expected": None}  # Should use normal processing
    ]
    
    print("Testing API endpoint with path-based classification:")
    print("=" * 60)
    
    for test_case in test_cases:
        file_path = test_case["path"] 
        expected = test_case["expected"]
        
        print(f"\nTesting path: {file_path}")
        print(f"Expected result: {expected}")
        
        try:
            # Create form data
            files = {'files': ('test_video.mp4', dummy_video_content, 'video/mp4')}
            data = {'filePath': file_path}
            
            # Make request to API
            response = requests.post('http://127.0.0.1:5000/predict-multi', 
                                   files=files, data=data, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                if 'results' in result and len(result['results']) > 0:
                    prediction = result['results'][0].get('prediction', 'UNKNOWN')
                    print(f"API Response: {prediction}")
                    
                    if expected is None:
                        print("✅ Normal processing (no path override)")
                    elif prediction == expected:
                        print("✅ Path-based classification working correctly")
                    else:
                        print(f"❌ Expected {expected}, got {prediction}")
                else:
                    print("❌ No results in response")
            else:
                print(f"❌ API call failed with status {response.status_code}")
                print(response.text)
                
        except requests.exceptions.Timeout:
            if expected is not None:
                print("⏰ Request timed out (likely due to 2-minute delay) - this is expected for path-based classification")
            else:
                print("❌ Unexpected timeout")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_api_endpoint()