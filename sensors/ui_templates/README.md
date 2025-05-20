# UI Templates for Alternative Screen Analysis

This directory contains template images of common UI elements for use with the `AlternativeScreenAnalyzer`'s template matching functionality.

## Purpose

These templates help the screen sensor recognize common UI elements across different applications through template matching, which is more reliable than contour-based detection for certain distinctive elements.

## Adding Templates

To add new templates:

1. Capture a clean screenshot of the UI element you want to detect
2. Crop tightly around the element with minimal background
3. Save as PNG or JPG with a descriptive name (e.g., `button_close.png`, `dropdown_arrow.png`)
4. Place in this directory

## Supported Elements

Common UI elements that work well as templates:

- Buttons (especially those with distinctive icons)
- Navigation elements
- Toggle switches
- Scrollbars
- Tab indicators
- Menu icons
- Dropdown arrows
- Checkboxes and radio buttons
- Window controls (minimize, maximize, close)

## Recommendations

- Keep templates small (ideally under 100x100 pixels)
- Use PNG format for elements with transparency
- Include only the distinctive part of the element
- Consider multiple variations of the same element (e.g., button in different states)
- Name files clearly to indicate the element type and purpose

The AlternativeScreenAnalyzer will automatically load all template images in this directory during initialization.