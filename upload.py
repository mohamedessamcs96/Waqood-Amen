#!/usr/bin/env python3
"""
Upload a video to the Gas Station Monitoring API.
Uploads the video and waits for background analysis to complete.

Usage:
    python upload.py                          # Upload cars.MP4 with auto-generated plate
    python upload.py --video my_video.mp4     # Upload specific video
    python upload.py --plate "ABC-123"        # Upload with specific plate number
"""
import requests
import time
import sys
import os
import argparse

API_URL = "http://localhost:8000"


def upload_video(video_path: str, plate: str = ""):
    """Upload video and wait for analysis."""

    if not os.path.exists(video_path):
        print(f" Video file not found: {video_path}")
        sys.exit(1)

    file_size = os.path.getsize(video_path) / (1024 * 1024)
    print(f" Video: {video_path} ({file_size:.1f} MB)")
    print(f"  Plate: {plate or '(auto-generated)'}")
    print()

    # Step 1: Upload
    print(" Uploading video...")
    start = time.time()
    with open(video_path, "rb") as f:
        files = {"video": (os.path.basename(video_path), f, "video/mp4")}
        data = {"plate": plate}
        response = requests.post(f"{API_URL}/api/cars/upload_video/", files=files, data=data, timeout=120)

    if response.status_code != 201:
        print(f" Upload failed: {response.text}")
        sys.exit(1)

    result = response.json()
    car_id = result["car_id"]
    upload_time = time.time() - start
    print(f" Uploaded in {upload_time:.1f}s — Car ID: {car_id}")

    # Show alert if plate has unpaid history
    if result.get("alert"):
        alert = result["alert"]
        print(f"\n ALERT: {alert['message']}")
        print()

    # Step 2: Wait for background analysis
    print(" Waiting for YOLO analysis to complete...")
    for i in range(120):  # Wait up to 10 minutes
        time.sleep(5)
        try:
            status_resp = requests.get(f"{API_URL}/api/cars/analysis_status/?car_id={car_id}", timeout=10)
            if status_resp.status_code == 200:
                status_data = status_resp.json()
                if status_data.get("analyzed"):
                    elapsed = time.time() - start
                    print(f"\n Analysis complete in {elapsed:.0f}s!")
                    print(f"    Vehicles detected: {status_data['vehicle_count']}")
                    return result
                else:
                    dots = "." * ((i % 3) + 1)
                    print(f"    Analyzing{dots} ({(i + 1) * 5}s)", end="\r")
        except Exception:
            pass

    print("\n Analysis timeout — it may still be running in the background.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to Gas Station Monitoring API")
    parser.add_argument("--video", default="cars.MP4", help="Path to video file")
    parser.add_argument("--plate", default="", help="License plate number (optional)")
    args = parser.parse_args()

    upload_video(args.video, args.plate)