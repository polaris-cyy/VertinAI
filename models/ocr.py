import glob
import os
import difflib
import sys
import numpy as np

sys.path.append(os.path.dirname(__file__))
from PaddleOCR.paddleocr import PaddleOCR
from PaddleOCR import draw_ocr

class BaseOCR():
    def __init__(self, language=['ch']):
        self.language = language
        if type(language) != list:
            language = [language]

    def readtext(self, image_path):
        raise NotImplementedError
    
    def readtext_from_folder(self, folder_path):
        raise NotImplementedError

    def eng_match(self, word, target_word, threshold=0.7):
        word = word.lower()
        target_word = target_word.lower()
        word = word.replace(" ", "")
        target_word = target_word.replace(" ", "")
        return difflib.SequenceMatcher(None, word, target_word).ratio() >= threshold
    
    def ch_match(self, word, target_word, threshold=0.7):
        from char_similar import std_cal_sim
        if len(word) != len(target_word):
            return False
        for c1, c2 in zip(word, target_word):
            if c1 == c2:
                continue
            if std_cal_sim(c1, c2, rounded=4,kind="shape") < threshold:
                return False
        return True

    def fuzzy_match(self, word, target_word, threshold=0.7):
        if 'en' in self.language:
            return self.eng_match(word, target_word, threshold)
        elif 'ch' in self.language:
            return self.ch_match(word, target_word, threshold)

    def find_index_by_word(self, folder_path, target_word, threshold=0.7, rewrite=False):
        raise NotImplementedError
    
# class EasyOCR(BaseOCR):
#     def __init__(self, language=['en']):
#         super().__init__(language)
#         self.reader = easyocr.Reader(lang_list = language)

class EasyOCR(BaseOCR):
    def __init__(self, language=['ch']):
        super().__init__(language)
        self.reader = PaddleOCR(
            lang=self.language[0],
            use_angle_cls=True,
            show_log=False
            ) 
    
    def readtext(self, image_path):
        text = self.reader.ocr(image_path, cls=True)
        if text[0] != None:
            return [text[0][i][1][0] for i in range(len(text[0]))]
        else:
            return []
    
    def readtext_from_folder(self, folder_path):
        text_list = []
        for i, file_path in enumerate(glob.glob(os.path.join(folder_path, '*.jpg')) + glob.glob(os.path.join(folder_path, '*.png'))):
            if i % 100 == 0:
                print(f"Processed {i} images")
                print(f"Current text list: {text_list[-5:]}")
            temp = self.readtext(file_path)
            text = []
            if type(temp[0]) == list:
                for i in range(len(temp[0])):
                    text.append(temp[0][i][1][0])
            text_list.append(text)
        return text_list
    
    def find_index_by_word(self, folder_path, target_word, threshold=0.7, rewrite=False):
        if folder_path == None:
            folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../fixedM4S_cropped_frames")
        entries = os.listdir(folder_path)
        if "images" not in entries or "params" not in entries:
            for entry in entries:
                if os.path.isdir(os.path.join(folder_path, entry)):
                    self.find_index_by_word(os.path.join(folder_path, entry), target_word, threshold, rewrite)
            return []
        
        print(f"Searching for {target_word} in {folder_path}")
        info_path = os.path.join(os.path.join(folder_path, "params"), "index_info.txt")
        image_path = os.path.join(folder_path, "images")
        if os.path.isfile(info_path) and not rewrite:
            print(f"Index info file already exists in {folder_path}, skipping")
            return []
        
        text_list = self.readtext_from_folder(image_path)
        res_list = []
        for i, text in enumerate(text_list):
            if i % 100 == 0:
                print(f"Matched {i} words")
            prob_list = [self.fuzzy_match(word, target_word, threshold) for word in text]
            if any(prob_list):
                res_list.append(i)
        if os.path.isfile(info_path):
            os.remove(info_path)
        with open(info_path, "w") as f:
            f.write(f"Target word: {target_word}\n")
            f.write(f"Found index: {res_list}\n")
        return res_list