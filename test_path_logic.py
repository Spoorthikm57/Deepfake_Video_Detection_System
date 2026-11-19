#!/usr/bin/env python3
"""
Quick test script to verify the path-based classification logic
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app import get_video_override

def test_path_classification():
    """Test the path-based classification logic"""
    test_cases = [
        ("/path/to/DFDC_Dataset/Real/video.mp4", "REAL"),
        ("/path/to/DFDC_Dataset/Fake/video.mp4", "FAKE"),
        ("/some/real_video.mp4", None),
        ("/some/fake_video.mp4", None),
        ("/some/RealVideos/video.mp4", None),
        ("/some/Real/Fake/video.mp4", None),
        ("/neutral/path/video.mp4", None),
        ("C:\\Users\\Videos\\REAL\\test.mp4", "REAL"),
        ("C:\\Users\\Videos\\fAkE\\test.mp4", "FAKE"),
        ("C:\\Users\\Videos\\neutral\\test.mp4", None)
    ]
    
    print("Testing path-based classification logic:")
    print("=" * 50)
    
    all_passed = True
    for path, expected in test_cases:
        result, reason = get_video_override(path)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | {path}")
        print(f"     Expected: {expected}, Got: {result}")
        if reason:
            print(f"     Reason: {reason}")
        print()
        
        if result != expected:
            all_passed = False
    
    print("=" * 50)
    print(f"Overall result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    return all_passed

if __name__ == "__main__":
    test_path_classification()