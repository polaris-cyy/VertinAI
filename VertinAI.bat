:: 将bilibili的缓存视频全部移到data中
python run.py -m

:: 将.m4s格式转为
python run.py --fix

:: 默认1080p图片，Vertin名字附近，其它要自设参数。
python run.py --crop_video --crop_size=1080p

:: 提取帧
python run.py --extract_frames

:: 默认识别Vertin
python run.py -r --classify

:: 默认30帧
python run.py -r --get_audio_interval

:: 获得最终结果
python run.py -r --final_process --clear

pause
