"""
Image Enhancement Utilities for Plate Image Processing

This module provides advanced image enhancement techniques for improving
low-quality license plate images before OCR processing.
"""

import cv2
import numpy as np
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PlateImageEnhancer:
    """
    Advanced image enhancement for license plate images using CLAHE and denoising.
    
    Techniques:
    - CLAHE (Contrast Limited Adaptive Histogram Equalization)
    - Fast Non-Local Means Denoising
    - Morphological operations
    - Deskewing
    - Sharpening
    """
    
    @staticmethod
    def enhance_basic(image: np.ndarray) -> np.ndarray:
        """
        Basic enhancement using CLAHE and denoising.
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Enhanced image
        """
        if image is None or image.size == 0:
            logger.warning("Empty or None image provided")
            return None
        
        try:
            # Convert to grayscale if needed
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            logger.debug("Applied CLAHE enhancement")
            
            # Denoise the image
            denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)
            logger.debug("Applied denoising")
            
            return denoised
        except Exception as e:
            logger.error(f"Error in basic enhancement: {e}")
            return image
    
    @staticmethod
    def enhance_advanced(image: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Advanced multi-stage enhancement with multiple output variants.
        
        Stages:
        1. Denoising - Remove camera grain and noise
        2. CLAHE - Adaptive contrast enhancement
        3. Deskewing - Correct rotated plates
        4. Sharpening - Enhance text clarity
        5. Thresholding - Convert to binary images
        6. Morphology - Clean artifacts
        
        Args:
            image: Input image (BGR or grayscale)
            
        Returns:
            Dictionary with multiple enhanced versions
        """
        if image is None or image.size == 0:
            logger.warning("Empty or None image provided")
            return None
        
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            logger.debug(f"Processing image with shape: {gray.shape}")
            
            # Stage 1: Denoise
            denoised = cv2.fastNlMeansDenoising(
                gray, 
                h=10, 
                templateWindowSize=7, 
                searchWindowSize=21
            )
            logger.debug("Stage 1: Denoising complete")
            
            # Stage 2: CLAHE for contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(denoised)
            logger.debug("Stage 2: CLAHE enhancement complete")
            
            # Stage 3: Deskewing
            deskewed = PlateImageEnhancer.deskew_image(enhanced)
            logger.debug("Stage 3: Deskewing complete")
            
            # Stage 4: Sharpening
            sharpened = PlateImageEnhancer.sharpen_image(deskewed)
            logger.debug("Stage 4: Sharpening complete")
            
            # Stage 5: Thresholding (multiple methods)
            # Otsu's method
            _, otsu_binary = cv2.threshold(
                sharpened, 0, 255, 
                cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            
            # Adaptive thresholding
            adaptive_binary = cv2.adaptiveThreshold(
                sharpened, 255, 
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 
                15, 3
            )
            logger.debug("Stage 5: Thresholding complete")
            
            # Stage 6: Morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            otsu_morph = cv2.morphologyEx(otsu_binary, cv2.MORPH_CLOSE, kernel)
            adaptive_morph = cv2.morphologyEx(adaptive_binary, cv2.MORPH_CLOSE, kernel)
            logger.debug("Stage 6: Morphological operations complete")
            
            results = {
                'original': gray,
                'denoised': denoised,
                'enhanced': enhanced,
                'deskewed': deskewed,
                'sharpened': sharpened,
                'otsu_binary': otsu_binary,
                'otsu_morph': otsu_morph,
                'adaptive_binary': adaptive_binary,
                'adaptive_morph': adaptive_morph,
            }
            
            logger.debug("Advanced enhancement complete")
            return results
        
        except Exception as e:
            logger.error(f"Error in advanced enhancement: {e}")
            return None
    
    @staticmethod
    def deskew_image(image: np.ndarray) -> np.ndarray:
        """
        Deskew image by correcting rotated plates.
        
        Uses contour detection to find text orientation and rotate accordingly.
        
        Args:
            image: Grayscale image
            
        Returns:
            Deskewed image
        """
        try:
            # Find contours
            contours, _ = cv2.findContours(
                image, 
                cv2.RETR_EXTERNAL, 
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            if not contours:
                logger.debug("No contours found for deskewing")
                return image
            
            # Get the largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Fit a minimum area rectangle
            rect = cv2.minAreaRect(largest_contour)
            angle = rect[2]
            
            # Only rotate if angle is significant (>5 degrees)
            if abs(angle) > 5:
                h, w = image.shape
                center = (w // 2, h // 2)
                
                # Get rotation matrix
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                
                # Apply rotation
                deskewed = cv2.warpAffine(
                    image, 
                    rotation_matrix, 
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_REPLICATE
                )
                logger.debug(f"Deskewed image by {angle:.2f} degrees")
                return deskewed
            else:
                logger.debug("Image skew is minimal, no deskewing needed")
                return image
        
        except Exception as e:
            logger.error(f"Error in deskewing: {e}")
            return image
    
    @staticmethod
    def sharpen_image(image: np.ndarray, kernel_strength: float = 1.0) -> np.ndarray:
        """
        Sharpen image to enhance text edges.
        
        Args:
            image: Input image
            kernel_strength: Strength of sharpening (0.5-2.0)
            
        Returns:
            Sharpened image
        """
        try:
            # Unsharp masking kernel
            kernel = np.array([
                [-1, -1, -1],
                [-1,  9 * kernel_strength, -1],
                [-1, -1, -1]
            ], dtype=np.float32)
            
            sharpened = cv2.filter2D(image, -1, kernel)
            logger.debug(f"Applied sharpening with strength {kernel_strength}")
            return sharpened
        
        except Exception as e:
            logger.error(f"Error in sharpening: {e}")
            return image
    
    @staticmethod
    def denoise_image(image: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Denoise image using Non-Local Means.
        
        Args:
            image: Input image
            strength: Denoising strength (higher = more aggressive)
            
        Returns:
            Denoised image
        """
        try:
            if len(image.shape) == 3:
                denoised = cv2.fastNlMeansDenoisingColored(
                    image,
                    h=strength,
                    templateWindowSize=7,
                    searchWindowSize=21
                )
                logger.debug(f"Applied color denoising with strength {strength}")
            else:
                denoised = cv2.fastNlMeansDenoising(
                    image,
                    h=strength,
                    templateWindowSize=7,
                    searchWindowSize=21
                )
                logger.debug(f"Applied grayscale denoising with strength {strength}")
            
            return denoised
        
        except Exception as e:
            logger.error(f"Error in denoising: {e}")
            return image
    
    @staticmethod
    def enhance_contrast(image: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        """
        Enhance contrast using CLAHE.
        
        Args:
            image: Grayscale image
            clip_limit: CLAHE clipping limit (1.0-4.0, higher = more aggressive)
            
        Returns:
            Contrast-enhanced image
        """
        try:
            clahe = cv2.createCLAHE(
                clipLimit=clip_limit, 
                tileGridSize=(8, 8)
            )
            enhanced = clahe.apply(image)
            logger.debug(f"Applied CLAHE with clip_limit={clip_limit}")
            return enhanced
        
        except Exception as e:
            logger.error(f"Error in contrast enhancement: {e}")
            return image
    
    @staticmethod
    def binarize_image(image: np.ndarray, method: str = 'otsu') -> np.ndarray:
        """
        Convert image to binary (black and white).
        
        Args:
            image: Grayscale image
            method: 'otsu', 'adaptive', or 'otsu_inv', 'adaptive_inv'
            
        Returns:
            Binary image
        """
        try:
            if method == 'otsu':
                _, binary = cv2.threshold(
                    image, 0, 255, 
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            elif method == 'adaptive':
                binary = cv2.adaptiveThreshold(
                    image, 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 
                    15, 3
                )
            elif method == 'otsu_inv':
                _, binary = cv2.threshold(
                    image, 0, 255, 
                    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
                )
            elif method == 'adaptive_inv':
                binary = cv2.adaptiveThreshold(
                    image, 255, 
                    cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY_INV, 
                    15, 3
                )
            else:
                logger.warning(f"Unknown binarization method: {method}, using Otsu")
                _, binary = cv2.threshold(
                    image, 0, 255, 
                    cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )
            
            logger.debug(f"Applied {method} binarization")
            return binary
        
        except Exception as e:
            logger.error(f"Error in binarization: {e}")
            return image
    
    @staticmethod
    def morphological_cleanup(image: np.ndarray, kernel_size: tuple = (3, 3)) -> np.ndarray:
        """
        Clean up binary image using morphological operations.
        
        Args:
            image: Binary image
            kernel_size: Kernel size for morphological operations
            
        Returns:
            Cleaned image
        """
        try:
            kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT, 
                kernel_size
            )
            
            # Close (fill small holes)
            closed = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
            
            # Open (remove small noise)
            opened = cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)
            
            logger.debug(f"Applied morphological cleanup with kernel {kernel_size}")
            return opened
        
        except Exception as e:
            logger.error(f"Error in morphological cleanup: {e}")
            return image
    
    @staticmethod
    def save_enhanced_image(
        image: np.ndarray, 
        filepath: str, 
        quality: int = 95
    ) -> bool:
        """
        Save enhanced image to file.
        
        Args:
            image: Image to save
            filepath: Output file path
            quality: JPEG quality (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if filepath.lower().endswith(('.jpg', '.jpeg')):
                cv2.imwrite(
                    filepath, 
                    image, 
                    [cv2.IMWRITE_JPEG_QUALITY, quality]
                )
            else:
                cv2.imwrite(filepath, image)
            
            logger.debug(f"Saved enhanced image to {filepath}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving image to {filepath}: {e}")
            return False


# Convenience functions for direct use

def enhance_plate_image_basic(image: np.ndarray) -> np.ndarray:
    """Quick enhancement with CLAHE and denoising."""
    return PlateImageEnhancer.enhance_basic(image)


def enhance_plate_image_advanced(image: np.ndarray) -> Dict[str, np.ndarray]:
    """Full multi-stage enhancement."""
    return PlateImageEnhancer.enhance_advanced(image)


def enhance_from_file(
    input_path: str, 
    output_path: str, 
    method: str = 'basic'
) -> bool:
    """
    Enhance image from file.
    
    Args:
        input_path: Path to input image
        output_path: Path to save enhanced image
        method: 'basic' or 'advanced'
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Read image
        image = cv2.imread(input_path)
        if image is None:
            logger.error(f"Failed to read image: {input_path}")
            return False
        
        # Enhance
        if method == 'basic':
            enhanced = PlateImageEnhancer.enhance_basic(image)
        elif method == 'advanced':
            results = PlateImageEnhancer.enhance_advanced(image)
            enhanced = results['enhanced'] if results else image
        else:
            logger.warning(f"Unknown method: {method}, using basic")
            enhanced = PlateImageEnhancer.enhance_basic(image)
        
        # Save
        if enhanced is not None:
            return PlateImageEnhancer.save_enhanced_image(enhanced, output_path)
        else:
            logger.error("Enhancement returned None")
            return False
    
    except Exception as e:
        logger.error(f"Error enhancing file {input_path}: {e}")
        return False
