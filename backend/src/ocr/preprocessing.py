"""
Image preprocessing module for OCR.
Contains functions for image enhancement, noise reduction, and other preprocessing steps
to improve OCR accuracy.
"""

import cv2
import numpy as np
from typing import Tuple, Optional


def resize_image(image: np.ndarray, width: int = 1000) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio.
    
    Args:
        image: Input image as numpy array
        width: Target width for the resized image
        
    Returns:
        Resized image
    """
    height, original_width = image.shape[:2]
    ratio = width / float(original_width)
    target_height = int(height * ratio)
    return cv2.resize(image, (width, target_height))


def grayscale(image: np.ndarray) -> np.ndarray:
    """
    Convert image to grayscale if it's not already.
    
    Args:
        image: Input image as numpy array
        
    Returns:
        Grayscale image
    """
    if len(image.shape) == 3:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return image


def denoise(image: np.ndarray) -> np.ndarray:
    """
    Apply denoising to the image.
    
    Args:
        image: Input grayscale image
        
    Returns:
        Denoised image
    """
    return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)


def threshold(image: np.ndarray) -> np.ndarray:
    """
    Apply adaptive thresholding to the image.
    
    Args:
        image: Input grayscale image
        
    Returns:
        Thresholded binary image
    """
    return cv2.adaptiveThreshold(
        image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )


def deskew(image: np.ndarray) -> np.ndarray:
    """
    Deskew the image to correct for rotation.
    
    Args:
        image: Input grayscale or binary image
        
    Returns:
        Deskewed image
    """
    # Calculate skew angle
    coords = np.column_stack(np.where(image > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    # Adjust angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    # Rotate image
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def preprocess_image(image_path: str) -> np.ndarray:
    """
    Apply full preprocessing pipeline to an image.
    
    Args:
        image_path: Path to the input image file
        
    Returns:
        Preprocessed image ready for OCR
    """
    # Read image
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not read image at {image_path}")
    
    # Apply preprocessing steps
    image = resize_image(image)
    image = grayscale(image)
    image = denoise(image)
    image = threshold(image)
    image = deskew(image)
    
    return image