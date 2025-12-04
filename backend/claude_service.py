# backend/claude_service.py
import anthropic
import time
import json
from typing import List, Optional, Dict, Any
from anthropic import APIError, APIConnectionError, RateLimitError, APIStatusError
import logging

from models import QuizQuestion

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClaudeAPIError(Exception):
    """Custom exception for Claude API errors with user-friendly messages"""
    def __init__(self, message: str, original_error: Optional[Exception] = None, retry_after: Optional[int] = None):
        self.message = message
        self.original_error = original_error
        self.retry_after = retry_after
        super().__init__(self.message)


class ClaudeService:
    """Service for interacting with Claude API with robust error handling"""

    def __init__(self, api_key: str, max_retries: int = 3, initial_retry_delay: float = 1.0):
        """
        Initialize Claude service with retry configuration

        Args:
            api_key: Anthropic API key
            max_retries: Maximum number of retry attempts
            initial_retry_delay: Initial delay in seconds before first retry
        """
        if not api_key:
            raise ClaudeAPIError("Claude API key is not configured. Please set ANTHROPIC_API_KEY in your environment.")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay

        logger.info("✅ Claude service initialized")

    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        import random
        base_delay = self.initial_retry_delay * (2 ** attempt)
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.1 * base_delay)
        return min(base_delay + jitter, 60.0)  # Cap at 60 seconds

    def _get_user_friendly_error(self, error: Exception) -> str:
        """Convert technical errors to user-friendly messages"""

        if isinstance(error, RateLimitError):
            return "You've made too many requests. Please wait a moment and try again."

        elif isinstance(error, APIConnectionError):
            return "Unable to connect to the AI service. Please check your internet connection and try again."

        elif isinstance(error, APIStatusError):
            status_code = getattr(error, 'status_code', None)

            if status_code == 401:
                return "API authentication failed. Please check your API key configuration."
            elif status_code == 403:
                return "Access denied. Your API key may not have the required permissions."
            elif status_code == 404:
                return "The requested AI model is not available."
            elif status_code == 429:
                return "Service is experiencing high demand. Please try again in a moment."
            elif status_code == 500:
                return "The AI service encountered an internal error. Please try again later."
            elif status_code == 529:
                return "The AI service is temporarily overloaded. Please try again in a few minutes."
            else:
                return f"The AI service returned an error (code {status_code}). Please try again."

        elif isinstance(error, json.JSONDecodeError):
            return "Received an invalid response from the AI service. Please try again."

        elif isinstance(error, anthropic.APIError):
            return "An unexpected error occurred with the AI service. Please try again."

        else:
            return "An unexpected error occurred while generating the quiz. Please try again."

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if the request should be retried"""

        # Don't retry if we've exhausted attempts
        if attempt >= self.max_retries:
            return False

        # Retry on connection errors
        if isinstance(error, APIConnectionError):
            return True

        # Retry on rate limits
        if isinstance(error, RateLimitError):
            return True

        # Retry on specific status codes
        if isinstance(error, APIStatusError):
            status_code = getattr(error, 'status_code', None)
            # Retry on server errors and rate limits
            if status_code in [429, 500, 502, 503, 504, 529]:
                return True

        # Don't retry on other errors (auth, validation, etc.)
        return False

    async def generate_quiz_questions(
        self,
        topic: str,
        num_questions: int,
        student_context: Dict[str, Any],
        model: str = "claude-sonnet-4-20250514"
    ) -> List[QuizQuestion]:
        """
        Generate quiz questions using Claude API with retry logic

        Args:
            topic: Quiz topic
            num_questions: Number of questions to generate
            student_context: Student information for personalization
            model: Claude model to use

        Returns:
            List of QuizQuestion objects

        Raises:
            ClaudeAPIError: If generation fails after all retries
        """

        topic_display = topic.replace("_", " ").title()

        # Create prompt for Claude
        prompt = f"""Generate {num_questions} multiple-choice algebra questions about {topic_display} for a high school student.

Student context:
- Current grade average: {student_context.get('grade_average', 'N/A')}
- Struggling with: {student_context.get('struggling_topics', 'N/A')}

Requirements:
1. Questions should be at an appropriate difficulty level
2. Include 4 options (A, B, C, D) per question
3. Provide detailed explanations for correct answers
4. Reference relevant math concepts in explanations

Output ONLY valid JSON in this exact format (no markdown, no extra text):
[
  {{
    "question": "Solve for x: 2x + 5 = 13",
    "options": {{
      "A": "x = 3",
      "B": "x = 4",
      "C": "x = 5",
      "D": "x = 6"
    }},
    "correct": "B",
    "explanation": "Subtract 5 from both sides: 2x = 8. Then divide by 2: x = 4. This uses the principle of inverse operations.",
    "topic": "{topic}"
  }}
]"""

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    delay = self._calculate_backoff_delay(attempt - 1)
                    logger.info(f"🔄 Retry attempt {attempt}/{self.max_retries} after {delay:.1f}s delay")
                    time.sleep(delay)

                logger.info(f"📞 Calling Claude API (attempt {attempt + 1}/{self.max_retries + 1})...")

                # Call Claude API
                message = self.client.messages.create(
                    model=model,
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )

                logger.info("✅ Claude API responded successfully!")

                # Parse response
                response_text = message.content[0].text.strip()

                # Remove markdown code blocks if present
                if response_text.startswith("```"):
                    response_text = response_text.split("```")[1]
                    if response_text.startswith("json"):
                        response_text = response_text[4:]
                response_text = response_text.strip()

                # Parse JSON
                questions_data = json.loads(response_text)
                logger.info(f"✅ Successfully parsed {len(questions_data)} questions")

                # Convert to QuizQuestion models
                questions = [QuizQuestion(**q) for q in questions_data]

                return questions

            except (APIConnectionError, RateLimitError, APIStatusError) as e:
                last_error = e
                logger.warning(f"⚠️ API error on attempt {attempt + 1}: {type(e).__name__}: {str(e)}")

                if not self._should_retry(e, attempt):
                    # Get user-friendly error message
                    user_message = self._get_user_friendly_error(e)

                    # Extract retry_after if available (for rate limits)
                    retry_after = None
                    if isinstance(e, RateLimitError):
                        retry_after = getattr(e, 'retry_after', None)

                    raise ClaudeAPIError(user_message, original_error=e, retry_after=retry_after)

                # Continue to next retry attempt
                continue

            except json.JSONDecodeError as e:
                last_error = e
                logger.error(f"❌ JSON parsing error: {str(e)}")
                logger.error(f"   Response text: {response_text[:200]}...")

                # Don't retry JSON parsing errors
                user_message = self._get_user_friendly_error(e)
                raise ClaudeAPIError(user_message, original_error=e)

            except Exception as e:
                last_error = e
                logger.error(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")

                # Don't retry unexpected errors
                user_message = self._get_user_friendly_error(e)
                raise ClaudeAPIError(user_message, original_error=e)

        # If we get here, all retries failed
        user_message = self._get_user_friendly_error(last_error) if last_error else "Failed to generate quiz after multiple attempts."
        raise ClaudeAPIError(user_message, original_error=last_error)


class FallbackQuizGenerator:
    """Fallback quiz generator when Claude API is unavailable"""

    @staticmethod
    def generate_fallback_questions(topic: str, num_questions: int) -> List[QuizQuestion]:
        """
        Generate basic fallback questions when API is unavailable

        Args:
            topic: Quiz topic
            num_questions: Number of questions to generate

        Returns:
            List of basic QuizQuestion objects
        """
        logger.info("🔄 Using fallback quiz generator")

        # Basic fallback questions by topic
        fallback_questions = {
            "linear_equations": [
                QuizQuestion(
                    question="Solve for x: 2x + 5 = 13",
                    options={"A": "x = 3", "B": "x = 4", "C": "x = 5", "D": "x = 6"},
                    correct="B",
                    explanation="Subtract 5 from both sides: 2x = 8. Then divide by 2: x = 4.",
                    topic=topic
                ),
                QuizQuestion(
                    question="What is the solution to: 3x - 7 = 14?",
                    options={"A": "x = 5", "B": "x = 6", "C": "x = 7", "D": "x = 8"},
                    correct="C",
                    explanation="Add 7 to both sides: 3x = 21. Then divide by 3: x = 7.",
                    topic=topic
                ),
            ],
            "quadratic_equations": [
                QuizQuestion(
                    question="What are the solutions to x² - 5x + 6 = 0?",
                    options={"A": "x = 1, 6", "B": "x = 2, 3", "C": "x = -2, -3", "D": "x = 1, 5"},
                    correct="B",
                    explanation="Factor to (x-2)(x-3) = 0. Solutions are x = 2 and x = 3.",
                    topic=topic
                ),
            ],
            "polynomials": [
                QuizQuestion(
                    question="Simplify: (2x + 3)(x - 4)",
                    options={"A": "2x² - 5x - 12", "B": "2x² - 8x - 12", "C": "2x² + 5x + 12", "D": "2x² + 11x - 12"},
                    correct="A",
                    explanation="Use FOIL: 2x² - 8x + 3x - 12 = 2x² - 5x - 12.",
                    topic=topic
                ),
            ],
            "factoring": [
                QuizQuestion(
                    question="Factor: x² + 7x + 12",
                    options={"A": "(x + 3)(x + 4)", "B": "(x + 2)(x + 6)", "C": "(x + 1)(x + 12)", "D": "(x - 3)(x - 4)"},
                    correct="A",
                    explanation="Find two numbers that multiply to 12 and add to 7: 3 and 4. So (x + 3)(x + 4).",
                    topic=topic
                ),
            ],
        }

        # Get questions for this topic, or use linear equations as default
        questions = fallback_questions.get(topic, fallback_questions["linear_equations"])

        # Return requested number of questions (cycle if needed)
        result = []
        for i in range(num_questions):
            result.append(questions[i % len(questions)])

        return result
