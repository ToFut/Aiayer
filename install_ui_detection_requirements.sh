#!/bin/bash

# Install UI Detection Requirements
# Sets up all dependencies needed for enhanced UI detection

echo "🔧 Installing UI Detection Requirements..."

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 Detected macOS"
    
    # Install Tesseract OCR via Homebrew
    if command -v brew >/dev/null 2>&1; then
        echo "📦 Installing Tesseract OCR via Homebrew..."
        brew install tesseract
    else
        echo "⚠️ Homebrew not found. Please install Tesseract manually:"
        echo "   Visit: https://github.com/tesseract-ocr/tesseract"
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🐧 Detected Linux"
    
    # Try different package managers
    if command -v apt-get >/dev/null 2>&1; then
        echo "📦 Installing Tesseract OCR via apt..."
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
    elif command -v yum >/dev/null 2>&1; then
        echo "📦 Installing Tesseract OCR via yum..."
        sudo yum install -y tesseract tesseract-langpack-eng
    elif command -v pacman >/dev/null 2>&1; then
        echo "📦 Installing Tesseract OCR via pacman..."
        sudo pacman -S tesseract tesseract-data-eng
    else
        echo "⚠️ Unknown package manager. Please install Tesseract manually:"
        echo "   Ubuntu/Debian: sudo apt-get install tesseract-ocr"
        echo "   CentOS/RHEL: sudo yum install tesseract"
    fi
    
else
    echo "❓ Unknown OS. Please install Tesseract OCR manually."
fi

# Install Python packages
echo "🐍 Installing Python packages..."

# Core computer vision packages
pip3 install opencv-python numpy pillow

# OCR package
pip3 install pytesseract

# Machine learning (optional but recommended)
pip3 install scikit-learn

# UI automation packages
pip3 install pyautogui pynput

# WebSocket for real-time communication
pip3 install websockets

# Additional useful packages
pip3 install matplotlib  # For debugging visualizations

echo ""
echo "✅ Installation complete!"
echo ""

# Test installations
echo "🧪 Testing installations..."

# Test OpenCV
python3 -c "import cv2; print(f'✅ OpenCV: {cv2.__version__}')" 2>/dev/null || echo "❌ OpenCV installation failed"

# Test Tesseract
python3 -c "import pytesseract; print('✅ Tesseract OCR: Available')" 2>/dev/null || echo "❌ Tesseract installation failed"

# Test scikit-learn
python3 -c "import sklearn; print(f'✅ Scikit-learn: {sklearn.__version__}')" 2>/dev/null || echo "❌ Scikit-learn installation failed"

# Test PyAutoGUI
python3 -c "import pyautogui; print('✅ PyAutoGUI: Available')" 2>/dev/null || echo "❌ PyAutoGUI installation failed"

# Test WebSocket
python3 -c "import websockets; print('✅ WebSocket: Available')" 2>/dev/null || echo "❌ WebSocket installation failed"

echo ""
echo "🎯 Next Steps:"
echo "   1. Run: python3 compare_detection_methods.py"
echo "   2. Run: python3 enhanced_ui_detection_engine.py" 
echo "   3. Run: ./start_teamviewer_ui_test.sh"
echo ""
echo "📚 Read: UI_DETECTION_EXPLAINED.md for detailed explanation"