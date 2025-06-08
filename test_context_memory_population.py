import asyncio
from memory.memory_system import MemorySystem

async def main():
    ms = MemorySystem()
    await ms.initialize()
    test_payload = {
        "active_window": "TestApp",
        "active_app": "TestApp",
        "active_apps": ["TestApp"],
        "window_title": "Test Window",
        "text": "This is a test event"
    }
    await ms.process_sensor_data("screen", test_payload)
    print("Test event processed. Check memory_state.json for context memory.")

if __name__ == "__main__":
    asyncio.run(main()) 