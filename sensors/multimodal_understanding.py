"""
Multimodal Screen Understanding
Enhances screen context with visual pattern recognition capabilities
"""

import cv2
import numpy as np
from PIL import Image
import torch
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class VisualPattern:
    """Visual pattern detected in screen content."""
    pattern_type: str  # e.g., 'chart', 'table', 'form', 'code-block', 'navigation'
    confidence: float
    bbox: Tuple[int, int, int, int]
    properties: Dict[str, Any]

class MultiModalUnderstanding:
    """Enhances screen understanding with visual pattern recognition."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        
        # Initialize visual pattern detectors
        self.detectors = {
            'chart': self._init_chart_detector(),
            'table': self._init_table_detector(),
            'form': self._init_form_detector(),
            'code_block': self._init_code_block_detector(),
            'ui_component': self._init_ui_component_detector()
        }
    
    @staticmethod
    def _default_config() -> Dict[str, Any]:
        return {
            'confidence_threshold': 0.7,
            'enable_gpu': False,
            'pattern_detection': {
                'chart': True,
                'table': True,
                'form': True,
                'code_block': True,
                'ui_component': True
            }
        }
    
    def _init_chart_detector(self):
        """Initialize chart detection model."""
        # In a real implementation, this would load a pre-trained model
        # For this example, we'll implement a simplified heuristic detector
        return lambda img: self._detect_charts_heuristic(img)
    
    def _init_table_detector(self):
        """Initialize table detection model."""
        return lambda img: self._detect_tables_heuristic(img)
    
    def _init_form_detector(self):
        """Initialize form detection model."""
        return lambda img: self._detect_forms_heuristic(img)
    
    def _init_code_block_detector(self):
        """Initialize code block detection model."""
        return lambda img: self._detect_code_blocks_heuristic(img)
    
    def _init_ui_component_detector(self):
        """Initialize UI component detection model."""
        return lambda img: self._detect_ui_components_heuristic(img)
    
    def analyze_image(self, img: Image.Image) -> List[VisualPattern]:
        """Detect visual patterns in the screen image."""
        # Convert to numpy array for OpenCV processing
        img_np = np.array(img)
        
        patterns = []
        
        # Apply each enabled detector
        for pattern_type, enabled in self.config['pattern_detection'].items():
            if enabled and pattern_type in self.detectors:
                detector = self.detectors[pattern_type]
                detected_patterns = detector(img_np)
                patterns.extend(detected_patterns)
        
        return patterns
    
    def _detect_charts_heuristic(self, img_np: np.ndarray) -> List[VisualPattern]:
        """Detect charts using heuristic approach."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        chart_patterns = []
        
        for contour in contours:
            # Calculate area
            area = cv2.contourArea(contour)
            
            # Skip small contours
            if area < 5000:  # Minimum size for a chart
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate aspect ratio
            aspect_ratio = w / h if h > 0 else 0
            
            # Charts often have aspect ratios close to golden ratio
            is_chart_aspect = 0.5 <= aspect_ratio <= 2.0
            
            # Extract region for additional analysis
            region = gray[y:y+h, x:x+w]
            
            # Check for regular patterns of lines, which are common in charts
            horizontal_lines = cv2.HoughLinesP(
                cv2.Canny(region, 50, 150),
                1, np.pi/180, 100, minLineLength=w/3, maxLineGap=20
            )
            
            vertical_lines = cv2.HoughLinesP(
                cv2.Canny(region, 50, 150),
                1, np.pi/180, 100, minLineLength=h/3, maxLineGap=20
            )
            
            has_grid_lines = (horizontal_lines is not None and len(horizontal_lines) > 2 and
                             vertical_lines is not None and len(vertical_lines) > 2)
            
            # Determine if region is likely a chart
            confidence = 0.0
            
            if is_chart_aspect:
                confidence += 0.3
            
            if has_grid_lines:
                confidence += 0.5
            
            # Additional checks for chart-like features could go here
            
            if confidence >= self.config['confidence_threshold']:
                # Determine chart type based on features
                chart_type = self._determine_chart_type(region, horizontal_lines, vertical_lines)
                
                chart_patterns.append(VisualPattern(
                    pattern_type='chart',
                    confidence=confidence,
                    bbox=(x, y, x+w, y+h),
                    properties={
                        'chart_type': chart_type,
                        'has_grid': has_grid_lines,
                        'aspect_ratio': aspect_ratio
                    }
                ))
        
        return chart_patterns
    
    def _determine_chart_type(self, region: np.ndarray, h_lines, v_lines) -> str:
        """Determine the type of chart based on visual features."""
        # Simple heuristic determination
        if h_lines is not None and v_lines is not None:
            if len(h_lines) > len(v_lines) * 2:
                return 'bar_chart'
            elif len(v_lines) > len(h_lines) * 2:
                return 'column_chart'
            else:
                return 'scatter_plot'
        elif h_lines is not None:
            return 'line_chart'
        else:
            return 'pie_chart'  # Default guess if no clear pattern
    
    def _detect_tables_heuristic(self, img_np: np.ndarray) -> List[VisualPattern]:
        """Detect tables using heuristic approach."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Find horizontal and vertical lines
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
        
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
        vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel)
        
        # Combine lines
        table_mask = horizontal_lines + vertical_lines
        
        # Find contours in the combined mask
        contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        table_patterns = []
        
        for contour in contours:
            # Calculate area
            area = cv2.contourArea(contour)
            
            # Skip small contours
            if area < 5000:  # Minimum size for a table
                continue
                
            x, y, w, h = cv2.boundingRect(contour)
            
            # Check for grid pattern
            region_h_lines = horizontal_lines[y:y+h, x:x+w]
            region_v_lines = vertical_lines[y:y+h, x:x+w]
            
            h_line_count = cv2.countNonZero(region_h_lines) / (w * h)
            v_line_count = cv2.countNonZero(region_v_lines) / (w * h)
            
            # Tables typically have evenly spaced lines
            is_grid_pattern = h_line_count > 0.05 and v_line_count > 0.05
            
            confidence = 0.0
            
            if is_grid_pattern:
                confidence += 0.7
                
            # Check for consistent cell sizes
            if self._has_consistent_cells(region_h_lines, region_v_lines):
                confidence += 0.3
                
            if confidence >= self.config['confidence_threshold']:
                # Estimate table properties
                rows, cols = self._estimate_table_dimensions(region_h_lines, region_v_lines)
                
                table_patterns.append(VisualPattern(
                    pattern_type='table',
                    confidence=confidence,
                    bbox=(x, y, x+w, y+h),
                    properties={
                        'rows': rows,
                        'columns': cols,
                        'cell_count': rows * cols
                    }
                ))
                
        return table_patterns
    
    def _has_consistent_cells(self, h_lines: np.ndarray, v_lines: np.ndarray) -> bool:
        """Check if table has consistent cell sizes."""
        # This would analyze line spacing for consistency
        # Simplified implementation for this example
        return True
    
    def _estimate_table_dimensions(self, h_lines: np.ndarray, v_lines: np.ndarray) -> Tuple[int, int]:
        """Estimate number of rows and columns in the table."""
        # Count horizontal and vertical lines
        # In a real implementation, this would do more sophisticated analysis
        # Simplified estimation for this example
        h_projection = np.sum(h_lines, axis=1)
        v_projection = np.sum(v_lines, axis=0)
        
        # Count peaks in projections (where lines are)
        h_peaks = self._count_peaks(h_projection)
        v_peaks = self._count_peaks(v_projection)
        
        # Rows = horizontal lines + 1, Columns = vertical lines + 1
        rows = max(1, h_peaks + 1)
        cols = max(1, v_peaks + 1)
        
        return rows, cols
    
    def _count_peaks(self, projection: np.ndarray) -> int:
        """Count number of peaks in projection."""
        # Simplified peak counting
        threshold = np.max(projection) * 0.5
        peaks = 0
        above_threshold = False
        
        for val in projection:
            if val > threshold and not above_threshold:
                peaks += 1
                above_threshold = True
            elif val <= threshold:
                above_threshold = False
                
        return peaks

    def _detect_forms_heuristic(self, img_np: np.ndarray) -> List[VisualPattern]:
        """Detect forms using heuristic approach."""
        # Forms often have input fields, labels, and buttons
        # This is a simplified implementation
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Find contours of potential input fields (light rectangles)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Count potential input fields
        input_field_candidates = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Input fields typically have certain aspect ratios
            aspect_ratio = w / h if h > 0 else 0
            
            if 3 < aspect_ratio < 10 and h > 20:
                input_field_candidates.append((x, y, w, h))
        
        form_patterns = []
        
        # Group nearby input fields into forms
        if len(input_field_candidates) > 2:
            # Simplified grouping - in reality would use clustering
            min_x = min([x for x, _, _, _ in input_field_candidates])
            min_y = min([y for _, y, _, _ in input_field_candidates])
            max_x = max([x + w for x, _, w, _ in input_field_candidates])
            max_y = max([y + h for _, y, _, h in input_field_candidates])
            
            # Expand form boundary
            padding = 20
            form_x = max(0, min_x - padding)
            form_y = max(0, min_y - padding)
            form_w = max_x - form_x + padding
            form_h = max_y - form_y + padding
            
            # Check for vertical alignment of fields (common in forms)
            is_vertical_form = self._check_vertical_alignment(input_field_candidates)
            
            # Forms often have button-like elements at the bottom
            has_buttons = self._detect_buttons(
                img_np[form_y:form_y+form_h, form_x:form_x+form_w]
            )
            
            confidence = 0.0
            
            if len(input_field_candidates) > 2:
                confidence += 0.3
                
            if is_vertical_form:
                confidence += 0.3
                
            if has_buttons:
                confidence += 0.4
                
            if confidence >= self.config['confidence_threshold']:
                form_patterns.append(VisualPattern(
                    pattern_type='form',
                    confidence=confidence,
                    bbox=(form_x, form_y, form_x+form_w, form_y+form_h),
                    properties={
                        'field_count': len(input_field_candidates),
                        'has_buttons': has_buttons,
                        'is_vertical': is_vertical_form
                    }
                ))
        
        return form_patterns
    
    def _check_vertical_alignment(self, fields: List[Tuple[int, int, int, int]]) -> bool:
        """Check if form fields are vertically aligned."""
        if not fields:
            return False
            
        # Group x-coordinates (allowing for small variations)
        x_coords = [x for x, _, _, _ in fields]
        
        # Check if most fields start at similar x-coordinates
        x_variation = max(x_coords) - min(x_coords)
        
        return x_variation < 50  # Threshold for alignment
    
    def _detect_buttons(self, form_region: np.ndarray) -> bool:
        """Detect button-like elements in a form."""
        # Simplified button detection
        # In reality, would use more sophisticated methods
        
        # Convert to HSV for color-based detection
        hsv = cv2.cvtColor(form_region, cv2.COLOR_BGR2HSV)
        
        # Look for colored rectangles (common for buttons)
        # Simplified by looking for saturated colors
        saturation = hsv[:, :, 1]
        _, thresh = cv2.threshold(saturation, 100, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Button-like aspect ratio and size
            if 2 < w/h < 5 and 30 < w < 200 and 20 < h < 50:
                return True
                
        return False
    
    def _detect_code_blocks_heuristic(self, img_np: np.ndarray) -> List[VisualPattern]:
        """Detect code blocks using heuristic approach."""
        # Code blocks often have consistent indentation and syntax highlighting
        
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to highlight text regions
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        code_block_patterns = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Skip small regions
            if w < 100 or h < 100:
                continue
                
            # Extract region
            region = img_np[y:y+h, x:x+w]
            
            # Check for signs of code:
            # 1. Consistent left margin (indentation pattern)
            has_indentation = self._detect_indentation_pattern(region)
            
            # 2. Check for syntax highlighting (colored text)
            has_syntax_highlighting = self._detect_syntax_highlighting(region)
            
            # 3. Check for monospaced font pattern
            has_monospace_pattern = self._detect_monospace_pattern(region)
            
            confidence = 0.0
            
            if has_indentation:
                confidence += 0.4
                
            if has_syntax_highlighting:
                confidence += 0.4
                
            if has_monospace_pattern:
                confidence += 0.2
                
            if confidence >= self.config['confidence_threshold']:
                code_block_patterns.append(VisualPattern(
                    pattern_type='code_block',
                    confidence=confidence,
                    bbox=(x, y, x+w, y+h),
                    properties={
                        'has_indentation': has_indentation,
                        'has_syntax_highlighting': has_syntax_highlighting,
                        'has_monospace': has_monospace_pattern
                    }
                ))
        
        return code_block_patterns
    
    def _detect_indentation_pattern(self, region: np.ndarray) -> bool:
        """Detect indentation pattern in code block."""
        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Threshold to get text
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Get horizontal projection (sum along rows)
        h_proj = np.sum(thresh, axis=1)
        
        # Find rows with text (non-zero projection)
        text_rows = np.where(h_proj > 0)[0]
        
        if len(text_rows) < 5:  # Need enough lines to detect pattern
            return False
            
        # Get first column with text in each row
        first_text_columns = []
        
        for row in text_rows:
            row_data = thresh[row, :]
            text_cols = np.where(row_data > 0)[0]
            if len(text_cols) > 0:
                first_text_columns.append(text_cols[0])
        
        # Check for consistent indentation patterns
        if len(first_text_columns) < 5:
            return False
            
        # Calculate indentation levels
        indentation_levels = [col // 4 for col in first_text_columns]  # Assuming 4 spaces per indent
        
        # Check for consistent indentation changes
        changes = np.diff(indentation_levels)
        unique_changes = np.unique(changes)
        
        # If we have consistent indentation changes, it's likely code
        return len(unique_changes) <= 2  # Allow for 0 and 1 level changes
    
    def _detect_syntax_highlighting(self, region: np.ndarray) -> bool:
        """Detect syntax highlighting in code block."""
        # Convert to HSV for color analysis
        hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
        
        # Count unique colors (excluding background)
        unique_colors = np.unique(hsv.reshape(-1, 3), axis=0)
        
        # Syntax highlighting typically has multiple colors
        return len(unique_colors) > 5
    
    def _detect_monospace_pattern(self, region: np.ndarray) -> bool:
        """Detect monospaced font pattern in code block."""
        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Threshold to get text
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Get vertical projection
        v_proj = np.sum(thresh, axis=0)
        
        # Find columns with text
        text_cols = np.where(v_proj > 0)[0]
        
        if len(text_cols) < 10:
            return False
            
        # Calculate spacing between text columns
        spacing = np.diff(text_cols)
        
        # Monospaced fonts have consistent spacing
        unique_spacing = np.unique(spacing)
        
        # If we have mostly consistent spacing, it's likely monospaced
        return len(unique_spacing) <= 2
    
    def _detect_ui_components_heuristic(self, img_np: np.ndarray) -> List[VisualPattern]:
        """Detect UI components using heuristic approach."""
        # Convert to grayscale
        gray = cv2.cvtColor(img_np, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        ui_patterns = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Skip very small or very large regions
            if w < 20 or h < 20 or w * h > img_np.shape[0] * img_np.shape[1] * 0.8:
                continue
                
            # Extract region
            region = img_np[y:y+h, x:x+w]
            
            # Check for common UI component patterns
            component_type, confidence = self._classify_ui_component(region)
            
            if confidence >= self.config['confidence_threshold']:
                ui_patterns.append(VisualPattern(
                    pattern_type='ui_component',
                    confidence=confidence,
                    bbox=(x, y, x+w, y+h),
                    properties={
                        'component_type': component_type,
                        'size': (w, h)
                    }
                ))
        
        return ui_patterns
    
    def _classify_ui_component(self, region: np.ndarray) -> Tuple[str, float]:
        """Classify UI component type and return confidence."""
        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Calculate aspect ratio
        h, w = gray.shape
        aspect_ratio = w / h if h > 0 else 0
        
        # Check for common UI component patterns
        if 0.8 <= aspect_ratio <= 1.2 and 20 <= w <= 50 and 20 <= h <= 50:
            return 'button', 0.8
        elif 2 <= aspect_ratio <= 5 and h <= 30:
            return 'input_field', 0.7
        elif 0.1 <= aspect_ratio <= 0.3 and w >= 100:
            return 'menu_item', 0.6
        elif 0.5 <= aspect_ratio <= 2 and w >= 100 and h >= 100:
            return 'panel', 0.7
        else:
            return 'unknown', 0.5

if __name__ == "__main__":
    # Test the multimodal understanding
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create instance
    mmu = MultiModalUnderstanding()
    
    # Test with a sample image
    from PIL import Image
    img = Image.open("test_screen.png")
    
    # Analyze image
    patterns = mmu.analyze_image(img)
    
    # Print results
    for pattern in patterns:
        print(f"Detected {pattern.pattern_type} with confidence {pattern.confidence:.2f}")
        print(f"Bounding box: {pattern.bbox}")
        print(f"Properties: {pattern.properties}")
        print() 