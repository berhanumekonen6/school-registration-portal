# ===================================================================
# SCHOOL REGISTRATION PORTAL - PERSISTENT WITH SUPABASE
# Enhanced with Real Assessment Weights, Profile Photos, Stats & Self-Service
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

# Try to import plotly, fallback if not installed
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# ===================================================================
# DEFAULT REMARKS TEXT
# ===================================================================
DEFAULT_REMARKS = "በአጠቃላይ የተማሪዎች ውጤት ጥሩ ነው፣ ነገር ግን የበለጠ ለማድረግ ከትምህርት ቤቱ ማህበረሰብ ተጨማሪ ጥረት ያስፈልጋል።"

# ===================================================================
# REAL ASSESSMENT WEIGHTS PER GRADE (Ethiopian School System)
# ===================================================================

GRADE_ASSESSMENT_CONFIG = {
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
    "Grade 1": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 2": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 3": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 4": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 5": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "ጋሞኛ", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"],
    "Grade 6": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "ጋሞኛ", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"],
    "Grade 7": ["አማርኛ", "ግዕዝ", "English (G)", "Mathematics", "G/Science", "Citizenship", "Social study", "Gammogna", "P.V.A", "I.T", "C.T.E", "H.P.E"],
    "Grade 8": ["አማርኛ", "ግዕዝ", "English (G)", "Mathematics", "G/Science", "Citizenship", "Social study", "Gammogna", "P.V.A", "I.T", "C.T.E", "H.P.E"],
    "Grade 9": ["English", "Mathematics", "Physics", "Chemistry", "Biology", "Geography", "History", "Citizenship Education (CE)", "Information Technology (IT)", "አማርኛ", "Health and Physical Education (HPE)"],
    "Grade 10": ["English", "Mathematics", "Physics", "Chemistry", "Biology", "Geography", "History", "Citizenship Education (CE)", "Information Technology (IT)", "አማርኛ", "Health and Physical Education (HPE)"],
    "Grade 11": ["Biology", "Chemistry", "Physics", "Technical Drawing", "Mathematics", "English", "Information Technology (IT)", "Citizenship Education / Civics", "Geography", "History", "Economics", "General Business"],
    "Grade 12": ["Biology", "Chemistry", "Physics", "Technical Drawing", "Mathematics", "English", "Information Technology (IT)", "Citizenship Education / Civics", "Geography", "History", "Economics", "General Business"],
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

# ---- Data Load with Error Handling ----
def load_all_data():
    supabase = get_supabase()
    
    try:
        res = supabase.table("students").select("*").execute()
        st.session_state.students = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load students: {e}")
        st.session_state.students = []
    
    try:
        res = supabase.table("teachers").select("*").execute()
        st.session_state.teachers = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load teachers: {e}")
        st.session_state.teachers = []
    
    try:
        res = supabase.table("evaluations").select("*").execute()
        st.session_state.evaluations = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load evaluations: {e}")
        st.session_state.evaluations = []
    
    try:
        res = supabase.table("batches").select("*").execute()
        st.session_state.batches = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load batches: {e}")
        st.session_state.batches = []
    
    try:
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
    except Exception as e:
        st.warning(f"Could not load users: {e}")
        st.session_state.user_db = {}
    
    try:
        res = supabase.table("notifications").select("*").order("id", desc=True).execute()
        st.session_state.notifications = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load notifications: {e}")
        st.session_state.notifications = []
    
    try:
        res = supabase.table("penalty_log").select("*").order("id", desc=True).execute()
        st.session_state.penalty_log = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load penalty_log: {e}")
        st.session_state.penalty_log = []
    
    try:
        res = supabase.table("homeroom_assignments").select("*").execute()
        st.session_state.homeroom_assignments = res.data if res.data else []
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg or "Could not find the table" in error_msg:
            st.warning("⚠️ Homeroom Assignments table not found. Please create it in Supabase.")
            st.session_state.homeroom_assignments = []
        else:
            st.warning(f"Could not load homeroom_assignments: {e}")
            st.session_state.homeroom_assignments = []
    
    try:
        res = supabase.table("subject_admin_assignments").select("*").execute()
        st.session_state.subject_admin_assignments = res.data if res.data else []
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg or "Could not find the table" in error_msg:
            st.warning("⚠️ Subject Admin Assignments table not found. Please create it in Supabase.")
            st.session_state.subject_admin_assignments = []
        else:
            st.warning(f"Could not load subject_admin_assignments: {e}")
            st.session_state.subject_admin_assignments = []

# ---- Assessment Helper Functions ----
def get_assessment_config(grade):
    return GRADE_ASSESSMENT_CONFIG.get(grade, GRADE_ASSESSMENT_CONFIG["Grade 1"])

def get_component_names(grade):
    config = get_assessment_config(grade)
    return [c["name"] for c in config["components"]]

def get_component_weights(grade):
    config = get_assessment_config(grade)
    return {c["name"]: c["weight"] for c in config["components"]}

def get_component_max_scores(grade):
    config = get_assessment_config(grade)
    return {c["name"]: c["max_score"] for c in config["components"]}

def compute_overall_from_components(scores_dict, grade):
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
    if not photo_bytes:
        return ""
    try:
        img = Image.open(io.BytesIO(photo_bytes))
        img.thumbnail((300, 300))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        encoded = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        
        supabase_admin = get_supabase_admin()
        try:
            supabase_admin.table("users").update({"profile_photo": encoded}).eq("username", username).execute()
            if username in st.session_state.user_db:
                st.session_state.user_db[username]["profile_photo"] = encoded
            return encoded
        except Exception as e:
            if "PGRST204" in str(e):
                st.warning("⚠️ Profile photo column not found. Please add: ALTER TABLE users ADD COLUMN profile_photo TEXT;")
            return ""
    except Exception as e:
        st.error(f"Error saving photo: {e}")
        return ""

def get_profile_photo(username):
    user_data = st.session_state.user_db.get(username, {})
    return user_data.get("profile_photo", "")

def display_profile_photo(username, size=80):
    photo_data = get_profile_photo(username)
    if photo_data and len(photo_data) > 10:
        return f'<img src="data:image/png;base64,{photo_data}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #1A73E8;">'
    else:
        initial = username[0].upper() if username else "U"
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#1A73E8,#4285F4);display:flex;align-items:center;justify-content:center;font-size:{size//2.5}px;color:white;font-weight:700;border:2px solid #1A73E8;">{initial}</div>'

# ---- Student Profile Photo Helpers ----
def save_student_photo(student_id, photo_bytes):
    if not photo_bytes:
        return ""
    try:
        img = Image.open(io.BytesIO(photo_bytes))
        img.thumbnail((300, 300))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        encoded = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
        
        supabase_admin = get_supabase_admin()
        try:
            supabase_admin.table("students").update({"profile_photo": encoded}).eq("id", student_id).execute()
            for s in st.session_state.students:
                if s["id"] == student_id:
                    s["profile_photo"] = encoded
                    break
            return encoded
        except Exception as e:
            if "PGRST204" in str(e):
                st.warning("⚠️ Profile photo column not found in students table. Please add: ALTER TABLE students ADD COLUMN profile_photo TEXT;")
            return ""
    except Exception as e:
        st.error(f"Error saving student photo: {e}")
        return ""

def get_student_photo(student_id):
    for s in st.session_state.students:
        if s.get("id") == student_id:
            return s.get("profile_photo", "")
    return ""

def display_student_photo(student_id, size=80):
    photo_data = get_student_photo(student_id)
    if photo_data and len(photo_data) > 10:
        return f'<img src="data:image/png;base64,{photo_data}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #34A853;">'
    else:
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:#E8F0FE;display:flex;align-items:center;justify-content:center;font-size:{size//2.5}px;color:#34A853;border:2px solid #34A853;">👤</div>'

# ---- Student Login Functions ----
def create_student_user(student_id, student_name):
    username = student_id
    password = generate_random_password(8)
    hashed_pw = hash_password(password)
    
    supabase_admin = get_supabase_admin()
    try:
        res = supabase_admin.table("users").select("username").eq("username", username).execute()
        if res.data:
            return None, "Student user already exists"
        
        supabase_admin.table("users").insert({
            "username": username,
            "password": hashed_pw,
            "role": "student",
            "name": student_name,
            "profile_photo": ""
        }).execute()
        
        try:
            supabase_admin.table("students").update({"password": password}).eq("id", student_id).execute()
        except Exception as e:
            if "PGRST204" in str(e):
                try:
                    supabase_admin.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS password TEXT DEFAULT '';")
                    supabase_admin.table("students").update({"password": password}).eq("id", student_id).execute()
                except:
                    pass
            else:
                pass
        
        if 'student_passwords' not in st.session_state:
            st.session_state.student_passwords = {}
        st.session_state.student_passwords[student_id] = password
        
        load_all_data()
        return password, "Student account created successfully"
    except Exception as e:
        return None, f"Error creating student account: {e}"

def reset_student_password(student_id):
    new_password = generate_random_password(8)
    hashed_pw = hash_password(new_password)
    
    supabase_admin = get_supabase_admin()
    try:
        supabase_admin.table("users").update({"password": hashed_pw}).eq("username", student_id).execute()
        
        try:
            supabase_admin.table("students").update({"password": new_password}).eq("id", student_id).execute()
        except Exception as e:
            if "PGRST204" in str(e):
                try:
                    supabase_admin.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS password TEXT DEFAULT '';")
                    supabase_admin.table("students").update({"password": new_password}).eq("id", student_id).execute()
                except:
                    pass
            else:
                pass
        
        if 'student_passwords' not in st.session_state:
            st.session_state.student_passwords = {}
        st.session_state.student_passwords[student_id] = new_password
        
        load_all_data()
        return new_password
    except Exception as e:
        return None

def get_student_password(student_id):
    if 'student_passwords' in st.session_state:
        if student_id in st.session_state.student_passwords:
            return st.session_state.student_passwords[student_id]
    
    for s in st.session_state.students:
        if s.get("id") == student_id:
            password = s.get("password", "")
            if password:
                if 'student_passwords' not in st.session_state:
                    st.session_state.student_passwords = {}
                st.session_state.student_passwords[student_id] = password
                return password
            break
    
    return "Not set"

def get_student_by_username(username):
    for s in st.session_state.students:
        if s.get("id") == username:
            return s
    return None

def login_user(username, password):
    if username == "admin" and password == "adminbb":
        st.session_state.logged_in = True
        st.session_state.current_user = "admin"
        st.session_state.current_role = "admin"
        add_notification("Welcome, School Administrator!", "success")
        return True, "✅ Login successful!"
    
    try:
        supabase = get_supabase()
        res = supabase.table("users").select("*").eq("username", username).execute()
        
        if not res.data:
            student_exists = False
            for s in st.session_state.students:
                if s.get("id") == username:
                    student_exists = True
                    break
            
            if student_exists:
                return False, "❌ Student account not created. Please ask admin to create your account."
            else:
                return False, "❌ User not found."
        
        user_data = res.data[0]
        stored_hash = user_data["password"]
        
        if verify_password(password, stored_hash):
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.session_state.current_role = user_data["role"]
            
            if username not in st.session_state.user_db:
                st.session_state.user_db[username] = {
                    "password": stored_hash,
                    "role": user_data["role"],
                    "name": user_data["name"],
                    "profile_photo": user_data.get("profile_photo", "")
                }
            
            add_notification(f"Welcome, {user_data['name']}!", "success")
            return True, "✅ Login successful!"
        else:
            return False, "❌ Incorrect password."
    except Exception as e:
        return False, f"❌ Login error: {e}"

def logout_user():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.session_state.current_role = None
    st.session_state.celebration_dismissed = False

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
    if 'student_passwords' not in st.session_state:
        st.session_state.student_passwords = {}

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

def get_subject_admin(subject, grade):
    for assignment in st.session_state.get('subject_admin_assignments', []):
        if assignment.get('subject') == subject:
            grade_range = assignment.get('grade_range', [])
            if not grade_range or grade in grade_range:
                return assignment.get('teacher_id')
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

def get_subject_mapping_for_admin(teacher_id):
    assignments = []
    for sa in st.session_state.get('subject_admin_assignments', []):
        if sa.get('teacher_id') == teacher_id:
            assignments.append(sa)
    return assignments

def get_student_rank(student_id, grade, section):
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

def get_rankings_by_grade_section(grade, section):
    students_in_class = [s for s in st.session_state.students 
                         if s.get("grade") == grade and s.get("section") == section]
    if not students_in_class:
        return []
    
    student_scores = []
    for s in students_in_class:
        evals = get_approved_evaluations_for_student(s["id"])
        avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2) if evals else 0
        student_scores.append({
            "id": s["id"],
            "name": s["name"],
            "avg": avg_score,
            "gender": s.get("gender", "N/A"),
            "evaluations": len(evals)
        })
    sorted_students = sorted(student_scores, key=lambda x: x["avg"], reverse=True)
    for i, s in enumerate(sorted_students):
        s["rank"] = i + 1
    return sorted_students

def get_homeroom_comment(avg_score):
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

def get_student_subject_scores(student_id, semester=None):
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
    avg_scores = {}
    for subj, scores in subject_scores.items():
        avg_scores[subj] = round(sum(scores) / len(scores), 2)
    return avg_scores

# ---- STATISTICAL FUNCTIONS ----
def generate_school_statistics():
    total_students = len(st.session_state.students)
    total_teachers = len(st.session_state.teachers)
    total_evaluations = len([e for e in st.session_state.evaluations if e.get("status") == "approved"])
    total_batches = len(st.session_state.batches)
    
    male_students = len([s for s in st.session_state.students if s.get("gender") == "M"])
    female_students = len([s for s in st.session_state.students if s.get("gender") == "F"])
    
    grade_distribution = {}
    for s in st.session_state.students:
        grade = s.get("grade", "Unknown")
        grade_distribution[grade] = grade_distribution.get(grade, 0) + 1
    
    section_distribution = {}
    for s in st.session_state.students:
        section = s.get("section", "Unknown")
        section_distribution[section] = section_distribution.get(section, 0) + 1
    
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
    
    teacher_workload = {}
    for t in st.session_state.teachers:
        teacher_id = t.get("id")
        batch_count = len([b for b in st.session_state.batches if b.get("teacher_id") == teacher_id])
        eval_count = len([e for e in st.session_state.evaluations if e.get("teacher_id") == teacher_id])
        teacher_workload[t.get("name", "Unknown")] = {
            "batches": batch_count,
            "evaluations": eval_count
        }
    
    pending_batches = len(get_batches_awaiting_final_approval())
    
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
    stats = generate_school_statistics()
    # ... (full function as in your original code)

# ===================================================================
# PAGE CONFIG
# ===================================================================
st.set_page_config(
    page_title="School Registration Portal",
    page_icon="SRP🏫@ET",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CELEBRATION PAGE FUNCTIONS ----
def is_celebration_period():
    today = datetime.now()
    m, d = today.month, today.day
    if m == 8 and d >= 21:
        return True
    if m == 9 and d <= 30:
        return True
    return False

def show_celebration_page():
    # ... (full function as in your original code)
    pass

# ---- LOGIN PAGE ----
def show_login_page():
    # ... (full function as in your original code)
    pass

# ---- PROFILE UPDATE ----
def show_profile_update():
    # ... (full function as in your original code)
    pass

# ---- PENALTY LOG & NOTIFICATIONS ----
def show_penalty_log():
    # ... (full function as in your original code)
    pass

def show_notification_center():
    # ... (full function as in your original code)
    pass

# ---- STUDENT CARD GENERATION ----
def generate_student_card(student, semester="Semester III"):
    # ... (full function as in your original code)
    pass

def show_student_card_panel():
    # ... (full function as in your original code)
    pass

# ---- SUBJECT ADMIN PANEL ----
def show_subject_admin_panel():
    # ... (full function as in your original code)
    pass

# ---- TEACHER PANEL ----
def show_teacher_panel():
    # ... (full function as in your original code)
    pass

# ---- STUDENT PANEL ----
def show_student_panel():
    # ... (full function as in your original code)
    pass

# ---- DEEP STATISTICS ----
def generate_deep_statistics():
    # ... (full function as in your original code)
    pass

def create_statistics_charts(stats):
    # ... (full function as in your original code)
    pass

def generate_deep_report_html(stats, charts):
    # ... (full function as in your original code)
    pass

def generate_deep_summary():
    # ... (full function as in your original code)
    pass

def show_deep_statistics():
    # ... (full function as in your original code)
    pass

# ---- ADMIN PANEL ----
def show_admin_panel():
    st.markdown("### 👨‍💼 Admin Dashboard")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15 = st.tabs([
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

    # Tab 0: My Profile
    with tab1:
        show_profile_update()

    # Tab 1: Overview
    with tab2:
        st.markdown("#### Dashboard Overview")
        stats = generate_school_statistics()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1: st.metric("👨‍🎓 Students", stats['total_students'])
        with col2: st.metric("👨‍🏫 Teachers", stats['total_teachers'])
        with col3: st.metric("📋 Subjects", len(st.session_state.subjects))
        with col4: st.metric("📝 Evaluations", stats['total_evaluations'])
        with col5: st.metric("⏳ Pending", stats['pending_batches'])
        with col6: st.metric("📈 Pass Rate", f"{stats['pass_rate']}%")
        
        if is_registration_open():
            st.success("🟢 Registration is currently **OPEN**")
        else:
            st.error("🔴 Registration is currently **CLOSED**")
        
        st.markdown("---")
        st.markdown("#### 🔐 Admin Credentials")
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;background:#F8F9FA;padding:15px;border-radius:12px;border:1px solid #E8EAED;">
            <div>
                <span style="font-weight:600;color:#5F6368;">👤 Username:</span>
                <span style="font-weight:700;color:#1A73E8;font-size:1.1rem;">admin</span>
            </div>
            <div>
                <span style="font-weight:600;color:#5F6368;">🔑 Password:</span>
                <span style="font-weight:700;color:#EA4335;background:#FCE8E6;padding:2px 12px;border-radius:4px;font-size:1.1rem;">adminbb</span>
                <span style="font-size:0.8rem;color:#5F6368;margin-left:10px;">(default)</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Tab 2: Registration
    with tab3:
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

    # Tab 3: Teachers
    with tab4:
        st.markdown("#### 👨‍🏫 Manage Teachers")
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
                assignment["grade"] = st.selectbox("Grade", grade_options, index=idx, key=f"assign_grade_{i}")
            with col2:
                assignment["section"] = st.text_input("Section", value=assignment["section"], key=f"assign_section_{i}")
            with col3:
                semester_options = ["Semester I", "Semester II"]
                try:
                    sem_idx = semester_options.index(assignment["semester"])
                except ValueError:
                    sem_idx = 0
                    assignment["semester"] = semester_options[0]
                assignment["semester"] = st.selectbox("Semester", semester_options, index=sem_idx, key=f"assign_semester_{i}")
            with col4:
                if st.button("✖", key=f"remove_assign_{i}", width='stretch'):
                    if len(st.session_state.assignments_list) > 1:
                        st.session_state.assignments_list.pop(i)
                        st.rerun()
        if st.button("➕ Add Assignment", width='stretch'):
            st.session_state.assignments_list.append({"grade": "Grade 1", "section": "A", "semester": "Semester I"})
            st.rerun()

        with st.form("add_teacher"):
            st.markdown("#### 👤 Teacher Details")
            col1, col2 = st.columns(2)
            with col1:
                teacher_name = st.text_input("Teacher Full Name *", placeholder="e.g., Abebe Kebede")
                teacher_subject = st.selectbox("Subject Taught *", ALL_SUBJECTS)
            with col2:
                teacher_email = st.text_input("Email Address", placeholder="teacher@school.edu")
            
            st.markdown("---")
            st.markdown("#### 📚 Subject Admin Assignment")
            st.caption("If this teacher should be a subject admin, select the subjects and grade ranges they will administer.")
            
            col1, col2 = st.columns(2)
            with col1:
                teacher_admin_subjects = st.multiselect(
                    "📚 Subjects this teacher administers (leave empty for regular teacher)",
                    options=ALL_SUBJECTS,
                    default=[],
                    help="Select subjects this teacher will be able to approve/reject"
                )
            with col2:
                if teacher_admin_subjects:
                    grade_range_options = ["All Grades"] + [f"Grade {i}" for i in range(1, 13)]
                    teacher_grade_range = st.multiselect(
                        "Grade Range (select specific grades or leave empty for all)",
                        options=grade_range_options,
                        default=["All Grades"],
                        help="Select which grades this teacher will administer (or 'All Grades')"
                    )
                else:
                    teacher_grade_range = []
                    st.info("Select subjects above to specify grade range")

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
                            "assignments": json.dumps(st.session_state.assignments_list),
                            "admin_subjects": json.dumps(teacher_admin_subjects)
                        }).execute()
                        
                        if teacher_admin_subjects:
                            if "All Grades" in teacher_grade_range or not teacher_grade_range:
                                grade_range = []
                            else:
                                grade_range = [g for g in teacher_grade_range if g != "All Grades"]
                            
                            for subject in teacher_admin_subjects:
                                supabase_admin.table("subject_admin_assignments").insert({
                                    "teacher_id": teacher_id,
                                    "teacher_name": teacher_name,
                                    "subject": subject,
                                    "grade_range": json.dumps(grade_range)
                                }).execute()
                        
                        load_all_data()
                        add_notification(f"👨‍🏫 New teacher added: {teacher_name}", "success")
                        
                        st.balloons()
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #E8F0FE 0%, #D2E3FC 100%);
                                    padding: 1.5rem;
                                    border-radius: 16px;
                                    border: 3px solid #1A73E8;
                                    margin: 1rem 0;">
                            <h3 style="color: #1A73E8; margin: 0 0 0.5rem 0;">✅ Teacher Added Successfully!</h3>
                            <div style="background: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                                <p><b>👤 Name:</b> {teacher_name}</p>
                                <p><b>📚 Subject:</b> {teacher_subject}</p>
                                <p><b>👤 Role:</b> {role.title()}</p>
                                <p><b>🔐 Admin Subjects:</b> {', '.join(teacher_admin_subjects) if teacher_admin_subjects else '(None - Regular Teacher)'}</p>
                                <p><b>🔑 Username:</b> <code style="font-size:1.2rem;background:#f0f0f0;padding:4px 12px;border-radius:4px;">{username}</code></p>
                                <p><b>🔐 Password:</b> <code style="font-size:1.2rem;background:#FCE8E6;padding:4px 12px;border-radius:4px;color:#EA4335;font-weight:700;">{password}</code></p>
                            </div>
                            <p style="color: #5F6368; margin-top: 0.5rem; font-size:0.9rem;">
                                ⚠️ Please share these credentials with the teacher.
                                They can change their password after logging in.
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        st.session_state.assignments_list = [{"grade": "Grade 1", "section": "A", "semester": "Semester I"}]
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error adding teacher: {e}")
                else:
                    st.error("❌ Please enter teacher name.")

        st.markdown("---")
        if st.session_state.teachers:
            st.markdown("#### 📋 All Teachers")
            for teacher in st.session_state.teachers:
                assignments = json.loads(teacher.get("assignments", "[]")) if teacher.get("assignments") else []
                assign_str = ", ".join([f"{a['grade']} ({a['section']}) - {a.get('semester', '')}" for a in assignments]) if assignments else "None"
                admin_subjects = json.loads(teacher.get("admin_subjects", "[]")) if teacher.get("admin_subjects") else []
                admin_str = ", ".join(admin_subjects) if admin_subjects else "None"
                teacher_password = teacher.get('password', 'N/A')
                
                is_subject_admin = len(admin_subjects) > 0
                role_badge = "Subject Admin" if is_subject_admin else "Teacher"
                role_color = "#E8F0FE" if is_subject_admin else "#F1F3F4"
                
                grade_range_str = ""
                if is_subject_admin:
                    grade_ranges = []
                    for sa in st.session_state.get('subject_admin_assignments', []):
                        if sa.get('teacher_id') == teacher.get('id'):
                            gr = sa.get('grade_range', [])
                            if gr:
                                grade_ranges.append(", ".join(gr))
                            else:
                                grade_ranges.append("All Grades")
                    if grade_ranges:
                        grade_range_str = f" (Grades: {', '.join(set(grade_ranges))})"
                
                st.markdown(f"""
                <div class="teacher-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4>👨‍🏫 {teacher['name']}</h4>
                            <p><b>📚 Subject:</b> {teacher['subject']}</p>
                            <p><b>📌 Assignments:</b> {assign_str}</p>
                            <p><b>🔐 Admin Subjects:</b> {admin_str if admin_str != "None" else "(None - Regular Teacher)"}{grade_range_str}</p>
                            <p><b>✉️ Email:</b> {teacher.get('email', 'N/A')}</p>
                        </div>
                        <div style="text-align:right;">
                            <span style="background:{role_color};padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;">
                                {role_badge}
                            </span>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px;background:#F8F9FA;padding:10px;border-radius:8px;">
                        <div><b>👤 Username:</b> <code>{teacher.get('username', 'N/A')}</code></div>
                        <div><b>🔑 Password:</b> <code style="background:#FCE8E6;padding:2px 10px;border-radius:4px;color:#EA4335;font-weight:700;">{teacher_password}</code></div>
                    </div>
                    <div style="margin-top:8px;font-size:0.85rem;color:#5F6368;">
                        <b>📅 Added:</b> {teacher.get('added', 'N/A')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # Tab 4: Subjects
    with tab5:
        st.markdown("#### 📚 Manage Subjects")
        # ... (rest of subjects tab)

    # Tab 5: All Data
    with tab6:
        st.markdown("#### 📋 All Data")
        if st.session_state.students:
            df = pd.DataFrame(st.session_state.students)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No students registered yet.")

    # Tab 6: Approvals
    with tab7:
        # ... (approvals tab)
        pass

    # Tab 7: Rankings
    with tab8:
        # ... (rankings tab)
        pass

    # Tab 8: Students
    with tab9:
        # ... (students tab with edit/delete)
        pass

    # Tab 9: Import/Export
    with tab10:
        # ... (import/export tab)
        pass

    # Tab 10: Reports
    with tab11:
        # ... (reports tab)
        pass

    # Tab 11: Penalty Log
    with tab12:
        show_penalty_log()

    # Tab 12: Settings
    with tab13:
        # ... (settings tab)
        pass

    # Tab 13: Homeroom
    with tab14:
        # ... (homeroom tab)
        pass

    # Tab 14: Student Cards
    with tab15:
        show_student_card_panel()

# ---- CSS ----
st.markdown("""
<style>
    /* Your full CSS from the original code */
</style>
""", unsafe_allow_html=True)

# ---- MAIN ----
def main():
    init_user_db()
    
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
    
    current_user = st.session_state.current_user
    role = st.session_state.current_role
    user_data = st.session_state.user_db.get(current_user, {})
    display_name = user_data.get("name", current_user.title())
    
    with st.sidebar:
        st.markdown("### School Portal")
        st.markdown("---")
        
        if role == "student":
            student = get_student_by_username(current_user)
            if student:
                st.markdown(display_student_photo(student["id"], 80), unsafe_allow_html=True)
            else:
                st.markdown(display_profile_photo(current_user, 80), unsafe_allow_html=True)
        else:
            st.markdown(display_profile_photo(current_user, 80), unsafe_allow_html=True)
        
        st.markdown(f"""
        <div style="text-align:center;margin:8px 0;">
            <p style="font-weight:600;color:#1A73E8;">{display_name}</p>
            <p style="font-size:0.85rem;color:#5F6368;">@{current_user} · {role.title()}</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        if role == "admin":
            nav_options = ["👤 My Profile", "📊 Dashboard", "👨‍🏫 Teachers", "👨‍🎓 Students", "✅ Approvals", "📊 Deep Statistics", "📄 Reports", "⚠️ Penalty Log", "🔔 Notifications"]
        elif role == "subject_admin":
            nav_options = ["👤 My Profile", "📋 Subject Admin", "⚠️ Penalties", "🔔 Notifications"]
        elif role == "teacher":
            nav_options = ["👤 My Profile", "👨‍🏫 My Dashboard", "⚠️ Penalties", "🔔 Notifications"]
        elif role == "student":
            nav_options = ["👨‍🎓 My Dashboard", "⚠️ Penalties", "🔔 Notifications"]
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
    
    current_page = getattr(st.session_state, 'current_page', "📊 Dashboard")
    
    if role == "admin":
        if current_page == "👤 My Profile":
            show_profile_update()
        elif current_page == "📊 Dashboard":
            show_admin_panel()
        elif current_page == "📊 Deep Statistics":
            show_deep_statistics()
        elif current_page == "👨‍🏫 Teachers":
            st.info("Use the Admin Dashboard → Teachers tab for full management.")
        elif current_page == "👨‍🎓 Students":
            st.info("Use the Admin Dashboard → Students tab for full management.")
        elif current_page == "✅ Approvals":
            st.info("Use the Admin Dashboard → Approvals tab.")
        elif current_page == "📄 Reports":
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
    
    elif role == "student":
        if current_page == "👨‍🎓 My Dashboard":
            show_student_panel()
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
