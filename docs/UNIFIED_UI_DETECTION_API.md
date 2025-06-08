# Unified UI Detection API

A comprehensive API for detecting and interacting with UI elements across applications and web pages, with improved accuracy and accessibility.

## Overview

The Unified UI Detection API combines multiple detection methods to accurately identify and characterize UI elements:

1. **Browser API Detection**: Uses Selenium to interact with web browser DOMs directly
2. **Accessibility API Detection**: Leverages system accessibility APIs for better element identification
3. **OCR Detection**: Uses text recognition to identify UI elements from screen content
4. **Computer Vision Detection**: Employs image analysis to detect UI elements visually

The API provides a simple, unified interface that abstracts away the complexity of these different detection methods while giving you access to all the rich information they provide.

## Installation

### Prerequisites

The API has several optional dependencies for different detection methods:

```bash
# Core dependencies
pip install pillow numpy pyautogui

# Browser detection
pip install selenium

# OCR detection
pip install easyocr

# Computer Vision detection
pip install opencv-python

# Platform-specific accessibility APIs
# (varies by platform)
```

## Basic Usage

```python
import asyncio
from unified_ui_detection_api import UnifiedUIDetectionAPI

async def main():
    # Initialize the API
    ui_detection = UnifiedUIDetectionAPI()
    
    # Detect UI elements from current screen
    result = await ui_detection.detect_ui_elements()
    
    # Print number of elements found
    print(f"Found {len(result.elements)} UI elements")
    
    # Print element types found
    type_counts = result.count_by_type()
    for element_type, count in type_counts.items():
        print(f"  - {element_type}: {count}")
    
    # Find a specific button
    search_button = ui_detection.find_element_by_text("Search")
    if search_button:
        print(f"Found search button at {search_button.center_point}")

asyncio.run(main())
```

## API Reference

### `UnifiedUIDetectionAPI` Class

The main class that provides access to all detection functionality.

#### Methods

- `detect_ui_elements(image_path=None, url=None, context=None) -> DetectionResult`: 
  Main method to detect UI elements using all available methods.
  
- `enable_detection_method(method: str, enabled: bool = True)`:
  Enable or disable a specific detection method.
  
- `find_element_by_text(text: str, result=None) -> Optional[UIElement]`:
  Find an element by its text content.
  
- `find_element_by_type(element_type: str, index: int = 0, result=None) -> Optional[UIElement]`:
  Find an element by its type and index.
  
- `find_element_at_position(x: int, y: int, result=None) -> Optional[UIElement]`:
  Find an element at the specified screen position.
  
- `visualize_detection(result: DetectionResult, output_path: str, show_labels: bool = True) -> bool`:
  Create a visualization of the detection result.
  
- `get_latest_result() -> Optional[DetectionResult]`:
  Get the latest detection result.
  
- `load_result(filepath: str) -> DetectionResult`:
  Load a detection result from a file.

### `DetectionResult` Class

Contains the results of a UI element detection operation.

#### Methods

- `to_dict() -> Dict[str, Any]`:
  Convert the result to a dictionary.
  
- `from_dict(data: Dict[str, Any]) -> DetectionResult`:
  Create a detection result from a dictionary.
  
- `get_elements_by_type(element_type: str) -> List[UIElement]`:
  Get all elements of a specific type.
  
- `get_element_by_id(element_id: str) -> Optional[UIElement]`:
  Get an element by its ID.
  
- `get_elements_containing_text(text: str, case_sensitive: bool = False) -> List[UIElement]`:
  Get elements containing the specified text.
  
- `count_by_type() -> Dict[str, int]`:
  Count elements by type.

### `UIElement` Class

Represents a detected UI element with its properties.

#### Properties

- `element_id`: Unique identifier for the element
- `element_type`: Type of UI element (e.g., "button", "textfield")
- `text`: Text content of the element
- `bounding_box`: Screen coordinates as [x1, y1, x2, y2]
- `center_point`: Center coordinates as (x, y)
- `confidence`: Detection confidence (0.0-1.0)
- `role`: Accessibility role of the element
- `state`: Element state (e.g., "enabled", "disabled")
- `properties`: Additional properties dictionary
- `detection_method`: Method used to detect this element
- `can_click`: Whether the element can be clicked
- `can_type`: Whether the element can receive text input
- `can_scroll`: Whether the element can be scrolled

#### Methods

- `to_dict() -> Dict[str, Any]`:
  Convert the element to a dictionary.
  
- `from_dict(data: Dict[str, Any]) -> UIElement`:
  Create an element from a dictionary.

## Examples

### Detecting Elements on a Web Page

```python
import asyncio
from unified_ui_detection_api import UnifiedUIDetectionAPI

async def detect_web_elements():
    ui_detection = UnifiedUIDetectionAPI()
    
    # Only use browser-based detection
    ui_detection.enable_detection_method("ocr", False)
    ui_detection.enable_detection_method("cv", False)
    
    # Detect elements on a web page
    result = await ui_detection.detect_ui_elements(url="https://example.com")
    
    # Find all links
    links = result.get_elements_by_type("link")
    print(f"Found {len(links)} links:")
    for link in links:
        print(f"  - {link.text}")
    
    # Create visualization
    ui_detection.visualize_detection(result, "web_elements.png")

asyncio.run(detect_web_elements())
```

### Analyzing UI from a Screenshot

```python
import asyncio
from unified_ui_detection_api import UnifiedUIDetectionAPI

async def analyze_screenshot(screenshot_path):
    ui_detection = UnifiedUIDetectionAPI()
    
    # Only use image-based detection methods
    ui_detection.enable_detection_method("browser", False)
    
    # Detect elements in the screenshot
    result = await ui_detection.detect_ui_elements(image_path=screenshot_path)
    
    # Find all buttons
    buttons = result.get_elements_by_type("button")
    print(f"Found {len(buttons)} buttons:")
    for button in buttons:
        print(f"  - {button.text} ({button.confidence:.2f})")
    
    # Find a specific element
    search_field = ui_detection.find_element_by_text("Search", result)
    if search_field:
        print(f"Found search field at {search_field.center_point}")

asyncio.run(analyze_screenshot("screenshot.png"))
```

## Command Line Usage

The API can also be used from the command line:

```bash
python unified_ui_detection_api.py --image screenshot.png --visualize
```

Options:
- `--image PATH`: Path to image for analysis
- `--url URL`: URL to analyze
- `--output PATH`: Output file path for JSON results
- `--visualize`: Create visualization
- `--vis-output PATH`: Visualization output path
- `--methods LIST`: Comma-separated list of detection methods to use

## Performance Considerations

- Browser-based detection is the most reliable for web applications but requires a browser instance
- OCR and CV detection are useful for native applications but can be slower
- Accessibility API detection is fast but platform-dependent

You can customize which detection methods are used based on your specific needs.

## Troubleshooting

### Browser Detection Issues

If browser detection fails:
- Ensure Chrome/Firefox is installed
- Check if the browser driver is compatible with your browser version
- Try launching a browser manually before detection

### OCR Detection Issues

If OCR detection is not working:
- Ensure easyocr is installed correctly
- Check that the image is clear and not too small
- Use higher resolution screenshots for better results

### Visualization Issues

If visualization fails:
- Ensure OpenCV is installed correctly
- Check file permissions for the output directory
- Use PNG format for best quality

## Contributing

Contributions are welcome! Areas for improvement include:
- Adding support for more accessibility APIs
- Improving element classification accuracy
- Optimizing performance for real-time applications
- Adding more specialized UI element detectors