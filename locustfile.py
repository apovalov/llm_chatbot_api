import json
import random
from locust import HttpUser, task, between


class ChatbotUser(HttpUser):
    """Simulates a chatbot user for load testing."""

    # Time to wait between requests (to mimic a real user)
    wait_time = between(1, 3)

    def on_start(self):
        """Run at the start of each user session to verify API health."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code != 200:
                response.failure(f"Health check failed: {response.status_code}")

    @task(10)  # Weight 10 out of 11 (≈90% of requests)
    def ask_question(self):
        """Main task: ask the chatbot a question."""
        questions = [
            "Hello! How are you?",
            "Tell me about yourself",
            "What's the weather today?",
            "Explain what artificial intelligence is",
            "Write a short poem",
            "Help me solve a math problem",
            "Give me a programming tip",
            "What is FastAPI?",
            "How does machine learning work?",
            "Tell me a joke",
        ]

        question = random.choice(questions)
        payload = {"text": question}

        with self.client.post(
            "/question",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="POST /question",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "text" in data and data["text"]:
                        response.success()
                    else:
                        response.failure("Empty response from API")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                # Rate limit hits are expected under heavy load
                response.success()
            elif response.status_code == 422:
                response.failure("Validation error")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)  # Weight 1 out of 11 (≈10% of requests)
    def health_check(self):
        """Periodically check API health."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "healthy":
                        response.success()
                    else:
                        response.failure("API reports unhealthy status")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"HTTP {response.status_code}")

    @task(1)  # Rare task for testing edge cases
    def test_edge_cases(self):
        """Test boundary conditions."""
        edge_cases = [
            {"text": ""},  # Empty string
            {"text": "x" * 1000},  # Very long string
            {"text": "Short question"},  # Normal-length string
        ]

        case = random.choice(edge_cases)

        with self.client.post(
            "/question",
            json=case,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="POST /question (edge cases)",
        ) as response:
            # For edge cases, we allow 200, 422, or 429
            if response.status_code in [200, 422, 429]:
                response.success()
            else:
                response.failure(f"Unexpected status code: {response.status_code}")


class HeavyUser(HttpUser):
    """A heavy user with minimal wait time."""

    wait_time = between(0.1, 0.5)  # Very rapid requests
    weight = 1  # Fewer of these users

    @task
    def rapid_fire_questions(self):
        """Send quick, successive requests."""
        quick_questions = [
            "Yes",
            "No",
            "Good",
            "Understood",
            "Thank you",
        ]

        question = random.choice(quick_questions)
        payload = {"text": question}

        with self.client.post(
            "/question",
            json=payload,
            headers={"Content-Type": "application/json"},
            catch_response=True,
            name="POST /question (rapid)",
        ) as response:
            if response.status_code in [200, 429]:  # 429 = rate limit OK
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class RegularUser(ChatbotUser):
    """A standard user, inheriting behavior from ChatbotUser."""

    weight = 9  # Majority of users
