# VertinAI

---

这是一个用于处理B站视频，识别特定角色名并裁剪相应片段的项目，功能如下：

- 将B站加密后的.m4s文件修复，并将.m4s文件转码为视频(.mp4)和音频(.mp3)
- 对视频进行裁剪，使其仅包含角色名部分(手动设置)
- 对视频按一定间隔采样，得到部分视频帧
- 识别含有角色名字的视频帧
- 根据得到的区间，对音视频进行裁剪，仅保留角色片段

CPU处理时间约为视频时长的一半

---

## Environment

基于以下环境，请自行配置:

```python
python 3.9.13
ffmpeg
---以下环境从第三步开始使用---
# paddleocr 安装方式 https://paddlepaddle.github.io/PaddleOCR/main/ppocr/installation.html#2-paddlepaddle-20
paddle
paddleocr

pip install -r requirements.txt --no-dependencies

```

## Structure

```
- VertinAI
|--- run.py # 主程序
|--- VertinAI.bat # 以默认参数运行
|--- fixM4S.py
|--- data_process.py
|--- models # 用于识别target_name, to be implemented
|  |--- ocr.py
|  |--- img_process.py # 用于图像增强
|  |--- ...
|--- data
|  |--- <file folder>
|     |--- <cached files>
|--- merge
|  |--- merge.py #运行此文件，合并input中的wav或mp4，生成文件位于output
|  |--- input
|  |--- output
|--- ref
|  |--- video
|  |--- images
|  |--- params
|--- result
|  |--- <file folder>
|     |--- xxx_fixed_final.mp4 #目标文件
|--- fixedM4S
|  |--- <file folder>
|     |--- xxx_fixed.wav
|     |--- xxx_fixed.mp4
|--- fixedM4S_cropped
|  |--- <file folder>
|     |--- xxx_fixed_cropped.mp4
|--- fixedM4S_cropped_frames
   |--- <file folder>
      |--- images
         |--- <_%06d.png>
      |--- params
         |--- interval_info.txt
         |--- frame_info.txt
         |--- index_info.txt
```



## Leverage

## Default setting

运行前，配置好python依赖环境，依次运行以下代码或VertinAI.bat：

- 重点！！！crop_size必须修改成角色名附近，输入格式为"宽度:高度:\x:y"，可以使用画图工具确定范围；target_word也要修改成对应的角色名

```bash
# 将bilibili的缓存视频全部移到data中
python run.py -m=true
# 将.m4s格式转为
python run.py --fix=true
# 默认自动识别图片，Vertin名字附近，其它要自设参数。
python run.py --crop_video=true --crop_size=auto --drop_score=0.5 --det_db_thresh=0.3 --det_db_unclip_ratio=1.5 --det_db_box_thresh=0.6 --ocr_enhance_list=["grayscale","enhance","sharpen"]
# 提取帧
python run.py --extract_frames=true
# 默认识别维尔汀，30帧视频
python run.py --classify=true
#获得最终结果
python run.py -fp=true --refine_intervals=true
python run.py -fp=true --get_video_segment=true
python run.py -fp=true --get_audio_segment=true
python run.py -fp=true --merge_audio_video=true

# <可选, 慎用!!!> 清除中间文件
python run.py --clear=true

# <可选> 按序合并result中的文件
python run.py --merge=true
```

- 运行完后，可将result文件夹中的输出放入./merge/input，运行merge.py，合成文件位于./merge/output

- 可以复制下面这个语句至cmd

  ```
  python run.py -m=true && python run.py --fix=true && python run.py --crop_video=true --crop_size=auto --drop_score=0.5 --det_db_thresh=0.3 --det_db_unclip_ratio=1.5 --det_db_box_thresh=0.6 --ocr_enhance_list=["grayscale","enhance","sharpen"] && python run.py --extract_frames=true && python run.py --classify=true && python run.py -fp=true --refine_intervals=true && python run.py -fp=true --get_video_segment=true && python run.py -fp=true --get_audio_segment=true && python run.py -fp=true --merge_audio_video=true
  ```

  

### Custom setting

使用自定义输入输出，在--help中查看，自行修改参数。考虑到OCR不太好用，小图像识别困难，可以微调或者进行数据增强。

代码中，可能有部分常量需要修改，如：

- 4K的后缀为30120，1080p的后缀为30080等；音频的后缀始终为30280。请使用ctrl+f自行修改。

- 不同分辨率/视频/人物需要对不同的位置进行crop，或者使用auto_crop

- video_frame_rate默认为30，请注意是否使用60帧视频进行处理

- 其余default_config.json中建议修改的自定义常量如下：

  ```python
  - 将target_word设为要识别的角色名
  
  对于crop_size
  - 如果人物出现时间较短, 建议找到相应片段，提取帧放入./ref/images
  - 如果人物出现次数较多, 可适当提高auto_crop_interval
  - 可以根据帧, 右键图片-编辑-画图工具, 得到角色名所在位置, crop_size格式为: 宽: 高: 左上x: 左上y
  
  对于高质量、背景不混乱的视频可改为
  - ocr_enhance可改为false
  - rec_algorithm可改为CRNN，
  - ocr_super_res可改为false
  - ocr参数如drop_score, det_db_thresh可更改
  
  对于相近的角色名，如37和77
  - 在invalid_char_list中加入错误的角色名
  - 在valid_char_list中加入正确的角色名，或可能角色名被错误识别成的名字，或是???这样的未知角色的名称
  
  对于有gpu的设备
  ```
- use_tensorrt设为true
  
  对于想保留纯音频/纯视频的
  - 将keep_audio/keep_video设为true
  ```
  
  
  ```

