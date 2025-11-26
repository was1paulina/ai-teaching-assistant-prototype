# backend/mock_data.py
from models import Student, Assignment, RiskLevel
from datetime import datetime, timedelta
import random
from typing import List

# Math topics for our demo course
MATH_TOPICS = [
    "linear_equations",
    "quadratic_equations",
    "radicals",
    "exponents",
    "polynomials",
    "factoring",
    "systems_of_equations",
    "inequalities"
]

def generate_mock_students(count: int = 30) -> List[Student]:
    """Generate realistic mock student data"""
    students = []

    # Define student archetypes for realistic scenarios
    archetypes = {
        "declining": 6,      # High risk - grades declining
        "struggling": 6,     # High risk - multiple attempts, low grades
        "moderate": 12,      # Medium risk - some issues
        "thriving": 6        # Low risk - doing well
    }

    student_id = 1

    # Generate "declining" students
    for i in range(archetypes["declining"]):
        name = get_student_name(student_id)
        assignments = generate_declining_assignments()
        student = create_student(student_id, name, assignments, days_inactive=random.randint(3, 7))
        students.append(student)
        student_id += 1

    # Generate "struggling" students
    for i in range(archetypes["struggling"]):
        name = get_student_name(student_id)
        assignments = generate_struggling_assignments()
        student = create_student(student_id, name, assignments, days_inactive=random.randint(0, 4))
        students.append(student)
        student_id += 1

    # Generate "moderate" students
    for i in range(archetypes["moderate"]):
        name = get_student_name(student_id)
        assignments = generate_moderate_assignments()
        student = create_student(student_id, name, assignments, days_inactive=random.randint(0, 3))
        students.append(student)
        student_id += 1

    # Generate "thriving" students
    for i in range(archetypes["thriving"]):
        name = get_student_name(student_id)
        assignments = generate_thriving_assignments()
        student = create_student(student_id, name, assignments, days_inactive=random.randint(0, 2))
        students.append(student)
        student_id += 1

    # Shuffle to mix risk levels
    random.shuffle(students)

    return students

def create_student(student_id: int, name: str, assignments: List[Assignment],
                   days_inactive: int) -> Student:
    """Create student with risk calculation"""
    from risk_engine import calculate_risk_score, get_risk_level, analyze_struggling_topics

    # Create base student
    student = Student(
        id=f"student-{student_id:03d}",
        name=name,
        email=f"{name.lower().replace(' ', '.')}@university.edu",
        last_active=datetime.now() - timedelta(days=days_inactive),
        risk_level=RiskLevel.LOW,  # Will be updated
        risk_score=0,  # Will be updated
        risk_reasons=[],
        assignments=assignments,
        struggling_topics=[]
    )

    # Calculate risk
    risk_score, reasons = calculate_risk_score(student)
    risk_level = get_risk_level(risk_score)
    struggling_topics = analyze_struggling_topics(student)

    student.risk_score = risk_score
    student.risk_level = risk_level
    student.risk_reasons = reasons
    student.struggling_topics = struggling_topics

    return student

def generate_declining_assignments() -> List[Assignment]:
    """Generate assignments with declining grades"""
    base_date = datetime.now() - timedelta(days=60)
    assignments = []

    scores = [85, 78, 72, 65, 58]  # Clear decline
    topics_sequence = [
        ["linear_equations"],
        ["quadratic_equations"],
        ["radicals", "exponents"],
        ["radicals", "polynomials"],
        ["radicals", "factoring"]
    ]

    for i, (score, topics) in enumerate(zip(scores, topics_sequence)):
        assignment = Assignment(
            id=f"assignment-{i+1}",
            name=f"Assignment {i+1}",
            score=score,
            attempts=min(i + 1, 4),  # Increasing attempts
            time_spent_minutes=random.randint(45, 90),
            topics=topics,
            submitted_at=base_date + timedelta(days=i*12)
        )
        assignments.append(assignment)

    return assignments

def generate_struggling_assignments() -> List[Assignment]:
    """Generate assignments with low scores and many attempts"""
    base_date = datetime.now() - timedelta(days=60)
    assignments = []

    scores = [65, 58, 52, 55, 48]
    attempts_list = [3, 4, 5, 4, 5]

    for i, (score, attempts) in enumerate(zip(scores, attempts_list)):
        topics = random.sample(MATH_TOPICS, k=random.randint(1, 2))
        assignment = Assignment(
            id=f"assignment-{i+1}",
            name=f"Assignment {i+1}",
            score=score,
            attempts=attempts,
            time_spent_minutes=random.randint(90, 150),  # Lots of time
            topics=topics,
            submitted_at=base_date + timedelta(days=i*12)
        )
        assignments.append(assignment)

    return assignments

def generate_moderate_assignments() -> List[Assignment]:
    """Generate assignments with moderate performance"""
    base_date = datetime.now() - timedelta(days=60)
    assignments = []

    scores = [75, 72, 68, 70, 73]

    for i, score in enumerate(scores):
        topics = random.sample(MATH_TOPICS, k=random.randint(1, 2))
        assignment = Assignment(
            id=f"assignment-{i+1}",
            name=f"Assignment {i+1}",
            score=score,
            attempts=random.randint(1, 3),
            time_spent_minutes=random.randint(50, 80),
            topics=topics,
            submitted_at=base_date + timedelta(days=i*12)
        )
        assignments.append(assignment)

    return assignments

def generate_thriving_assignments() -> List[Assignment]:
    """Generate assignments with strong performance"""
    base_date = datetime.now() - timedelta(days=60)
    assignments = []

    scores = [88, 90, 92, 89, 94]

    for i, score in enumerate(scores):
        topics = random.sample(MATH_TOPICS, k=random.randint(1, 2))
        assignment = Assignment(
            id=f"assignment-{i+1}",
            name=f"Assignment {i+1}",
            score=score,
            attempts=1,
            time_spent_minutes=random.randint(30, 60),
            topics=topics,
            submitted_at=base_date + timedelta(days=i*12)
        )
        assignments.append(assignment)

    return assignments

def get_student_name(student_id: int) -> str:
    """Generate diverse student names"""
    first_names = [
        "Alice", "Bob", "Carlos", "Diana", "Emma", "Frank",
        "Grace", "Henry", "Iris", "James", "Kate", "Leo",
        "Maria", "Noah", "Olivia", "Peter", "Quinn", "Rosa",
        "Sam", "Tina", "Uma", "Victor", "Wendy", "Xavier",
        "Yuki", "Zara", "Amir", "Bella", "Chen", "Dev"
    ]

    last_names = [
        "Anderson", "Brown", "Chen", "Davis", "Evans", "Foster",
        "Garcia", "Harris", "Ibrahim", "Johnson", "Kumar", "Lee",
        "Martinez", "Nguyen", "O'Brien", "Patel", "Quinn", "Rodriguez",
        "Smith", "Thompson", "Underwood", "Vargas", "Williams", "Xu",
        "Yang", "Zhang", "Ahmed", "Bennett", "Cohen", "Diaz"
    ]

    # Use student_id to get consistent names
    first = first_names[(student_id - 1) % len(first_names)]
    last = last_names[(student_id - 1) % len(last_names)]
    return f"{first} {last}"
