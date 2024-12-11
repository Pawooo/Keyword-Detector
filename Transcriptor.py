import os  # For file and folder management
import re  # For regular expressions to match patterns in filenames
import json  # For saving transcription data to JSON
import subprocess  # For running FFmpeg and MKV extraction commands
from datetime import timedelta  # For formatting timestamps
import whisper  # For audio transcription using the Whisper model
import torch  # To determine if GPU (CUDA) is available and to use CUDA cores
import pykakasi  # For Japanese-to-Romaji conversion

# Initialize pykakasi for Japanese to Romaji conversion
kks = pykakasi.kakasi()

# Load the Whisper model
model = whisper.load_model("large", device="cuda" if torch.cuda.is_available() else "cpu")

# Format timestamps to HH:MM:SS
def format_timestamp(seconds):
    seconds = float(seconds)
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}h{minutes:02}m{seconds:02}s"


# Convert Japanese text to Romaji
def japanese_to_romaji(japanese_text):
    result = kks.convert(japanese_text)
    # return ''.join([item['hepburn'] for item in result]) # No Spacing, spacing for search is not relevant as it comes like 'bokuhaomoshiroi'
    return ' '.join([item['hepburn'] for item in result])

# Search for matching segments by keywords
def search_segments(segments, keywords):
    matching_segments = []
    for segment in segments:
        text = segment['text']
        romaji = japanese_to_romaji(text)
        segment['romaji'] = romaji # Modify JSON to include romaji field (but it's not saved here)
        
        # Check for keyword matches in Japanese or Romaji
        if any(keyword in text or keyword in romaji for keyword in keywords):
            matching_segments.append(segment)
    return matching_segments

# Find the corresponding video file
def find_video_file(video_folder, episode_number):
    for video_file in os.listdir(video_folder):
        if re.search(fr"{episode_number}", video_file):
            return os.path.join(video_folder, video_file)
    return None


# Extract video fragments matching specific keywords
def extract_fragments_with_keywords(video_file, segments, output_folder, keywords, base_name):
    for idx, segment in enumerate(search_segments(segments, keywords), start=1):
        start_time = segment['start'] - 2
        end_time = segment['end'] + 2
        start_time = max(start_time, 0) # Ensure start time is not negative
        start_hhmmss = format_timestamp(start_time)
        fragment_name = f"{base_name}_segment{idx}_{start_hhmmss}.mp4"
        fragment_path = os.path.join(output_folder, fragment_name)
        extract_video_fragment(video_file, start_time, end_time, fragment_path)
        print(f"Extracted fragment: {fragment_path}")


# Extract video fragments using FFMPEG
def extract_video_fragment(video_path, start_time, end_time, output_path):
    command = [
        "ffmpeg", "-y",  # Overwrite output if exists
        "-i", video_path,
        "-ss", str(start_time),  # Start time
        "-to", str(end_time),    # End time
        # "-c", "copy",       # Copy codec (faster processing, BUT MAY END UP CORRUPTING IMAGERY AT THE BEGINNING AND THE END)
        "-c:v", "libx264",  # Reencode video
        # "-c:a", "aac", #reencode audio (if needed)
        output_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # FFMPEG LOGS
    print("FFMPEG Output:", result.stdout.decode())
    print("FFMPEG Error:", result.stderr.decode())


# Extract audio tracks from MKV files
def extract_aac_from_mkv(mkv_folder, audio_folder):
    os.makedirs(audio_folder, exist_ok=True)
    for file in os.listdir(mkv_folder):
        if file.endswith(".mkv"):
            mkv_path = os.path.join(mkv_folder, file)
            output_path = os.path.join(audio_folder, os.path.splitext(file)[0] + ".aac")
            command = ["mkvextract", "tracks", mkv_path, f"1:{output_path}"]
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(f"Extracted {output_path}")


# Process an audio file and extract fragments matching keywords
def process_audio_and_video(audio_path, video_folder, json_folder, mp4_folder, keywords):
    # Transcribe the audio
    result = model.transcribe(audio_path, language="ja")
    
    # Extract base name and episode number
    file_name = os.path.basename(audio_path)
    match = re.search(r"(Naruto Shippuden - (\d+))", file_name)
    if not match:
        print(f"Skipping {file_name}: Could not extract episode number.")
        return
    base_name, episode_number = match.groups()
    
    # Find corresponding video file
    video_file = find_video_file(video_folder, episode_number)
    if not video_file:
        print(f"Video file not found for {base_name}. Skipping video extraction.")
        return

    print(f"Found video file: {video_file} for {base_name}")

    # Add Romaji to each segment and save the transcription to a JSON file
    for segment in result['segments']:
        segment['romaji'] = japanese_to_romaji(segment['text'])

    json_path = os.path.join(json_folder, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result['segments'], f, ensure_ascii=False, indent=2)
    print(f"Transcription saved to {json_path}")

    # Extract video fragments matching the keywords
    extract_fragments_with_keywords(video_file, result['segments'], mp4_folder, keywords, base_name)


# Process all audio files and their corresponding video files
def process_folder(audio_folder, video_folder, json_folder, mp4_folder, keywords):
    for file_name in os.listdir(audio_folder):
        if file_name.endswith(('.aac', '.mp3', '.wav', '.flac')):
            audio_path = os.path.join(audio_folder, file_name)
            process_audio_and_video(audio_path, video_folder, json_folder, mp4_folder, keywords)


# Paths and keywords
audio_folder = "InputAudio"
video_folder = "InputVideo"
output_folder = "Output"
json_folder = os.path.join(output_folder, "json")
mp4_folder = os.path.join(output_folder, "mp4")
os.makedirs(json_folder, exist_ok=True)
os.makedirs(mp4_folder, exist_ok=True)

keywords = ["keyword"]  # Replace with desired keywords (in Japanese Kanji or Romaji)

# Extract AAC files from MKV (if needed)
extract_aac_from_mkv(video_folder, audio_folder)

# Process all audio and video files
process_folder(audio_folder, video_folder, json_folder, mp4_folder, keywords)
