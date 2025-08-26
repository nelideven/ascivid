# ascivid
Simple video to ASCII renderer. Uses FFplay for audio.

## Dependencies
- Python 3.8+
- OpenCV for video decoding (```pip install opencv-python```)
- NumPy for fast pixel math (```pip install numpy```)
- FFmpeg (specifically ffplay) for audio playback

## Usage
```python ascivid.py <video_file> [options]```

## Options
```
  -h, --help         show this help message and exit
  -gui, --disp       Enable FFplay's GUI
  -i, --inverse      Invert brightness
  -nc, --no-color    Disable color
  -w, --width WIDTH  ASCII output width
  -bl, --blocks      Use solid block character for all pixels
  -pre, --prerender  Pre-render frames before playback
```

## Example
```python ascivid.py demo.mp4 -w 100 -bl -nc```<br>
This renders demo.mp4 at width 100 using block characters with no color.
