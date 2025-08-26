# ascivid
Simple video to ASCII renderer. Uses FFplay for audio.

## Dependencies
- Python 3.8+
- OpenCV for video decoding
- ```pip install opencv-python```
- NumPy for fast pixel math
- ```pip install numpy```
- FFmpeg (specifically ffplay) for audio playback

## Usage
```python ascivid.py <video_file> [options]```

Example
```python ascivid.py demo.mp4 -w 100 -bl -nc```
This renders demo.mp4 at width 100 using block characters with no color.
