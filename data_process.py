import os
import ast
import time
import shutil
import json
from tqdm import tqdm
from pydub import AudioSegment
from moviepy import VideoFileClip
from moviepy import AudioFileClip
import cv2
import ffmpeg

audio_suffix = "30280"
split_str = "-"
fade_frame = 3 # acrossfade融合的帧数
max_gap = 2 # 防止恰好有一两帧名字没识别上

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
    
    ad = ffmpeg.input(audio_path)
    vd = ffmpeg.input(video_path)
    (
        ffmpeg.output
        (
            vd,
            ad,
            output_path,
            acodec="aac",
            vcodec="copy"
        )
        .run(quiet=True)
    )

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

def video_crop(
        input_path=None,
        output_path=None,
        rewrite=False,
        crop_size=None,
        target_word=None,
        num_threads="2"
):

    if not os.path.isfile(input_path):
        raise FileNotFoundError("输入文件{}不存在".format(input_path))
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
            print("输出文件{}已存在".format(output_path))
            return
    width, height, x1, y1 = map(int, crop_size.split(":"))
    (
        ffmpeg
        .input(input_path)
        .filter("crop", width, height, x1, y1)
        .output(output_path)
        .run(capture_stdout=True, capture_stderr=True)
    )
    return output_path

def video_crop_from_folder(
        input_path=None,
        output_path=None,
        rewrite=False,
        crop_size=None,
        target_word=None,
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
            video_crop(path_name, os.path.join(output_path, os.path.basename(path_name)), rewrite, crop_size, target_word, num_threads)
        elif os.path.isdir(path_name):
            video_crop_from_folder(path_name, os.path.join(output_path, os.path.basename(path_name)), rewrite, crop_size, target_word, num_threads)
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
    if not os.path.isdir(os.path.join(output_path, "images")):
        os.makedirs(os.path.join(output_path, "images"))
    if not os.path.isdir(os.path.join(output_path, "params")):
        os.makedirs(os.path.join(output_path, "params"))
    
    print("正在提取帧: ", input_path)
    
    cap = cv2.VideoCapture(input_path)
    frame_count = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    last_time = time.time()
    with tqdm(total=total_frames, desc="提取进度", position=0, leave=True, ncols=100) as pbar:
        while True:
            ret = cap.grab()
            if not ret:
                break
            frame_count += 1
            current_time = time.time()
            if current_time - last_time > 0.2:
                pbar.update(frame_count - pbar.n)
            if frame_count % frame_interval == 0:
                ret, frame = cap.retrieve()
                cv2.imwrite(os.path.join(os.path.join(output_path, "images"), f"{frame_count: 08d}.png"), frame)
        pbar.update(total_frames - pbar.n)
        cap.release()

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
            if found_index[i] <= current_end + max_gap:
                intervals[-1] = (current_start, found_index[i])
            else:
                intervals.append((found_index[i], found_index[i]))
        
        with open(interval_info, "w") as f:
            f.write(f"Intervals: {intervals}\n")
        return intervals

def get_audio_segment(audio_path, new_audio_path, intervals, video_frame_rate=30):
    if os.path.isfile(new_audio_path):
        print("音频{}已存在".format(new_audio_path))
        return

    fade_time = 1000*fade_frame / video_frame_rate
    input_files = []
    print("正在提取音频片段", audio_path)
    total_duration = fade_time / 1000
    for i, (start, end) in enumerate(intervals):
        duration = int((end - start + 1) * 1000 / video_frame_rate)
        start_time = int(start * 1000 / video_frame_rate)
        total_duration += duration - fade_time/1000

        output_segment = os.path.join(os.path.dirname(new_audio_path), f"segment_{i}.wav")
        input_files.append(output_segment)
        if not audio_path.endswith(".wav"):
            audio_path = audio_path + ".wav"
        
        audio = AudioSegment.from_file(audio_path, format="wav")
        cropped_audio: AudioSegment = audio[start_time: start_time + duration]
        cropped_audio.export(output_segment, format="wav")
    print("音频片段提取完成，总时长: {:.3f}秒".format(total_duration/1000))

    audio = AudioSegment.from_wav(input_files[0])
    for i in range(1, len(input_files)):
        another = AudioSegment.from_wav(input_files[i])
        if another.duration_seconds * 1000 < fade_time:
            continue
        audio = audio.append(another, crossfade=fade_time)
    audio.export(new_audio_path, format="wav")

    for i in range(len(intervals)):  
        os.remove(input_files[i])  

def refine_intervals(cropped_video_path, refined_interval_path, intervals, \
                      target_word, expand=10, parser=None):
    from models.ocr import EasyOCR
    reader = EasyOCR(parser)
    cap = cv2.VideoCapture(cropped_video_path)
    
    count = 0
    i_count = 0
    last_update_time = time.time()
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))


    print("--------------细化间隔--------------")
    
    with tqdm(total=total_frames, desc="处理进度", position=0, leave=True, ncols=100) as pbar:
        while (cap.isOpened()):
            current_time = time.time()
            if current_time - last_update_time > 0.2:
                last_update_time = current_time
                pbar.update(count - pbar.n)

            ret = cap.grab()
            if ret == True and i_count < len(intervals):
                count += 1
                start, end = intervals[i_count]
                if count >= start and count <= end:
                    continue
                if (count < start and count + expand >= start) or \
                        (count > end and count - expand <= end):
                    if i_count+1 < len(intervals) and count >= intervals[i_count+1][0]:
                        i_count += 1
                        continue
                    if i_count != 0 and count <= intervals[i_count-1][1]:
                        continue
                    ret, frame = cap.retrieve()
                    word = reader.readtext(frame, with_enhance=False)
                    flag = False
                    if word != []:
                        flag = any([reader.fuzzy_match(w, target_word) for w in word])
                    if not flag:
                        word = reader.readtext(frame, with_enhance=True)
                        if word != []:
                            flag = any([reader.fuzzy_match(w, target_word) for w in word])
                    if not flag:
                        continue
                    if count < start and count + expand >= start:
                        intervals[i_count] = (count, end)
                    elif count > end and count - expand <= end:
                        intervals[i_count] = (start, count)
                elif count > end:
                    i_count += 1
            else:
                break
        pbar.update(total_frames - pbar.n)
    cap.release()
    refined_intervals = []
    i = 0
    interval = intervals[i]
    for i in range(1, len(intervals)):
        if intervals[i][0] <= max_gap + interval[1]:
            interval = (min(interval[0], intervals[i][0]), max(interval[1], intervals[i][1]))
        else:
            refined_intervals.append(interval)
            interval = intervals[i]
    refined_intervals.append(interval)
    intervals = refined_intervals

    json.dump(intervals, open(refined_interval_path, "w"), indent=4)

def get_video_segment(video_path, new_video_path, intervals):
    import cv2

    if isinstance(video_path, str) and os.path.isfile(new_video_path):
        print("视频{}已存在".format(new_video_path))
        return

    cap = cv2.VideoCapture(video_path)
    fps_video = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    videoWriter = cv2.VideoWriter(new_video_path, fourcc, fps_video, (frame_width, frame_height))
    count = 0
    i_count = 0
    last_update_time = time.time()
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print("--------------生成视频--------------")
    with tqdm(total=total_frames, desc="处理进度", position=0, leave=True, ncols=100) as pbar:
        while (cap.isOpened()):
            ret = cap.grab()
            if ret == True and i_count < len(intervals):
                current_time = time.time()
                count += 1
                if current_time - last_update_time > 0.2:
                    last_update_time = current_time
                    pbar.update(count - pbar.n)
                start, end = intervals[i_count]
                if i_count != len(intervals)-1:
                    end -= fade_frame

                if count >= start and count <= end:
                    ret, frame = cap.retrieve()
                    videoWriter.write(frame)
                if count >= end:
                    i_count += 1
            else:
                break
        pbar.update(total_frames - pbar.n)
        
    videoWriter.release()
    cap.release()

def get_final_segment(input_path=None,  rewrite=False, expand=20, video_frame_rate=30, keep_audio=False, keep_video=False, language=['ch'], parser=None):

    if input_path is None:
        input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixedM4S_cropped_frames")

    entries = os.listdir(input_path)
    if "images" not in entries or "params" not in entries:
        for entry in entries:
            get_final_segment(os.path.join(input_path, entry), rewrite, expand, video_frame_rate, keep_audio, keep_video, language, parser)
    print(input_path)
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
        intervals[i] = (frame_rate*(start+1), frame_rate*(end+1))
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
            if entry.endswith(".wav"):
                audio_path = os.path.join(main_dir, entry.replace(".wav", ""))
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
        print("结果已存在")
        return

    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    
    new_audio_path = os.path.join(output_path, os.path.basename(audio_path)) + ".wav"
    new_video_path = os.path.join(output_path, os.path.basename(video_path)) + ".mp4"
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    print("生成最终片段 ", input_path)
    refined_interval_path = os.path.join(os.path.dirname(new_video_path), "refined_intervals.json")
    if os.path.isfile(refined_interval_path):
        print("已细化采样区间")
        intervals = json.load(open(refined_interval_path, "r"))
    elif parser.refine_intervals or parser.get_video_segment or parser.get_audio_segment:
        refine_intervals(cropped_video_path, refined_interval_path, \
                     intervals, target_word, expand=expand, parser=parser)
    if parser.get_video_segment:
        get_video_segment(video_path + ".mp4", new_video_path, intervals)
    if parser.get_audio_segment:
        get_audio_segment(audio_path, new_audio_path, intervals, video_frame_rate=video_frame_rate)
    if parser.merge_audio_video:
        print("--------------音视频合并--------------")
        merge_audio_video(new_audio_path, new_video_path, os.path.join(output_path, os.path.basename(main_dir) + "_final.mp4"), \
                        keep_audio=keep_audio, keep_video=keep_video)
    print("--------------完成----------------")

def clear(input_path=None):
    if input_path is None:
        input_path = os.path.dirname(os.path.abspath(__file__))

    path_list = ["data", "fixedM4S", "fixedM4S_cropped", "fixedM4S_cropped_frames", "merge/input", "ref/images", "ref/video"]
    for path_name in path_list:
        abs_path = os.path.join(input_path, path_name)
        if os.path.isdir(abs_path):
            print(f"Clearing {abs_path}")
            shutil.rmtree(abs_path)
    print("Done")
