import cv2
import numpy as np
import os

def enhance(img):
    if os.path.isfile(img):
        img = cv2.imread(img)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    limg = clahe.apply(l)
    enhanced_lab = cv2.merge((limg, a, b))
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced

def enlarge(img, scale_factor=2.0, max_size=1000):
    if os.path.isfile(img):
        img = cv2.imread(img)
    if max(img.shape) > max_size:
        return img
    enlarged = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    return enlarged

def sharpen(img):
    if os.path.isfile(img):
        img = cv2.imread(img)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(img, -1, kernel)
    return sharpened

def super_resolution(img, model, max_size=1000):
    if os.path.isfile(img):
        img = cv2.imread(img)
    if max(img.shape) > max_size:
        return img
    img = model.upsample(img)
    return img