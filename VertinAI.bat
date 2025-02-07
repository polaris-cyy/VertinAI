:: 将bilibili的缓存视频全部移到data中
python run.py -m=true

:: 将.m4s格式转为
python run.py --fix=true

:: 默认自动识别图片，Vertin名字附近，其它要自设参数。
python run.py --crop_video=true --crop_size=auto --drop_score=0.5 --det_db_thresh=0.3 --det_db_unclip_ratio=1.5 --det_db_box_thresh=0.6 --ocr_enhance_list=["grayscale","enhance","sharpen"]

:: 提取帧
python run.py --extract_frames=true

:: 默认识别Vertin
python run.py --classify=true

:: 获得最终结果
python run.py -fp=true --refine_intervals=true
python run.py -fp=true --get_video_segment=true
python run.py -fp=true --get_audio_segment=true
python run.py -fp=true --merge_audio_video=true

pause
