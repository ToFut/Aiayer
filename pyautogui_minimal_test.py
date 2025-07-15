import pyautogui
import time

print("Moving mouse in 3 seconds...")
time.sleep(3)
pyautogui.moveTo(100, 100, duration=1)
pyautogui.click()
pyautogui.typewrite("Hello from PyAutoGUI!", interval=0.1)
print("Done.") 