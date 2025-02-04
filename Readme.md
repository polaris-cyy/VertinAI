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
|  |--- ...
|--- data
|  |--- <file folder>
|     |--- <cached files>
|---merge
|  |--- merge.py #运行此文件，合并input中的mp3或mp4，生成文件位于output
|  |--- input
|  |--- output
|
|--- result
|  |--- <file folder>
|     |--- xxx_fixed_final.mp4 #目标文件
|--- fixedM4S
|  |--- <file folder>
|     |--- xxx_fixed.mp3
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

```bash
# 将bilibili的缓存视频全部移到data中
python run.py -m
# 将.m4s格式转为
python run.py --fix
# 默认1080p图片，Vertin名字附近，其它要自设参数。
python run.py --crop_video --crop_size=1080p
# 提取帧
python run.py --extract_frames
# 默认识别维尔汀，30帧视频
python run.py --classify
#获得最终结果
python run.py --final_process

# <可选> 清除中间文件
python run.py --clear
```

- 运行完后，可将result文件夹中的输出放入./merge/input，运行merge.py，合成文件位于./merge/output

### Custom setting

使用自定义输入输出，在--help中查看，自行修改参数。考虑到OCR不太好用，小图像识别困难，可以微调或者进行数据增强。

代码中，可能有部分常量需要修改，如：

- 4K的后缀为30120，1080p的后缀为30080等；音频的后缀始终为30280。请使用ctrl+f自行修改。
- 不同分辨率/视频/人物需要对不同的位置进行crop
- video_frame_rate默认为30，请注意是否使用60帧视频进行处理

