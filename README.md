<div align="center">

# 🚀 ScoutIQ

### *The AI That Scouts Opportunities Before You Do*

An AI-powered multi-agent career assistant built using **Google ADK** that helps job seekers discover opportunities, verify employers, track applications, and monitor recruiter emails from one intelligent workspace.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)]()
[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4?style=for-the-badge&logo=google&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)]()
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)]()

</div>

---

# 🌟 Overview

Searching for jobs today often means juggling multiple websites, verifying whether companies are genuine, manually tracking applications, and constantly checking emails for recruiter updates.

**ScoutIQ** simplifies this entire journey using multiple AI agents working together.

Instead of switching between platforms, ScoutIQ provides one intelligent dashboard that analyzes resumes, recommends personalized jobs, verifies employer trust, tracks applications, and automatically monitors recruiter emails.

---

# ✨ Features

## 📄 Resume Intelligence
- Extracts skills, education, internships and projects
- Creates a structured candidate profile
- SHA-256 resume caching to reduce repeated AI calls

---

## 🎯 Smart Job Discovery
- Role-aware job matching
- Personalized recommendations
- Location, salary and work-mode filtering

---

## 🛡 Company Verification
- Trust analysis
- Scam detection
- Employer credibility checks

---

## 📋 Application Tracker
- Track every application
- View interview progress
- Update application stages

---

## 📧 Email Monitoring Agent
Supports **Dual Mode**

✅ Mock Mode (No setup required)

✅ Live Gmail Mode (Google OAuth)

Automatically detects:

- Interview Invitations
- Assessment Links
- Offer Letters
- Rejections
- Application Confirmations

Updates the tracker automatically.

---

# 🤖 Multi-Agent Architecture

ScoutIQ is powered by specialized AI agents:

| Agent | Responsibility |
|--------|----------------|
| Resume Analyzer Agent | Resume Parsing |
| Job Discovery Agent | Finds relevant jobs |
| Company Verification Agent | Verifies employer trust |
| Application Tracker Agent | Tracks applications |
| Email Monitoring Agent | Reads recruiter emails |

---

# 🏗 System Architecture

> Add your architecture diagram here.

Example:

```
User
   │
   ▼
Streamlit Frontend
   │
FastAPI Backend
   │
Google ADK
   │
──────────────────────────────
Resume Agent
Job Agent
Verification Agent
Tracker Agent
Email Agent
──────────────────────────────
   │
SQLite Database
Gemini AI
MCP Server
```

---

# 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python |
| Multi-Agent Framework | Google ADK |
| Backend | FastAPI |
| Frontend | Streamlit |
| Database | SQLite |
| AI Model | Gemini |
| Protocol | MCP |
| Authentication | Google OAuth |

---

# 📂 Project Structure

```
ScoutIQ/

├── agents/
│   ├── resume_analyzer.py
│   ├── discovery.py
│   ├── verification.py
│   ├── tracker.py
│   └── email_monitor.py
│
├── api/
├── database/
├── docs/
├── mcp_servers/
├── tests/
├── tools/
│
├── app.py
├── main.py
├── requirements.txt
└── README.md
```

---

# ⚙ Installation

Clone the repository

```bash
git clone https://github.com/nehaeluvathingal/ScoutIQ.git
```

Move into the folder

```bash
cd ScoutIQ
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

# ▶ Running the Application

Start the backend

```bash
python main.py
```

Start Streamlit

```bash
streamlit run app.py
```

---

# 📸 Screenshots

Add screenshots of:

- 🏠 Home Dashboard
- 📄 Resume Upload
- 🎯 Job Discovery
- 📋 Application Tracker
- 📧 Email Monitor

---

# 🎥 Demo Video

🔗 **YouTube Demo**

Paste your **Unlisted YouTube link** here after uploading.

---

# 🧠 Concepts Demonstrated

This project demonstrates multiple concepts from the **Google AI Agents Intensive Course**:

- ✅ Google ADK Multi-Agent System
- ✅ Model Context Protocol (MCP)
- ✅ Tool Calling
- ✅ Agent Orchestration
- ✅ Secure Authentication
- ✅ Hybrid AI Workflows
- ✅ AI-powered Classification

---

# 🔮 Future Improvements

- LinkedIn integration
- Naukri integration
- Indeed integration
- ATS Resume Score
- Interview Preparation Agent
- Salary Prediction Agent
- Cover Letter Generator
- Calendar Integration

---

# 👩‍💻 Author

**Neha Eluvathingal**

Computer Science & Business Systems Graduate

Kaggle AI Agents Capstone Project

---

<div align="center">

## ⭐ If you found this project interesting, consider giving it a star!

</div>
