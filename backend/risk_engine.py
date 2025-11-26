# backend/risk_engine.py
from models import Student, RiskLevel
from typing import List

def calculate_risk_score(student: Student) -> tuple[int, List[str]]:
    """
    Calculate risk score (0-100) and identify trigger reasons
    Returns: (risk_score, reasons)
    """
    score = 0
    reasons = []

    assignments = student.assignments
    if not assignments:
        return 0, []

    # Get recent performance data
    recent_grades = [a.score for a in assignments[-4:]]  # Last 4 assignments
    latest_grade = recent_grades[-1] if recent_grades else 100
    latest_attempts = assignments[-1].attempts if assignments else 1

    # 1. Grade trend analysis (0-20 points)
    if len(recent_grades) >= 3:
        if is_declining(recent_grades):
            score += 20
            reasons.append("declining_grades")

    # 2. Absolute performance (0-25 points)
    if latest_grade < 60:
        score += 25
        reasons.append("grade_below_60")
    elif latest_grade < 70:
        score += 15
        reasons.append("grade_below_70")

    # 3. Assignment attempts (0-15 points)
    if latest_attempts >= 5:
        score += 15
        reasons.append("multiple_attempts_5plus")
    elif latest_attempts >= 3:
        score += 10
        reasons.append("multiple_attempts_3plus")

    # 4. Engagement - days since last active (0-15 points)
    from datetime import datetime, timedelta
    days_inactive = (datetime.now() - student.last_active).days
    if days_inactive > 7:
        score += 15
        reasons.append("inactive_7plus_days")
    elif days_inactive > 5:
        score += 10
        reasons.append("inactive_5plus_days")

    # 5. Time spent (0-10 points)
    # Assume class average is 60 minutes per assignment
    class_avg_time = 60
    if assignments[-1].time_spent_minutes > class_avg_time * 2:
        score += 10
        reasons.append("excessive_time")

    return min(score, 100), reasons

def is_declining(grades: List[float]) -> bool:
    """Check if grades show declining trend"""
    if len(grades) < 3:
        return False

    # Simple declining check: each grade lower than previous
    for i in range(1, len(grades)):
        if grades[i] > grades[i-1]:
            return False
    return True

def get_risk_level(risk_score: int) -> RiskLevel:
    """Convert numeric risk score to risk level"""
    if risk_score >= 41:
        return RiskLevel.HIGH
    elif risk_score >= 21:
        return RiskLevel.MEDIUM
    else:
        return RiskLevel.LOW

def analyze_struggling_topics(student: Student) -> List[str]:
    """Identify topics where student struggles"""
    topic_scores = {}

    for assignment in student.assignments:
        for topic in assignment.topics:
            if topic not in topic_scores:
                topic_scores[topic] = []
            topic_scores[topic].append(assignment.score)

    # Topics with average score < 70
    struggling = []
    for topic, scores in topic_scores.items():
        avg_score = sum(scores) / len(scores)
        if avg_score < 70:
            struggling.append(topic)

    return struggling
