# 📌 KajBuzz: An Intelligent Task Planner 🚀

> *Your virtual assistant for managing tasks, time, and productivity.*

![KajBuzz](https://img.shields.io/badge/Version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.13.1-green)
![Django](https://img.shields.io/badge/Django-5.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

KajBuzz is a **web-based productivity assistant** designed for students and professionals. It helps manage tasks, exams, assignments, projects, and personal reminders while automating scheduling and providing smart productivity insights.  

---
## 🔗 Useful Links  

- 🌐 **Live Hosting**: [KajBuzz on PythonAnywhere](https://rayed.pythonanywhere.com/)  

---
## 👨‍💻 Team Members  

- **Rayed Riasat Rabbi**  
- **Md. Azmine Amin Mormo** 
- **Barshon Basak** 
- **Md. Tazrian Hasnat**

---
## 🛠 Technology Stack  

**Frontend**: Django Templates, TailwindCSS, HTMX, AlpineJS  
**Backend**: Django 5 (Python 3.13.1)  
**Database**: MySQL (Django ORM)  
**Auth**: Django Allauth (Email & Google OAuth)  
**Background Tasks**: Django-Q  
**Deployment**: PythonAnywhere  
**Integrations**: Google Calendar API, Canvas LMS, Stripe Subscriptions  
**AI**: OpenRouter API, scikit-learn  

---
## ✨ Features

### 🎯 Core Functionality
- **📝 Task Management** - CRUD operations with priorities, deadlines, and effort estimates
- **🤖 Auto-Scheduling** - Rule-based engine using time blocks
- **🖱️ Manual Editing** - Drag-and-drop with event locking
- **📋 Kanban & List Views** - Multiple task visualization options
- **⏰ Pomodoro Timer** - Focus sessions with break reminders (Premium)
- **📅 Google Calendar Sync** - OAuth 2.0 integration

### 🤖 AI Enhancements
- **🧠 AI Scheduling Suggestions** - OpenRouter API integration
- **💬 AI Chatbot** - Scheduling and productivity advice
- **🎤 Voice Assistant** - Voice commands for task management (Premium)

### 📊 Analytics & Insights
- **📈 Progress Tracking** - Actual vs. estimated time analysis
- **✅ Habit Tracking** - Build and monitor daily habits
- **🔥 Consistency Heatmap** - Visual task completion history
- **📄 PDF Export** - Printable schedule summaries

### 🔐 User Management
- **🔐 Authentication** - Email + Google OAuth login
- **🎭 Role-Based Access** - Regular, Premium, and Admin roles
- **🔔 Notifications** - Browser + email reminders

### 🎨 UX & Customization
- **🌙 Dark/Light Mode** - Theme switching
- **📱 Responsive Design** - Mobile and desktop optimized
- **🎓 Canvas LMS Integration** - Auto-import assignments

## ⚡ Installation & Setup  

```bash
# Clone the repository
git clone https://github.com/your-username/KajBuzz.git
cd KajBuzz

# Create virtual environment
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Run server
python manage.py runserver

```
### Files Arrangement
```
intelligent_task_planner,
├─ intelligent_task_planner,
│  ├─ asgi.py,
│  ├─ settings.py,
│  ├─ urls.py,
│  ├─ wsgi.py,
│  └─ __init__.py,
├─ manage.py,
├─ package.json,
├─ planner,
│  ├─ admin.py,
│  ├─ apps.py,
│  ├─ forms.py,
│  ├─ migrations,
│  │  ├─ 0001_initial.py,
│  │  ├─ 0002_alter_task_options_and_more.py,
│  │  └─ __init__.py,
│  ├─ models.py,
│  ├─ services,
│  │  ├─ scheduling_engine.py,
│  │  └─ __init__.py,
│  ├─ templates,
│  │  └─ planner,
│  │     ├─ calendar.html,
│  │     ├─ kanban.html,
│  │     ├─ onboarding.html,
│  │     └─ partials,
│  │        ├─ calendar_task.html,
│  │        ├─ task_card.html,
│  │        └─ unscheduled_task.html,
│  ├─ tests.py,
│  ├─ urls.py,
│  ├─ views.py,
│  └─ __init__.py,
├─ pyproject.toml,
├─ requirements.txt,
├─ static,
│  ├─ css,
│  │  └─ input.css,
│  ├─ images,
│  └─ js,
├─ tailwind.config.js,
├─ templates,
│  ├─ account,
│  │  ├─ base.html,
│  │  ├─ email_confirmation_signup.html,
│  │  ├─ login.html,
│  │  ├─ logout.html,
│  │  └─ signup.html,
│  ├─ base.html,
│  └─ landing.html,
└─ uv.lock,

```

