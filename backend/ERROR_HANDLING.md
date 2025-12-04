# Claude API Error Handling Documentation

## Overview

This document describes the comprehensive error handling system implemented for Claude API interactions in the AI Teaching Assistant application.

## Features Implemented

### 1. Retry Logic with Exponential Backoff

**Location:** `backend/claude_service.py:135-185`

The system automatically retries failed API calls with exponential backoff:

- **Maximum retries:** 3 (configurable)
- **Initial delay:** 1 second (configurable)
- **Backoff strategy:** Exponential with jitter to prevent thundering herd
- **Maximum delay:** Capped at 60 seconds

**Formula:** `delay = min(initial_delay * (2 ^ attempt) + random_jitter, 60s)`

**Retryable errors:**
- Connection failures (APIConnectionError)
- Rate limits (RateLimitError, status 429)
- Server errors (status 500, 502, 503, 504, 529)

**Non-retryable errors:**
- Authentication errors (status 401, 403)
- Not found errors (status 404)
- Validation errors

### 2. User-Friendly Error Messages

**Location:** `backend/claude_service.py:57-90`

All technical errors are translated to user-friendly messages:

| Error Type | User Message |
|------------|--------------|
| RateLimitError | "You've made too many requests. Please wait a moment and try again." |
| APIConnectionError | "Unable to connect to the AI service. Please check your internet connection and try again." |
| Status 401 | "API authentication failed. Please check your API key configuration." |
| Status 429 | "Service is experiencing high demand. Please try again in a moment." |
| Status 500 | "The AI service encountered an internal error. Please try again later." |
| Status 529 | "The AI service is temporarily overloaded. Please try again in a few minutes." |
| JSON errors | "Received an invalid response from the AI service. Please try again." |
| Other errors | "An unexpected error occurred while generating the quiz. Please try again." |

### 3. Fallback Mechanism

**Location:** `backend/claude_service.py:248-326`

When the Claude API is unavailable or fails after all retries, the system automatically falls back to a local quiz generator:

- **Pre-configured questions** for common algebra topics
- **Topics covered:** Linear Equations, Quadratic Equations, Polynomials, Factoring
- **Seamless fallback:** No user intervention required
- **Quality maintained:** All fallback questions include explanations and correct answers

### 4. Comprehensive Logging

**Location:** Throughout `backend/claude_service.py`

All API interactions are logged for debugging and monitoring:

- Initialization events
- API call attempts
- Retry attempts with delays
- Success/failure outcomes
- Error details (without exposing sensitive data)

## Usage

### Basic Usage

```python
from claude_service import ClaudeService, ClaudeAPIError, FallbackQuizGenerator

# Initialize service with custom retry settings
service = ClaudeService(
    api_key="your-api-key",
    max_retries=3,
    initial_retry_delay=1.0
)

# Generate quiz questions with automatic error handling
try:
    questions = await service.generate_quiz_questions(
        topic="linear_equations",
        num_questions=5,
        student_context={
            "grade_average": "75%",
            "struggling_topics": "Linear Equations"
        }
    )
except ClaudeAPIError as e:
    # Handle error with user-friendly message
    print(f"Error: {e.message}")

    # Use fallback if needed
    questions = FallbackQuizGenerator.generate_fallback_questions(
        topic="linear_equations",
        num_questions=5
    )
```

### Integration in FastAPI

The error handling is integrated in `backend/main.py:124-202`:

```python
# Service is initialized on startup
claude_service = ClaudeService(
    api_key=api_key,
    max_retries=3,
    initial_retry_delay=1.0
)

# Automatic fallback in quiz generation endpoint
questions = await claude_service.generate_quiz_questions(...)
```

## Testing

Run the comprehensive test suite:

```bash
cd backend
python3 test_error_handling.py
```

**Test coverage:**
- Exponential backoff calculations
- User-friendly error message generation
- Retry logic decision making
- Fallback quiz generator
- Integration scenarios

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional (defaults shown)
CLAUDE_MAX_RETRIES=3
CLAUDE_INITIAL_RETRY_DELAY=1.0
```

### Runtime Configuration

```python
# Configure at initialization
service = ClaudeService(
    api_key=api_key,
    max_retries=5,              # More retries for production
    initial_retry_delay=2.0     # Longer initial delay
)
```

## Error Flow Diagram

```
API Call Attempt
    |
    ├─ Success ──────────────────────────> Return Questions
    |
    └─ Error
        |
        ├─ Retryable? (connection, rate limit, server error)
        |   |
        |   ├─ Yes, attempts left?
        |   |   |
        |   |   ├─ Yes ──> Wait (exponential backoff) ──> Retry
        |   |   |
        |   |   └─ No ──> User-Friendly Error ──> Fallback Quiz
        |   |
        |   └─ No (auth, validation error) ──> User-Friendly Error ──> Fallback Quiz
        |
        └─ Fallback Quiz Generated ────────────────────> Return Questions
```

## Best Practices

1. **Always catch ClaudeAPIError:** This provides user-friendly error messages
2. **Use fallback generator:** Ensure users always get content even if API fails
3. **Monitor logs:** Review error logs to identify patterns and issues
4. **Adjust retry settings:** Tune based on your application's needs and API limits
5. **Test error scenarios:** Regularly test with network issues and rate limits

## Future Enhancements

Potential improvements for consideration:

- Circuit breaker pattern to prevent overwhelming the API
- Request queuing for rate limit management
- Caching successful responses to reduce API calls
- Metrics collection for monitoring (response times, error rates)
- Custom fallback quiz generation based on student performance

## Support

For issues or questions:
- Check logs for detailed error information
- Review test results: `python3 test_error_handling.py`
- Consult Anthropic API documentation: https://docs.anthropic.com
