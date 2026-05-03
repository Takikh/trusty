"""
Test script to diagnose ffmpeg/whisper pipeline.
Run: py -3.14 test_ffmpeg.py
"""
import subprocess
import tempfile
import os
import urllib.request
import imageio_ffmpeg

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
print(f"FFmpeg path: {ffmpeg_exe}")

# Download a real webm audio sample to test with
test_url = "https://www.learningcontainer.com/wp-content/uploads/2020/02/Kalimba.webm"
webm_path = os.path.join(tempfile.gettempdir(), "test_audio.webm")
wav_path = webm_path + ".wav"

print(f"Downloading test WebM...")
try:
    urllib.request.urlretrieve(test_url, webm_path)
    print(f"Downloaded: {os.path.getsize(webm_path)} bytes")
except Exception as e:
    print(f"Download failed: {e}")
    # Try probing our own dummy file
    with open(webm_path, 'wb') as f:
        f.write(b'\x1a\x45\xdf\xa3' + b'\x00' * 100)  # fake webm header

# Step 1: Probe the file to see what streams are inside
print("\n--- FFPROBE INFO ---")
result = subprocess.run(
    [ffmpeg_exe, "-i", webm_path],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
print(result.stderr.decode(errors='ignore'))

# Step 2: Try conversion with -vn
print("\n--- CONVERTING with -vn ---")
result = subprocess.run(
    [ffmpeg_exe, "-y", "-i", webm_path, "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE
)
print(f"Return code: {result.returncode}")
print(result.stderr.decode(errors='ignore')[-2000:])

if result.returncode == 0:
    print(f"\nSuccess! WAV size: {os.path.getsize(wav_path)} bytes")
    # Try whisper
    print("\n--- TESTING WHISPER ---")
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(wav_path)
    print(f"Detected language: {info.language}")
    for seg in segments:
        print(f"  Segment: {seg.text}")
else:
    print("\nConversion FAILED. Trying without -vn...")
    result2 = subprocess.run(
        [ffmpeg_exe, "-y", "-i", webm_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    print(f"Return code (no -vn): {result2.returncode}")
    print(result2.stderr.decode(errors='ignore')[-2000:])

# Cleanup
for p in [webm_path, wav_path]:
    if os.path.exists(p):
        os.unlink(p)

print("\nDone.")
