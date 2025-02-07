import os
from glob import glob
import subprocess
import shutil

def merge_wav(input_files, output_path, fade_frame=3, video_frame_rate=30):
    filter_chains = []

    real_input_files = []
    for i in range(len(input_files)):
        real_input_files.append("-i")
        real_input_files.append(input_files[i])
        filter_chains.append(f"[{i}:a]")


    fade_time = fade_frame / video_frame_rate
    
    filter_complex = ""

    for i in range(1, len(filter_chains)):
        if i == 1:
            filter_complex += f"{filter_chains[0]}{filter_chains[1]}acrossfade=d={fade_time:.3f}"
        else:
            filter_complex += f"[a{i-1}]{filter_chains[i]}acrossfade=d={fade_time:.3f}"
        if i+1 == len(filter_chains):
            filter_complex += "[outa];"
        else:
            filter_complex += f"[a{i}];"
    filter_complex = filter_complex.rstrip(";")
    cmd = []
    if len(real_input_files) > 1:
        cmd = [  
            'ffmpeg',  
            *real_input_files,
            '-filter_complex', filter_complex,
            # '-loglevel', 'quiet',
            '-map', '[outa]',
            '-y',
            output_path
        ]
    else:
        cmd = [  
            'ffmpeg',  
            *real_input_files,
            '-loglevel', 'quiet',
            '-y',
            "-c", "copy",
            output_path
        ]
    subprocess.run(cmd, shell=True,check=True)  

def merge_mp4(input_files, output_path, fade_frame=3, video_frame_rate=30):
    file_list = "temp_file_list.txt"
    with open(file_list, "w") as f:
        for file in input_files:
            f.write("file '{}'\n".format(file))
    cmd = [
        'ffmpeg',
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', file_list,
        '-loglevel', 'quiet',
        '-c', 'copy',
        output_path
    ]
    subprocess.run(cmd, check=True)
    os.remove(file_list)


def merge(suffix='auto', fade_frame=3, video_frame_rate=30):
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
            files = [file for file in os.path.join(path, dir) if file.endswith(suffix)]
            if len(files) > 1:
                files = [file for file in files if file.endswith("final."+suffix)]
            for file in os.listdir(os.path.join(path, dir)):
                shutil.copy(os.path.join(path, dir, file), os.path.join(pwd, "input"))
        input_files = [os.path.join(pwd, "input", x) for x in os.listdir(os.path.join(pwd, "input")) if x.endswith(suffix)]

    if suffix =='wav':
        merge_wav(input_files, output_path, fade_frame, video_frame_rate)
    elif suffix =='mp4':
        merge_mp4(input_files, output_path, fade_frame, video_frame_rate)
    else:
        raise NotImplementedError


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--suffix', type=str, default='auto', help='suffix of input files, auto for auto detect')
    parser.add_argument('--fade_frame', type=int, default=3, help='number of frames for audio fade in/out')
    parser.add_argument('--video_frame_rate', type=int, default=30, help='frame rate of video')
    merge(**vars(parser.parse_args()))
