#!/usr/bin/env python3
"""
Скрипт для бенчмарков и профилирования API производительности.
"""

import asyncio
import json
import time
from statistics import mean, median, stdev
from typing import List, Dict, Any

import httpx
import matplotlib.pyplot as plt


class APIBenchmark:
    """Класс для проведения бенчмарков API."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    async def single_request(
        self, client: httpx.AsyncClient, question: str
    ) -> Dict[str, Any]:
        """Выполняет одиночный запрос и измеряет метрики."""
        start_time = time.perf_counter()

        try:
            response = await client.post(
                f"{self.base_url}/question", json={"text": question}, timeout=30.0
            )

            end_time = time.perf_counter()
            response_time = end_time - start_time

            return {
                "success": True,
                "status_code": response.status_code,
                "response_time": response_time,
                "question_length": len(question),
                "response_length": len(response.text)
                if response.status_code == 200
                else 0,
                "headers": dict(response.headers),
                "error": None,
            }

        except Exception as e:
            end_time = time.perf_counter()
            return {
                "success": False,
                "status_code": 0,
                "response_time": end_time - start_time,
                "question_length": len(question),
                "response_length": 0,
                "headers": {},
                "error": str(e),
            }

    async def concurrent_benchmark(
        self, questions: List[str], concurrency: int = 5
    ) -> None:
        """Запускает параллельные запросы для нагрузочного тестирования."""
        print(f"🚀 Запуск benchmark с {concurrency} параллельными запросами...")

        async with httpx.AsyncClient() as client:
            # Создаем задачи
            tasks = []
            for i in range(len(questions)):
                question = questions[i % len(questions)]
                task = self.single_request(client, question)
                tasks.append(task)

                # Ограничиваем количество одновременных запросов
                if len(tasks) >= concurrency:
                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)
                    tasks = []

                    # Небольшая пауза между батчами
                    await asyncio.sleep(0.1)

            # Обрабатываем оставшиеся задачи
            if tasks:
                results = await asyncio.gather(*tasks)
                self.results.extend(results)

    async def sequential_benchmark(self, questions: List[str]) -> None:
        """Запускает последовательные запросы."""
        print("🔄 Запуск последовательных запросов...")

        async with httpx.AsyncClient() as client:
            for question in questions:
                result = await self.single_request(client, question)
                self.results.append(result)

                # Небольшая пауза между запросами
                await asyncio.sleep(0.5)

    def analyze_results(self) -> Dict[str, Any]:
        """Анализирует результаты бенчмарков."""
        if not self.results:
            return {"error": "Нет данных для анализа"}

        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]

        if not successful:
            return {"error": "Все запросы завершились ошибкой"}

        response_times = [r["response_time"] for r in successful]

        analysis = {
            "total_requests": len(self.results),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(self.results) * 100,
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "mean": mean(response_times),
                "median": median(response_times),
                "std_dev": stdev(response_times) if len(response_times) > 1 else 0,
            },
            "status_codes": {},
            "errors": [],
        }

        # Подсчет кодов ответов
        for result in self.results:
            code = result["status_code"]
            analysis["status_codes"][code] = analysis["status_codes"].get(code, 0) + 1

        # Сбор ошибок
        for result in failed:
            if result["error"]:
                analysis["errors"].append(result["error"])

        return analysis

    def print_results(self, analysis: Dict[str, Any]) -> None:
        """Выводит результаты в консоль."""
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ BENCHMARK")
        print("=" * 60)

        if "error" in analysis:
            print(f"❌ Ошибка: {analysis['error']}")
            return

        print("📈 Общая статистика:")
        print(f"   Всего запросов: {analysis['total_requests']}")
        print(f"   Успешных: {analysis['successful_requests']}")
        print(f"   Неудачных: {analysis['failed_requests']}")
        print(f"   Успешность: {analysis['success_rate']:.1f}%")

        rt = analysis["response_times"]
        print("\n⏱️ Время ответа (сек):")
        print(f"   Минимальное: {rt['min']:.4f}")
        print(f"   Максимальное: {rt['max']:.4f}")
        print(f"   Среднее: {rt['mean']:.4f}")
        print(f"   Медиана: {rt['median']:.4f}")
        print(f"   Стандартное отклонение: {rt['std_dev']:.4f}")

        print("\n📋 Коды ответов:")
        for code, count in analysis["status_codes"].items():
            print(f"   {code}: {count} запросов")

        if analysis["errors"]:
            print("\n❌ Ошибки:")
            for error in set(analysis["errors"]):
                count = analysis["errors"].count(error)
                print(f"   {error}: {count} раз")

    def save_chart(
        self, analysis: Dict[str, Any], filename: str = "results/benchmark_chart.png"
    ) -> None:
        """Сохраняет график результатов."""
        if "error" in analysis or not self.results:
            return

        successful = [r for r in self.results if r["success"]]
        response_times = [r["response_time"] for r in successful]

        plt.figure(figsize=(12, 8))

        # График времени ответа
        plt.subplot(2, 2, 1)
        plt.plot(response_times, "b-", alpha=0.7)
        plt.title("Время ответа по запросам")
        plt.xlabel("Номер запроса")
        plt.ylabel("Время (сек)")
        plt.grid(True, alpha=0.3)

        # Гистограмма времени ответа
        plt.subplot(2, 2, 2)
        plt.hist(response_times, bins=20, alpha=0.7, color="green")
        plt.title("Распределение времени ответа")
        plt.xlabel("Время (сек)")
        plt.ylabel("Количество запросов")
        plt.grid(True, alpha=0.3)

        # График кодов ответов
        plt.subplot(2, 2, 3)
        codes = list(analysis["status_codes"].keys())
        counts = list(analysis["status_codes"].values())
        plt.bar([str(c) for c in codes], counts, alpha=0.7, color="orange")
        plt.title("Коды ответов")
        plt.xlabel("HTTP код")
        plt.ylabel("Количество")
        plt.grid(True, alpha=0.3)

        # Сводная информация
        plt.subplot(2, 2, 4)
        plt.text(0.1, 0.8, f"Всего запросов: {analysis['total_requests']}", fontsize=12)
        plt.text(0.1, 0.7, f"Успешность: {analysis['success_rate']:.1f}%", fontsize=12)
        plt.text(
            0.1,
            0.6,
            f"Среднее время: {analysis['response_times']['mean']:.3f}s",
            fontsize=12,
        )
        plt.text(
            0.1,
            0.5,
            f"Медиана: {analysis['response_times']['median']:.3f}s",
            fontsize=12,
        )
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axis("off")
        plt.title("Сводка")

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"📊 График сохранен: {filename}")


async def main():
    """Основная функция для запуска бенчмарков."""
    # Тестовые вопросы
    test_questions = [
        "Hello!",
        "How are you?",
        "What is AI?",
        "Tell me a joke",
        "Explain quantum physics",
        "Write a poem about coding",
        "What's the weather like?",
        "Help me with Python",
        "Translate: Bonjour",
        "What is 2+2?",
    ]

    print("🔧 Начинаем профилирование API...")

    # Проверка доступности API
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ API не доступен!")
                return
    except Exception as e:
        print(f"❌ Не удается подключиться к API: {e}")
        return

    benchmark = APIBenchmark()

    # Последовательный тест
    print("\n1️⃣ Последовательный тест (5 запросов)...")
    await benchmark.sequential_benchmark(test_questions[:5])

    # Параллельный тест
    print("\n2️⃣ Параллельный тест (10 запросов, 3 потока)...")
    await benchmark.concurrent_benchmark(test_questions[:10], concurrency=3)

    # Анализ результатов
    analysis = benchmark.analyze_results()
    benchmark.print_results(analysis)

    # Сохранение графика
    try:
        benchmark.save_chart(analysis)
    except Exception as e:
        print(f"⚠️ Не удалось сохранить график: {e}")

    # Сохранение JSON отчета
    with open("results/benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(
            {"analysis": analysis, "raw_results": benchmark.results},
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n💾 Отчет сохранен: results/benchmark_report.json")
    print("✅ Профилирование завершено!")


if __name__ == "__main__":
    asyncio.run(main())
