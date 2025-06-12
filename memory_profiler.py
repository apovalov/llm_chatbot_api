#!/usr/bin/env python3
"""
Профилирование памяти для API запросов.
"""

import asyncio
import time
from memory_profiler import profile
import httpx


@profile
async def test_memory_usage():
    """Тестирует использование памяти при API запросах."""
    print("🧠 Начинаем профилирование памяти...")

    async with httpx.AsyncClient() as client:
        # Проверка доступности API
        try:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            print(f"✅ API доступен: {response.status_code}")
        except Exception as e:
            print(f"❌ API недоступен: {e}")
            return

        # Тестовые запросы
        questions = [
            "Hello!",
            "What is artificial intelligence?",
            "Explain Python programming",
            "Tell me about FastAPI",
            "Write a short story",
        ]

        # Последовательные запросы
        for i, question in enumerate(questions, 1):
            print(f"📤 Запрос {i}: {question[:30]}...")

            try:
                start_time = time.perf_counter()
                response = await client.post(
                    "http://localhost:8000/question",
                    json={"text": question},
                    timeout=30.0,
                )
                end_time = time.perf_counter()

                print(f"✅ Ответ получен за {end_time - start_time:.2f}s")

            except Exception as e:
                print(f"❌ Ошибка: {e}")

            # Пауза между запросами
            await asyncio.sleep(1)

    print("🏁 Профилирование памяти завершено!")


if __name__ == "__main__":
    asyncio.run(test_memory_usage())
