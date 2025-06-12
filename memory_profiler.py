#!/usr/bin/env python3
"""
Memory profiling for API requests.
"""

import asyncio
import time
from memory_profiler import profile
import httpx


@profile
async def test_memory_usage():
    """Test memory usage during API requests."""
    print("🧠 Starting memory profiling...")

    async with httpx.AsyncClient() as client:
        # Check API availability
        try:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            print(f"✅ API available: {response.status_code}")
        except Exception as e:
            print(f"❌ API unavailable: {e}")
            return

        # Test questions
        questions = [
            "Hello!",
            "What is artificial intelligence?",
            "Explain Python programming",
            "Tell me about FastAPI",
            "Write a short story",
        ]

        # Sequential requests
        for i, question in enumerate(questions, start=1):
            print(f"📤 Request {i}: {question[:30]}...")

            try:
                start_time = time.perf_counter()
                response = await client.post(
                    "http://localhost:8000/question",
                    json={"text": question},
                    timeout=30.0,
                )
                end_time = time.perf_counter()

                print(f"✅ Response received in {end_time - start_time:.2f}s")

            except Exception as e:
                print(f"❌ Error: {e}")

            # Pause between requests
            await asyncio.sleep(1)

    print("🏁 Memory profiling completed!")


if __name__ == "__main__":
    asyncio.run(test_memory_usage())
