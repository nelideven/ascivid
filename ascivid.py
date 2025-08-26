'''
ascivid - Simple video to ASCII renderer using OpenCV and FFplay for audio.
This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
    
import cv2
import argparse
import subprocess
import os
import time
import shutil
import tempfile
import numpy as np

ASCII_CHARS = None
args = None

# ASCII conversion
def render(frame):
    h, w = frame.shape[:2]
    new_h = int(args.width * (h / w) * 0.5)
    frame = cv2.resize(frame, (args.width, new_h))

    r, g, b = frame[:, :, 2], frame[:, :, 1], frame[:, :, 0]
    brightness = (0.299 * r + 0.587 * g + 0.114 * b).astype(np.uint8)

    ascii_str = ""
    for y in range(new_h):
        for x in range(args.width):
            val = brightness[y, x]
            char = "█" if args.blocks else ASCII_LUT[val]
            if args.no_color:
                ascii_str += char
            else:
                ascii_str += f"\033[38;2;{r[y,x]};{g[y,x]};{b[y,x]}m{char}\033[0m"
        ascii_str += "\n"
    return ascii_str

# Live rendering
def main(file_path):
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    subprocess.Popen(ffplay_cmd)
    time.sleep(0.15)

    start_time = time.time()
    current_frame = 0

    try:
        while True:
            # Calculate how many frames should have been shown by now
            elapsed = time.time() - start_time
            target_frame = int(elapsed * fps)

            # Skip frames if we're behind
            while current_frame < target_frame:
                ret, frame = cap.read()
                if not ret:
                    break
                current_frame += 1

            if current_frame != target_frame:
                continue  # Still catching up

            ret, frame = cap.read()
            if not ret:
                break

            ascii_str = render(frame)
            print("\033[H\033[J", end="")
            print(ascii_str)

            current_frame += 1

        print("\033[H\033[J", end="")

    except KeyboardInterrupt:
        print("\033[H\033[JInterrupted. Cleaning up...\n")

    finally:
        cap.release()

# Pre-rendering
def main_pre(file_path):
    from multiprocessing import Process, Queue, cpu_count
    temp_dir = tempfile.mkdtemp(prefix="ascii_frames_")
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_queue = Queue(maxsize=64)
    frame_index = 0

    workers = []

    def worker(frame_queue, temp_dir):
        while True:
            item = frame_queue.get()
            if item is None:
                break
            index, frame = item
            ascii_str = render(frame)
            with open(os.path.join(temp_dir, f"{index:06}.txt"), "w") as f:
                f.write(ascii_str)

    try:
        print("Spawning renderers...")
        workers = [Process(target=worker, args=(frame_queue, temp_dir)) for _ in range(cpu_count())]
        for p in workers:
            p.start()

        print("Decoding frames...")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_queue.put((frame_index, frame))
            frame_index += 1

        for _ in workers:
            frame_queue.put(None)

        cap.release()

        print("Playback starting...\n")
        subprocess.Popen(ffplay_cmd)
        time.sleep(0.15)

        start_time = time.time()
        for i in range(frame_index):
            with open(os.path.join(temp_dir, f"{i:06}.txt")) as f:
                print("\033[H\033[J", end="")
                print(f.read())
            expected = start_time + (i + 1) / fps
            sleep = expected - time.time()
            if sleep > 0:
                time.sleep(sleep)

        print("\033[H\033[J", end="")

    except KeyboardInterrupt:
        print("\033[H\033[JInterrupted. Cleaning up...\n")
        for p in workers:
            if p.is_alive():
                p.terminate()
        cap.release()

    finally:
        time.sleep(1)
        shutil.rmtree(temp_dir)

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple video to ASCII renderer using OpenCV and FFplay for audio.")
    parser.add_argument("file", help="Path to the video file.")
    parser.add_argument("-gui", "--disp", action="store_true", help="Enable FFplay's GUI")
    parser.add_argument("-i", "--inverse", action="store_true", help="Invert brightness")
    parser.add_argument("-nc", "--no-color", action="store_true", help="Disable color")
    parser.add_argument("-w", "--width", type=int, default=80, help="ASCII output width")
    parser.add_argument("-bl", "--blocks", action="store_true", help="Use solid block character for all pixels")
    parser.add_argument("-pre", "--prerender", action="store_true", help="Pre-render frames before playback")
    args = parser.parse_args()

    ffplay_cmd = ["ffplay", "-autoexit", "-loglevel", "warning", args.file]
    if not args.disp:
        ffplay_cmd += ["-nodisp"]

    ASCII_CHARS = "@%#*+=-:. " if args.inverse else " .:-=+*#%@"
    ASCII_LUT = [ASCII_CHARS[i * (len(ASCII_CHARS) - 1) // 255] for i in range(256)]

    if args.prerender:
        main_pre(args.file)
    else:
        main(args.file)