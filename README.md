# AI Teaching Assistant - Proactive Student Intervention System

## Overview

An AI-powered middleware that sits on top of Learning Management Systems to automatically identify struggling students and provide personalized support before they drop out.



## Problem Statement

Online course instructors managing 100+ students cannot monitor individual progress in real-time. Students fail silently until it's too late. Traditional LMS platforms are reactive, not proactive.

## Solution

This system:
- **Monitors** student performance patterns (grades, attempts, engagement)
- **Identifies** at-risk students using risk scoring algorithm
- **Intervenes** automatically with AI-generated personalized practice materials
- **Provides** instructors with actionable insights (top struggle topics, class-wide metrics)

## Key Features

### 1. Risk Detection Engine
Analyzes multiple signals:
- Grade trends (declining pattern detection)
- Assignment attempts (>3 attempts = struggle indicator)
- Time spent (>2x class average = struggling)
- Engagement (days since last active)
- Produces risk score (0-100) with categorization (🔴 High, 🟡 Medium, 🟢 Low)

### 2. Instructor Dashboard
- Real-time view of all students with risk indicators
- Course-wide analytics (18/30 students at risk)
- Top struggle topics identified automatically
- Individual student performance timelines

### 3. AI-Powered Quiz Generation
- Integrates with Claude API (Anthropic)
- Generates personalized practice questions based on:
  - Student's current skill level
  - Specific struggling topics
  - Recent performance patterns
- Includes detailed explanations for each answer

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI (REST API)
- Anthropic Claude API (Sonnet 4)
- Pydantic (data validation)

**Frontend:**
- Vanilla JavaScript (no framework dependencies)
- HTML5/CSS3
- Fetch API for backend communication

**Architecture:**
- RESTful API design
- In-memory mock data (production would use PostgreSQL/MongoDB)
- Modular risk scoring algorithm

## Demo Setup

### Prerequisites
- Python 3.10+
- Claude API key from [Anthropic](https://console.anthropic.com/)

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/ai-teaching-assistant-demo.git
cd ai-teaching-assistant-demo

# Backend setup
cd backend
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your_key_here" > .env
python main.py

# Frontend setup (new terminal)
cd ../frontend
python -m http.server 3000
```

Open `http://localhost:3000`

## Demo Data

The system includes 30 mock students across 4 archetypes:
- **Declining (6 students):** Grades dropping steadily (85→58%)
- **Struggling (6 students):** Low scores, multiple attempts
- **Moderate (12 students):** Some challenges, ~70% average
- **Thriving (6 students):** Strong performance, 88-94%

## API Endpoints
```
GET  /api/students          # All students with risk calculations
GET  /api/students/{id}     # Individual student details
GET  /api/analytics         # Course-wide metrics
POST /api/quiz/generate     # Generate AI-powered quiz
```

## Risk Scoring Algorithm
```python
Risk Score = Grade Trend (0-20) 
           + Absolute Performance (0-25)
           + Assignment Attempts (0-15)
           + Engagement (0-15)
           + Time Spent (0-10)

Categories:
- High Risk: 41-100 (immediate intervention)
- Medium Risk: 21-40 (monitor closely)
- Low Risk: 0-20 (on track)
```

## Future Enhancements (Production Roadmap)

### Phase 1: Real LMS Integration
- Canvas API integration
- Moodle connector
- Brightspace/D2L support

### Phase 2: Enhanced AI Features
- Automated intervention messages
- Flashcard generation
- Study guide creation
- Chat-based tutoring

### Phase 3: Advanced Analytics
- Predictive dropout modeling
- Cohort analysis
- A/B testing framework
- Instructor effectiveness metrics

### Phase 4: Enterprise Features
- Multi-tenancy support
- Role-based access control
- SSO integration
- White-label branding

## Business Model

**Target Market:** Small-to-medium online education companies

**Pricing Strategy:**
- Tier 1: $200-500/month (up to 500 students)
- Tier 2: $500-1000/month (500-2000 students)
- Enterprise: Custom pricing (2000+ students)

**Value Proposition:**
- Instructors save 4-5 hours/week
- Improve completion rates by 10-15%
- Identify struggling students 2-4 weeks earlier
- Reduce support ticket volume by 30%

## Why This Matters

**Market Opportunity:**
- Online education market: $350B by 2025
- Average course completion rate: 40-60%
- Each dropout = lost revenue + damaged reputation

**Impact:**
- Instructors: Scale personalized support
- Students: Get help before failing
- Institutions: Improve outcomes, increase revenue

## About This Project

Built as a **technical product demo** to showcase:
- End-to-end product development (concept → working prototype)
- AI/ML integration (Claude API, prompt engineering)
- Full-stack capabilities (Python backend, vanilla JS frontend)
- Product thinking (problem identification, user personas, business model)

**Development Time:** ~2 days (including research, design, implementation)

## Contact

**Paulina Tsaryk**
- LinkedIn: https://www.linkedin.com/in/paulinatsaryk/
- Email: palina.tsaryk@gmail.com

---

*This is a demonstration prototype. For production deployment, additional work is required: authentication, database persistence, security hardening, LMS integration, comprehensive testing, and scalability improvements.*