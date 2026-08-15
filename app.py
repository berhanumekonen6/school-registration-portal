# ===================================================================
# SCHOOL REGISTRATION PORTAL - ENHANCED
# Admin-Controlled Student & Teacher Management System
# WITH TEACHER LOGIN & EVALUATION APPROVAL WORKFLOW
# Berhanu Mekonen, PhD, Arba Minch University, August 14, 2026
# ===================================================================

import streamlit as st
import pandas as pd
import hashlib
from datetime import datetime, timedelta
import json
import os
import random
import string
import io  # for Excel export

st.set_page_config(
    page_title="School Registration Portal",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================================
# AUTHENTICATION SYSTEM
# ===================================================================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def generate_username(full_name):
    """Generate username from full name (e.g., Berhanu Mekonen → berhanu.mekonen)"""
    parts = full_name.strip().lower().split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    else:
        return parts[0]

def generate_random_password(length=8):
    """Generate a random password"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Default admin account
DEFAULT_USERS = {
    "admin": {
        "password": hash_password("admin123"),
        "role": "admin",
        "name": "School Administrator"
    }
}

def init_user_db():
    if 'user_db' not in st.session_state:
        st.session_state.user_db = DEFAULT_USERS.copy()
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_role' not in st.session_state:
        st.session_state.current_role = None
    
    # School data
    if 'students' not in st.session_state:
        st.session_state.students = []
    if 'teachers' not in st.session_state:
        st.session_state.teachers = []
    if 'subjects' not in st.session_state:
        st.session_state.subjects = ["Mathematics", "English", "Science", "History", "Geography", "Physics", "Chemistry", "Biology", "Computer Science", "Physical Education"]
    if 'evaluations' not in st.session_state:
        st.session_state.evaluations = []
    if 'registration_period' not in st.session_state:
        st.session_state.registration_period = {
            "start": datetime.now(),
            "end": datetime.now() + timedelta(days=30)
        }
    if 'registration_open' not in st.session_state:
        st.session_state.registration_open = True
    if 'notifications' not in st.session_state:
        st.session_state.notifications = []
    if 'penalty_log' not in st.session_state:
        st.session_state.penalty_log = []

def add_notification(message, notification_type="info", user=None):
    """Add notification for specific user or all users"""
    st.session_state.notifications.append({
        "id": len(st.session_state.notifications),
        "message": message,
        "type": notification_type,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "read": False,
        "target_user": user  # None means all users
    })

def log_penalty(user, action, reason):
    st.session_state.penalty_log.append({
        "user": user,
        "action": action,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "penalty_type": "warning"
    })
    add_notification(f"⚠️ PENALTY: {user} attempted {action} outside allowed time", "warning")

def login_user(username, password):
    init_user_db()
    if username not in st.session_state.user_db:
        return False, "❌ User not found. Please contact administrator."
    stored_hash = st.session_state.user_db[username]["password"]
    if verify_password(password, stored_hash):
        st.session_state.logged_in = True
        st.session_state.current_user = username
        st.session_state.current_role = st.session_state.user_db[username]["role"]
        add_notification(f"Welcome, {st.session_state.user_db[username]['name']}!", "success")
        return True, "✅ Login successful!"
    else:
        return False, "❌ Incorrect password. Please try again."

def logout_user():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.current_role = None

# ===================================================================
# GRADE LOCALIZATION
# ===================================================================

def get_grade_display(grade):
    grade_num = grade.replace("Grade ", "")
    try:
        num = int(grade_num)
        if num <= 8:
            amharic_grades = {
                "1": "1ኛ", "2": "2ኛ", "3": "3ኛ", "4": "4ኛ",
                "5": "5ኛ", "6": "6ኛ", "7": "7ኛ", "8": "8ኛ"
            }
            return f"{amharic_grades.get(grade_num, grade_num)} ክፍል"
        else:
            return grade
    except:
        return grade

def get_grade_class(grade):
    grade_num = grade.replace("Grade ", "")
    try:
        num = int(grade_num)
        return "amharic-grade" if num <= 8 else "english-grade"
    except:
        return "english-grade"

def is_registration_open():
    period = st.session_state.registration_period
    now = datetime.now()
    return period["start"] <= now <= period["end"]

def check_action_allowed(action_name, user_name="Unknown"):
    if is_registration_open():
        return True, None
    else:
        period = st.session_state.registration_period
        reason = f"Attempted {action_name} outside allowed time. Allowed: {period['start'].strftime('%B %d, %Y %I:%M %p')} - {period['end'].strftime('%B %d, %Y %I:%M %p')}"
        log_penalty(user_name, action_name, reason)
        return False, reason

# ===================================================================
# CSS STYLES
# ===================================================================

st.markdown("""
<style>
    :root {
        --primary: #1B5E20;
        --primary-light: #2E7D32;
        --primary-dark: #0D3B0D;
        --accent: #1A73E8;
        --accent-hover: #1557B0;
        --gold: #FFD700;
        --dark: #0a1a0a;
        --dark-card: #0f2a0f;
    }

    html, body, .stApp {
        font-size: 18px !important;
        line-height: 1.8 !important;
        background: #FFFFFF !important;
    }

    .stApp, .main, .block-container {
        background: #FFFFFF !important;
        color: #202124 !important;
    }

    h1, h2, h3, h4, h5, h6, p, li, span, div, .stMarkdown, .stTextInput, .stSelectbox, .stButton {
        color: #202124 !important;
        font-weight: 500 !important;
    }

    h1 {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #1A73E8, #4285F4, #34A853);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    h2 {
        font-size: 2.8rem !important;
        font-weight: 700 !important;
        color: #1A73E8 !important;
        border-bottom: 3px solid #E8F0FE;
        padding-bottom: 0.5rem;
    }
    h3 {
        font-size: 2.2rem !important;
        font-weight: 600 !important;
        color: #1A73E8 !important;
    }
    h4 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #202124 !important;
    }

    p, li, .stMarkdown {
        font-size: 1.2rem !important;
        font-weight: 400 !important;
        line-height: 2 !important;
        color: #202124 !important;
    }

    .main-header {
        background: linear-gradient(rgba(27, 94, 32, 0.65), rgba(13, 59, 13, 0.75)),
                    url('https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=1200&h=400&fit=crop') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        padding: 2rem 3rem 1.8rem 3rem !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 4px 30px rgba(0,0,0,0.1) !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .main-header::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        bottom: 0 !important;
        background: linear-gradient(135deg, rgba(27, 94, 32, 0.3), rgba(13, 59, 13, 0.4)) !important;
        z-index: 0 !important;
    }

    .main-header .header-content {
        position: relative !important;
        z-index: 1 !important;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 20px;
    }

    .main-header .logo-section {
        display: flex;
        align-items: center;
        gap: 25px;
        flex: 1;
    }

    .main-header .logo-icon {
        width: 75px;
        height: 75px;
        background: rgba(255, 215, 0, 0.2) !important;
        border: 2px solid #FFD700 !important;
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.8rem;
        color: #FFFFFF;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        animation: pulse 3s infinite;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    .main-header .logo-text h1 {
        font-size: 3.5rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        background: none !important;
        -webkit-text-fill-color: #FFFFFF !important;
        margin: 0;
        text-shadow: 0 2px 30px rgba(0,0,0,0.3);
    }

    .main-header .logo-text .subtitle {
        color: rgba(255, 255, 255, 0.95) !important;
        font-size: 1.4rem !important;
        font-weight: 400 !important;
        margin: 5px 0 0 0;
        text-shadow: 0 1px 15px rgba(0,0,0,0.2);
    }

    .main-header .logo-text .subtitle .highlight {
        color: #FFD700 !important;
        font-weight: 600 !important;
    }

    .main-header .logo-text .developer-credit {
        color: rgba(255, 255, 255, 0.7) !important;
        font-size: 1rem !important;
        font-weight: 400 !important;
        margin: 8px 0 0 0;
        font-style: italic;
        letter-spacing: 0.5px;
        text-shadow: 0 1px 10px rgba(0,0,0,0.2);
    }

    .main-header .logo-text .developer-credit .highlight-name {
        color: #FFD700 !important;
        font-weight: 600 !important;
    }

    .main-header .logo-text .developer-credit .highlight-institution {
        color: #90EE90 !important;
        font-weight: 600 !important;
    }

    .main-header .header-right {
        display: flex;
        align-items: center;
        gap: 30px;
        flex-wrap: wrap;
    }

    .main-header .header-stats {
        display: flex;
        gap: 25px;
        flex-wrap: wrap;
        align-items: center;
    }

    .main-header .stat-item {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 12px 22px;
        border-radius: 14px;
        text-align: center;
        min-width: 100px;
        transition: all 0.3s;
    }

    .main-header .stat-item:hover {
        border-color: #FFD700;
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.2) !important;
    }

    .main-header .stat-item .number {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        color: #FFD700 !important;
        display: block;
    }

    .main-header .stat-item .label {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        color: rgba(255, 255, 255, 0.8) !important;
        display: block;
        margin-top: 4px;
    }

    .user-info {
        display: flex;
        align-items: center;
        gap: 15px;
        background: rgba(255, 255, 255, 0.9) !important;
        padding: 8px 20px;
        border-radius: 30px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        backdrop-filter: blur(10px);
    }

    .user-info .user-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: linear-gradient(135deg, #1A73E8, #4285F4);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 1.2rem;
    }

    .user-info .user-name {
        color: #202124 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }

    .status-bar {
        background: #F8F9FA !important;
        border: 1px solid #E8EAED;
        border-radius: 16px;
        padding: 1.2rem 2.5rem;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 15px;
    }

    .status-bar .status-dot {
        width: 14px;
        height: 14px;
        border-radius: 50%;
        display: inline-block;
        animation: blink 2s infinite;
    }

    .status-bar .status-dot.online {
        background: #34A853;
        box-shadow: 0 0 20px rgba(52,168,83,0.3);
    }

    .status-bar .status-dot.offline {
        background: #EA4335;
        box-shadow: 0 0 20px rgba(234,67,53,0.3);
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }

    .status-bar .status-text {
        color: #202124 !important;
        font-size: 1.2rem !important;
        font-weight: 500 !important;
    }

    .status-bar .status-text .highlight-green {
        color: #34A853 !important;
        font-weight: 700 !important;
    }

    .status-bar .status-text .highlight-red {
        color: #EA4335 !important;
        font-weight: 700 !important;
    }

    .status-bar .live-badge {
        background: linear-gradient(135deg, #1A73E8, #4285F4);
        color: #FFFFFF !important;
        padding: 6px 18px;
        border-radius: 25px;
        font-size: 1rem !important;
        font-weight: 600 !important;
        border: none;
    }

    .badge-pending {
        background: #FCE8E6 !important;
        color: #EA4335 !important;
        border: 1px solid #EA4335;
        padding: 4px 16px;
        border-radius: 25px;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    .badge-approved {
        background: #E6F4EA !important;
        color: #34A853 !important;
        border: 1px solid #34A853;
        padding: 4px 16px;
        border-radius: 25px;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    .badge-rejected {
        background: #FCE8E6 !important;
        color: #EA4335 !important;
        border: 1px solid #EA4335;
        padding: 4px 16px;
        border-radius: 25px;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }

    .stButton > button {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        padding: 0.9rem 2.2rem !important;
        background: linear-gradient(135deg, #1A73E8, #4285F4) !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        width: 100%;
        transition: all 0.3s !important;
        box-shadow: 0 2px 8px rgba(26,115,232,0.25) !important;
        min-height: 55px !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 4px 16px rgba(26,115,232,0.35) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: #F8F9FA !important;
        border-radius: 16px;
        padding: 8px;
        border: 1px solid #E8EAED;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 14px 30px;
        color: #5F6368 !important;
        font-weight: 500 !important;
        font-size: 1.1rem !important;
    }

    .stTabs [aria-selected="true"] {
        background: #FFFFFF !important;
        color: #1A73E8 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        border: 1px solid #E8EAED;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > input {
        background: #FFFFFF !important;
        border: 1px solid #DADCE0 !important;
        border-radius: 12px !important;
        color: #202124 !important;
        padding: 14px 20px !important;
        font-size: 1.15rem !important;
        font-weight: 400 !important;
        min-height: 55px !important;
        transition: all 0.3s !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #1A73E8 !important;
        box-shadow: 0 0 0 3px rgba(26,115,232,0.15) !important;
    }

    .css-1d391kg, .css-12w0qpk, [data-testid="stSidebar"] {
        background: #F8F9FA !important;
        border-right: 1px solid #E8EAED !important;
    }

    .student-card, .teacher-card, .eval-card {
        background: #FFFFFF !important;
        border: 1px solid #E8EAED !important;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .student-card:hover, .teacher-card:hover, .eval-card:hover {
        transform: translateY(-4px);
        border-color: #1A73E8 !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
    }

    .notification-item {
        padding: 0.75rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 4px solid #1A73E8;
        background: #F8F9FA;
    }

    .notification-item.unread {
        background: #E8F0FE;
        border-left-color: #EA4335;
    }

    .notification-item .notification-time {
        color: #5F6368 !important;
        font-size: 0.8rem !important;
    }

    .notification-item.warning {
        border-left-color: #EA4335;
        background: #FCE8E6;
    }

    .notification-item.success {
        border-left-color: #34A853;
        background: #E6F4EA;
    }

    .login-container {
        max-width: 500px;
        margin: 3rem auto;
        padding: 2.5rem;
        background: #FFFFFF !important;
        border: 1px solid #E8EAED;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }

    .admin-card {
        background: #FFFFFF !important;
        border: 1px solid #E8EAED;
        border-radius: 16px;
        padding: 2rem;
        margin: 1.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 4px 24px rgba(0,0,0,0.04);
    }

    .amharic-grade {
        font-family: 'Noto Sans Ethiopic', 'Segoe UI', sans-serif;
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #1A73E8 !important;
    }

    .english-grade {
        font-size: 1.3rem !important;
        font-weight: 600 !important;
        color: #1A73E8 !important;
    }

    .approval-card {
        background: #FFFFFF !important;
        border: 2px solid #E8EAED;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .approval-card.pending {
        border-left: 6px solid #FBBC04;
    }

    .approval-card.approved {
        border-left: 6px solid #34A853;
    }

    .approval-card.rejected {
        border-left: 6px solid #EA4335;
    }

    @media (max-width: 768px) {
        .block-container { padding: 0.5rem 0.75rem !important; }
        .main-header .logo-text h1 { font-size: 1.8rem !important; }
        .main-header .logo-text .subtitle { font-size: 1rem !important; }
        .main-header .header-stats .stat-item { min-width: 60px !important; padding: 8px 12px !important; }
        .main-header .header-stats .stat-item .number { font-size: 1.2rem !important; }
        .main-header .header-stats .stat-item .label { font-size: 0.7rem !important; }
    }

    @media (max-width: 480px) {
        .block-container { padding: 0.25rem 0.5rem !important; }
        .main-header .logo-text h1 { font-size: 1.4rem !important; }
        .main-header .header-content { flex-direction: column !important; align-items: flex-start !important; }
        .main-header .header-right { width: 100% !important; flex-direction: column !important; align-items: stretch !important; }
        .main-header .header-stats { display: grid !important; grid-template-columns: 1fr 1fr !important; gap: 8px !important; }
        .main-header .stat-item { min-width: auto !important; padding: 6px 10px !important; }
        .main-header .logo-icon { width: 50px !important; height: 50px !important; font-size: 1.8rem !important; }
        .login-container { padding: 1.5rem !important; margin: 1rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def get_student_by_id(student_id):
    for s in st.session_state.students:
        if s.get("id") == student_id:
            return s
    return None

def get_teacher_name(teacher_id):
    for t in st.session_state.teachers:
        if t.get("id") == teacher_id:
            return t.get("name", "Unknown")
    return "Unknown"

def get_teacher_by_username(username):
    for t in st.session_state.teachers:
        if t.get("username") == username:
            return t
    return None

def get_pending_evaluations():
    return [e for e in st.session_state.evaluations if e.get("status") == "pending"]

def get_evaluations_by_teacher(teacher_id):
    return [e for e in st.session_state.evaluations if e.get("teacher_id") == teacher_id]

def show_notification_center():
    unread = len([n for n in st.session_state.notifications if not n.get('read', False)])

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔔 Notifications")
        if unread > 0:
            st.warning(f"📌 {unread} new notification(s)")
    with col2:
        if st.button("Mark All Read"):
            for n in st.session_state.notifications:
                n['read'] = True
            st.rerun()

    if st.session_state.notifications:
        for note in reversed(st.session_state.notifications[-10:]):
            unread_class = "unread" if not note.get('read', False) else ""
            warning_class = "warning" if note.get('type') == 'warning' else ""
            success_class = "success" if note.get('type') == 'success' else ""
            st.markdown(f"""
            <div class="notification-item {unread_class} {warning_class} {success_class}">
                <strong>{note['message']}</strong>
                <div class="notification-time">⏱ {note['time']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notifications")

def show_penalty_log():
    st.markdown("### ⚠️ Penalty Log")

    if st.session_state.penalty_log:
        user_penalties = [p for p in st.session_state.penalty_log if p.get("user") == st.session_state.current_user]
        if user_penalties:
            st.markdown(f"""
            <div style="background:#FCE8E6;padding:1rem;border-radius:12px;border:2px solid #EA4335;margin-bottom:1rem;">
                <p style="color:#EA4335;font-weight:700;">⚠️ You have {len(user_penalties)} penalty record(s).</p>
                <p style="color:#EA4335;">Penalties are recorded when registration or evaluation is attempted outside the allowed time period.</p>
            </div>
            """, unsafe_allow_html=True)
            df = pd.DataFrame(user_penalties)
            st.dataframe(df, use_container_width=True)
        else:
            st.success("✅ You have no penalties recorded.")
    else:
        st.success("✅ No penalties recorded in the system.")

# ===================================================================
# ADMIN FUNCTIONS
# ===================================================================

def show_admin_panel():
    st.markdown("### 👨‍💼 Admin Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "📊 Overview",
        "⏰ Registration Period",
        "👨‍🏫 Teachers",
        "📚 Subjects",
        "📋 All Data",
        "✅ Approvals",
        "📊 Rankings",
        "👨‍🎓 Students",
        "📥 Import/Export",
        "📄 Approval Report",
        "⚠️ Penalty Log"
    ])

    with tab1:
        st.markdown("#### Dashboard Overview")

        pending_count = len(get_pending_evaluations())
        total_evals = len(st.session_state.evaluations)

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("👨‍🎓 Students", len(st.session_state.students))
        with col2:
            st.metric("👨‍🏫 Teachers", len(st.session_state.teachers))
        with col3:
            subjects_count = len([s for s in st.session_state.subjects if isinstance(s, dict)]) if st.session_state.subjects else len(st.session_state.subjects)
            st.metric("📋 Subjects", subjects_count)
        with col4:
            period = st.session_state.registration_period
            now = datetime.now()
            if period["start"] <= now <= period["end"]:
                st.metric("Registration", "🟢 Open", delta="Active")
            else:
                st.metric("Registration", "🔴 Closed", delta="Inactive")
        with col5:
            st.metric("📝 Evaluations", total_evals)
        with col6:
            st.metric("⏳ Pending", pending_count, delta="Needs Approval" if pending_count > 0 else "All Approved")

        st.markdown("#### 📅 Registration Period")
        period = st.session_state.registration_period
        st.info(f"**Start:** {period['start'].strftime('%B %d, %Y %I:%M %p')}")
        st.info(f"**End:** {period['end'].strftime('%B %d, %Y %I:%M %p')}")

        if is_registration_open():
            st.success("🟢 Registration is currently **OPEN**")
        else:
            st.error("🔴 Registration is currently **CLOSED**")
            st.warning("⚠️ Any registration or evaluation attempts outside this period will be logged as PENALTIES.")

        st.markdown("#### 📊 Recent Activities")
        if st.session_state.notifications:
            for note in reversed(st.session_state.notifications[-5:]):
                warning_class = "warning" if note.get('type') == 'warning' else ""
                success_class = "success" if note.get('type') == 'success' else ""
                st.markdown(f"""
                <div class="notification-item {warning_class} {success_class}">
                    <strong>{note['message']}</strong>
                    <div class="notification-time">⏱ {note['time']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent activities")

    with tab2:
        st.markdown("#### ⏰ Set Registration Period")

        period = st.session_state.registration_period

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", period["start"].date())
            start_time = st.time_input("Start Time", period["start"].time())
        with col2:
            end_date = st.date_input("End Date", period["end"].date())
            end_time = st.time_input("End Time", period["end"].time())

        if st.button("📅 Update Registration Period", use_container_width=True):
            new_start = datetime.combine(start_date, start_time)
            new_end = datetime.combine(end_date, end_time)
            if new_start >= new_end:
                st.error("❌ Start time must be before end time.")
            else:
                st.session_state.registration_period["start"] = new_start
                st.session_state.registration_period["end"] = new_end
                add_notification(f"Registration period updated: {new_start.strftime('%B %d, %Y %I:%M %p')} - {new_end.strftime('%B %d, %Y %I:%M %p')}", "info")
                st.success("✅ Registration period updated successfully!")
                st.rerun()

        if is_registration_open():
            st.success("🟢 Registration is currently **OPEN**")
            st.info("📝 Students can register and teachers can submit evaluations.")
        else:
            st.error("🔴 Registration is currently **CLOSED**")
            st.warning("⚠️ Any attempts to register or evaluate will be logged as PENALTIES.")

    with tab3:
        st.markdown("#### 👨‍🏫 Manage Teachers")

        with st.form("add_teacher"):
            teacher_name = st.text_input("Teacher Full Name *", placeholder="e.g., Abebe Kebede")
            teacher_subject = st.selectbox("Subject Taught *", [s if isinstance(s, str) else s.get("name", "") for s in st.session_state.subjects] if st.session_state.subjects else ["Mathematics", "English", "Science"])
            teacher_email = st.text_input("Email Address", placeholder="teacher@school.edu")

            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("➕ Add Teacher", use_container_width=True)

            if submitted and teacher_name:
                username = generate_username(teacher_name)
                if username in st.session_state.user_db:
                    counter = 1
                    while f"{username}{counter}" in st.session_state.user_db:
                        counter += 1
                    username = f"{username}{counter}"

                password = generate_random_password()
                hashed_pw = hash_password(password)

                st.session_state.user_db[username] = {
                    "password": hashed_pw,
                    "role": "teacher",
                    "name": teacher_name
                }

                teacher = {
                    "id": f"T{len(st.session_state.teachers)+1:04d}",
                    "name": teacher_name,
                    "subject": teacher_subject,
                    "email": teacher_email,
                    "username": username,
                    "password": password,
                    "added": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.teachers.append(teacher)

                add_notification(f"👨‍🏫 New teacher added: {teacher_name} (Username: {username})", "success")
                st.success(f"""
                ✅ Teacher {teacher_name} added successfully!

                **Login Credentials:**
                - **Username:** `{username}`
                - **Password:** `{password}`

                ⚠️ Please provide these credentials to the teacher. They will need to change their password on first login.
                """)
                st.rerun()
            elif submitted:
                st.error("❌ Please enter teacher name.")

        st.markdown("---")

        if st.session_state.teachers:
            st.markdown("#### 📋 All Teachers")
            for teacher in st.session_state.teachers:
                st.markdown(f"""
                <div class="teacher-card">
                    <h4>👨‍🏫 {teacher['name']}</h4>
                    <p><b>📚 Subject:</b> {teacher['subject']}</p>
                    <p><b>✉️ Email:</b> {teacher.get('email', 'N/A')}</p>
                    <p><b>👤 Username:</b> <code>{teacher.get('username', 'N/A')}</code></p>
                    <p><b>📅 Added:</b> {teacher.get('added', 'N/A')}</p>
                    <p><b>🔑 Password:</b> <code>{teacher.get('password', 'N/A')}</code> <span style="color:#5F6368;font-size:0.8rem;">(save this)</span></p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No teachers registered yet. Add your first teacher!")

    with tab4:
        st.markdown("#### 📚 Manage Subjects")

        current_subjects = [s if isinstance(s, str) else s.get("name", "") for s in st.session_state.subjects]
        if current_subjects:
            st.markdown("**Current Subjects:**")
            cols = st.columns(4)
            for i, subj in enumerate(current_subjects):
                cols[i % 4].markdown(f"- 📘 {subj}")
        else:
            st.info("No subjects available.")

        st.markdown("---")

        with st.form("add_subject"):
            new_subject = st.text_input("New Subject Name")
            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("➕ Add Subject", use_container_width=True)

            if submitted and new_subject:
                if new_subject not in current_subjects:
                    st.session_state.subjects.append(new_subject)
                    add_notification(f"📚 New subject added: {new_subject}", "info")
                    st.success(f"✅ Subject {new_subject} added!")
                    st.rerun()
                else:
                    st.warning(f"⚠️ Subject '{new_subject}' already exists.")

    with tab5:
        st.markdown("#### 📋 All Data")

        st.markdown("##### 👨‍🎓 Students")
        if st.session_state.students:
            df_students = pd.DataFrame(st.session_state.students)
            df_students["Grade Display"] = df_students["grade"].apply(get_grade_display)
            st.dataframe(df_students, use_container_width=True)
        else:
            st.info("No students registered yet.")

        st.markdown("##### 👨‍🏫 Teachers")
        if st.session_state.teachers:
            df_teachers = pd.DataFrame(st.session_state.teachers)
            st.dataframe(df_teachers, use_container_width=True)
        else:
            st.info("No teachers yet.")

        st.markdown("##### 📝 Evaluations")
        if st.session_state.evaluations:
            df_evals = pd.DataFrame(st.session_state.evaluations)
            def status_badge(status):
                if status == "pending":
                    return "⏳ Pending"
                elif status == "approved":
                    return "✅ Approved"
                elif status == "rejected":
                    return "❌ Rejected"
                return status
            df_evals["Status"] = df_evals["status"].apply(status_badge)
            st.dataframe(df_evals, use_container_width=True)
        else:
            st.info("No evaluations yet.")

        st.markdown("##### 📤 Export Data")
        if st.button("📥 Export All Data (JSON)", use_container_width=True):
            data = {
                "students": st.session_state.students,
                "teachers": st.session_state.teachers,
                "evaluations": st.session_state.evaluations,
                "subjects": st.session_state.subjects,
                "penalty_log": st.session_state.penalty_log,
                "registration_period": {
                    "start": st.session_state.registration_period["start"].isoformat(),
                    "end": st.session_state.registration_period["end"].isoformat()
                },
                "exported_at": datetime.now().isoformat()
            }
            st.download_button(
                label="📥 Download JSON",
                data=json.dumps(data, indent=2),
                file_name=f"school_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("##### ⚠️ Danger Zone")
        if st.button("🗑️ Clear All Data (Admin Only)", use_container_width=True):
            if st.checkbox("I confirm I want to delete ALL data"):
                st.session_state.students = []
                st.session_state.teachers = []
                st.session_state.evaluations = []
                st.session_state.penalty_log = []
                add_notification("🗑️ All data cleared by admin", "warning")
                st.warning("All data has been cleared.")
                st.rerun()

    with tab6:
        st.markdown("#### ✅ Pending Approvals")

        pending = get_pending_evaluations()

        if not pending:
            st.success("🎉 No pending evaluations. All evaluations have been reviewed.")
        else:
            st.markdown(f"**{len(pending)} evaluation(s) awaiting approval**")

            for eval_item in pending:
                student = get_student_by_id(eval_item.get("student_id", ""))
                student_name = student.get("name", "Unknown") if student else "Unknown"
                grade_display = get_grade_display(student.get("grade", "")) if student else "N/A"
                teacher_name = get_teacher_name(eval_item.get("teacher_id", ""))

                assessments_html = ""
                for a in eval_item.get("assessments", []):
                    assessments_html += f"<li>{a['name']}: {a['score']} (Weight: {a['weight']})</li>"

                overall = eval_item.get("overall_score", 0)

                st.markdown(f"""
                <div class="approval-card pending">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4>👤 {student_name}</h4>
                            <p><b>📚 Grade:</b> {grade_display}</p>
                            <p><b>📋 Subject:</b> {eval_item.get('subject', 'N/A')}</p>
                            <p><b>👨‍🏫 Teacher:</b> {teacher_name}</p>
                            <p><b>📝 Remarks:</b> {eval_item.get('remarks', 'N/A')}</p>
                            <p><b>📊 Overall Score:</b> {overall}%</p>
                            <p><b>📅 Submitted:</b> {eval_item.get('date', 'N/A')}</p>
                            <p><b>Assessments:</b></p>
                            <ul>{assessments_html}</ul>
                        </div>
                        <div style="text-align:right;">
                            <span class="badge-pending">⏳ Pending</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve", key=f"approve_{eval_item['id']}", use_container_width=True):
                        eval_item["status"] = "approved"
                        add_notification(f"✅ Evaluation for {student_name} approved by admin", "success")
                        st.success(f"✅ Evaluation approved!")
                        st.rerun()
                with col2:
                    if st.button(f"❌ Reject", key=f"reject_{eval_item['id']}", use_container_width=True):
                        eval_item["status"] = "rejected"
                        add_notification(f"❌ Evaluation for {student_name} rejected by admin", "warning")
                        st.warning(f"❌ Evaluation rejected!")
                        st.rerun()
                st.markdown("---")

    with tab7:  # Rankings (FIXED: added key)
        st.markdown("#### 📊 Grade Rankings")

        grade_options = [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, index=0, key="rank_grade")

        students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
        if not students_in_grade:
            st.info(f"No students registered in {selected_grade} yet.")
        else:
            student_data = []
            for student in students_in_grade:
                evals = [e for e in st.session_state.evaluations
                         if e.get("student_id") == student["id"]
                         and e.get("status") == "approved"]
                if evals:
                    avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
                    student_data.append({
                        "Name": student["name"],
                        "Average Score": avg_score,
                        "Evaluations": len(evals)
                    })
                else:
                    student_data.append({
                        "Name": student["name"],
                        "Average Score": 0,
                        "Evaluations": 0
                    })

            df = pd.DataFrame(student_data)
            if not df.empty:
                df_sorted = df.sort_values("Average Score", ascending=False).reset_index(drop=True)
                df_sorted["Rank"] = df_sorted.index + 1
                df_sorted = df_sorted[["Rank", "Name", "Average Score", "Evaluations"]]
                st.dataframe(df_sorted, use_container_width=True, hide_index=True)
                st.metric("👥 Total Students", len(df_sorted))
                st.metric("🏆 Highest Average", f"{df_sorted['Average Score'].max()}%")
                st.metric("📉 Lowest Average", f"{df_sorted['Average Score'].min()}%")
            else:
                st.info("No approved evaluations yet for this grade.")

    with tab8:  # Student Management
        st.markdown("### 👨‍🎓 Student Management")

        # ---- Add Student Form ----
        with st.expander("➕ Add New Student", expanded=False):
            with st.form("add_student_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Full Name *")
                    age = st.number_input("Age", min_value=5, max_value=25, step=1)
                    grade = st.selectbox("Grade", [f"Grade {i}" for i in range(1, 13)])
                    semester = st.selectbox("Semester", ["Semester I", "Semester II", "Semester III"])
                with col2:
                    gender = st.selectbox("Gender", ["M", "F", "Other"])
                    parent = st.text_input("Parent/Guardian")
                    contact = st.text_input("Contact")
                    subjects = st.multiselect("Subjects", st.session_state.subjects)
                submitted = st.form_submit_button("Add Student")
                if submitted:
                    if not name or not subjects:
                        st.error("Name and at least one subject are required.")
                    else:
                        new_student = {
                            "id": f"S{len(st.session_state.students)+1:04d}",
                            "name": name,
                            "age": age,
                            "gender": gender,
                            "grade": grade,
                            "semester": semester,
                            "subjects": subjects,
                            "parent_name": parent,
                            "contact": contact,
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "evaluations_count": 0
                        }
                        st.session_state.students.append(new_student)
                        add_notification(f"👨‍🎓 Student {name} added manually", "success")
                        st.success(f"✅ Student {name} added!")
                        st.rerun()

        # ---- Student List with Delete ----
        st.markdown("#### 📋 All Students")
        if st.session_state.students:
            df = pd.DataFrame(st.session_state.students)
            display_cols = ["id", "name", "grade", "semester", "subjects"]
            st.dataframe(df[display_cols], use_container_width=True)

            st.markdown("#### 🗑️ Delete Student")
            student_to_delete = st.selectbox(
                "Select student to delete",
                options=[f"{s['name']} ({s['id']})" for s in st.session_state.students]
            )
            if student_to_delete:
                student_id = student_to_delete.split("(")[-1].replace(")", "")
                if st.button("Delete Selected Student", type="primary", use_container_width=True):
                    if st.checkbox(f"⚠️ Confirm delete of {student_to_delete}?"):
                        st.session_state.students = [s for s in st.session_state.students if s["id"] != student_id]
                        st.session_state.evaluations = [e for e in st.session_state.evaluations if e.get("student_id") != student_id]
                        add_notification(f"🗑️ Student {student_to_delete} deleted", "warning")
                        st.success(f"✅ Deleted {student_to_delete}")
                        st.rerun()
        else:
            st.info("No students registered yet.")

    with tab9:  # Import/Export
        st.markdown("### 📥 Import / Export Data")

        # ---- Import ----
        st.markdown("#### 📤 Import Students from Excel")
        uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df_sheets = pd.read_excel(uploaded_file, sheet_name=None)
                total_added = 0
                for sheet_name, sheet_df in df_sheets.items():
                    grade = " ".join(sheet_name.split()[:2]) if len(sheet_name.split()) >= 2 else sheet_name
                    # Find header row (contains "ተ.ቁ" or "No")
                    header_row = None
                    for idx, row in sheet_df.iterrows():
                        if "ተ.ቁ" in str(row.values) or "No" in str(row.values):
                            header_row = idx
                            break
                    if header_row is None:
                        continue
                    sheet_df.columns = sheet_df.iloc[header_row]
                    data_df = sheet_df.iloc[header_row+1:].reset_index(drop=True)
                    for _, row in data_df.iterrows():
                        name = row.get("የተማሪ ሙሉ ስም")
                        if pd.isna(name) or name == "":
                            continue
                        # Collect subjects from columns that are subject names
                        subject_cols = ["አማርኛ", "ግዕዝ", "እንግሊዘኛ(S", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"]
                        subjects = [col for col in subject_cols if col in sheet_df.columns]
                        student = {
                            "id": f"S{len(st.session_state.students)+1:04d}",
                            "name": name,
                            "grade": grade,
                            "semester": row.get("ሴሚስተር", "I"),
                            "subjects": subjects,
                            "age": row.get("እድሜ", 0),
                            "gender": row.get("ፆታ", ""),
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "evaluations_count": 0
                        }
                        st.session_state.students.append(student)
                        total_added += 1
                st.success(f"✅ Imported {total_added} students from {len(df_sheets)} sheets.")
                add_notification(f"📥 Imported {total_added} students via Excel", "info")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

        # ---- Export ----
        st.markdown("#### 📤 Export All Data")
        if st.button("📥 Export Students to Excel", use_container_width=True):
            if st.session_state.students:
                df_export = pd.DataFrame(st.session_state.students)
                df_export["subjects"] = df_export["subjects"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, sheet_name="Students", index=False)
                st.download_button(
                    label="Download Excel",
                    data=output.getvalue(),
                    file_name=f"students_export_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.warning("No students to export.")

    with tab10:  # Approval Report (FIXED: added key)
        st.markdown("### 📄 Approval Report (Grade‑wise)")

        grade_options = [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, key="report_grade")

        students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
        if not students_in_grade:
            st.info(f"No students in {selected_grade}.")
        else:
            report_data = []
            for student in students_in_grade:
                evals = [e for e in st.session_state.evaluations
                         if e.get("student_id") == student["id"] and e.get("status") == "approved"]
                if evals:
                    avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
                    latest_eval = evals[-1]
                    assessments = latest_eval.get("assessments", [])
                    test_scores = {a["name"]: a["score"] for a in assessments}
                else:
                    avg_score = 0
                    test_scores = {"Test 1": 0, "Test 2": 0, "Test 3": 0, "Test 4": 0, "Final Exam": 0}

                report_data.append({
                    "Student ID": student["id"],
                    "Name": student["name"],
                    "Semester": student.get("semester", ""),
                    "Test 1": test_scores.get("Test 1", 0),
                    "Test 2": test_scores.get("Test 2", 0),
                    "Test 3": test_scores.get("Test 3", 0),
                    "Test 4": test_scores.get("Test 4", 0),
                    "Final Exam": test_scores.get("Final Exam", 0),
                    "Overall Score": avg_score,
                    "Evaluations": len(evals)
                })

            df_report = pd.DataFrame(report_data)
            if not df_report.empty:
                df_report_sorted = df_report.sort_values("Overall Score", ascending=False).reset_index(drop=True)
                df_report_sorted["Rank"] = df_report_sorted.index + 1
                st.dataframe(df_report_sorted, use_container_width=True, hide_index=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_report_sorted.to_excel(writer, sheet_name=f"{selected_grade}_Report", index=False)
                st.download_button(
                    label="📥 Download Approval Report (Excel)",
                    data=output.getvalue(),
                    file_name=f"Approval_Report_{selected_grade}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            else:
                st.info("No approved evaluations for this grade yet.")

    with tab11:
        show_penalty_log()

# ===================================================================
# STUDENT FUNCTIONS
# ===================================================================

def show_student_panel():
    st.markdown("### 👨‍🎓 Student Dashboard")

    if not is_registration_open():
        period = st.session_state.registration_period
        st.error(f"""
        🔴 **Registration is currently CLOSED**

        Registration period:
        - **Start:** {period['start'].strftime('%B %d, %Y %I:%M %p')}
        - **End:** {period['end'].strftime('%B %d, %Y %I:%M %p')}

        ⚠️ **ATTENTION:** Any registration attempt outside this period will be logged as a PENALTY.
        Please contact the school administrator for assistance.
        """)
        return

    tab1, tab2 = st.tabs(["📝 Register", "📊 My Profile"])

    with tab1:
        st.markdown("#### 📝 Student Registration")

        allowed, reason = check_action_allowed("Student Registration", st.session_state.current_user)
        if not allowed:
            st.error(f"""
            ⚠️ **PENALTY WARNING!**

            {reason}

            You have been logged for attempting to register outside the allowed period.
            Please wait until the registration period opens.
            """)
            return

        with st.form("student_registration"):
            col1, col2 = st.columns(2)
            with col1:
                student_name = st.text_input("Full Name *", placeholder="e.g., Abebe Kebede")
                age = st.number_input("Age *", min_value=5, max_value=25, step=1)

                grade_options = [f"Grade {i}" for i in range(1, 13)]
                grade_display_options = [get_grade_display(g) for g in grade_options]
                selected_grade_idx = st.selectbox(
                    "Grade *",
                    range(len(grade_options)),
                    format_func=lambda i: grade_display_options[i]
                )
                grade = grade_options[selected_grade_idx]

            with col2:
                semester = st.selectbox("Semester *", ["Semester I", "Semester II"])
                parent_name = st.text_input("Parent/Guardian Name", placeholder="e.g., Kebede Alemu")
                contact = st.text_input("Contact Number", placeholder="+251 9XX XXX XXX")

            current_subjects = [s if isinstance(s, str) else s.get("name", "") for s in st.session_state.subjects]
            if not current_subjects:
                current_subjects = ["Mathematics", "English", "Science", "History", "Geography"]

            selected_subjects = st.multiselect("Select Subjects *", current_subjects, default=current_subjects[:3])

            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("📝 Register", use_container_width=True)

            if submitted:
                if not student_name or not age or not grade or not selected_subjects:
                    st.error("❌ Please fill in all required fields (*).")
                else:
                    student = {
                        "id": f"S{len(st.session_state.students)+1:04d}",
                        "name": student_name,
                        "age": age,
                        "grade": grade,
                        "grade_display": get_grade_display(grade),
                        "semester": semester,
                        "subjects": selected_subjects,
                        "parent_name": parent_name,
                        "contact": contact,
                        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "evaluations_count": 0
                    }
                    st.session_state.students.append(student)
                    add_notification(f"👨‍🎓 New student registered: {student_name} (Grade: {get_grade_display(grade)})", "success")
                    st.success(f"✅ Student {student_name} registered successfully!")
                    st.balloons()
                    st.rerun()

    with tab2:
        st.markdown("#### 📊 My Profile")

        student_name_input = st.text_input("Enter your registered name to view profile:", placeholder="Your full name...")

        if student_name_input:
            matching_students = [s for s in st.session_state.students if s["name"].lower() == student_name_input.lower()]
            if matching_students:
                student = matching_students[0]
                student_evals = [e for e in st.session_state.evaluations if e.get("student_id") == student["id"]]

                grade_display = get_grade_display(student["grade"])
                grade_class = get_grade_class(student["grade"])

                st.markdown(f"""
                <div class="student-card">
                    <h3>👤 {student['name']}</h3>
                    <p><b>ID:</b> {student['id']}</p>
                    <p><b>Age:</b> {student['age']}</p>
                    <p><b>Grade:</b> <span class="{grade_class}">{grade_display}</span></p>
                    <p><b>Semester:</b> {student['semester']}</p>
                    <p><b>Subjects:</b> {', '.join(student['subjects'])}</p>
                    <p><b>Registered:</b> {student.get('registered_at', 'N/A')}</p>
                    <p><b>Evaluations:</b> {len(student_evals)}</p>
                </div>
                """, unsafe_allow_html=True)

                if student_evals:
                    st.markdown("##### 📝 My Evaluations")
                    for eval_item in student_evals:
                        teacher_name = get_teacher_name(eval_item.get("teacher_id", ""))
                        status = eval_item.get("status", "pending")
                        status_label = "⏳ Pending" if status == "pending" else "✅ Approved" if status == "approved" else "❌ Rejected"
                        status_class = "badge-pending" if status == "pending" else "badge-approved" if status == "approved" else "badge-rejected"

                        st.markdown(f"""
                        <div class="eval-card">
                            <p><b>📚 Subject:</b> {eval_item.get('subject', 'N/A')}</p>
                            <p><b>👨‍🏫 Teacher:</b> {teacher_name}</p>
                            <p><b>📝 Evaluation:</b> {eval_item.get('evaluation', 'N/A')}</p>
                            <p><b>⭐ Score:</b> {eval_item.get('score', 'N/A')}/100</p>
                            <p><b>📅 Date:</b> {eval_item.get('date', 'N/A')}</p>
                            <p><b>Status:</b> <span class="{status_class}">{status_label}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No evaluations yet.")
            else:
                st.warning("No student found with that name. Please check your spelling.")

# ===================================================================
# TEACHER FUNCTIONS (ENHANCED)
# ===================================================================

def show_teacher_panel():
    st.markdown("### 👨‍🏫 Teacher Dashboard")

    teacher = get_teacher_by_username(st.session_state.current_user)
    if not teacher:
        st.error("❌ Teacher profile not found. Please contact administrator.")
        return

    teacher_id = teacher["id"]
    teacher_name = teacher["name"]
    teacher_subject = teacher.get("subject", "")

    if not teacher_subject:
        st.warning("No subject assigned. Please contact administrator.")
        return

    # Grade selector (persist in session)
    if "teacher_selected_grade" not in st.session_state:
        st.session_state.teacher_selected_grade = "Grade 1"

    grade_options = [f"Grade {i}" for i in range(1, 13)]
    selected_grade = st.selectbox(
        "📚 Select Grade to Evaluate",
        grade_options,
        index=grade_options.index(st.session_state.teacher_selected_grade),
        key="grade_selector"
    )
    st.session_state.teacher_selected_grade = selected_grade

    # Helper to get eligible students (subject + grade)
    def get_eligible_students(grade):
        return [s for s in st.session_state.students
                if s.get("grade") == grade
                and teacher_subject in s.get("subjects", [])]

    # Helper to get pending eval for a student
    def get_pending_eval(student_id):
        for e in st.session_state.evaluations:
            if (e.get("teacher_id") == teacher_id and
                e.get("student_id") == student_id and
                e.get("subject") == teacher_subject and
                e.get("status") == "pending"):
                return e
        return None

    # Helper to compute overall weighted score
    def compute_overall(assessments):
        total_weighted = 0
        total_weight = 0
        for a in assessments:
            score = a.get("score", 0)
            weight = a.get("weight", 0)
            total_weighted += score * weight
            total_weight += weight
        return round(total_weighted / total_weight, 2) if total_weight > 0 else 0

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Submit Evaluation",
        "📊 My Submissions",
        "📊 My Students",
        "✅ Approval Status"
    ])

    # ---------- TAB 1: Submit Evaluation ----------
    with tab1:
        st.markdown("#### 📝 Submit Student Evaluation")

        allowed, reason = check_action_allowed("Student Evaluation", teacher_name)
        if not allowed:
            st.error(f"⚠️ **PENALTY WARNING!**\n{reason}")
            return

        eligible_students = get_eligible_students(selected_grade)
        if not eligible_students:
            st.info(f"No students in {selected_grade} taking {teacher_subject}.")
            return

        # Student selection
        student_options = {f"{s['name']} ({get_grade_display(s['grade'])})": s["id"] for s in eligible_students}
        selected_display = st.selectbox("Select Student", list(student_options.keys()))
        student_id = student_options[selected_display]
        student = get_student_by_id(student_id)

        # Check existing pending evaluation
        existing_eval = get_pending_eval(student_id)
        if existing_eval:
            st.warning("⚠️ You already have a pending evaluation for this student. Edit it below.")
            assessments = existing_eval.get("assessments", [])
            remarks = existing_eval.get("remarks", "")
        else:
            assessments = [
                {"name": "Test 1", "score": 0, "weight": 10},
                {"name": "Test 2", "score": 0, "weight": 10},
                {"name": "Test 3", "score": 0, "weight": 10},
                {"name": "Test 4", "score": 0, "weight": 10},
                {"name": "Final Exam", "score": 0, "weight": 20}
            ]
            remarks = ""

        # Display student info
        grade_display = get_grade_display(student["grade"])
        st.markdown(f"""
        <div style="background:#F8F9FA;padding:1rem;border-radius:12px;margin-bottom:1rem;border-left:4px solid #1A73E8;">
            <p><b>👤 Student:</b> {student['name']}</p>
            <p><b>📚 Grade:</b> {grade_display}</p>
            <p><b>📋 Subject:</b> {teacher_subject}</p>
        </div>
        """, unsafe_allow_html=True)

        with st.form("assessment_form"):
            st.markdown("**Enter scores (0‑100) and weights for each assessment:**")
            new_assessments = []
            cols = st.columns(2)
            for i, a in enumerate(assessments):
                with cols[i % 2]:
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        score = st.number_input(
                            f"{a['name']} Score",
                            min_value=0, max_value=100, value=a.get("score", 0),
                            key=f"score_{student_id}_{i}"
                        )
                    with col2:
                        weight = st.selectbox(
                            f"{a['name']} Weight",
                            options=[5, 10, 15, 20, 30, 40, 50],
                            index=[5,10,15,20,30,40,50].index(a.get("weight", 10)),
                            key=f"weight_{student_id}_{i}"
                        )
                new_assessments.append({"name": a["name"], "score": score, "weight": weight})

            remarks = st.text_area("Remarks / Comments", value=remarks)

            submitted = st.form_submit_button("💾 Submit for Approval", use_container_width=True)

            if submitted:
                if sum(a["weight"] for a in new_assessments) == 0:
                    st.error("❌ At least one assessment must have a positive weight.")
                else:
                    overall = compute_overall(new_assessments)
                    if existing_eval:
                        existing_eval["assessments"] = new_assessments
                        existing_eval["remarks"] = remarks
                        existing_eval["overall_score"] = overall
                        existing_eval["date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                        add_notification(f"📝 Evaluation updated for {student['name']} (Pending)", "info")
                        st.success("✅ Evaluation updated successfully!")
                    else:
                        eval_item = {
                            "id": f"E{len(st.session_state.evaluations)+1:04d}",
                            "student_id": student_id,
                            "student_name": student["name"],
                            "teacher_id": teacher_id,
                            "teacher_name": teacher_name,
                            "subject": teacher_subject,
                            "assessments": new_assessments,
                            "remarks": remarks,
                            "overall_score": overall,
                            "status": "pending",
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.evaluations.append(eval_item)
                        add_notification(f"📝 New evaluation for {student['name']} (Pending)", "info")
                        st.success(f"✅ Evaluation submitted! Overall Score: {overall}%")
                        st.balloons()
                    st.rerun()

    # ---------- TAB 2: My Submissions ----------
    with tab2:
        st.markdown("#### 📊 My Submitted Evaluations")
        my_evals = [e for e in st.session_state.evaluations if e.get("teacher_id") == teacher_id]
        if not my_evals:
            st.info("You haven't submitted any evaluations yet.")
        else:
            for eval_item in reversed(my_evals):
                student = get_student_by_id(eval_item.get("student_id", ""))
                student_name = student.get("name", "Unknown") if student else "Unknown"
                status = eval_item.get("status", "pending")
                status_label = "⏳ Pending" if status == "pending" else "✅ Approved" if status == "approved" else "❌ Rejected"
                status_class = "badge-pending" if status == "pending" else "badge-approved" if status == "approved" else "badge-rejected"
                overall = eval_item.get("overall_score", 0)

                assessments_html = "".join(f"<li>{a['name']}: {a['score']} (W:{a['weight']})</li>" for a in eval_item.get("assessments", []))
                st.markdown(f"""
                <div class="eval-card">
                    <div style="display:flex;justify-content:space-between;">
                        <div>
                            <p><b>👤 Student:</b> {student_name}</p>
                            <p><b>📚 Subject:</b> {eval_item.get('subject', 'N/A')}</p>
                            <p><b>📊 Overall:</b> {overall}%</p>
                            <p><b>📅 Date:</b> {eval_item.get('date', 'N/A')}</p>
                            <ul>{assessments_html}</ul>
                        </div>
                        <div><span class="{status_class}">{status_label}</span></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if status == "pending":
                    if st.button(f"✏️ Edit", key=f"edit_{eval_item['id']}"):
                        st.session_state.edit_student_id = eval_item["student_id"]
                        st.rerun()

    # ---------- TAB 3: My Students ----------
    with tab3:
        st.markdown("#### 📊 My Students")
        students_in_grade = get_eligible_students(selected_grade)
        if students_in_grade:
            st.markdown(f"**Students in {selected_grade} taking {teacher_subject}:**")
            for s in students_in_grade:
                evals_count = len([e for e in st.session_state.evaluations
                                  if e.get("student_id") == s["id"]
                                  and e.get("subject") == teacher_subject])
                approved_count = len([e for e in st.session_state.evaluations
                                     if e.get("student_id") == s["id"]
                                     and e.get("subject") == teacher_subject
                                     and e.get("status") == "approved"])
                status = "✅ Approved" if approved_count > 0 else "⏳ Pending" if evals_count > 0 else "📝 Not Evaluated"
                grade_display = get_grade_display(s["grade"])
                grade_class = get_grade_class(s["grade"])
                st.markdown(f"""
                <div class="student-card">
                    <h4>👤 {s['name']}</h4>
                    <p><b>Grade:</b> <span class="{grade_class}">{grade_display}</span></p>
                    <p><b>Status:</b> {status}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No students in {selected_grade} taking your subject.")

    # ---------- TAB 4: Approval Status ----------
    with tab4:
        st.markdown("#### ✅ Approval Status")
        my_evals = [e for e in st.session_state.evaluations if e.get("teacher_id") == teacher_id]
        pending = [e for e in my_evals if e.get("status") == "pending"]
        approved = [e for e in my_evals if e.get("status") == "approved"]
        rejected = [e for e in my_evals if e.get("status") == "rejected"]
        col1, col2, col3 = st.columns(3)
        col1.metric("⏳ Pending", len(pending))
        col2.metric("✅ Approved", len(approved))
        col3.metric("❌ Rejected", len(rejected))

# ===================================================================
# LOGIN PAGE (without visible admin credentials)
# ===================================================================

def show_login_page():
    init_user_db()

    st.markdown("""
    <div style="text-align:center; padding:1rem 0;">
        <div style="font-size:4rem; margin-bottom:0.5rem;">🏫</div>
        <h1 style="font-size:3rem; margin:0;">School Registration Portal</h1>
        <p style="color:#5F6368; font-size:1.2rem; margin-top:0.5rem;">Admin-Controlled Student & Teacher Management System</p>
        <p style="color:#5F6368; font-size:1rem;">Grades 1-8 in Amharic · Grades 9-12 in English</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter password")

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("🔐 Sign In", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("❌ Please enter both username and password.")
                else:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        # Only show penalty warning (no credentials)
        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem; padding-top:1rem; border-top:1px solid #E8EAED;">
            <p style="color:#5F6368; font-size:0.85rem;">
                ⚠️ <b>Penalty System:</b> Any registration or evaluation attempts outside the allowed period are logged as penalties.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ===================================================================
# MAIN APPLICATION
# ===================================================================

def main():
    init_user_db()

    if not st.session_state.logged_in:
        show_login_page()
        return

    current_user = st.session_state.current_user
    role = st.session_state.current_role
    user_data = st.session_state.user_db.get(current_user, {})
    display_name = user_data.get("name", current_user.title())

    # SIDEBAR
    with st.sidebar:
        st.markdown("### School Portal")
        st.markdown("---")

        st.markdown(f"""
        <div style="background:#E8F0FE;padding:1rem;border-radius:12px;margin-bottom:1rem;">
            <p style="margin:0;font-weight:600;color:#1A73E8;">👤 {display_name}</p>
            <p style="margin:0;font-size:0.85rem;color:#5F6368;">@{current_user} · {role.title()}</p>
        </div>
        """, unsafe_allow_html=True)

        if role == "admin":
            nav_options = [
                "🏠 Dashboard",
                "👨‍🏫 Teachers",
                "👨‍🎓 Students",
                "📋 Evaluations",
                "✅ Approvals",
                "📊 Rankings",
                "📥 Import/Export",
                "📄 Approval Report",
                "⚠️ Penalty Log",
                "🔔 Notifications"
            ]
        elif role == "teacher":
            nav_options = ["👨‍🏫 My Dashboard", "📝 Submit Evaluation", "📊 My Students", "✅ Approval Status", "⚠️ My Penalties", "🔔 Notifications"]
        else:
            nav_options = ["👨‍🎓 My Profile", "📝 Register", "⚠️ My Penalties", "🔔 Notifications"]

        selected_page = st.radio("Navigation", nav_options, index=0)
        st.session_state.current_page = selected_page

        if st.button("🚪 Logout", use_container_width=True):
            logout_user()
            st.rerun()

        st.markdown("---")
        st.markdown("🏫 School Registration Portal")
        st.markdown("*Berhanu Mekonen, PhD*")
        st.markdown("*Arba Minch University*")

    # HEADER
    total_students = len(st.session_state.students)
    total_teachers = len(st.session_state.teachers)
    total_evaluations = len(st.session_state.evaluations)
    total_penalties = len(st.session_state.penalty_log)
    pending_count = len(get_pending_evaluations())

    st.markdown(f"""
    <div class="main-header">
        <div class="header-content">
            <div class="logo-section">
                <div class="logo-icon">🏫</div>
                <div class="logo-text">
                    <h1>School Registration Portal</h1>
                    <div class="subtitle">
                        {role.title()} Panel · <span class="highlight">{display_name}</span>
                    </div>
                    <div class="developer-credit">
                        🏫 <span class="highlight-name">Berhanu Mekonen, PhD</span> ·
                        <span class="highlight-institution">Arba Minch University</span> ·
                        August 14, 2026
                    </div>
                </div>
            </div>
            <div class="header-right">
                <div class="user-info">
                    <div class="user-avatar">{display_name[0]}</div>
                    <span class="user-name">{display_name}</span>
                </div>
                <div class="header-stats">
                    <div class="stat-item"><span class="number">{total_students}</span><span class="label">Students</span></div>
                    <div class="stat-item"><span class="number">{total_teachers}</span><span class="label">Teachers</span></div>
                    <div class="stat-item"><span class="number">{total_evaluations}</span><span class="label">Evaluations</span></div>
                    <div class="stat-item"><span class="number" style="color:#FBBC04;">{pending_count}</span><span class="label">Pending</span></div>
                    <div class="stat-item"><span class="number" style="color:#EA4335;">{total_penalties}</span><span class="label">Penalties</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # STATUS BAR
    if is_registration_open():
        dot_class = "online"
        status_text = f"<span class='highlight-green'>OPEN</span> · Registration & Evaluation active"
    else:
        dot_class = "offline"
        status_text = f"<span class='highlight-red'>CLOSED</span> · Registration & Evaluation locked · <span class='highlight-red'>Penalties apply</span>"

    period = st.session_state.registration_period
    st.markdown(f"""
    <div class="status-bar">
        <div>
            <span class="status-dot {dot_class}"></span>
            <span class="status-text">Status: {status_text}</span>
        </div>
        <div>
            <span class="live-badge">📅 {period['start'].strftime('%b %d')} → {period['end'].strftime('%b %d, %Y')}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # PAGE ROUTING
    current_page = getattr(st.session_state, 'current_page', "🏠 Dashboard")

    if role == "admin":
        if current_page == "🏠 Dashboard":
            show_admin_panel()
        elif current_page == "👨‍🏫 Teachers":
            # Quick teacher management – reuse the teacher management from tab3
            st.markdown("### 👨‍🏫 Teacher Management")
            tab1, tab2 = st.tabs(["📋 All Teachers", "➕ Add Teacher"])
            with tab1:
                if st.session_state.teachers:
                    for t in st.session_state.teachers:
                        st.markdown(f"""
                        <div class="teacher-card">
                            <h4>👨‍🏫 {t['name']}</h4>
                            <p><b>📚 Subject:</b> {t['subject']}</p>
                            <p><b>✉️ Email:</b> {t.get('email', 'N/A')}</p>
                            <p><b>👤 Username:</b> <code>{t.get('username', 'N/A')}</code></p>
                            <p><b>🔑 Password:</b> <code>{t.get('password', 'N/A')}</code></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No teachers yet.")
            with tab2:
                with st.form("add_teacher_simple"):
                    name = st.text_input("Teacher Name")
                    subject = st.selectbox("Subject", [s if isinstance(s, str) else s.get("name", "") for s in st.session_state.subjects] if st.session_state.subjects else ["Mathematics", "English", "Science"])
                    email = st.text_input("Email")
                    if st.form_submit_button("Add Teacher"):
                        if name:
                            username = generate_username(name)
                            if username in st.session_state.user_db:
                                counter = 1
                                while f"{username}{counter}" in st.session_state.user_db:
                                    counter += 1
                                username = f"{username}{counter}"
                            password = generate_random_password()
                            st.session_state.user_db[username] = {
                                "password": hash_password(password),
                                "role": "teacher",
                                "name": name
                            }
                            st.session_state.teachers.append({
                                "id": f"T{len(st.session_state.teachers)+1:04d}",
                                "name": name,
                                "subject": subject,
                                "email": email,
                                "username": username,
                                "password": password,
                                "added": datetime.now().strftime("%Y-%m-%d %H:%M")
                            })
                            add_notification(f"👨‍🏫 New teacher: {name}", "success")
                            st.success(f"✅ Teacher {name} added! Username: {username}, Password: {password}")
                            st.rerun()
                        else:
                            st.error("Please enter teacher name.")
        elif current_page == "👨‍🎓 Students":
            # Show student management (already integrated in tab8)
            st.markdown("### 👨‍🎓 Student Management")
            st.info("Use the **Admin Dashboard → Students** tab for full management (add/delete/import/export).")
        elif current_page == "📋 Evaluations":
            st.markdown("### 📋 All Evaluations")
            if st.session_state.evaluations:
                df = pd.DataFrame(st.session_state.evaluations)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No evaluations yet.")
        elif current_page == "✅ Approvals":
            st.markdown("### ✅ Pending Approvals")
            pending = get_pending_evaluations()
            if not pending:
                st.success("🎉 No pending evaluations.")
            else:
                for eval_item in pending:
                    student = get_student_by_id(eval_item.get("student_id", ""))
                    student_name = student.get("name", "Unknown") if student else "Unknown"
                    teacher_name = get_teacher_name(eval_item.get("teacher_id", ""))
                    with st.container():
                        st.markdown(f"""
                        <div class="approval-card pending">
                            <p><b>👤 Student:</b> {student_name}</p>
                            <p><b>📋 Subject:</b> {eval_item.get('subject', 'N/A')}</p>
                            <p><b>👨‍🏫 Teacher:</b> {teacher_name}</p>
                            <p><b>📝 Remarks:</b> {eval_item.get('remarks', 'N/A')}</p>
                            <p><b>📊 Overall Score:</b> {eval_item.get('overall_score', 0)}%</p>
                        </div>
                        """, unsafe_allow_html=True)
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✅ Approve", key=f"approve_simple_{eval_item['id']}", use_container_width=True):
                                eval_item["status"] = "approved"
                                add_notification(f"✅ Evaluation for {student_name} approved", "success")
                                st.success("✅ Approved!")
                                st.rerun()
                        with col2:
                            if st.button(f"❌ Reject", key=f"reject_simple_{eval_item['id']}", use_container_width=True):
                                eval_item["status"] = "rejected"
                                add_notification(f"❌ Evaluation for {student_name} rejected", "warning")
                                st.warning("❌ Rejected!")
                                st.rerun()
                        st.markdown("---")
        elif current_page == "📊 Rankings":
            # Show rankings (already in tab7)
            st.markdown("### 📊 Grade Rankings")
            grade_options = [f"Grade {i}" for i in range(1, 13)]
            selected_grade = st.selectbox("Select Grade", grade_options, index=0, key="rank_grade")
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            if not students_in_grade:
                st.info(f"No students registered in {selected_grade} yet.")
            else:
                student_data = []
                for student in students_in_grade:
                    evals = [e for e in st.session_state.evaluations
                             if e.get("student_id") == student["id"]
                             and e.get("status") == "approved"]
                    if evals:
                        avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
                        student_data.append({
                            "Name": student["name"],
                            "Average Score": avg_score,
                            "Evaluations": len(evals)
                        })
                    else:
                        student_data.append({
                            "Name": student["name"],
                            "Average Score": 0,
                            "Evaluations": 0
                        })
                df = pd.DataFrame(student_data)
                if not df.empty:
                    df_sorted = df.sort_values("Average Score", ascending=False).reset_index(drop=True)
                    df_sorted["Rank"] = df_sorted.index + 1
                    df_sorted = df_sorted[["Rank", "Name", "Average Score", "Evaluations"]]
                    st.dataframe(df_sorted, use_container_width=True, hide_index=True)
                    st.metric("👥 Total Students", len(df_sorted))
                    st.metric("🏆 Highest Average", f"{df_sorted['Average Score'].max()}%")
                    st.metric("📉 Lowest Average", f"{df_sorted['Average Score'].min()}%")
                else:
                    st.info("No approved evaluations yet for this grade.")
        elif current_page == "📥 Import/Export":
            st.markdown("### 📥 Import / Export Data")
            st.info("Please use the **Admin Dashboard → Import/Export** tab for full functionality.")
        elif current_page == "📄 Approval Report":
            st.markdown("### 📄 Approval Report (Grade‑wise)")
            # Same as tab10
            grade_options = [f"Grade {i}" for i in range(1, 13)]
            selected_grade = st.selectbox("Select Grade", grade_options, key="report_grade")
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            if not students_in_grade:
                st.info(f"No students in {selected_grade}.")
            else:
                report_data = []
                for student in students_in_grade:
                    evals = [e for e in st.session_state.evaluations
                             if e.get("student_id") == student["id"] and e.get("status") == "approved"]
                    if evals:
                        avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
                        latest_eval = evals[-1]
                        assessments = latest_eval.get("assessments", [])
                        test_scores = {a["name"]: a["score"] for a in assessments}
                    else:
                        avg_score = 0
                        test_scores = {"Test 1": 0, "Test 2": 0, "Test 3": 0, "Test 4": 0, "Final Exam": 0}
                    report_data.append({
                        "Student ID": student["id"],
                        "Name": student["name"],
                        "Semester": student.get("semester", ""),
                        "Test 1": test_scores.get("Test 1", 0),
                        "Test 2": test_scores.get("Test 2", 0),
                        "Test 3": test_scores.get("Test 3", 0),
                        "Test 4": test_scores.get("Test 4", 0),
                        "Final Exam": test_scores.get("Final Exam", 0),
                        "Overall Score": avg_score,
                        "Evaluations": len(evals)
                    })
                df_report = pd.DataFrame(report_data)
                if not df_report.empty:
                    df_report_sorted = df_report.sort_values("Overall Score", ascending=False).reset_index(drop=True)
                    df_report_sorted["Rank"] = df_report_sorted.index + 1
                    st.dataframe(df_report_sorted, use_container_width=True, hide_index=True)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_report_sorted.to_excel(writer, sheet_name=f"{selected_grade}_Report", index=False)
                    st.download_button(
                        label="📥 Download Approval Report (Excel)",
                        data=output.getvalue(),
                        file_name=f"Approval_Report_{selected_grade}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                else:
                    st.info("No approved evaluations for this grade yet.")
        elif current_page == "⚠️ Penalty Log":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

    elif role == "teacher":
        if current_page == "👨‍🏫 My Dashboard" or current_page == "📝 Submit Evaluation" or current_page == "📊 My Students" or current_page == "✅ Approval Status":
            show_teacher_panel()
        elif current_page == "⚠️ My Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

    else:  # student
        if current_page == "👨‍🎓 My Profile" or current_page == "📝 Register":
            show_student_panel()
        elif current_page == "⚠️ My Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

if __name__ == "__main__":
    main()
