import argparse
from pathlib import Path
import os, json

class OptionParser():
    def __init__(self):
        self.parser = argparse.ArgumentParser()
        self.default_config = json.load(open(os.path.join(os.path.dirname(__file__), "default_config.json"), "r"))  
        self.parser.add_argument('--folder_operation', "-f", type=bool, help="Whether to perform file operation or not.")
        self.parser.add_argument('--input_path', "-i", help="输入路径.")
        self.parser.add_argument('--output_path', "-o",help="输出路径.")
        self.parser.add_argument("--cache_path", "-c", help="bilibili缓存路径.")
        self.parser.add_argument("--move_data", "-m", type=bool, help="移动bilibili缓存视频到data文件夹.")
        self.parser.add_argument("--num_threads", "-t", type=str, help="多线程加速.")

        self.parser.add_argument("--merge", type=bool, help="合并merge文件夹中的文件.")

        self.parser.add_argument("--extract_frames", type=bool, help="提取视频帧.")
        self.parser.add_argument("--rewrite", "-re", type=bool, help="覆盖已存在的文件.")
        self.parser.add_argument("--frame_interval", type=int, help="抽帧间隔.")

        self.parser.add_argument("--compress_video", type=bool, help="是否压缩视频帧率.")
        self.parser.add_argument("--frame_rate", type=str, help="目标帧率.")
        self.parser.add_argument("--high_quality", type=bool, help="压缩视频质量.")

        self.parser.add_argument("--crop_video", type=bool, help="是否裁剪视频.")
        self.parser.add_argument("--crop_size", type=str, help="裁剪尺寸. auto为自适应尺寸. 格式为'width:height:x:y', 如'1280:720:0:0'表示裁剪为1280x720的图像,并从原图的左上角(0,0)开始裁剪.")

        self.parser.add_argument("--fix", type=bool, help="将b站缓存视频转为wav和mp4.")
        self.parser.add_argument("--buf_size", type=int, help="缓存池大小.")

        # 一些ocr参数
        self.parser.add_argument("--classify", type=bool, help="视频角色名识别.")
        self.parser.add_argument("--classifier", type=str, help="选用ocr, 目前只有paddleocr.")
        self.parser.add_argument("--match_threshold", type=float, help="模糊匹配阈值.")
        self.parser.add_argument("--target_word", type=str, help="角色名.")
        self.parser.add_argument("--language", type=str, help="识别模型语言.")
        self.parser.add_argument("--auto_crop_interval", type=int, help="自动裁剪帧间隔, 单位为秒.")
        self.parser.add_argument("--ocr_enhance_list", type=list, help="图像增强选项, 目前支持[binary, grayscale, sharpen, enhance, enlarge,\n\
                                 super_resolution, laplacian_sharpen, high_boost_sharpen, dilate, erode\n].")
        self.parser.add_argument("--rec_algorithm", type=str, choices=["CRNN", "SVTR_LCNet"], help="使用识别低质量文本的参数")
        self.parser.add_argument("--rec_batch_num", type=int, help="ocr批大小")
        self.parser.add_argument("--drop_score", type=float, help="")
        self.parser.add_argument("--det_db_thresh", type=float, help="")
        self.parser.add_argument("--det_db_box_thresh", type=float, help="")
        self.parser.add_argument("--det_db_unclip_ratio", type=float, help="")
        self.parser.add_argument("--use_multiscale_det", type=bool, help="")
        self.parser.add_argument("--det_scales", type=list, help="")
        self.parser.add_argument("--use_tensorrt", type=bool, help="是否使用tensorrt加速, 需要gpu")
        self.parser.add_argument("--invalid_char_list", type=list, help="用于强制过滤非法角色名")
        self.parser.add_argument("--valid_char_list", type=list, help="合法角色名列表, 用于某些难以判别的场合")

        self.parser.add_argument("--final_process", '-fp', type=bool, help="是否进行切片与合并.")
        self.parser.add_argument("--refine_intervals", type=bool, help="是否进行区间细化.")
        self.parser.add_argument("--get_audio_segment", type=bool, help="是否进行音频切片.")
        self.parser.add_argument("--get_video_segment", type=bool, help="是否进行视频切片.")
        self.parser.add_argument("--merge_audio_video", type=bool, help="是否合并音视频.")
        self.parser.add_argument("--video_frame_rate", type=int, help="视频帧率.")
        self.parser.add_argument("--expand", type=int, help="片段扩展长度.")
        self.parser.add_argument("--keep_audio", type=bool, help="合并后是否保留音频.")
        self.parser.add_argument("--keep_video", type=bool, help="合并后是否保留视频.")

        self.parser.add_argument("--clear", type=bool, help="清理中间文件, 保留data和result.")

    def process_crop_size(self):
        crop_size = self.parser.crop_size
        special_input = ["4k", "1080p", "720p", "480p", "360p", "auto"]
        if crop_size in special_input:
            if crop_size == "4k":
                crop_size = "140:40:1300:1440"
            elif crop_size == '1080p':
                crop_size = "300:100:429:637"
            elif crop_size == "480p":
                crop_size = "32:13:291:320"
            elif crop_size == "auto":
                from models.ocr import EasyOCR
                ocr = EasyOCR(self.parser)
                crop_size = ocr.auto_crop(self.parser.target_word)
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
        config = self.default_config.copy()
        config.update({k: v for k, v in vars(self.parser).items() if v is not None})
        self.parser.__dict__.update(config)

        if self.parser.input_path is not None:
            self.parser.input_path = Path(self.parser.input_path).resolve().as_posix()
        if self.parser.output_path is not None:
            self.parser.output_path = Path(self.parser.output_path).resolve().as_posix()
        if self.parser.crop_video is True:
            self.process_crop_size()
        if type(self.parser.language) != list:
            self.parser.language = [self.parser.language]

        return self.parser
        
