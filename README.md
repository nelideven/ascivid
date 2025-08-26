# ascivid
Simple video to ASCII renderer. Uses FFplay for audio.

Dependencies
Python 3.8+
OpenCV for video decoding
```pip install opencv-python```
NumPy for fast pixel math
```pip install numpy```
FFmpeg (specifically ffplay) for audio playback

Install via package manager:
- Ubuntu/Debian: sudo apt install ffmpeg
- macOS (Homebrew): brew install ffmpeg
- Windows: Download from ffmpeg.org and add to PATH

Usage
```python ascivid.py <video_file> [options]```

Options
Flag
Description
-w <int>
Set ASCII output width (default: 80)
-nc
Disable ANSI color output
-bl
Use solid block character (█) for all pixels
-i
Invert brightness mapping
-gui
Enable FFplay's GUI window
-pre
Pre-render frames before playback (multiprocessing)

Example
```python ascivid.py demo.mp4 -w 100 -bl -nc```
This renders demo.mp4 at width 100 using block characters with no color.
