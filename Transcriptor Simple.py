import os  # For file and folder management
import re  # For regular expressions to match patterns in filenames
import json  # For saving transcription data to JSON
import subprocess  # For running FFmpeg commands
from datetime import timedelta  # For formatting timestamps
import whisper  # For audio transcription using the Whisper model
import torch  # To determine if GPU (CUDA) is available and use GPU for rendering

# Load the Whisper model
model = whisper.load_model("large", device="cuda" if torch.cuda.is_available() else "cpu")

# Function to format timestamps to HH:MM:SS
def format_timestamp(seconds):
    seconds = float(seconds)
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02}:{minutes:02}:{seconds:02}"

# Function to find the corresponding video file
def find_video_file(video_folder, episode_number):
    for video_file in os.listdir(video_folder):
        if re.search(fr"{episode_number}", video_file):
            return os.path.join(video_folder, video_file)
    return None

# Extract video fragments matching specific words in the JSON
def extract_fragments_with_word(video_file, result, output_folder, word_to_search, base_name):
    for idx, segment in enumerate(result['segments'], start=1):
        if word_to_search in segment['text']:  # Check if the specific word is in the text
            # start_time = format_timestamp(segment['start'])
            # end_time = format_timestamp(segment['end'])
            start_time = segment['start']
            end_time = segment['end']
            fragment_name = f"{base_name}_segment{idx}_{word_to_search}.mp4"
            fragment_path = os.path.join(output_folder, fragment_name)
            extract_video_fragment(video_file, start_time, end_time, fragment_path)
            print(f"Extracted fragment: {fragment_path}")

# Function to extract video fragments using FFMPEG LOGS
def extract_video_fragment(video_path, start_time, end_time, output_path):
    command = [
        "ffmpeg", "-y",  # Overwrite output if exists
        "-i", video_path,
        "-ss", start_time,  # Start time
        "-to", end_time,    # End time
        # "-c", "copy",       # Copy codec (faster processing, BUT MAY END UP CORRUPTING IMAGERY AT THE BEGINNING AND THE END)
        "-c:v", "libx264", #reencode video
        # "-c:a", "aac", #reencode audio (if needed)
        output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # FFMPEG LOGS
    print("FFmpeg Output:", result.stdout.decode())
    print("FFmpeg Error:", result.stderr.decode())

# Function to process an audio file and extract fragments matching a specific word
def process_audio_and_video(audio_path, video_folder, output_folder, word_to_search):
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

    # Save the transcription to a JSON file
    json_path = os.path.join(output_folder, f"{base_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        for segment in result['segments']:
            segment['start'] = format_timestamp(segment['start'])
            segment['end'] = format_timestamp(segment['end'])
        json.dump(result['segments'], f, ensure_ascii=False, indent=2)
    print(f"Transcription saved to {json_path}")

    # Extract video fragments matching the specific word
    extract_fragments_with_word(video_file, result, output_folder, word_to_search, base_name)


# Process all audio files and their corresponding video files
def process_folder(audio_folder, video_folder, output_folder):
    for file_name in os.listdir(audio_folder):
        if file_name.endswith(('.aac', '.mp3', '.wav')):
            audio_path = os.path.join(audio_folder, file_name)
            process_audio_and_video(audio_path, video_folder, output_folder)

# Paths and word to search
audio_folder = "InputAudio"
video_folder = "InputVideo"
output_folder = "Output"
word_to_search = "keyword"  # Replace with the word you want to match

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# Process all audio files
for file_name in os.listdir(audio_folder):
    if file_name.endswith(('.aac', '.mp3', '.wav')):
        audio_path = os.path.join(audio_folder, file_name)
        process_audio_and_video(audio_path, video_folder, output_folder, word_to_search)

