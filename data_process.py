import subprocess
import os
import glob
import ast
import time
import shutil

audio_suffix = "30280"
split_str = "-"


def move_data(cache_path, output_path=None):
    if not os.path.isdir(cache_path):
        raise FileNotFoundError("Input folder {} not found".format(cache_path))
    if output_path is None:
        output_path = os.path.abspath(__file__)
        output_path = os.path.join(os.path.dirname(output_path), "data")
        if not os.path.isdir(output_path):
            os.makedirs(output_path)

    print("Moving data from {} to {}".format(cache_path, output_path))
    for dir_path in os.listdir(cache_path):
        dir_path = os.path.join(cache_path, dir_path)
        if os.path.isdir(dir_path):
            shutil.move(dir_path, output_path)

def merge_audio_video(audio_path, video_path, output_path="output.mp4", keep_audio=False, keep_video=False):
    if not os.path.isfile(audio_path):
        raise FileNotFoundError("Audio file {} not found".format(audio_path))
    if not os.path.isfile(video_path):
        raise FileNotFoundError("Video file {} not found".format(video_path))
    print("Merging audio and video from {} and {} to {}".format(audio_path, video_path, output_path))
    cmd = [
        'ffmpeg',  
        "-loglevel", "quiet",
        '-i', video_path,    # 输入视频文件  
        '-i', audio_path,    # 输入音频文件  
        '-c:v', 'copy',      # 复制视频流，不进行转码  
        '-c:a', 'aac',       # 使用 AAC 编码音频  
        '-strict', 'experimental',  # 允许使用实验性的编解码器  
        output_path
    ]
    subprocess.run(cmd, Shell=True, check=True)

    if not keep_audio:
        os.remove(audio_path)
    if not keep_video:
        os.remove(video_path)

def merge_audio_video_from_folder(input_folder, output_folder=None, keep_audio=False, keep_video=False):
    if not os.path.isdir(input_folder):
        raise FileNotFoundError("Input folder {} not found".format(input_folder))
    if output_folder is None:
        output_folder = os.path.join(os.path.dirname(input_folder), "merged")
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    entries = os.listdir(input_folder)
    audio_path = []
    video_path = []
    for entry in entries:
        if os.path.isfile(os.path.join(input_folder, entry)):
            if audio_suffix in entry:
                audio_path.append(os.path.join(input_folder, entry))
            else:
                video_path.append(os.path.join(input_folder, entry))
        elif os.path.isdir(os.path.join(input_folder, entry)):
            merge_audio_video_from_folder(os.path.join(input_folder, entry), output_folder, keep_audio, keep_video)
    if len(audio_path) == 1 and len(video_path) == 1:
        merge_audio_video(
            audio_path[0], 
            video_path[0], 
            os.path.join(output_folder, os.path.basename(audio_path[0]).split(".")[0]) + ".mp4",
            keep_audio, 
            keep_video
        )
    else:
        print("More than one audio or video file found, skipping")
        

def video_compress(
        input_path,
        output_path=None,
        frame_rate="25",
        rewrite=False,
        high_quality=False,
        num_threads="2"
):
    if input_path is None:
        raise ValueError("Input path cannot be None")
    if not os.path.isfile(input_path):
        raise FileNotFoundError("Input file {} not found".format(input_path))
    if output_path is None:
        file_basename = os.path.basename(input_path)
        file_name, file_extension = os.path.splitext(file_basename)
        file_name = f"{file_name}_compressed{file_extension}"
        output_path = os.path.join(os.path.dirname(input_path), file_name)
    if os.path.exists(output_path):
        if rewrite:
            os.remove(output_path)
        else:
            return
    cmd = []
    if high_quality:
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-r", frame_rate,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "slow",
            "-loglevel", "quiet",
            "-threads", num_threads,
            output_path
        ]
    else:
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-r", frame_rate,
            "-loglevel", "quiet",
            "-threads", num_threads,
            output_path
        ]
    subprocess.run(cmd, shell=True)

def video_compress_from_folder(
        input_folder=None,
        output_folder = None,
        frame_rate = "25",
        rewrite = False,
        high_quality=False,
        num_threads="2"
):
    if input_folder is None:
        input_folder = os.path.join(os.getcwd(), "fixedM4S")
    print(input_folder)
    if not os.path.isdir(input_folder):
        raise FileNotFoundError("Input folder {} not found".format(input_folder))
    if output_folder is None:
        folder_name = os.path.dirname(input_folder)
        output_folder = os.path.join(folder_name, os.path.splitext(os.path.basename(input_folder))[0] + "_compressed")
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)
    for input_path in glob.glob(os.path.join(input_folder, "*.mp4")):
        output_path = os.path.join(output_folder, os.path.basename(input_path))
        video_compress(input_path, output_path, frame_rate, rewrite=rewrite, high_quality=high_quality, num_threads=num_threads)

def video_crop(
        input_path=None,
        output_path=None,
        rewrite=False,
        crop_size=None,
        num_threads="2"
):

    if not os.path.isfile(input_path):
        raise FileNotFoundError("Input file {} not found".format(input_path))
    if output_path is None:
        file_basename = os.path.basename(input_path)
        file_name, file_extension = os.path.splitext(file_basename)
        file_name = f"{file_name}_cropped{file_extension}"
        output_path = os.path.join(os.path.dirname(input_path), file_name)
    if os.path.isdir(output_path):
        output_path = os.path.join(output_path, os.path.basename(input_path))
    if os.path.exists(output_path):
        if rewrite:
            os.remove(output_path)
        else:
            print("Output file {} already exists, skipping".format(output_path))
            return
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", "format=gray",
        "-filter:v", "crop="+crop_size,
        "-threads", num_threads,
        "-loglevel", "quiet",
        output_path
    ]
    subprocess.run(cmd, shell=True)
    return output_path

def video_crop_from_folder(
        input_path=None,
        output_path=None,
        rewrite=False,
        crop_size=None,
        num_threads="2"
):
    if input_path is None:
        input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixedM4S")
    if not os.path.isdir(input_path):
        raise FileNotFoundError("Input folder {} not found".format(input_path))
    if output_path is None:
        output_path = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(output_path, "fixedM4S_cropped")
    if not os.path.isdir(output_path):
        os.makedirs(output_path)

    print("Cropping videos from {} to {}".format(input_path, output_path))
    for path_name in os.listdir(input_path):
        path_name = os.path.join(input_path, path_name)
        if os.path.isfile(path_name) and path_name.endswith(".mp4"):
            video_crop(path_name, os.path.join(output_path, os.path.basename(path_name)), rewrite, crop_size, num_threads)
        elif os.path.isdir(path_name):
            video_crop_from_folder(path_name, os.path.join(output_path, os.path.basename(path_name)), rewrite, crop_size, num_threads)
    return output_path

def extract_frames(
        input_path=None,
        output_path=None,
        frame_interval = 30,
        num_threads="2"
):
    if not os.path.isfile(input_path):
        raise FileNotFoundError("Input file {} not found".format(input_path))
    if output_path is None:
        filename = os.path.basename(input_path)
        filename = os.path.splitext(filename)[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{filename}_frames")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    os.makedirs(os.path.join(output_path, "images"))
    os.makedirs(os.path.join(output_path, "params"))
    
    print("Extracting frames from video ", input_path)
    cmd = [
        "ffmpeg", 
        "-i", input_path,
        '-vf', f'select=eq(mod(n\,{frame_interval})\, 0)',
        '-vsync', '0',
        "-loglevel", "quiet",
        "-threads", num_threads,
        os.path.join(os.path.join(output_path, "images"), r"_%06d.png")
    ]
    subprocess.run(cmd, shell=True)
    with open(os.path.join(os.path.join(output_path, "params"), "frame_info.txt"), "w") as f:
        f.write(f"Frame_interval: {frame_interval}\n")
    return frame_interval

def extract_frames_from_folder(
        input_folder=None,
        output_folder=None,
        frame_interval=30,
        num_threads="2"
):
    if input_folder is None:
        input_folder = os.path.join(os.getcwd(), "fixedM4S_cropped")
        if not os.path.isdir(input_folder):
           input_folder = os.path.join(os.getcwd(), "fixedM4S")
    if not os.path.isdir(input_folder):
        raise FileNotFoundError("Input folder {} not found".format(input_folder))
    
    if output_folder is None:
        output_folder = os.path.dirname(__file__)
        output_folder = os.path.join(output_folder, os.path.basename(input_folder) + "_frames")
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    print("Extracting frames from {} to {}".format(input_folder, output_folder))
    for path_name in os.listdir(input_folder):
        path_name = os.path.join(input_folder, path_name)
        if os.path.isfile(path_name) and path_name.endswith(".mp4"):
            extract_frames(path_name, output_folder, frame_interval, num_threads)
        elif os.path.isdir(path_name):
            extract_frames_from_folder(path_name, os.path.join(output_folder, os.path.basename(path_name)), frame_interval, num_threads)
    return frame_interval

def calculate_audio_interval(input_path=None,  rewrite=False):
    if input_path is None:
        input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixedM4S_cropped_frames")
    
    all_path = os.listdir(input_path)
    if "params" not in all_path or "images" not in all_path:
        for path_name in all_path:
            if os.path.isdir(os.path.join(input_path, path_name)):
                calculate_audio_interval(os.path.join(input_path, path_name), rewrite)
    else:
        print(f"Calculating audio interval for {input_path}")
        interval_info = os.path.join(os.path.join(input_path, "params"), "interval_info.txt")
        if os.path.isfile(interval_info) and not rewrite:
            return
        
        index_info = os.path.join(os.path.join(input_path, "params"), "index_info.txt")
        if not os.path.isfile(index_info):
            return
        found_index = []

        with open(index_info, "r") as f:
            for line in f:
                if "Found index" in line:
                    line = line.split(":")[1].strip()
                    found_index = ast.literal_eval(line)
        
        if found_index == []:
            with open(interval_info, "w") as f:
                f.write("Intervals: []\n")
            return []
        intervals = [(found_index[0], found_index[0])]
        for i in range(1, len(found_index)):
            current_start, current_end = intervals[-1]
            if found_index[i] == current_end + 1:
                intervals[-1] = (current_start, found_index[i])
            else:
                intervals.append((found_index[i], found_index[i]))
        
        with open(interval_info, "w") as f:
            f.write(f"Intervals: {intervals}\n")
        return intervals

def get_audio_segment(audio_path, new_audio_path, intervals, video_frame_rate=30):
    temp_list_file = "temp_files.txt"    
    print("Extracting audio segments from audio", audio_path)
    with open(temp_list_file, 'w') as f:  
        for i, (start, duration) in enumerate(intervals):  
            duration = int((duration - start + 1) * 1000 / video_frame_rate)
            start = int(start * 1000 / video_frame_rate)
            start_hour = start // 3600000
            start_min = (start % 3600000) // 60000
            start_sec = (start % 60000) // 1000
            start_mini = start % 1000
            start_time = f"{start_hour:02d}:{start_min:02d}:{start_sec:02d}.{start_mini:03d}"

            output_segment = f"segment_{i}.mp3"  
            subprocess.run([  
                'ffmpeg',  
                "-loglevel", "quiet",  
                '-i', audio_path + ".mp3",  
                '-ss', str(start_time),  
                '-t', str(duration) + "ms",  
                '-c', 'copy',  
                output_segment  
            ])  
            f.write(f"file '{output_segment}'\n")  

    subprocess.run([  
        'ffmpeg',  
        '-f', 'concat',  
        '-safe', '0',  
        '-i', temp_list_file,  
        '-c', 'copy',  
        new_audio_path  
    ])  
    for i in range(len(intervals)):  
        os.remove(f"segment_{i}.mp3")  
    os.remove(temp_list_file)  

def get_video_segment(video_path, cropped_video_path, new_video_path, intervals, \
                      target_word, expand=10, info_show=1000, language=["ch"]):
    import cv2
    from models.ocr import EasyOCR
    reader = EasyOCR(language=language)
    cap = cv2.VideoCapture(cropped_video_path)
    
    count = 0
    i_count = 0
    start_time = time.time()

    print("--------------Refining intervals--------------")
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True and i_count < len(intervals):
            if count % info_show == 0:
                print(f"Time: {time.time() - start_time}s")
                print(f"Frame: {count}, i_count: {i_count}")

            count += 1
            start, end = intervals[i_count]
            if count >= start and count <= end:
                continue
            else:
                if (count < start and count + expand >= start) or \
                        (count > end and count - expand <= end):
                    word = reader.readtext(frame)
                    flag = False
                    if word != []:
                        flag = any([reader.fuzzy_match(w, target_word) for w in word])
                    if count < start and count + expand >= start:
                        if flag:
                            intervals[i_count] = (count, end)
                    elif count > end and count - expand <= end:
                        if flag:
                            intervals[i_count] = (start, count)
                        else:
                            i_count += 1
                elif count > end:
                    i_count += 1
            # 截取相应时间内的视频信息
        else:
            break

    cap.release()
    cap = cv2.VideoCapture(video_path)
    fps_video = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    videoWriter = cv2.VideoWriter(new_video_path, fourcc, fps_video, (frame_width, frame_height))
    i_count = 0
    count = 0
    start_time = time.time()

    for i, (start, end) in enumerate(intervals):
        intervals[i] = (start+3, end-3)

    print("--------------Generating video--------------")
    while (cap.isOpened()):
        ret, frame = cap.read()
        if ret == True and i_count < len(intervals):
            if count % info_show == 0:
                print(f"Time: {time.time() - start_time}s")
                print(f"Count: {count}, i_count: {i_count}")
            start, end = intervals[i_count]
            if count >= start and count <= end:
                videoWriter.write(frame)
            if count >= end:
                i_count += 1
            count += 1
        else:
            break
    print(i_count, count)
    videoWriter.release()
    cap.release()

def get_final_segment(input_path=None,  rewrite=False, expand=20, video_frame_rate=30, keep_audio=False, keep_video=False, language=['ch']):

    if input_path is None:
        input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixedM4S_cropped_frames")

    entries = os.listdir(input_path)
    if "images" not in entries or "params" not in entries:
        for entry in entries:
            get_final_segment(os.path.join(input_path, entry), rewrite, expand, video_frame_rate, keep_audio, keep_video, language)
    
    param_path = os.path.join(input_path, "params")
    interval_info = os.path.join(param_path, "interval_info.txt")
    frame_info = os.path.join(param_path, "frame_info.txt")
    index_info = os.path.join(param_path, "index_info.txt")
    if not os.path.isfile(interval_info):
        return
    
    intervals = []
    frame_rate = 0
    target_word = ""
    with open(interval_info, "r") as f:
        for line in f:
            if "Intervals" in line:
                line = line.split(":")[1].strip()
                intervals = ast.literal_eval(line)

    with open(index_info, "r") as f:
        for line in f:
            if "Target word" in line:
                line = line.split(":")[1].strip()
                target_word = line
    
    with open(frame_info, "r") as f:
        for line in f:
            if "Frame_interval" in line:
                line = line.split(":")[1].strip()
                frame_rate = int(line)
    
    if intervals == []:
        return

    for i, (start, end) in enumerate(intervals):
        intervals[i] = (frame_rate*(start), frame_rate*(end))
    audio_path = None
    video_path = None
    output_path = None
    cropped_video_path = None
    if video_path == None:
        main_dir = os.path.abspath(__file__)
        main_dir = os.path.dirname(main_dir)
        cropped_video_path = os.path.join(main_dir, "fixedM4S_cropped")
        cropped_video_path = os.path.join(cropped_video_path, os.path.basename(input_path))
        main_dir = os.path.join(main_dir, "fixedM4S")
        main_dir = os.path.join(main_dir, os.path.basename(input_path))
        cropped_video_path = os.path.join(cropped_video_path, os.listdir(cropped_video_path)[0])
        entries = os.listdir(main_dir)
        for entry in entries:
            if entry.endswith(".mp3"):
                audio_path = os.path.join(main_dir, entry.replace(".mp3", ""))
            elif entry.endswith(".mp4"):
                video_path = os.path.join(main_dir, entry.replace(".mp4", ""))

    if output_path is None:
        output_path = os.path.abspath(__file__)
        output_path = os.path.dirname(output_path)
        output_path = os.path.join(output_path, "result")
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        output_path = os.path.join(output_path, os.path.basename(input_path))
    if os.path.isfile(os.path.join(output_path, os.path.basename(main_dir) + "_final.mp4")):
        print("Final segment already exists")
        return

    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    
    new_audio_path = os.path.join(output_path, os.path.basename(audio_path)) + ".mp3"
    new_video_path = os.path.join(output_path, os.path.basename(video_path)) + ".mp4"
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    print("Generating final segment for ", input_path)
    get_video_segment(video_path+".mp4", cropped_video_path, new_video_path, \
                      intervals, target_word, expand=expand, language=language)
    get_audio_segment(audio_path, new_audio_path, intervals, video_frame_rate=video_frame_rate)
    print("--------------Merging video and audio--------------")
    merge_audio_video(new_video_path, new_audio_path, os.path.join(output_path, os.path.basename(main_dir) + "_final.mp4"), \
                      keep_audio=keep_audio, keep_video=keep_video)
    print("--------------Done----------------")

def clear(input_path=None):
    if input_path is None:
        input_path = os.path.dirname(os.path.abspath(__file__))

    path_list = ["fixedM4S", "fixedM4S_cropped", "fixedM4S_cropped_frames"]
    for path_name in path_list:
        abs_path = os.path.join(input_path, path_name)
        if os.path.isdir(abs_path):
            print(f"Clearing {abs_path}")
            shutil.rmtree(abs_path)
    print("Done")
