"""
Visual Data Extraction and Parsing System
Advanced OCR and visual analysis for extracting structured data from screen content.
"""

import cv2
import numpy as np
import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class ExtractedText:
    """Represents extracted text with position and confidence."""
    text: str
    confidence: float
    bounds: Tuple[int, int, int, int]  # x, y, width, height
    font_size: Optional[int] = None
    is_bold: bool = False
    color: Optional[Tuple[int, int, int]] = None

@dataclass
class StructuredData:
    """Represents structured data extracted from visual content."""
    data_type: str  # email, file, process, etc.
    fields: Dict[str, Any]
    confidence: float
    source_region: Tuple[int, int, int, int]
    extraction_method: str
    timestamp: datetime

class OCREngine:
    """Advanced OCR engine with multiple backends and preprocessing."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.OCREngine")
        
    async def extract_text(self, image: np.ndarray, preprocessing: bool = True) -> List[ExtractedText]:
        """Extract text from image with position information."""
        if preprocessing:
            image = await self._preprocess_image(image)
        
        # For now, simulate OCR results
        # In real implementation, this would use pytesseract, EasyOCR, or similar
        return await self._simulate_ocr_results(image)
    
    async def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR results."""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Noise reduction
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # Enhance contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Binarization
        _, binary = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary
    
    async def _simulate_ocr_results(self, image: np.ndarray) -> List[ExtractedText]:
        """Simulate OCR results for demonstration."""
        height, width = image.shape[:2]
        
        # Simulate some extracted text blocks
        mock_results = [
            ExtractedText(
                text="Sample Email Subject: Important Meeting",
                confidence=0.95,
                bounds=(50, 100, 400, 25),
                font_size=14,
                is_bold=True
            ),
            ExtractedText(
                text="From: john@example.com",
                confidence=0.88,
                bounds=(50, 130, 200, 20),
                font_size=12
            ),
            ExtractedText(
                text="Date: 2024-01-15 10:30 AM",
                confidence=0.92,
                bounds=(50, 155, 180, 20),
                font_size=12
            ),
            ExtractedText(
                text="Chrome - Google Search",
                confidence=0.90,
                bounds=(10, 10, 200, 30),
                font_size=16,
                is_bold=True
            )
        ]
        
        return mock_results

class TextAnalyzer:
    """Analyzes extracted text to identify patterns and structure."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.TextAnalyzer")
        
        # Patterns for different data types
        self.patterns = {
            "email": {
                "subject": r"(?:Subject|Re|Fwd?):\s*(.+)",
                "from": r"From:\s*([^\n\r]+)",
                "to": r"To:\s*([^\n\r]+)",
                "date": r"(?:Date|Sent):\s*([^\n\r]+)",
                "email_address": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
            },
            "file": {
                "filename": r"([^\\/:*?\"<>|]+\.[a-zA-Z0-9]+)",
                "size": r"(\d+(?:\.\d+)?\s*[KMGT]?B)",
                "date_modified": r"(?:Modified|Date):\s*([^\n\r]+)",
                "file_type": r"\.([a-zA-Z0-9]+)$"
            },
            "process": {
                "process_name": r"^([A-Za-z][A-Za-z0-9\s\-\.]+)",
                "cpu_usage": r"(\d+(?:\.\d+)?%)",
                "memory_usage": r"(\d+(?:\.\d+)?\s*[KMGT]?B)",
                "pid": r"PID:\s*(\d+)"
            },
            "browser": {
                "url": r"https?://[^\s]+",
                "title": r"<title>([^<]+)</title>",
                "domain": r"https?://([^/]+)",
                "search_query": r"[?&]q=([^&]+)"
            },
            "time": {
                "time_12h": r"(\d{1,2}:\d{2}(?:\:\d{2})?\s*[APap][Mm])",
                "time_24h": r"(\d{1,2}:\d{2}(?:\:\d{2})?)",
                "date_mdy": r"(\d{1,2}/\d{1,2}/\d{2,4})",
                "date_ymd": r"(\d{4}-\d{1,2}-\d{1,2})",
                "relative_time": r"(\d+)\s+(minutes?|hours?|days?)\s+ago"
            }
        }
    
    async def analyze_text_structure(self, extracted_texts: List[ExtractedText]) -> Dict[str, List[Dict[str, Any]]]:
        """Analyze extracted text to identify structured data."""
        results = {
            "emails": [],
            "files": [],
            "processes": [],
            "browser_data": [],
            "time_references": []
        }
        
        # Combine all text for pattern matching
        full_text = "\n".join([et.text for et in extracted_texts])
        
        # Analyze for each data type
        results["emails"] = await self._extract_email_data(extracted_texts, full_text)
        results["files"] = await self._extract_file_data(extracted_texts, full_text)
        results["processes"] = await self._extract_process_data(extracted_texts, full_text)
        results["browser_data"] = await self._extract_browser_data(extracted_texts, full_text)
        results["time_references"] = await self._extract_time_data(extracted_texts, full_text)
        
        return results
    
    async def _extract_email_data(self, texts: List[ExtractedText], full_text: str) -> List[Dict[str, Any]]:
        """Extract email-related data."""
        emails = []
        email_patterns = self.patterns["email"]
        
        # Group related email elements
        current_email = {}
        
        for text_item in texts:
            text = text_item.text
            
            # Check for email patterns
            for field, pattern in email_patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if field == "email_address":
                        # Store all email addresses found
                        email_addresses = re.findall(pattern, text, re.IGNORECASE)
                        current_email["email_addresses"] = email_addresses
                    else:
                        current_email[field] = match.group(1).strip()
                    current_email["confidence"] = text_item.confidence
                    current_email["bounds"] = text_item.bounds
        
        if current_email:
            emails.append(current_email)
        
        return emails
    
    async def _extract_file_data(self, texts: List[ExtractedText], full_text: str) -> List[Dict[str, Any]]:
        """Extract file-related data."""
        files = []
        file_patterns = self.patterns["file"]
        
        for text_item in texts:
            text = text_item.text
            
            # Look for filenames
            filename_match = re.search(file_patterns["filename"], text)
            if filename_match:
                file_data = {
                    "filename": filename_match.group(1),
                    "confidence": text_item.confidence,
                    "bounds": text_item.bounds
                }
                
                # Look for additional file info in the same line
                size_match = re.search(file_patterns["size"], text)
                if size_match:
                    file_data["size"] = size_match.group(1)
                
                date_match = re.search(file_patterns["date_modified"], text)
                if date_match:
                    file_data["date_modified"] = date_match.group(1)
                
                # Extract file extension
                ext_match = re.search(file_patterns["file_type"], file_data["filename"])
                if ext_match:
                    file_data["file_type"] = ext_match.group(1)
                
                files.append(file_data)
        
        return files
    
    async def _extract_process_data(self, texts: List[ExtractedText], full_text: str) -> List[Dict[str, Any]]:
        """Extract process/application data."""
        processes = []
        process_patterns = self.patterns["process"]
        
        for text_item in texts:
            text = text_item.text
            
            # Look for process information
            if any(indicator in text.lower() for indicator in ["cpu", "memory", "process", "pid"]):
                process_data = {
                    "confidence": text_item.confidence,
                    "bounds": text_item.bounds
                }
                
                # Extract process name (first word that's not a number or percentage)
                words = text.split()
                for word in words:
                    if not re.match(r'^\d+%?$', word) and len(word) > 2:
                        process_data["process_name"] = word
                        break
                
                # Extract CPU usage
                cpu_match = re.search(process_patterns["cpu_usage"], text)
                if cpu_match:
                    process_data["cpu_usage"] = cpu_match.group(1)
                
                # Extract memory usage
                memory_match = re.search(process_patterns["memory_usage"], text)
                if memory_match:
                    process_data["memory_usage"] = memory_match.group(1)
                
                if len(process_data) > 2:  # More than just confidence and bounds
                    processes.append(process_data)
        
        return processes
    
    async def _extract_browser_data(self, texts: List[ExtractedText], full_text: str) -> List[Dict[str, Any]]:
        """Extract browser-related data."""
        browser_data = []
        browser_patterns = self.patterns["browser"]
        
        for text_item in texts:
            text = text_item.text
            
            # Look for URLs
            url_match = re.search(browser_patterns["url"], text)
            if url_match:
                data = {
                    "url": url_match.group(0),
                    "confidence": text_item.confidence,
                    "bounds": text_item.bounds
                }
                
                # Extract domain
                domain_match = re.search(browser_patterns["domain"], data["url"])
                if domain_match:
                    data["domain"] = domain_match.group(1)
                
                # Look for search queries
                query_match = re.search(browser_patterns["search_query"], data["url"])
                if query_match:
                    data["search_query"] = query_match.group(1)
                
                browser_data.append(data)
            
            # Look for page titles (if this is a browser window)
            elif "chrome" in text.lower() or "safari" in text.lower() or "firefox" in text.lower():
                browser_data.append({
                    "browser_title": text,
                    "confidence": text_item.confidence,
                    "bounds": text_item.bounds
                })
        
        return browser_data
    
    async def _extract_time_data(self, texts: List[ExtractedText], full_text: str) -> List[Dict[str, Any]]:
        """Extract time-related data."""
        time_data = []
        time_patterns = self.patterns["time"]
        
        for text_item in texts:
            text = text_item.text
            
            time_info = {
                "confidence": text_item.confidence,
                "bounds": text_item.bounds,
                "original_text": text
            }
            
            # Check different time formats
            for time_type, pattern in time_patterns.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    time_info[time_type] = match.group(1)
                    
                    # Try to parse to standard format
                    parsed_time = await self._parse_time_string(match.group(1), time_type)
                    if parsed_time:
                        time_info["parsed_time"] = parsed_time
            
            if len(time_info) > 3:  # More than just confidence, bounds, and original_text
                time_data.append(time_info)
        
        return time_data
    
    async def _parse_time_string(self, time_str: str, time_type: str) -> Optional[str]:
        """Parse time string to standard format."""
        try:
            if time_type in ["time_12h", "time_24h"]:
                # Return as-is for now, could parse to datetime
                return time_str
            elif time_type in ["date_mdy", "date_ymd"]:
                # Return as-is for now, could parse to date
                return time_str
            elif time_type == "relative_time":
                # Could calculate actual datetime
                return time_str
        except Exception as e:
            self.logger.debug(f"Failed to parse time string '{time_str}': {e}")
        
        return None

class VisualStructureAnalyzer:
    """Analyzes visual structure of content to understand layout and relationships."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.VisualStructureAnalyzer")
    
    async def analyze_layout(self, image: np.ndarray, extracted_texts: List[ExtractedText]) -> Dict[str, Any]:
        """Analyze the visual layout of content."""
        layout_info = {
            "text_regions": [],
            "visual_groups": [],
            "table_structures": [],
            "menu_structures": [],
            "form_elements": []
        }
        
        # Group texts by visual proximity
        layout_info["visual_groups"] = await self._group_texts_by_proximity(extracted_texts)
        
        # Detect table-like structures
        layout_info["table_structures"] = await self._detect_table_structures(image, extracted_texts)
        
        # Detect menu structures
        layout_info["menu_structures"] = await self._detect_menu_structures(extracted_texts)
        
        # Detect form elements
        layout_info["form_elements"] = await self._detect_form_elements(image, extracted_texts)
        
        return layout_info
    
    async def _group_texts_by_proximity(self, texts: List[ExtractedText]) -> List[List[ExtractedText]]:
        """Group texts that are visually close to each other."""
        groups = []
        used_indices = set()
        
        for i, text1 in enumerate(texts):
            if i in used_indices:
                continue
            
            group = [text1]
            used_indices.add(i)
            
            for j, text2 in enumerate(texts):
                if j in used_indices:
                    continue
                
                # Check if texts are close enough to be grouped
                if self._are_texts_related(text1, text2):
                    group.append(text2)
                    used_indices.add(j)
            
            groups.append(group)
        
        return groups
    
    def _are_texts_related(self, text1: ExtractedText, text2: ExtractedText, threshold: int = 50) -> bool:
        """Check if two text elements are visually related."""
        x1, y1, w1, h1 = text1.bounds
        x2, y2, w2, h2 = text2.bounds
        
        # Calculate distance between centers
        center1 = (x1 + w1/2, y1 + h1/2)
        center2 = (x2 + w2/2, y2 + h2/2)
        
        distance = ((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)**0.5
        
        return distance < threshold
    
    async def _detect_table_structures(self, image: np.ndarray, texts: List[ExtractedText]) -> List[Dict[str, Any]]:
        """Detect table-like structures in the image."""
        tables = []
        
        # Use edge detection to find grid patterns
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Detect horizontal and vertical lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
        
        horizontal_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(gray, cv2.MORPH_OPEN, vertical_kernel)
        
        # Combine lines to detect table structure
        table_structure = cv2.add(horizontal_lines, vertical_lines)
        
        # Find contours that might represent table cells
        contours, _ = cv2.findContours(table_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours that look like table cells
        table_cells = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / h if h > 0 else 0
            
            # Table cells should have reasonable dimensions and aspect ratio
            if 50 < w < 300 and 20 < h < 100 and 0.5 < aspect_ratio < 5.0:
                table_cells.append((x, y, w, h))
        
        if len(table_cells) > 2:  # At least 3 cells to consider it a table
            tables.append({
                "type": "table",
                "cells": table_cells,
                "confidence": 0.7
            })
        
        return tables
    
    async def _detect_menu_structures(self, texts: List[ExtractedText]) -> List[Dict[str, Any]]:
        """Detect menu-like structures."""
        menus = []
        
        # Look for horizontal alignments (horizontal menus)
        y_groups = {}
        for text in texts:
            y = text.bounds[1]
            y_range = y // 10 * 10  # Group by 10-pixel ranges
            
            if y_range not in y_groups:
                y_groups[y_range] = []
            y_groups[y_range].append(text)
        
        # Check for menu-like patterns
        for y_range, group_texts in y_groups.items():
            if len(group_texts) >= 3:  # At least 3 items in a row
                # Check if they contain menu-like words
                menu_words = ["file", "edit", "view", "help", "tools", "window"]
                menu_count = sum(1 for text in group_texts 
                               if any(word in text.text.lower() for word in menu_words))
                
                if menu_count >= 2:
                    menus.append({
                        "type": "horizontal_menu",
                        "items": [text.text for text in group_texts],
                        "bounds": self._get_group_bounds(group_texts),
                        "confidence": menu_count / len(group_texts)
                    })
        
        return menus
    
    async def _detect_form_elements(self, image: np.ndarray, texts: List[ExtractedText]) -> List[Dict[str, Any]]:
        """Detect form elements like input fields, buttons, etc."""
        form_elements = []
        
        # Look for form-related text
        form_indicators = ["search", "enter", "submit", "login", "password", "email", "name"]
        
        for text in texts:
            text_lower = text.text.lower()
            
            if any(indicator in text_lower for indicator in form_indicators):
                form_elements.append({
                    "type": "form_label",
                    "text": text.text,
                    "bounds": text.bounds,
                    "confidence": 0.8
                })
        
        return form_elements
    
    def _get_group_bounds(self, texts: List[ExtractedText]) -> Tuple[int, int, int, int]:
        """Get bounding box that encompasses all texts in a group."""
        if not texts:
            return (0, 0, 0, 0)
        
        min_x = min(text.bounds[0] for text in texts)
        min_y = min(text.bounds[1] for text in texts)
        max_x = max(text.bounds[0] + text.bounds[2] for text in texts)
        max_y = max(text.bounds[1] + text.bounds[3] for text in texts)
        
        return (min_x, min_y, max_x - min_x, max_y - min_y)

class DataExtractor:
    """Main data extraction coordinator."""
    
    def __init__(self, backend_instance):
        self.backend = backend_instance
        self.ocr_engine = OCREngine()
        self.text_analyzer = TextAnalyzer()
        self.visual_analyzer = VisualStructureAnalyzer()
        self.logger = logging.getLogger(f"{__name__}.DataExtractor")
    
    async def extract_structured_data(self, image: np.ndarray, 
                                    data_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract structured data from an image."""
        self.logger.info("Starting visual data extraction")
        
        try:
            # Step 1: OCR extraction
            extracted_texts = await self.ocr_engine.extract_text(image)
            self.logger.info(f"Extracted {len(extracted_texts)} text elements")
            
            # Step 2: Text analysis
            structured_data = await self.text_analyzer.analyze_text_structure(extracted_texts)
            self.logger.info("Completed text structure analysis")
            
            # Step 3: Visual layout analysis
            layout_info = await self.visual_analyzer.analyze_layout(image, extracted_texts)
            self.logger.info("Completed visual layout analysis")
            
            # Step 4: Combine results
            results = {
                "extraction_timestamp": datetime.now().isoformat(),
                "image_dimensions": image.shape[:2],
                "raw_texts": [asdict(text) for text in extracted_texts],
                "structured_data": structured_data,
                "layout_analysis": layout_info,
                "extraction_quality": await self._assess_extraction_quality(extracted_texts, structured_data)
            }
            
            # Filter by requested data types if specified
            if data_types:
                results["structured_data"] = {
                    key: value for key, value in results["structured_data"].items()
                    if any(dt in key for dt in data_types)
                }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in visual data extraction: {e}")
            return {
                "extraction_timestamp": datetime.now().isoformat(),
                "error": str(e),
                "extraction_quality": {"overall_score": 0.0}
            }
    
    async def extract_specific_data_type(self, image: np.ndarray, data_type: str) -> List[StructuredData]:
        """Extract specific type of structured data."""
        extraction_result = await self.extract_structured_data(image, [data_type])
        
        structured_items = []
        
        if data_type in extraction_result.get("structured_data", {}):
            items = extraction_result["structured_data"][data_type]
            
            for item in items:
                structured_data = StructuredData(
                    data_type=data_type,
                    fields=item,
                    confidence=item.get("confidence", 0.5),
                    source_region=item.get("bounds", (0, 0, 0, 0)),
                    extraction_method="visual_ocr_analysis",
                    timestamp=datetime.now()
                )
                structured_items.append(structured_data)
        
        return structured_items
    
    async def _assess_extraction_quality(self, texts: List[ExtractedText], 
                                       structured_data: Dict[str, List]) -> Dict[str, float]:
        """Assess the quality of data extraction."""
        quality_metrics = {}
        
        # Text extraction quality
        if texts:
            avg_confidence = sum(text.confidence for text in texts) / len(texts)
            quality_metrics["text_confidence"] = avg_confidence
        else:
            quality_metrics["text_confidence"] = 0.0
        
        # Data structure quality
        total_structured_items = sum(len(items) for items in structured_data.values())
        quality_metrics["structured_data_count"] = total_structured_items
        
        # Overall quality score
        text_quality = quality_metrics["text_confidence"]
        structure_quality = min(1.0, total_structured_items / 10)  # Normalize to 0-1
        
        quality_metrics["overall_score"] = (text_quality + structure_quality) / 2
        
        return quality_metrics

# Integration with existing backend
async def integrate_visual_extraction_system(backend_instance):
    """
    Integrate visual data extraction system into the existing backend.
    """
    extractor = DataExtractor(backend_instance)
    
    # Add extractor to backend instance
    backend_instance.visual_extractor = extractor
    
    # Add new handler methods
    async def extract_visual_data(self, image: Optional[np.ndarray] = None, 
                                data_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract structured data from screen or provided image."""
        if image is None:
            image = await self.capture_screen_fast()
        
        return await self.visual_extractor.extract_structured_data(image, data_types)
    
    async def extract_specific_visual_data(self, data_type: str, 
                                         image: Optional[np.ndarray] = None) -> List[StructuredData]:
        """Extract specific type of data from screen or provided image."""
        if image is None:
            image = await self.capture_screen_fast()
        
        return await self.visual_extractor.extract_specific_data_type(image, data_type)
    
    # Bind methods to backend instance
    import types
    backend_instance.extract_visual_data = types.MethodType(
        extract_visual_data, backend_instance
    )
    backend_instance.extract_specific_visual_data = types.MethodType(
        extract_specific_visual_data, backend_instance
    )
    
    return backend_instance

if __name__ == "__main__":
    # Test the visual extraction system
    async def test_extraction():
        print("Visual Data Extraction System initialized")
        print("Components:")
        print("  - OCREngine: Advanced text extraction with preprocessing")
        print("  - TextAnalyzer: Pattern matching and structure identification")
        print("  - VisualStructureAnalyzer: Layout and relationship analysis") 
        print("  - DataExtractor: Main coordination and quality assessment")
        
        # Simulate extraction
        extractor = DataExtractor(None)
        mock_image = np.zeros((600, 800, 3), dtype=np.uint8)
        
        result = await extractor.extract_structured_data(mock_image)
        print(f"\nSimulated extraction result keys: {list(result.keys())}")
    
    asyncio.run(test_extraction())