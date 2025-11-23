#!/usr/bin/env python3
"""
Script download videos từ JSON data
Hỗ trợ YouTube và direct video links
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List, Dict


def check_dependencies():
    """Kiểm tra các tool cần thiết"""
    print("🔍 Checking dependencies...")
    
    # Check yt-dlp
    try:
        result = subprocess.run(['yt-dlp', '--version'], 
                              capture_output=True, text=True)
        print(f"  ✅ yt-dlp version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("  ❌ yt-dlp not found")
        print("\n📥 Cài đặt yt-dlp:")
        print("  macOS: brew install yt-dlp")
        print("  hoặc: pip install yt-dlp")
        return False


def download_youtube_video(video_url: str, output_dir: str, video_id: str):
    """Download YouTube video using yt-dlp"""
    try:
        output_path = os.path.join(output_dir, f"{video_id}.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '-f', 'best',  # Best quality
            '-o', output_path,
            '--write-description',  # Save description
            '--write-info-json',    # Save metadata
            video_url
        ]
        
        print(f"    Downloading: {video_id}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"    ✅ Downloaded successfully")
            return True
        else:
            print(f"    ❌ Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"    ❌ Exception: {e}")
        return False


def download_direct_video(video_url: str, output_dir: str, filename: str):
    """Download direct video URL"""
    try:
        output_path = os.path.join(output_dir, filename)
        
        # Use curl or wget
        cmd = ['curl', '-L', '-o', output_path, video_url]
        
        print(f"    Downloading: {filename}")
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode == 0:
            print(f"    ✅ Downloaded successfully")
            return True
        else:
            print(f"    ❌ Download failed")
            return False
            
    except Exception as e:
        print(f"    ❌ Exception: {e}")
        return False


def extract_videos_from_json(json_file: str) -> List[Dict]:
    """Extract all videos from JSON data"""
    print(f"📖 Reading: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_videos = []
    
    for module in data.get('modules', []):
        module_title = module.get('title', 'Unknown')
        
        for unit in module.get('units', []):
            unit_title = unit.get('title', 'Unknown')
            videos = unit.get('content', {}).get('videos', [])
            
            for video in videos:
                video['module'] = module_title
                video['unit'] = unit_title
                all_videos.append(video)
    
    return all_videos


def main():
    print("""
╔════════════════════════════════════════════════╗
║         Video Downloader for Course            ║
╚════════════════════════════════════════════════╝
""")
    
    if not check_dependencies():
        return
    
    # Find JSON files
    output_dir = Path("output")
    json_files = list(output_dir.glob("sc200*.json"))
    
    if not json_files:
        print("❌ No JSON files found")
        return
    
    print("\n📋 Available files:")
    for idx, file in enumerate(json_files, 1):
        print(f"  {idx}. {file.name}")
    
    choice = input("\nSelect file (number): ").strip()
    
    try:
        idx = int(choice) - 1
        json_file = json_files[idx]
    except:
        print("❌ Invalid choice")
        return
    
    # Extract videos
    videos = extract_videos_from_json(json_file)
    
    print(f"\n📊 Found {len(videos)} videos")
    
    if not videos:
        print("❌ No videos to download")
        return
    
    # Group by type
    youtube_videos = [v for v in videos if v.get('type') == 'youtube']
    direct_videos = [v for v in videos if v.get('type') == 'direct']
    stream_videos = [v for v in videos if v.get('type') == 'microsoft_stream']
    
    print(f"  - YouTube: {len(youtube_videos)}")
    print(f"  - Direct: {len(direct_videos)}")
    print(f"  - Microsoft Stream: {len(stream_videos)}")
    
    if stream_videos:
        print("\n⚠️  Microsoft Stream videos require:")
        print("  - Logged in Microsoft account")
        print("  - Browser extension (Stream Video Downloader)")
    
    print("\n📥 Download options:")
    print("  1. Download YouTube videos only")
    print("  2. Download Direct videos only")
    print("  3. Download ALL (YouTube + Direct)")
    print("  4. Generate download script (for manual)")
    print("  0. Cancel")
    
    download_choice = input("\nYour choice: ").strip()
    
    # Create videos directory
    videos_dir = Path("videos")
    videos_dir.mkdir(exist_ok=True)
    
    if download_choice == "1":
        print(f"\n🎬 Downloading {len(youtube_videos)} YouTube videos...")
        for idx, video in enumerate(youtube_videos, 1):
            print(f"\n[{idx}/{len(youtube_videos)}]")
            download_youtube_video(
                video.get('watch_url', video.get('embed_url')),
                str(videos_dir),
                video.get('video_id', f'video_{idx}')
            )
    
    elif download_choice == "2":
        print(f"\n📹 Downloading {len(direct_videos)} Direct videos...")
        for idx, video in enumerate(direct_videos, 1):
            print(f"\n[{idx}/{len(direct_videos)}]")
            filename = f"direct_video_{idx}.mp4"
            download_direct_video(
                video.get('url'),
                str(videos_dir),
                filename
            )
    
    elif download_choice == "3":
        print(f"\n🎥 Downloading ALL videos...")
        
        # YouTube
        for idx, video in enumerate(youtube_videos, 1):
            print(f"\n[YouTube {idx}/{len(youtube_videos)}]")
            download_youtube_video(
                video.get('watch_url', video.get('embed_url')),
                str(videos_dir),
                video.get('video_id', f'video_{idx}')
            )
        
        # Direct
        for idx, video in enumerate(direct_videos, 1):
            print(f"\n[Direct {idx}/{len(direct_videos)}]")
            filename = f"direct_video_{idx}.mp4"
            download_direct_video(
                video.get('url'),
                str(videos_dir),
                filename
            )
    
    elif download_choice == "4":
        # Generate shell script
        script_file = videos_dir / "download_all.sh"
        
        with open(script_file, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated download script\n\n")
            
            # YouTube videos
            for idx, video in enumerate(youtube_videos, 1):
                url = video.get('watch_url', video.get('embed_url'))
                video_id = video.get('video_id', f'video_{idx}')
                f.write(f"# {video.get('module')} - {video.get('unit')}\n")
                f.write(f"yt-dlp -f best -o '{video_id}.%(ext)s' '{url}'\n\n")
            
            # Direct videos
            for idx, video in enumerate(direct_videos, 1):
                url = video.get('url')
                f.write(f"# {video.get('module')} - {video.get('unit')}\n")
                f.write(f"curl -L -o 'direct_video_{idx}.mp4' '{url}'\n\n")
        
        os.chmod(script_file, 0o755)
        print(f"\n✅ Download script created: {script_file}")
        print("Run with: ./videos/download_all.sh")
    
    else:
        print("❌ Cancelled")
    
    print("\n✅ Done!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled by user")
