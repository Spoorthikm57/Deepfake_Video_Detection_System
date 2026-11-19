#!/usr/bin/env python3
"""
Test script to analyze specific videos and check their outputs.
"""
import sys
import os
import logging
sys.path.append('.')

# Reduce logging verbosity for cleaner output
logging.basicConfig(level=logging.ERROR)

from app import analyze_video_full

def test_video(video_path, expected_result=None):
    """Test a single video and show results."""
    print(f"\n{'='*60}")
    print(f"Testing: {video_path}")
    print('='*60)
    
    if not os.path.exists(video_path):
        print(f"❌ Video not found: {video_path}")
        return
    
    try:
        result = analyze_video_full(video_path)
        
        if 'error' in result:
            print(f"❌ ERROR: {result['error']}")
            return
        
        prediction = result['prediction']
        real_frames = result['frame_counts']['REAL']
        fake_frames = result['frame_counts']['FAKE']
        total_analyzed = result['frames_used']
        
        print(f"📊 ANALYSIS RESULTS:")
        print(f"   Final Prediction: {prediction}")
        print(f"   REAL frames: {real_frames}")
        print(f"   FAKE frames: {fake_frames}")
        print(f"   Total analyzed: {total_analyzed}")
        print(f"   Decision rule: REAL frames >= 10 → REAL, else FAKE")
        
        if expected_result:
            if prediction.upper() == expected_result.upper():
                print(f"✅ PASS: Expected {expected_result.upper()}, got {prediction}")
            else:
                print(f"❌ FAIL: Expected {expected_result.upper()}, got {prediction}")
                print(f"   To get {expected_result.upper()}: need {'≥10' if expected_result.upper() == 'REAL' else '<10'} REAL frames")
                print(f"   Currently has: {real_frames} REAL frames")
        
    except Exception as e:
        print(f"❌ ERROR processing video: {e}")
        import traceback
        traceback.print_exc()

def main():
    print("🎬 VIDEO ANALYSIS TEST SUITE")
    print("Testing videos with 10-frame threshold rule")
    
    # Test the videos mentioned by user
    test_videos = [
        # Similar to "01_02__outside_talking_still_laughing__YVGY8LOK" -> should be FAKE
        ('uploads/07__outside_talking_still_laughing.mp4', 'FAKE'),
        
        # Similar to "01_02__walk_down_hall_angry__YVGY8LOK" -> should be FAKE  
        ('uploads/14__walk_down_hall_angry.mp4', 'FAKE'),
        
        # Similar to "01__exit_phone_room" -> should be REAL
        ('uploads/01__talking_against_wall.mp4', 'REAL'),
    ]
    
    for video_path, expected in test_videos:
        test_video(video_path, expected)
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY:")
    print("- Current rule: If REAL frames >= 10 → REAL, else FAKE")
    print("- To force FAKE: video must have < 10 REAL frames")  
    print("- To force REAL: video must have >= 10 REAL frames")
    print('='*60)

if __name__ == "__main__":
    main()