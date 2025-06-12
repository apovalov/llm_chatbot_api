#!/usr/bin/env python3
"""
Script for benchmarking and profiling API performance.
"""

import asyncio
import json
import time
from statistics import mean, median, stdev
from typing import List, Dict, Any

import httpx
import matplotlib.pyplot as plt


class APIBenchmark:
    """Class for performing API benchmarks."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict[str, Any]] = []

    async def single_request(
        self, client: httpx.AsyncClient, question: str
    ) -> Dict[str, Any]:
        """Execute a single request and measure metrics."""
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
        """Run parallel requests for load testing."""
        print(f"🚀 Starting benchmark with {concurrency} concurrent requests...")

        async with httpx.AsyncClient() as client:
            tasks = []
            for i in range(len(questions)):
                question = questions[i % len(questions)]
                tasks.append(self.single_request(client, question))

                if len(tasks) >= concurrency:
                    results = await asyncio.gather(*tasks)
                    self.results.extend(results)
                    tasks = []

                    # Small delay between batches
                    await asyncio.sleep(0.1)

            # Process any remaining tasks
            if tasks:
                results = await asyncio.gather(*tasks)
                self.results.extend(results)

    async def sequential_benchmark(self, questions: List[str]) -> None:
        """Run sequential requests."""
        print("🔄 Starting sequential requests...")

        async with httpx.AsyncClient() as client:
            for question in questions:
                result = await self.single_request(client, question)
                self.results.append(result)

                # Small delay between requests
                await asyncio.sleep(0.5)

    def analyze_results(self) -> Dict[str, Any]:
        """Analyze benchmark results."""
        if not self.results:
            return {"error": "No data to analyze"}

        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]

        if not successful:
            return {"error": "All requests failed"}

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

        # Count status codes
        for result in self.results:
            code = result["status_code"]
            analysis["status_codes"][code] = analysis["status_codes"].get(code, 0) + 1

        # Collect errors
        for result in failed:
            if result["error"]:
                analysis["errors"].append(result["error"])

        return analysis

    def print_results(self, analysis: Dict[str, Any]) -> None:
        """Print the benchmarking results to the console."""
        print("\n" + "=" * 60)
        print("📊 BENCHMARK RESULTS")
        print("=" * 60)

        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            return

        print("📈 Summary:")
        print(f"   Total requests: {analysis['total_requests']}")
        print(f"   Successful: {analysis['successful_requests']}")
        print(f"   Failed: {analysis['failed_requests']}")
        print(f"   Success rate: {analysis['success_rate']:.1f}%")

        rt = analysis["response_times"]
        print("\n⏱️ Response time (seconds):")
        print(f"   Min: {rt['min']:.4f}")
        print(f"   Max: {rt['max']:.4f}")
        print(f"   Mean: {rt['mean']:.4f}")
        print(f"   Median: {rt['median']:.4f}")
        print(f"   Std dev: {rt['std_dev']:.4f}")

        print("\n📋 Status codes:")
        for code, count in analysis["status_codes"].items():
            print(f"   {code}: {count} requests")

        if analysis["errors"]:
            print("\n❌ Errors:")
            for error in set(analysis["errors"]):
                count = analysis["errors"].count(error)
                print(f"   {error}: {count} times")

    def save_chart(
        self, analysis: Dict[str, Any], filename: str = "results/benchmark_chart.png"
    ) -> None:
        """Save the benchmark chart to a file."""
        if "error" in analysis or not self.results:
            return

        successful = [r for r in self.results if r["success"]]
        response_times = [r["response_time"] for r in successful]

        plt.figure(figsize=(12, 8))

        # Response time plot
        plt.subplot(2, 2, 1)
        plt.plot(response_times, alpha=0.7)
        plt.title("Response Time per Request")
        plt.xlabel("Request Index")
        plt.ylabel("Time (s)")
        plt.grid(True, alpha=0.3)

        # Histogram of response times
        plt.subplot(2, 2, 2)
        plt.hist(response_times, bins=20, alpha=0.7)
        plt.title("Response Time Distribution")
        plt.xlabel("Time (s)")
        plt.ylabel("Number of Requests")
        plt.grid(True, alpha=0.3)

        # Status codes bar chart
        plt.subplot(2, 2, 3)
        codes = list(analysis["status_codes"].keys())
        counts = list(analysis["status_codes"].values())
        plt.bar([str(c) for c in codes], counts, alpha=0.7)
        plt.title("Status Codes")
        plt.xlabel("HTTP Code")
        plt.ylabel("Number of Requests")
        plt.grid(True, alpha=0.3)

        # Summary panel
        plt.subplot(2, 2, 4)
        plt.text(0.1, 0.8, f"Total requests: {analysis['total_requests']}", fontsize=12)
        plt.text(
            0.1, 0.7, f"Success rate: {analysis['success_rate']:.1f}%", fontsize=12
        )
        plt.text(
            0.1,
            0.6,
            f"Mean time: {analysis['response_times']['mean']:.3f}s",
            fontsize=12,
        )
        plt.text(
            0.1,
            0.5,
            f"Median time: {analysis['response_times']['median']:.3f}s",
            fontsize=12,
        )
        plt.xlim(0, 1)
        plt.ylim(0, 1)
        plt.axis("off")
        plt.title("Summary")

        plt.tight_layout()
        plt.savefig(filename, dpi=300, bbox_inches="tight")
        print(f"📊 Chart saved: {filename}")


async def main():
    """Main function to run benchmarks."""
    # Test questions
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

    print("🔧 Starting API profiling...")

    # Check API availability
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ API is unavailable!")
                return
    except Exception as e:
        print(f"❌ Unable to connect to API: {e}")
        return

    benchmark = APIBenchmark()

    # Sequential test
    print("\n1️⃣ Sequential test (5 requests)...")
    await benchmark.sequential_benchmark(test_questions[:5])

    # Concurrent test
    print("\n2️⃣ Concurrent test (10 requests, 3 threads)...")
    await benchmark.concurrent_benchmark(test_questions[:10], concurrency=3)

    # Analyze results
    analysis = benchmark.analyze_results()
    benchmark.print_results(analysis)

    # Save chart
    try:
        benchmark.save_chart(analysis)
    except Exception as e:
        print(f"⚠️ Failed to save chart: {e}")

    # Save JSON report
    with open("results/benchmark_report.json", "w", encoding="utf-8") as f:
        json.dump(
            {"analysis": analysis, "raw_results": benchmark.results},
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\n💾 Report saved: results/benchmark_report.json")
    print("✅ Profiling completed!")


if __name__ == "__main__":
    asyncio.run(main())
