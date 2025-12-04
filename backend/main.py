# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
from dotenv import load_dotenv
from pydantic import BaseModel

from models import Student, QuizResponse, CourseAnalytics, QuizQuestion
from mock_data import generate_mock_students
from risk_engine import calculate_risk_score, get_risk_level
from claude_service import ClaudeService, ClaudeAPIError, FallbackQuizGenerator

class QuizRequest(BaseModel):
    student_id: str
    topic: str
    num_questions: int = 5

load_dotenv()

app = FastAPI(title="AI Teaching Assistant Demo")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for demo
students_db: List[Student] = []

# Claude service instance (initialized on startup)
claude_service: Optional[ClaudeService] = None
use_fallback: bool = False

@app.on_event("startup")
async def startup_event():
    """Initialize mock data and Claude service on startup"""
    global students_db, claude_service, use_fallback

    students_db = generate_mock_students(30)
    print(f"✅ Generated {len(students_db)} mock students")

    # Initialize Claude service
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if api_key:
        try:
            # Configure retry settings (3 retries, 1 second initial delay)
            claude_service = ClaudeService(
                api_key=api_key,
                max_retries=3,
                initial_retry_delay=1.0
            )
            print("✅ Claude service initialized with error handling")
        except ClaudeAPIError as e:
            print(f"⚠️ Claude service initialization failed: {e.message}")
            print("   Using fallback quiz generator")
            use_fallback = True
    else:
        print("⚠️ No ANTHROPIC_API_KEY found. Using fallback quiz generator.")
        use_fallback = True

@app.get("/")
async def root():
    return {
        "message": "AI Teaching Assistant Demo API",
        "endpoints": {
            "students": "/api/students",
            "analytics": "/api/analytics",
            "quiz": "/api/quiz/generate"
        }
    }

@app.get("/api/students", response_model=List[Student])
async def get_students():
    """Get all students with risk calculations"""
    return students_db

@app.get("/api/students/{student_id}", response_model=Student)
async def get_student(student_id: str):
    """Get single student details"""
    student = next((s for s in students_db if s.id == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.get("/api/analytics", response_model=CourseAnalytics)
async def get_analytics():
    """Get course-wide analytics"""
    total = len(students_db)

    # Count risk levels
    high_risk = sum(1 for s in students_db if s.risk_level == "high")
    medium_risk = sum(1 for s in students_db if s.risk_level == "medium")
    low_risk = sum(1 for s in students_db if s.risk_level == "low")

    # Calculate top struggle topics
    topic_counts = {}
    for student in students_db:
        for topic in student.struggling_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

    top_topics = sorted(
        [{"topic": topic, "count": count} for topic, count in topic_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]

    # Average risk score
    avg_risk = sum(s.risk_score for s in students_db) / total if total > 0 else 0

    return CourseAnalytics(
        total_students=total,
        at_risk_count=high_risk + medium_risk,
        risk_breakdown={"high": high_risk, "medium": medium_risk, "low": low_risk},
        top_struggle_topics=top_topics,
        avg_risk_score=round(avg_risk, 1)
    )

@app.post("/api/quiz/generate", response_model=QuizResponse)
async def generate_quiz(request: QuizRequest):
    """Generate practice quiz using Claude API with robust error handling"""

    print(f"\n🎯 Quiz generation requested:")
    print(f"   Student: {request.student_id}")
    print(f"   Topic: {request.topic}")
    print(f"   Questions: {request.num_questions}")

    # Get student context
    student = next((s for s in students_db if s.id == request.student_id), None)
    if not student:
        print(f"❌ Student not found: {request.student_id}")
        raise HTTPException(status_code=404, detail="Student not found")

    print(f"✅ Student found: {student.name}")

    # Format topic for display
    topic_display = request.topic.replace("_", " ").title()

    # Prepare student context for Claude
    student_context = {
        "grade_average": f"{student.assignments[-1].score:.0f}%" if student.assignments else "N/A",
        "struggling_topics": ', '.join(student.struggling_topics) if student.struggling_topics else "None"
    }

    questions = None
    used_fallback = False

    # Try to use Claude API if available
    if not use_fallback and claude_service:
        try:
            print("📞 Attempting to generate quiz with Claude API...")
            questions = await claude_service.generate_quiz_questions(
                topic=request.topic,
                num_questions=request.num_questions,
                student_context=student_context
            )
            print("🎉 Quiz generated successfully with Claude API!")

        except ClaudeAPIError as e:
            print(f"⚠️ Claude API error: {e.message}")

            # Check if we should use fallback
            if e.original_error:
                print(f"   Original error: {type(e.original_error).__name__}")

            # Use fallback for certain errors
            print("🔄 Falling back to offline quiz generator...")
            questions = FallbackQuizGenerator.generate_fallback_questions(
                topic=request.topic,
                num_questions=request.num_questions
            )
            used_fallback = True

            # Return user-friendly error with fallback questions
            print("✅ Generated fallback quiz")

    # Use fallback if Claude service not available
    if questions is None:
        print("🔄 Using fallback quiz generator (Claude API not configured)...")
        questions = FallbackQuizGenerator.generate_fallback_questions(
            topic=request.topic,
            num_questions=request.num_questions
        )
        used_fallback = True
        print("✅ Generated fallback quiz")

    # Create response
    quiz_id = f"quiz-{request.student_id}-{request.topic}"
    if used_fallback:
        quiz_id += "-fallback"

    return QuizResponse(
        quiz_id=quiz_id,
        student_id=request.student_id,
        topic=topic_display,
        questions=questions
    )
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
