# ===================================================================
# SCHOOL REGISTRATION PORTAL - PERSISTENT WITH SUPABASE
# All data stored in Supabase PostgreSQL – never lost.
# Admin can delete any record permanently (using service_role key).
# Berhanu Mekonen, PhD, Arba Minch University, June 25, 2026
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
import time  # for celebration delays
from supabase import create_client, Client

# ===================================================================
# DEFAULT REMARKS TEXT (pre-filled for all new batches)
# ===================================================================
DEFAULT_REMARKS = "በአጠቃላይ የተማሪዎች ውጤት ጥሩ ነው፣ ነገር ግን የበለጠ ለማድረግ ከትምህርት ቤቱ ማህበረሰብ ተጨማሪ ጥረት ያስፈልጋል።"

# ===================================================================
# GRADE-SUBJECT MAPPING (Ethiopian Curriculum - SNNPE)
# ===================================================================

GRADE_SUBJECTS = {
    # Grades 1-4
    "Grade 1": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 2": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 3": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 4": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],

    # Grades 5-6
    "Grade 5": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "ጋሞኛ", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"],
    "Grade 6": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "ጋሞኛ", "ሒሳብ", "አ/ሳይንስ", "ግብረ -ገብ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"],

    # Grades 7-8
    "Grade 7": ["አማርኛ", "ግዕዝ", "English (G)", "Mathematics", "G/Science", "Citizenship", "Social study", "Gammogna", "P.V.A", "I.T", "C.T.E", "H.P.E"],
    "Grade 8": ["አማርኛ", "ግዕዝ", "English (G)", "Mathematics", "G/Science", "Citizenship", "Social study", "Gammogna", "P.V.A", "I.T", "C.T.E", "H.P.E"],

    # Grades 9-10
    "Grade 9": ["English", "Mathematics", "Physics", "Chemistry", "Biology", "Geography", "History", "Citizenship Education (CE)", "Information Technology (IT)", "አማርኛ", "Health and Physical Education (HPE)"],
    "Grade 10": ["English", "Mathematics", "Physics", "Chemistry", "Biology", "Geography", "History", "Citizenship Education (CE)", "Information Technology (IT)", "አማርኛ", "Health and Physical Education (HPE)"],

    # Grades 11-12
    "Grade 11": [
        "Biology", "Chemistry", "Physics", "Technical Drawing", "Mathematics", "English",
        "Information Technology (IT)", "Citizenship Education / Civics",
        "Geography", "History", "Economics", "General Business"
    ],
    "Grade 12": [
        "Biology", "Chemistry", "Physics", "Technical Drawing", "Mathematics", "English",
        "Information Technology (IT)", "Citizenship Education / Civics",
        "Geography", "History", "Economics", "General Business"
    ],
}

# ---- Assessment default maximum scores ----
DEFAULT_MAX_SCORES = {
    "Test 1": 10,
    "Test 2": 10,
    "Test 3": 10,
    "Test 4": 30,
    "Final Exam": 40
}

# ---- Allowed max score options ----
MAX_SCORE_OPTIONS = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

# ---- School Settings (can be edited by admin) ----
if 'school_name' not in st.session_state:
    st.session_state.school_name = "የሙከራ ትምህርት ቤት"
if 'school_city' not in st.session_state:
    st.session_state.school_city = "አርባ ምንጭ"
if 'director_name' not in st.session_state:
    st.session_state.director_name = "____________________________"

# ---- Supabase Client (anon) ----
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

# ---- Admin Client (service_role) for deletions ----
def init_supabase_admin():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["service_role_key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Admin Supabase connection error: {e}. Please check your service role key.")
        st.stop()

def get_supabase_admin():
    if "supabase_admin" not in st.session_state:
        st.session_state.supabase_admin = init_supabase_admin()
    return st.session_state.supabase_admin

# ---- Data Load ----
def load_all_data():
    supabase = get_supabase()
    res = supabase.table("students").select("*").execute()
    st.session_state.students = res.data if res.data else []
    res = supabase.table("teachers").select("*").execute()
    st.session_state.teachers = res.data if res.data else []
    res = supabase.table("evaluations").select("*").execute()
    st.session_state.evaluations = res.data if res.data else []
    res = supabase.table("batches").select("*").execute()
    st.session_state.batches = res.data if res.data else []
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
    res = supabase.table("notifications").select("*").order("id", desc=True).execute()
    st.session_state.notifications = res.data if res.data else []
    res = supabase.table("penalty_log").select("*").order("id", desc=True).execute()
    st.session_state.penalty_log = res.data if res.data else []
    # Load homeroom assignments
    res = supabase.table("homeroom_assignments").select("*").execute()
    st.session_state.homeroom_assignments = res.data if res.data else []

# ---- sync_table ----
def sync_table(table_name, data, key_column="id"):
    supabase_admin = get_supabase_admin()
    try:
        supabase_admin.table(table_name).delete().execute()
    except Exception as e:
        st.warning(f"Could not clear table {table_name}: {e}")
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
    if cleaned_data:
        try:
            supabase_admin.table(table_name).insert(cleaned_data).execute()
        except Exception as e:
            st.warning(f"Error inserting into {table_name}: {e}")

# ---- sync_all ----
def sync_all():
    supabase_admin = get_supabase_admin()
    tables = ["evaluations", "batches", "notifications", "penalty_log", "students", "teachers", "users", "homeroom_assignments"]
    for table in tables:
        try:
            supabase_admin.table(table).delete().execute()
        except Exception as e:
            st.warning(f"Could not clear {table}: {e}")
    user_list = []
    for username, info in st.session_state.user_db.items():
        user_list.append({
            "username": username,
            "password": info["password"],
            "role": info["role"],
            "name": info["name"]
        })
    sync_table("users", user_list, key_column="username")
    sync_table("teachers", st.session_state.teachers)
    sync_table("students", st.session_state.students)
    sync_table("batches", st.session_state.batches)
    sync_table("evaluations", st.session_state.evaluations)
    sync_table("notifications", st.session_state.notifications, key_column="id")
    sync_table("penalty_log", st.session_state.penalty_log, key_column="id")
    sync_table("homeroom_assignments", st.session_state.homeroom_assignments)

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

def get_all_subjects():
    all_subs = set()
    for subs in GRADE_SUBJECTS.values():
        all_subs.update(subs)
    return sorted(list(all_subs))

ALL_SUBJECTS = get_all_subjects()

# ---- Username uniqueness check (Option A) ----
def is_username_taken(username):
    """Check if a username already exists in the users table (direct Supabase query)."""
    supabase = get_supabase()
    try:
        res = supabase.table("users").select("username").eq("username", username).execute()
        return len(res.data) > 0
    except Exception as e:
        st.warning(f"Could not check username uniqueness: {e}")
        # Assume it's free if we can't query (fallback)
        return False

# ---- Modified init_user_db to use admin client ----
def init_user_db():
    if 'students' not in st.session_state:
        load_all_data()
    if "admin" not in st.session_state.user_db:
        st.session_state.user_db["admin"] = {
            "password": hash_password("adminbb"),
            "role": "admin",
            "name": "School Administrator"
        }
        supabase_admin = get_supabase_admin()
        try:
            supabase_admin.table("users").insert({
                "username": "admin",
                "password": hash_password("adminbb"),
                "role": "admin",
                "name": "School Administrator"
            }).execute()
        except:
            pass
        load_all_data()
    if 'subjects' not in st.session_state:
        st.session_state.subjects = ALL_SUBJECTS
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
    if 'celebration_dismissed' not in st.session_state:
        st.session_state.celebration_dismissed = False

def login_user(username, password):
    if username == "admin" and password == "adminbb":
        st.session_state.logged_in = True
        st.session_state.current_user = "admin"
        st.session_state.current_role = "admin"
        add_notification("Welcome, School Administrator!", "success")
        return True, "✅ Login successful!"
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
    st.session_state.celebration_dismissed = False   # reset so celebration shows again after logout

# ---- Modified add_notification to use admin client ----
def add_notification(message, notification_type="info", user=None):
    supabase_admin = get_supabase_admin()
    new_notif = {
        "message": message,
        "type": notification_type,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "read": False,
        "target_user": user
    }
    try:
        res = supabase_admin.table("notifications").insert(new_notif).execute()
        if res.data:
            st.session_state.notifications.insert(0, res.data[0])
    except Exception as e:
        st.error(f"Error adding notification: {e}")

# ---- Modified log_penalty to use admin client ----
def log_penalty(user, action, reason):
    supabase_admin = get_supabase_admin()
    new_entry = {
        "user": user,
        "action": action,
        "reason": reason,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "penalty_type": "warning"
    }
    try:
        res = supabase_admin.table("penalty_log").insert(new_entry).execute()
        if res.data:
            st.session_state.penalty_log.insert(0, res.data[0])
        add_notification(f"⚠️ PENALTY: {user} attempted {action} outside allowed time", "warning")
    except Exception as e:
        st.error(f"Error logging penalty: {e}")

# ---- Page config ----
st.set_page_config(
    page_title="School Registration Portal",
    page_icon="SRP🏫@ET",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS (full) ----
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

    .badge-subject-approved {
        background: #FFF3CD !important;
        color: #856404 !important;
        border: 1px solid #FFEEBA;
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

    .approval-card.subject-approved {
        border-left: 6px solid #FFC107;
    }

    .approval-card.approved {
        border-left: 6px solid #34A853;
    }

    .approval-card.rejected {
        border-left: 6px solid #EA4335;
    }

    /* ---- Watermark ---- */
    .watermark-container {
        position: relative;
        overflow: hidden;
    }
    .watermark-text {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-20deg);
        font-size: 3rem;
        font-weight: bold;
        color: rgba(0, 0, 0, 0.08);
        white-space: nowrap;
        pointer-events: none;
        z-index: 10;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.02);
        letter-spacing: 4px;
        width: 100%;
        text-align: center;
        font-style: italic;
    }

    @media (max-width: 768px) {
        .watermark-text {
            font-size: 1.5rem;
            transform: translate(-50%, -50%) rotate(-15deg);
        }
        .block-container { padding: 0.5rem 0.75rem !important; }
        .main-header .logo-text h1 { font-size: 1.8rem !important; }
        .main-header .logo-text .subtitle { font-size: 1rem !important; }
        .main-header .header-stats .stat-item { min-width: 60px !important; padding: 8px 12px !important; }
        .main-header .header-stats .stat-item .number { font-size: 1.2rem !important; }
        .main-header .header-stats .stat-item .label { font-size: 0.7rem !important; }
    }

    @media (max-width: 480px) {
        .watermark-text {
            font-size: 1rem;
            transform: translate(-50%, -50%) rotate(-10deg);
        }
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
    """Deprecated: kept for backward compatibility – use get_batches_for_subject_admin or get_batches_awaiting_final_approval."""
    return [b for b in st.session_state.batches if b.get("status") == "pending"]

def get_batches_for_subject_admin(admin_id):
    """Get all batches pending for a specific subject admin (status='pending' and subject_admin_id matches)."""
    return [b for b in st.session_state.batches if b.get("subject_admin_id") == admin_id and b.get("status") == "pending"]

def get_batches_awaiting_final_approval():
    """Get batches that need School Admin final approval (subject_approved) OR (pending with no subject_admin assigned)."""
    return [b for b in st.session_state.batches 
            if (b.get("status") == "subject_approved") or 
               (b.get("status") == "pending" and b.get("subject_admin_id") is None)]

def get_approved_evaluations_for_student(student_id):
    return [e for e in st.session_state.evaluations if e.get("student_id") == student_id and e.get("status") == "approved"]

def get_homeroom_teacher(grade, section):
    for h in st.session_state.homeroom_assignments:
        if h.get("grade") == grade and h.get("section") == section:
            return h.get("teacher_id")
    return None

def get_teacher_assignments_for_semester(teacher_id, semester):
    teacher = next((t for t in st.session_state.teachers if t.get("id") == teacher_id), None)
    if not teacher:
        return []
    assignments = json.loads(teacher.get("assignments", "[]"))
    return [a for a in assignments if a.get("semester") == semester]

def get_student_subject_scores(student_id, semester=None):
    """Return dict of subject -> average score for a student, optionally filtered by semester."""
    evals = [e for e in st.session_state.evaluations if e.get("student_id") == student_id and e.get("status") == "approved"]
    if semester:
        evals = [e for e in evals if e.get("semester") == semester]
    subject_scores = {}
    for e in evals:
        subject = e.get("subject")
        score = e.get("overall_score", 0)
        if subject not in subject_scores:
            subject_scores[subject] = []
        subject_scores[subject].append(score)
    # compute average per subject
    avg_scores = {}
    for subj, scores in subject_scores.items():
        avg_scores[subj] = round(sum(scores) / len(scores), 2)
    return avg_scores

# ---- Get student rank ----
def get_student_rank(student_id, grade, section):
    """
    Compute the student's rank within their grade and section based on overall average score.
    Returns: (rank_display_string, rank_number, total_students)
    """
    students_in_class = [s for s in st.session_state.students 
                         if s.get("grade") == grade and s.get("section") == section]
    if not students_in_class:
        return "1/1", 1, 1
    student_scores = []
    for s in students_in_class:
        evals = get_approved_evaluations_for_student(s["id"])
        avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2) if evals else 0
        student_scores.append({"id": s["id"], "avg": avg_score})
    sorted_students = sorted(student_scores, key=lambda x: x["avg"], reverse=True)
    total = len(sorted_students)
    rank = 1
    for i, s in enumerate(sorted_students):
        if s["id"] == student_id:
            rank = i + 1
            break
    return f"{rank}/{total}", rank, total

# ---- Get short homeroom comment based on grading scale ----
def get_homeroom_comment(avg_score):
    """
    Return a short and precise Amharic+English comment based on the grading scale.
    Includes a motivational message for each range.
    """
    if avg_score >= 90:
        amh = "እጅግ በጣም ጥሩ ከዚህ የተሻለ ለመስራት የተማሪዉና የወላጅ ጥረት ይታከልበት፡፡ «ትምህርት የወደፊት ሕይወትህ መክፈቻ ቁልፍ ነው፤ በጠንካራ ሥራ እያንዳንዱን በር ክፈት!»"
        eng = "Excellent. To achieve even better, the student and parents should intensify their effort. «Education is the key to your future life; open every door with hard work!»"
    elif avg_score >= 80:
        amh = "በጣም ጥሩ ከዚህ የተሻለ ለመስራት ትንሽ ተጨማሪ ጥረት ያስፈልጋል፡፡ «ትምህርት የወደፊት ሕይወትህ መክፈቻ ቁልፍ ነው፤ በጠንካራ ሥራ እያንዳንዱን በር ክፈት!»"
        eng = "Very good. A little more effort will lead to excellent results. «Education is the key to your future life; open every door with hard work!»"
    elif avg_score >= 60:
        amh = "በቂ ነው፤ የበለጠ ለማድረግ መማርን መለማመድ ያስፈልጋል፡፡ «ትምህርት የወደፊት ሕይወትህ መክፈቻ ቁልፍ ነው፤ በጠንካራ ሥራ እያንዳንዱን በር ክፈት!»"
        eng = "Satisfactory. More practice and study are needed to improve. «Education is the key to your future life; open every door with hard work!»"
    elif avg_score >= 50:
        amh = "መጠነኛ ነው፤ ከወላጆች እና ከመምህራን ተጨማሪ ክትትል ይጠበቃል፡፡ «ትምህርት የወደፊት ሕይወትህ መክፈቻ ቁልፍ ነው፤ በጠንካራ ሥራ እያንዳንዱን በር ክፈት!»"
        eng = "Fair. More attention from parents and teachers is needed. «Education is the key to your future life; open every door with hard work!»"
    else:
        amh = "ዝቅተኛ ነው፤ ወላጆችና መምህራን በጋራ ለማሻሻል ጥረት ማድረግ አለባቸው፡፡ «ትምህርት የወደፊት ሕይወትህ መክፈቻ ቁልፍ ነው፤ በጠንካራ ሥራ እያንዳንዱን በር ክፈት!»"
        eng = "Poor. Parents and teachers must work together to help the student improve. «Education is the key to your future life; open every door with hard work!»"
    return amh, eng

# ---- Get subject admin for a given subject ----
def get_subject_admin(subject):
    """Return teacher_id of the first teacher who administers the given subject."""
    for t in st.session_state.teachers:
        admin_subjects = json.loads(t.get("admin_subjects", "[]"))
        if subject in admin_subjects:
            return t["id"]
    return None

# ===================================================================
# ETHIOPIAN NEW YEAR CELEBRATION DETECTION & PAGE
# ===================================================================

def is_celebration_period():
    """
    Approximate Ethiopian New Year celebration period:
    Nehase 15 – Meskerem 20  (roughly Aug 21 – Sep 30 Gregorian).
    Returns True if today is within that window.
    """
    today = datetime.now()
    m, d = today.month, today.day
    # Nehase 15 ~ Aug 21, Meskerem 20 ~ Sep 30
    if m == 8 and d >= 21:
        return True
    if m == 9 and d <= 30:
        return True
    return False

def show_celebration_page():
    """Display a full‑screen Ethiopian New Year celebration with balloons, flags, and a portal entry button."""
    # CSS remains the same (using st.markdown with unsafe_allow_html=True is fine for styles)
    st.markdown("""
    <style>
        .celebration-wrapper {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            overflow: hidden;
            background: linear-gradient(180deg, #006B3F 0%, #FCD116 50%, #EF3340 100%);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-family: 'Noto Sans Ethiopic', 'Segoe UI', sans-serif;
        }
        .balloon {
            position: absolute;
            bottom: -100px;
            width: 60px;
            height: 80px;
            border-radius: 50% 50% 50% 50% / 40% 40% 60% 60%;
            animation: floatUp 8s linear infinite;
            opacity: 0.8;
        }
        .balloon::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 2px;
            height: 30px;
            background: #333;
        }
        @keyframes floatUp {
            0% { transform: translateY(0) scale(1) rotate(0deg); opacity: 0.8; }
            100% { transform: translateY(-120vh) scale(0.5) rotate(20deg); opacity: 0.2; }
        }
        .flag-container {
            position: absolute;
            width: 20vw;
            max-width: 250px;
            aspect-ratio: 3 / 2;
            border-radius: 12px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);
            animation: flagFloat 10s ease-in-out infinite;
            opacity: 0.85;
            z-index: 2;
        }
        .flag-stripe {
            width: 100%;
            height: 33.333%;
        }
        .flag-stripe.green  { background: #006B3F; }
        .flag-stripe.yellow { background: #FCD116; }
        .flag-stripe.red    { background: #EF3340; }
        .flag-left {
            top: 15%;
            left: 5%;
            animation-delay: 0s;
        }
        .flag-right {
            bottom: 20%;
            right: 5%;
            animation-delay: -5s;
        }
        @keyframes flagFloat {
            0%   { transform: rotate(-2deg) translate(0, 0); }
            25%  { transform: rotate(2deg) translate(15px, -10px); }
            50%  { transform: rotate(-1deg) translate(-10px, 5px); }
            75%  { transform: rotate(3deg) translate(10px, -5px); }
            100% { transform: rotate(-2deg) translate(0, 0); }
        }
        .celebration-content {
            position: relative;
            z-index: 10;
            text-align: center;
            color: white;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.5);
            padding: 1rem;
        }
        .celebration-title {
            font-size: 3.8rem;
            font-weight: 800;
            background: rgba(0,0,0,0.3);
            padding: 1rem 2rem;
            border-radius: 20px;
            backdrop-filter: blur(5px);
            border: 2px solid rgba(255,215,0,0.5);
            margin-bottom: 1rem;
            line-height: 1.3;
        }
        .celebration-subtitle {
            font-size: 2rem;
            background: rgba(0,0,0,0.2);
            padding: 0.5rem 2rem;
            border-radius: 30px;
            display: inline-block;
        }
        .flag-emojis {
            font-size: 3.5rem;
        }
        .celebration-btn {
            display: inline-block;
            margin-top: 2rem;
            padding: 1rem 3rem;
            font-size: 1.8rem;
            font-weight: 700;
            border-radius: 50px;
            background: #FCD116;
            color: #006B3F;
            border: 3px solid #EF3340;
            text-decoration: none;
            transition: all 0.3s;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            cursor: pointer;
        }
        .celebration-btn:hover {
            transform: scale(1.05);
            background: #EF3340;
            color: #FCD116;
            border-color: #006B3F;
        }
        .boom-text {
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: 4px;
            color: #FFD700;
            text-shadow: 0 0 20px rgba(255,215,0,0.6);
            margin-top: 0.5rem;
        }
        @media (max-width: 768px) {
            .flag-container { width: 30vw; max-width: 150px; }
            .celebration-title { font-size: 2.2rem; padding: 0.5rem 1rem; }
            .celebration-subtitle { font-size: 1.4rem; }
            .celebration-btn { font-size: 1.2rem; padding: 0.7rem 2rem; }
            .boom-text { font-size: 1.4rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    import random
    colors = ['#006B3F', '#FCD116', '#EF3340']
    balloon_html = ""
    for _ in range(40):
        color = random.choice(colors)
        left = random.randint(0, 95)
        size = random.randint(40, 80)
        delay = random.uniform(0, 8)
        duration = random.uniform(6, 10)
        balloon_html += f"""
        <div class="balloon" style="left:{left}%; width:{size}px; height:{size*1.2}px; 
             background:{color}; animation-duration:{duration}s; animation-delay:{delay}s;"></div>
        """

    html_content = f"""
    <div class="celebration-wrapper">
        {balloon_html}

        <!-- Ethiopian Flags (slow movement) -->
        <div class="flag-container flag-left">
            <div class="flag-stripe green"></div>
            <div class="flag-stripe yellow"></div>
            <div class="flag-stripe red"></div>
        </div>
        <div class="flag-container flag-right">
            <div class="flag-stripe green"></div>
            <div class="flag-stripe yellow"></div>
            <div class="flag-stripe red"></div>
        </div>

        <div style="position:absolute; top:0; left:0; width:100%; height:100%; background: rgba(0,0,0,0.2); z-index:5;"></div>
        <div class="celebration-content">
            <div class="flag-emojis">🇪🇹 🎉 🎊</div>
            <div class="celebration-title">እንኳን ለኢትዮጲያ ዘመን መለዎጫ በዓል አደረሳችሁ!🎉</div>
            <div class="celebration-subtitle">መልካም አዲስ ዓመት! Happy Ethiopian New Year!</div>
            <div style="margin: 0.8rem 0; font-size: 2rem; background: rgba(0,0,0,0.3); 
                        padding: 0.5rem 2rem; border-radius: 30px; display:inline-block;">
                🟢 🟡 🔴
            </div>
            <div class="boom-text">ኢትዮጲያ💪📚✍️🌍2019 ዓ.ም🕊️ 🎓🔥🚀 ኢትዮጲያ</div>
            <br>
            <a href="?celebration_dismissed=true" class="celebration-btn">🚪 Enter Portal</a>
        </div>
    </div>
    """

    # ---- The secure way to inject raw HTML ----
    try:
        # Streamlit >= 1.38 – direct HTML injection
        st.html(html_content)
    except AttributeError:
        # Fallback to the deprecated but still working method
        st.components.v1.html(html_content, height=800, scrolling=False)

# ===================================================================
# SUBJECT ADMIN PANEL
# ===================================================================

def show_subject_admin_panel():
    st.markdown("### 📋 Subject Admin Dashboard")

    teacher = get_teacher_by_username(st.session_state.current_user)
    if not teacher:
        st.error("Subject admin profile not found.")
        return

    teacher_id = teacher["id"]
    my_pending_batches = get_batches_for_subject_admin(teacher_id)

    if not my_pending_batches:
        st.success("🎉 No pending batches for your subjects.")
        return

    st.markdown(f"**{len(my_pending_batches)} batches awaiting your review**")

    for batch in my_pending_batches:
        batch_id = batch["id"]
        teacher_name = batch.get("teacher_name", "Unknown")
        subject = batch.get("subject", "N/A")
        grade = batch.get("grade", "N/A")
        section = batch.get("section", "N/A")
        semester = batch.get("semester", "N/A")
        student_count = len(batch.get("students", []))
        submitted_date = batch.get("submitted_at", "N/A")
        batch_remarks = batch.get("remarks", "")

        st.markdown(f"""
        <div class="approval-card pending">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                <div>
                    <h4 style="color:#1A73E8;font-size:1.8rem;margin:0 0 0.5rem 0;">📦 Batch from {teacher_name} · {subject}</h4>
                    <p><b>📚 Subject:</b> {subject}</p>
                    <p><b>📋 Grade:</b> {grade}</p>
                    <p><b>📌 Section:</b> {section}</p>
                    <p><b>📌 Semester:</b> {semester}</p>
                    <p><b>👥 Students:</b> {student_count}</p>
                    <p><b>📅 Submitted:</b> {submitted_date}</p>
                    <p><b>Batch Remarks:</b> {batch_remarks if batch_remarks else 'None'}</p>
                </div>
                <div style="text-align:right;">
                    <span class="badge-pending">⏳ Pending</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_batch = pd.DataFrame(batch["students"])
        display_cols = ["student_name", "Test 1", "Test 2", "Test 3", "Test 4", "Final Exam", "overall"]
        available_cols = [col for col in display_cols if col in df_batch.columns]
        st.dataframe(df_batch[available_cols], use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Approve", key=f"subj_approve_{batch['id']}", width='stretch'):
                supabase_admin = get_supabase_admin()
                try:
                    supabase_admin.table("batches").update({"status": "subject_approved"}).eq("id", batch["id"]).execute()
                    load_all_data()
                    add_notification(f"Batch {batch['id']} approved by subject admin {teacher['name']}", "success")
                    # Celebration
                    st.balloons()
                    st.markdown("""
                    <div style="background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                                padding: 2rem;
                                border-radius: 16px;
                                text-align: center;
                                border: 3px solid #43a047;">
                        <div style="font-size: 4rem;">📋✅👏📚</div>
                        <h2 style="color: #1a365d;">✅ Batch Approved by Subject Admin!</h2>
                        <p style="font-size: 1.2rem; color: #2d4059;">
                            🎈 Forwarded to School Admin for final approval. 🎈
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    time.sleep(1.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to approve: {e}")
        with col2:
            if st.button(f"❌ Reject", key=f"subj_reject_{batch['id']}", width='stretch'):
                supabase_admin = get_supabase_admin()
                try:
                    supabase_admin.table("batches").update({"status": "rejected"}).eq("id", batch["id"]).execute()
                    load_all_data()
                    add_notification(f"Batch {batch['id']} rejected by subject admin {teacher['name']}", "warning")
                    st.warning("❌ Batch rejected!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to reject: {e}")
        st.markdown("---")

# ===================================================================
# Penalty Log and Notification Center
# ===================================================================

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

def show_notification_center():
    unread = len([n for n in st.session_state.notifications if not n.get('read', False)])
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 🔔 Notifications")
        if unread > 0:
            st.warning(f"📌 {unread} new notification(s)")
    with col2:
        if st.button("Mark All Read", width='stretch'):
            supabase_admin = get_supabase_admin()
            for n in st.session_state.notifications:
                n['read'] = True
                try:
                    supabase_admin.table("notifications").update({"read": True}).eq("id", n["id"]).execute()
                except:
                    pass
            load_all_data()
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

# ===================================================================
# GENERATE STUDENT REPORT CARD (PREMIUM VERSION – FIXED OVERFLOW & BLANK LINES)
# ===================================================================

def generate_student_card(student, semester="Semester III"):
    """
    Generate a two‑page landscape HTML report card with:
    - Premium gold‑accented design.
    - Rank computed from student's grade and section.
    - Homeroom comment based on the grading scale (short + motivational).
    - Director's Name and Signature as blank dashed lines (manual fill).
    - Font sizes reduced to prevent margin overflow.
    """
    # ---- Student data ----
    name = student.get('name', '_________')
    gender = student.get('gender', '_________')
    age = student.get('age', '_________')
    address = student.get('address', '_________')
    grade = student.get('grade', 'Grade 1')
    section = student.get('section', 'A')
    academic_year = "2018"

    # ---- School settings (only school name is used now) ----
    school_name = st.session_state.school_name

    # ---- Scores ----
    sem1_scores = get_student_subject_scores(student['id'], "Semester I")
    sem2_scores = get_student_subject_scores(student['id'], "Semester II")
    all_subjects = set(sem1_scores.keys()) | set(sem2_scores.keys())
    sorted_subjects = sorted(all_subjects)

    table_rows = []
    total_sem1 = 0
    total_sem2 = 0
    for subj in sorted_subjects:
        s1 = sem1_scores.get(subj, 0)
        s2 = sem2_scores.get(subj, 0)
        avg = round((s1 + s2) / 2, 2) if (s1 or s2) else 0
        total_sem1 += s1
        total_sem2 += s2
        table_rows.append(f"<tr><td class='subject-name'>{subj}</td><td>{s1}</td><td>{s2}</td><td>{avg}</td></tr>")

    subject_count = len(sorted_subjects)
    avg_sem1 = round(total_sem1 / subject_count, 1) if subject_count > 0 else 0
    avg_sem2 = round(total_sem2 / subject_count, 1) if subject_count > 0 else 0
    overall_avg = round((avg_sem1 + avg_sem2) / 2, 1) if subject_count > 0 else 0

    # ---- Rank ----
    rank_display, _, _ = get_student_rank(student['id'], grade, section)
    rank = rank_display

    # ---- Homeroom comment ----
    amh_comment, eng_comment = get_homeroom_comment(overall_avg)

    # ---- Other fields ----
    absence = "3"
    conduct = "A"
    promoted = str(int(grade.replace("Grade ", "")) + 1) + "ኛ" if overall_avg >= 50 else "_________"

    # ---- Build HTML (compact, reduced font sizes) ----
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Student Report Card – {name}</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Ethiopic:wght@400;600;700&family=Segoe+UI:wght@400;600;700&display=swap');
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        @page {{ size: landscape; margin: 1cm 1.2cm; }}
        body {{
            font-family: 'Noto Sans Ethiopic', 'Segoe UI', Tahoma, sans-serif;
            background: #f0f2f5;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 10px;
            font-size: 0.8rem;
        }}
        .card-container {{
            max-width: 1100px;
            width: 100%;
            background: #ffffff;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(0, 20, 40, 0.15);
            border: 2px solid #c9a84c;
            padding: 16px 18px;
            position: relative;
            overflow: visible !important;
        }}
        .card-container::before {{
            content: '';
            position: absolute;
            top: -6px;
            left: 30px;
            right: 30px;
            height: 6px;
            background: linear-gradient(90deg, #c9a84c, #f5e7b0, #c9a84c);
            border-radius: 12px 12px 0 0;
        }}
        .page {{
            display: flex;
            flex-wrap: wrap;
            width: 100%;
            min-height: 400px;
        }}
        .page-break {{
            page-break-before: always;
            border-top: 3px double #c9a84c;
            margin-top: 12px;
            padding-top: 12px;
        }}
        .column {{
            flex: 1 1 50%;
            padding: 6px 10px;
            min-width: 250px;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }}
        /* ---- Grading policy ---- */
        .grading-policy {{
            font-size: 0.75rem;
            line-height: 1.5;
            color: #1f2a3e;
        }}
        .grading-policy h2 {{
            font-size: 1.1rem;
            font-weight: 700;
            color: #1a365d;
            border-bottom: 3px solid #c9a84c;
            padding-bottom: 4px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}
        .grading-policy h2 span {{
            font-size: 0.75rem;
            font-weight: 400;
            color: #5a6f8e;
        }}
        .grade-scale {{
            background: #f1f5fb;
            border-radius: 10px;
            padding: 8px 12px;
            margin: 8px 0;
            border-left: 3px solid #c9a84c;
            font-size: 0.75rem;
        }}
        .grade-scale div {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px dashed #dce3ed;
            padding: 1px 0;
            flex-wrap: wrap;
        }}
        .grade-scale div:last-child {{ border-bottom: none; }}
        .grade-scale .range {{ font-weight: 600; color: #1a365d; min-width: 80px; }}
        .grade-scale .desc {{ color: #2d4059; }}
        .divider-light {{
            height: 1px;
            background: linear-gradient(90deg, #dce3ed, transparent);
            margin: 10px 0;
        }}
        /* ---- Cover page ---- */
        .cover-page {{ text-align: center; }}
        .cover-page .school-name {{
            font-size: 1.3rem;
            font-weight: 700;
            color: #1a365d;
            letter-spacing: 1px;
            word-wrap: break-word;
        }}
        .cover-page .card-title {{
            font-size: 0.95rem;
            font-weight: 600;
            color: #1a365d;
            margin: 4px 0 10px 0;
            border-bottom: 2px solid #c9a84c;
            padding-bottom: 4px;
            word-wrap: break-word;
            line-height: 1.3;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 6px 0;
            font-size: 0.75rem;
        }}
        .info-table td {{
            padding: 4px 3px;
            vertical-align: top;
            word-wrap: break-word;
        }}
        .info-table .label {{
            font-weight: 600;
            color: #1a365d;
            white-space: nowrap;
        }}
        .info-table .value {{
            border-bottom: 1px dashed #c9d6e8;
            padding-left: 6px;
            min-width: 60px;
            text-align: left;
            word-break: break-word;
        }}
        .motto-box {{
            margin-top: 12px;
            padding: 8px 12px;
            background: linear-gradient(135deg, #f6f2e7, #faf8f2);
            border-radius: 30px;
            border: 1px solid #e1d5b8;
            text-align: center;
            font-style: italic;
            font-weight: 500;
            color: #2d4059;
            font-size: 0.8rem;
            letter-spacing: 0.3px;
            word-wrap: break-word;
        }}
        /* ---- Marks table ---- */
        .marks-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.7rem;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }}
        .marks-table th {{
            background: #1a365d;
            color: #fff;
            font-weight: 600;
            padding: 5px 3px;
            text-align: center;
            border: none;
            font-size: 0.65rem;
            letter-spacing: 0.3px;
        }}
        .marks-table th:first-child {{ text-align: left; padding-left: 8px; }}
        .marks-table td {{
            padding: 4px 3px;
            text-align: center;
            border: 1px solid #e2e8f0;
            background: #fff;
            font-size: 0.7rem;
        }}
        .marks-table tr:nth-child(even) td {{ background: #f8faff; }}
        .marks-table .subject-name {{
            font-weight: 600;
            text-align: left;
            padding-left: 8px;
            background: #f0f4fb !important;
            color: #1a365d;
            font-size: 0.7rem;
        }}
        .marks-table .total-row td {{
            font-weight: 700;
            background: #e8eff9 !important;
            border-top: 2px solid #1a365d;
            border-bottom: 2px solid #1a365d;
        }}
        .marks-table .avg-row td {{
            font-weight: 700;
            background: #dce6f2 !important;
            border-top: 2px solid #1a365d;
        }}
        .marks-table .stat-row td {{
            padding: 3px 4px;
            background: #f5f8fa;
            font-size: 0.7rem;
        }}
        .marks-table .stat-label {{
            font-weight: 600;
            text-align: left;
            padding-left: 8px;
            color: #1a365d;
        }}
        /* ---- Comments ---- */
        .comments-section {{
            font-size: 0.75rem;
        }}
        .comments-section .section-title {{
            font-size: 0.95rem;
            font-weight: 700;
            color: #1a365d;
            text-align: center;
            border-bottom: 2px solid #c9a84c;
            padding-bottom: 4px;
            margin-bottom: 10px;
            word-wrap: break-word;
        }}
        .comments-section .semester-block {{
            border: 1px solid #d4dce8;
            border-radius: 10px;
            padding: 8px 10px;
            margin-bottom: 10px;
            background: #fafcff;
        }}
        .comments-section .semester-title {{
            font-weight: 700;
            color: #1a365d;
            border-bottom: 1px solid #c9a84c;
            padding-bottom: 3px;
            margin-bottom: 6px;
            text-align: center;
            font-size: 0.8rem;
        }}
        .comments-section .comment-line {{
            margin: 3px 0;
            display: flex;
            align-items: center;
            flex-wrap: wrap;
        }}
        .comments-section .comment-line .line {{
            flex: 1;
            border-bottom: 1px solid #8a9a8a;
            margin-left: 6px;
            height: 14px;
            min-width: 40px;
        }}
        .director-sign {{
            margin-top: 10px;
            border-top: 1px solid #d4dce8;
            padding-top: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }}
        .director-sign .line {{
            flex: 1;
            border-bottom: 1px solid #8a9a8a;
            margin-left: 8px;
            height: 14px;
            min-width: 40px;
        }}
        .teacher-comment-box {{
            min-height: 24px;
            border-bottom: 1px dashed #aaa;
            margin: 4px 0 8px 0;
            padding: 4px 6px;
            background: #f9fafb;
            border-radius: 4px;
            font-size: 0.7rem;
            line-height: 1.4;
        }}
        /* ---- Print ---- */
        @media print {{
            body {{ background: white; padding: 0; }}
            .card-container {{
                box-shadow: none;
                border: 2px solid #c9a84c;
                border-radius: 16px;
                padding: 12px 14px;
                max-width: 100%;
                overflow: visible !important;
            }}
            .card-container::before {{ display: none; }}
            .page {{ min-height: 0; }}
            .page-break {{
                border-top: none;
                margin-top: 0;
                padding-top: 0;
            }}
            .column {{ padding: 4px 8px; }}
        }}
        /* ---- Responsive ---- */
        @media (max-width: 768px) {{
            .column {{ flex: 1 1 100%; padding: 4px 6px; min-width: 0; }}
            .page-break {{ border-top: 2px solid #c9a84c; margin-top: 10px; padding-top: 10px; }}
            .header-title h1 {{ font-size: 1rem; }}
            .cover-page .card-title {{ font-size: 0.8rem; }}
            .cover-page .school-name {{ font-size: 1rem; }}
            .info-table {{ font-size: 0.7rem; }}
            .info-table td {{ display: block; width: 100%; padding: 2px 0; }}
            .info-table .label {{ white-space: normal; }}
            .grading-policy h2 {{ font-size: 0.95rem; }}
            .grading-policy .grade-scale {{ font-size: 0.7rem; padding: 6px 8px; }}
            .marks-table {{ font-size: 0.6rem; }}
            .marks-table th {{ font-size: 0.55rem; padding: 3px 2px; }}
            .marks-table td {{ font-size: 0.6rem; padding: 2px 2px; }}
            .comments-section {{ font-size: 0.7rem; }}
            .comments-section .section-title {{ font-size: 0.8rem; }}
        }}
        @media (max-width: 480px) {{
            .card-container {{ padding: 8px 6px; }}
            .cover-page .card-title {{ font-size: 0.7rem; }}
            .header-title h1 {{ font-size: 0.8rem; }}
            .header-logo {{ width: 30px; height: 30px; font-size: 0.7rem; }}
            .header-right {{ font-size: 0.6rem; padding: 2px 8px; }}
        }}
    </style>
</head>
<body>
<div class="card-container">
    <!-- ============================================================ -->
    <!-- PAGE 1                                                       -->
    <!-- ============================================================ -->
    <div class="page">
        <!-- LEFT COLUMN: Grading Policy -->
        <div class="column grading-policy">
            <h2>የማርክ አሰጣጥ ደንብ <span>METHOD OF MARKING</span></h2>
            <div style="background:#f9fbf9; border:1px solid #d4dce8; border-radius:10px; padding:10px 12px; margin-bottom:10px;">
                <p><strong>የማርክ አሰጣጥ ደንብ</strong></p>
                <p>ትምህርት ቤቶች በመዝገብ ውስጥ የሚጽፏቸው የትማሪዎች የትምህርት ደረጃ በሚከተለው ዓይነት ይመደባል፡</p>
                <div class="grade-scale">
                    <div><span class="range">100 – 90%</span> <span class="desc">እጅግ በጣም ጥሩ</span></div>
                    <div><span class="range">89 – 80%</span> <span class="desc">በጣም ጥሩ</span></div>
                    <div><span class="range">79 – 60%</span> <span class="desc">በቂ</span></div>
                    <div><span class="range">59 – 50%</span> <span class="desc">መጠነኛ</span></div>
                    <div><span class="range">50% በታች</span> <span class="desc">ዝቅተኛ</span></div>
                </div>
                <p>ከመቶ ዜሮ (0%) ምን ጊዜም ቢሆን ለተማሪ አይሰጥም፣ ዜሮ መስጠት ፈጽሞ አልተማረም ማለት ነው፡፡ ተማሪ ከክፍሉ ያልተገኘ እንደሆነ አልነበረም ተብሎ "AB" (Absent) ይጻፍበታል፡፡</p>
            </div>
            <div style="background:#f9fbf9; border:1px solid #d4dce8; border-radius:10px; padding:10px 12px;">
                <p><strong>METHOD OF MARKING</strong></p>
                <p>Student's achievement in each class will be assigned the following values:</p>
                <div class="grade-scale" style="border-left-color:#1a365d;">
                    <div><span class="range">100 – 90%</span> <span class="desc">Excellent</span></div>
                    <div><span class="range">89 – 80%</span> <span class="desc">Very good</span></div>
                    <div><span class="range">79 – 60%</span> <span class="desc">Satisfactory</span></div>
                    <div><span class="range">59 – 50%</span> <span class="desc">Fair</span></div>
                    <div><span class="range">50% – Below</span> <span class="desc">Poor</span></div>
                </div>
                <p>Point Zero (0%) should never be given, since it would mean no work has been done absolutely. If a student has been absent from class for the whole period covered, and has not made up of the work, he (she) should be marked "AB" for 'Absent'.</p>
            </div>
        </div>

        <!-- RIGHT COLUMN: Cover Page -->
        <div class="column cover-page">
            <div class="school-name">{school_name}</div>
            <div class="card-title">የተማሪ ውጤት መግለጫ<br>Student Report Card</div>
            <table class="info-table">
                <tr><td class="label">የት/ቤቱ ስም / Name of school:</td><td class="value">{school_name}</td></tr>
                <tr><td class="label">ክልል / Region:</td><td class="value">_________</td><td class="label">ዞን / Zone:</td><td class="value">_________</td></tr>
                <tr><td class="label">ወረዳ / Wereda:</td><td class="value">_________</td><td class="label">ክፍለ ከተማ / Kebele:</td><td class="value">_________</td></tr>
                <tr><td class="label">የተማሪው ስም / Name of student:</td><td class="value">{name}</td></tr>
                <tr><td class="label">ፆታ / Sex:</td><td class="value">{gender}</td><td class="label">ዕድሜ / Age:</td><td class="value">{age}</td></tr>
                <tr><td class="label">አድራሻ / Address:</td><td class="value">{address}</td></tr>
                <tr><td class="label">የትምህርት ዘመን / Academic Year:</td><td class="value">{academic_year}</td></tr>
                <tr><td class="label">ክፍሉ / Grade:</td><td class="value">{grade}</td></tr>
                <tr><td class="label">ክፍል ተዛውሯል/ራለች / Promoted to grade:</td><td class="value">{promoted}</td></tr>
                <tr><td class="label">የት/ቤቱ ርዕሰ መምህር ስም / Director's Name:</td><td class="value">____________________</td></tr>
                <tr><td class="label">ፊርማ / Signature:</td><td class="value">____________________</td></tr>
            </table>
            <div class="motto-box">"ትውልድን የሚተካ ትውልድ በተሻለ ጥራት እናፈራለን"</div>
        </div>
    </div>

    <!-- ============================================================ -->
    <!-- PAGE 2                                                       -->
    <!-- ============================================================ -->
    <div class="page page-break">
        <!-- LEFT COLUMN: Marks Table -->
        <div class="column">
            <table class="marks-table">
                <thead>
                    <tr>
                        <th style="text-align:left;padding-left:8px;">የትምህርት ዓይነት<br>Subject</th>
                        <th>1ኛ ወሰነ-ት/ም<br>1st Sem.</th>
                        <th>2ኛ ወሰነ-ት/ም<br>2nd Sem.</th>
                        <th>አማካይ<br>Avg.</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                    <tr class="total-row">
                        <td class="subject-name">ድምር / Total</td>
                        <td>{total_sem1}</td>
                        <td>{total_sem2}</td>
                        <td>{round((total_sem1 + total_sem2) / 2, 1)}</td>
                    </tr>
                    <tr class="avg-row">
                        <td class="subject-name">አማካይ / Average</td>
                        <td>{avg_sem1}</td>
                        <td>{avg_sem2}</td>
                        <td>{overall_avg}</td>
                    </tr>
                    <tr class="stat-row">
                        <td class="stat-label">የቀረበት ቀን / Absence</td>
                        <td>-</td>
                        <td>{absence}</td>
                        <td>{absence}</td>
                    </tr>
                    <tr class="stat-row">
                        <td class="stat-label">ፀባይ / Conduct</td>
                        <td>{conduct}</td>
                        <td>{conduct}</td>
                        <td>{conduct}</td>
                    </tr>
                    <tr class="stat-row">
                        <td class="stat-label">ደረጃ / Rank</td>
                        <td>{rank}</td>
                        <td>{rank}</td>
                        <td>{rank}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <!-- RIGHT COLUMN: Teacher & Parent Comments -->
        <div class="column comments-section">
            <div class="section-title">የክፍል መምህሩ አስተያየት / Remarks from Home Room Teacher</div>

            <!-- Semester 1 -->
            <div class="semester-block">
                <div class="semester-title">1ኛ ወሰነ-ት/ም / FIRST SEMESTER</div>
                <div><strong>የክፍሉ መምህር አስተያየት / Home Room Teacher Comment:</strong></div>
                <div class="teacher-comment-box">
                    {amh_comment}<br><span style="font-size:0.65rem; color:#555;">{eng_comment}</span>
                </div>
                <div class="comment-line">
                    <span>ስምና ፊርማ / Name &amp; Signature:</span>
                    <span class="line"></span>
                </div>
                <div><strong>የወላጅ ወይም አሳዳጊ አስተያየት / Parent or Guardian Recommendation:</strong></div>
                <div style="min-height:20px; border-bottom:1px dashed #aaa; margin:4px 0 6px 0;"></div>
                <div class="comment-line">
                    <span>የወላጅ ወይም አሳዳጊ ፊርማ / Signature:</span>
                    <span class="line"></span>
                </div>
            </div>

            <!-- Semester 2 -->
            <div class="semester-block">
                <div class="semester-title">ሁለተኛ መንፈቅ ዓመት / SECOND SEMESTER</div>
                <div><strong>የክፍሉ መምህር አስተያየት / Home Room Teacher Comment:</strong></div>
                <div class="teacher-comment-box">
                    {amh_comment}<br><span style="font-size:0.65rem; color:#555;">{eng_comment}</span>
                </div>
                <div class="comment-line">
                    <span>ስምና ፊርማ / Name &amp; Signature:</span>
                    <span class="line"></span>
                </div>
                <div><strong>የወላጅ ወይም አሳዳጊ አስተያየት / Parent or Guardian Recommendation:</strong></div>
                <div style="min-height:20px; border-bottom:1px dashed #aaa; margin:4px 0 6px 0;"></div>
                <div class="comment-line">
                    <span>የወላጅ ወይም አሳዳጊ ፊርማ / Signature:</span>
                    <span class="line"></span>
                </div>
            </div>

            <!-- Director's signature -->
            <div class="director-sign">
                <span><strong>የርዕሰ መምህሩ ፊርማ / Director's Signature:</strong></span>
                <span class="line"></span>
            </div>
        </div>
    </div>
</div>
</body>
</html>
"""
    return html

# ---- show_student_card_panel ----
def show_student_card_panel():
    st.markdown("### 🎓 Student Report Cards")
    st.markdown("Generate a two‑page landscape report card matching the official Ethiopian school format.")
    st.info("📄 Download the HTML file, open it in a browser, and use **Print → Save as PDF** to get a PDF card.")

    col1, col2, col3 = st.columns(3)
    with col1:
        grade_options = ["All"] + [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, index=0)
    with col2:
        if selected_grade != "All":
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            sections = sorted(set([s.get("section", "A") for s in students_in_grade]))
            if not sections:
                sections = ["A"]
            section_options = ["All"] + sections
            selected_section = st.selectbox("Select Section", section_options, index=0)
        else:
            selected_section = "All"
    with col3:
        semester_options = ["Semester I", "Semester II", "Semester III"]
        selected_semester = st.selectbox("Semester", semester_options, index=2)

    filtered_students = st.session_state.students
    if selected_grade != "All":
        filtered_students = [s for s in filtered_students if s.get("grade") == selected_grade]
    if selected_section != "All":
        filtered_students = [s for s in filtered_students if s.get("section") == selected_section]

    if not filtered_students:
        st.info("No students match the selection.")
        return

    st.markdown(f"**{len(filtered_students)} students found**")

    for student in filtered_students:
        with st.expander(f"📄 {student['name']} - {student.get('grade', '')} {student.get('section', '')}"):
            html = generate_student_card(student, selected_semester)
            st.download_button(
                label=f"📥 Download HTML Card for {student['name']}",
                data=html.encode('utf-8'),
                file_name=f"Student_Card_{student['name']}_{selected_semester}.html",
                mime="text/html",
                key=f"download_{student['id']}"
            )
            st.markdown("#### Preview")
            # ✅ Use st.components.v1.html (works reliably)
            st.components.v1.html(html, height=800, scrolling=True)
            
# ===================================================================
# ADMIN PANEL (complete)
# ===================================================================

def show_admin_panel():
    st.markdown("### 👨‍💼 Admin Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14 = st.tabs([
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
        "⚠️ Penalty Log",
        "🏫 Settings",
        "👨‍🏫 Homeroom",
        "🎓 Student Cards"
    ])

    # --- Tab 1: Overview ---
    with tab1:
        st.markdown("#### Dashboard Overview")
        pending_batches = len(get_batches_awaiting_final_approval())  # Use new function
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

        if pending_batches == 0:
            st.balloons()
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
                        padding: 2rem;
                        border-radius: 20px;
                        text-align: center;
                        border: 3px solid #FFD700;
                        margin: 1rem 0;">
                <div style="font-size: 4.5rem;">🏆🎓📚🌟👏</div>
                <h2 style="color: #1a365d;">All Batches Approved!</h2>
                <p style="font-size: 1.3rem; color: #2d4059;">
                    Every evaluation has been reviewed and approved. <br>🎯 Outstanding work, Admin!
                </p>
                <p style="font-size: 1rem; color: #4a5b7a;">📖 You're shaping the future of education! 📖</p>
            </div>
            """, unsafe_allow_html=True)

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
        if st.button("📅 Update Registration Period", width='stretch'):
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

    # --- Tab 3: Teachers ---
    with tab3:
        st.markdown("#### 👨‍🏫 Manage Teachers")

        # ---- Assignment management (outside the form) ----
        st.markdown("##### 📌 Assignments (Grade, Section & Semester)")
        st.caption("Add the grade(s), section(s), and semester(s) this teacher is responsible for.")
        if "assignments_list" not in st.session_state:
            st.session_state.assignments_list = [{"grade": "Grade 1", "section": "A", "semester": "Semester I"}]

        for i, assignment in enumerate(st.session_state.assignments_list):
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
            with col1:
                grade_options = [f"Grade {g}" for g in range(1, 13)]
                try:
                    idx = grade_options.index(assignment["grade"])
                except ValueError:
                    idx = 0
                    assignment["grade"] = grade_options[0]
                assignment["grade"] = st.selectbox(
                    "Grade",
                    grade_options,
                    index=idx,
                    key=f"assign_grade_{i}"
                )
            with col2:
                assignment["section"] = st.text_input(
                    "Section",
                    value=assignment["section"],
                    key=f"assign_section_{i}"
                )
            with col3:
                semester_options = ["Semester I", "Semester II"]
                try:
                    sem_idx = semester_options.index(assignment["semester"])
                except ValueError:
                    sem_idx = 0
                    assignment["semester"] = semester_options[0]
                assignment["semester"] = st.selectbox(
                    "Semester",
                    semester_options,
                    index=sem_idx,
                    key=f"assign_semester_{i}"
                )
            with col4:
                if st.button("✖", key=f"remove_assign_{i}", width='stretch'):
                    if len(st.session_state.assignments_list) > 1:
                        st.session_state.assignments_list.pop(i)
                        st.rerun()
        if st.button("➕ Add Assignment", width='stretch'):
            st.session_state.assignments_list.append({"grade": "Grade 1", "section": "A", "semester": "Semester I"})
            st.rerun()

        # ---- Add Teacher Form ----
        with st.form("add_teacher"):
            teacher_name = st.text_input("Teacher Full Name *", placeholder="e.g., Abebe Kebede")
            teacher_subject = st.selectbox("Subject Taught *", st.session_state.subjects if st.session_state.subjects else ALL_SUBJECTS)
            teacher_email = st.text_input("Email Address", placeholder="teacher@school.edu")
            # NEW: Subject Admin assignment
            teacher_admin_subjects = st.multiselect(
                "Subjects this teacher administers (leave empty for regular teacher)",
                options=ALL_SUBJECTS,
                default=[]
            )

            col1, col2 = st.columns([1, 3])
            with col1:
                submitted = st.form_submit_button("➕ Add Teacher", width='stretch')

            if submitted and teacher_name:
                base_username = generate_username(teacher_name)
                username = base_username
                counter = 1
                while is_username_taken(username):
                    username = f"{base_username}{counter}"
                    counter += 1

                password = generate_random_password()
                hashed_pw = hash_password(password)

                existing_ids = [int(t['id'][1:]) for t in st.session_state.teachers if t['id'].startswith('T')]
                next_num = max(existing_ids) + 1 if existing_ids else 1
                teacher_id = f"T{next_num:04d}"
                added_time = datetime.now().strftime("%Y-%m-%d %H:%M")
                assignments_json = json.dumps(st.session_state.assignments_list)
                admin_subjects_json = json.dumps(teacher_admin_subjects)

                # Determine role: if admin_subjects non-empty, role = subject_admin else teacher
                role = "subject_admin" if teacher_admin_subjects else "teacher"

                supabase_admin = get_supabase_admin()
                try:
                    user_data = {
                        "username": username,
                        "password": hashed_pw,
                        "role": role,
                        "name": teacher_name
                    }
                    supabase_admin.table("users").insert(user_data).execute()
                    teacher_data = {
                        "id": teacher_id,
                        "name": teacher_name,
                        "subject": teacher_subject,
                        "email": teacher_email,
                        "username": username,
                        "password": password,
                        "added": added_time,
                        "assignments": assignments_json,
                        "admin_subjects": admin_subjects_json
                    }
                    supabase_admin.table("teachers").insert(teacher_data).execute()
                    load_all_data()
                    add_notification(f"👨‍🏫 New teacher added: {teacher_name} (role: {role})", "success")
                    st.success(f"""
                    ✅ Teacher {teacher_name} added successfully!
                    **Login Credentials:**
                    - **Username:** `{username}`
                    - **Password:** `{password}`
                    - **Role:** {role.title()}
                    """)
                    st.session_state.assignments_list = [{"grade": "Grade 1", "section": "A", "semester": "Semester I"}]
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error adding teacher: {e}")
            elif submitted:
                st.error("❌ Please enter teacher name.")

        st.markdown("---")
        if st.session_state.teachers:
            st.markdown("#### 📋 All Teachers")
            for teacher in st.session_state.teachers:
                assignments = json.loads(teacher.get("assignments", "[]"))
                assign_str = ", ".join([f"{a['grade']} ({a['section']}) - {a.get('semester', '')}" for a in assignments]) if assignments else "None"
                admin_subjects = json.loads(teacher.get("admin_subjects", "[]"))
                admin_str = ", ".join(admin_subjects) if admin_subjects else "None"
                # Get password - show if exists
                teacher_password = teacher.get('password', 'N/A')
                st.markdown(f"""
                <div class="teacher-card">
                    <h4>👨‍🏫 {teacher['name']}</h4>
                    <p><b>📚 Subject:</b> {teacher['subject']}</p>
                    <p><b>📌 Assignments:</b> {assign_str}</p>
                    <p><b>🔐 Admin Subjects:</b> {admin_str}</p>
                    <p><b>✉️ Email:</b> {teacher.get('email', 'N/A')}</p>
                    <p><b>👤 Username:</b> <code>{teacher.get('username', 'N/A')}</code></p>
                    <p><b>📅 Added:</b> {teacher.get('added', 'N/A')}</p>
                    <p><b>🔑 Password:</b> <code style="background:#FCE8E6;padding:2px 10px;border-radius:4px;color:#EA4335;font-weight:700;">{teacher_password}</code></p>
                </div>
                """, unsafe_allow_html=True)

            # ---------- EDIT TEACHER ----------
            st.markdown("#### ✏️ Edit Teacher")
            teacher_options = {f"{t['name']} ({t['id']})": t for t in st.session_state.teachers}
            selected_teacher_label = st.selectbox("Select teacher to edit", options=list(teacher_options.keys()))
            if selected_teacher_label:
                teacher = teacher_options[selected_teacher_label]
                with st.expander("Edit this teacher", expanded=True):
                    st.markdown("##### 📌 Edit Assignments")
                    current_assignments = json.loads(teacher.get("assignments", "[]"))
                    if "edit_assignments" not in st.session_state:
                        st.session_state.edit_assignments = current_assignments if current_assignments else [{"grade": "Grade 1", "section": "A", "semester": "Semester I"}]

                    for i, ass in enumerate(st.session_state.edit_assignments):
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                        with col1:
                            grade_options = [f"Grade {g}" for g in range(1, 13)]
                            try:
                                idx = grade_options.index(ass["grade"])
                            except ValueError:
                                idx = 0
                                ass["grade"] = grade_options[0]
                            ass["grade"] = st.selectbox(
                                "Grade",
                                grade_options,
                                index=idx,
                                key=f"edit_assign_grade_{i}"
                            )
                        with col2:
                            ass["section"] = st.text_input(f"Section", value=ass["section"], key=f"edit_assign_section_{i}")
                        with col3:
                            semester_options = ["Semester I", "Semester II"]
                            try:
                                sem_idx = semester_options.index(ass["semester"])
                            except ValueError:
                                sem_idx = 0
                                ass["semester"] = semester_options[0]
                            ass["semester"] = st.selectbox(
                                "Semester",
                                semester_options,
                                index=sem_idx,
                                key=f"edit_assign_semester_{i}"
                            )
                        with col4:
                            if st.button("✖", key=f"edit_remove_assign_{i}", width='stretch'):
                                if len(st.session_state.edit_assignments) > 1:
                                    st.session_state.edit_assignments.pop(i)
                                    st.rerun()
                    if st.button("➕ Add Assignment", key="edit_add_assign", width='stretch'):
                        st.session_state.edit_assignments.append({"grade": "Grade 1", "section": "A", "semester": "Semester I"})
                        st.rerun()

                    # Admin Subjects
                    current_admin_subjects = json.loads(teacher.get("admin_subjects", "[]"))
                    new_admin_subjects = st.multiselect(
                        "Subjects this teacher administers",
                        options=ALL_SUBJECTS,
                        default=current_admin_subjects
                    )

                    with st.form("edit_teacher_form"):
                        new_name = st.text_input("Teacher Full Name", value=teacher["name"])
                        new_subject = st.selectbox("Subject", st.session_state.subjects,
                                                   index=st.session_state.subjects.index(teacher["subject"]) if teacher["subject"] in st.session_state.subjects else 0)
                        new_email = st.text_input("Email Address", value=teacher.get("email", ""))

                        if st.form_submit_button("💾 Update Teacher", width='stretch'):
                            teacher["name"] = new_name
                            teacher["subject"] = new_subject
                            teacher["email"] = new_email
                            teacher["assignments"] = json.dumps(st.session_state.edit_assignments)
                            teacher["admin_subjects"] = json.dumps(new_admin_subjects)
                            # Update user role
                            new_role = "subject_admin" if new_admin_subjects else "teacher"
                            supabase_admin = get_supabase_admin()
                            try:
                                supabase_admin.table("teachers").update(teacher).eq("id", teacher["id"]).execute()
                                if teacher.get("username") in st.session_state.user_db:
                                    st.session_state.user_db[teacher["username"]]["name"] = new_name
                                    st.session_state.user_db[teacher["username"]]["role"] = new_role
                                    supabase_admin.table("users").update({"name": new_name, "role": new_role}).eq("username", teacher["username"]).execute()
                                load_all_data()
                                add_notification(f"✏️ Teacher {new_name} updated", "info")
                                st.success(f"✅ Teacher {new_name} updated successfully!")
                                st.session_state.edit_assignments = json.loads(teacher.get("assignments", "[]")) if teacher.get("assignments") else [{"grade":"Grade 1","section":"A","semester":"Semester I"}]
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to update teacher: {e}")

            st.markdown("---")
            st.markdown("#### 🗑️ Delete Teacher")
            teacher_to_delete = st.selectbox(
                "Select teacher to delete",
                options=[f"{t['name']} ({t['id']})" for t in st.session_state.teachers]
            )
            if teacher_to_delete:
                teacher_id = teacher_to_delete.split("(")[-1].replace(")", "")
                if st.button("Delete this teacher", type="primary", width='stretch'):
                    try:
                        supabase_admin = get_supabase_admin()
                        username_to_remove = None
                        for t in st.session_state.teachers:
                            if t["id"] == teacher_id:
                                username_to_remove = t.get("username")
                                break
                        if not username_to_remove:
                            st.error("Username not found for this teacher.")
                            st.stop()
                        supabase_admin.table("evaluations").delete().eq("teacher_id", teacher_id).execute()
                        supabase_admin.table("batches").delete().eq("teacher_id", teacher_id).execute()
                        supabase_admin.table("teachers").delete().eq("id", teacher_id).execute()
                        supabase_admin.table("users").delete().eq("username", username_to_remove).execute()
                        load_all_data()
                        add_notification(f"🗑️ Teacher {teacher_to_delete} deleted permanently", "warning")
                        st.success(f"✅ Teacher {teacher_to_delete} deleted successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error deleting teacher: {e}")
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
                submitted = st.form_submit_button("➕ Add Subject", width='stretch')
            if submitted and new_subject:
                if new_subject not in current_subjects:
                    st.session_state.subjects.append(new_subject)
                    add_notification(f"📚 New subject added: {new_subject}", "info")
                    st.success(f"✅ Subject {new_subject} added!")
                    st.rerun()
                else:
                    st.warning(f"⚠️ Subject '{new_subject}' already exists.")

    # --- Tab 5: All Data ---
    with tab5:
        st.markdown("#### 📋 All Data")

        st.markdown("##### 👨‍🎓 Students by Grade")
        grade_options = ["All Grades"] + [f"Grade {i}" for i in range(1, 13)]
        selected_grade_filter = st.selectbox(
            "Filter by Grade",
            options=grade_options,
            index=0,
            key="all_data_grade_filter"
        )
        if selected_grade_filter == "All Grades":
            filtered_students = st.session_state.students
            heading = "👨‍🎓 All Students"
        else:
            filtered_students = [s for s in st.session_state.students if s.get("grade") == selected_grade_filter]
            heading = f"👨‍🎓 {selected_grade_filter} Students"
        st.markdown(f"##### {heading}")
        if filtered_students:
            df_students = pd.DataFrame(filtered_students)
            df_students["Grade Display"] = df_students["grade"].apply(get_grade_display)
            st.dataframe(df_students, use_container_width=True)
        else:
            st.info(f"No students registered in {selected_grade_filter}.")

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
        if st.button("📥 Export All Data (JSON)", width='stretch'):
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
                width='stretch'
            )

        st.markdown("##### ⚠️ Danger Zone")
        if st.button("🗑️ Clear All Data (Admin Only)", width='stretch'):
            if st.checkbox("I confirm I want to delete ALL data (students, teachers, evaluations, batches, penalties)"):
                st.session_state.students = []
                st.session_state.teachers = []
                st.session_state.evaluations = []
                st.session_state.batches = []
                st.session_state.penalty_log = []
                sync_all()
                add_notification(f"🗑️ All data cleared by admin", "warning")
                st.warning("All data has been cleared.")
                st.rerun()

    # --- Tab 6: Approvals (Batches) ---
    with tab6:
        st.markdown("#### ✅ Pending Batches for Final Approval")
        pending_batches = get_batches_awaiting_final_approval()  # subject-approved or no subject admin
        if not pending_batches:
            st.success("🎉 No pending batches awaiting final approval.")
        else:
            st.markdown(f"**{len(pending_batches)} batch(es) awaiting your final review**")
            for batch in pending_batches:
                batch_id = batch["id"]
                teacher_name = batch.get("teacher_name", "Unknown")
                subject = batch.get("subject", "N/A")
                grade = batch.get("grade", "N/A")
                section = batch.get("section", "N/A")
                semester = batch.get("semester", "N/A")
                student_count = len(batch.get("students", []))
                submitted_date = batch.get("submitted_at", "N/A")
                batch_remarks = batch.get("remarks", "")
                weights = batch.get("weights", {})
                max_scores = batch.get("max_scores", DEFAULT_MAX_SCORES)
                weight_str = f"Test1={weights.get('Test 1',0)}, Test2={weights.get('Test 2',0)}, Test3={weights.get('Test 3',0)}, Test4={weights.get('Test 4',0)}, Final={weights.get('Final Exam',0)}"
                max_str = f"Max: Test1={max_scores.get('Test 1',0)}, Test2={max_scores.get('Test 2',0)}, Test3={max_scores.get('Test 3',0)}, Test4={max_scores.get('Test 4',0)}, Final={max_scores.get('Final Exam',0)}"
                # Indicate if subject-admin approved
                if batch.get("status") == "subject_approved":
                    approval_note = "✅ Approved by Subject Admin"
                else:
                    approval_note = "⏳ No Subject Admin assigned"

                st.markdown(f"""
                <div class="approval-card pending">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4 style="color:#1A73E8;font-size:1.8rem;margin:0 0 0.5rem 0;">📦 Batch from {teacher_name} · {subject}</h4>
                            <p><b>📚 Subject:</b> {subject}</p>
                            <p><b>📋 Grade:</b> {grade}</p>
                            <p><b>📌 Section:</b> {section}</p>
                            <p><b>📌 Semester:</b> {semester}</p>
                            <p><b>👥 Students:</b> {student_count}</p>
                            <p><b>📅 Submitted:</b> {submitted_date}</p>
                            <p><b>Weights:</b> {weight_str}</p>
                            <p><b>Max Scores:</b> {max_str}</p>
                            <p><b>Batch Remarks:</b> {batch_remarks if batch_remarks else 'None'}</p>
                            <p><b>Status:</b> {approval_note}</p>
                        </div>
                        <div style="text-align:right;">
                            <span class="badge-pending">⏳ Pending Final Approval</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                df_batch = pd.DataFrame(batch["students"])
                display_cols = ["student_name", "Test 1", "Test 2", "Test 3", "Test 4", "Final Exam", "overall"]
                available_cols = [col for col in display_cols if col in df_batch.columns]
                st.dataframe(df_batch[available_cols], use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve Final", key=f"final_approve_{batch_id}", width='stretch'):
                        supabase_admin = get_supabase_admin()
                        try:
                            res = supabase_admin.table("evaluations").select("id").order("id", desc=True).limit(1).execute()
                            if res.data and res.data[0].get("id"):
                                last_id = res.data[0]["id"]
                                num = int(last_id[1:]) + 1
                            else:
                                num = len(st.session_state.evaluations) + 1
                        except:
                            num = len(st.session_state.evaluations) + 1

                        for student_entry in batch["students"]:
                            eval_item = {
                                "id": f"E{num:04d}",
                                "student_id": student_entry["student_id"],
                                "student_name": student_entry["student_name"],
                                "teacher_id": batch["teacher_id"],
                                "teacher_name": batch["teacher_name"],
                                "subject": batch["subject"],
                                "semester": semester,
                                "assessments": [
                                    {"name": "Test 1", "score": student_entry["Test 1"], "weight": batch["weights"]["Test 1"], "max_score": batch["max_scores"]["Test 1"]},
                                    {"name": "Test 2", "score": student_entry["Test 2"], "weight": batch["weights"]["Test 2"], "max_score": batch["max_scores"]["Test 2"]},
                                    {"name": "Test 3", "score": student_entry["Test 3"], "weight": batch["weights"]["Test 3"], "max_score": batch["max_scores"]["Test 3"]},
                                    {"name": "Test 4", "score": student_entry["Test 4"], "weight": batch["weights"]["Test 4"], "max_score": batch["max_scores"]["Test 4"]},
                                    {"name": "Final Exam", "score": student_entry["Final Exam"], "weight": batch["weights"]["Final Exam"], "max_score": batch["max_scores"]["Final Exam"]}
                                ],
                                "remarks": batch_remarks,
                                "overall_score": student_entry["overall"],
                                "status": "approved",
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "batch_id": batch_id
                            }
                            try:
                                supabase_admin.table("evaluations").insert(eval_item).execute()
                            except Exception as e:
                                st.error(f"Failed to save evaluation for {student_entry['student_name']}: {e}")
                            st.session_state.evaluations.append(eval_item)
                            num += 1

                        batch["status"] = "approved"
                        try:
                            supabase_admin.table("batches").update({"status": "approved"}).eq("id", batch_id).execute()
                            load_all_data()
                            add_notification(f"✅ Batch from {teacher_name} finally approved ({student_count} students)", "success")
                            # Celebration
                            st.balloons()
                            st.markdown(f"""
                            <div style="background: linear-gradient(135deg, #fff9e6 0%, #fff3cd 100%);
                                        padding: 2.5rem;
                                        border-radius: 20px;
                                        text-align: center;
                                        border: 4px solid #FFD700;
                                        margin: 1.5rem 0;
                                        box-shadow: 0 12px 48px rgba(255, 215, 0, 0.35);">
                                <div style="font-size: 5rem; line-height: 1.3;">🎓🏆🌟✨📜</div>
                                <h2 style="color: #1a365d; font-size: 2.2rem; margin: 0.5rem 0;">✅ Batch Approved!</h2>
                                <p style="font-size: 1.4rem; color: #2d4059; font-weight: 600;">
                                    <strong>{student_count}</strong> student evaluations created successfully!
                                </p>
                                <p style="font-size: 1.1rem; color: #4a5b7a; margin-top: 0.5rem;">
                                    📚 Every approved evaluation builds a brighter future! Keep leading the way! 🎓
                                </p>
                            </div>
                            """, unsafe_allow_html=True)
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to approve batch: {e}")
                with col2:
                    if st.button(f"❌ Reject Final", key=f"final_reject_{batch_id}", width='stretch'):
                        batch["status"] = "rejected"
                        supabase_admin = get_supabase_admin()
                        try:
                            supabase_admin.table("batches").update({"status": "rejected"}).eq("id", batch_id).execute()
                            load_all_data()
                            add_notification(f"❌ Batch from {teacher_name} rejected", "warning")
                            st.warning("❌ Batch rejected!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to reject batch: {e}")
                st.markdown("---")

    # --- Tab 7: Rankings ---
    with tab7:
        st.markdown("#### 📊 Grade Rankings by Section")

        grade_options = [f"Grade {i}" for i in range(1, 13)]
        col1, col2 = st.columns(2)
        with col1:
            selected_grade = st.selectbox("Select Grade", grade_options, index=0, key="rank_grade")
        with col2:
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            sections = sorted(set([s.get("section", "A") for s in students_in_grade]))
            if not sections:
                sections = ["A"]
            section_options = ["All"] + sections
            selected_section = st.selectbox("Select Section", section_options, index=0, key="rank_section")

        if selected_section == "All":
            students_in_grade_section = students_in_grade
        else:
            students_in_grade_section = [s for s in students_in_grade if s.get("section") == selected_section]

        if not students_in_grade_section:
            st.info(f"No students registered in {selected_grade} ({selected_section}) yet.")
        else:
            student_data = []
            for student in students_in_grade_section:
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
                st.info("No approved evaluations yet for this grade and section.")

    # --- Tab 8: Students ---
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
                    section = st.text_input("Section (e.g., A, B, C)", value="A")
                    subjects = GRADE_SUBJECTS.get(grade, [])
                    st.info(f"📚 Subjects for {grade}: {', '.join(subjects)}")
                submitted = st.form_submit_button("Add Student", width='stretch')
                if submitted:
                    if not name:
                        st.error("Name is required.")
                    else:
                        existing_ids = [int(s['id'][1:]) for s in st.session_state.students if s['id'].startswith('S')]
                        next_num = max(existing_ids) + 1 if existing_ids else 1
                        student_id = f"S{next_num:04d}"
                        new_student = {
                            "id": student_id,
                            "name": name,
                            "age": age,
                            "gender": gender,
                            "grade": grade,
                            "section": section,
                            "semester": semester,
                            "subjects": subjects,
                            "parent_name": parent,
                            "contact": contact,
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "evaluations_count": 0
                        }
                        supabase_admin = get_supabase_admin()
                        try:
                            supabase_admin.table("students").insert(new_student).execute()
                            load_all_data()
                            add_notification(f"👨‍🎓 Student {name} added manually", "success")
                            st.success(f"✅ Student {name} added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add student: {e}")

        st.markdown("#### 📋 All Students")
        if st.session_state.students:
            df = pd.DataFrame(st.session_state.students)
            display_cols = ["id", "name", "grade", "section", "semester", "subjects"]
            st.dataframe(df[display_cols], use_container_width=True)

            # Edit Student
            st.markdown("#### ✏️ Edit Student")
            student_options = {f"{s['name']} ({s['id']})": s for s in st.session_state.students}
            selected_student_label = st.selectbox("Select student to edit", options=list(student_options.keys()))
            if selected_student_label:
                student = student_options[selected_student_label]
                with st.expander("Edit this student", expanded=True):
                    with st.form("edit_student_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            new_name = st.text_input("Full Name", value=student["name"])
                            age_val = student.get("age") or 5
                            try:
                                age_val = int(age_val)
                            except:
                                age_val = 5
                            new_age = st.number_input("Age", min_value=5, max_value=25, step=1, value=age_val)
                            grade_idx = [f"Grade {i}" for i in range(1,13)].index(student["grade"]) if student["grade"] in [f"Grade {i}" for i in range(1,13)] else 0
                            new_grade = st.selectbox("Grade", [f"Grade {i}" for i in range(1,13)], index=grade_idx)
                            new_semester = st.selectbox("Semester", ["Semester I", "Semester II"],
                                                        index=["Semester I", "Semester II"].index(student["semester"]) if student["semester"] in ["Semester I", "Semester II"] else 0)
                        with col2:
                            gender_idx = ["M","F","Other"].index(student.get("gender","M")) if student.get("gender","M") in ["M","F","Other"] else 0
                            new_gender = st.selectbox("Gender", ["M","F","Other"], index=gender_idx)
                            new_parent = st.text_input("Parent/Guardian", value=student.get("parent_name",""))
                            new_contact = st.text_input("Contact", value=student.get("contact",""))
                            new_section = st.text_input("Section", value=student.get("section","A"))
                            new_subjects = GRADE_SUBJECTS.get(new_grade, [])
                            st.info(f"📚 Subjects for {new_grade}: {', '.join(new_subjects)}")
                        if st.form_submit_button("💾 Update Student", width='stretch'):
                            student["name"] = new_name
                            student["age"] = new_age
                            student["grade"] = new_grade
                            student["section"] = new_section
                            student["semester"] = new_semester
                            student["gender"] = new_gender
                            student["parent_name"] = new_parent
                            student["contact"] = new_contact
                            student["subjects"] = new_subjects
                            supabase_admin = get_supabase_admin()
                            try:
                                supabase_admin.table("students").update(student).eq("id", student["id"]).execute()
                                load_all_data()
                                add_notification(f"✏️ Student {new_name} updated", "info")
                                st.success(f"✅ Student {new_name} updated successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Failed to update student: {e}")

            # Delete Student
            st.markdown("#### 🗑️ Delete Student")
            student_to_delete = st.selectbox(
                "Select student to delete",
                options=[f"{s['name']} ({s['id']})" for s in st.session_state.students],
                key="delete_student"
            )
            if student_to_delete:
                student_id = student_to_delete.split("(")[-1].replace(")", "")
                if st.button("Delete Selected Student", type="primary", width='stretch'):
                    if st.checkbox(f"⚠️ Confirm delete of {student_to_delete}?"):
                        supabase_admin = get_supabase_admin()
                        try:
                            supabase_admin.table("students").delete().eq("id", student_id).execute()
                            supabase_admin.table("evaluations").delete().eq("student_id", student_id).execute()
                            load_all_data()
                            add_notification(f"🗑️ Student {student_to_delete} deleted", "warning")
                            st.success(f"✅ Deleted {student_to_delete}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to delete student: {e}")
        else:
            st.info("No students registered yet.")

    # --- Tab 9: Import/Export ---
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

                supabase = get_supabase_admin()

                try:
                    res = supabase.table("students").select("id").execute()
                    existing_ids = [int(r['id'][1:]) for r in res.data if r['id'].startswith('S')]
                    next_num = max(existing_ids) + 1 if existing_ids else 1
                except Exception as e:
                    st.error(f"Could not fetch existing student IDs: {e}")
                    st.stop()

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
                        if grade in GRADE_SUBJECTS:
                            subjects = GRADE_SUBJECTS[grade]
                        else:
                            subjects = [clean_nan_value(s) for s in subject_cols if s in sheet_df.columns]

                        student_id = f"S{next_num:04d}"
                        next_num += 1

                        student = {
                            "id": student_id,
                            "name": clean_nan_value(name),
                            "grade": clean_nan_value(grade),
                            "section": clean_nan_value(row.get("ክፍል", "A")),
                            "semester": clean_nan_value(row.get("ሴሚስተር", "I")),
                            "subjects": subjects,
                            "age": clean_nan_value(row.get("እድሜ", 0)),
                            "gender": clean_nan_value(row.get("ፆታ", "")),
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "evaluations_count": 0
                        }
                        try:
                            supabase.table("students").insert(student).execute()
                            st.session_state.students.append(student)
                            total_added += 1
                        except Exception as e:
                            st.warning(f"Failed to insert student {student['name']}: {e}")

                load_all_data()
                st.success(f"✅ Imported {total_added} students from {len(df_sheets)} sheets.")
                add_notification(f"📥 Imported {total_added} students via Excel", "info")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

        st.markdown("#### 📤 Export All Data")
        if st.button("📥 Export Students to Excel", width='stretch'):
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
                    width='stretch'
                )
            else:
                st.warning("No students to export.")

    # --- Tab 10: Comprehensive Approval Report ---
    with tab10:
        st.markdown("### 📊 Comprehensive Grade Report (Subject-wise)")

        grade_options = [f"Grade {i}" for i in range(1, 13)]
        col1, col2 = st.columns(2)
        with col1:
            selected_grade = st.selectbox("Select Grade", grade_options, key="report_grade")
        with col2:
            students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
            sections = sorted(set([s.get("section", "A") for s in students_in_grade]))
            if not sections:
                sections = ["A"]
            section_options = ["All"] + sections
            selected_section = st.selectbox("Select Section", section_options, key="report_section")

        if selected_section == "All":
            students_in_grade_section = students_in_grade
        else:
            students_in_grade_section = [s for s in students_in_grade if s.get("section") == selected_section]

        if not students_in_grade_section:
            st.info(f"No students registered in {selected_grade} ({selected_section}).")
        else:
            student_ids = [s["id"] for s in students_in_grade_section]
            approved_evals = [e for e in st.session_state.evaluations
                              if e.get("student_id") in student_ids and e.get("status") == "approved"]
            if not approved_evals:
                st.info("No approved evaluations found for this grade and section.")
            else:
                student_subject_scores = {}
                for eval_item in approved_evals:
                    sid = eval_item["student_id"]
                    subject = eval_item["subject"]
                    score = eval_item.get("overall_score", 0)
                    student_subject_scores.setdefault(sid, {}).setdefault(subject, []).append(score)
                all_subjects = set()
                for s_scores in student_subject_scores.values():
                    all_subjects.update(s_scores.keys())
                all_subjects = sorted(list(all_subjects))
                report_data = []
                for student in students_in_grade_section:
                    sid = student["id"]
                    name = student["name"]
                    scores_by_subject = student_subject_scores.get(sid, {})
                    row = {"Student ID": sid, "Name": name, "Section": student.get("section", "A")}
                    subject_scores = []
                    for subj in all_subjects:
                        scores = scores_by_subject.get(subj, [])
                        avg_score = round(sum(scores) / len(scores), 2) if scores else 0
                        row[subj] = avg_score
                        subject_scores.append(avg_score)
                    valid_scores = [s for s in subject_scores if s > 0]
                    overall = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0
                    row["Overall Average (%)"] = overall
                    row["Evaluations"] = len(scores_by_subject)
                    report_data.append(row)
                df_report = pd.DataFrame(report_data)
                df_sorted = df_report.sort_values("Overall Average (%)", ascending=False).reset_index(drop=True)
                df_sorted["Rank"] = df_sorted["Overall Average (%)"].rank(method="min", ascending=False).astype(int)
                columns_order = ["Rank", "Student ID", "Name", "Section"] + all_subjects + ["Overall Average (%)", "Evaluations"]
                columns_order = [col for col in columns_order if col in df_sorted.columns]
                df_final = df_sorted[columns_order]
                st.dataframe(df_final, use_container_width=True, hide_index=True)
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, sheet_name=f"{selected_grade}_{selected_section}_Report", index=False)
                st.download_button(
                    label="📥 Download Grade Report (Excel)",
                    data=output.getvalue(),
                    file_name=f"Grade_Report_{selected_grade}_{selected_section}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )

        st.markdown("---")
        st.markdown("#### 📤 Download All Approved Evaluations")
        if st.session_state.evaluations:
            approved_evals = [e for e in st.session_state.evaluations if e.get("status") == "approved"]
            if approved_evals:
                if st.button("📥 Download All Approved Evaluations (Excel)", width='stretch'):
                    rows = []
                    for e in approved_evals:
                        student = get_student_by_id(e.get("student_id"))
                        grade = student.get("grade", "N/A") if student else "N/A"
                        assessments = e.get("assessments", [])
                        scores = {a["name"]: a["score"] for a in assessments}
                        row = {
                            "Student ID": e.get("student_id"),
                            "Student Name": e.get("student_name"),
                            "Grade": grade,
                            "Subject": e.get("subject"),
                            "Teacher": e.get("teacher_name"),
                            "Overall Score (%)": e.get("overall_score"),
                            "Remarks": e.get("remarks", ""),
                            "Date Approved": e.get("date", ""),
                            "Test 1": scores.get("Test 1", ""),
                            "Test 2": scores.get("Test 2", ""),
                            "Test 3": scores.get("Test 3", ""),
                            "Test 4": scores.get("Test 4", ""),
                            "Final Exam": scores.get("Final Exam", "")
                        }
                        rows.append(row)
                    df_export = pd.DataFrame(rows)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_export.to_excel(writer, sheet_name="Approved Evaluations", index=False)
                    st.download_button(
                        label="📥 Download Excel",
                        data=output.getvalue(),
                        file_name=f"approved_evaluations_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        width='stretch'
                    )
            else:
                st.info("No approved evaluations yet.")
        else:
            st.info("No evaluations found.")

    # --- Tab 11: Penalty Log ---
    with tab11:
        show_penalty_log()

    # --- Tab 12: Settings ---
    with tab12:
        st.markdown("### 🏫 School Settings")
        st.markdown("Update school name, city, and director's name that will appear on student report cards.")
        new_name = st.text_input("School Name", value=st.session_state.school_name)
        new_city = st.text_input("City/Town", value=st.session_state.school_city)
        new_director = st.text_input("Director's Name", value=st.session_state.director_name)
        if st.button("💾 Update School Settings", width='stretch'):
            st.session_state.school_name = new_name
            st.session_state.school_city = new_city
            st.session_state.director_name = new_director
            st.success("✅ School settings updated!")
            st.info("📌 **Note:** The School Name and Director's Name you just set will be dynamically applied to every Student Report Card generated.")

    # --- Tab 13: Homeroom Assignments ---
    with tab13:
        st.markdown("### 👨‍🏫 Homeroom Teacher Assignments")
        st.markdown("Assign a homeroom teacher to each grade and section. The homeroom teacher can view student cards for their class.")

        grade_section_pairs = sorted(set([(s.get("grade"), s.get("section")) for s in st.session_state.students if s.get("grade") and s.get("section")]))
        if not grade_section_pairs:
            st.info("No students found. Add students first.")
        else:
            st.markdown("#### Current Assignments")
            assignments_df = pd.DataFrame(st.session_state.homeroom_assignments)
            if not assignments_df.empty:
                assignments_df["Teacher Name"] = assignments_df["teacher_id"].apply(lambda x: get_teacher_name(x))
                st.dataframe(assignments_df[["grade", "section", "Teacher Name"]], use_container_width=True)
            else:
                st.info("No homeroom assignments yet.")

            st.markdown("#### Assign Homeroom Teacher")
            col1, col2, col3 = st.columns(3)
            with col1:
                assigned_pairs = set([(h.get("grade"), h.get("section")) for h in st.session_state.homeroom_assignments])
                available_pairs = [pair for pair in grade_section_pairs if pair not in assigned_pairs]
                if available_pairs:
                    pair_labels = [f"{g} - {s}" for g, s in available_pairs]
                    selected_pair_label = st.selectbox("Select Grade - Section", pair_labels)
                    selected_grade, selected_section = selected_pair_label.split(" - ")
                else:
                    st.info("All grade-section pairs already have homeroom teachers.")
                    selected_grade, selected_section = None, None
            with col2:
                teacher_options = {f"{t['name']} ({t['id']})": t['id'] for t in st.session_state.teachers}
                selected_teacher_label = st.selectbox("Select Teacher", options=list(teacher_options.keys())) if teacher_options else None
                selected_teacher_id = teacher_options.get(selected_teacher_label) if selected_teacher_label else None
            with col3:
                if selected_grade and selected_teacher_id:
                    if st.button("Assign Homeroom Teacher", width='stretch'):
                        supabase_admin = get_supabase_admin()
                        try:
                            new_assignment = {
                                "grade": selected_grade,
                                "section": selected_section,
                                "teacher_id": selected_teacher_id,
                                "assigned_at": datetime.now().isoformat()
                            }
                            supabase_admin.table("homeroom_assignments").insert(new_assignment).execute()
                            load_all_data()
                            add_notification(f"👨‍🏫 Homeroom teacher assigned: {selected_grade} - {selected_section} → {get_teacher_name(selected_teacher_id)}", "success")
                            st.success("✅ Homeroom teacher assigned successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to assign homeroom teacher: {e}")

    # --- Tab 14: Student Cards ---
    with tab14:
        show_student_card_panel()

# ===================================================================
# STUDENT PANEL (Profile only)
# ===================================================================

def show_student_panel():
    st.markdown("### 👨‍🎓 Student Dashboard")
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
                <p><b>Section:</b> {student.get('section', 'N/A')}</p>
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

# ===================================================================
# TEACHER PANEL (modified to assign subject admin)
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
    assignments = json.loads(teacher.get("assignments", "[]"))

    if not teacher_subject:
        st.warning("No subject assigned. Please contact administrator.")
        return

    if not assignments:
        st.warning("No grade/section/semester assignments. Please contact administrator.")
        return

    available_semesters = sorted(set([a.get("semester") for a in assignments if a.get("semester")]))
    if not available_semesters:
        st.warning("No semester assigned. Please contact administrator.")
        return

    selected_semester = st.selectbox(
        "📚 Select Semester",
        available_semesters,
        index=0 if available_semesters else None,
        key="teacher_semester"
    )

    semester_assignments = [a for a in assignments if a.get("semester") == selected_semester]
    assigned_grades = list(set([a["grade"] for a in semester_assignments]))
    if not assigned_grades:
        st.warning(f"No assignments for {selected_semester}.")
        return

    if "teacher_selected_grade" not in st.session_state or st.session_state.teacher_selected_grade not in assigned_grades:
        st.session_state.teacher_selected_grade = assigned_grades[0]

    selected_grade = st.selectbox(
        "📚 Select Grade to Evaluate",
        assigned_grades,
        index=assigned_grades.index(st.session_state.teacher_selected_grade) if st.session_state.teacher_selected_grade in assigned_grades else 0,
        key="grade_selector"
    )
    st.session_state.teacher_selected_grade = selected_grade

    assigned_sections = [a["section"] for a in semester_assignments if a["grade"] == selected_grade]
    if not assigned_sections:
        st.error("No sections assigned for this grade in this semester. Contact admin.")
        return

    if "teacher_selected_section" not in st.session_state or st.session_state.teacher_selected_section not in assigned_sections:
        st.session_state.teacher_selected_section = assigned_sections[0]

    selected_section = st.selectbox(
        "📚 Select Section",
        assigned_sections,
        index=assigned_sections.index(st.session_state.teacher_selected_section) if st.session_state.teacher_selected_section in assigned_sections else 0,
        key="section_selector"
    )
    st.session_state.teacher_selected_section = selected_section

    valid_subjects = GRADE_SUBJECTS.get(selected_grade, [])
    is_subject_valid = teacher_subject in valid_subjects
    st.markdown(f"""
    <div style="background:#F8F9FA;padding:0.75rem;border-radius:8px;margin-bottom:0.5rem;border:1px solid #E8EAED;">
        <b>📋 Subjects for {selected_grade}:</b> {', '.join(valid_subjects) if valid_subjects else 'Not defined'}
    </div>
    """, unsafe_allow_html=True)

    if not is_subject_valid:
        st.error(f"""
        ⚠️ **Subject Mismatch!**  
        Your assigned subject is **{teacher_subject}**, but this grade requires one of:  
        **{', '.join(valid_subjects)}**.  
        Please select a different grade or contact the administrator.
        """)

    def get_eligible_students(grade, section):
        return [s for s in st.session_state.students
                if s.get("grade") == grade and s.get("section") == section
                and teacher_subject in s.get("subjects", [])]

    existing_batch = None
    for b in st.session_state.batches:
        if (b.get("teacher_id") == teacher_id and
            b.get("grade") == selected_grade and
            b.get("section") == selected_section and
            b.get("subject") == teacher_subject and
            b.get("semester") == selected_semester and
            b.get("status") == "pending"):
            existing_batch = b
            break

    can_submit = any(a.get("semester") == selected_semester for a in assignments)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Batch Submission" if can_submit else "📝 View Only (Previous Semester)",
        "📊 My Submissions",
        "📊 My Students",
        "✅ Approval Status"
    ])

    # ---------- TAB 1: Submit Batch ----------
    with tab1:
        if can_submit:
            st.markdown("#### 📝 Submit Batch Evaluation")
            st.markdown(f"""
            <div style="background:#E8F0FE;padding:1rem;border-radius:12px;margin-bottom:1rem;border-left:4px solid #1A73E8;">
                <h4 style="margin:0;color:#1A73E8;font-size:1.8rem;">👨‍🏫 Teacher: {teacher_name}</h4>
                <p style="margin:0;color:#202124;font-size:1.2rem;"><b>📚 Subject:</b> {teacher_subject}</p>
                <p style="margin:0;color:#202124;font-size:1.2rem;"><b>📋 Grade:</b> {selected_grade} · <b>Section:</b> {selected_section} · <b>Semester:</b> {selected_semester}</p>
            </div>
            """, unsafe_allow_html=True)

            if not is_subject_valid:
                st.error("❌ You cannot submit evaluations for this grade because your subject is not in the curriculum.")
                return

            allowed, reason = check_action_allowed("Student Evaluation (Batch)", teacher_name)
            if not allowed:
                st.error(f"⚠️ **PENALTY WARNING!**\n{reason}")
                return

            eligible_students = get_eligible_students(selected_grade, selected_section)
            if not eligible_students:
                st.info(f"No students in {selected_grade} ({selected_section}) taking {teacher_subject}.")
                return

            if existing_batch:
                student_data = existing_batch["students"]
                weights = existing_batch["weights"]
                max_scores = existing_batch.get("max_scores", DEFAULT_MAX_SCORES.copy())
                remarks = existing_batch.get("remarks", DEFAULT_REMARKS)
            else:
                weights = {"Test 1": 10, "Test 2": 10, "Test 3": 10, "Test 4": 30, "Final Exam": 40}
                max_scores = DEFAULT_MAX_SCORES.copy()
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
                remarks = DEFAULT_REMARKS

            st.markdown("**Set assessment weights and maximum scores:**")
            weight_options = [0,5,10,15,20,30,40,50]
            def get_max_options(current_max):
                opts = MAX_SCORE_OPTIONS.copy()
                if current_max not in opts:
                    opts.append(current_max)
                    opts.sort()
                return opts

            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown("**Test 1**")
                w1 = st.selectbox("Weight", options=weight_options, index=weight_options.index(weights["Test 1"]), key="w1")
                max1 = st.selectbox("Max Score", options=get_max_options(max_scores["Test 1"]), index=get_max_options(max_scores["Test 1"]).index(max_scores["Test 1"]), key="max1")
            with col2:
                st.markdown("**Test 2**")
                w2 = st.selectbox("Weight", options=weight_options, index=weight_options.index(weights["Test 2"]), key="w2")
                max2 = st.selectbox("Max Score", options=get_max_options(max_scores["Test 2"]), index=get_max_options(max_scores["Test 2"]).index(max_scores["Test 2"]), key="max2")
            with col3:
                st.markdown("**Test 3**")
                w3 = st.selectbox("Weight", options=weight_options, index=weight_options.index(weights["Test 3"]), key="w3")
                max3 = st.selectbox("Max Score", options=get_max_options(max_scores["Test 3"]), index=get_max_options(max_scores["Test 3"]).index(max_scores["Test 3"]), key="max3")
            with col4:
                st.markdown("**Test 4**")
                w4 = st.selectbox("Weight", options=weight_options, index=weight_options.index(weights["Test 4"]), key="w4")
                max4 = st.selectbox("Max Score", options=get_max_options(max_scores["Test 4"]), index=get_max_options(max_scores["Test 4"]).index(max_scores["Test 4"]), key="max4")
            with col5:
                st.markdown("**Final Exam**")
                wf = st.selectbox("Weight", options=weight_options, index=weight_options.index(weights["Final Exam"]), key="wf")
                maxf = st.selectbox("Max Score", options=get_max_options(max_scores["Final Exam"]), index=get_max_options(max_scores["Final Exam"]).index(max_scores["Final Exam"]), key="maxf")

            new_weights = {"Test 1": w1, "Test 2": w2, "Test 3": w3, "Test 4": w4, "Final Exam": wf}
            new_max_scores = {"Test 1": max1, "Test 2": max2, "Test 3": max3, "Test 4": max4, "Final Exam": maxf}

            def compute_overall_row(row, weights, max_scores):
                total_weighted = 0
                total_weight = 0
                for name in weights.keys():
                    max_score = max_scores.get(name, 100)
                    raw = row.get(name, 0)
                    pct = (raw / max_score) * 100 if max_score > 0 else 0
                    total_weighted += pct * weights[name]
                    total_weight += weights[name]
                return round(total_weighted / total_weight, 2) if total_weight > 0 else 0

            st.markdown(f"**Enter raw scores (each out of its max score):**")
            df_edit = pd.DataFrame(student_data)
            columns_order = ["student_id", "student_name", "Test 1", "Test 2", "Test 3", "Test 4", "Final Exam", "overall"]
            df_edit = df_edit[columns_order]

            col_config = {
                "student_id": st.column_config.TextColumn("ID", disabled=True),
                "student_name": st.column_config.TextColumn("Student Name", disabled=True),
                "overall": st.column_config.NumberColumn("Overall (%)", disabled=True)
            }
            for name in ["Test 1", "Test 2", "Test 3", "Test 4", "Final Exam"]:
                max_val = new_max_scores.get(name, 100)
                col_config[name] = st.column_config.NumberColumn(
                    f"{name} (max {max_val})",
                    min_value=0,
                    max_value=max_val,
                    step=1
                )

            edited_df = st.data_editor(
                df_edit,
                column_config=col_config,
                hide_index=True,
                use_container_width=True,
                key="batch_editor"
            )

            remarks = st.text_area("Batch Remarks / Comments (optional)", value=remarks)

            if remarks.strip():
                st.markdown(f"""
                <div class="watermark-container">
                    <div class="watermark-text">{remarks}</div>
                </div>
                """, unsafe_allow_html=True)

            if st.button("💾 Submit Batch for Approval", width='stretch'):
                students_list = edited_df.to_dict(orient="records")
                for rec in students_list:
                    rec["overall"] = compute_overall_row(rec, new_weights, new_max_scores)

                # ---- Assign subject admin ----
                subject_admin_id = get_subject_admin(teacher_subject)

                if existing_batch:
                    existing_batch["students"] = students_list
                    existing_batch["weights"] = new_weights
                    existing_batch["max_scores"] = new_max_scores
                    existing_batch["remarks"] = remarks
                    existing_batch["subject_admin_id"] = subject_admin_id
                    existing_batch["submitted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    supabase_admin = get_supabase_admin()
                    try:
                        supabase_admin.table("batches").update(existing_batch).eq("id", existing_batch["id"]).execute()
                        load_all_data()
                        add_notification(f"📝 Batch updated for {teacher_name} ({selected_grade} {selected_section} {selected_semester} {teacher_subject})", "info")
                        st.success("✅ Batch updated successfully! Awaiting approval.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to update batch: {e}")
                else:
                    batch = {
                        "id": str(uuid.uuid4())[:8],
                        "teacher_id": teacher_id,
                        "teacher_name": teacher_name,
                        "grade": selected_grade,
                        "section": selected_section,
                        "semester": selected_semester,
                        "subject": teacher_subject,
                        "students": students_list,
                        "weights": new_weights,
                        "max_scores": new_max_scores,
                        "remarks": remarks,
                        "status": "pending",
                        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "subject_admin_id": subject_admin_id  # NEW
                    }
                    supabase_admin = get_supabase_admin()
                    try:
                        supabase_admin.table("batches").insert(batch).execute()
                        load_all_data()
                        add_notification(f"📦 New batch submitted by {teacher_name} ({selected_grade} {selected_section} {selected_semester} {teacher_subject})", "info")
                        # Celebration
                        st.balloons()
                        st.markdown("""
                        <div style="background: #E8F0FE; padding: 1.5rem; border-radius: 12px; text-align: center; border: 2px solid #1A73E8;">
                            <div style="font-size: 3.5rem; line-height: 1.4;">📚✍️🚀✨</div>
                            <h3 style="color: #1A73E8; margin: 0.5rem 0;">✅ Batch Submitted!</h3>
                            <p style="font-size: 1.1rem;">Your evaluations are now pending approval. You'll be notified once reviewed.</p>
                            <p style="font-size: 0.95rem; color: #5F6368;">🌟 Thank you for your dedication, Teacher! 🌟</p>
                        </div>
                        """, unsafe_allow_html=True)
                        time.sleep(2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to save batch: {e}")
        else:
            st.info("📌 You do not have permission to submit evaluations for this semester. You can view your previous submissions below.")

    # ---------- TAB 2: My Submissions ----------
    with tab2:
        st.markdown("#### 📊 My Submissions (Batches)")
        my_batches = [b for b in st.session_state.batches if b.get("teacher_id") == teacher_id and b.get("semester") == selected_semester]
        if not my_batches:
            st.info("You haven't submitted any batches for this semester.")
        else:
            for batch in reversed(my_batches):
                status = batch.get("status", "pending")
                if status == "approved":
                    status_label = "🎉✅ Approved 🎉"
                elif status == "subject_approved":
                    status_label = "⏳ Approved by Subject Admin, pending final"
                elif status == "pending":
                    status_label = "⏳ Pending"
                else:
                    status_label = "❌ Rejected"
                status_class = "badge-approved" if status == "approved" else "badge-subject-approved" if status == "subject_approved" else "badge-pending" if status == "pending" else "badge-rejected"
                student_count = len(batch.get("students", []))
                batch_remarks = batch.get("remarks", "")
                semester = batch.get("semester", "N/A")
                st.markdown(f"""
                <div class="eval-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4 style="color:#1A73E8;font-size:1.8rem;margin:0 0 0.5rem 0;">👨‍🏫 {batch['teacher_name']} · 📚 {batch['subject']}</h4>
                            <p><b>📋 Grade:</b> {batch['grade']}</p>
                            <p><b>📌 Section:</b> {batch.get('section', 'N/A')}</p>
                            <p><b>📌 Semester:</b> {semester}</p>
                            <p><b>👥 Students:</b> {student_count}</p>
                            <p><b>📅 Submitted:</b> {batch.get('submitted_at', 'N/A')}</p>
                            <p><b>Remarks:</b> {batch_remarks if batch_remarks else 'None'}</p>
                        </div>
                        <div style="text-align:right;">
                            <span class="{status_class}">{status_label}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Celebration banner for approved batches
                if status == "approved":
                    st.markdown("""
                    <div style="background: #E6F4EA; padding: 0.8rem 1.2rem; border-radius: 12px; 
                                border-left: 6px solid #34A853; margin-bottom: 0.8rem;
                                display: flex; align-items: center; gap: 12px;">
                        <span style="font-size: 2rem;">🏆📚</span>
                        <span style="font-size: 1.1rem; font-weight: 600; color: #1e7e34;">
                            🎉 Congratulations! Your batch has been fully approved! 🎉
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

                if status == "approved":
                    if st.button(f"📥 Download Batch (Excel)", key=f"download_batch_{batch['id']}", width='stretch'):
                        df_batch = pd.DataFrame(batch["students"])
                        df_batch["Grade"] = batch["grade"]
                        df_batch["Section"] = batch.get("section", "")
                        df_batch["Semester"] = batch.get("semester", "")
                        df_batch["Subject"] = batch["subject"]
                        df_batch["Teacher"] = batch["teacher_name"]
                        df_batch["Remarks"] = batch_remarks
                        cols = ["student_id", "student_name", "Grade", "Section", "Semester", "Subject", "Teacher", "Test 1", "Test 2", "Test 3", "Test 4", "Final Exam", "overall", "Remarks"]
                        available_cols = [c for c in cols if c in df_batch.columns]
                        df_export = df_batch[available_cols]
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df_export.to_excel(writer, sheet_name="Batch", index=False)
                        st.download_button(
                            label="📥 Click to Download",
                            data=output.getvalue(),
                            file_name=f"batch_{batch['id']}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"download_btn_{batch['id']}",
                            width='stretch'
                        )
                if status == "pending" and can_submit:
                    if st.button(f"✏️ Edit Batch", key=f"edit_batch_{batch['id']}", width='stretch'):
                        st.session_state.edit_batch_id = batch["id"]
                        st.rerun()

    # ---------- TAB 3: My Students ----------
    with tab3:
        st.markdown("#### 📊 My Students")
        students_in_grade_section = get_eligible_students(selected_grade, selected_section)
        if students_in_grade_section:
            st.markdown(f"**Students in {selected_grade} ({selected_section}) taking {teacher_subject} (Semester: {selected_semester}):**")
            for s in students_in_grade_section:
                evals = get_approved_evaluations_for_student(s["id"])
                approved_count = len(evals)
                status = "✅ Approved" if approved_count > 0 else "📝 Not Evaluated"
                grade_display = get_grade_display(s["grade"])
                grade_class = get_grade_class(s["grade"])
                st.markdown(f"""
                <div class="student-card">
                    <h4>👤 {s['name']}</h4>
                    <p><b>Grade:</b> <span class="{grade_class}">{grade_display}</span></p>
                    <p><b>Section:</b> {s.get('section', 'N/A')}</p>
                    <p><b>Status:</b> {status}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info(f"No students in {selected_grade} ({selected_section}) taking your subject.")

    # ---------- TAB 4: Approval Status ----------
    with tab4:
        st.markdown("#### ✅ Approval Status")
        my_batches = [b for b in st.session_state.batches if b.get("teacher_id") == teacher_id and b.get("semester") == selected_semester]
        pending = [b for b in my_batches if b.get("status") == "pending"]
        subject_approved = [b for b in my_batches if b.get("status") == "subject_approved"]
        approved = [b for b in my_batches if b.get("status") == "approved"]
        rejected = [b for b in my_batches if b.get("status") == "rejected"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("⏳ Pending", len(pending))
        col2.metric("📋 Subject Approved", len(subject_approved))
        col3.metric("✅ Fully Approved", len(approved))
        col4.metric("❌ Rejected", len(rejected))

# ===================================================================
# LOGIN PAGE
# ===================================================================

def show_login_page():
    st.markdown("""
    <div style="text-align:center; padding:1rem 0;">
        <div style="font-size:4rem; margin-bottom:0.5rem;">📚✍️🌍SRP🏫ET ኢትዮጲያ🕊️🎓🚀</div>
        <h1 style="font-size:3rem; margin:0;">School Registration Portal</h1>
        <p style="color:#5F6368; font-size:1.2rem; margin-top:0.5rem;">👨‍🏫📚Admin-Controlled Student & Teacher Management System⏱️🎯🏃‍➡️ </p>
        <p style="color:#5F6368; font-size:1rem;"> 🏫🇪🇹📚 Grades🎓1-12🎓🚀in Ethiopia📚✍️🌍ኢትዮጲያ🕊️🔥🚀</p>
    </div>
    """, unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔐🔑Password", type="password", placeholder="Enter password")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submitted = st.form_submit_button("🇪🇹🌍🎓 Sign In 🔐🔑", width='stretch')
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

# ===================================================================
# MAIN
# ===================================================================

def main():
    init_user_db()

    # ---- Handle celebration dismissal via query param ----
    if st.query_params.get("celebration_dismissed"):
        st.session_state.celebration_dismissed = True
        st.query_params.clear()
        st.rerun()

    if not st.session_state.logged_in:
        # Check for Ethiopian New Year celebration period
        if is_celebration_period() and not st.session_state.get("celebration_dismissed", False):
            show_celebration_page()
            return   # stop further rendering; the page is fully occupied
        else:
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
        elif role == "subject_admin":
            nav_options = ["📋 Subject Admin Dashboard", "⚠️ My Penalties", "🔔 Notifications"]
        elif role == "teacher":
            nav_options = ["👨‍🏫 My Dashboard", "📝 Submit Evaluation", "📊 My Students", "✅ Approval Status", "⚠️ My Penalties", "🔔 Notifications"]
        else:
            nav_options = ["👨‍🎓 My Profile", "⚠️ My Penalties", "🔔 Notifications"]

        selected_page = st.radio("Navigation", nav_options, index=0)
        st.session_state.current_page = selected_page

        if st.button("🚪 Logout", width='stretch'):
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
    pending_batches = len(get_batches_awaiting_final_approval())  # School Admin pending count

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
                        June 25, 2026
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
            # Quick link to the Teachers tab in Admin panel
            st.info("Please use the **Admin Dashboard → Teachers** tab for full teacher management with subject admin assignment.")
            # Optionally, replicate the simple teacher list
            if st.session_state.teachers:
                for t in st.session_state.teachers:
                    admin_subjects = json.loads(t.get("admin_subjects", "[]"))
                    admin_str = ", ".join(admin_subjects) if admin_subjects else "None"
                    st.markdown(f"""
                    <div class="teacher-card">
                        <h4>👨‍🏫 {t['name']}</h4>
                        <p><b>📚 Subject:</b> {t['subject']}</p>
                        <p><b>🔐 Admin Subjects:</b> {admin_str}</p>
                        <p><b>✉️ Email:</b> {t.get('email', 'N/A')}</p>
                        <p><b>👤 Username:</b> <code>{t.get('username', 'N/A')}</code></p>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No teachers yet.")
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
            # Quick ranking view
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
                    st.dataframe(df_sorted[["Rank", "Name", "Average Score", "Evaluations"]], use_container_width=True, hide_index=True)
        elif current_page == "📥 Import/Export":
            st.markdown("### 📥 Import / Export Data")
            st.info("Please use the **Admin Dashboard → Import/Export** tab for full functionality.")
        elif current_page == "📄 Approval Report":
            st.markdown("### 📄 Approval Report (Grade‑wise)")
            st.info("Please use the **Admin Dashboard → Approval Report** tab for the comprehensive grade report.")
        elif current_page == "⚠️ Penalty Log":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

    elif role == "subject_admin":
        if current_page == "📋 Subject Admin Dashboard":
            show_subject_admin_panel()
        elif current_page == "⚠️ My Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

    elif role == "teacher":
        if current_page in ["👨‍🏫 My Dashboard", "📝 Submit Evaluation", "📊 My Students", "✅ Approval Status"]:
            show_teacher_panel()
        elif current_page == "⚠️ My Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

    else:
        if current_page == "👨‍🎓 My Profile":
            show_student_panel()
        elif current_page == "⚠️ My Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

if __name__ == "__main__":
    main()
