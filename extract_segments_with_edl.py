import re
import subprocess
import os
import sys
from datetime import timedelta

def parse_srt(srt_path):
    """
    Parses the SRT file and extracts start and end times.
    Returns a list of tuples: [(start1, end1), (start2, end2), ...]
    """
    with open(srt_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expression to match time ranges
    pattern = re.compile(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s-->\s(\d{2}):(\d{2}):(\d{2}),(\d{3})')
    matches = pattern.findall(content)

    # Remove the first segment if it's a placeholder (e.g., all zeros)
    if matches and all(part == '00' for part in matches[0][:2]):
        matches = matches[1:]

    time_ranges = []
    for match in matches:
        start_time = f"{match[0]}:{match[1]}:{match[2]}.{match[3]}"
        end_time = f"{match[4]}:{match[5]}:{match[6]}.{match[7]}"
        time_ranges.append((start_time, end_time))
    
    return time_ranges

def extract_segments(input_video, time_ranges, segments_dir):
    """
    Extracts video segments based on the provided time ranges.
    Saves segments in the specified directory.
    Returns a list of segment file paths.
    """
    os.makedirs(segments_dir, exist_ok=True)
    segments = []

    for idx, (start, end) in enumerate(time_ranges, start=1):
        segment_filename = f"segment_{idx:03d}.mov"
        segment_path = os.path.join(segments_dir, segment_filename)
        print(f"Extracting Segment {idx}: {start} to {end}")
        
        # FFmpeg command to extract the segment
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output files without asking
            '-i', input_video,
            '-ss', start,
            '-to', end,
            '-c', 'copy',
            segment_path
        ]
        
        # Execute the command
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if result.returncode != 0:
            print(f"Error extracting segment {idx}: {result.stderr.decode('utf-8')}")
            sys.exit(1)
        
        segments.append({
            'filename': segment_filename,
            'start': start,
            'end': end
        })
    
    return segments

def format_time_for_edl(time_str):
    """
    Converts time from HH:MM:SS.mmm to HH:MM:SS:FF format for EDL.
    Assumes 30 frames per second (adjust if different).
    """
    parts = time_str.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds, millis = parts[2].split('.')
    seconds = int(seconds)
    millis = int(millis)
    total_seconds = hours * 3600 + minutes * 60 + seconds + millis / 1000.0
    frames = int((millis / 1000.0) * 30)  # Assuming 30 fps
    return f"{hours:02}:{minutes:02}:{seconds:02}:{frames:02}"

def generate_edl(segments, edl_path, original_video):
    """
    Generates an EDL file mapping segments to their original timeline.
    """
    with open(edl_path, 'w', encoding='utf-8') as f:
        f.write("TITLE: Extracted Segments EDL\n")
        f.write("FCM: NON-DROP FRAME\n\n")
        for idx, segment in enumerate(segments, start=1):
            event = f"{idx:03}  AX       V     C        {format_time_for_edl(segment['start'])} {format_time_for_edl(segment['end'])} {format_time_for_edl(segment['start'])} {format_time_for_edl(segment['end'])}\n"
            f.write(event)
    print(f"EDL file created at {edl_path}")

def main():
    # Configuration
    input_video = 'IMG_0106.mov'
    srt_file = '90 days in Japan without a plan.srt'
    segments_dir = 'segments'
    edl_file = 'segments.edl'
    final_video = 'final_video.mov'  # Optional: Not creating a final video in this script

    # Check if input files exist
    if not os.path.isfile(input_video):
        print(f"Input video file '{input_video}' not found.")
        sys.exit(1)
    
    if not os.path.isfile(srt_file):
        print(f"SRT file '{srt_file}' not found.")
        sys.exit(1)
    
    # Step 1: Parse the SRT file
    print("Parsing SRT file...")
    time_ranges = parse_srt(srt_file)
    print(f"Found {len(time_ranges)} segments to extract.")

    if not time_ranges:
        print("No valid time ranges found in the SRT file.")
        sys.exit(1)
    
    # Step 2: Extract video segments
    segments = extract_segments(input_video, time_ranges, segments_dir)
    print(f"Extracted {len(segments)} segments successfully.")
    print(f"All segments are saved in the '{segments_dir}' directory.")

    # Step 3: Generate EDL file
    generate_edl(segments, edl_file, input_video)

    print("All tasks completed successfully!")
    print("You can now import both the extracted segments and the original video into your editing software.")
    print("Use the EDL file to map the segments to their original positions if your software supports EDL imports.")

if __name__ == "__main__":
    main()
