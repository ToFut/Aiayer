#!/usr/bin/env python3
"""
Generate sample screenshots for the advanced DO button examination framework
This script creates realistic UI mockups for testing agent's UI understanding
"""
import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
import random

# Define constants
SCREENSHOTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Font paths for different platforms
FONT_PATHS = {
    'linux': [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
    ],
    'darwin': [  # macOS
        '/System/Library/Fonts/Helvetica.ttc',
        '/Library/Fonts/Arial.ttf',
        '/System/Library/Fonts/SFNSText.ttf'
    ],
    'win32': [
        'C:\\Windows\\Fonts\\arial.ttf',
        'C:\\Windows\\Fonts\\segoeui.ttf'
    ]
}

def find_font():
    """Find an available font on the system"""
    platform = sys.platform
    
    # Check platform-specific font paths
    if platform in FONT_PATHS:
        for path in FONT_PATHS[platform]:
            if os.path.exists(path):
                return path
    
    # If no font found, return None (will use default)
    return None

def create_browser_search_screenshot():
    """Create a screenshot of a browser search interface"""
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw browser chrome
    draw.rectangle([(0, 0), (800, 40)], fill=(240, 240, 240))
    draw.line([(0, 40), (800, 40)], fill=(200, 200, 200), width=1)
    
    # Draw address bar
    draw.rectangle([(50, 8), (650, 32)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((60, 12), "https://www.searchengine.com", fill=(0, 0, 0), font=small_font)
    
    # Draw logo
    draw.text((80, 70), "SearchEngine", fill=(66, 133, 244), font=large_font)
    
    # Draw search box
    draw.rectangle([(80, 120), (700, 160)], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    draw.text((100, 132), "Search here...", fill=(150, 150, 150), font=medium_font)
    
    # Add search button
    draw.rectangle([(650, 120), (700, 160)], fill=(66, 133, 244), outline=(66, 133, 244))
    draw.text((660, 132), "Search", fill=(255, 255, 255), font=medium_font)
    
    # Add some suggested searches
    draw.text((100, 180), "Suggested searches:", fill=(100, 100, 100), font=small_font)
    suggestions = ["latest news", "weather forecast", "sports results", "technology trends"]
    for i, suggestion in enumerate(suggestions):
        draw.text((100, 210 + i*30), suggestion, fill=(66, 133, 244), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "browser_search.png")
    img.save(output_path)
    print(f"Created browser search screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'search_box': (390, 140),  # center of the search box
        'search_button': (675, 140)  # center of the search button
    }

def create_email_compose_screenshot():
    """Create a screenshot of an email composition interface"""
    img = Image.new('RGB', (800, 600), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw email app header
    draw.rectangle([(0, 0), (800, 50)], fill=(25, 118, 210))
    draw.text((30, 15), "Email Client", fill=(255, 255, 255), font=large_font)
    
    # Draw sidebar
    draw.rectangle([(0, 50), (200, 600)], fill=(255, 255, 255))
    
    # Draw compose button
    draw.rectangle([(30, 80), (170, 110)], fill=(255, 152, 0), outline=(255, 152, 0))
    draw.text((60, 87), "Compose", fill=(255, 255, 255), font=medium_font)
    
    # Draw folders
    folders = ["Inbox", "Sent", "Drafts", "Trash"]
    for i, folder in enumerate(folders):
        draw.text((30, 150 + i*40), folder, fill=(0, 0, 0), font=medium_font)
    
    # Draw compose area
    draw.rectangle([(220, 70), (780, 580)], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((250, 85), "New Message", fill=(0, 0, 0), font=large_font)
    
    # Draw form fields
    form_labels = ["To:", "Subject:", ""]
    y_positions = [140, 190, 240]
    
    for i, label in enumerate(form_labels):
        draw.text((250, y_positions[i]), label, fill=(0, 0, 0), font=medium_font)
        if i < 2:  # Don't draw line for message body
            draw.line([(310, y_positions[i] + 25), (750, y_positions[i] + 25)], fill=(200, 200, 200), width=1)
    
    # Draw send button
    draw.rectangle([(250, 500), (330, 530)], fill=(25, 118, 210), outline=(25, 118, 210))
    draw.text((275, 507), "Send", fill=(255, 255, 255), font=medium_font)
    
    # Draw discard button
    draw.rectangle([(350, 500), (430, 530)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((370, 507), "Discard", fill=(0, 0, 0), font=medium_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "email_compose.png")
    img.save(output_path)
    print(f"Created email compose screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'compose_button': (100, 95),  # center of compose button
        'to_field': (530, 140),  # center of To field
        'subject_field': (530, 190),  # center of Subject field
        'body_field': (500, 350),  # center of body field
        'send_button': (290, 515)  # center of send button
    }

def create_spreadsheet_screenshot():
    """Create a screenshot of a spreadsheet interface"""
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw spreadsheet header
    draw.rectangle([(0, 0), (800, 40)], fill=(48, 145, 58))
    draw.text((30, 10), "Spreadsheet App", fill=(255, 255, 255), font=large_font)
    
    # Draw toolbar
    draw.rectangle([(0, 40), (800, 80)], fill=(240, 240, 240))
    toolbar_items = ["File", "Edit", "View", "Insert", "Format", "Data", "Tools", "Help"]
    for i, item in enumerate(toolbar_items):
        draw.text((50 + i*90, 55), item, fill=(0, 0, 0), font=small_font)
    
    # Draw formula bar
    draw.rectangle([(0, 80), (800, 110)], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((20, 90), "fx", fill=(0, 0, 0), font=medium_font)
    draw.rectangle([(50, 85), (750, 105)], fill=(255, 255, 255), outline=(200, 200, 200))
    
    # Draw column headers
    columns = ["A", "B", "C", "D", "E", "F"]
    for i, col in enumerate(columns):
        draw.rectangle([(50 + i*100, 110), (150 + i*100, 140)], fill=(240, 240, 240), outline=(220, 220, 220))
        draw.text((90 + i*100, 120), col, fill=(0, 0, 0), font=small_font)
    
    # Draw row headers
    for i in range(1, 11):
        draw.rectangle([(20, 140 + i*30), (50, 170 + i*30)], fill=(240, 240, 240), outline=(220, 220, 220))
        draw.text((35, 150 + i*30), str(i), fill=(0, 0, 0), font=small_font)
    
    # Draw grid
    for i in range(6):
        for j in range(10):
            draw.rectangle([(50 + i*100, 140 + j*30), (150 + i*100, 170 + j*30)], fill=(255, 255, 255), outline=(220, 220, 220))
    
    # Add some data
    data = [
        ("Product", "Units Sold", "Price", "Revenue"),
        ("Product A", "", "$10.99", ""),
        ("Product B", "", "$15.50", ""),
        ("Product C", "", "$8.75", "")
    ]
    
    for i, row in enumerate(data):
        for j, cell in enumerate(row):
            draw.text((60 + j*100, 150 + i*30), cell, fill=(0, 0, 0), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "spreadsheet.png")
    img.save(output_path)
    print(f"Created spreadsheet screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'cell_b2': (150, 180),  # center of B2 cell (Product A units)
        'cell_b3': (150, 210),  # center of B3 cell (Product B units)
        'cell_b4': (150, 240)   # center of B4 cell (Product C units)
    }

def create_calendar_screenshot():
    """Create a screenshot of a calendar interface"""
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw calendar header
    draw.rectangle([(0, 0), (800, 50)], fill=(66, 133, 244))
    draw.text((30, 15), "Calendar App", fill=(255, 255, 255), font=large_font)
    
    # Draw new event button
    draw.rectangle([(30, 70), (180, 100)], fill=(255, 64, 129), outline=(255, 64, 129))
    draw.text((60, 77), "New Event", fill=(255, 255, 255), font=medium_font)
    
    # Draw calendar navigation
    draw.text((250, 80), "October 2023", fill=(0, 0, 0), font=large_font)
    draw.rectangle([(460, 80), (490, 100)], fill=(240, 240, 240), outline=(200, 200, 200))
    draw.text((470, 82), "<", fill=(0, 0, 0), font=medium_font)
    draw.rectangle([(500, 80), (530, 100)], fill=(240, 240, 240), outline=(200, 200, 200))
    draw.text((510, 82), ">", fill=(0, 0, 0), font=medium_font)
    
    # Draw day labels
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for i, day in enumerate(days):
        draw.text((60 + i*100, 130), day, fill=(100, 100, 100), font=small_font)
    
    # Draw calendar grid
    calendar_days = [
        ["1", "2", "3", "4", "5", "6", "7"],
        ["8", "9", "10", "11", "12", "13", "14"],
        ["15", "16", "17", "18", "19", "20", "21"],
        ["22", "23", "24", "25", "26", "27", "28"],
        ["29", "30", "31", " ", " ", " ", " "]
    ]
    
    for week in range(5):
        for day in range(7):
            x1, y1 = 30 + day*100, 150 + week*80
            x2, y2 = 130 + day*100, 230 + week*80
            draw.rectangle([(x1, y1), (x2, y2)], fill=(255, 255, 255), outline=(220, 220, 220))
            draw.text((x1 + 10, y1 + 10), calendar_days[week][day], fill=(0, 0, 0), font=small_font)
            
            # Add some random events
            if random.random() < 0.3 and calendar_days[week][day].strip():
                event_colors = [(76, 175, 80), (255, 152, 0), (233, 30, 99)]
                color = random.choice(event_colors)
                draw.rectangle([(x1 + 10, y1 + 40), (x2 - 10, y1 + 60)], fill=color, outline=color)
                draw.text((x1 + 15, y1 + 43), "Event", fill=(255, 255, 255), font=small_font)
    
    # Highlight next Monday (for the test)
    monday_pos = (1, 0)  # Week 1, Monday position
    x1, y1 = 30 + monday_pos[1]*100, 150 + monday_pos[0]*80
    x2, y2 = 130 + monday_pos[1]*100, 230 + monday_pos[0]*80
    draw.rectangle([(x1, y1), (x2, y2)], fill=(232, 240, 254), outline=(66, 133, 244), width=2)
    
    # Draw new event dialog
    draw.rectangle([(250, 150), (550, 450)], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    draw.text((270, 170), "Create Event", fill=(0, 0, 0), font=large_font)
    
    # Draw form fields
    fields = ["Title:", "Date:", "Time:", "Duration:"]
    for i, field in enumerate(fields):
        draw.text((270, 220 + i*50), field, fill=(0, 0, 0), font=medium_font)
        draw.rectangle([(350, 215 + i*50), (530, 245 + i*50)], fill=(255, 255, 255), outline=(200, 200, 200))
    
    # Draw save button
    draw.rectangle([(450, 400), (530, 430)], fill=(66, 133, 244), outline=(66, 133, 244))
    draw.text((475, 407), "Save", fill=(255, 255, 255), font=medium_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "calendar.png")
    img.save(output_path)
    print(f"Created calendar screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'new_event_button': (105, 85),  # center of new event button
        'event_title': (440, 230),  # center of title field
        'date_field': (440, 280),  # center of date field
        'next_monday': (80, 190),  # position of next Monday
        'time_field': (440, 330),  # center of time field
        'duration_field': (440, 380),  # center of duration field
        'save_button': (490, 415)  # center of save button
    }

def create_social_media_screenshot():
    """Create a screenshot of a social media posting interface"""
    img = Image.new('RGB', (800, 600), color=(240, 242, 245))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw header
    draw.rectangle([(0, 0), (800, 60)], fill=(59, 89, 152))
    draw.text((30, 20), "Social Media", fill=(255, 255, 255), font=large_font)
    
    # Draw search bar
    draw.rectangle([(300, 15), (550, 45)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((320, 22), "Search...", fill=(150, 150, 150), font=small_font)
    
    # Draw left sidebar
    sidebar_items = ["News Feed", "Messenger", "Watch", "Marketplace", "Groups"]
    for i, item in enumerate(sidebar_items):
        draw.text((40, 100 + i*40), item, fill=(0, 0, 0), font=medium_font)
    
    # Draw post creation area
    draw.rectangle([(200, 80), (700, 220)], fill=(255, 255, 255), outline=(220, 220, 220), width=1)
    draw.ellipse([(220, 100), (260, 140)], fill=(200, 200, 200))  # Profile picture
    draw.text((280, 110), "What's on your mind?", fill=(100, 100, 100), font=medium_font)
    
    # Draw post field
    draw.rectangle([(220, 150), (680, 180)], fill=(245, 246, 247), outline=(220, 220, 220))
    
    # Draw post buttons
    draw.line([(200, 190), (700, 190)], fill=(220, 220, 220), width=1)
    buttons = ["Photo/Video", "Tag Friends", "Feeling/Activity"]
    for i, button in enumerate(buttons):
        x_pos = 270 + i * 150
        draw.text((x_pos, 197), button, fill=(100, 100, 100), font=small_font)
    
    # Draw publish button
    draw.rectangle([(600, 150), (680, 180)], fill=(59, 89, 152), outline=(59, 89, 152))
    draw.text((620, 157), "Publish", fill=(255, 255, 255), font=small_font)
    
    # Draw some posts
    for i in range(2):
        y_offset = 240 + i * 180
        
        # Post container
        draw.rectangle([(200, y_offset), (700, y_offset + 160)], fill=(255, 255, 255), outline=(220, 220, 220), width=1)
        
        # User info
        draw.ellipse([(220, y_offset + 20), (250, y_offset + 50)], fill=(200, 200, 200))
        draw.text((260, y_offset + 25), f"User {i+1}", fill=(59, 89, 152), font=medium_font)
        draw.text((260, y_offset + 45), "2h ago", fill=(150, 150, 150), font=small_font)
        
        # Post content
        post_texts = [
            "Just had an amazing day at the beach! The weather was perfect! #summer #beach",
            "Check out this new book I'm reading. Highly recommended! #reading #books"
        ]
        draw.text((220, y_offset + 70), post_texts[i], fill=(0, 0, 0), font=small_font)
        
        # Like, comment, share
        draw.line([(200, y_offset + 120), (700, y_offset + 120)], fill=(220, 220, 220), width=1)
        actions = ["Like", "Comment", "Share"]
        for j, action in enumerate(actions):
            x_pos = 270 + j * 150
            draw.text((x_pos, y_offset + 130), action, fill=(100, 100, 100), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "social_media.png")
    img.save(output_path)
    print(f"Created social media screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'post_field': (450, 165),  # center of post field
        'publish_button': (640, 165)  # center of publish button
    }

def create_file_explorer_screenshot():
    """Create a screenshot of a file explorer interface"""
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw file explorer header
    draw.rectangle([(0, 0), (800, 50)], fill=(27, 94, 32))
    draw.text((30, 15), "File Explorer", fill=(255, 255, 255), font=large_font)
    
    # Draw toolbar
    draw.rectangle([(0, 50), (800, 90)], fill=(240, 240, 240))
    toolbar_items = ["File", "Edit", "View", "Tools", "Help"]
    for i, item in enumerate(toolbar_items):
        draw.text((50 + i*80, 65), item, fill=(0, 0, 0), font=small_font)
    
    # Draw navigation buttons
    draw.rectangle([(500, 60), (540, 80)], fill=(220, 220, 220), outline=(200, 200, 200))
    draw.text((515, 62), "<", fill=(0, 0, 0), font=medium_font)
    draw.rectangle([(550, 60), (590, 80)], fill=(220, 220, 220), outline=(200, 200, 200))
    draw.text((565, 62), ">", fill=(0, 0, 0), font=medium_font)
    
    # Draw address bar
    draw.rectangle([(50, 100), (750, 130)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((70, 107), "C:\\Users\\User\\Documents", fill=(0, 0, 0), font=small_font)
    
    # Draw sidebar
    draw.rectangle([(0, 140), (200, 600)], fill=(245, 245, 245))
    sidebar_items = ["Quick Access", "Desktop", "Documents", "Downloads", "Music", "Pictures", "Videos"]
    for i, item in enumerate(sidebar_items):
        draw.text((30, 160 + i*40), item, fill=(0, 0, 0), font=small_font)
    
    # Draw new folder button
    draw.rectangle([(230, 150), (350, 180)], fill=(27, 94, 32), outline=(27, 94, 32))
    draw.text((250, 157), "New Folder", fill=(255, 255, 255), font=small_font)
    
    # Draw file list header
    draw.rectangle([(220, 190), (780, 220)], fill=(240, 240, 240), outline=(220, 220, 220))
    header_items = ["Name", "Date modified", "Type", "Size"]
    for i, item in enumerate(header_items):
        draw.text((250 + i*140, 200), item, fill=(0, 0, 0), font=small_font)
    
    # Draw files and folders
    items = [
        ("Documents", "9/25/2023 10:30 AM", "Folder", ""),
        ("quarterly_report.docx", "9/20/2023 3:45 PM", "Microsoft Word Document", "25 KB"),
        ("budget.xlsx", "9/15/2023 2:10 PM", "Microsoft Excel Worksheet", "42 KB"),
        ("presentation.pptx", "9/10/2023 11:20 AM", "Microsoft PowerPoint Presentation", "1.2 MB"),
        ("notes.txt", "9/5/2023 9:15 AM", "Text Document", "2 KB")
    ]
    
    for i, item in enumerate(items):
        y_pos = 230 + i * 40
        draw.rectangle([(220, y_pos), (780, y_pos + 30)], fill=(255, 255, 255), outline=(240, 240, 240))
        for j, field in enumerate(item):
            draw.text((250 + j*140, y_pos + 5), field, fill=(0, 0, 0), font=small_font)
    
    # Highlight the document to be moved
    draw.rectangle([(220, 270), (780, 300)], fill=(232, 240, 254), outline=(66, 133, 244), width=1)
    
    # Draw move to button
    draw.rectangle([(400, 150), (500, 180)], fill=(255, 152, 0), outline=(255, 152, 0))
    draw.text((420, 157), "Move to", fill=(255, 255, 255), font=small_font)
    
    # Draw move dialog
    draw.rectangle([(300, 320), (600, 550)], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    draw.text((320, 340), "Move to Folder", fill=(0, 0, 0), font=large_font)
    
    # Draw folder list in dialog
    folders = ["Desktop", "Documents", "Downloads", "Project Files", "Archive"]
    for i, folder in enumerate(folders):
        y_pos = 380 + i * 30
        if folder == "Project Files":  # Highlight target folder
            draw.rectangle([(320, y_pos - 5), (580, y_pos + 25)], fill=(232, 240, 254), outline=(66, 133, 244), width=1)
        draw.text((340, y_pos), folder, fill=(0, 0, 0), font=small_font)
    
    # Draw confirm button
    draw.rectangle([(490, 500), (580, 530)], fill=(27, 94, 32), outline=(27, 94, 32))
    draw.text((510, 507), "Confirm", fill=(255, 255, 255), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "file_explorer.png")
    img.save(output_path)
    print(f"Created file explorer screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'new_folder_button': (290, 165),  # center of new folder button
        'folder_name_field': (450, 380),  # position where folder name would be entered
        'create_button': (470, 450),  # position of create button (not shown in UI but needed for test)
        'quarterly_report_file': (400, 285),  # center of the highlighted file
        'move_to_button': (450, 165),  # center of move to button
        'project_files_folder': (450, 440),  # center of Project Files folder option
        'confirm_move_button': (535, 515)  # center of confirm button
    }

def create_code_editor_screenshot():
    """Create a screenshot of a code editor interface"""
    img = Image.new('RGB', (800, 600), color=(40, 44, 52))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw code editor header
    draw.rectangle([(0, 0), (800, 40)], fill=(30, 34, 42))
    draw.text((30, 10), "Code Editor", fill=(255, 255, 255), font=medium_font)
    
    # Draw toolbar
    draw.rectangle([(0, 40), (800, 70)], fill=(50, 54, 62))
    toolbar_items = ["File", "Edit", "View", "Navigate", "Code", "Refactor", "Build", "Debug", "Tools"]
    for i, item in enumerate(toolbar_items):
        draw.text((30 + i*80, 50), item, fill=(200, 200, 200), font=small_font)
    
    # Draw sidebar with file tree
    draw.rectangle([(0, 70), (200, 600)], fill=(40, 44, 52))
    draw.text((20, 90), "Project Explorer", fill=(200, 200, 200), font=small_font)
    
    # Draw file tree
    files = [
        "├ src/",
        "│  ├ main.js",
        "│  ├ utils.js",
        "│  └ components/",
        "│     ├ App.js",
        "│     ├ Header.js",
        "│     └ Footer.js",
        "├ tests/",
        "│  ├ main.test.js",
        "│  └ utils.test.js",
        "├ package.json",
        "└ README.md"
    ]
    
    for i, file in enumerate(files):
        draw.text((20, 120 + i*20), file, fill=(180, 180, 180), font=small_font)
    
    # Draw search icon
    draw.rectangle([(730, 45), (760, 65)], fill=(70, 74, 82))
    draw.text((740, 47), "🔍", fill=(200, 200, 200), font=small_font)
    
    # Draw code content
    code_lines = [
        "// utils.js - Utility functions for the application",
        "",
        "/**",
        " * Format currency value with appropriate symbol",
        " * @param {number} value - The value to format",
        " * @param {string} currency - Currency code (USD, EUR, etc)",
        " * @returns {string} Formatted currency string",
        " */",
        "export function formatCurrency(value, currency = 'USD') {",
        "  const symbols = {",
        "    USD: '$',",
        "    EUR: '€',",
        "    GBP: '£',",
        "    JPY: '¥'",
        "  };",
        "",
        "  const symbol = symbols[currency] || '$';",
        "  return `${symbol}${value.toFixed(2)}`;",
        "}",
        "",
        "/**",
        " * Calculate total price from an array of items",
        " */",
        "export function calculateTotal(items, taxRate = 0.1) {",
        "  const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);",
        "  const tax = subtotal * taxRate;",
        "  return subtotal + tax;",
        "}",
        "",
        "export function formatDate(date) {",
        "  return new Date(date).toLocaleDateString();",
        "}"
    ]
    
    # Draw line numbers and code
    for i, line in enumerate(code_lines):
        line_number = i + 1
        # Line number background
        draw.rectangle([(200, 70 + i*20), (230, 90 + i*20)], fill=(30, 34, 42))
        # Line number text
        draw.text((210, 70 + i*20), str(line_number), fill=(100, 100, 100), font=small_font)
        
        # Syntax highlighting (simple version)
        if "function" in line:
            # Function declaration
            parts = line.split("function ")
            draw.text((240, 70 + i*20), parts[0] + "function ", fill=(220, 220, 170), font=small_font)
            draw.text((240 + draw.textlength(parts[0] + "function ", font=small_font), 70 + i*20), 
                      parts[1], fill=(97, 175, 239), font=small_font)
        elif line.strip().startswith("//") or line.strip().startswith("*"):
            # Comments
            draw.text((240, 70 + i*20), line, fill=(117, 113, 94), font=small_font)
        elif "return" in line:
            # Return statement
            parts = line.split("return ")
            draw.text((240, 70 + i*20), parts[0] + "return ", fill=(198, 120, 221), font=small_font)
            draw.text((240 + draw.textlength(parts[0] + "return ", font=small_font), 70 + i*20), 
                      parts[1], fill=(152, 195, 121), font=small_font)
        else:
            # Regular code
            draw.text((240, 70 + i*20), line, fill=(171, 178, 191), font=small_font)
    
    # Highlight the function we want to add a comment to
    y_start = 70 + 22 * 20  # Line 23 (calculateTotal function)
    draw.rectangle([(200, y_start - 2), (700, y_start + 18)], outline=(97, 175, 239), width=1)
    
    # Draw search results popup
    draw.rectangle([(300, 100), (600, 200)], fill=(50, 54, 62), outline=(70, 74, 82))
    draw.text((320, 110), "Search Results for: calculateTotal", fill=(200, 200, 200), font=small_font)
    
    search_results = [
        "utils.js:23: export function calculateTotal(items, taxRate = 0.1) {",
        "main.js:45: const total = calculateTotal(cartItems, TAX_RATE);",
        "App.js:78: this.setState({ total: calculateTotal(this.state.items) });"
    ]
    
    for i, result in enumerate(search_results):
        if i == 0:  # Highlight the first result
            draw.rectangle([(310, 140 + i*20), (590, 160 + i*20)], fill=(70, 74, 82))
        draw.text((320, 140 + i*20), result, fill=(200, 200, 200), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "code_editor.png")
    img.save(output_path)
    print(f"Created code editor screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'search_icon': (745, 55),  # center of search icon
        'search_field': (450, 110),  # center of search field in popup
        'search_result': (450, 150),  # center of first search result
        'line_before_function': (300, 450),  # position before the calculateTotal function
        'editor': (400, 450)  # general position in the editor
    }

def create_shopping_cart_screenshot():
    """Create a screenshot of a shopping cart interface"""
    img = Image.new('RGB', (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw shop header
    draw.rectangle([(0, 0), (800, 70)], fill=(25, 118, 210))
    draw.text((40, 25), "Online Store", fill=(255, 255, 255), font=large_font)
    
    # Draw navigation menu
    nav_items = ["Home", "Products", "Categories", "Deals", "Contact"]
    for i, item in enumerate(nav_items):
        draw.text((250 + i*100, 27), item, fill=(255, 255, 255), font=medium_font)
    
    # Draw cart icon
    draw.text((750, 25), "🛒", fill=(255, 255, 255), font=large_font)
    
    # Draw search bar
    draw.rectangle([(200, 90), (600, 120)], fill=(255, 255, 255), outline=(200, 200, 200))
    draw.text((220, 97), "Search for products...", fill=(150, 150, 150), font=small_font)
    
    # Draw category sidebar
    draw.rectangle([(20, 150), (180, 580)], fill=(240, 240, 240))
    draw.text((30, 170), "Categories", fill=(0, 0, 0), font=medium_font)
    
    categories = ["Electronics", "Clothing", "Home & Garden", "Books", "Toys", "Beauty", "Sports"]
    for i, category in enumerate(categories):
        draw.text((40, 210 + i*40), category, fill=(60, 60, 60), font=small_font)
    
    # Draw product grid
    products = [
        ("Wireless Headphones", "$79.99"),
        ("Smartphone Case", "$19.99"),
        ("Bluetooth Speaker", "$49.99"),
        ("USB-C Cable", "$12.99")
    ]
    
    for i, product in enumerate(products):
        row, col = i // 2, i % 2
        x1 = 220 + col * 280
        y1 = 150 + row * 200
        x2 = x1 + 250
        y2 = y1 + 180
        
        # Product card
        draw.rectangle([(x1, y1), (x2, y2)], fill=(255, 255, 255), outline=(220, 220, 220))
        
        # Product image placeholder
        draw.rectangle([(x1 + 20, y1 + 20), (x2 - 20, y1 + 100)], fill=(240, 240, 240))
        
        # Product info
        draw.text((x1 + 20, y1 + 110), product[0], fill=(0, 0, 0), font=small_font)
        draw.text((x1 + 20, y1 + 130), product[1], fill=(25, 118, 210), font=medium_font)
        
        # Add to cart button
        if i == 0:  # Highlight the first product (headphones)
            draw.rectangle([(x1 + 20, y1 + 150), (x2 - 20, y1 + 170)], fill=(76, 175, 80), outline=(76, 175, 80))
            draw.text((x1 + 35, y1 + 152), "Add to Cart", fill=(255, 255, 255), font=small_font)
        else:
            draw.rectangle([(x1 + 20, y1 + 150), (x2 - 20, y1 + 170)], fill=(25, 118, 210), outline=(25, 118, 210))
            draw.text((x1 + 35, y1 + 152), "Add to Cart", fill=(255, 255, 255), font=small_font)
    
    # Draw cart popup
    draw.rectangle([(500, 150), (750, 350)], fill=(255, 255, 255), outline=(200, 200, 200), width=2)
    draw.text((520, 170), "Your Cart", fill=(0, 0, 0), font=medium_font)
    
    # Draw cart items
    draw.line([(500, 200), (750, 200)], fill=(220, 220, 220), width=1)
    draw.text((520, 210), "Wireless Headphones", fill=(0, 0, 0), font=small_font)
    draw.text((520, 230), "1 × $79.99", fill=(100, 100, 100), font=small_font)
    
    # Draw cart summary
    draw.line([(500, 260), (750, 260)], fill=(220, 220, 220), width=1)
    draw.text((520, 270), "Subtotal:", fill=(0, 0, 0), font=small_font)
    draw.text((670, 270), "$79.99", fill=(0, 0, 0), font=small_font)
    draw.text((520, 290), "Shipping:", fill=(0, 0, 0), font=small_font)
    draw.text((670, 290), "$5.99", fill=(0, 0, 0), font=small_font)
    draw.text((520, 310), "Total:", fill=(0, 0, 0), font=medium_font)
    draw.text((670, 310), "$85.98", fill=(25, 118, 210), font=medium_font)
    
    # Draw buttons
    draw.rectangle([(550, 340), (650, 370)], fill=(25, 118, 210), outline=(25, 118, 210))
    draw.text((570, 347), "Checkout", fill=(255, 255, 255), font=small_font)
    
    draw.rectangle([(660, 340), (740, 370)], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((670, 347), "Continue", fill=(0, 0, 0), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "shopping_cart.png")
    img.save(output_path)
    print(f"Created shopping cart screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'headphones_product': (330, 200),  # center of headphones product card
        'add_to_cart_button': (330, 320),  # center of add to cart button
        'view_cart_button': (750, 25),  # position of cart icon
        'checkout_button': (600, 355)  # center of checkout button
    }

def create_pdf_form_screenshot():
    """Create a screenshot of a PDF form interface"""
    img = Image.new('RGB', (800, 600), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw PDF viewer header
    draw.rectangle([(0, 0), (800, 50)], fill=(35, 35, 35))
    draw.text((30, 15), "PDF Viewer", fill=(255, 255, 255), font=large_font)
    
    # Draw toolbar
    draw.rectangle([(0, 50), (800, 80)], fill=(60, 60, 60))
    toolbar_items = ["File", "Edit", "View", "Tools", "Window", "Help"]
    for i, item in enumerate(toolbar_items):
        draw.text((50 + i*80, 60), item, fill=(220, 220, 220), font=small_font)
    
    # Draw zoom controls
    draw.rectangle([(650, 55), (700, 75)], fill=(80, 80, 80))
    draw.text((660, 58), "100%", fill=(255, 255, 255), font=small_font)
    
    # Draw page navigation
    draw.rectangle([(720, 55), (740, 75)], fill=(80, 80, 80))
    draw.text((726, 58), "<", fill=(255, 255, 255), font=small_font)
    draw.rectangle([(745, 55), (765, 75)], fill=(80, 80, 80))
    draw.text((751, 58), ">", fill=(255, 255, 255), font=small_font)
    
    # Draw PDF page
    draw.rectangle([(50, 100), (750, 550)], fill=(255, 255, 255), outline=(200, 200, 200))
    
    # Draw form title
    draw.text((300, 120), "Registration Form", fill=(0, 0, 0), font=large_font)
    
    # Draw form fields
    form_fields = [
        "Personal Information",
        "Name:",
        "Email:",
        "Phone:",
        "Address:",
        "",
        "Preferences",
        "Subscribe to newsletter:",
        "Preferred contact method:"
    ]
    
    for i, field in enumerate(form_fields):
        if i == 0 or i == 6:  # Section headers
            draw.text((100, 180 + i*40), field, fill=(0, 0, 0), font=medium_font)
            draw.line([(100, 200 + i*40), (700, 200 + i*40)], fill=(200, 200, 200), width=1)
        elif field:  # Regular fields
            draw.text((100, 180 + i*40), field, fill=(0, 0, 0), font=small_font)
            
            # Draw form input fields
            if "Name" in field:
                draw.rectangle([(250, 175 + i*40), (700, 195 + i*40)], fill=(250, 250, 250), outline=(200, 200, 200))
            elif "Email" in field:
                draw.rectangle([(250, 175 + i*40), (700, 195 + i*40)], fill=(250, 250, 250), outline=(200, 200, 200))
            elif "Phone" in field:
                draw.rectangle([(250, 175 + i*40), (700, 195 + i*40)], fill=(250, 250, 250), outline=(200, 200, 200))
            elif "Address" in field:
                draw.rectangle([(250, 175 + i*40), (700, 235 + i*40)], fill=(250, 250, 250), outline=(200, 200, 200))
            elif "newsletter" in field:
                draw.rectangle([(250, 175 + i*40), (270, 195 + i*40)], fill=(250, 250, 250), outline=(200, 200, 200))
            elif "contact" in field:
                draw.rectangle([(250, 175 + i*40), (350, 195 + i*40)], fill=(250, 250, 250), outline=(200, 200, 200))
                draw.text((270, 177 + i*40), "Email", fill=(0, 0, 0), font=small_font)
    
    # Draw submit button
    draw.rectangle([(350, 500), (450, 530)], fill=(0, 120, 215), outline=(0, 120, 215))
    draw.text((370, 507), "Save Form", fill=(255, 255, 255), font=medium_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "pdf_form.png")
    img.save(output_path)
    print(f"Created PDF form screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'name_field': (475, 185),  # center of name field
        'email_field': (475, 225),  # center of email field
        'subscribe_checkbox': (260, 345),  # center of subscribe checkbox
        'save_form_button': (400, 515)  # center of save form button
    }

def create_data_viz_screenshot():
    """Create a screenshot of a data visualization tool interface"""
    img = Image.new('RGB', (800, 600), color=(250, 250, 250))
    draw = ImageDraw.Draw(img)
    
    # Try to use a font if available
    font_path = find_font()
    large_font = ImageFont.truetype(font_path, 20) if font_path else ImageFont.load_default()
    medium_font = ImageFont.truetype(font_path, 16) if font_path else ImageFont.load_default()
    small_font = ImageFont.truetype(font_path, 12) if font_path else ImageFont.load_default()
    
    # Draw header
    draw.rectangle([(0, 0), (800, 60)], fill=(63, 81, 181))
    draw.text((30, 20), "Data Visualization Tool", fill=(255, 255, 255), font=large_font)
    
    # Draw sidebar
    draw.rectangle([(0, 60), (200, 600)], fill=(240, 240, 240))
    draw.text((20, 80), "Data Sources", fill=(0, 0, 0), font=medium_font)
    
    data_sources = ["Sales Data", "Customer Metrics", "Product Performance", "Regional Stats"]
    for i, source in enumerate(data_sources):
        draw.rectangle([(20, 110 + i*40), (180, 140 + i*40)], fill=(255, 255, 255), outline=(220, 220, 220))
        draw.text((30, 117 + i*40), source, fill=(0, 0, 0), font=small_font)
    
    # Draw chart type selector
    draw.text((20, 300), "Chart Type", fill=(0, 0, 0), font=medium_font)
    draw.rectangle([(20, 330), (180, 360)], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((30, 337), "Line Chart", fill=(0, 0, 0), font=small_font)
    draw.text((150, 337), "▼", fill=(0, 0, 0), font=small_font)
    
    # Draw chart options dropdown
    draw.rectangle([(20, 360), (180, 480)], fill=(255, 255, 255), outline=(100, 100, 100))
    chart_types = ["Line Chart", "Bar Chart", "Pie Chart", "Area Chart", "Scatter Plot"]
    for i, chart in enumerate(chart_types):
        if chart == "Bar Chart":
            draw.rectangle([(20, 360 + i*24), (180, 384 + i*24)], fill=(230, 230, 250))
        draw.text((30, 367 + i*24), chart, fill=(0, 0, 0), font=small_font)
    
    # Draw data selector
    draw.text((20, 400), "Data Fields", fill=(0, 0, 0), font=medium_font)
    draw.rectangle([(20, 430), (180, 460)], fill=(255, 255, 255), outline=(220, 220, 220))
    draw.text((30, 437), "Sales by Quarter", fill=(0, 0, 0), font=small_font)
    draw.text((150, 437), "▼", fill=(0, 0, 0), font=small_font)
    
    # Draw main chart area
    draw.rectangle([(220, 80), (780, 450)], fill=(255, 255, 255), outline=(220, 220, 220))
    
    # Draw chart title input
    draw.text((230, 90), "Chart Title:", fill=(0, 0, 0), font=small_font)
    draw.rectangle([(310, 85), (770, 105)], fill=(250, 250, 250), outline=(200, 200, 200))
    draw.text((320, 87), "Quarterly Sales Performance", fill=(100, 100, 100), font=small_font)
    
    # Draw x and y axis
    draw.line([(250, 400), (750, 400)], fill=(0, 0, 0), width=1)  # X-axis
    draw.line([(250, 150), (250, 400)], fill=(0, 0, 0), width=1)  # Y-axis
    
    # Draw x-axis labels
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    for i, quarter in enumerate(quarters):
        x_pos = 300 + i * 150
        draw.text((x_pos, 410), quarter, fill=(0, 0, 0), font=small_font)
    
    # Draw y-axis labels
    values = ["0", "25K", "50K", "75K", "100K"]
    for i, value in enumerate(values):
        y_pos = 400 - i * 50
        draw.text((220, y_pos), value, fill=(0, 0, 0), font=small_font)
    
    # Draw bar chart
    bar_values = [45, 65, 35, 80]
    bar_colors = [(33, 150, 243), (76, 175, 80), (255, 152, 0), (233, 30, 99)]
    
    for i, value in enumerate(bar_values):
        x_pos = 300 + i * 150
        bar_height = value * 2.5
        draw.rectangle([(x_pos - 20, 400 - bar_height), (x_pos + 20, 400)], fill=bar_colors[i], outline=(255, 255, 255))
        draw.text((x_pos - 10, 400 - bar_height - 20), f"{value}K", fill=(0, 0, 0), font=small_font)
    
    # Draw export options
    draw.text((230, 470), "Export Options:", fill=(0, 0, 0), font=medium_font)
    
    export_options = ["PNG", "JPEG", "PDF", "SVG", "CSV"]
    for i, option in enumerate(export_options):
        x_pos = 350 + i * 80
        draw.rectangle([(x_pos, 470), (x_pos + 60, 490)], fill=(240, 240, 240), outline=(200, 200, 200))
        draw.text((x_pos + 10, 473), option, fill=(0, 0, 0), font=small_font)
    
    # Draw export button
    draw.rectangle([(680, 520), (780, 550)], fill=(63, 81, 181), outline=(63, 81, 181))
    draw.text((700, 527), "Export Chart", fill=(255, 255, 255), font=small_font)
    
    # Save the image
    output_path = os.path.join(SCREENSHOTS_DIR, "data_viz.png")
    img.save(output_path)
    print(f"Created data visualization screenshot: {output_path}")
    
    # Add annotations for test framework
    return {
        'chart_type_dropdown': (100, 345),  # center of chart type dropdown
        'bar_chart_option': (100, 385),  # center of bar chart option
        'data_selector': (100, 445),  # center of data selector field
        'sales_by_quarter_option': (100, 480),  # position for sales by quarter option (not shown in dropdown)
        'chart_title_field': (540, 95),  # center of chart title field
        'export_button': (730, 535),  # center of export button
        'png_format_option': (380, 480),  # center of PNG option
        'export_confirm_button': (730, 535)  # same as export button
    }

def generate_all_screenshots():
    """Generate all test screenshots"""
    print(f"Generating screenshots in {SCREENSHOTS_DIR}")
    
    # Create screenshot directory if it doesn't exist
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    # Generate each screenshot
    screenshot_generators = [
        create_browser_search_screenshot,
        create_email_compose_screenshot,
        create_spreadsheet_screenshot,
        create_calendar_screenshot,
        create_social_media_screenshot,
        create_file_explorer_screenshot,
        create_code_editor_screenshot,
        create_shopping_cart_screenshot,
        create_pdf_form_screenshot,
        create_data_viz_screenshot
    ]
    
    # Generate each screenshot
    for generator in screenshot_generators:
        try:
            generator()
        except Exception as e:
            print(f"Error generating screenshot with {generator.__name__}: {e}")
    
    print(f"Generated {len(screenshot_generators)} screenshots")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate test screenshots for the DO button exam framework')
    parser.add_argument('--output-dir', type=str, default=SCREENSHOTS_DIR,
                        help='Directory to save screenshots (default: test_screenshots)')
    args = parser.parse_args()
    
    # Update screenshots directory if specified
    if args.output_dir != SCREENSHOTS_DIR:
        SCREENSHOTS_DIR = args.output_dir
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    
    # Generate all screenshots
    generate_all_screenshots()