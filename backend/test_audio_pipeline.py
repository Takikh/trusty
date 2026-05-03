"""
Test 2: Save the actual audio the browser sends, then run ffmpeg on it.
This script starts a minimal WebSocket server that:
1. Accepts a connection
2. Waits for binary audio data
3. Saves it to disk
4. Runs ffmpeg on it and shows the full output

Run: py -3.14 test_audio_pipeline.py
Then go to the browser and do ONE interview response.
"""
import asyncio
import websockets
import subprocess
import tempfile
import os
import imageio_ffmpeg
from faster_whisper import WhisperModel

SAVE_PATH = os.path.join(tempfile.gettempdir(), "browser_audio_test.webm")
WAV_PATH = SAVE_PATH + ".wav"

async def handler(websocket):
    print("Client connected. Send me audio binary data from the browser.", flush=True)
    async for message in websocket:
        if isinstance(message, bytes):
            print(f"\nReceived {len(message)} bytes", flush=True)
            
            # Save raw bytes
            with open(SAVE_PATH, 'wb') as f:
                f.write(message)
            print(f"Saved to: {SAVE_PATH}", flush=True)
            
            # Check file header
            with open(SAVE_PATH, 'rb') as f:
                header = f.read(16)
            print(f"File header (hex): {header.hex()}", flush=True)
            print(f"File header (ascii): {header}", flush=True)
            
            # Run ffmpeg with full stderr output
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            print(f"\n--- Running ffmpeg ---", flush=True)
            result = subprocess.run(
                [ffmpeg_exe, "-y", "-i", SAVE_PATH, "-vn", "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", WAV_PATH],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            print(f"Return code: {result.returncode}", flush=True)
            print("STDERR:", result.stderr.decode(errors='ignore'), flush=True)
            
            if result.returncode == 0:
                print(f"\nWAV created: {os.path.getsize(WAV_PATH)} bytes", flush=True)
                
                # Try whisper
                print("\n--- Running Whisper ---", flush=True)
                model = WhisperModel("base", device="cpu", compute_type="int8")
                segments, info = model.transcribe(WAV_PATH)
                texts = [s.text for s in segments]
                print(f"Transcription: {' '.join(texts)}", flush=True)
            else:
                print("\nffmpeg FAILED. Trying with pydub instead...", flush=True)
                try:
                    from pydub import AudioSegment
                    audio = AudioSegment.from_file(SAVE_PATH)
                    audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                    audio.export(WAV_PATH, format="wav")
                    print(f"pydub worked! WAV size: {os.path.getsize(WAV_PATH)}", flush=True)
                except Exception as e:
                    print(f"pydub also failed: {e}", flush=True)
            
            await websocket.send("DONE")
            break

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8002):
        print("Test server listening on ws://localhost:8002", flush=True)
        print("Open your browser console and run:", flush=True)
        print('  navigator.mediaDevices.getUserMedia({audio:true}).then(s=>{const mr=new MediaRecorder(s);const chunks=[];mr.ondataavailable=e=>chunks.push(e.data);mr.onstop=()=>{const ws=new WebSocket("ws://localhost:8002");ws.onopen=()=>ws.send(new Blob(chunks));};mr.start();setTimeout(()=>mr.stop(),5000);})', flush=True)
        await asyncio.sleep(120)

asyncio.run(main())
