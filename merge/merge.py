import os
from glob import glob
import subprocess
import shutil
from pydub import AudioSegment
import ffmpeg

def merge_wav(input_files, output_path, fade_frame=3, video_frame_rate=30):
    fade_time = 1000 * fade_frame / video_frame_rate
    audio = AudioSegment.from_wav(input_files[0])
    for i in range(1, len(input_files)):
        another = AudioSegment.from_wav(input_files[i])
        audio = audio.append(another, crossfade=fade_time)
    audio.export(output_path, format="wav")

def merge_mp4(input_files, output_path, fade_frame=3, video_frame_rate=30):
    inputs = [ffmpeg.input(file) for file in input_files]
    
    # 使用 concat 滤镜并重置时间戳
    video = ffmpeg.concat(*[i.video for i in inputs], v=1, a=0)
    audio = ffmpeg.concat(*[i.audio for i in inputs], v=0, a=1)

    (
        ffmpeg
        .output(video, audio, output_path)
        .run(overwrite_output=True)
    )



def merge(suffix='auto', fade_frame=3, video_frame_rate=30, to_mp3=False):
    pwd = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(pwd, 'input')
    output_path = os.path.join(pwd, 'output')
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if not os.path.exists(input_path):
        os.makedirs(input_path)
    input_files = os.listdir(input_path)
    if suffix == 'auto':
        if input_files[0].endswith('.wav'):
            suffix = 'wav'
        elif input_files[0].endswith('.mp4'):
            suffix = 'mp4'
        else:
            raise NotImplementedError
        
    input_files = [os.path.join(input_path, x) for x in input_files if x.endswith(suffix)]    
    output_path = os.path.join(output_path, 'output.'+suffix)

    if input_files == []:
        path = os.path.dirname(pwd)
        path = os.path.join(path, "result")
        for dir in os.listdir(path):
            files = [file for file in os.listdir(os.path.join(path, dir)) if file.endswith(suffix)]
            if len(files) > 1:
                files = [file for file in files if file.endswith("final."+suffix)]
            for file in files:
                shutil.copy(os.path.join(path, dir, file), os.path.join(pwd, "input"))
        input_files = [os.path.join(pwd, "input", x) for x in os.listdir(os.path.join(pwd, "input")) if x.endswith(suffix)]
    if suffix =='wav':
        merge_wav(input_files, output_path, fade_frame, video_frame_rate)
    elif suffix =='mp4':
        merge_mp4(input_files, output_path, fade_frame, video_frame_rate)
    else:
        raise NotImplementedError

def to_mp3():
    input_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", 'output.wav')
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output",'output.mp3')
    (
        ffmpeg
       .input(input_path)
       .output(output_path)
       .run(quiet=False)
    )   

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix', type=str, default='auto', help='suffix of input files, auto for auto detect')
    parser.add_argument('--fade_frame', type=int, default=3, help='number of frames for audio fade in/out')
    parser.add_argument('--video_frame_rate', type=int, default=30, help='frame rate of video')
    parser.add_argument('--to_mp3', action='store_true', default=False, help='convert output to mp3')
    parser = parser.parse_args()
    merge(**vars(parser))
    if parser.to_mp3:
        to_mp3()
