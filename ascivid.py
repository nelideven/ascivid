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
import numpy as np
from multiprocessing import Process, Queue, cpu_count, Manager

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
            # char = "█" if args.blocks else ASCII_LUT[val]
            char = "#" if args.blocks else ASCII_LUT[val]  # Uncomment for something lighter for the blocks option (the full block is memory intensive)
            if args.no_color:
                ascii_str += char
            else:
                if args.inverse:
                    ascii_str += f"\033[38;2;{255 - r[y,x]};{255 - g[y,x]};{255 - b[y,x]}m{char}\033[0m"
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

            ret, frame = cap.read()
            if not ret:
                break

            ascii_str = render(frame)
            print("\033[H\033[J", end="") if os.name != 'nt' or confirmation.lower() == 'y' else ""
            print(ascii_str)

            current_frame += 1

        print("\033[H\033[J", end="") if os.name != 'nt' or confirmation.lower() == 'y' else ""

    except KeyboardInterrupt:
        print("\nInterrupted. Cleaning up...\n")

    finally:
        cap.release()

# Pre-rendering
def main_pre(file_path):
    manager = Manager()
    ascii_frames = manager.dict()
    if args.tempdir:
        if not os.path.exists(args.tempdir):
            os.makedirs(args.tempdir)
            print(f"Created temporary directory at {args.tempdir}")
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        print("Error: Could not open video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    start_time = time.time()
    frame_queue = Queue(maxsize=64)
    frame_index = 0

    workers = []

    def worker(frame_queue, ascii_frames, tempdir=None):
        try:
            while True:
                item = frame_queue.get()
                if item is None:
                    break
                index, frame = item
                ascii_save = render(frame)
                if tempdir:
                    with open(os.path.join(tempdir, f"frame_{index:06d}.txt"), "w", encoding="utf-8") as f:
                        f.write(ascii_save)
                else:
                    ascii_frames[index] = ascii_save
        except KeyboardInterrupt:
            print("Thread exiting due to user interruption.")

    try:
        print("Spawning renderers...")
        workers = [Process(target=worker, args=(frame_queue, ascii_frames, args.tempdir), daemon=True) for _ in range(cpu_count())]
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

        i = 0
        start_time = time.time()

        if args.tempdir:
            total_frames = len([f for f in os.listdir(args.tempdir) if f.startswith("frame_") and f.endswith(".txt")])
        else:
            total_frames = len(ascii_frames)

        while i < total_frames:
            elapsed = time.time() - start_time
            target_frame = int(elapsed * fps)

            if i < target_frame:
                i += 1
                continue
            
            if args.tempdir:
                with open(os.path.join(args.tempdir, f"frame_{i:06d}.txt"), "r", encoding="utf-8") as f:
                    ascii_str = f.read()
            else:
                ascii_str = ascii_frames[i]
            print("\033[H\033[J", end="") if os.name != 'nt' or confirmation.lower() == 'y' else ""
            print(ascii_str)

            expected = start_time + (i + 1) / fps
            sleep = expected - time.time()
            if sleep > 0:
                time.sleep(sleep)

            i += 1

        print("\033[H\033[J", end="") if os.name != 'nt' or confirmation.lower() == 'y' else ""

    except KeyboardInterrupt:
        print("\nInterrupted. Cleaning up...\n")
        for p in workers:
            if p.is_alive():
                p.terminate()
        cap.release()
    finally:
        time.sleep(0.25)
        if args.tempdir:
            shutil.rmtree(args.tempdir, ignore_errors=True)

# Entry point
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple video to ASCII renderer using OpenCV and FFplay for audio.")
    parser.add_argument("file", help="Path to the video file.")
    parser.add_argument("-gui", "--disp", action="store_true", help="Enable FFplay's GUI")
    parser.add_argument("-i", "--inverse", action="store_true", help="Invert brightness and color")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-nc", "--no-color", action="store_true", help="Disable color")
    group.add_argument("-bl", "--blocks", action="store_true", help="Use solid block character for all pixels")
    parser.add_argument("-w", "--width", type=int, default=80, help="ASCII output width")
    parser.add_argument("-pre", "--prerender", action="store_true", help="Pre-render frames before playback")
    parser.add_argument("-tmp", "--tempdir", type=str, default=None, help="Temporary directory for pre-rendering")
    args = parser.parse_args()

    ffplay_cmd = ["ffplay", "-autoexit", "-loglevel", "warning", args.file]
    if not args.disp:
        ffplay_cmd += ["-nodisp"]

    ASCII_CHARS = "@%#*+=-:. " if args.inverse else " .:-=+*#%@"
    ASCII_LUT = [ASCII_CHARS[i * (len(ASCII_CHARS) - 1) // 255] for i in range(256)]

    if os.name == 'nt':
        print("!! WARNING !!")
        print("You may be running windows, on an older Windows Command Host. Due to Command Host's limitations, color output WILL NOT WORK!!")
        print("Please consider using Windows Terminal.")
        confirmation = input("Do you want to continue using color? [y/N]: ")
        if confirmation.lower() != 'y':
            args.no_color = True

    if args.prerender:
        main_pre(args.file)
    else:
        main(args.file)