# ===================================================================
# SCHOOL REGISTRATION PORTAL - PERSISTENT WITH SUPABASE
# Enhanced with Real Assessment Weights, Profile Photos, and Stats
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
import time
import base64
from supabase import create_client, Client
from PIL import Image

# ===================================================================
# DEFAULT REMARKS TEXT
# ===================================================================
DEFAULT_REMARKS = "በአጠቃላይ የተማሪዎች ውጤት ጥሩ ነው፣ ነገር ግን የበለጠ ለማድረግ ከትምህርት ቤቱ ማህበረሰብ ተጨማሪ ጥረት ያስፈልጋል።"

# ===================================================================
# REAL ASSESSMENT WEIGHTS PER GRADE (Ethiopian School System)
# ===================================================================

# Assessment configuration: For each grade, define assessment components with weights
GRADE_ASSESSMENT_CONFIG = {
    # Grades 1-3: 9 components
    "Grade 1": {
        "components": [
            {"name": "ሙከራ (Test 1)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 2)", "weight": 10, "max_score": 10},
            {"name": "ሙከራ (Test 3)", "weight": 5, "max_score": 5},
            {"name": "አጋማሽ ፈተና (Mid-Exam)", "weight": 15, "max_score": 15},
            {"name": "ሙከራ (Test 4)", "weight": 5, "max_score": 5},
            {"name": "ቡድን ስራ (Group Work)", "weight": 10, "max_score": 10},
            {"name": "የግል ስራ (Assignment)", "weight": 10, "max_score": 10},
            {"name": "ደብተር/ተሳትፎ (Exercise)", "weight": 10, "max_score": 10},
            {"name": "ማጠቃለያ ፈተና (Final Exam)", "weight": 30, "max_score": 30}
        ]
    },
    "Grade 2": {
        "components": [
            {"name": "ሙከራ (Test 1)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 2)", "weight": 10, "max_score": 10},
            {"name": "ሙከራ (Test 3)", "weight": 5, "max_score": 5},
            {"name": "አጋማሽ ፈተና (Mid-Exam)", "weight": 15, "max_score": 15},
            {"name": "ሙከራ (Test 4)", "weight": 5, "max_score": 5},
            {"name": "ቡድን ስራ (Group Work)", "weight": 10, "max_score": 10},
            {"name": "የግል ስራ (Assignment)", "weight": 10, "max_score": 10},
            {"name": "ደብተር/ተሳትፎ (Exercise)", "weight": 10, "max_score": 10},
            {"name": "ማጠቃለያ ፈተና (Final Exam)", "weight": 30, "max_score": 30}
        ]
    },
    "Grade 3": {
        "components": [
            {"name": "ሙከራ (Test 1)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 2)", "weight": 10, "max_score": 10},
            {"name": "ሙከራ (Test 3)", "weight": 5, "max_score": 5},
            {"name": "አጋማሽ ፈተና (Mid-Exam)", "weight": 15, "max_score": 15},
            {"name": "ሙከራ (Test 4)", "weight": 5, "max_score": 5},
            {"name": "ቡድን ስራ (Group Work)", "weight": 10, "max_score": 10},
            {"name": "የግል ስራ (Assignment)", "weight": 10, "max_score": 10},
            {"name": "ደብተር/ተሳትፎ (Exercise)", "weight": 10, "max_score": 10},
            {"name": "ማጠቃለያ ፈተና (Final Exam)", "weight": 30, "max_score": 30}
        ]
    },
    # Grades 4-5: 9 components with different weights
    "Grade 4": {
        "components": [
            {"name": "ሙከራ (Test 1)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 2)", "weight": 5, "max_score": 5},
            {"name": "የቡድን ስራ (Group Work)", "weight": 5, "max_score": 5},
            {"name": "አጋማሽ ፈተና (Mid-Exam)", "weight": 20, "max_score": 20},
            {"name": "ሙከራ (Test 3)", "weight": 5, "max_score": 5},
            {"name": "የግል ስራ (Assignment)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 4)", "weight": 5, "max_score": 5},
            {"name": "ደብተር/ተሳትፎ (Exercise)", "weight": 10, "max_score": 10},
            {"name": "ማጠቃለያ ፈተና (Final Exam)", "weight": 40, "max_score": 40}
        ]
    },
    "Grade 5": {
        "components": [
            {"name": "ሙከራ (Test 1)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 2)", "weight": 5, "max_score": 5},
            {"name": "የቡድን ስራ (Group Work)", "weight": 5, "max_score": 5},
            {"name": "አጋማሽ ፈተና (Mid-Exam)", "weight": 20, "max_score": 20},
            {"name": "ሙከራ (Test 3)", "weight": 5, "max_score": 5},
            {"name": "የግል ስራ (Assignment)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 4)", "weight": 5, "max_score": 5},
            {"name": "ደብተር/ተሳትፎ (Exercise)", "weight": 10, "max_score": 10},
            {"name": "ማጠቃለያ ፈተና (Final Exam)", "weight": 40, "max_score": 40}
        ]
    },
    # Grades 6: 9 components (same as 4-5 but can be customized per subject)
    "Grade 6": {
        "components": [
            {"name": "ሙከራ (Test 1)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 2)", "weight": 5, "max_score": 5},
            {"name": "የቡድን ስራ (Group Work)", "weight": 5, "max_score": 5},
            {"name": "አጋማሽ ፈተና (Mid-Exam)", "weight": 20, "max_score": 20},
            {"name": "ሙከራ (Test 3)", "weight": 5, "max_score": 5},
            {"name": "የግል ስራ (Assignment)", "weight": 5, "max_score": 5},
            {"name": "ሙከራ (Test 4)", "weight": 5, "max_score": 5},
            {"name": "ደብተር/ተሳትፎ (Exercise)", "weight": 10, "max_score": 10},
            {"name": "ማጠቃለያ ፈተና (Final Exam)", "weight": 40, "max_score": 40}
        ]
    },
    # Grade 7: 6 components
    "Grade 7": {
        "components": [
            {"name": "Quiz", "weight": 5, "max_score": 5},
            {"name": "Test", "weight": 5, "max_score": 5},
            {"name": "Mid-Exam", "weight": 15, "max_score": 15},
            {"name": "Group Work", "weight": 10, "max_score": 10},
            {"name": "Assignment", "weight": 5, "max_score": 5},
            {"name": "Final-Exam", "weight": 60, "max_score": 60}
        ]
    },
    # Grade 8: 6 components (same as 7)
    "Grade 8": {
        "components": [
            {"name": "Quiz", "weight": 5, "max_score": 5},
            {"name": "Test", "weight": 5, "max_score": 5},
            {"name": "Mid-Exam", "weight": 15, "max_score": 15},
            {"name": "Group Work", "weight": 10, "max_score": 10},
            {"name": "Assignment", "weight": 5, "max_score": 5},
            {"name": "Final-Exam", "weight": 60, "max_score": 60}
        ]
    },
    # Grades 9-12: Can be customized, using standard components
    "Grade 9": {
        "components": [
            {"name": "Quiz 1", "weight": 5, "max_score": 5},
            {"name": "Quiz 2", "weight": 5, "max_score": 5},
            {"name": "Test 1", "weight": 10, "max_score": 10},
            {"name": "Mid-Exam", "weight": 20, "max_score": 20},
            {"name": "Test 2", "weight": 10, "max_score": 10},
            {"name": "Assignment", "weight": 10, "max_score": 10},
            {"name": "Final-Exam", "weight": 40, "max_score": 40}
        ]
    },
    "Grade 10": {
        "components": [
            {"name": "Quiz 1", "weight": 5, "max_score": 5},
            {"name": "Quiz 2", "weight": 5, "max_score": 5},
            {"name": "Test 1", "weight": 10, "max_score": 10},
            {"name": "Mid-Exam", "weight": 20, "max_score": 20},
            {"name": "Test 2", "weight": 10, "max_score": 10},
            {"name": "Assignment", "weight": 10, "max_score": 10},
            {"name": "Final-Exam", "weight": 40, "max_score": 40}
        ]
    },
    "Grade 11": {
        "components": [
            {"name": "Quiz 1", "weight": 5, "max_score": 5},
            {"name": "Quiz 2", "weight": 5, "max_score": 5},
            {"name": "Test 1", "weight": 10, "max_score": 10},
            {"name": "Mid-Exam", "weight": 20, "max_score": 20},
            {"name": "Test 2", "weight": 10, "max_score": 10},
            {"name": "Assignment", "weight": 10, "max_score": 10},
            {"name": "Final-Exam", "weight": 40, "max_score": 40}
        ]
    },
    "Grade 12": {
        "components": [
            {"name": "Quiz 1", "weight": 5, "max_score": 5},
            {"name": "Quiz 2", "weight": 5, "max_score": 5},
            {"name": "Test 1", "weight": 10, "max_score": 10},
            {"name": "Mid-Exam", "weight": 20, "max_score": 20},
            {"name": "Test 2", "weight": 10, "max_score": 10},
            {"name": "Assignment", "weight": 10, "max_score": 10},
            {"name": "Final-Exam", "weight": 40, "max_score": 40}
        ]
    }
}

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
    "Grade 11": ["Biology", "Chemistry", "Physics", "Technical Drawing", "Mathematics", "English", "Information Technology (IT)", "Citizenship Education / Civics", "Geography", "History", "Economics", "General Business"],
    "Grade 12": ["Biology", "Chemistry", "Physics", "Technical Drawing", "Mathematics", "English", "Information Technology (IT)", "Citizenship Education / Civics", "Geography", "History", "Economics", "General Business"],
}

# ---- School Settings ----
if 'school_name' not in st.session_state:
    st.session_state.school_name = "የሙከራ ትምህርት ቤት"
if 'school_city' not in st.session_state:
    st.session_state.school_city = "አርባ ምንጭ"
if 'director_name' not in st.session_state:
    st.session_state.director_name = "____________________________"

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
                "name": u["name"],
                "profile_photo": u.get("profile_photo", "")
            }
    st.session_state.user_db = user_db
    res = supabase.table("notifications").select("*").order("id", desc=True).execute()
    st.session_state.notifications = res.data if res.data else []
    res = supabase.table("penalty_log").select("*").order("id", desc=True).execute()
    st.session_state.penalty_log = res.data if res.data else []
    res = supabase.table("homeroom_assignments").select("*").execute()
    st.session_state.homeroom_assignments = res.data if res.data else []

# ---- Helper: Get assessment config for a grade ----
def get_assessment_config(grade):
    """Get the assessment components for a given grade."""
    return GRADE_ASSESSMENT_CONFIG.get(grade, GRADE_ASSESSMENT_CONFIG["Grade 1"])

def get_component_names(grade):
    """Get just the names of assessment components for a grade."""
    config = get_assessment_config(grade)
    return [c["name"] for c in config["components"]]

def get_component_weights(grade):
    """Get a dict of component name -> weight for a grade."""
    config = get_assessment_config(grade)
    return {c["name"]: c["weight"] for c in config["components"]}

def get_component_max_scores(grade):
    """Get a dict of component name -> max_score for a grade."""
    config = get_assessment_config(grade)
    return {c["name"]: c["max_score"] for c in config["components"]}

def compute_overall_from_components(scores_dict, grade):
    """Compute overall score from component scores using grade weights."""
    weights = get_component_weights(grade)
    total_weighted = 0
    total_weight = 0
    for name, score in scores_dict.items():
        if name in weights:
            total_weighted += score * weights[name]
            total_weight += weights[name]
    return round(total_weighted / total_weight, 2) if total_weight > 0 else 0

# ---- Auth Functions ----
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

def is_username_taken(username):
    supabase = get_supabase()
    try:
        res = supabase.table("users").select("username").eq("username", username).execute()
        return len(res.data) > 0
    except Exception as e:
        return False

# ---- Profile Photo Helpers ----
def save_profile_photo(username, photo_bytes):
    """Save profile photo to Supabase storage or as base64."""
    if photo_bytes:
        encoded = base64.b64encode(photo_bytes).decode('utf-8')
        return encoded
    return ""

def get_profile_photo(username):
    """Get profile photo for a user."""
    user_data = st.session_state.user_db.get(username, {})
    return user_data.get("profile_photo", "")

def display_profile_photo(username, size=80):
    """Display profile photo as HTML image."""
    photo_data = get_profile_photo(username)
    if photo_data:
        return f'<img src="data:image/png;base64,{photo_data}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #1A73E8;">'
    else:
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:#E8F0FE;display:flex;align-items:center;justify-content:center;font-size:{size//2}px;color:#1A73E8;border:2px solid #1A73E8;">{username[0].upper()}</div>'

# ---- Init User DB ----
def init_user_db():
    if 'students' not in st.session_state:
        load_all_data()
    if "admin" not in st.session_state.user_db:
        st.session_state.user_db["admin"] = {
            "password": hash_password("adminbb"),
            "role": "admin",
            "name": "School Administrator",
            "profile_photo": ""
        }
        supabase_admin = get_supabase_admin()
        try:
            supabase_admin.table("users").insert({
                "username": "admin",
                "password": hash_password("adminbb"),
                "role": "admin",
                "name": "School Administrator",
                "profile_photo": ""
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
    st.session_state.celebration_dismissed = False

# ---- Notifications ----
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

# ---- Registration Check ----
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

# ---- Helper Functions ----
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

def get_batches_for_subject_admin(admin_id):
    return [b for b in st.session_state.batches if b.get("subject_admin_id") == admin_id and b.get("status") == "pending"]

def get_batches_awaiting_final_approval():
    return [b for b in st.session_state.batches 
            if (b.get("status") == "subject_approved") or 
               (b.get("status") == "pending" and b.get("subject_admin_id") is None)]

def get_approved_evaluations_for_student(student_id):
    return [e for e in st.session_state.evaluations if e.get("student_id") == student_id and e.get("status") == "approved"]

def get_subject_admin(subject):
    for t in st.session_state.teachers:
        admin_subjects = json.loads(t.get("admin_subjects", "[]"))
        if subject in admin_subjects:
            return t["id"]
    return None

def get_grade_display(grade):
    grade_num = grade.replace("Grade ", "")
    try:
        num = int(grade_num)
        if num <= 8:
            amharic_grades = {"1": "1ኛ", "2": "2ኛ", "3": "3ኛ", "4": "4ኛ",
                            "5": "5ኛ", "6": "6ኛ", "7": "7ኛ", "8": "8ኛ"}
            return f"{amharic_grades.get(grade_num, grade_num)} ክፍል"
        else:
            return grade
    except:
        return grade

# ---- Page Config ----
st.set_page_config(
    page_title="School Registration Portal",
    page_icon="SRP🏫@ET",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================================================================
# STATISTICAL ANALYSIS FUNCTIONS
# ===================================================================

def generate_school_statistics():
    """Generate comprehensive school statistics report."""
    
    total_students = len(st.session_state.students)
    total_teachers = len(st.session_state.teachers)
    total_evaluations = len([e for e in st.session_state.evaluations if e.get("status") == "approved"])
    total_batches = len(st.session_state.batches)
    
    # Gender distribution
    male_students = len([s for s in st.session_state.students if s.get("gender") == "M"])
    female_students = len([s for s in st.session_state.students if s.get("gender") == "F"])
    
    # Grade distribution
    grade_distribution = {}
    for s in st.session_state.students:
        grade = s.get("grade", "Unknown")
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
    
    # Section distribution
    section_distribution = {}
    for s in st.session_state.students:
        section = s.get("section", "Unknown")
        section_distribution[section] = section_distribution.get(section, 0) + 1
    
    # Subject-wise performance
    subject_performance = {}
    for e in st.session_state.evaluations:
        if e.get("status") == "approved":
            subject = e.get("subject", "Unknown")
            score = e.get("overall_score", 0)
            if subject not in subject_performance:
                subject_performance[subject] = []
            subject_performance[subject].append(score)
    
    subject_averages = {}
    for subject, scores in subject_performance.items():
        subject_averages[subject] = round(sum(scores) / len(scores), 2) if scores else 0
    
    # Grade-wise performance
    grade_performance = {}
    for s in st.session_state.students:
        grade = s.get("grade", "Unknown")
        evals = get_approved_evaluations_for_student(s["id"])
        if evals:
            avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
            if grade not in grade_performance:
                grade_performance[grade] = []
            grade_performance[grade].append(avg_score)
    
    grade_averages = {}
    for grade, scores in grade_performance.items():
        grade_averages[grade] = round(sum(scores) / len(scores), 2) if scores else 0
    
    # Teacher workload
    teacher_workload = {}
    for t in st.session_state.teachers:
        teacher_id = t.get("id")
        batch_count = len([b for b in st.session_state.batches if b.get("teacher_id") == teacher_id])
        eval_count = len([e for e in st.session_state.evaluations if e.get("teacher_id") == teacher_id])
        teacher_workload[t.get("name", "Unknown")] = {
            "batches": batch_count,
            "evaluations": eval_count
        }
    
    # Pending approvals
    pending_batches = len(get_batches_awaiting_final_approval())
    
    # Overall pass rate (>=50%)
    passed = 0
    failed = 0
    for s in st.session_state.students:
        evals = get_approved_evaluations_for_student(s["id"])
        if evals:
            avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
            if avg_score >= 50:
                passed += 1
            else:
                failed += 1
    
    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_evaluations": total_evaluations,
        "total_batches": total_batches,
        "male_students": male_students,
        "female_students": female_students,
        "gender_ratio": f"{male_students}:{female_students}" if female_students > 0 else f"{male_students}:0",
        "grade_distribution": grade_distribution,
        "section_distribution": section_distribution,
        "subject_averages": subject_averages,
        "grade_averages": grade_averages,
        "teacher_workload": teacher_workload,
        "pending_batches": pending_batches,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / (passed + failed)) * 100, 1) if (passed + failed) > 0 else 0,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }

def generate_statistics_report():
    """Generate a formatted HTML report for office use."""
    stats = generate_school_statistics()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>School Statistics Report</title>
        <style>
            body {{ font-family: 'Segoe UI', 'Noto Sans Ethiopic', sans-serif; padding: 30px; background: #f8f9fa; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); }}
            h1 {{ color: #1A73E8; border-bottom: 3px solid #1A73E8; padding-bottom: 10px; }}
            h2 {{ color: #202124; margin-top: 25px; border-bottom: 2px solid #E8EAED; padding-bottom: 8px; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #E8F0FE; padding: 20px; border-radius: 12px; text-align: center; }}
            .stat-card .number {{ font-size: 2.5rem; font-weight: 700; color: #1A73E8; }}
            .stat-card .label {{ font-size: 0.9rem; color: #5F6368; }}
            table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            th, td {{ padding: 10px 12px; border: 1px solid #E8EAED; text-align: left; }}
            th {{ background: #F1F3F4; font-weight: 600; }}
            tr:nth-child(even) {{ background: #F8F9FA; }}
            .footer {{ margin-top: 30px; border-top: 2px solid #E8EAED; padding-top: 20px; color: #5F6368; text-align: center; font-size: 0.9rem; }}
            .badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
            .badge-green {{ background: #E6F4EA; color: #34A853; }}
            .badge-yellow {{ background: #FEF7E0; color: #F9AB00; }}
            .badge-red {{ background: #FCE8E6; color: #EA4335; }}
            .print-btn {{ background: #1A73E8; color: white; border: none; padding: 12px 30px; border-radius: 30px; font-size: 1rem; cursor: pointer; margin: 10px 0; }}
            .print-btn:hover {{ background: #1557B0; }}
            @media print {{ .no-print {{ display: none; }} body {{ background: white; padding: 15px; }} .container {{ box-shadow: none; border: 1px solid #ddd; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 School Statistical Report</h1>
        <p><strong>School:</strong> {st.session_state.school_name}</p>
        <p><strong>Report Generated:</strong> {stats['generated_at']}</p>
        
        <!-- Summary Stats -->
        <h2>📋 Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['total_students']}</div><div class="label">Total Students</div></div>
            <div class="stat-card"><div class="number">{stats['total_teachers']}</div><div class="label">Total Teachers</div></div>
            <div class="stat-card"><div class="number">{stats['total_evaluations']}</div><div class="label">Approved Evaluations</div></div>
            <div class="stat-card"><div class="number">{stats['total_batches']}</div><div class="label">Total Batches</div></div>
            <div class="stat-card"><div class="number">{stats['pending_batches']}</div><div class="label">Pending Approvals</div></div>
            <div class="stat-card"><div class="number">{stats['pass_rate']}%</div><div class="label">Overall Pass Rate</div></div>
        </div>
        
        <!-- Gender Distribution -->
        <h2>👤 Gender Distribution</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['male_students']}</div><div class="label">Male Students</div></div>
            <div class="stat-card"><div class="number">{stats['female_students']}</div><div class="label">Female Students</div></div>
            <div class="stat-card"><div class="number">{stats['gender_ratio']}</div><div class="label">Male:Female Ratio</div></div>
        </div>
        
        <!-- Pass/Fail -->
        <h2>✅ Pass / Fail Status</h2>
        <div class="stats-grid">
            <div class="stat-card" style="background:#E6F4EA;"><div class="number" style="color:#34A853;">{stats['passed']}</div><div class="label">Passed</div></div>
            <div class="stat-card" style="background:#FCE8E6;"><div class="number" style="color:#EA4335;">{stats['failed']}</div><div class="label">Failed</div></div>
            <div class="stat-card"><div class="number">{stats['pass_rate']}%</div><div class="label">Pass Rate</div></div>
        </div>
        
        <!-- Grade Distribution -->
        <h2>📚 Grade Distribution</h2>
        <table>
            <thead><tr><th>Grade</th><th>Students</th><th>% of Total</th></tr></thead>
            <tbody>
"""
    total = stats['total_students']
    for grade, count in sorted(stats['grade_distribution'].items()):
        pct = round((count / total) * 100, 1) if total > 0 else 0
        html += f"<tr><td>{grade}</td><td>{count}</td><td>{pct}%</td></tr>"
    html += """
            </tbody>
        </table>
        
        <!-- Section Distribution -->
        <h2>📌 Section Distribution</h2>
        <table>
            <thead><tr><th>Section</th><th>Students</th><th>% of Total</th></tr></thead>
            <tbody>
"""
    for section, count in sorted(stats['section_distribution'].items()):
        pct = round((count / total) * 100, 1) if total > 0 else 0
        html += f"<tr><td>{section}</td><td>{count}</td><td>{pct}%</td></tr>"
    html += """
            </tbody>
        </table>
        
        <!-- Subject Performance -->
        <h2>📖 Subject Performance Averages</h2>
        <table>
            <thead><tr><th>Subject</th><th>Average Score (%)</th><th>Performance</th></tr></thead>
            <tbody>
"""
    for subject, avg in sorted(stats['subject_averages'].items(), key=lambda x: x[1], reverse=True):
        badge = "badge-green" if avg >= 70 else "badge-yellow" if avg >= 50 else "badge-red"
        html += f"<tr><td>{subject}</td><td>{avg}%</td><td><span class='badge {badge}'>{'🌟 Excellent' if avg >= 70 else '📈 Good' if avg >= 50 else '📉 Needs Improvement'}</span></td></tr>"
    html += """
            </tbody>
        </table>
        
        <!-- Grade Performance -->
        <h2>🎓 Grade-wise Performance</h2>
        <table>
            <thead><tr><th>Grade</th><th>Average Score (%)</th></tr></thead>
            <tbody>
"""
    for grade, avg in sorted(stats['grade_averages'].items()):
        html += f"<tr><td>{grade}</td><td>{avg}%</td></tr>"
    html += """
            </tbody>
        </table>
        
        <!-- Teacher Workload -->
        <h2>👨‍🏫 Teacher Workload</h2>
        <table>
            <thead><tr><th>Teacher</th><th>Batches</th><th>Evaluations</th></tr></thead>
            <tbody>
"""
    for teacher, workload in sorted(stats['teacher_workload'].items()):
        html += f"<tr><td>{teacher}</td><td>{workload['batches']}</td><td>{workload['evaluations']}</td></tr>"
    html += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p>Report generated by School Registration Portal</p>
            <p>© {datetime.now().year} {st.session_state.school_name} - All Rights Reserved</p>
        </div>
    </div>
    
    <div style="text-align:center;margin:20px 0;" class="no-print">
        <button onclick="window.print()" class="print-btn">🖨️ Print / Save as PDF</button>
    </div>
</body>
</html>
"""
    return html

# ===================================================================
# SELF-SERVICE PROFILE UPDATE
# ===================================================================

def show_profile_update():
    """Allow users to update their own username and password."""
    st.markdown("### 👤 My Profile Settings")
    
    current_username = st.session_state.current_user
    user_data = st.session_state.user_db.get(current_username, {})
    display_name = user_data.get("name", current_username.title())
    
    # Display current profile
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(display_profile_photo(current_username, 120), unsafe_allow_html=True)
        
        # Photo upload
        uploaded_file = st.file_uploader(
            "📸 Update Profile Photo",
            type=["jpg", "jpeg", "png"],
            key="profile_photo_upload"
        )
        if uploaded_file:
            try:
                img = Image.open(uploaded_file)
                # Resize to reasonable size
                img.thumbnail((300, 300))
                img_bytes = io.BytesIO()
                img.save(img_bytes, format='PNG')
                photo_data = img_bytes.getvalue()
                encoded = base64.b64encode(photo_data).decode('utf-8')
                
                # Update Supabase
                supabase_admin = get_supabase_admin()
                try:
                    supabase_admin.table("users").update({"profile_photo": encoded}).eq("username", current_username).execute()
                    st.session_state.user_db[current_username]["profile_photo"] = encoded
                    st.success("✅ Profile photo updated!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to update photo: {e}")
            except Exception as e:
                st.error(f"Error processing image: {e}")
    
    with col2:
        st.markdown(f"**Name:** {display_name}")
        st.markdown(f"**Username:** {current_username}")
        st.markdown(f"**Role:** {user_data.get('role', 'unknown').title()}")
    
    st.markdown("---")
    
    # Update username
    with st.expander("✏️ Change Username", expanded=False):
        st.warning("⚠️ Changing your username will affect your login credentials.")
        new_username = st.text_input("New Username", value=current_username)
        if new_username != current_username:
            if st.button("Update Username", key="update_username"):
                if not new_username or len(new_username) < 3:
                    st.error("Username must be at least 3 characters.")
                elif is_username_taken(new_username):
                    st.error("Username already taken. Please choose another.")
                else:
                    supabase_admin = get_supabase_admin()
                    try:
                        # Update users table
                        supabase_admin.table("users").update({"username": new_username}).eq("username", current_username).execute()
                        # Update teachers table if applicable
                        for t in st.session_state.teachers:
                            if t.get("username") == current_username:
                                supabase_admin.table("teachers").update({"username": new_username}).eq("id", t["id"]).execute()
                        # Update session
                        st.session_state.user_db[new_username] = st.session_state.user_db.pop(current_username)
                        st.session_state.current_user = new_username
                        add_notification(f"Username changed from {current_username} to {new_username}", "info")
                        st.success(f"✅ Username updated to {new_username}! Please log in again.")
                        logout_user()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update username: {e}")
    
    # Update password
    with st.expander("🔐 Change Password", expanded=False):
        with st.form("change_password_form"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password"):
                if not verify_password(current_pw, user_data["password"]):
                    st.error("❌ Current password is incorrect.")
                elif len(new_pw) < 6:
                    st.error("New password must be at least 6 characters.")
                elif new_pw != confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    supabase_admin = get_supabase_admin()
                    try:
                        hashed = hash_password(new_pw)
                        supabase_admin.table("users").update({"password": hashed}).eq("username", current_username).execute()
                        st.session_state.user_db[current_username]["password"] = hashed
                        add_notification("Password changed successfully", "success")
                        st.success("✅ Password updated successfully!")
                    except Exception as e:
                        st.error(f"Failed to update password: {e}")

# ===================================================================
# CSS (Full)
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

    .approval-card {
        background: #FFFFFF !important;
        border: 2px solid #E8EAED;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s;
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

    .login-container {
        max-width: 500px;
        margin: 3rem auto;
        padding: 2.5rem;
        background: #FFFFFF !important;
        border: 1px solid #E8EAED;
        border-radius: 16px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    }

    @media (max-width: 768px) {
        .block-container { padding: 0.5rem 0.75rem !important; }
        .main-header .logo-text h1 { font-size: 1.8rem !important; }
        .main-header .header-stats .stat-item { min-width: 60px !important; padding: 8px 12px !important; }
        .main-header .header-stats .stat-item .number { font-size: 1.2rem !important; }
    }
</style>
""", unsafe_allow_html=True)

# ===================================================================
# CELEBRATION PAGE
# ===================================================================

def is_celebration_period():
    today = datetime.now()
    m, d = today.month, today.day
    if m == 8 and d >= 21:
        return True
    if m == 9 and d <= 30:
        return True
    return False

def show_celebration_page():
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
            cursor: pointer;
        }
        .celebration-btn:hover {
            transform: scale(1.05);
            background: #EF3340;
            color: #FCD116;
        }
        @media (max-width: 768px) {
            .celebration-title { font-size: 2.2rem; padding: 0.5rem 1rem; }
            .celebration-btn { font-size: 1.2rem; padding: 0.7rem 2rem; }
        }
    </style>
    """, unsafe_allow_html=True)

    html = f"""
    <div class="celebration-wrapper">
        <div style="position:absolute;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.2);z-index:5;"></div>
        <div class="celebration-content">
            <div style="font-size:4rem;">🇪🇹 🎉 🎊</div>
            <div class="celebration-title">እንኳን ለኢትዮጲያ ዘመን መለዎጫ በዓል አደረሳችሁ!🎉</div>
            <div style="font-size:2rem;background:rgba(0,0,0,0.2);padding:0.5rem 2rem;border-radius:30px;display:inline-block;">
                መልካም አዲስ ዓመት! Happy Ethiopian New Year!
            </div>
            <br>
            <a href="?celebration_dismissed=true" class="celebration-btn">🚪 Enter Portal</a>
        </div>
    </div>
    """
    
    try:
        st.html(html)
    except AttributeError:
        st.components.v1.html(html, height=800, scrolling=False)

# ===================================================================
# ADMIN PANEL (Enhanced)
# ===================================================================

def show_admin_panel():
    st.markdown("### 👨‍💼 Admin Dashboard")
    
    # Profile Update tab added
    tab0, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14 = st.tabs([
        "👤 My Profile",
        "📊 Overview",
        "⏰ Registration",
        "👨‍🏫 Teachers",
        "📚 Subjects",
        "📋 All Data",
        "✅ Approvals",
        "📊 Rankings",
        "👨‍🎓 Students",
        "📥 Import/Export",
        "📄 Reports",
        "⚠️ Penalty Log",
        "🏫 Settings",
        "👨‍🏫 Homeroom",
        "🎓 Student Cards"
    ])
    
    # --- Tab 0: My Profile ---
    with tab0:
        show_profile_update()
    
    # --- Tab 1: Overview ---
    with tab1:
        st.markdown("#### Dashboard Overview")
        stats = generate_school_statistics()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("👨‍🎓 Students", stats['total_students'])
        with col2: st.metric("👨‍🏫 Teachers", stats['total_teachers'])
        with col3: st.metric("📋 Subjects", len(st.session_state.subjects))
        with col4: st.metric("📝 Evaluations", stats['total_evaluations'])
        with col5: st.metric("⏳ Pending", stats['pending_batches'])
        with col6: st.metric("📈 Pass Rate", f"{stats['pass_rate']}%")
        
        # Status indicators
        if is_registration_open():
            st.success("🟢 Registration is currently **OPEN**")
        else:
            st.error("🔴 Registration is currently **CLOSED**")
        
        # Quick stats
        st.markdown("#### 📊 Quick Statistics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"**Gender Distribution:**")
            st.markdown(f"👨 Male: {stats['male_students']}")
            st.markdown(f"👩 Female: {stats['female_students']}")
        with col2:
            st.markdown(f"**Pass/Fail:**")
            st.markdown(f"✅ Passed: {stats['passed']}")
            st.markdown(f"❌ Failed: {stats['failed']}")
        with col3:
            st.markdown(f"**Teachers:**")
            st.markdown(f"👨‍🏫 Total: {stats['total_teachers']}")
            st.markdown(f"📦 Batches: {stats['total_batches']}")
    
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
                add_notification(f"Registration period updated", "info")
                st.success("✅ Registration period updated successfully!")
                st.rerun()
    
    # --- Tab 3: Teachers ---
    with tab3:
        st.markdown("#### 👨‍🏫 Manage Teachers")
        
        # Add Teacher Form (simplified - full version in existing code)
        with st.form("add_teacher"):
            teacher_name = st.text_input("Teacher Full Name *", placeholder="e.g., Abebe Kebede")
            teacher_subject = st.selectbox("Subject Taught *", ALL_SUBJECTS)
            teacher_email = st.text_input("Email Address", placeholder="teacher@school.edu")
            teacher_admin_subjects = st.multiselect(
                "Subjects this teacher administers (leave empty for regular teacher)",
                options=ALL_SUBJECTS,
                default=[]
            )
            
            if st.form_submit_button("➕ Add Teacher", width='stretch'):
                if teacher_name:
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
                    role = "subject_admin" if teacher_admin_subjects else "teacher"
                    
                    supabase_admin = get_supabase_admin()
                    try:
                        supabase_admin.table("users").insert({
                            "username": username,
                            "password": hashed_pw,
                            "role": role,
                            "name": teacher_name,
                            "profile_photo": ""
                        }).execute()
                        supabase_admin.table("teachers").insert({
                            "id": teacher_id,
                            "name": teacher_name,
                            "subject": teacher_subject,
                            "email": teacher_email,
                            "username": username,
                            "password": password,
                            "added": added_time,
                            "assignments": "[]",
                            "admin_subjects": json.dumps(teacher_admin_subjects)
                        }).execute()
                        load_all_data()
                        add_notification(f"👨‍🏫 New teacher added: {teacher_name}", "success")
                        st.success(f"""
                        ✅ Teacher {teacher_name} added successfully!
                        **Username:** `{username}`
                        **Password:** `{password}`
                        **Role:** {role.title()}
                        """)
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding teacher: {e}")
                else:
                    st.error("❌ Please enter teacher name.")
        
        # List teachers
        if st.session_state.teachers:
            st.markdown("#### 📋 All Teachers")
            for t in st.session_state.teachers:
                admin_subjects = json.loads(t.get("admin_subjects", "[]"))
                admin_str = ", ".join(admin_subjects) if admin_subjects else "None"
                st.markdown(f"""
                <div class="teacher-card">
                    <h4>👨‍🏫 {t['name']}</h4>
                    <p><b>📚 Subject:</b> {t['subject']}</p>
                    <p><b>🔐 Admin Subjects:</b> {admin_str}</p>
                    <p><b>👤 Username:</b> <code>{t.get('username', 'N/A')}</code></p>
                </div>
                """, unsafe_allow_html=True)
    
    # --- Tab 4: Subjects ---
    with tab4:
        st.markdown("#### 📚 Manage Subjects")
        current_subjects = [s if isinstance(s, str) else s.get("name", "") for s in st.session_state.subjects]
        if current_subjects:
            st.markdown("**Current Subjects:**")
            cols = st.columns(4)
            for i, subj in enumerate(current_subjects):
                cols[i % 4].markdown(f"- 📘 {subj}")
        
        with st.form("add_subject"):
            new_subject = st.text_input("New Subject Name")
            if st.form_submit_button("➕ Add Subject", width='stretch'):
                if new_subject and new_subject not in current_subjects:
                    st.session_state.subjects.append(new_subject)
                    add_notification(f"📚 New subject added: {new_subject}", "info")
                    st.success(f"✅ Subject {new_subject} added!")
                    st.rerun()
                elif new_subject:
                    st.warning(f"⚠️ Subject '{new_subject}' already exists.")
    
    # --- Tab 5: All Data ---
    with tab5:
        st.markdown("#### 📋 All Data")
        if st.session_state.students:
            df = pd.DataFrame(st.session_state.students)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No students registered yet.")
    
    # --- Tab 6: Approvals ---
    with tab6:
        st.markdown("#### ✅ Pending Batches for Final Approval")
        pending_batches = get_batches_awaiting_final_approval()
        if not pending_batches:
            st.success("🎉 No pending batches awaiting final approval.")
        else:
            for batch in pending_batches:
                # Display batch info
                st.markdown(f"""
                <div class="approval-card pending">
                    <h4>📦 Batch from {batch.get('teacher_name', 'Unknown')} · {batch.get('subject', 'N/A')}</h4>
                    <p><b>Grade:</b> {batch.get('grade', 'N/A')} · <b>Section:</b> {batch.get('section', 'N/A')}</p>
                    <p><b>Students:</b> {len(batch.get('students', []))}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve", key=f"approve_{batch['id']}", width='stretch'):
                        # Process approval
                        supabase_admin = get_supabase_admin()
                        try:
                            res = supabase_admin.table("evaluations").select("id").order("id", desc=True).limit(1).execute()
                            num = int(res.data[0]["id"][1:]) + 1 if res.data else 1
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
                                "semester": batch.get("semester", "Semester I"),
                                "overall_score": student_entry.get("overall", 0),
                                "status": "approved",
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "batch_id": batch["id"]
                            }
                            supabase_admin.table("evaluations").insert(eval_item).execute()
                            num += 1
                        
                        supabase_admin.table("batches").update({"status": "approved"}).eq("id", batch["id"]).execute()
                        load_all_data()
                        add_notification(f"✅ Batch approved", "success")
                        st.balloons()
                        st.success("✅ Batch approved successfully!")
                        time.sleep(1)
                        st.rerun()
                with col2:
                    if st.button(f"❌ Reject", key=f"reject_{batch['id']}", width='stretch'):
                        supabase_admin = get_supabase_admin()
                        supabase_admin.table("batches").update({"status": "rejected"}).eq("id", batch["id"]).execute()
                        load_all_data()
                        st.warning("❌ Batch rejected!")
                        st.rerun()
    
    # --- Tab 7: Rankings ---
    with tab7:
        st.markdown("#### 📊 Grade Rankings")
        grade_options = [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, key="rank_grade")
        
        students_in_grade = [s for s in st.session_state.students if s.get("grade") == selected_grade]
        if not students_in_grade:
            st.info(f"No students in {selected_grade}")
        else:
            student_data = []
            for s in students_in_grade:
                evals = get_approved_evaluations_for_student(s["id"])
                avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2) if evals else 0
                student_data.append({"Name": s["name"], "Average": avg_score, "Evaluations": len(evals)})
            df = pd.DataFrame(student_data).sort_values("Average", ascending=False).reset_index(drop=True)
            df["Rank"] = df.index + 1
            st.dataframe(df[["Rank", "Name", "Average", "Evaluations"]], use_container_width=True, hide_index=True)
    
    # --- Tab 8: Students ---
    with tab8:
        st.markdown("#### 👨‍🎓 Student Management")
        with st.expander("➕ Add New Student", expanded=False):
            with st.form("add_student_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Full Name *")
                    age = st.number_input("Age", min_value=5, max_value=25, step=1)
                    grade = st.selectbox("Grade", [f"Grade {i}" for i in range(1, 13)])
                with col2:
                    gender = st.selectbox("Gender", ["M", "F", "Other"])
                    parent = st.text_input("Parent/Guardian")
                    section = st.text_input("Section", value="A")
                
                if st.form_submit_button("Add Student", width='stretch'):
                    if name:
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
                            "subjects": GRADE_SUBJECTS.get(grade, []),
                            "parent_name": parent,
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        supabase_admin = get_supabase_admin()
                        try:
                            supabase_admin.table("students").insert(new_student).execute()
                            load_all_data()
                            add_notification(f"👨‍🎓 Student {name} added", "success")
                            st.success(f"✅ Student {name} added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add student: {e}")
                    else:
                        st.error("Name is required.")
    
    # --- Tab 9: Import/Export ---
    with tab9:
        st.markdown("### 📥 Import / Export Data")
        uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df, use_container_width=True)
                if st.button("Import Students", width='stretch'):
                    # Simple import logic
                    supabase = get_supabase_admin()
                    count = 0
                    for _, row in df.iterrows():
                        if pd.notna(row.get("Name")):
                            existing_ids = [int(s['id'][1:]) for s in st.session_state.students if s['id'].startswith('S')]
                            next_num = max(existing_ids) + 1 if existing_ids else 1
                            student = {
                                "id": f"S{next_num:04d}",
                                "name": str(row.get("Name", "")),
                                "grade": str(row.get("Grade", "Grade 1")),
                                "section": str(row.get("Section", "A")),
                                "gender": str(row.get("Gender", "")),
                                "parent_name": str(row.get("Parent", "")),
                                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "subjects": GRADE_SUBJECTS.get(str(row.get("Grade", "Grade 1")), [])
                            }
                            supabase.table("students").insert(student).execute()
                            count += 1
                    load_all_data()
                    st.success(f"✅ Imported {count} students!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    # --- Tab 10: Reports ---
    with tab10:
        st.markdown("### 📄 School Reports")
        
        # Statistics Dashboard
        stats = generate_school_statistics()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("👨‍🎓 Total Students", stats['total_students'])
            st.metric("👨‍🏫 Total Teachers", stats['total_teachers'])
        with col2:
            st.metric("📝 Evaluations", stats['total_evaluations'])
            st.metric("📦 Batches", stats['total_batches'])
        with col3:
            st.metric("✅ Pass Rate", f"{stats['pass_rate']}%")
            st.metric("⏳ Pending", stats['pending_batches'])
        
        # Gender breakdown
        st.markdown("#### Gender Distribution")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"👨 Male: {stats['male_students']}")
        with col2:
            st.markdown(f"👩 Female: {stats['female_students']}")
        
        # Grade distribution
        st.markdown("#### Grade Distribution")
        if stats['grade_distribution']:
            df_grades = pd.DataFrame(stats['grade_distribution'].items(), columns=["Grade", "Students"])
            st.dataframe(df_grades, use_container_width=True, hide_index=True)
        
        # Subject performance
        st.markdown("#### Subject Performance")
        if stats['subject_averages']:
            df_subjects = pd.DataFrame(stats['subject_averages'].items(), columns=["Subject", "Average Score"])
            df_subjects = df_subjects.sort_values("Average Score", ascending=False)
            st.dataframe(df_subjects, use_container_width=True, hide_index=True)
        
        # Download Report
        html_report = generate_statistics_report()
        st.download_button(
            label="📥 Download Full Report (HTML)",
            data=html_report.encode('utf-8'),
            file_name=f"School_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            width='stretch'
        )
        
        # Excel Export
        if st.button("📥 Export Data to Excel", width='stretch'):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Students
                if st.session_state.students:
                    pd.DataFrame(st.session_state.students).to_excel(writer, sheet_name="Students", index=False)
                # Teachers
                if st.session_state.teachers:
                    pd.DataFrame(st.session_state.teachers).to_excel(writer, sheet_name="Teachers", index=False)
                # Evaluations
                if st.session_state.evaluations:
                    pd.DataFrame(st.session_state.evaluations).to_excel(writer, sheet_name="Evaluations", index=False)
                # Statistics
                stats_df = pd.DataFrame([stats])
                stats_df.to_excel(writer, sheet_name="Statistics", index=False)
            st.download_button(
                label="📥 Download Excel",
                data=output.getvalue(),
                file_name=f"School_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width='stretch'
            )
    
    # --- Tab 11: Penalty Log ---
    with tab11:
        show_penalty_log()
    
    # --- Tab 12: Settings ---
    with tab12:
        st.markdown("### 🏫 School Settings")
        new_name = st.text_input("School Name", value=st.session_state.school_name)
        new_city = st.text_input("City/Town", value=st.session_state.school_city)
        new_director = st.text_input("Director's Name", value=st.session_state.director_name)
        if st.button("💾 Update School Settings", width='stretch'):
            st.session_state.school_name = new_name
            st.session_state.school_city = new_city
            st.session_state.director_name = new_director
            st.success("✅ School settings updated!")
    
    # --- Tab 13: Homeroom ---
    with tab13:
        st.markdown("### 👨‍🏫 Homeroom Teacher Assignments")
        # Simple homeroom assignment view
        if st.session_state.homeroom_assignments:
            df = pd.DataFrame(st.session_state.homeroom_assignments)
            df["Teacher Name"] = df["teacher_id"].apply(get_teacher_name)
            st.dataframe(df[["grade", "section", "Teacher Name"]], use_container_width=True)
        else:
            st.info("No homeroom assignments yet.")
    
    # --- Tab 14: Student Cards ---
    with tab14:
        show_student_card_panel()

# ===================================================================
# STUDENT CARD GENERATION (Simplified)
# ===================================================================

def show_student_card_panel():
    st.markdown("### 🎓 Student Report Cards")
    st.info("📄 Generate a two-page landscape report card for each student.")
    
    col1, col2 = st.columns(2)
    with col1:
        grade_options = ["All"] + [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, index=0)
    with col2:
        semester_options = ["Semester I", "Semester II", "Semester III"]
        selected_semester = st.selectbox("Semester", semester_options, index=2)
    
    if selected_grade != "All":
        filtered_students = [s for s in st.session_state.students if s.get("grade") == selected_grade]
    else:
        filtered_students = st.session_state.students
    
    if not filtered_students:
        st.info("No students match the selection.")
        return
    
    st.markdown(f"**{len(filtered_students)} students found**")
    
    for student in filtered_students[:10]:  # Show first 10
        with st.expander(f"📄 {student['name']} - {student.get('grade', '')} {student.get('section', '')}"):
            # Simplified card preview
            evals = get_approved_evaluations_for_student(student["id"])
            avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2) if evals else 0
            
            st.markdown(f"""
            <div class="student-card">
                <h4>👤 {student['name']}</h4>
                <p><b>Grade:</b> {student.get('grade', 'N/A')}</p>
                <p><b>Section:</b> {student.get('section', 'N/A')}</p>
                <p><b>Average Score:</b> {avg_score}%</p>
                <p><b>Evaluations:</b> {len(evals)}</p>
            </div>
            """, unsafe_allow_html=True)

# ===================================================================
# PENALTY LOG
# ===================================================================

def show_penalty_log():
    st.markdown("### ⚠️ Penalty Log")
    if st.session_state.penalty_log:
        user_penalties = [p for p in st.session_state.penalty_log if p.get("user") == st.session_state.current_user]
        if user_penalties:
            st.markdown(f"""
            <div style="background:#FCE8E6;padding:1rem;border-radius:12px;border:2px solid #EA4335;margin-bottom:1rem;">
                <p style="color:#EA4335;font-weight:700;">⚠️ You have {len(user_penalties)} penalty record(s).</p>
            </div>
            """, unsafe_allow_html=True)
            df = pd.DataFrame(user_penalties)
            st.dataframe(df, use_container_width=True)
        else:
            st.success("✅ No penalties recorded.")
    else:
        st.success("✅ No penalties recorded in the system.")

# ===================================================================
# NOTIFICATION CENTER
# ===================================================================

def show_notification_center():
    unread = len([n for n in st.session_state.notifications if not n.get('read', False)])
    st.markdown("### 🔔 Notifications")
    if unread > 0:
        st.warning(f"📌 {unread} new notification(s)")
    
    if st.session_state.notifications:
        for note in st.session_state.notifications[:10]:
            unread_class = "unread" if not note.get('read', False) else ""
            st.markdown(f"""
            <div class="notification-item {unread_class}">
                <strong>{note['message']}</strong>
                <div class="notification-time">⏱ {note['time']}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No notifications")

# ===================================================================
# SUBJECT ADMIN PANEL
# ===================================================================

def show_subject_admin_panel():
    st.markdown("### 📋 Subject Admin Dashboard")
    
    teacher = get_teacher_by_username(st.session_state.current_user)
    if not teacher:
        st.error("Subject admin profile not found.")
        return
    
    my_pending_batches = get_batches_for_subject_admin(teacher["id"])
    
    if not my_pending_batches:
        st.success("🎉 No pending batches for your subjects.")
        return
    
    for batch in my_pending_batches:
        st.markdown(f"""
        <div class="approval-card pending">
            <h4>📦 Batch from {batch.get('teacher_name', 'Unknown')} · {batch.get('subject', 'N/A')}</h4>
            <p><b>Grade:</b> {batch.get('grade', 'N/A')} · <b>Section:</b> {batch.get('section', 'N/A')}</p>
            <p><b>Students:</b> {len(batch.get('students', []))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Approve", key=f"subj_approve_{batch['id']}", width='stretch'):
                supabase_admin = get_supabase_admin()
                supabase_admin.table("batches").update({"status": "subject_approved"}).eq("id", batch["id"]).execute()
                load_all_data()
                add_notification(f"Batch approved by subject admin", "success")
                st.balloons()
                st.success("✅ Batch approved!")
                time.sleep(1)
                st.rerun()
        with col2:
            if st.button(f"❌ Reject", key=f"subj_reject_{batch['id']}", width='stretch'):
                supabase_admin = get_supabase_admin()
                supabase_admin.table("batches").update({"status": "rejected"}).eq("id", batch["id"]).execute()
                load_all_data()
                st.warning("❌ Batch rejected!")
                st.rerun()

# ===================================================================
# TEACHER PANEL (with real assessment weights)
# ===================================================================

def show_teacher_panel():
    st.markdown("### 👨‍🏫 Teacher Dashboard")
    
    teacher = get_teacher_by_username(st.session_state.current_user)
    if not teacher:
        st.error("❌ Teacher profile not found.")
        return
    
    teacher_id = teacher["id"]
    teacher_name = teacher["name"]
    teacher_subject = teacher.get("subject", "")
    assignments = json.loads(teacher.get("assignments", "[]"))
    
    if not assignments:
        st.warning("No grade/section assignments. Contact admin.")
        return
    
    # Select semester and grade
    available_semesters = sorted(set([a.get("semester", "Semester I") for a in assignments]))
    selected_semester = st.selectbox("📚 Select Semester", available_semesters, key="teacher_semester")
    
    semester_assignments = [a for a in assignments if a.get("semester") == selected_semester]
    assigned_grades = list(set([a["grade"] for a in semester_assignments]))
    if not assigned_grades:
        st.warning(f"No assignments for {selected_semester}")
        return
    
    selected_grade = st.selectbox("📚 Select Grade", assigned_grades, key="grade_selector")
    assigned_sections = [a["section"] for a in semester_assignments if a["grade"] == selected_grade]
    selected_section = st.selectbox("📚 Select Section", assigned_sections, key="section_selector")
    
    # Get assessment config for this grade
    assessment_config = get_assessment_config(selected_grade)
    components = assessment_config["components"]
    weights = {c["name"]: c["weight"] for c in components}
    max_scores = {c["name"]: c["max_score"] for c in components}
    
    st.markdown(f"""
    <div style="background:#E8F0FE;padding:1rem;border-radius:12px;margin-bottom:1rem;">
        <h4 style="margin:0;color:#1A73E8;">👨‍🏫 {teacher_name}</h4>
        <p><b>📚 Subject:</b> {teacher_subject}</p>
        <p><b>📋 Grade:</b> {selected_grade} · <b>Section:</b> {selected_section} · <b>Semester:</b> {selected_semester}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show assessment components
    st.markdown("#### 📋 Assessment Components")
    comp_df = pd.DataFrame(components)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
    
    # Get eligible students
    eligible_students = [s for s in st.session_state.students 
                         if s.get("grade") == selected_grade and s.get("section") == selected_section
                         and teacher_subject in s.get("subjects", [])]
    
    if not eligible_students:
        st.info(f"No students in {selected_grade} ({selected_section}) taking {teacher_subject}.")
        return
    
    # Check existing batch
    existing_batch = None
    for b in st.session_state.batches:
        if (b.get("teacher_id") == teacher_id and
            b.get("grade") == selected_grade and
            b.get("section") == selected_section and
            b.get("subject") == teacher_subject and
            b.get("semester") == selected_semester and
            b.get("status") in ["pending", "subject_approved"]):
            existing_batch = b
            break
    
    # Prepare student data
    if existing_batch:
        student_data = existing_batch["students"]
        remarks = existing_batch.get("remarks", DEFAULT_REMARKS)
    else:
        student_data = []
        for s in eligible_students:
            student_entry = {"student_id": s["id"], "student_name": s["name"]}
            for c in components:
                student_entry[c["name"]] = 0
            student_entry["overall"] = 0
            student_data.append(student_entry)
        remarks = DEFAULT_REMARKS
    
    # Data editor with component columns
    st.markdown("#### ✏️ Enter Scores")
    df_edit = pd.DataFrame(student_data)
    
    # Build column config
    col_config = {
        "student_id": st.column_config.TextColumn("ID", disabled=True),
        "student_name": st.column_config.TextColumn("Student Name", disabled=True),
        "overall": st.column_config.NumberColumn("Overall (%)", disabled=True, format="%.1f%%")
    }
    for c in components:
        max_val = c["max_score"]
        col_config[c["name"]] = st.column_config.NumberColumn(
            f"{c['name']} (max {max_val})",
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
    
    # Compute overall scores
    for idx, row in edited_df.iterrows():
        total_weighted = 0
        total_weight = 0
        for c in components:
            score = row.get(c["name"], 0)
            total_weighted += score * weights[c["name"]]
            total_weight += weights[c["name"]]
        edited_df.at[idx, "overall"] = round(total_weighted / total_weight, 2) if total_weight > 0 else 0
    
    # Remarks
    remarks = st.text_area("Batch Remarks / Comments", value=remarks)
    
    # Submit button
    if st.button("💾 Submit Batch for Approval", width='stretch'):
        if not is_registration_open():
            st.error("⚠️ Registration period is closed. Cannot submit.")
        else:
            students_list = edited_df.to_dict(orient="records")
            subject_admin_id = get_subject_admin(teacher_subject)
            
            batch_data = {
                "teacher_id": teacher_id,
                "teacher_name": teacher_name,
                "grade": selected_grade,
                "section": selected_section,
                "semester": selected_semester,
                "subject": teacher_subject,
                "students": students_list,
                "weights": weights,
                "max_scores": max_scores,
                "remarks": remarks,
                "status": "pending",
                "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "subject_admin_id": subject_admin_id
            }
            
            supabase_admin = get_supabase_admin()
            try:
                if existing_batch:
                    supabase_admin.table("batches").update(batch_data).eq("id", existing_batch["id"]).execute()
                else:
                    batch_data["id"] = str(uuid.uuid4())[:8]
                    supabase_admin.table("batches").insert(batch_data).execute()
                load_all_data()
                add_notification(f"📦 Batch submitted by {teacher_name}", "info")
                st.balloons()
                st.success("✅ Batch submitted successfully!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to submit: {e}")

# ===================================================================
# LOGIN PAGE
# ===================================================================

def show_login_page():
    st.markdown("""
    <div style="text-align:center; padding:1rem 0;">
        <div style="font-size:4rem; margin-bottom:0.5rem;">📚✍️🌍SRP🏫ET</div>
        <h1 style="font-size:3rem; margin:0;">School Registration Portal</h1>
        <p style="color:#5F6368; font-size:1.2rem;">👨‍🏫📚 Admin-Controlled Student & Teacher Management</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username")
            password = st.text_input("🔐 Password", type="password", placeholder="Enter password")
            
            if st.form_submit_button("🇪🇹 Sign In", width='stretch'):
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("❌ Please enter both username and password.")
        st.markdown('</div>', unsafe_allow_html=True)

# ===================================================================
# MAIN# ===================================================================

def main():
    init_user_db()
    
    # Handle celebration dismissal
    if st.query_params.get("celebration_dismissed"):
        st.session_state.celebration_dismissed = True
        st.query_params.clear()
        st.rerun()
    
    if not st.session_state.logged_in:
        if is_celebration_period() and not st.session_state.get("celebration_dismissed", False):
            show_celebration_page()
            return
        else:
            show_login_page()
            return
    
    # Sidebar
    current_user = st.session_state.current_user
    role = st.session_state.current_role
    user_data = st.session_state.user_db.get(current_user, {})
    display_name = user_data.get("name", current_user.title())
    
    with st.sidebar:
        st.markdown("### School Portal")
        st.markdown("---")
        
        # Profile photo
        st.markdown(display_profile_photo(current_user, 80), unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center;margin:8px 0;">
            <p style="font-weight:600;color:#1A73E8;">{display_name}</p>
            <p style="font-size:0.85rem;color:#5F6368;">@{current_user} · {role.title()}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Navigation
        if role == "admin":
            nav_options = [
                "👤 My Profile",
                "📊 Dashboard",
                "👨‍🏫 Teachers",
                "👨‍🎓 Students",
                "✅ Approvals",
                "📄 Reports",
                "⚠️ Penalty Log",
                "🔔 Notifications"
            ]
        elif role == "subject_admin":
            nav_options = ["👤 My Profile", "📋 Subject Admin", "⚠️ Penalties", "🔔 Notifications"]
        elif role == "teacher":
            nav_options = ["👤 My Profile", "👨‍🏫 My Dashboard", "⚠️ Penalties", "🔔 Notifications"]
        else:
            nav_options = ["👤 My Profile", "⚠️ Penalties", "🔔 Notifications"]
        
        selected_page = st.radio("Navigation", nav_options, index=0)
        st.session_state.current_page = selected_page
        
        if st.button("🚪 Logout", width='stretch'):
            logout_user()
            st.rerun()
        
        st.markdown("---")
        st.markdown("🏫 School Registration Portal")
        st.markdown("*Berhanu Mekonen, PhD*")
        st.markdown("*Arba Minch University*")
    
    # Header
    total_students = len(st.session_state.students)
    total_teachers = len(st.session_state.teachers)
    pending_batches = len(get_batches_awaiting_final_approval())
    
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
                </div>
            </div>
            <div class="header-right">
                <div class="header-stats">
                    <div class="stat-item"><span class="number">{total_students}</span><span class="label">Students</span></div>
                    <div class="stat-item"><span class="number">{total_teachers}</span><span class="label">Teachers</span></div>
                    <div class="stat-item"><span class="number" style="color:#FBBC04;">{pending_batches}</span><span class="label">Pending</span></div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Status bar
    if is_registration_open():
        dot_class = "online"
        status_text = "OPEN · Registration active"
    else:
        dot_class = "offline"
        status_text = "CLOSED · Penalties apply"
    st.markdown(f"""
    <div class="status-bar">
        <div>
            <span class="status-dot {dot_class}"></span>
            <span class="status-text">Status: {status_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Routing
    current_page = getattr(st.session_state, 'current_page', "📊 Dashboard")
    
    if role == "admin":
        if current_page == "👤 My Profile":
            show_profile_update()
        elif current_page == "📊 Dashboard":
            show_admin_panel()
        elif current_page == "👨‍🏫 Teachers":
            st.markdown("### 👨‍🏫 Teacher Management")
            st.info("Use the Admin Dashboard → Teachers tab for full management.")
        elif current_page == "👨‍🎓 Students":
            st.markdown("### 👨‍🎓 Student Management")
            st.info("Use the Admin Dashboard → Students tab for full management.")
        elif current_page == "✅ Approvals":
            st.markdown("### ✅ Approvals")
            st.info("Use the Admin Dashboard → Approvals tab.")
        elif current_page == "📄 Reports":
            st.markdown("### 📄 Reports")
            st.info("Use the Admin Dashboard → Reports tab.")
        elif current_page == "⚠️ Penalty Log":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()
    
    elif role == "subject_admin":
        if current_page == "👤 My Profile":
            show_profile_update()
        elif current_page == "📋 Subject Admin":
            show_subject_admin_panel()
        elif current_page == "⚠️ Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()
    
    elif role == "teacher":
        if current_page == "👤 My Profile":
            show_profile_update()
        elif current_page == "👨‍🏫 My Dashboard":
            show_teacher_panel()
        elif current_page == "⚠️ Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()
    
    else:
        if current_page == "👤 My Profile":
            show_profile_update()
        elif current_page == "⚠️ Penalties":
            show_penalty_log()
        elif current_page == "🔔 Notifications":
            show_notification_center()

if __name__ == "__main__":
    main()
