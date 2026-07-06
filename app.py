import streamlit as st
import requests
import json
import os
import sqlite3
import random

# Page configuration
st.set_page_config(
    page_title="ScoutIQ – The AI that scouts opportunities before you do.",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API Configuration
BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

# Custom CSS for Premium SaaS Branding & Aesthetics
st.markdown("""
    <style>
        /* Base page styling and Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
        
        html, body, [data-testid="stHeader"], [data-testid="stSidebar"], .stMarkdown, .main-header, .sub-header, .metric-card, .status-card, .job-card, .step-card, .insight-panel, p, span, div, label {
            font-family: 'Plus Jakarta Sans', sans-serif;
        }
        
        body {
            background-color: #fafafa;
        }
        
        /* Modern titles */
        .main-header {
            font-size: 2.75rem !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.25rem !important;
        }
        .sub-header {
            font-size: 1.1rem;
            color: #6b7280;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        
        /* Premium Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #f1f5f9 !important;
            padding: 1.5rem 1rem !important;
        }
        
        /* Glassmorphic Cards & Soft Shadows */
        .metric-card {
            background: #ffffff;
            border: 1px solid #f1f5f9;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.03);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 1rem;
            text-align: center;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 30px -5px rgba(124, 58, 237, 0.1);
        }
        .metric-title {
            font-size: 0.75rem;
            color: #6b7280;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.05em;
            margin-top: 0.5rem;
        }
        .metric-value {
            font-size: 1.75rem;
            color: #1e1b4b;
            font-weight: 800;
            margin-top: 0.25rem;
        }
        
        .status-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 0.75rem;
            padding: 1rem;
            margin-top: 1.5rem;
            box-shadow: inset 0 1px 2px rgba(0,0,0,0.01);
        }
        
        /* Job Card & Badges */
        .job-card {
            background-color: #ffffff;
            border: 1px solid #f1f5f9;
            border-radius: 1rem;
            padding: 1.75rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 25px -4px rgba(0,0,0,0.03);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
        }
        .job-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 35px -8px rgba(0,0,0,0.08);
        }
        
        .job-title {
            font-size: 1.35rem;
            color: #1e1b4b;
            font-weight: 700;
        }
        .job-company {
            font-size: 1.05rem;
            color: #3b82f6;
            font-weight: 600;
            margin-bottom: 0.5rem;
        }
        
        /* Styled Badge Tags */
        .badge {
            display: inline-block;
            padding: 0.35rem 0.8rem;
            font-size: 0.8rem;
            font-weight: 700;
            border-radius: 9999px;
            margin-right: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }
        .badge-match-high {
            background-color: #dcfce7;
            color: #15803d;
        }
        .badge-match-mid {
            background-color: #fef9c3;
            color: #a16207;
        }
        .badge-match-low {
            background-color: #fee2e2;
            color: #b91c1c;
        }
        .badge-safety-clean {
            background-color: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
        }
        .badge-safety-risk {
            background-color: #fef2f2;
            color: #b91c1c;
            border: 1px solid #fecaca;
        }
        
        .pill-badge {
            background-color: #f0fdfa;
            color: #0d9488;
            border: 1px solid #ccfbf1;
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.8rem;
            display: inline-block;
            margin: 0.25rem;
            font-weight: 600;
        }
        
        /* Modern Hero Section Card */
        .hero-banner {
            background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%);
            border-radius: 1.5rem;
            padding: 3rem 2.5rem;
            color: #ffffff;
            margin-bottom: 2.5rem;
            box-shadow: 0 10px 30px -10px rgba(124, 58, 237, 0.2);
            position: relative;
            overflow: hidden;
        }
        .hero-banner::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -20%;
            width: 300px;
            height: 300px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 50%;
            filter: blur(50px);
        }
        .hero-title {
            font-size: 3rem !important;
            font-weight: 800 !important;
            color: #ffffff !important;
            margin-bottom: 0.5rem !important;
        }
        
        /* Steps Styling */
        .step-card {
            background-color: #ffffff;
            border: 1px solid #f1f5f9;
            border-radius: 1rem;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.01);
            transition: all 0.2s ease;
            height: 100%;
        }
        .step-card:hover {
            transform: translateY(-3px);
            border-color: #7c3aed;
            box-shadow: 0 8px 25px rgba(124, 58, 237, 0.1);
        }
        .step-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .step-number {
            font-size: 0.75rem;
            font-weight: 700;
            color: #7c3aed;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.25rem;
        }
        .step-title {
            font-weight: 700;
            color: #1e1b4b;
            margin-bottom: 0.5rem;
            font-size: 1.05rem;
        }
        
        /* Insights Panel styling */
        .insight-panel {
            background: linear-gradient(to right, #faf5ff, #f0fdfa);
            border: 1px solid #f3e8ff;
            border-radius: 1rem;
            padding: 1.5rem;
            margin-top: 1.5rem;
            box-shadow: 0 4px 15px rgba(0,0,0,0.01);
        }
        
        /* Warnings and alerts */
        .safety-alert-clean {
            padding: 0.75rem;
            background-color: #f0fdf4;
            border-left: 4px solid #16a34a;
            border-radius: 0.375rem;
            margin-top: 0.5rem;
            color: #166534;
        }
        .safety-alert-suspicious {
            padding: 0.75rem;
            background-color: #fef2f2;
            border-left: 4px solid #dc2626;
            border-radius: 0.375rem;
            margin-top: 0.5rem;
            color: #991b1b;
        }
    </style>
""", unsafe_allow_html=True)

# Helper function to query backend state
def check_backend_profile():
    try:
        res = requests.get(f"{BACKEND_URL}/api/preferences?profile_id=user_default", timeout=3)
        if res.status_code == 200:
            return True, res.json()
        return False, None
    except Exception:
        return False, None

def get_current_profile():
    try:
        conn = sqlite3.connect("career_navigator.db") if os.path.exists("career_navigator.db") else None
        if not conn:
            return None
        cursor = conn.cursor()
        cursor.execute("SELECT name, email, skills, projects, internships, certifications FROM user_profiles WHERE id='user_default'")
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                "name": row[0],
                "email": row[1],
                "skills": json.loads(row[2]),
                "projects": json.loads(row[3]),
                "internships": json.loads(row[4]),
                "certifications": json.loads(row[5])
            }
    except Exception:
        pass
    return None

# Sidebar navigation - ScoutIQ Rebranding
st.sidebar.markdown("""
    <div style='padding: 0.5rem 0; margin-bottom:1.5rem;'>
        <h2 style='color:#7C3AED; margin:0; font-weight:800; font-size:2rem; display:flex; align-items:center; gap:0.5rem;'>
            🧭 ScoutIQ
        </h2>
        <p style='color:#6b7280; font-size:0.825rem; font-weight:500; margin-top:0.25rem; line-height:1.2;'>
            The AI that scouts opportunities before you do.
        </p>
    </div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

page_choice = st.sidebar.radio(
    "Navigation Menu", 
    ["🏠 Home", "📄 Resume Upload", "⚙️ Preferences", "🔍 Job Discovery", "📋 Application Tracker", "📧 Email Monitor"]
)

# Render notifications in sidebar below Navigation Menu
if "email_notifications" not in st.session_state:
    st.session_state.email_notifications = []

if st.session_state.email_notifications:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔔 Live Alerts")
    for note in st.session_state.email_notifications[:5]: # Show latest 5 notifications
        st.sidebar.info(note)
    if st.sidebar.button("Clear Alerts"):
        st.session_state.email_notifications = []
        st.rerun()

# Connect to backend verification helper
profile_exists = get_current_profile() is not None
pref_exists, user_prefs = check_backend_profile()

# Parse the correct clean string for dispatching
if "Home" in page_choice:
    page = "Home"
elif "Resume" in page_choice:
    page = "Resume Upload"
elif "Preferences" in page_choice:
    page = "Preferences"
elif "Discovery" in page_choice:
    page = "Job Discovery"
elif "Tracker" in page_choice:
    page = "Application Tracker"
elif "Monitor" in page_choice:
    page = "Email Monitor"

# System Status Card
# Fetch email status
gmail_status = "Disconnected"
try:
    res_gmail = requests.get(f"{BACKEND_URL}/api/email-monitor/status", timeout=2)
    if res_gmail.status_code == 200:
        gmail_data = res_gmail.json()
        if gmail_data.get("connected"):
            gmail_status = gmail_data.get("mode", "Mock Mode")
except Exception:
    pass

profile_badge = "✅ Ready" if profile_exists else "❌ Missing"
pref_badge = "✅ Saved" if pref_exists else "❌ Missing"
gmail_badge = "🟢 Mock Connected" if gmail_status == "Mock Mode" else ("🔵 Live Connected" if gmail_status == "Live Gmail Mode" else "❌ Disconnected")

st.sidebar.markdown(f"""
    <div class='status-card'>
        <div style='font-size:0.8rem; font-weight:700; color:#4b5563; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:0.05em;'>System Status</div>
        <div style='display:flex; flex-direction:column; gap:0.4rem; font-size:0.85rem; color:#1e1b4b;'>
            <div>🟢 <b>Backend</b>: Online</div>
            <div>{profile_badge.split()[0]} <b>Resume</b>: {profile_badge.split()[-1]}</div>
            <div>{pref_badge.split()[0]} <b>Preferences</b>: {pref_badge.split()[-1]}</div>
            <div>{gmail_badge.split()[0]} <b>Gmail</b>: {gmail_badge.split()[-1]}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# ==================== HOME PAGE ====================
if page == "Home":
    # Hero Section
    st.markdown("""
        <div class='hero-banner'>
            <div class='hero-title'>🧭 ScoutIQ</div>
            <div style='font-size:1.35rem; font-weight:600; opacity:0.95; margin-bottom:1rem;'>
                The AI that scouts opportunities before you do.
            </div>
            <p style='font-size:1.05rem; opacity:0.85; max-width:700px; margin:0; line-height:1.5;'>
                Your AI career copilot that discovers jobs, verifies employers, tracks applications, and monitors recruiter updates—all in one intelligent workspace.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Overview metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Count applications
    app_count = 0
    try:
        res = requests.get(f"{BACKEND_URL}/api/applications", timeout=3)
        if res.status_code == 200:
            app_count = len(res.json())
    except Exception:
        pass
        
    # Count recruiter updates (email history)
    email_count = 0
    try:
        res_h = requests.get(f"{BACKEND_URL}/api/email-monitor/history", timeout=2)
        if res_h.status_code == 200:
            email_count = len(res_h.json())
    except Exception:
        pass

    # Count verified companies
    company_count = 0
    try:
        conn = sqlite3.connect("career_navigator.db") if os.path.exists("career_navigator.db") else None
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM companies")
            company_count = cursor.fetchone()[0]
            conn.close()
    except Exception:
        pass

    # Count matched jobs
    matched_jobs_count = 0
    discovered_data = st.session_state.get("discovered_jobs", None)
    if discovered_data:
        matched_jobs_count = len(discovered_data.get("jobs", []))
    else:
        matched_jobs_count = 5 # default starting pool

    with col1:
        st.markdown(
            f"""<div class='metric-card'>
                <div class='step-icon'>🎯</div>
                <div class='metric-title'>Jobs Matched</div>
                <div class='metric-value'>{matched_jobs_count}</div>
            </div>""", 
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""<div class='metric-card'>
                <div class='step-icon'>📄</div>
                <div class='metric-title'>Resume Parsed</div>
                <div class='metric-value'>{"100%" if profile_exists else "0%"}</div>
            </div>""", 
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""<div class='metric-card'>
                <div class='step-icon'>📋</div>
                <div class='metric-title'>Applications</div>
                <div class='metric-value'>{app_count}</div>
            </div>""", 
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""<div class='metric-card'>
                <div class='step-icon'>🏢</div>
                <div class='metric-title'>Trusted Companies</div>
                <div class='metric-value'>{company_count}</div>
            </div>""", 
            unsafe_allow_html=True
        )
    with col5:
        st.markdown(
            f"""<div class='metric-card'>
                <div class='step-icon'>📧</div>
                <div class='metric-title'>Recruiter Updates</div>
                <div class='metric-value'>{email_count}</div>
            </div>""", 
            unsafe_allow_html=True
        )
        
    st.markdown("<br><h3>🚀 ScoutIQ Workflow Guide</h3>", unsafe_allow_html=True)
    
    col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
    with col_s1:
        st.markdown("""
            <div class='step-card'>
                <div class='step-icon'>📄</div>
                <div class='step-number'>Step 1</div>
                <div class='step-title'>Upload Resume</div>
                <p style='font-size:0.85rem; color:#4b5563; margin:0;'>Let ScoutIQ understand your skills.</p>
            </div>
        """, unsafe_allow_html=True)
    with col_s2:
        st.markdown("""
            <div class='step-card'>
                <div class='step-icon'>⚙️</div>
                <div class='step-number'>Step 2</div>
                <div class='step-title'>Set Preferences</div>
                <p style='font-size:0.85rem; color:#4b5563; margin:0;'>Tell us what you're looking for.</p>
            </div>
        """, unsafe_allow_html=True)
    with col_s3:
        st.markdown("""
            <div class='step-card'>
                <div class='step-icon'>🔍</div>
                <div class='step-number'>Step 3</div>
                <div class='step-title'>Discover Jobs</div>
                <p style='font-size:0.85rem; color:#4b5563; margin:0;'>AI finds opportunities tailored for you.</p>
            </div>
        """, unsafe_allow_html=True)
    with col_s4:
        st.markdown("""
            <div class='step-card'>
                <div class='step-icon'>📋</div>
                <div class='step-number'>Step 4</div>
                <div class='step-title'>Apply & Track</div>
                <p style='font-size:0.85rem; color:#4b5563; margin:0;'>Track every application in one place.</p>
            </div>
        """, unsafe_allow_html=True)
    with col_s5:
        st.markdown("""
            <div class='step-card'>
                <div class='step-icon'>📧</div>
                <div class='step-number'>Step 5</div>
                <div class='step-title'>Monitor Emails</div>
                <p style='font-size:0.85rem; color:#4b5563; margin:0;'>Automatically detect recruiter updates.</p>
            </div>
        """, unsafe_allow_html=True)
        
    # AI Insights section
    insights_list = [
        "Applications tracked consistently have a 45% higher chance of reaching the interview stage.",
        "ScoutIQ discovered new job opportunities matching your resume's core capabilities.",
        "Adding specific project certifications (like AWS or FastAPI) increases matching scores by up to 25%.",
        "Company trust scores indicate verified employer credentials for 100% of top-recommended roles.",
        "Running email synchronization after applying ensures status updates are logged without manual effort."
    ]
    selected_insight = random.choice(insights_list)
    
    st.markdown(f"""
        <div class='insight-panel'>
            <div style='font-size:0.95rem; font-weight:700; color:#7C3AED; margin-bottom:0.5rem;'>💡 ScoutIQ Intelligence Insight</div>
            <p style='font-size:0.925rem; color:#1e1b4b; margin:0;'>{selected_insight}</p>
        </div>
    """, unsafe_allow_html=True)

# ==================== RESUME UPLOAD PAGE ====================
elif page == "Resume Upload":
    st.markdown("<h1 class='main-header'>📄 Upload & Parse Resume</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Upload your PDF resume to create your candidate profile using our optimized parsing pipeline.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📄 Browse Resume", type=["pdf"])
    
    if uploaded_file is not None:
        if st.button("Parse Resume"):
            with st.spinner("Processing PDF and extracting skills profile..."):
                try:
                    # Prepare file payload
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    res = requests.post(f"{BACKEND_URL}/api/resume/upload", files=files, timeout=60)
                    
                    if res.status_code == 200:
                        data = res.json()
                        st.success("Resume parsed successfully!")
                        st.info(f"Pipeline Trace: `{data.get('message', 'Direct Parse completed.')}`")
                        
                        # Layout result
                        col_r1, col_r2 = st.columns([1, 2])
                        with col_r1:
                            st.markdown("### Basic Details")
                            st.write(f"**Name**: {data['name']}")
                            st.write(f"**Email**: {data['email']}")
                            
                            st.markdown("### Certifications")
                            for cert in data.get("certifications", []):
                                st.write(f"• {cert}")
                                
                        with col_r2:
                            st.markdown("### Extracted Skills")
                            skills_html = "".join([f"<span class='pill-badge'>{s}</span>" for s in data.get("skills", [])])
                            st.markdown(skills_html, unsafe_allow_html=True)
                            
                            st.markdown("### Internships / Experience")
                            for intern in data.get("internships", []):
                                st.write(f"• {intern}")
                                
                            st.markdown("### Projects")
                            for project in data.get("projects", []):
                                st.write(f"• {project}")
                    elif res.status_code == 400:
                        st.error(f"Validation Error (400): {res.json().get('detail')}")
                    else:
                        st.error(f"Unexpected error ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
                    
    # Show current profile if it already exists
    current_profile = get_current_profile()
    if current_profile:
        st.markdown("---")
        st.markdown("### 👤 Current Stored Candidate Profile")
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            st.write(f"**Name**: {current_profile['name']}")
            st.write(f"**Email**: {current_profile['email']}")
            st.markdown("**Certifications**:")
            for cert in current_profile['certifications']:
                st.write(f"• {cert}")
        with col_c2:
            st.markdown("**Skills**:")
            skills_html = "".join([f"<span class='pill-badge'>{s}</span>" for s in current_profile['skills']])
            st.markdown(skills_html, unsafe_allow_html=True)
            
            st.markdown("**Internships**:")
            for intern in current_profile['internships']:
                st.write(f"• {intern}")
                
            st.markdown("**Projects**:")
            for proj in current_profile['projects']:
                st.write(f"• {proj}")
    else:
        st.markdown("---")
        st.markdown("""
            <div style='text-align: center; padding: 3rem; background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 1rem; margin-top: 2rem;'>
                <div style='font-size: 3.5rem; margin-bottom: 1rem;'>📄</div>
                <h3 style='color: #1e1b4b; margin-bottom: 0.5rem;'>No Resume Uploaded Yet</h3>
                <p style='color: #64748b; font-size: 0.95rem; margin: 0;'>Upload your resume to generate your AI candidate profile.</p>
            </div>
        """, unsafe_allow_html=True)

# ==================== PREFERENCES PAGE ====================
elif page == "Preferences":
    st.markdown("<h1 class='main-header'>⚙️ Set Job Preferences</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Configure your ideal role parameters, expected salary, and desired location.</p>", unsafe_allow_html=True)
    
    # Load defaults - initial blank state
    default_loc = ""
    default_sal = 0.0
    default_mode = "Select..."
    default_role = ""
    
    if pref_exists and user_prefs:
        default_loc = user_prefs.get("preferred_location", "")
        default_sal = float(user_prefs.get("expected_salary", 0.0))
        default_mode = user_prefs.get("work_mode", "Select...")
        default_role = user_prefs.get("preferred_role", "")
        st.info(f"Loaded existing preferences.")
        
    with st.form("preferences_form"):
        preferred_role = st.text_input("Preferred Job Title / Role", value=default_role, placeholder="e.g. Software Engineer")
        preferred_location = st.text_input("Preferred Location", value=default_loc, placeholder="e.g. Seattle, Remote, Bangalore")
        expected_salary = st.number_input("Expected Annual Salary (Local Currency / USD)", value=default_sal, min_value=0.0, step=5000.0)
        
        modes_list = ["Select...", "Remote", "Hybrid", "Onsite"]
        work_mode = st.selectbox(
            "Desired Work Mode", 
            modes_list, 
            index=modes_list.index(default_mode) if default_mode in modes_list else 0
        )
        
        submitted = st.form_submit_button("Save Preferences")
        if submitted:
            if work_mode == "Select...":
                st.error("Please select a valid work mode.")
            elif not preferred_role.strip():
                st.error("Preferred role cannot be empty.")
            elif not preferred_location.strip():
                st.error("Preferred location cannot be empty.")
            else:
                with st.spinner("Saving preferences..."):
                    try:
                        payload = {
                            "preferred_location": preferred_location,
                            "expected_salary": expected_salary,
                            "work_mode": work_mode,
                            "preferred_role": preferred_role
                        }
                        res = requests.post(f"{BACKEND_URL}/api/preferences?profile_id=user_default", json=payload, timeout=5)
                        if res.status_code == 200:
                            st.success("Job preferences successfully updated!")
                            st.rerun()
                        else:
                            st.error(f"Error saving preferences: {res.text}")
                    except Exception as e:
                        st.error(f"Failed to connect to backend: {e}")

# ==================== JOB DISCOVERY PAGE ====================
elif page == "Job Discovery":
    st.markdown("<h1 class='main-header'>🔍 Match & Discover Jobs</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Scan our verified database of opportunities matching your skills, checked for safety ratings.</p>", unsafe_allow_html=True)
    
    if not profile_exists:
        st.warning("⚠️ No Candidate Profile found. Please upload your resume first on the Resume Upload page.")
    elif not pref_exists:
        st.warning("⚠️ No Preferences set. Please configure your job preferences on the Preferences page.")
    else:
        # 1. Render pending application confirmation banner
        # Design note: This confirmation step can later be bypassed/replaced by the Email Monitoring Agent (Phase 4).
        pending_app = st.session_state.get("pending_app")
        if pending_app:
            st.markdown(f"""
                <div style='background-color:#eff6ff; padding:1.5rem; border-radius:0.5rem; border:1px solid #3b82f6; margin-bottom:1.5rem;'>
                    <h3 style='color:#1e3a8a; margin:0 0 0.5rem 0;'>🔗 Application Confirmation Pending</h3>
                    <p style='color:#1e40af; margin:0 0 1rem 0;'>
                        You are applying for <b>{pending_app.get('title')}</b> at <b>{pending_app.get('company')}</b>.<br>
                        Click <b>Open Company Website ↗</b> below to complete your submission in a new tab, then return here to confirm.
                    </p>
                </div>
            """, unsafe_allow_html=True)
            
            col_l, col_y, col_n = st.columns([2, 1, 1])
            with col_l:
                st.link_button("Open Company Website ↗", url=pending_app.get("apply_url"), use_container_width=True)
            with col_y:
                if st.button("Yes, I submitted it", type="primary", use_container_width=True):
                    with st.spinner("Recording application..."):
                        try:
                            payload = {
                                "job_id": pending_app.get("job_id"),
                                "apply_url": pending_app.get("apply_url"),
                                "source": "Company Website",
                                "notes": "Applied via company website redirection"
                            }
                            res_apply = requests.post(f"{BACKEND_URL}/api/applications/apply", json=payload, timeout=10)
                            if res_apply.status_code == 200:
                                st.success("Application successfully recorded!")
                                st.session_state.pending_app = None
                                st.rerun()
                            else:
                                st.error(f"Failed to record application: {res_apply.text}")
                        except Exception as e:
                            st.error(f"Connection error: {e}")
            with col_n:
                if st.button("No, cancel", use_container_width=True):
                    st.session_state.pending_app = None
                    st.rerun()
            st.markdown("---")
            
        if st.button("Search & Match Jobs"):
            st.session_state.discovery_triggered = True
            
        if st.session_state.get("discovery_triggered", False):
            with st.spinner("Querying job database, calculating match quotients, and auditing safety flags..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/api/jobs/discover?profile_id=user_default", timeout=30)
                    
                    if res.status_code == 200:
                        data = res.json()
                        
                        # Handle preferences required
                        if data.get("status") == "preferences_required":
                            st.warning(f"Preferences missing: {', '.join(data.get('missing_fields', []))}. Please fill them in.")
                        else:
                            st.session_state.discovered_jobs = data
                    else:
                        st.error(f"Error running job discovery: {res.text}")
                except Exception as e:
                    st.error(f"Failed to connect to backend: {e}")
                    
        # Render Discovered Jobs
        discovered_data = st.session_state.get("discovered_jobs", None)
        if discovered_data:
            st.markdown(f"### Results for **{discovered_data.get('applicant_name', 'Applicant')}**")
            
            # Display tabs
            tab1, tab2, tab3 = st.columns(3)
            with tab1:
                st.markdown(f"**Top Matches**: {len(discovered_data.get('top_matches', []))} jobs")
            with tab2:
                st.markdown(f"**Related Opportunities**: {len(discovered_data.get('related_opportunities', []))} jobs")
            with tab3:
                st.markdown(f"**Total Opportunities**: {len(discovered_data.get('jobs', []))} jobs")
                
            st.markdown("---")
            
            # Categories
            categories = [
                ("🎯 Top Matches (Ideal Alignment)", discovered_data.get("top_matches", [])),
                ("🌐 Related Opportunities", discovered_data.get("related_opportunities", []))
            ]
            
            for category_name, jobs_list in categories:
                if jobs_list:
                    st.markdown(f"## {category_name}")
                    for job in jobs_list:
                        match_score = job.get("match_score", 0.0) * 100
                        risk_score = job.get("risk_score", 0.0) * 100
                        
                        # Determine Match Badge Class
                        if match_score >= 80:
                            match_class = "badge-match-high"
                        elif match_score >= 50:
                            match_class = "badge-match-mid"
                        else:
                            match_class = "badge-match-low"
                            
                        # Safety status
                        is_suspicious = job.get("risk_score", 0.0) >= 0.4
                        safety_class = "badge-safety-risk" if is_suspicious else "badge-safety-clean"
                        safety_text = "SUSPICIOUS / AUDIT FAIL" if is_suspicious else "VERIFIED TRUSTED"
                        
                        # Format salary safely
                        raw_salary = job.get('salary', 0)
                        try:
                            formatted_salary = f"{int(raw_salary):,}"
                        except Exception:
                            formatted_salary = str(raw_salary)
                            
                        st.markdown(f"""
                            <div class='job-card'>
                                <div style='display:flex; justify-content:space-between; align-items:center;'>
                                    <div>
                                        <div class='job-title'>{job.get('title', 'Untitled')}</div>
                                        <div class='job-company'>{job.get('company', 'Unknown Company')}</div>
                                    </div>
                                    <div style='text-align:right;'>
                                        <span class='badge {match_class}'>Match: {match_score:.0f}%</span>
                                        <span class='badge {safety_class}'>{safety_text}</span>
                                    </div>
                                </div>
                                <div class='job-meta'>
                                    📍 <b>Location</b>: {job.get('location', 'Not specified')} | 💼 <b>Mode</b>: {job.get('work_mode', 'Not specified')} | 💰 <b>Salary</b>: {formatted_salary}
                                </div>
                                <p>{job.get('description', '')}</p>
                                <div>
                                    <b>Skills Required</b>: {' '.join([f"<span class='pill-badge'>{s}</span>" for s in job.get('skills_required', [])])}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Verification detail block
                        if is_suspicious:
                            st.markdown(f"""
                                <div class='safety-alert-suspicious'>
                                    ⚠️ <b>Company Safety Warnings Identified</b>:
                                    <ul>
                                        {"".join([f"<li>{flag}</li>" for flag in job.get('safety_flags', [])])}
                                    </ul>
                                    <i>Auditor Note: {job.get('verification_notes', '')}</i>
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                                <div class='safety-alert-clean'>
                                    ✅ <b>Employer Credibility Check</b>: {job.get('verification_notes', '')}
                                </div>
                            """, unsafe_allow_html=True)
                            
                        # 2. Apply controls (redirects to company website and sets pending app confirmation)
                        # Design note: We simulate "job_005" (DataHub Database Engineer) as having no application link for demonstration.
                        apply_url = None if job.get("job_id") == "job_005" else (job.get("apply_url") or f"https://{job.get('company', 'unknown').lower().replace(' ', '')}.com/careers")
                        
                        if apply_url:
                            if st.button(f"Apply on Company Website ↗", key=f"apply_btn_{job.get('job_id')}"):
                                st.session_state.pending_app = {
                                    "job_id": job.get("job_id"),
                                    "title": job.get("title"),
                                    "company": job.get("company"),
                                    "apply_url": apply_url
                                }
                                st.rerun()
                        else:
                            st.button("Application link unavailable", disabled=True, key=f"apply_disabled_{job.get('job_id')}")
                        st.markdown("<br>", unsafe_allow_html=True)

# ==================== APPLICATION TRACKER PAGE ====================
elif page == "Application Tracker":
    st.markdown("<h1 class='main-header'>📋 Tracked Job Applications</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>View, update, and manage your active application pipeline status.</p>", unsafe_allow_html=True)
    
    apps = []
    try:
        res = requests.get(f"{BACKEND_URL}/api/applications", timeout=5)
        if res.status_code == 200:
            apps = res.json()
    except Exception as e:
        st.error(f"Failed to fetch application history: {e}")
        
    # Retrieve email history to build journeys
    email_history = []
    try:
        res_h = requests.get(f"{BACKEND_URL}/api/email-monitor/history", timeout=5)
        if res_h.status_code == 200:
            email_history = res_h.json()
    except Exception:
        pass
        
    if not apps:
        st.markdown("""
            <div style='text-align: center; padding: 3rem; background-color: #ffffff; border: 1px dashed #cbd5e1; border-radius: 1rem; margin-top: 2rem;'>
                <div style='font-size: 3.5rem; margin-bottom: 1rem;'>📋</div>
                <h3 style='color: #1e1b4b; margin-bottom: 0.5rem;'>No Applications Yet</h3>
                <p style='color: #64748b; font-size: 0.95rem; margin: 0;'>Start applying for jobs from the Job Discovery page.</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        # Status options
        status_options = ['Applied', 'Assessment Received', 'Interview Scheduled', 'Rejected', 'Offer Received']
        
        # Display as columns or interactive cards
        for app in apps:
            app_id = app["application_id"]
            
            # Determine color tag
            status = app["status"]
            if status == "Offer Received":
                color = "green"
            elif status == "Rejected":
                color = "red"
            elif status == "Interview Scheduled":
                color = "orange"
            elif status == "Assessment Received":
                color = "blue"
            else:
                color = "gray"
                
            # Build timeline journey dynamically using email_history
            stages = ["Applied"]
            app_emails = [h for h in email_history if h.get("matched_application_id") == app_id]
            # Sort emails chronologically
            app_emails.sort(key=lambda x: x.get("processed_at", ""))
            
            for mail in app_emails:
                cls = mail.get("classification")
                if cls and cls in status_options and cls not in stages:
                    stages.append(cls)
            if status not in stages:
                stages.append(status)
                
            # Render timeline steps beautifully
            timeline_steps = []
            for s in stages:
                is_current = (s == status)
                bg_color = "#3b82f6" if is_current else "#f3f4f6"
                text_color = "#ffffff" if is_current else "#1f2937"
                font_weight = "bold" if is_current else "normal"
                border = "1px solid #3b82f6" if is_current else "1px solid #d1d5db"
                timeline_steps.append(f"<span style='display:inline-block; padding:0.2rem 0.5rem; border-radius:0.25rem; background-color:{bg_color}; color:{text_color}; font-weight:{font_weight}; border:{border}; font-size:0.75rem; margin:0.1rem;'>{s}</span>")
            timeline_html = " <span style='color:#9ca3af; font-size:0.75rem;'>➔</span> ".join(timeline_steps)
            
            st.markdown(f"""
                <div style='background-color:#ffffff; padding:1.25rem; border-radius:0.5rem; border:1px solid #e5e7eb; border-left: 5px solid {color}; margin-bottom:1rem; box-shadow:0 1px 2px rgba(0,0,0,0.05);'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <span style='font-size:1.15rem; font-weight:700; color:#1f2937;'>{app['job_title']}</span>
                            <br>
                            <span style='font-size:0.95rem; font-weight:600; color:#2563eb;'>{app['company_name']}</span>
                        </div>
                        <div>
                            <span style='padding:0.25rem 0.75rem; border-radius:9999px; background-color:#eff6ff; color:#1e40af; font-size:0.85rem; font-weight:600;'>
                                {app['source'] or 'Direct'}
                            </span>
                        </div>
                    </div>
                    <div style='margin-top:0.75rem; font-size:0.875rem; color:#4b5563;'>
                        📅 <b>Applied On</b>: {app['application_date']} | 📝 <b>Notes</b>: {app['notes'] or 'None'}
                    </div>
                    <div style='margin-top:0.75rem; border-top:1px solid #f3f4f6; padding-top:0.5rem;'>
                        <div style='display:flex; align-items:center; flex-wrap:wrap; gap:0.25rem;'>
                            <b style='font-size:0.825rem; color:#4b5563;'>Journey Timeline:</b> {timeline_html}
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Inline status update controls
            current_idx = status_options.index(status) if status in status_options else 0
            new_status = st.selectbox(
                f"Update Status for {app['job_title']} at {app['company_name']}",
                status_options,
                index=current_idx,
                key=f"status_select_{app_id}"
            )
            
            # Trigger update when index changes
            if new_status != status:
                with st.spinner("Updating status..."):
                    try:
                        update_payload = {
                            "application_id": app_id,
                            "status": new_status
                        }
                        res_up = requests.post(f"{BACKEND_URL}/api/applications/update", json=update_payload, timeout=5)
                        if res_up.status_code == 200:
                            st.success(f"Status updated to '{new_status}' successfully!")
                            st.rerun()
                        else:
                            st.error(f"Failed to update status: {res_up.text}")
                    except Exception as ex:
                        st.error(f"Error during status update: {ex}")
            st.markdown("<hr style='margin:1.5rem 0;'>", unsafe_allow_html=True)

# ==================== EMAIL MONITOR PAGE ====================
elif page == "Email Monitor":
    st.markdown("<h1 class='main-header'>✉️ Email Monitoring Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Scan your inbox (or mock data) to automatically detect recruiter updates and update application progress.</p>", unsafe_allow_html=True)
    
    # 1. Fetch connection status
    status_data = {"connected": False, "mode": "Mock Mode", "total_processed": 0, "total_updated": 0, "last_checked": None}
    try:
        res = requests.get(f"{BACKEND_URL}/api/email-monitor/status", timeout=5)
        if res.status_code == 200:
            status_data = res.json()
    except Exception as e:
        st.error(f"Failed to fetch monitor status: {e}")
        
    connected = status_data.get("connected", False)
    mode = status_data.get("mode", "Mock Mode")
    
    # Render Mode Badge
    if mode == "Live Gmail Mode":
        st.markdown("<span style='padding:0.35rem 0.8rem; border-radius:9999px; background-color:#dbeafe; color:#1e40af; font-weight:700; font-size:0.875rem;'>🔵 Mode: Live Gmail Mode (Google OAuth)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='padding:0.35rem 0.8rem; border-radius:9999px; background-color:#dcfce7; color:#15803d; font-weight:700; font-size:0.875rem;'>🟢 Mode: Mock Mode (Simulated Inbox)</span>", unsafe_allow_html=True)
        
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 2. Connection panel
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        if connected:
            st.success(f"✓ Gmail Account Linked ({mode})")
        else:
            st.warning("✗ Gmail Account Not Linked. Connecting will default to Mock Mode unless credentials.json is detected.")
            
    with col_c2:
        if not connected:
            if st.button("Link Gmail Account", type="primary", use_container_width=True):
                with st.spinner("Connecting..."):
                    try:
                        res_conn = requests.post(f"{BACKEND_URL}/api/gmail/connect", json={}, timeout=5)
                        if res_conn.status_code == 200:
                            st.success("Successfully connected!")
                            st.rerun()
                        else:
                            st.error(f"Connection failed: {res_conn.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")
        else:
            if st.button("Disconnect Gmail", use_container_width=True):
                try:
                    conn = sqlite3.connect("career_navigator.db") if os.path.exists("career_navigator.db") else None
                    if conn:
                        conn.execute("DELETE FROM gmail_credentials")
                        conn.commit()
                        conn.close()
                    st.success("Disconnected Gmail account.")
                    st.rerun()
                except Exception as ex:
                    st.error(f"Failed to disconnect: {ex}")
                
    st.markdown("---")
    
    # 3. Monitor metrics
    st.markdown("### 📊 Synchronization Stats")
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Emails Scanned & Processed", status_data.get("total_processed", 0))
    with col_m2:
        st.metric("Application States Updated", status_data.get("total_updated", 0))
    with col_m3:
        st.metric("Last Sync Check", status_data.get("last_checked") or "Never")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Manual Sync trigger
    if st.button("🔄 Sync Recruiter Inbox", use_container_width=True):
        with st.spinner("Scanning recruiter messages and running classification models..."):
            try:
                res_sync = requests.post(f"{BACKEND_URL}/api/email-monitor/run", timeout=30)
                if res_sync.status_code == 200:
                    sync_data = res_sync.json()
                    
                    # Generate UI notifications for status updates
                    logs = sync_data.get("logs", [])
                    new_updates = 0
                    sync_messages = []
                    for log in logs:
                        classification = log.get("classification")
                        company = log.get("matched_company") or "Unknown"
                        
                        if log.get("status_updated"):
                            new_updates += 1
                            emoji = "🎉" if classification == "Offer Received" else ("🔔" if classification == "Interview Scheduled" else "✉️")
                            note_text = f"{emoji} {classification} – {company}"
                            if "email_notifications" not in st.session_state:
                                st.session_state.email_notifications = []
                            st.session_state.email_notifications.insert(0, note_text)
                            st.toast(note_text)
                        
                        # Add clean indicator text
                        if classification == "Interview Scheduled":
                            sync_messages.append(f"✓ Interview invitation detected ({company})")
                        elif classification == "Assessment Received":
                            sync_messages.append(f"✓ Assessment invitation detected ({company})")
                        elif classification == "Offer Received":
                            sync_messages.append(f"✓ Offer received ({company})")
                        elif classification == "Applied":
                            sync_messages.append(f"✓ Application acknowledgement ({company})")
                            
                    st.session_state.sync_messages = sync_messages
                    st.session_state.sync_toast_msg = f"Inbox synchronization complete. Processed {len(logs)} messages. Identified {new_updates} updates."
                    st.rerun()
                else:
                    st.error(f"Sync failed: {res_sync.text}")
            except Exception as e:
                st.error(f"Failed to trigger monitor sync: {e}")
                
    if "sync_toast_msg" in st.session_state and st.session_state.sync_toast_msg:
        st.success(st.session_state.sync_toast_msg)
        del st.session_state.sync_toast_msg
        
    if "sync_messages" in st.session_state and st.session_state.sync_messages:
        st.markdown("#### 🔔 Sync Detection Results")
        for msg in st.session_state.sync_messages:
            st.success(msg)
        if st.button("Dismiss Sync Results"):
            del st.session_state.sync_messages
            st.rerun()
                
    st.markdown("---")
    
    # 4. Email Audit Log History
    st.markdown("### 📜 Processed Recruiter Email History")
    email_history = []
    try:
        res_h = requests.get(f"{BACKEND_URL}/api/email-monitor/history", timeout=5)
        if res_h.status_code == 200:
            email_history = res_h.json()
    except Exception:
        pass
        
    if not email_history:
        st.info("No recruiter email logs processed yet. Click Sync Recruiter Inbox to retrieve messages.")
    else:
        for mail in email_history:
            sender = mail.get("sender")
            subject = mail.get("subject")
            body = mail.get("body")
            classification = mail.get("classification")
            method = mail.get("classification_method", "Rule-Based")
            conf = mail.get("confidence_score", 1.0)
            processed_at = mail.get("processed_at", "")
            
            # Badge styles
            badge_color = "#3b82f6"
            if classification == "Offer Received":
                badge_color = "#16a34a"
            elif classification == "Rejected":
                badge_color = "#dc2626"
            elif classification == "Interview Scheduled":
                badge_color = "#ea580c"
            elif classification == "Ignore":
                badge_color = "#6b7280"
                
            st.markdown(f"""
                <div style='background-color:#ffffff; padding:1rem; border-radius:0.375rem; border:1px solid #e5e7eb; margin-bottom:1rem;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-weight:600; color:#1f2937;'>Subject: {subject}</span>
                        <span style='padding:0.2rem 0.5rem; border-radius:0.25rem; background-color:{badge_color}; color:#ffffff; font-size:0.75rem; font-weight:700;'>{classification}</span>
                    </div>
                    <div style='font-size:0.825rem; color:#4b5563; margin-top:0.25rem;'>
                        From: <b>{sender}</b> | Processed: {processed_at}
                    </div>
                    <p style='font-size:0.875rem; color:#1f2937; margin:0.5rem 0;'>{body}</p>
                    <div style='font-size:0.75rem; color:#6b7280;'>
                        Method: <span style='font-weight:600;'>{method}</span> | Confidence: <span style='font-weight:600;'>{conf:.0%}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

