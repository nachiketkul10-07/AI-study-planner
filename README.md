# 📚 AI Study Planner

A production-ready Streamlit application that generates personalised study schedules — no API keys, no external services required.

## ✨ Features

- **Smart Scheduling** — Distributes study hours by subject difficulty
- **4 Study Styles** — Balanced, Intensive, Slow & Steady, Night Owl
- **Interactive Checklist** — Track daily tasks with checkboxes
- **Progress Tracker** — Visual progress bar across all study days
- **Subject Chart** — Bar chart of allocated hours per subject
- **Recovery Days** — Optional buffer days every 6 study days
- **Motivational Tips** — Daily tips to keep you on track
- **Export to Markdown** — Download your full plan as a `.md` file

### 🆕 Advanced Features

- **⏱️ Pomodoro Timer** — Built-in focus timer with 25/5 Pomodoro and 50/10 Deep Work modes, SVG ring animation, session counter, and audio notifications
- **📊 Analytics Dashboard** — Plotly-powered donut chart (subject distribution), area chart (daily hours), GitHub-style heatmap calendar, and cumulative progress tracker
- **📝 Per-Subject Topics** — Break subjects into chapters/topics for more focused scheduling with automatic round-robin cycling across study days
- **📅 Calendar Export** — Download your plan as an `.ics` file importable into Google Calendar, Outlook, and Apple Calendar
- **💾 Save & Load Plans** — Persist study plans as JSON files, load previous plans, auto-save progress so checkboxes survive page refreshes

## 🗂️ Project Structure

```
ai_study_planner/
├── app.py                    # Main Streamlit application
├── requirements.txt
├── README.md
├── saved_plans/              # Auto-created — saved plan JSON files
└── utils/
    ├── __init__.py
    ├── validators.py         # Input validation (subjects, dates, topics)
    ├── prompt_builder.py     # Schedule generation with topic support
    ├── ui_helpers.py         # All Streamlit rendering functions
    ├── pomodoro.py           # Pomodoro timer HTML/CSS/JS component
    ├── analytics.py          # Plotly analytics dashboard
    ├── calendar_export.py    # ICS calendar file generation
    └── storage.py            # JSON-based save/load system
```

## 🚀 Getting Started

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

### 3. Open in browser
Streamlit will open the app at `http://localhost:8501`

## 🎯 How to Use

1. Enter your subjects (comma-separated)
2. Set difficulty levels (1–5) for each subject
3. *(Optional)* Add topics/chapters for each subject
4. Pick your exam/deadline date
5. Choose daily study hours and study style
6. Toggle recovery days and motivational tips
7. Click **Generate My Study Plan**
8. Use the **📋 Schedule** tab to track daily progress
9. Check the **📊 Analytics** tab for visual insights
10. Use the **⏱️ Pomodoro Timer** for focused study sessions
11. Download your plan as `.md` or `.ics` from the Schedule tab
12. Save/load plans from the sidebar

## 🛠️ Tech Stack

- **Python 3.10+**
- **Streamlit** — UI framework
- **Pandas** — Data handling for charts
- **Plotly** — Interactive analytics visualisations
- No external APIs required

## 📄 License

MIT — free to use and modify.
