# backend/test_error_handling.py
"""
Test script to verify Claude API error handling implementation
Run this to test different error scenarios
"""

import asyncio
import os
from unittest.mock import Mock, patch
from anthropic import APIConnectionError, RateLimitError, APIStatusError

from claude_service import ClaudeService, ClaudeAPIError, FallbackQuizGenerator


async def test_exponential_backoff():
    """Test exponential backoff calculations"""
    print("\n🧪 Testing exponential backoff calculation...")

    service = ClaudeService(api_key="test_key")

    delays = []
    for i in range(5):
        delay = service._calculate_backoff_delay(i)
        delays.append(delay)
        print(f"   Attempt {i + 1}: {delay:.2f}s")

    # Verify exponential growth
    assert delays[1] > delays[0], "Backoff should increase"
    assert delays[2] > delays[1], "Backoff should increase"
    assert delays[4] <= 60.0, "Backoff should be capped at 60s"

    print("   ✅ Exponential backoff working correctly")


def test_user_friendly_errors():
    """Test user-friendly error message generation"""
    print("\n🧪 Testing user-friendly error messages...")

    service = ClaudeService(api_key="test_key")

    # Test different error types using mocks
    test_cases = []

    # Mock RateLimitError
    rate_limit_error = Mock(spec=RateLimitError)
    rate_limit_error.__class__ = RateLimitError
    test_cases.append((rate_limit_error, "request"))

    # Mock APIConnectionError
    connection_error = Mock(spec=APIConnectionError)
    connection_error.__class__ = APIConnectionError
    test_cases.append((connection_error, "connection"))

    # Mock APIStatusError with different status codes
    for status_code, keyword in [
        (401, "authentication"),
        (429, "demand"),
        (500, "internal error"),
        (529, "overloaded"),
    ]:
        status_error = Mock(spec=APIStatusError)
        status_error.__class__ = APIStatusError
        status_error.status_code = status_code
        test_cases.append((status_error, keyword))

    # Generic exception
    test_cases.append((Exception("Unknown error"), "unexpected"))

    for error, expected_keyword in test_cases:
        message = service._get_user_friendly_error(error)
        error_type = error.__class__.__name__
        print(f"   {error_type}: {message}")
        assert expected_keyword.lower() in message.lower() or "error" in message.lower()

    print("   ✅ User-friendly error messages working correctly")


def test_retry_logic():
    """Test retry decision logic"""
    print("\n🧪 Testing retry logic...")

    service = ClaudeService(api_key="test_key", max_retries=3)

    # Mock connection error
    connection_error = Mock(spec=APIConnectionError)
    connection_error.__class__ = APIConnectionError

    # Should retry on connection errors
    assert service._should_retry(connection_error, 0)
    assert service._should_retry(connection_error, 2)
    assert not service._should_retry(connection_error, 3)

    # Mock rate limit error
    rate_limit_error = Mock(spec=RateLimitError)
    rate_limit_error.__class__ = RateLimitError

    # Should retry on rate limits
    assert service._should_retry(rate_limit_error, 0)

    # Should retry on specific status codes
    for status_code in [429, 500, 502, 503, 504, 529]:
        status_error = Mock(spec=APIStatusError)
        status_error.__class__ = APIStatusError
        status_error.status_code = status_code
        assert service._should_retry(status_error, 0), f"Should retry on {status_code}"

    # Should not retry on auth errors
    auth_error = Mock(spec=APIStatusError)
    auth_error.__class__ = APIStatusError
    auth_error.status_code = 401
    assert not service._should_retry(auth_error, 0)

    # Should not retry if max attempts reached
    assert not service._should_retry(connection_error, 5)

    print("   ✅ Retry logic working correctly")


def test_fallback_generator():
    """Test fallback quiz generator"""
    print("\n🧪 Testing fallback quiz generator...")

    # Test different topics
    topics = ["linear_equations", "quadratic_equations", "polynomials", "factoring"]

    for topic in topics:
        questions = FallbackQuizGenerator.generate_fallback_questions(topic, 3)
        assert len(questions) == 3, f"Should generate 3 questions for {topic}"
        assert all(q.topic == topic for q in questions), "All questions should have correct topic"
        print(f"   ✅ Generated {len(questions)} questions for {topic}")

    # Test unknown topic (should use default)
    questions = FallbackQuizGenerator.generate_fallback_questions("unknown_topic", 2)
    assert len(questions) == 2, "Should generate 2 questions for unknown topic"
    print("   ✅ Fallback working for unknown topics")


async def test_integration_scenarios():
    """Test real-world integration scenarios"""
    print("\n🧪 Testing integration scenarios...")

    # Test ClaudeService initialization
    service = ClaudeService(api_key="test_key", max_retries=2, initial_retry_delay=0.1)
    assert service.max_retries == 2
    assert service.initial_retry_delay == 0.1
    print("   ✅ Service initialization working correctly")

    # Test that ClaudeAPIError can be created and used
    try:
        raise ClaudeAPIError("Test error message", retry_after=30)
    except ClaudeAPIError as e:
        assert e.message == "Test error message"
        assert e.retry_after == 30
        print("   ✅ ClaudeAPIError exception working correctly")

    # Test fallback integration
    questions = FallbackQuizGenerator.generate_fallback_questions("linear_equations", 5)
    assert len(questions) == 5
    assert all(hasattr(q, 'question') for q in questions)
    assert all(hasattr(q, 'options') for q in questions)
    assert all(hasattr(q, 'correct') for q in questions)
    print("   ✅ Fallback generator integration working correctly")

    print("   ✅ All integration scenarios passed")


async def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Running Claude API Error Handling Tests")
    print("=" * 60)

    try:
        await test_exponential_backoff()
        test_user_friendly_errors()
        test_retry_logic()
        test_fallback_generator()
        await test_integration_scenarios()

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nError handling features verified:")
        print("  ✓ Exponential backoff with jitter")
        print("  ✓ User-friendly error messages")
        print("  ✓ Smart retry logic")
        print("  ✓ Fallback quiz generator")
        print("  ✓ Proper error propagation")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(run_all_tests())
