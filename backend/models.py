# backend/models.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Assignment(BaseModel):
    id: str
    name: str
    score: float  # 0-100
    attempts: int
    time_spent_minutes: int
    topics: List[str]
    submitted_at: datetime

class Student(BaseModel):
    id: str
    name: str
    email: str
    course_id: str = "math-101"
    last_active: datetime
    risk_level: RiskLevel
    risk_score: int  # 0-100
    risk_reasons: List[str]
    assignments: List[Assignment]
    struggling_topics: List[str]

class QuizQuestion(BaseModel):
    question: str
    options: dict  # {"A": "...", "B": "...", etc}
    correct: str
    explanation: str
    topic: str

class QuizResponse(BaseModel):
    quiz_id: str
    student_id: str
    topic: str
    questions: List[QuizQuestion]

class CourseAnalytics(BaseModel):
    total_students: int
    at_risk_count: int
    risk_breakdown: dict  # {"high": 6, "medium": 12, "low": 12}
    top_struggle_topics: List[dict]  # [{"topic": "radicals", "count": 8}, ...]
    avg_risk_score: float
