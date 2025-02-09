import cv2
import numpy as np
import os

# 二值化
def binary(img, block_size=21, c=5):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, block_size, c
    )
    return binary

# 灰度化
def grayscale(img):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return gray

#clahe增强
def enhance(img):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    limg = clahe.apply(l)
    enhanced_lab = cv2.merge((limg, a, b))
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    return enhanced

# 放大
def enlarge(img, scale_factor=2.0, max_size=1000):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    if max(img.shape) > max_size:
        return img
    enlarged = cv2.resize(img, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)
    return enlarged

# 锐化
def sharpen(img):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    sharpened = cv2.filter2D(img, -1, kernel)
    return sharpened

# 拉普拉斯锐化
def laplacian_sharpen(img, k=1.0):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    laplacian = cv2.Laplacian(img, cv2.CV_64F)
    laplacian = np.uint8(np.absolute(laplacian))
    sharpened = cv2.addWeighted(img, 1, laplacian, k, 0)
    return sharpened

# 高斯模糊
def high_boost_sharpen(image, k=1.5):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    blurred = cv2.GaussianBlur(image, (0, 0), 1.0)
    mask = cv2.subtract(image, blurred)
    sharpened = cv2.addWeighted(image, 1.0, mask, k, 0)
    return sharpened

#超分辨率
def super_resolution(img, model, max_size=1000):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    if max(img.shape) > max_size:
        return img
    img = model.upsample(img)
    return img

def erode(img, kernel=np.ones((3, 3), np.uint8)):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    eroded = cv2.erode(img, kernel, iterations=1)
    return eroded

def dilate(img, kernel=np.ones((3, 3), np.uint8)):
    if isinstance(img, str) and os.path.isfile(img):
        img = cv2.imread(img)
    dilated = cv2.dilate(img, kernel, iterations=1)
    return dilated