# ===================================================================
# SCHOOL REGISTRATION PORTAL - PERSISTENT WITH SUPABASE
# All data stored in Supabase PostgreSQL – never lost.
# Admin can delete any record if needed.
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
import io
import uuid
import math
from supabase import create_client, Client

# ---- Supabase Client ----
def init_supabase():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase connection error: {e}. Please check your secrets.")
        st.stop()

def get_supabase():
    if "supabase" not in st.session_state:
        st.session_state.supabase = init_supabase()
    return st.session_state.supabase

# ---- Data Load & Sync ----
def load_all_data():
    supabase = get_supabase()
    
    # Students
    res = supabase.table("students").select("*").execute()
    st.session_state.students = res.data if res.data else []
    
    # Teachers
    res = supabase.table("teachers").select("*").execute()
    st.session_state.teachers = res.data if res.data else []
    
    # Evaluations
    res = supabase.table("evaluations").select("*").execute()
    st.session_state.evaluations = res.data if res.data else []
    
    # Batches
    res = supabase.table("batches").select("*").execute()
    st.session_state.batches = res.data if res.data else []
    
    # Users (convert to dict)
    res = supabase.table("users").select("*").execute()
    user_db = {}
    if res.data:
        for u in res.data:
            user_db[u["username"]] = {
                "password": u["password"],
                "role": u["role"],
                "name": u["name"]
            }
    st.session_state.user_db = user_db
    
    # Notifications
    res = supabase.table("notifications").select("*").order("id", desc=True).execute()
    st.session_state.notifications = res.data if res.data else []
    
    # Penalty log
    res = supabase.table("penalty_log").select("*").order("id", desc=True).execute()
    st.session_state.penalty_log = res.data if res.data else []

# ---- NEW sync_table handles NaN and no neq ----
def sync_table(table_name, data, key_column="id"):
    """Sync a table: delete all rows and insert new data, handling foreign keys and NaNs."""
    supabase = get_supabase()

    # Delete all rows – simple delete without condition.
    try:
        supabase.table(table_name).delete().execute()
    except Exception as e:
        st.warning(f"Could not clear table {table_name}: {e}")

    # Clean NaN values – replace with None (which becomes NULL in PostgreSQL)
    def clean_nan(item):
        if isinstance(item, float) and math.isnan(item):
            return None
        if isinstance(item, list):
            return [clean_nan(i) for i in item]
        if isinstance(item, dict):
            return {k: clean_nan(v) for k, v in item.items()}
        return item

    cleaned_data = []
    for record in data:
        cleaned_record = clean_nan(record)
        cleaned_data.append(cleaned_record)

    # Insert new data
    if cleaned_data:
        try:
            supabase.table(table_name).insert(cleaned_data).execute()
        except Exception as e:
            st.warning(f"Error inserting into {table_name}: {e}")

# ---- NEW sync_all respects foreign keys ----
def sync_all():
    """Sync all session state data to Supabase, respecting foreign key constraints."""
    # Delete all in correct order (children first)
    try:
        get_supabase().table("evaluations").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear evaluations: {e}")
    
    try:
        get_supabase().table("batches").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear batches: {e}")
    
    try:
        get_supabase().table("notifications").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear notifications: {e}")
    try:
        get_supabase().table("penalty_log").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear penalty_log: {e}")
    
    try:
        get_supabase().table("students").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear students: {e}")
    
    try:
        get_supabase().table("teachers").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear teachers: {e}")
    
    try:
        get_supabase().table("users").delete().execute()
    except Exception as e:
        st.warning(f"Could not clear users: {e}")
    
    # Insert in correct order (parents first)
    # Users first
    user_list = []
    for username, info in st.session_state.user_db.items():
        user_list.append({
            "username": username,
            "password": info["password"],
            "role": info["role"],
            "name": info["name"]
        })
    sync_table("users", user_list, key_column="username")
    
    # Teachers
    sync_table("teachers", st.session_state.teachers)
    
    # Students
    sync_table("students", st.session_state.students)
    
    # Batches (depends on teachers)
    sync_table("batches", st.session_state.batches)
    
    # Evaluations (depends on students and teachers)
    sync_table("evaluations", st.session_state.evaluations)
    
    # Notifications and penalty_log
    sync_table("notifications", st.session_state.notifications, key_column="id")
    sync_table("penalty_log", st.session_state.penalty_log, key_column="id")

# ---- Auth ----
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def generate_username(full_name):
    parts = full_name.strip().lower().split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    else:
        return parts[0]

def generate_random_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def init_user_db():
    # Load data from Supabase if not already in session
    if 'students' not in st.session_state:
        load_all_data()
    # Ensure default admin exists (if not in Supabase, it will be added)
    if "admin" not in st.session_state.user_db:
        st.session_state.user_db["admin"] = {
            "password": hash_password("admin123"),
            "role": "admin",
            "name": "School Administrator"
        }
        sync_all()
    
    if 'subjects' not in st.session_state:
        st.session_state.subjects = ["Mathematics", "English", "Science", "History", "Geography", "Physics", "Chemistry", "Biology", "Computer Science", "Physical Education"]
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'current_role' not in st.session_state:
        st.session_state.current_role = None
    if 'registration_period' not in st.session_state:
        st.session_state.registration_period = {
            "start": datetime.now(),
            "end": datetime.now() + timedelta(days=30)
        }
    if 'registration_open' not in st.session_state:
        st.session_state.registration_open = True

def login_user(username, password):
    # 🔒 TEMPORARY HARDCODE – allows admin login while we fix Supabase
    if username == "admin" and password == "admin123":
        st.session_state.logged_in = True
        st.session_state.current_user = "admin"
        st.session_state.current_role = "admin"
        add_notification("Welcome, School Administrator!", "success")
        return True, "✅ Login successful!"
    
    # Original authentication logic (for teachers and future admins)
    init_user_db()
    if username not in st.session_state.user_db:
        return False, "❌ User not found."
    stored_hash = st.session_state.user_db[username]["password"]
    if verify_password(password, stored_hash):
        st.session_state.logged_in = True
        st.session_state.current_user = username
        st.session_state.current_role = st.session_state.user_db[username]["role"]
        add_notification(f"Welcome, {st.session_state.user_db[username]['name']}!", "success")
        return True, "✅ Login successful!"
    else:
        return False, "❌ Incorrect password."

def logout_user():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.current_role = None

def add_notification(message, notification_type="info", user=None):
    supabase = get_supabase()
    new_notif = {
        "message": message,
        "type": notification_type,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "read": False,
        "target_user": user
    }
    try:
        res = supabase.table("notifications").insert(new_notif).execute()
        if res.data:
            st.session_state.notifications.insert(0, res.data[0])
        sync_all()
    except Exception as e:
        st.error(f"Error adding notification: {e}")

def log_penalty(user, action, reason):
    supabase = get_supabase()
    new_entry = {
        "user": user,
        "action": action,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "penalty_type": "warning"
    }
    try:
        res = supabase.table("penalty_log").insert(new_entry).execute()
        if res.data:
            st.session_state.penalty_log.insert(0, res.data[0])
        add_notification(f"⚠️ PENALTY: {user} attempted {action} outside allowed time", "warning")
        sync_all()
    except Exception as e:
        st.error(f"Error logging penalty: {e}")

# ---- Page config ----
st.set_page_config(
    page_title="School Registration Portal",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS (same as before - kept for brevity) ----
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

# ---- Helper functions ----
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

def get_pending_batches():
    return [b for b in st.session_state.batches if b.get("status") == "pending"]

def get_approved_evaluations_for_student(student_id):
    return [e for e in st.session_state.evaluations if e.get("student_id") == student_id and e.get("status") == "approved"]

def show_notification_center():
    unread = len([n for n in st.session_state.notifications if not n.get('read', False)])
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔔 Notifications")
        if unread > 0:
            st.warning(f"📌 {unread} new notification(s)")
    with col2:
        if st.button("Mark All Read"):
            supabase = get_supabase()
            for n in st.session_state.notifications:
                n['read'] = True
                try:
                    supabase.table("notifications").update({"read": True}).eq("id", n["id"]).execute()
                except:
                    pass
            sync_all()
            st.rerun()
    if st.session_state.notifications:
        for note in st.session_state.notifications[:10]:
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

# ---- ADMIN PANEL ----
def show_admin_panel():
    st.markdown("### 👨‍💼 Admin Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
        "📊 Overview",
        "⏰ Registration Period",
        "👨‍🏫 Teachers",
        "📚 Subjects",
        "📋 All Data",
        "✅ Approvals (Batches)",
        "📊 Rankings",
        "👨‍🎓 Students",
        "📥 Import/Export",
        "📄 Approval Report",
        "⚠️ Penalty Log"
    ])

    # --- Tab 1: Overview ---
    with tab1:
        st.markdown("#### Dashboard Overview")
        pending_batches = len(get_pending_batches())
        total_evals = len(st.session_state.evaluations)

        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("👨‍🎓 Students", len(st.session_state.students))
        with col2: st.metric("👨‍🏫 Teachers", len(st.session_state.teachers))
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
        with col5: st.metric("📝 Evaluations", total_evals)
        with col6: st.metric("⏳ Pending Batches", pending_batches, delta="Needs Approval" if pending_batches > 0 else "All Approved")

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
            for note in st.session_state.notifications[:5]:
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

    # --- Tab 2: Registration Period ---
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

    # --- Tab 3: Teachers (with delete) ---
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
                # Add to user_db
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
                sync_all()
                st.success(f"""
                ✅ Teacher {teacher_name} added successfully!
                **Login Credentials:**
                - **Username:** `{username}`
                - **Password:** `{password}`
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

            st.markdown("---")
            st.markdown("#### 🗑️ Delete Teacher")
            teacher_to_delete = st.selectbox(
                "Select teacher to delete",
                options=[f"{t['name']} ({t['id']})" for t in st.session_state.teachers]
            )
            if teacher_to_delete:
                teacher_id = teacher_to_delete.split("(")[-1].replace(")", "")
                if st.button("Delete this teacher", type="primary", use_container_width=True):
                    # Find username
                    username_to_remove = None
                    for t in st.session_state.teachers:
                        if t["id"] == teacher_id:
                            username_to_remove = t.get("username")
                            break
                    # Remove from teachers list
                    st.session_state.teachers = [t for t in st.session_state.teachers if t["id"] != teacher_id]
                    # Remove from user_db
                    if username_to_remove and username_to_remove in st.session_state.user_db:
                        del st.session_state.user_db[username_to_remove]
                    sync_all()
                    st.success(f"Deleted teacher {teacher_to_delete}")
                    add_notification(f"🗑️ Teacher {teacher_to_delete} deleted", "warning")
                    st.rerun()
        else:
            st.info("No teachers registered yet. Add your first teacher!")

    # --- Tab 4: Subjects ---
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
                    sync_all()
                    st.success(f"✅ Subject {new_subject} added!")
                    st.rerun()
                else:
                    st.warning(f"⚠️ Subject '{new_subject}' already exists.")

    # --- Tab 5: All Data ---
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

        st.markdown("##### 📝 Evaluations (Approved)")
        if st.session_state.evaluations:
            df_evals = pd.DataFrame(st.session_state.evaluations)
            st.dataframe(df_evals, use_container_width=True)
        else:
            st.info("No approved evaluations yet.")

        st.markdown("##### 📦 Batches (Pending)")
        if st.session_state.batches:
            df_batches = pd.DataFrame(st.session_state.batches)
            st.dataframe(df_batches, use_container_width=True)
        else:
            st.info("No batches.")

        st.markdown("##### 🔐 User Accounts")
        if st.session_state.user_db:
            user_list = []
            for username, data in st.session_state.user_db.items():
                user_list.append({
                    "Username": username,
                    "Role": data.get("role", "unknown"),
                    "Name": data.get("name", "")
                })
            df_users = pd.DataFrame(user_list)
            st.dataframe(df_users, use_container_width=True)
        else:
            st.info("No user accounts found.")

        st.markdown("##### 📤 Export Data")
        if st.button("📥 Export All Data (JSON)", use_container_width=True):
            data = {
                "students": st.session_state.students,
                "teachers": st.session_state.teachers,
                "evaluations": st.session_state.evaluations,
                "batches": st.session_state.batches,
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
            if st.checkbox("I confirm I want to delete ALL data (students, teachers, evaluations, batches, penalties)"):
                st.session_state.students = []
                st.session_state.teachers = []
                st.session_state.evaluations = []
                st.session_state.batches = []
                st.session_state.penalty_log = []
                sync_all()
                add_notification("🗑️ All data cleared by admin", "warning")
                st.warning("All data has been cleared.")
                st.rerun()

    # --- Tab 6: Approvals (Batches) - UPDATED with Teacher & Subject Title ---
    with tab6:
        st.markdown("#### ✅ Pending Batches")
        pending_batches = get_pending_batches()
        if not pending_batches:
            st.success("🎉 No pending batches. All evaluations have been reviewed.")
        else:
            st.markdown(f"**{len(pending_batches)} batch(es) awaiting approval**")
            for batch in pending_batches:
                batch_id = batch["id"]
                teacher_name = batch.get("teacher_name", "Unknown")
                subject = batch.get("subject", "N/A")
                grade = batch.get("grade", "N/A")
                student_count = len(batch.get("students", []))
                submitted_date = batch.get("submitted_at", "N/A")

                # ---- NEW: Large header with teacher and subject ----
                st.markdown(f"""
                <div class="approval-card pending">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4 style="color:#1A73E8;font-size:1.8rem;margin:0 0 0.5rem 0;">📦 Batch from {teacher_name} · {subject}</h4>
                            <p><b>📚 Subject:</b> {subject}</p>
                            <p><b>📋 Grade:</b> {grade}</p>
                            <p><b>👥 Students:</b> {student_count}</p>
                            <p><b>📅 Submitted:</b> {submitted_date}</p>
                            <p><b>Weights:</b> Test1={batch['weights']['Test 1']}, Test2={batch['weights']['Test 2']}, Test3={batch['weights']['Test 3']}, Test4={batch['weights']['Test 4']}, Final={batch['weights']['Final Exam']}</p>
                        </div>
                        <div style="text-align:right;">
                            <span class="badge-pending">⏳ Pending</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                df_batch = pd.DataFrame(batch["students"])
                st.dataframe(df_batch[["student_name", "Test 1", "Test 2", "Test 3", "Test 4", "Final Exam", "overall"]], use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve Batch", key=f"approve_batch_{batch_id}", use_container_width=True):
                        batch["status"] = "approved"
                        for student_entry in batch["students"]:
                            eval_item = {
                                "id": f"E{len(st.session_state.evaluations)+1:04d}",
                                "student_id": student_entry["student_id"],
                                "student_name": student_entry["student_name"],
                                "teacher_id": batch["teacher_id"],
                                "teacher_name": batch["teacher_name"],
                                "subject": batch["subject"],
                                "assessments": [
                                    {"name": "Test 1", "score": student_entry["Test 1"], "weight": batch["weights"]["Test 1"]},
                                    {"name": "Test 2", "score": student_entry["Test 2"], "weight": batch["weights"]["Test 2"]},
                                    {"name": "Test 3", "score": student_entry["Test 3"], "weight": batch["weights"]["Test 3"]},
                                    {"name": "Test 4", "score": student_entry["Test 4"], "weight": batch["weights"]["Test 4"]},
                                    {"name": "Final Exam", "score": student_entry["Final Exam"], "weight": batch["weights"]["Final Exam"]}
                                ],
                                "remarks": batch.get("remarks", ""),
                                "overall_score": student_entry["overall"],
                                "status": "approved",
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "batch_id": batch_id
                            }
                            st.session_state.evaluations.append(eval_item)
                        batch["status"] = "approved"
                        sync_all()
                        add_notification(f"✅ Batch from {teacher_name} approved ({student_count} students)", "success")
                        st.success(f"✅ Batch approved! {student_count} student evaluations created.")
                        st.rerun()
                with col2:
                    if st.button(f"❌ Reject Batch", key=f"reject_batch_{batch_id}", use_container_width=True):
                        batch["status"] = "rejected"
                        sync_all()
                        add_notification(f"❌ Batch from {teacher_name} rejected", "warning")
                        st.warning("❌ Batch rejected!")
                        st.rerun()
                st.markdown("---")

    # --- Tab 7: Rankings ---
    with tab7:
        st.markdown("#### 📊 Grade Rankings")
        grade_options = [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, index=0, key="rank_grade")
        students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
        if not students_in_grade:
            st.info(f"No students registered in {selected_grade} yet.")
        else:
            student_data = []
            for student in students_in_grade:
                evals = get_approved_evaluations_for_student(student["id"])
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

    # --- Tab 8: Students (with delete) ---
    with tab8:
        st.markdown("### 👨‍🎓 Student Management")
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
                        sync_all()
                        st.success(f"✅ Student {name} added!")
                        st.rerun()

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
                        sync_all()
                        add_notification(f"🗑️ Student {student_to_delete} deleted", "warning")
                        st.success(f"✅ Deleted {student_to_delete}")
                        st.rerun()
        else:
            st.info("No students registered yet.")

    # --- Tab 9: Import/Export (with NaN cleaning) ---
    with tab9:
        st.markdown("### 📥 Import / Export Data")
        st.markdown("#### 📤 Import Students from Excel")
        uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df_sheets = pd.read_excel(uploaded_file, sheet_name=None)
                total_added = 0

                def clean_nan_value(value):
                    if isinstance(value, float) and math.isnan(value):
                        return None
                    return value

                for sheet_name, sheet_df in df_sheets.items():
                    grade = " ".join(sheet_name.split()[:2]) if len(sheet_name.split()) >= 2 else sheet_name
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
                        subject_cols = ["አማርኛ", "ግዕዝ", "እንግሊዘኛ(S", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"]
                        subjects = [col for col in subject_cols if col in sheet_df.columns]
                        student = {
                            "id": f"S{len(st.session_state.students)+1:04d}",
                            "name": clean_nan_value(name),
                            "grade": clean_nan_value(grade),
                            "semester": clean_nan_value(row.get("ሴሚስተር", "I")),
                            "subjects": [clean_nan_value(s) for s in subjects],
                            "age": clean_nan_value(row.get("እድሜ", 0)),
                            "gender": clean_nan_value(row.get("ፆታ", "")),
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "evaluations_count": 0
                        }
                        st.session_state.students.append(student)
                        total_added += 1
                sync_all()
                st.success(f"✅ Imported {total_added} students from {len(df_sheets)} sheets.")
                add_notification(f"📥 Imported {total_added} students via Excel", "info")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

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

    # --- Tab 10: Approval Report ---
    with tab10:
        st.markdown("### 📄 Approval Report (Grade‑wise)")
        grade_options = [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, key="report_grade")
        students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
        if not students_in_grade:
            st.info(f"No students in {selected_grade}.")
        else:
            report_data = []
            for student in students_in_grade:
                evals = get_approved_evaluations_for_student(student["id"])
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

    # --- Tab 11: Penalty Log ---
    with tab11:
        show_penalty_log()

# ---- STUDENT PANEL ----
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
        """)
        return

    tab1, tab2 = st.tabs(["📝 Register", "📊 My Profile"])
    with tab1:
        st.markdown("#### 📝 Student Registration")
        allowed, reason = check_action_allowed("Student Registration", st.session_state.current_user)
        if not allowed:
            st.error(f"⚠️ **PENALTY WARNING!**\n{reason}")
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
                    sync_all()
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
                        status_label = "✅ Approved" if status == "approved" else "❌ Rejected" if status == "rejected" else "⏳ Pending"
                        status_class = "badge-approved" if status == "approved" else "badge-rejected" if status == "rejected" else "badge-pending"
                        st.markdown(f"""
                        <div class="eval-card">
                            <p><b>📚 Subject:</b> {eval_item.get('subject', 'N/A')}</p>
                            <p><b>👨‍🏫 Teacher:</b> {teacher_name}</p>
                            <p><b>📊 Overall Score:</b> {eval_item.get('overall_score', 0)}%</p>
                            <p><b>📅 Date:</b> {eval_item.get('date', 'N/A')}</p>
                            <p><b>Status:</b> <span class="{status_class}">{status_label}</span></p>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No evaluations yet.")
            else:
                st.warning("No student found with that name. Please check your spelling.")

# ---- TEACHER PANEL (UPDATED: Batch Submission & My Submissions with Teacher & Subject) ----
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

    def get_eligible_students(grade):
        return [s for s in st.session_state.students
                if s.get("grade") == grade
                and teacher_subject in s.get("subjects", [])]

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Batch Submission",
        "📊 My Submissions",
        "📊 My Students",
        "✅ Approval Status"
    ])

    # ---------- TAB 1: Submit Batch Evaluation (UPDATED with Teacher & Subject Title) ----------
    with tab1:
        st.markdown("#### 📝 Submit Batch Evaluation")
        # ---- NEW: Display teacher and subject ----
        st.markdown(f"""
        <div style="background:#E8F0FE;padding:1rem;border-radius:12px;margin-bottom:1rem;border-left:4px solid #1A73E8;">
            <h4 style="margin:0;color:#1A73E8;font-size:1.8rem;">👨‍🏫 Teacher: {teacher_name}</h4>
            <p style="margin:0;color:#202124;font-size:1.2rem;"><b>📚 Subject:</b> {teacher_subject}</p>
        </div>
        """, unsafe_allow_html=True)

        allowed, reason = check_action_allowed("Student Evaluation (Batch)", teacher_name)
        if not allowed:
            st.error(f"⚠️ **PENALTY WARNING!**\n{reason}")
            return

        eligible_students = get_eligible_students(selected_grade)
        if not eligible_students:
            st.info(f"No students in {selected_grade} taking {teacher_subject}.")
            return

        # Check for existing pending batch
        existing_batch = None
        for b in st.session_state.batches:
            if (b.get("teacher_id") == teacher_id and
                b.get("grade") == selected_grade and
                b.get("subject") == teacher_subject and
                b.get("status") == "pending"):
                existing_batch = b
                break

        if existing_batch:
            student_data = existing_batch["students"]
            weights = existing_batch["weights"]
            remarks = existing_batch.get("remarks", "")
        else:
            weights = {"Test 1": 10, "Test 2": 10, "Test 3": 10, "Test 4": 10, "Final Exam": 20}
            student_data = []
            for s in eligible_students:
                student_data.append({
                    "student_id": s["id"],
                    "student_name": s["name"],
                    "Test 1": 0,
                    "Test 2": 0,
                    "Test 3": 0,
                    "Test 4": 0,
                    "Final Exam": 0,
                    "overall": 0
                })
            remarks = ""

        st.markdown("**Set assessment weights (apply to all students):**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            w1 = st.selectbox("Test 1", options=[5,10,15,20,30,40,50], index=[5,10,15,20,30,40,50].index(weights["Test 1"]), key="w1")
        with col2:
            w2 = st.selectbox("Test 2", options=[5,10,15,20,30,40,50], index=[5,10,15,20,30,40,50].index(weights["Test 2"]), key="w2")
        with col3:
            w3 = st.selectbox("Test 3", options=[5,10,15,20,30,40,50], index=[5,10,15,20,30,40,50].index(weights["Test 3"]), key="w3")
        with col4:
            w4 = st.selectbox("Test 4", options=[5,10,15,20,30,40,50], index=[5,10,15,20,30,40,50].index(weights["Test 4"]), key="w4")
        with col5:
            wf = st.selectbox("Final Exam", options=[5,10,15,20,30,40,50], index=[5,10,15,20,30,40,50].index(weights["Final Exam"]), key="wf")
        new_weights = {"Test 1": w1, "Test 2": w2, "Test 3": w3, "Test 4": w4, "Final Exam": wf}

        def compute_overall_row(row, weights):
            total_weighted = (row["Test 1"] * weights["Test 1"] +
                              row["Test 2"] * weights["Test 2"] +
                              row["Test 3"] * weights["Test 3"] +
                              row["Test 4"] * weights["Test 4"] +
                              row["Final Exam"] * weights["Final Exam"])
            total_weight = sum(weights.values())
            return round(total_weighted / total_weight, 2) if total_weight > 0 else 0

        st.markdown("**Enter scores for each student (0–100):**")
        df_edit = pd.DataFrame(student_data)
        columns_order = ["student_id", "student_name", "Test 1", "Test 2", "Test 3", "Test 4", "Final Exam", "overall"]
        df_edit = df_edit[columns_order]

        edited_df = st.data_editor(
            df_edit,
            column_config={
                "student_id": st.column_config.TextColumn("ID", disabled=True),
                "student_name": st.column_config.TextColumn("Student Name", disabled=True),
                "Test 1": st.column_config.NumberColumn("Test 1", min_value=0, max_value=100, step=1),
                "Test 2": st.column_config.NumberColumn("Test 2", min_value=0, max_value=100, step=1),
                "Test 3": st.column_config.NumberColumn("Test 3", min_value=0, max_value=100, step=1),
                "Test 4": st.column_config.NumberColumn("Test 4", min_value=0, max_value=100, step=1),
                "Final Exam": st.column_config.NumberColumn("Final Exam", min_value=0, max_value=100, step=1),
                "overall": st.column_config.NumberColumn("Overall (calc)", disabled=True)
            },
            hide_index=True,
            use_container_width=True,
            key="batch_editor"
        )

        edited_df["overall"] = edited_df.apply(lambda row: compute_overall_row(row, new_weights), axis=1)
        remarks = st.text_area("Remarks / Comments (optional)", value=remarks)

        if st.button("💾 Submit Batch for Approval", use_container_width=True):
            students_list = edited_df.to_dict(orient="records")
            for rec in students_list:
                rec["overall"] = compute_overall_row(rec, new_weights)

            if existing_batch:
                existing_batch["students"] = students_list
                existing_batch["weights"] = new_weights
                existing_batch["remarks"] = remarks
                existing_batch["submitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                add_notification(f"📝 Batch updated for {teacher_name} ({selected_grade} {teacher_subject})", "info")
                st.success("✅ Batch updated successfully! Awaiting approval.")
            else:
                batch = {
                    "id": str(uuid.uuid4())[:8],
                    "teacher_id": teacher_id,
                    "teacher_name": teacher_name,
                    "grade": selected_grade,
                    "subject": teacher_subject,
                    "students": students_list,
                    "weights": new_weights,
                    "remarks": remarks,
                    "status": "pending",
                    "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.batches.append(batch)
                add_notification(f"📦 New batch submitted by {teacher_name} ({selected_grade} {teacher_subject})", "info")
                st.success("✅ Batch submitted successfully! Waiting for admin approval.")
                st.balloons()
            sync_all()
            st.rerun()

    # ---------- TAB 2: My Submissions (UPDATED with Teacher & Subject Title) ----------
    with tab2:
        st.markdown("#### 📊 My Submissions (Batches)")
        my_batches = [b for b in st.session_state.batches if b.get("teacher_id") == teacher_id]
        if not my_batches:
            st.info("You haven't submitted any batches yet.")
        else:
            for batch in reversed(my_batches):
                status = batch.get("status", "pending")
                status_label = "⏳ Pending" if status == "pending" else "✅ Approved" if status == "approved" else "❌ Rejected"
                status_class = "badge-pending" if status == "pending" else "badge-approved" if status == "approved" else "badge-rejected"
                student_count = len(batch.get("students", []))
                # ---- NEW: Large header with teacher and subject ----
                st.markdown(f"""
                <div class="eval-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4 style="color:#1A73E8;font-size:1.8rem;margin:0 0 0.5rem 0;">👨‍🏫 {batch['teacher_name']} · 📚 {batch['subject']}</h4>
                            <p><b>📋 Grade:</b> {batch['grade']}</p>
                            <p><b>👥 Students:</b> {student_count}</p>
                            <p><b>📅 Submitted:</b> {batch.get('submitted_at', 'N/A')}</p>
                        </div>
                        <div style="text-align:right;">
                            <span class="{status_class}">{status_label}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if status == "pending":
                    if st.button(f"✏️ Edit Batch", key=f"edit_batch_{batch['id']}"):
                        st.session_state.edit_batch_id = batch["id"]
                        st.rerun()

    # ---------- TAB 3: My Students ----------
    with tab3:
        st.markdown("#### 📊 My Students")
        students_in_grade = get_eligible_students(selected_grade)
        if students_in_grade:
            st.markdown(f"**Students in {selected_grade} taking {teacher_subject}:**")
            for s in students_in_grade:
                evals = get_approved_evaluations_for_student(s["id"])
                approved_count = len(evals)
                status = "✅ Approved" if approved_count > 0 else "📝 Not Evaluated"
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
        my_batches = [b for b in st.session_state.batches if b.get("teacher_id") == teacher_id]
        pending = [b for b in my_batches if b.get("status") == "pending"]
        approved = [b for b in my_batches if b.get("status") == "approved"]
        rejected = [b for b in my_batches if b.get("status") == "rejected"]
        col1, col2, col3 = st.columns(3)
        col1.metric("⏳ Pending Batches", len(pending))
        col2.metric("✅ Approved Batches", len(approved))
        col3.metric("❌ Rejected Batches", len(rejected))

# ---- LOGIN PAGE ----
def show_login_page():
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
        st.markdown("""
        <div style="text-align:center; margin-top:1.5rem; padding-top:1rem; border-top:1px solid #E8EAED;">
            <p style="color:#5F6368; font-size:0.85rem;">
                ⚠️ <b>Penalty System:</b> Any registration or evaluation attempts outside the allowed period are logged as penalties.
            </p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---- MAIN ----
def main():
    init_user_db()

    if not st.session_state.logged_in:
        show_login_page()
        return

    current_user = st.session_state.current_user
    role = st.session_state.current_role
    user_data = st.session_state.user_db.get(current_user, {})
    display_name = user_data.get("name", current_user.title())

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

    # ---- Header ----
    total_students = len(st.session_state.students)
    total_teachers = len(st.session_state.teachers)
    total_evaluations = len(st.session_state.evaluations)
    total_penalties = len(st.session_state.penalty_log)
    pending_batches = len(get_pending_batches())

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
                    <div class="stat-item"><span class="number" style="color:#FBBC04;">{pending_batches}</span><span class="label">Pending Batches</span></div>
                    <div class="stat-item"><span class="number" style="color:#EA4335;">{total_penalties}</span><span class="label">Penalties</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    # ---- Routing ----
    current_page = getattr(st.session_state, 'current_page', "🏠 Dashboard")

    if role == "admin":
        if current_page == "🏠 Dashboard":
            show_admin_panel()
        elif current_page == "👨‍🏫 Teachers":
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
                            sync_all()
                            st.success(f"✅ Teacher {name} added! Username: {username}, Password: {password}")
                            st.rerun()
                        else:
                            st.error("Please enter teacher name.")
        elif current_page == "👨‍🎓 Students":
            st.markdown("### 👨‍🎓 Student Management")
            st.info("Use the **Admin Dashboard → Students** tab for full management.")
        elif current_page == "📋 Evaluations":
            st.markdown("### 📋 All Evaluations")
            if st.session_state.evaluations:
                df = pd.DataFrame(st.session_state.evaluations)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No evaluations yet.")
        elif current_page == "✅ Approvals":
            st.info("Please use the **Admin Dashboard → Approvals (Batches)** tab.")
        elif current_page == "📊 Rankings":
            st.markdown("### 📊 Grade Rankings")
            grade_options = [f"Grade {i}" for i in range(1, 13)]
            selected_grade = st.selectbox("Select Grade", grade_options, index=0, key="rank_grade")
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            if not students_in_grade:
                st.info(f"No students registered in {selected_grade} yet.")
            else:
                student_data = []
                for student in students_in_grade:
                    evals = get_approved_evaluations_for_student(student["id"])
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
            grade_options = [f"Grade {i}" for i in range(1, 13)]
            selected_grade = st.selectbox("Select Grade", grade_options, key="report_grade")
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            if not students_in_grade:
                st.info(f"No students in {selected_grade}.")
            else:
                report_data = []
                for student in students_in_grade:
                    evals = get_approved_evaluations_for_student(student["id"])
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
