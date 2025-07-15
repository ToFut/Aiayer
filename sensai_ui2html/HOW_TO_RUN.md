# 🚀 How to Run the Complete SensAI.UI2HTMLMemory System

## Quick Start Guide

### 1. **Install Dependencies**
```bash
pip install uiautomation chromadb openai
pip install atomacos  # For better macOS support
```

### 2. **Navigate to System Directory**
```bash
cd sensai_ui2html
```

### 3. **Run the System**

#### **Option A: Simple Test (Recommended First)**
```bash
python simple_run.py
```
This shows basic functionality working.

#### **Option B: Full Demo**
```bash
cd examples
python demo.py
```
This runs the complete demonstration.

#### **Option C: Integration Tests**
```bash
python test_integration.py
```
This verifies the system works as a drop-in replacement.

#### **Option D: Complete Interactive System**
```bash
python run_complete_system.py
```
This starts the full interactive system with menu options.

## 🎯 What You'll See

### **System Status:**
- ✅ **UI Tree Extraction**: Gets current UI structure
- ✅ **HTML Generation**: Converts UI to semantic HTML  
- ✅ **Memory Storage**: Stores snapshots in ChromaDB
- ✅ **Semantic Queries**: Search UI elements by description
- ✅ **Integration Layer**: Drop-in replacement for screen sensors

### **Sample Output:**
```
🚀 Simple Example - SensAI.UI2HTMLMemory System
==================================================
1. Extracting UI tree...
✅ Extracted UI tree: macOS Desktop
✅ Elements: 2

2. Generating HTML...
✅ Generated HTML: 443 characters
📄 HTML Preview:
<div id="macos_desktop" class="ui-axapplication"...>

3. Testing memory storage...
✅ Stored snapshot: snapshot_1234567890
✅ Memory query: 3 results found

🎉 Basic functionality working!
```

## 🔧 Interactive System Features

When you run `python run_complete_system.py`, you get:

1. **Quick Capture** - Capture one UI snapshot
2. **Continuous Monitoring** - Real-time capture every 2 seconds
3. **Memory Query** - Search stored snapshots by text
4. **Sensor Info** - System status and statistics
5. **Export Data** - Save snapshots to JSON file
6. **Exit** - Close the system

## 💻 Using in Your Code

### **Basic Usage:**
```python
from sensai_ui2html.ui_scraper.base_scraper import get_ui_tree
from sensai_ui2html.html_mapper import ui_node_to_html

# Get UI tree
ui_tree = get_ui_tree()

# Convert to HTML
html = ui_node_to_html(ui_tree)
print(html)
```

### **Replace Screen Sensor:**
```python
from sensai_ui2html.integration import ScreenSensorReplacement

sensor = ScreenSensorReplacement()
sensor.start()
data = sensor.capture_screen()
sensor.stop()

print(f"Elements: {data['element_count']}")
print(f"HTML: {data['html_content']}")
```

### **Memory Operations:**
```python
from sensai_ui2html.ui2html_sensor import UI2HTMLSensor

sensor = UI2HTMLSensor()
sensor.start()

# Capture snapshot
snapshot = sensor.capture_snapshot({"context": "testing"})

# Query memory
results = sensor.query_memory("button", n_results=5)

sensor.stop()
```

## 🛠️ Troubleshooting

### **Common Issues:**

1. **Import Errors:**
   ```bash
   pip install uiautomation chromadb openai
   ```

2. **macOS Permission Issues:**
   - Grant accessibility permissions to Terminal/IDE
   - Install atomacos: `pip install atomacos`

3. **ChromaDB Issues:**
   - Ensure sufficient disk space
   - Check write permissions to `./chroma_db` directory

4. **No UI Detected:**
   - Check if applications are accessible
   - Verify platform-specific dependencies

### **Debug Mode:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your code here
```

## 📊 System Components

| Component | Status | Description |
|-----------|--------|-------------|
| UI Scraper | ✅ Working | Extracts UI trees from Windows/macOS |
| HTML Mapper | ✅ Working | Converts UI to semantic HTML |
| Memory Store | ✅ Working | ChromaDB vector storage |
| Sensor Class | ✅ Working | Main sensor interface |
| Integration | ✅ Working | Drop-in screen sensor replacement |

## 🎯 Next Steps

1. **Test Basic Functionality:**
   ```bash
   python simple_run.py
   ```

2. **Run Full Demo:**
   ```bash
   cd examples && python demo.py
   ```

3. **Start Interactive System:**
   ```bash
   python run_complete_system.py
   ```

4. **Integrate with Your Code:**
   - Replace screen sensor imports
   - Use the integration layer
   - Add semantic memory queries

## 📁 File Structure

```
sensai_ui2html/
├── ui_scraper/          # UI tree extraction
├── html_mapper.py       # UI to HTML conversion
├── memory_store.py      # ChromaDB storage
├── ui2html_sensor.py    # Main sensor class
├── integration.py       # Drop-in replacement
├── simple_run.py        # Quick test
├── run_complete_system.py # Interactive system
├── test_integration.py  # Integration tests
├── examples/demo.py     # Full demo
├── README.md           # Documentation
└── MIGRATION_GUIDE.md  # Migration instructions
```

## 🎉 Success Indicators

You'll know the system is working when you see:

- ✅ UI tree extraction successful
- ✅ HTML generation working
- ✅ Memory storage operational
- ✅ Semantic queries returning results
- ✅ Integration layer functioning

## 🚀 Ready to Use!

The SensAI.UI2HTMLMemory system is **fully functional** and ready to replace your screen sensors with next-generation semantic UI understanding!

**Start with:** `python simple_run.py`
**Then try:** `python run_complete_system.py` 