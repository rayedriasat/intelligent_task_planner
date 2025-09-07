# KajBuzz - Intelligent Task Planner

[![Python](https://img.shields.io/badge/Python-3.13.1-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-5.2.4-092E20?logo=django)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An AI-powered academic task planning system that helps students manage assignments, optimize schedules, and integrate seamlessly with educational tools.

**Live Demo**: https://Rayed.pythonanywhere.com

## 🌟 Key Features

### 🤖 AI Schedule Assistant
Our flagship feature uses advanced AI to intelligently schedule your tasks based on:
- Task priorities and deadlines
- Your available time blocks
- Estimated task durations
- Workload balancing

<img src="https://github.com/user-attachments/assets/bde9a136-3633-4a45-a19e-8e45dfdb4d6e" alt="AI Chat" width="95%">

*AI Chat Interface - Discuss your schedule and get intelligent recommendations*

### 📅 Smart Scheduling Engine
Automatically places tasks in optimal time slots while respecting your availability and preventing overbooking.

<img src="https://github.com/user-attachments/assets/934cb241-b988-4de7-becd-457a4f16f231" alt="Calendar View" width="95%">

*Calendar View - Visualize your scheduled tasks and available time blocks*

<img src="https://github.com/user-attachments/assets/a1361a2f-9a70-4294-ae40-38c7a813163f" alt="Calendar Ai-Suggestion" width="95%">

*Ai Suggestions*


### 🔗 Seamless Integrations
- **Google Calendar**: Bi-directional sync keeps your schedule consistent across platforms
- **Canvas LMS**: Automatically imports assignments and deadlines from your courses

### 🍅 Productivity Tracking
Built-in Pomodoro timer helps you maintain focus and track time spent on tasks.

### 📊 Analytics & Insights
Get insights into your productivity patterns and scheduling optimization history.

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- MySQL 8.0+
- Node.js (for frontend asset compilation)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/rayedriasat/intelligent_task_planner.git
   cd intelligent_task_planner
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp env_example.txt .env
   # Edit .env with your configuration
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Start the development server:
   ```bash
   python manage.py runserver
   ```

## 🎯 Core Functionality

### AI-Powered Task Scheduling
The AI analyzes your tasks and available time to create an optimized schedule:
- Prioritizes urgent tasks automatically
- Respects your defined availability
- Splits large tasks across multiple time blocks when needed
- Provides confidence scores and reasoning for each suggestion

### Intelligent Overload Detection
The system alerts you when your workload exceeds available time and provides actionable recommendations to rebalance your schedule.

### Natural Language Interaction
Chat with our AI assistant to discuss your schedule, ask questions about your tasks, and get personalized productivity recommendations.

## 🛠️ Technology Stack

- **Backend**: Python 3.13, Django 5.2
- **Frontend**: HTMX, Alpine.js, TailwindCSS
- **Database**: MySQL 8.0+
- **AI Integration**: OpenRouter API
- **Task Queue**: Django-Q2
- **Authentication**: Django-allauth with Google OAuth

## 📸 Screenshots

<!-- Add your screenshots here -->
<div style="display: flex; flex-wrap: wrap; gap: 10px;">
  <img src="https://github.com/user-attachments/assets/6564ba27-cca3-4672-a550-1cdab5518242" alt="Dashboard" width="45%">
  <img src="https://github.com/user-attachments/assets/f56c16f9-838d-4989-b75e-318bd5064631" alt="Kanban Board" width="45%">
  <img src="https://github.com/user-attachments/assets/2d4f69dd-b3e6-49aa-88e1-b6c235cfd225" alt="Dark Mode Kanban" width="45%">
  <img src="https://github.com/user-attachments/assets/bde9a136-3633-4a45-a19e-8e45dfdb4d6e" alt="AI Chat" width="45%">
  <img src="https://github.com/user-attachments/assets/5e57d3ff-d7af-4472-9601-0dc54e5be250" alt="LMS Canvas Integration" width="45%">
  <img src="https://github.com/user-attachments/assets/934cb241-b988-4de7-becd-457a4f16f231" alt="Calendar View" width="45%">
  <img src="https://github.com/user-attachments/assets/a1361a2f-9a70-4294-ae40-38c7a813163f" alt="Calendar Ai-Suggestion" width="45%">
  <img src="https://github.com/user-attachments/assets/8dcca8ed-f2e0-49c5-b389-88cb5deba350" alt="Habits" width="45%">
</div>

## 📄 PDF Export
Generate professional PDF schedules for sharing and printing.

## 🔐 Security
- Secure authentication with Google OAuth
- API key protection for external services
- Data encryption for sensitive information

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Thanks to all contributors who have helped shape this project
- OpenRouter for providing the AI capabilities
- PythonAnywhere for hosting platform
