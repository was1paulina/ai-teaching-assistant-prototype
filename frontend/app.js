// frontend/app.js
const API_URL = 'http://localhost:8000';

let studentsData = [];
let currentStudent = null;
let currentFilter = 'all';

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadData();
    setupEventListeners();
});

async function loadData() {
    try {
        // Load students
        const studentsResponse = await fetch(`${API_URL}/api/students`);
        studentsData = await studentsResponse.json();

        // Load analytics
        const analyticsResponse = await fetch(`${API_URL}/api/analytics`);
        const analytics = await analyticsResponse.json();

        // Update UI
        updateAnalytics(analytics);
        updateTopics(analytics.top_struggle_topics);
        renderStudents();

    } catch (error) {
        console.error('Error loading data:', error);
        alert('Failed to load data. Make sure the backend server is running.');
    }
}

function updateAnalytics(analytics) {
    document.getElementById('total-students').textContent = analytics.total_students;
    document.getElementById('at-risk').textContent = analytics.at_risk_count;
    document.getElementById('avg-risk-score').textContent =
        analytics.avg_risk_score.toFixed(1);
}

function updateTopics(topics) {
    const topicsList = document.getElementById('topics-list');
    topicsList.innerHTML = topics.slice(0, 5).map(topic => `
        <div class="topic-item">
            <span class="topic-name">${formatTopic(topic.topic)}</span>
            <span class="topic-count">${topic.count}</span>
        </div>
    `).join('');
}

function renderStudents() {
    const grid = document.getElementById('students-grid');

    const filteredStudents = studentsData.filter(student => {
        if (currentFilter === 'all') return true;
        return student.risk_level === currentFilter;
    });

    grid.innerHTML = filteredStudents.map(student => {
        const riskIcon = getRiskIcon(student.risk_level);
        const latestGrade = student.assignments[student.assignments.length - 1]?.score || 0;
        const daysInactive = getDaysInactive(student.last_active);

        return `
            <div class="student-card" onclick="showStudentDetail('${student.id}')">
                <div class="student-header">
                    <div class="student-name">${student.name}</div>
                    <div class="risk-indicator">${riskIcon}</div>
                </div>
                <div class="student-details">
                    <div class="detail-row">
                        <span>Latest Grade:</span>
                        <span class="assignment-score ${getScoreClass(latestGrade)}">
                            ${latestGrade.toFixed(0)}%
                        </span>
                    </div>
                    <div class="detail-row">
                        <span>Risk Score:</span>
                        <span>${student.risk_score}</span>
                    </div>
                    <div class="detail-row">
                        <span>Last Active:</span>
                        <span>${daysInactive}</span>
                    </div>
                    <div class="detail-row">
                        <span>Status:</span>
                        <span class="risk-badge ${student.risk_level}">
                            ${student.risk_level}
                        </span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function showStudentDetail(studentId) {
    currentStudent = studentsData.find(s => s.id === studentId);
    if (!currentStudent) return;

    // Update modal content
    document.getElementById('modal-student-name').textContent = currentStudent.name;
    document.getElementById('modal-risk').textContent = currentStudent.risk_level.toUpperCase();
    document.getElementById('modal-risk').className = `risk-badge ${currentStudent.risk_level}`;
    document.getElementById('modal-risk-score').textContent = currentStudent.risk_score;
    document.getElementById('modal-last-active').textContent =
        formatDate(currentStudent.last_active);

    // Render assignments
    const assignmentsList = document.getElementById('modal-assignments');
    assignmentsList.innerHTML = currentStudent.assignments.map(assignment => `
        <div class="assignment-item">
            <div class="assignment-name">${assignment.name}</div>
            <div class="assignment-score ${getScoreClass(assignment.score)}">
                ${assignment.score.toFixed(0)}%
            </div>
            <div class="assignment-meta">
                ${assignment.attempts} attempt${assignment.attempts > 1 ? 's' : ''}<br>
                ${assignment.time_spent_minutes} min
            </div>
        </div>
    `).join('');

    // Render struggling topics
    const topicsList = document.getElementById('modal-topics');
    if (currentStudent.struggling_topics.length > 0) {
        topicsList.innerHTML = currentStudent.struggling_topics.map(topic => `
            <span class="topic-tag">${formatTopic(topic)}</span>
        `).join('');
    } else {
        topicsList.innerHTML = '<p style="color: var(--gray-600)">No struggling topics identified</p>';
    }

    // Populate topic selector
    const topicSelect = document.getElementById('quiz-topic-select');
    topicSelect.innerHTML = '<option value="">Select a topic...</option>' +
        currentStudent.struggling_topics.map(topic => `
            <option value="${topic}">${formatTopic(topic)}</option>
        `).join('');

    // Clear any previous quiz
    document.getElementById('quiz-container').classList.add('hidden');

    // Show modal
    document.getElementById('student-modal').classList.remove('hidden');
}

function closeModal() {
    document.getElementById('student-modal').classList.add('hidden');
    currentStudent = null;
}

async function generateQuiz() {
    if (!currentStudent) return;
    
    const topicSelect = document.getElementById('quiz-topic-select');
    const topic = topicSelect.value;
    
    if (!topic) {
        alert('Please select a topic first');
        return;
    }
    
    // Show loading
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        const response = await fetch(`${API_URL}/api/quiz/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                student_id: currentStudent.id,
                topic: topic,
                num_questions: 5
            })
        });
        
        if (!response.ok) {
            throw new Error('Failed to generate quiz');
        }
        
        const quiz = await response.json();
        displayQuiz(quiz);
        
    } catch (error) {
        console.error('Error generating quiz:', error);
        alert('Failed to generate quiz. Please check your Claude API key.');
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
}

function displayQuiz(quiz) {
    const container = document.getElementById('quiz-container');

    container.innerHTML = `
        <div class="quiz-header">
            <h3>📝 Practice Quiz: ${quiz.topic}</h3>
            <p style="color: var(--gray-600); margin-top: 5px;">
                Generated for ${currentStudent.name}
            </p>
        </div>
        ${quiz.questions.map((q, index) => `
            <div class="quiz-question">
                <div class="question-number">Question ${index + 1} of ${quiz.questions.length}</div>
                <div class="question-text">${q.question}</div>
                <div class="quiz-options">
                    ${Object.entries(q.options).map(([key, value]) => `
                        <div class="quiz-option ${key === q.correct ? 'correct' : ''}">
                            <strong>${key})</strong> ${value}
                        </div>
                    `).join('')}
                </div>
                <div class="quiz-explanation">
                    <div class="explanation-label">✓ Correct Answer: ${q.correct}</div>
                    <div>${q.explanation}</div>
                </div>
            </div>
        `).join('')}
    `;

    container.classList.remove('hidden');

    // Scroll to quiz
    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function setupEventListeners() {
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.filter-btn').forEach(b =>
                b.classList.remove('active'));
            e.target.classList.add('active');

            currentFilter = e.target.dataset.filter;
            renderStudents();
        });
    });

    // Close modal on outside click
    document.getElementById('student-modal').addEventListener('click', (e) => {
        if (e.target.id === 'student-modal') {
            closeModal();
        }
    });
}

// Helper functions
function getRiskIcon(level) {
    const icons = {
        high: '🔴',
        medium: '🟡',
        low: '🟢'
    };
    return icons[level] || '⚪';
}

function getScoreClass(score) {
    if (score >= 80) return 'score-high';
    if (score >= 60) return 'score-medium';
    return 'score-low';
}

function formatTopic(topic) {
    return topic.split('_').map(word =>
        word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
    });
}

function getDaysInactive(lastActiveString) {
    const lastActive = new Date(lastActiveString);
    const now = new Date();
    const days = Math.floor((now - lastActive) / (1000 * 60 * 60 * 24));

    if (days === 0) return 'Today';
    if (days === 1) return '1 day ago';
    return `${days} days ago`;
}
