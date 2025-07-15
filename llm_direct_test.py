#!/usr/bin/env python3
import asyncio
import time
from llm.llm_service import LLMService

async def main():
    llm = LLMService()
    print("\n--- Direct LLM Test: Simple Prompt ---")
    messages = [{ 'role': 'user', 'content': 'What is 2+2?' }]
    t0 = time.time()
    resp = await llm.llm_client.generate_response(messages)
    t1 = time.time()
    print(f"Simple: {t1-t0:.2f}s | {resp.strip()}")

    print("\n--- Direct LLM Test: Multi-step JSON Prompt ---")
    plan_prompt = '''Task: Search Segev in Google\nWhat are the step-by-step actions? Return a JSON array of steps. Each step: id, description, action_type, target, value, confidence, estimated_duration, reasoning.'''
    messages = [{ 'role': 'user', 'content': plan_prompt }]
    t0 = time.time()
    resp = await llm.llm_client.generate_response(messages)
    t1 = time.time()
    print(f"Multi-step: {t1-t0:.2f}s | {resp.strip()[:200]}...\n")

if __name__ == "__main__":
    asyncio.run(main()) 