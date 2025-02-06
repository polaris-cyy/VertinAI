:: 将bilibili的缓存视频全部移到data中
python run.py -m=true

:: 将.m4s格式转为
python run.py --fix=true

:: 默认自动识别图片，Vertin名字附近，其它要自设参数。
python run.py --crop_video=true --crop_size=auto --target_word=马库斯

:: 提取帧
python run.py --extract_frames=true

:: 默认识别Vertin
python run.py --classify=true --target_word="马库斯"

:: 获得最终结果
python run.py --final_process=true

pause
