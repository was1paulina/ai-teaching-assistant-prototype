# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
from dotenv import load_dotenv
import anthropic
from pydantic import BaseModel

from models import Student, QuizResponse, CourseAnalytics, QuizQuestion
from mock_data import generate_mock_students
from risk_engine import calculate_risk_score, get_risk_level

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

@app.on_event("startup")
async def startup_event():
    """Initialize mock data on startup"""
    global students_db
    students_db = generate_mock_students(30)
    print(f"✅ Generated {len(students_db)} mock students")

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
    """Generate practice quiz using Claude API"""
    
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
    
    # Initialize Claude client
    api_key = os.getenv("ANTHROPIC_API_KEY")
    print(f"🔑 API Key loaded: {api_key[:20] if api_key else 'NONE'}...")
    
    if not api_key:
        print("❌ No API key found in environment!")
        raise HTTPException(status_code=500, detail="Claude API key not configured")
    
    client = anthropic.Anthropic(api_key=api_key)
    print("✅ Anthropic client initialized")
    
    # Format topic for display
    topic_display = request.topic.replace("_", " ").title()
    
    # Create prompt for Claude
    prompt = f"""Generate {request.num_questions} multiple-choice algebra questions about {topic_display} for a high school student.

Student context:
- Current grade average: {student.assignments[-1].score:.0f}%
- Struggling with: {', '.join(student.struggling_topics)}

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
    "topic": "{request.topic}"
  }}
]"""
    
    try:
        print("📞 Calling Claude API...")
        
        # Call Claude API
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        print("✅ Claude API responded!")
        
        # Parse response
        response_text = message.content[0].text.strip()
        print(f"📝 Response length: {len(response_text)} characters")
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        print(f"🔍 Cleaned response preview: {response_text[:100]}...")
        
        # Parse JSON
        import json
        questions_data = json.loads(response_text)
        print(f"✅ Parsed {len(questions_data)} questions")
        
        # Convert to QuizQuestion models
        questions = [QuizQuestion(**q) for q in questions_data]
        
        print("🎉 Quiz generation successful!")
        
        return QuizResponse(
            quiz_id=f"quiz-{request.student_id}-{request.topic}",
            student_id=request.student_id,
            topic=topic_display,
            questions=questions
        )
        
    except Exception as e:
        print(f"\n❌ ERROR during quiz generation:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Message: {str(e)}")
        import traceback
        print(f"   Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")
 
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
