# Keyword Detector for Video/Audio
1. Uses OpenAI Whisper to parse data
2. Generates JSON to use for search and video processing
3. Processes video based on matching keywords and outputs video fragments with matching keyword

## How to use
### This version is tailored for Japanese with pykakasi, but you can disable it and use it for any other language Whisper works with
0. Install Prerequisites
1. Put your files in InputAudio/InputVideo (or only video in InputVideo)
2. `python -m venv venv`
3. `venv\Scripts\activate`
4. `pip install -r requirements.txt`
3. `python Transcriptor.py`

## Prerequisites
1. Python 3.12
2. mkvtoolnix \
https://mkvtoolnix.download/ \
Edit System Variables -> path -> C:\Program Files\MKVToolNix (mkvextract.exe)
3. `cuda_12.6.3_561.17_windows` for GPU processing \
https://developer.nvidia.com/cuda-downloads \
Edit System Variables -> path -> C:\Program Files\NVIDIA Corporation\Nsight Compute 2024.3.2 \
Edit System Variables -> path -> C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\bin \
Edit System Variables -> path -> C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.6\libnvvp
4. ffmpeg (essentials is enough) \
https://www.gyan.dev/ffmpeg/builds/ \
Edit System Variables -> path -> C:\Program Files\FFmpeg\bin (or any other place you have decided to move it in) \
Choco also works if you prefer

## Note to Self
1. Pytorch proper DL Link generator https://pytorch.org/get-started/locally/#with-cuda-1 (included in venv, not required) \
`pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124`
2. `pip install git+https://github.com/openai/whisper.git` resolved issues I had with `pip install whisper`
3. Available languages https://github.com/openai/whisper/blob/main/whisper/tokenizer.py
4. Matroska audio extraction GUI (if needed) gMKVExtractGUI.exe 
http://forum.doom9.org/showthread.php?t=170249