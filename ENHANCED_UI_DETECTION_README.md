# Enhanced UI Detection System

A comprehensive UI element detection system that integrates multiple advanced approaches for superior accuracy and reliability.

## Overview

This enhanced system combines the following better approaches for UI element detection:

### 1. 🔍 Accessibility APIs
- **macOS**: Uses Quartz and ApplicationServices frameworks
- **Windows**: Uses Win32 API for accessibility 
- **Linux**: Uses AT-SPI (Assistive Technology Service Provider Interface)
- **Function**: `get_element_role()` returns semantic roles like "button", "textfield", etc.

### 2. 🤖 Machine Learning Models
- **Framework**: Scikit-learn Random Forest Classifier
- **Features**: TF-IDF vectorization of UI text content
- **Function**: `classify_element()` learns UI element patterns
- **Training**: Automatic training on synthetic UI element data

### 3. 🌐 Browser/OS APIs
- **Selenium WebDriver**: Direct DOM element access
- **Chrome DevTools Protocol (CDP)**: Native browser API control
- **Function**: `get_dom_elements()` provides direct UI structure access
- **Capabilities**: Real-time element coordinates, attributes, and states

### 4. 📝 OCR + NLP Understanding
- **OCR**: EasyOCR for text extraction from screenshots
- **NLP**: SpaCy for intent analysis ("Search", "Submit", "Cancel")
- **Functions**: 
  - `extract_text_content()` for OCR
  - `analyze_intent()` for NLP understanding

## Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements_enhanced_ui_detection.txt
```

### 2. Install SpaCy Language Model
```bash
python -m spacy download en_core_web_sm
```

### 3. Platform-Specific Setup

#### macOS
- Accessibility permissions may be required
- Grant Terminal/IDE accessibility permissions in System Preferences

#### Windows
- Install Visual C++ redistributables for pywin32
- Some features may require administrator privileges

#### Linux
- Install AT-SPI development libraries:
```bash
sudo apt-get install python3-pyatspi libatspi2.0-dev
```

### 4. Browser Setup for DOM Access
```bash
# For Chrome automation
pip install webdriver-manager
```

Or download ChromeDriver manually and add to PATH.

## Usage

### Basic Usage
```python
from enhanced_ui_detection_system import EnhancedUIDetectionSystem

# Initialize the detector
detector = EnhancedUIDetectionSystem()

# Analyze a screenshot
app_context = {"app_name": "Chrome", "view_name": "Google Search"}
result = await detector.enhanced_detect_ui_elements("screenshot.png", app_context)

# Access results
print(f"Found {len(result.elements)} elements")
print(f"Detection methods used: {result.detection_methods_used}")

for element in result.elements:
    print(f"- {element.element_type}: {element.element_text}")
    print(f"  Detected by: {element.detected_by}")
    print(f"  Confidence: {element.confidence}")
```

### Individual Component Usage

#### Accessibility API
```python
from enhanced_ui_detection_system import AccessibilityDetector

detector = AccessibilityDetector()
role = detector.get_element_role(x=100, y=200)  # Get role at coordinates
print(f"Element role: {role}")
```

#### Machine Learning Classification
```python
from enhanced_ui_detection_system import MLUIClassifier

classifier = MLUIClassifier()
element_type, confidence = classifier.classify_element("Submit button", "form context")
print(f"Classified as: {element_type} (confidence: {confidence})")
```

#### Browser API Access
```python
from browser_api_integration import BrowserAPIManager

browser = BrowserAPIManager()
browser.connect_to_browser("chrome")
elements = browser.get_native_dom_elements()

for elem in elements:
    print(f"DOM Element: {elem.element_type} at {elem.center_point}")
```

#### OCR + NLP
```python
from enhanced_ui_detection_system import OCRNLPDetector

detector = OCRNLPDetector()
ocr_results = detector.extract_text_content("screenshot.png")
nlp_results = detector.analyze_intent(ocr_results["text"])
print(f"Detected intent: {nlp_results['intent']}")
```

## Enhanced Element Data Structure

The system returns `EnhancedUIElement` objects with comprehensive information:

```python
element = EnhancedUIElement(
    element_id="unique_id",
    element_type="button",
    element_text="Submit",
    bounding_box=[x1, y1, x2, y2],
    center_point=(x, y),
    state="enabled",
    role="button",  # Accessibility role
    confidence=0.95,
    detected_by=["Browser API", "ML", "Accessibility API"],
    accessibility_info={...},
    ml_confidence=0.87,
    ocr_text="Submit",
    nlp_intent="submit",
    dom_attributes={...}
)
```

## Testing

Run the comprehensive test suite:

```bash
python test_enhanced_ui_detection.py
```

This tests all detection methods and provides a detailed report.

## Integration with Existing System

### Replace Existing Detectors
```python
# Old approach
from ui_element_detector import UIElementDetector
detector = UIElementDetector()

# New enhanced approach
from enhanced_ui_detection_system import EnhancedUIDetectionSystem
detector = EnhancedUIDetectionSystem()

# Same interface, better results
result = await detector.enhanced_detect_ui_elements(image_path, context)
```

### Gradual Migration
```python
# Use enhanced detection as fallback
try:
    # Try enhanced detection first
    result = await enhanced_detector.enhanced_detect_ui_elements(image_path)
    if len(result.elements) > 0:
        return result
except Exception:
    # Fallback to original detection
    return await original_detector.detect_ui_elements(image_path)
```

## Architecture

```
EnhancedUIDetectionSystem
├── AccessibilityDetector (Platform-specific APIs)
├── MLUIClassifier (Scikit-learn models)
├── BrowserAPIDetector (Selenium + CDP)
├── OCRNLPDetector (EasyOCR + SpaCy)
└── Integration Layer (Combines all approaches)
```

## Performance Considerations

1. **Parallel Processing**: All detection methods run concurrently
2. **Caching**: ML models and browser connections are cached
3. **Fallbacks**: Graceful degradation if components are unavailable
4. **Efficiency**: Only available detection methods are used

## Accuracy Improvements

The enhanced system provides significant accuracy improvements:

- **Precision**: DOM API provides exact element coordinates
- **Recall**: Multiple detection methods catch different element types
- **Confidence**: Multi-source validation increases reliability
- **Context**: Accessibility and semantic information improves understanding

## Troubleshooting

### Common Issues

1. **Accessibility Permission Denied**
   - Grant accessibility permissions in system settings
   - Run with appropriate privileges

2. **Browser Connection Failed**
   - Ensure Chrome is running with `--remote-debugging-port=9222`
   - Check firewall settings

3. **OCR Not Working**
   - Verify image file exists and is readable
   - Check EasyOCR installation

4. **ML Model Training Failed**
   - Ensure sufficient disk space for model files
   - Check write permissions in models/ directory

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed information about each detection method
```

## Contributing

To add new detection methods:

1. Create a new detector class following the existing patterns
2. Implement the required interface methods
3. Add integration in `EnhancedUIDetectionSystem`
4. Update tests and documentation

## License

[Your license information here]