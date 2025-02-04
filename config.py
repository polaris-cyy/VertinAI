import argparse
from pathlib import Path

class OptionParser():
    def __init__(self):
        self.parser = argparse.ArgumentParser()

        self.parser.add_argument('--file_operation', "-f", action='store_true', default=False, help="Whether to perform file operation or not.")
        self.parser.add_argument('--input_path', "-i", default = None, help="Path of the input file or directory.")
        self.parser.add_argument('--output_path', "-o", default = None,help="Path of the output file or directory.")
        self.parser.add_argument("--cache_path", "-c", default=r"C:\Users\86139\Videos\bilibili", help="Path of the cache directory.")
        self.parser.add_argument("--move_data", "-m", action='store_true', default=False, help="Whether to move data or not.")
        self.parser.add_argument("--num_threads", "-t", default="1", type=str, help="Number of threads to use for file operation.")

        self.parser.add_argument("--merge", action='store_true', default=False, help="Whether to merge videos or not.")

        self.parser.add_argument("--extract_frames", action='store_true', default=False, help="Whether to extract frames or not.")
        self.parser.add_argument("--rewrite", "-re", action='store_true', default=False, help="Whether to overwrite existing files or not.")
        self.parser.add_argument("--frame_interval", default=30, type=int, help="Frame interval for extracting frames.")

        self.parser.add_argument("--compress_video", action='store_true', default=False, help="Whether to compress videos or not.")
        self.parser.add_argument("--frame_rate", default="30", type=str, help="Frame rate for compressing videos.")
        self.parser.add_argument("--high_quality", action="store_true", default=False, help="Whether to use high quality or not.")

        self.parser.add_argument("--crop_video", action='store_true', default=False, help="Whether to crop videos or not.")
        self.parser.add_argument("--crop_size", type=str, default="1080p", help="Format: width:height:x:y, or 360p/480p/720p/1080p/4k. ")

        self.parser.add_argument("--fix", action='store_true', default=False, help="Whether to fix M4S files or not.")
        self.parser.add_argument("--buf_size", default=256*1024*1024, type=int, help="Buffer size for fixing M4S files.")

        self.parser.add_argument("--classify", action='store_true', default=False, help="Whether to recognize text or not.")
        self.parser.add_argument("--classifier", default="paddleocr", type=str, help="Name of the classifier to recognize text.")
        self.parser.add_argument("--match_threshold", default=0.7, type=float, help="Threshold for matching text.")
        self.parser.add_argument("--target_word", default="马库斯", type=str, help="Target word to search for in the text.")
        self.parser.add_argument("--language", default="ch", type=str, help="Language of the text to recognize.")

        self.parser.add_argument("--final_process", '-fp', action='store_true', default=False, help="Get the final video clip.")
        self.parser.add_argument("--video_frame_rate", default=30, type=int, help="Frame rate for input and output video.")
        self.parser.add_argument("--expand", default=20, type=int, help="Expansion amount for the final video clip.")
        self.parser.add_argument("--keep_audio", default=True, action="store_true", help="Whether to keep audio or not.")
        self.parser.add_argument("--keep_video", default=True, action="store_true", help="Whether to keep video or not.")

        self.parser.add_argument("--clear", default=False, action="store_true", help="Whether to clear cache or not.")

    def process_crop_size(self):
        crop_size = self.parser.crop_size
        special_input = ["4k", "1080p", "720p", "480p", "360p"]
        if crop_size in special_input:
            if crop_size == "4k":
                crop_size = "140:40:1300:1440"
            elif crop_size == '1080p':
                crop_size = "300:100:429:637"
            elif crop_size == "480p":
                crop_size = "32:13:291:320"
            else:
                pass
        else:
            crop_size = crop_size.split(":")
            if len(crop_size)!= 4:
                raise ValueError("Invalid crop size format.")
            crop_size = [int(x) for x in crop_size]
            for x in crop_size:
                if x < 0:
                    raise ValueError("Invalid crop size. Can't be negative.")
        self.parser.crop_size = crop_size

    def parse(self):
        self.parser = self.parser.parse_args()
        if self.parser.input_path is not None:
            self.parser.input_path = Path(self.parser.input_path).resolve().as_posix()
        if self.parser.output_path is not None:
            self.parser.output_path = Path(self.parser.output_path).resolve().as_posix()
        self.parser.file_operation = not self.parser.file_operation
        self.process_crop_size()
        if (self.parser.language) != list:
            self.parser.language = [self.parser.language]

        return self.parser
        
