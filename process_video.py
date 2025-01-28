import re
import subprocess
import os
import sys

def parse_srt(srt_path):
    """
    Parses the SRT file and extracts start and end times.
    Returns a list of tuples: [(start1, end1), (start2, end2), ...]
    """
    with open(srt_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Regular expression to match time ranges
    pattern = re.compile(r'(\d{2}:\d{2}:\d{2}),(\d{3})\s-->\s(\d{2}:\d{2}:\d{2}),(\d{3})')
    matches = pattern.findall(content)

    # Remove the first segment if it's a placeholder (e.g., all zeros)
    if matches and matches[0][0] == '00' and matches[0][1] == '000':
        matches = matches[1:]

    time_ranges = []
    for match in matches:
        start_time = f"{match[0]}.{match[1]}"
        end_time = f"{match[2]}.{match[3]}"
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
        
        segments.append(segment_path)
    
    return segments

def create_concat_list(segments, concat_list_path):
    """
    Creates a concat list file required by FFmpeg for concatenation.
    """
    with open(concat_list_path, 'w', encoding='utf-8') as f:
        for segment in segments:
            # FFmpeg requires paths to be escaped if they contain special characters
            escaped_path = segment.replace("'", "'\\''")
            f.write(f"file '{escaped_path}'\n")
    print(f"Created concatenation list at {concat_list_path}")

def concatenate_segments(concat_list_path, final_video):
    """
    Concatenates video segments into a final video using FFmpeg.
    """
    print("Concatenating segments into final video...")
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        '-c', 'copy',
        final_video
    ]
    
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if result.returncode != 0:
        print(f"Error concatenating segments: {result.stderr.decode('utf-8')}")
        sys.exit(1)
    
    print(f"Final video created: {final_video}")

def main():
    # Configuration
    input_video = 'IMG_0106.mov'
    srt_file = '90 days in Japan without a plan.srt'
    segments_dir = 'segments'
    concat_list = 'concat_list.txt'
    final_video = 'final_video.mov'

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
    print(f"Extracted {len(segments)} segments.")

    # Step 3: Create concat list
    create_concat_list(segments, concat_list)

    # Step 4: Concatenate segments
    concatenate_segments(concat_list, final_video)

    print("All tasks completed successfully!")

if __name__ == "__main__":
    main()
