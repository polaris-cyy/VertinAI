import sys, os
sys.path.append(os.path.dirname(__file__))

import glob
import difflib
import numpy as np
from tqdm import tqdm
import time
from os.path import dirname, abspath, join, isfile, isdir, exists
from argparse import ArgumentParser
import shutil
import json
from img_process import *
import cv2
from PaddleOCR.paddleocr import PaddleOCR

class BaseOCR():
    def __init__(self, opt: ArgumentParser):
        self.language = opt.language
        self.auto_crop_interval = opt.auto_crop_interval
        self.crop_ratio = opt.crop_ratio
        self.ocr_enhance_list = opt.ocr_enhance_list
        self.rec_algorithm = opt.rec_algorithm
        self.rec_batch_num = opt.rec_batch_num
        self.use_tensorrt = opt.use_tensorrt
        self.threshold = opt.match_threshold
        self.invalid_char_list = opt.invalid_char_list
        self.valid_char_list = opt.valid_char_list
        self.drop_score=opt.drop_score
        self.det_db_thresh = opt.det_db_thresh
        self.det_db_box_thresh = opt.det_db_box_thresh
        self.det_db_unclip_ratio = opt.det_db_unclip_ratio
        self.use_multiscale_det = opt.use_multiscale_det
        self.det_scales = opt.det_scales
        self.always_auto_crop = opt.always_auto_crop
        self.dbscan_eps = opt.dbscan_eps
        self.dbscan_min_samples = opt.dbscan_min_samples
        self.use_gpu = opt.use_tensorrt
        self.only_one_return = opt.only_one_return
        
        self.sr_model=None
        if "super_resolution" in self.ocr_enhance_list:
            sr_path = join(dirname(abspath(__file__)), "LapSRN_x2.pb")
            self.sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
            self.sr_model.readModel(sr_path)
            self.sr_model.setModel("lapsrn", 2)            

        if type(self.language) != list:
            self.language = [self.language]

    # Every subclass should implement its own readtext method
    def readtext(self, image_path, with_bb=False, with_enhance=True):
        raise NotImplementedError
    
    def readtext_from_folder(self, folder_path):
        text_list = []
        last_time = time.time()
        with tqdm(total=len(glob.glob(join(folder_path, '*.jpg')) + glob.glob(join(folder_path, '*.png'))), \
                  desc="已处理", leave=True, ncols=100) as pbar:
            for i, file_path in enumerate(glob.glob(join(folder_path, '*.jpg')) + glob.glob(join(folder_path, '*.png'))):
                current_time = time.time()
                if current_time - last_time > 0.2:
                    pbar.update(i - pbar.n)
                    last_time = current_time
                text = self.readtext(file_path)
                text_list.append(text)
            pbar.update(len(glob.glob(join(folder_path, '*.jpg')) + glob.glob(join(folder_path, '*.png'))) - pbar.n)
        return text_list

    def eng_match(self, word, target_word):
        word = word.lower()
        target_word = target_word.lower()
        word = word.replace(" ", "")
        target_word = target_word.replace(" ", "")
        return difflib.SequenceMatcher(None, word, target_word).ratio() >= self.threshold
    
    def ch_match(self, word, target_word):
        from char_similar import std_cal_sim
        rat = difflib.SequenceMatcher(None, word, target_word).ratio()
        if rat >= self.threshold:
            return True
        
        if len(word)!= len(target_word):
            return False
        for c1, c2 in zip(word, target_word):
            if c1 == c2:
                continue
            if std_cal_sim(c1, c2, rounded=4,kind="shape") < self.threshold:
                return False
        return True

    def fuzzy_match(self, word, target_word):
        if word in self.invalid_char_list:
            return False
        if word == target_word or word in self.valid_char_list:
            return True
        
        if word.startswith(target_word):
            return True

        if target_word not in self.valid_char_list:
            self.valid_char_list.append(target_word)
        res = []
        for tword in self.valid_char_list:
            if 'en' in self.language:
                res.append(self.eng_match(word, tword))
            elif 'ch' in self.language:
                res.append(self.ch_match(word, tword))
        return any(res)

    def find_index_by_word(self, folder_path, target_word, rewrite=False):
        if folder_path == None:
            folder_path = join(dirname(dirname(abspath(__file__))), "fixedM4S_cropped_frames")
        entries = os.listdir(folder_path)
        if "images" not in entries or "params" not in entries:
            for entry in entries:
                if isdir(join(folder_path, entry)):
                    self.find_index_by_word(join(folder_path, entry), target_word, rewrite)
            return []
        
        print(f"识别{target_word}, 目录为{folder_path}")
        info_path = join(join(folder_path, "params"), "index_info.txt")
        image_path = join(folder_path, "images")
        if isfile(info_path) and not rewrite:
            print(f"文件已存在于{folder_path}")
            return []
        
        text_list = self.readtext_from_folder(image_path)
        res_list = []
        last_time = time.time()
        with tqdm(total=len(text_list), desc="已识别", leave=True, ncols=100) as pbar:
            for i, text in enumerate(text_list):
                current_time = time.time()
                if current_time - last_time > 0.2:
                    pbar.update(i - pbar.n)
                    last_time = current_time
                prob_list = [self.fuzzy_match(word, target_word) for word in text]
                if any(prob_list):
                    res_list.append(i)
            pbar.update(len(text_list) - pbar.n)
        if isfile(info_path):
            os.remove(info_path)
        with open(info_path, "w") as f:
            f.write(f"Target word: {target_word}\n")
            f.write(f"Found index: {res_list}\n")
        return res_list
    
    def auto_crop(self, target_word):
        import cv2
        from sklearn.cluster import DBSCAN
        import data_process

        # step 1: get centers and boxes
        temp_only_one_return = self.only_one_return
        if self.only_one_return:
            self.only_one_return = False
        ref_path = join(dirname(dirname(abspath(__file__))), "ref")
        if not exists(ref_path):
            os.makedirs(ref_path)
        ref_params = join(ref_path, "params")
        if not exists(ref_params):
            os.makedirs(ref_params)
        else:
            param = join(ref_params, f"{target_word}.json")
            if isfile(param) and not self.always_auto_crop:
                with open(param, "r") as f:
                    bb_info = json.load(f)
                print(f"{target_word}已有对应crop_size: {bb_info['crop_size']}")
                return bb_info['crop_size']
                

        ref_video = join(ref_path, "video")
        if not exists(ref_video):
            os.makedirs(ref_video)
        ref_img = join(ref_path, "images")
        if not exists(ref_img):
            os.makedirs(ref_img)

        if len(os.listdir(ref_img)) == 0 and len(os.listdir(ref_video)) == 0:
            print("自动确定crop size需要参考图或视频, 放置于ref目录下对应文件夹中。自动选择第一个视频作为参考。")
            copy_path = join(dirname(ref_path), "fixedM4S")
            copy_path = join(copy_path, os.listdir(copy_path)[0])
            copy_path = join(copy_path, [x for x in os.listdir(copy_path) if x.endswith(".mp4")][0])
            shutil.copy(copy_path, ref_video)
        if len(os.listdir(ref_img)) == 0:
            ref_video = join(ref_video, os.listdir(ref_video)[0])
            cap = cv2.VideoCapture(ref_video)
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_inverval = self.auto_crop_interval * fps
            cap.release()
            output_path = dirname(ref_img)
            data_process.extract_frames(ref_video, output_path, frame_inverval)

        boxes, centers = [], []
        with tqdm(total = len(os.listdir(ref_img)), desc="计算crop size", leave=True, ncols=100) as pbar:
            last_time = time.time()
            for i, image in enumerate(os.listdir(ref_img)):
                current_time = time.time()
                if current_time - last_time > 0.2:
                    pbar.update(i - pbar.n)
                
                bb, texts = self.readtext(join(ref_img, image), with_bb=True, with_enhance=False)
                
                for i, text in enumerate(texts):
                    if self.fuzzy_match(text, target_word):
                        boxes.append(bb[i])
                        center = (int((bb[i][0][0] + bb[i][2][0])/2), int((bb[i][0][1] + bb[i][2][1])/2))
                        centers.append(center)
            pbar.update(len(os.listdir(ref_img)) - pbar.n)
        # step 2: cluster centers

        centers = np.array(centers)
        print(f"共有{len(centers)}/{len(os.listdir(ref_img))}个候选位置")
        dbscan = DBSCAN(eps=self.dbscan_eps, min_samples=self.dbscan_min_samples)
        labels = dbscan.fit_predict(centers)
        # print(clusters)
        unique_labels, counts = np.unique(labels, return_counts=True)
        # print(unique_labels, counts)
        main_cluster_label = unique_labels[np.argmax(counts)]
        # print(main_cluster_label)
        boxes = np.array(boxes)
        boxes = boxes[labels == main_cluster_label]


        # step 3: get rect
        min_x = np.min(boxes[:, :, 0])
        min_y = np.min(boxes[:, :, 1])
        max_x = np.max(boxes[:, :, 0])
        max_y = np.max(boxes[:, :, 1])
        width = max_x-min_x
        height = max_y-min_y
        crop_ratio = self.crop_ratio
        min_x = max(0, min_x-width*(crop_ratio-1)/2)
        min_y = max(0, min_y-height*(crop_ratio-1)/2)
        width = crop_ratio * width
        height = crop_ratio * height
        width, height, min_x, min_y = int(width), int(height), int(min_x), int(min_y)
        ret = f"{width}:{height}:{min_x}:{min_y}"
        with open(join(ref_params, f"{target_word}.json"), "w") as f:
            json.dump({"crop_size": ret}, f)
        print("建议crop size: {}".format(ret))

        self.only_one_return = temp_only_one_return
        return ret
    
# class EasyOCR(BaseOCR):
#     def __init__(self, language=['en']):
#         super().__init__(language)
#         self.reader = easyocr.Reader(lang_list = language)

class EasyOCR(BaseOCR):
    def __init__(self, opt: ArgumentParser):
        super().__init__(opt)
        self.reader = PaddleOCR(
            lang=self.language[0],
            use_angle_cls=True,
            show_log=False,
            rec_algorithm=self.rec_algorithm,
            rec_batch_num=self.rec_batch_num,
            drop_score=self.drop_score,
            det_db_thresh=self.det_db_thresh,
            det_db_box_thresh=self.det_db_box_thresh,
            det_db_unclip_ratio=self.det_db_unclip_ratio,
            use_multiscale_det=self.use_multiscale_det,
            det_scales=self.det_scales,
            use_gpu=self.use_gpu,
            use_tensorrt=self.use_tensorrt,
            ) 
    
    def readtext(self, image_path, with_bb=False, with_enhance=True):
        if isfile(image_path):
            image_path = cv2.imread(image_path)
        if with_enhance:
            for enhance_step in self.ocr_enhance_list:
                if enhance_step == "super_resolution":
                    image_path = super_resolution(image_path, self.sr_model)
                else: 
                    image_path = eval(enhance_step)(image_path)
        text = self.reader.ocr(image_path, cls=True)
        texts = []
        bbs = []
        height, width = image_path.shape[:2]
        mid_x, mid_y = width/2, height/2
        if text[0] != None:
            for i in range(len(text[0])):
                t = text[0][i][1][0]
                bb = text[0][i][0]
                texts.append(t)
                bbs.append(bb)
        if self.only_one_return and texts != []:
            temp_texts, temp_bbs = [], []
            for (t, bb) in zip(texts, bbs):
                bb = np.array(bb)
                min_x, min_y, max_x, max_y = np.min(bb[:, 0]), np.min(bb[:, 1]), np.max(bb[:, 0]), np.max(bb[:, 1])
                if min_x < mid_x and max_x > mid_x and min_y < mid_y and max_y > mid_y:
                    temp_texts.append(t)
                    temp_bbs.append(bb)
            if len(temp_texts) > 0:
                texts, bbs = temp_texts, temp_bbs
            if len(texts) != 1:
                temp_text = texts[0]
                temp_bb = bbs[0]
                min_dis = float('inf')
                for (t, bb) in zip(texts, bbs):
                    bb = np.array(bb)
                    min_x, min_y, max_x, max_y = np.min(bb[:, 0]), np.min(bb[:, 1]), np.max(bb[:, 0]), np.max(bb[:, 1])
                    dis = np.linalg.norm(np.array([mid_x, mid_y]) - np.array([(min_x+max_x)/2, (min_y+max_y)/2]))
                    if dis  < min_dis:
                        temp_text, temp_bb, min_dis = t, bb, dis
                texts, bbs = [temp_text], [temp_bb]
        if with_bb:
            return bbs, texts
        else:
            return texts
        
if __name__ == "__main__":
    
    ocr = PaddleOCR(
        lang='ch',
        use_angle_cls=True,
        show_log=False,
        rec_algorithm="SVTR_LCNet",
        rec_batch_num=10,
        drop_score=0.5,
        det_db_thresh=0.3,
        det_db_box_thresh=0.5,
        det_db_unclip_ratio=2.0,
        use_multiscale_det=True,
        det_scales=[0.5, 1.0, 2.0]
        
    ) 
    path = r"D:\D\VertinAI\1.png"
    sr_model = cv2.dnn_superres.DnnSuperResImpl_create()
    sr_path = "D:\D\VertinAI\models\LapSRN_x2.pb"
    sr_model.readModel(sr_path)
    sr_model.setModel("lapsrn", 2)  
    img = cv2.imread(path)
    # img = super_resolution(img, sr_model)
    # img = grayscale(path)
    
    # img = super_resolution(img, sr_model)
    # img = dilate(img)
    # img = sharpen(img)

    # img = grayscale(img)
    # img = sharpen(img)

    text = ocr.ocr(img, cls=True)
    print(text)
    cv2.imshow("img", img)
    cv2.waitKey(0)
    # text = ocr.ocr(img, cls=True)
    print(text)