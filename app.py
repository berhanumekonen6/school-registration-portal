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
    # Grades 4-6: 9 components with different weights
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
    # Grade 7-8: 6 components
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
    # Grades 9-12: 7 components
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
    "Grade 1": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 2": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 3": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    "Grade 4": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "እንግሊዘኛ(S)", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "ጋሞኛ", "እይታና ትወና", "ስፖርት"],
    # Grades 5-6
    "Grade 5": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "ጋሞኛ", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"],
    "Grade 6": ["አማርኛ", "ግዕዝ", "እንሊዘኛ(G)", "ጋሞኛ", "ሒሳብ", "አ/ሳይንስ", "ግብረ-ገብ", "እይታና ትወና", "ስፖርት", "ኮምፒተር"],
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

# ---- Helper function to safely parse JSON fields ----
def safe_json_loads(value, default=None):
    """Safely parse JSON data, handling both strings and already-parsed objects."""
    if value is None:
        return default if default is not None else []
    if isinstance(value, (list, dict)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return default if default is not None else []
    return default if default is not None else []

# ---- Data Load with Error Handling ----
def load_all_data():
    supabase = get_supabase()
    
    # Load students
    try:
        res = supabase.table("students").select("*").execute()
        st.session_state.students = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load students: {e}")
        st.session_state.students = []
    
    # Load teachers
    try:
        res = supabase.table("teachers").select("*").execute()
        st.session_state.teachers = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load teachers: {e}")
        st.session_state.teachers = []
    
    # Load evaluations
    try:
        res = supabase.table("evaluations").select("*").execute()
        st.session_state.evaluations = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load evaluations: {e}")
        st.session_state.evaluations = []
    
    # Load batches
    try:
        res = supabase.table("batches").select("*").execute()
        st.session_state.batches = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load batches: {e}")
        st.session_state.batches = []
    
    # Load users
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
    
    # Load notifications
    try:
        res = supabase.table("notifications").select("*").order("id", desc=True).execute()
        st.session_state.notifications = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load notifications: {e}")
        st.session_state.notifications = []
    
    # Load penalty_log
    try:
        res = supabase.table("penalty_log").select("*").order("id", desc=True).execute()
        st.session_state.penalty_log = res.data if res.data else []
    except Exception as e:
        st.warning(f"Could not load penalty_log: {e}")
        st.session_state.penalty_log = []
    
    # Load homeroom_assignments (with error handling for missing table)
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
    
    # Load subject_admin_assignments (with error handling for missing table)
    try:
        res = supabase.table("subject_admin_assignments").select("*").execute()
        st.session_state.subject_admin_assignments = res.data if res.data else []
    except Exception as e:
        error_msg = str(e)
        if "PGRST205" in error_msg or "Could not find the table" in error_msg:
            # Table doesn't exist - create empty list
            st.session_state.subject_admin_assignments = []
        else:
            st.warning(f"Could not load subject_admin_assignments: {e}")
            st.session_state.subject_admin_assignments = []

# ---- Assessment Helper Functions ----
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
    """Save profile photo to Supabase."""
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
    """Get profile photo for a user."""
    user_data = st.session_state.user_db.get(username, {})
    return user_data.get("profile_photo", "")

def display_profile_photo(username, size=80):
    """Display profile photo as HTML image."""
    photo_data = get_profile_photo(username)
    if photo_data and len(photo_data) > 10:
        return f'<img src="data:image/png;base64,{photo_data}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #1A73E8;">'
    else:
        initial = username[0].upper() if username else "U"
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:linear-gradient(135deg,#1A73E8,#4285F4);display:flex;align-items:center;justify-content:center;font-size:{size//2.5}px;color:white;font-weight:700;border:2px solid #1A73E8;">{initial}</div>'

# ---- Student Profile Photo Helpers ----
def save_student_photo(student_id, photo_bytes):
    """Save student profile photo with error handling."""
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
    """Get student profile photo."""
    for s in st.session_state.students:
        if s.get("id") == student_id:
            return s.get("profile_photo", "")
    return ""

def display_student_photo(student_id, size=80):
    """Display student profile photo."""
    photo_data = get_student_photo(student_id)
    if photo_data and len(photo_data) > 10:
        return f'<img src="data:image/png;base64,{photo_data}" style="width:{size}px;height:{size}px;border-radius:50%;object-fit:cover;border:2px solid #34A853;">'
    else:
        return f'<div style="width:{size}px;height:{size}px;border-radius:50%;background:#E8F0FE;display:flex;align-items:center;justify-content:center;font-size:{size//2.5}px;color:#34A853;border:2px solid #34A853;">👤</div>'

# ---- Student Login Functions ----
def create_student_user(student_id, student_name):
    """Create a user account for a student and store password."""
    username = student_id
    password = generate_random_password(8)
    hashed_pw = hash_password(password)
    
    supabase_admin = get_supabase_admin()
    try:
        # Check if user already exists
        res = supabase_admin.table("users").select("username").eq("username", username).execute()
        if res.data:
            return None, "Student user already exists"
        
        # Create user account
        supabase_admin.table("users").insert({
            "username": username,
            "password": hashed_pw,
            "role": "student",
            "name": student_name,
            "profile_photo": ""
        }).execute()
        
        # Store password in student record for admin reference
        try:
            supabase_admin.table("students").update({"password": password}).eq("id", student_id).execute()
        except Exception as e:
            if "PGRST204" in str(e):
                # Column doesn't exist - try to add it
                try:
                    supabase_admin.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS password TEXT DEFAULT '';")
                    supabase_admin.table("students").update({"password": password}).eq("id", student_id).execute()
                except:
                    pass
            else:
                pass
        
        # Store in session state for display
        if 'student_passwords' not in st.session_state:
            st.session_state.student_passwords = {}
        st.session_state.student_passwords[student_id] = password
        
        # Reload data to refresh user_db
        load_all_data()
        
        return password, "Student account created successfully"
    except Exception as e:
        return None, f"Error creating student account: {e}"

def reset_student_password(student_id):
    """Reset student password and update both tables."""
    new_password = generate_random_password(8)
    hashed_pw = hash_password(new_password)
    
    supabase_admin = get_supabase_admin()
    try:
        # Update users table
        supabase_admin.table("users").update({"password": hashed_pw}).eq("username", student_id).execute()
        
        # Update students table
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
        
        # Update session state
        if 'student_passwords' not in st.session_state:
            st.session_state.student_passwords = {}
        st.session_state.student_passwords[student_id] = new_password
        
        # Reload data to refresh user_db
        load_all_data()
        
        return new_password
    except Exception as e:
        return None

def get_student_password(student_id):
    """Get student password from session or student record."""
    # Check session first
    if 'student_passwords' in st.session_state:
        if student_id in st.session_state.student_passwords:
            return st.session_state.student_passwords[student_id]
    
    # Check student record
    for s in st.session_state.students:
        if s.get("id") == student_id:
            password = s.get("password", "")
            if password:
                # Cache in session
                if 'student_passwords' not in st.session_state:
                    st.session_state.student_passwords = {}
                st.session_state.student_passwords[student_id] = password
                return password
            break
    
    return "Not set"

def get_student_by_username(username):
    """Get student by username (student ID)."""
    for s in st.session_state.students:
        if s.get("id") == username:
            return s
    return None

def login_user(username, password):
    """Login user with proper error handling."""
    # Admin login
    if username == "admin" and password == "adminbb":
        st.session_state.logged_in = True
        st.session_state.current_user = "admin"
        st.session_state.current_role = "admin"
        add_notification("Welcome, School Administrator!", "success")
        return True, "✅ Login successful!"
    
    try:
        # Get fresh data from database
        supabase = get_supabase()
        
        # Check if user exists
        res = supabase.table("users").select("*").eq("username", username).execute()
        
        if not res.data:
            # Check if this is a student ID that exists in students table
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
            # Update session state
            st.session_state.logged_in = True
            st.session_state.current_user = username
            st.session_state.current_role = user_data["role"]
            
            # Update user_db in session
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
    """Get batches for a specific subject admin."""
    return [b for b in st.session_state.batches if b.get("subject_admin_id") == admin_id and b.get("status") == "pending"]

def get_batches_awaiting_final_approval():
    return [b for b in st.session_state.batches 
            if (b.get("status") == "subject_approved") or 
               (b.get("status") == "pending" and b.get("subject_admin_id") is None)]

def get_approved_evaluations_for_student(student_id):
    return [e for e in st.session_state.evaluations if e.get("student_id") == student_id and e.get("status") == "approved"]

def get_subject_admin(subject, grade):
    """Get the subject admin for a given subject and grade."""
    for assignment in st.session_state.get('subject_admin_assignments', []):
        if assignment.get('subject') == subject:
            # Check if this admin covers this grade
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
    """Get all subject assignments for a subject admin."""
    assignments = []
    for sa in st.session_state.get('subject_admin_assignments', []):
        if sa.get('teacher_id') == teacher_id:
            assignments.append(sa)
    return assignments

# ---- STATISTICAL FUNCTIONS ----
def generate_school_statistics():
    """Generate basic school statistics for the dashboard."""
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
        
        <h2>📋 Summary Statistics</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['total_students']}</div><div class="label">Total Students</div></div>
            <div class="stat-card"><div class="number">{stats['total_teachers']}</div><div class="label">Total Teachers</div></div>
            <div class="stat-card"><div class="number">{stats['total_evaluations']}</div><div class="label">Approved Evaluations</div></div>
            <div class="stat-card"><div class="number">{stats['total_batches']}</div><div class="label">Total Batches</div></div>
            <div class="stat-card"><div class="number">{stats['pending_batches']}</div><div class="label">Pending Approvals</div></div>
            <div class="stat-card"><div class="number">{stats['pass_rate']}%</div><div class="label">Overall Pass Rate</div></div>
        </div>
        
        <h2>👤 Gender Distribution</h2>
        <div class="stats-grid">
            <div class="stat-card"><div class="number">{stats['male_students']}</div><div class="label">Male Students</div></div>
            <div class="stat-card"><div class="number">{stats['female_students']}</div><div class="label">Female Students</div></div>
            <div class="stat-card"><div class="number">{stats['gender_ratio']}</div><div class="label">Male:Female Ratio</div></div>
        </div>
        
        <h2>✅ Pass / Fail Status</h2>
        <div class="stats-grid">
            <div class="stat-card" style="background:#E6F4EA;"><div class="number" style="color:#34A853;">{stats['passed']}</div><div class="label">Passed</div></div>
            <div class="stat-card" style="background:#FCE8E6;"><div class="number" style="color:#EA4335;">{stats['failed']}</div><div class="label">Failed</div></div>
            <div class="stat-card"><div class="number">{stats['pass_rate']}%</div><div class="label">Pass Rate</div></div>
        </div>
        
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

# ---- DEEP STATISTICAL ANALYSIS FUNCTIONS ----
def generate_deep_statistics():
    """Generate comprehensive deep statistics with all metrics."""
    
    stats = {
        "student_stats": {},
        "performance_metrics": {},
        "demographics": {},
        "subject_analysis": {},
        "grade_analysis": {},
        "teacher_analysis": {},
        "trends": {},
        "summary": {}
    }
    
    # Basic counts
    stats["summary"]["total_students"] = len(st.session_state.students)
    stats["summary"]["total_teachers"] = len(st.session_state.teachers)
    stats["summary"]["total_evaluations"] = len([e for e in st.session_state.evaluations if e.get("status") == "approved"])
    stats["summary"]["total_batches"] = len(st.session_state.batches)
    stats["summary"]["pending_approvals"] = len(get_batches_awaiting_final_approval())
    
    # Gender distribution
    male = len([s for s in st.session_state.students if s.get("gender") == "M"])
    female = len([s for s in st.session_state.students if s.get("gender") == "F"])
    other = len([s for s in st.session_state.students if s.get("gender") not in ["M", "F"]])
    stats["demographics"]["gender"] = {"Male": male, "Female": female, "Other": other}
    
    # Grade distribution
    grade_dist = {}
    for s in st.session_state.students:
        grade = s.get("grade", "Unknown")
        grade_dist[grade] = grade_dist.get(grade, 0) + 1
    stats["demographics"]["grade_distribution"] = grade_dist
    
    # Section distribution
    section_dist = {}
    for s in st.session_state.students:
        section = s.get("section", "Unknown")
        section_dist[section] = section_dist.get(section, 0) + 1
    stats["demographics"]["section_distribution"] = section_dist
    
    # Subject performance
    subject_scores = {}
    for e in st.session_state.evaluations:
        if e.get("status") == "approved":
            subject = e.get("subject", "Unknown")
            score = e.get("overall_score", 0)
            if subject not in subject_scores:
                subject_scores[subject] = []
            subject_scores[subject].append(score)
    
    subject_avg = {}
    subject_min = {}
    subject_max = {}
    subject_count = {}
    for subject, scores in subject_scores.items():
        if scores:
            subject_avg[subject] = round(sum(scores) / len(scores), 2)
            subject_min[subject] = min(scores)
            subject_max[subject] = max(scores)
            subject_count[subject] = len(scores)
    stats["subject_analysis"]["averages"] = subject_avg
    stats["subject_analysis"]["min"] = subject_min
    stats["subject_analysis"]["max"] = subject_max
    stats["subject_analysis"]["counts"] = subject_count
    
    # Grade-wise performance
    grade_perf = {}
    for s in st.session_state.students:
        grade = s.get("grade", "Unknown")
        evals = get_approved_evaluations_for_student(s["id"])
        if evals:
            avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
            if grade not in grade_perf:
                grade_perf[grade] = []
            grade_perf[grade].append(avg_score)
    
    grade_avg = {}
    grade_min = {}
    grade_max = {}
    for grade, scores in grade_perf.items():
        if scores:
            grade_avg[grade] = round(sum(scores) / len(scores), 2)
            grade_min[grade] = min(scores)
            grade_max[grade] = max(scores)
    stats["grade_analysis"]["averages"] = grade_avg
    stats["grade_analysis"]["min"] = grade_min
    stats["grade_analysis"]["max"] = grade_max
    
    # Pass/Fail by grade
    pass_fail = {}
    for s in st.session_state.students:
        grade = s.get("grade", "Unknown")
        evals = get_approved_evaluations_for_student(s["id"])
        if evals:
            avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
            if grade not in pass_fail:
                pass_fail[grade] = {"passed": 0, "failed": 0}
            if avg_score >= 50:
                pass_fail[grade]["passed"] += 1
            else:
                pass_fail[grade]["failed"] += 1
    stats["grade_analysis"]["pass_fail"] = pass_fail
    
    # Overall pass rate
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
    stats["summary"]["passed"] = passed
    stats["summary"]["failed"] = failed
    stats["summary"]["pass_rate"] = round((passed / (passed + failed)) * 100, 1) if (passed + failed) > 0 else 0
    
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
    stats["teacher_analysis"]["workload"] = teacher_workload
    
    # Section performance
    section_perf = {}
    for s in st.session_state.students:
        section = s.get("section", "Unknown")
        grade = s.get("grade", "Unknown")
        key = f"{grade} - Section {section}"
        evals = get_approved_evaluations_for_student(s["id"])
        if evals:
            avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2)
            if key not in section_perf:
                section_perf[key] = []
            section_perf[key].append(avg_score)
    
    section_avg = {}
    for key, scores in section_perf.items():
        if scores:
            section_avg[key] = round(sum(scores) / len(scores), 2)
    stats["grade_analysis"]["section_performance"] = section_avg
    
    # Generate timestamp
    stats["generated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return stats

# ---- CREATE STATISTICS CHARTS ----
def create_statistics_charts(stats):
    """Create interactive Plotly charts for statistics."""
    if not PLOTLY_AVAILABLE:
        return {}
    
    charts = {}
    
    # 1. Gender Distribution Pie Chart
    gender_data = stats["demographics"]["gender"]
    fig1 = go.Figure(data=[go.Pie(
        labels=list(gender_data.keys()),
        values=list(gender_data.values()),
        hole=0.4,
        marker=dict(colors=['#1A73E8', '#EA4335', '#FBBC04']),
        textinfo='label+percent',
        textposition='inside'
    )])
    fig1.update_layout(
        title="Gender Distribution",
        height=400,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14)
    )
    charts["gender_pie"] = fig1
    
    # 2. Grade Distribution Bar Chart
    grade_data = stats["demographics"]["grade_distribution"]
    sorted_grades = sorted(grade_data.keys())
    fig2 = go.Figure(data=[go.Bar(
        x=sorted_grades,
        y=[grade_data[g] for g in sorted_grades],
        marker=dict(
            color='#1A73E8',
            line=dict(color='#1557B0', width=2)
        ),
        text=[grade_data[g] for g in sorted_grades],
        textposition='outside'
    )])
    fig2.update_layout(
        title="Student Distribution by Grade",
        xaxis_title="Grade",
        yaxis_title="Number of Students",
        height=400,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        showlegend=False
    )
    charts["grade_distribution"] = fig2
    
    # 3. Subject Performance Bar Chart
    subject_avg = stats["subject_analysis"]["averages"]
    if subject_avg:
        sorted_subjects = sorted(subject_avg.items(), key=lambda x: x[1], reverse=True)
        colors = ['#34A853' if s >= 70 else '#FBBC04' if s >= 50 else '#EA4335' for _, s in sorted_subjects]
        fig3 = go.Figure(data=[go.Bar(
            x=[s[0] for s in sorted_subjects],
            y=[s[1] for s in sorted_subjects],
            marker=dict(
                color=colors,
                line=dict(color='rgba(0,0,0,0.1)', width=1)
            ),
            text=[f"{s[1]}%" for s in sorted_subjects],
            textposition='outside'
        )])
        fig3.update_layout(
            title="Subject Performance Averages",
            xaxis_title="Subject",
            yaxis_title="Average Score (%)",
            height=450,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14),
            showlegend=False,
            yaxis_range=[0, 105]
        )
        charts["subject_performance"] = fig3
    else:
        charts["subject_performance"] = None
    
    # 4. Grade-wise Performance with Min/Max
    grade_avg = stats["grade_analysis"]["averages"]
    grade_min = stats["grade_analysis"]["min"]
    grade_max = stats["grade_analysis"]["max"]
    if grade_avg:
        sorted_grade_names = sorted(grade_avg.keys())
        
        fig4 = go.Figure()
        fig4.add_trace(go.Bar(
            name='Average',
            x=sorted_grade_names,
            y=[grade_avg[g] for g in sorted_grade_names],
            marker_color='#1A73E8',
            text=[f"{grade_avg[g]}%" for g in sorted_grade_names],
            textposition='outside'
        ))
        fig4.add_trace(go.Scatter(
            name='Min-Max Range',
            x=sorted_grade_names + sorted_grade_names[::-1],
            y=[grade_min[g] for g in sorted_grade_names] + [grade_max[g] for g in sorted_grade_names[::-1]],
            fill='toself',
            fillcolor='rgba(26, 115, 232, 0.2)',
            line=dict(color='rgba(26, 115, 232, 0.5)'),
            showlegend=True
        ))
        fig4.update_layout(
            title="Grade-wise Performance with Min-Max Range",
            xaxis_title="Grade",
            yaxis_title="Score (%)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis_range=[0, 105]
        )
        charts["grade_performance"] = fig4
    else:
        charts["grade_performance"] = None
    
    # 5. Pass/Fail Stacked Bar Chart
    pass_fail_data = stats["grade_analysis"]["pass_fail"]
    if pass_fail_data:
        grade_names = sorted(pass_fail_data.keys())
        passed_data = [pass_fail_data[g]["passed"] for g in grade_names]
        failed_data = [pass_fail_data[g]["failed"] for g in grade_names]
        
        fig5 = go.Figure(data=[
            go.Bar(name='Passed', x=grade_names, y=passed_data, marker_color='#34A853'),
            go.Bar(name='Failed', x=grade_names, y=failed_data, marker_color='#EA4335')
        ])
        fig5.update_layout(
            title="Pass/Fail Distribution by Grade",
            xaxis_title="Grade",
            yaxis_title="Number of Students",
            height=400,
            barmode='stack',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        charts["pass_fail"] = fig5
    else:
        charts["pass_fail"] = None
    
    # 6. Section Performance
    section_perf = stats["grade_analysis"]["section_performance"]
    if section_perf:
        sorted_sections = sorted(section_perf.items(), key=lambda x: x[1], reverse=True)
        colors_section = ['#34A853' if s >= 70 else '#FBBC04' if s >= 50 else '#EA4335' for _, s in sorted_sections]
        fig6 = go.Figure(data=[go.Bar(
            x=[s[0] for s in sorted_sections],
            y=[s[1] for s in sorted_sections],
            marker=dict(
                color=colors_section,
                line=dict(color='rgba(0,0,0,0.1)', width=1)
            ),
            text=[f"{s[1]}%" for s in sorted_sections],
            textposition='outside'
        )])
        fig6.update_layout(
            title="Section-wise Performance",
            xaxis_title="Class (Grade - Section)",
            yaxis_title="Average Score (%)",
            height=400,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14),
            showlegend=False,
            yaxis_range=[0, 105]
        )
        charts["section_performance"] = fig6
    else:
        charts["section_performance"] = None
    
    # 7. Teacher Workload
    workload = stats["teacher_analysis"]["workload"]
    if workload:
        teacher_names = list(workload.keys())
        batch_counts = [workload[t]["batches"] for t in teacher_names]
        eval_counts = [workload[t]["evaluations"] for t in teacher_names]
        
        fig7 = go.Figure(data=[
            go.Bar(name='Batches', x=teacher_names, y=batch_counts, marker_color='#1A73E8'),
            go.Bar(name='Evaluations', x=teacher_names, y=eval_counts, marker_color='#34A853')
        ])
        fig7.update_layout(
            title="Teacher Workload Distribution",
            xaxis_title="Teacher",
            yaxis_title="Count",
            height=400,
            barmode='group',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(size=14),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        charts["teacher_workload"] = fig7
    else:
        charts["teacher_workload"] = None
    
    # 8. Summary Statistics Cards (as a gauge chart for pass rate)
    fig8 = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=stats["summary"]["pass_rate"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Pass Rate"},
        delta={'reference': 50},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "#34A853" if stats["summary"]["pass_rate"] >= 60 else "#FBBC04" if stats["summary"]["pass_rate"] >= 50 else "#EA4335"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'rgba(234, 67, 53, 0.3)'},
                {'range': [50, 70], 'color': 'rgba(251, 188, 4, 0.3)'},
                {'range': [70, 100], 'color': 'rgba(52, 168, 83, 0.3)'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 50
            }
        }
    ))
    fig8.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(size=16)
    )
    charts["pass_rate_gauge"] = fig8
    
    return charts

def generate_deep_report_html(stats, charts):
    """Generate a comprehensive HTML report with all charts embedded."""
    import base64
    import io
    
    chart_images = {}
    for name, fig in charts.items():
        if fig is not None:
            try:
                img_bytes = fig.to_image(format="png", width=800, height=500, scale=2)
                b64 = base64.b64encode(img_bytes).decode('utf-8')
                chart_images[name] = b64
            except:
                chart_images[name] = None
    
    # Prepare data tables
    subject_table = ""
    for subject, avg in sorted(stats["subject_analysis"]["averages"].items(), key=lambda x: x[1], reverse=True):
        badge = "badge-excellent" if avg >= 70 else "badge-good" if avg >= 60 else "badge-average" if avg >= 50 else "badge-poor"
        label = "Excellent" if avg >= 70 else "Good" if avg >= 60 else "Average" if avg >= 50 else "Poor"
        subject_table += f"<tr><td>{subject}</td><td>{avg}%</td><td><span class='badge {badge}'>{label}</span></td></tr>"
    
    grade_table = ""
    for grade, avg in sorted(stats["grade_analysis"]["averages"].items()):
        grade_table += f"<tr><td>{grade}</td><td>{avg}%</td></tr>"
    
    section_table = ""
    for section, avg in sorted(stats["grade_analysis"]["section_performance"].items(), key=lambda x: x[1], reverse=True):
        section_table += f"<tr><td>{section}</td><td>{avg}%</td></tr>"
    
    teacher_table = ""
    for teacher, workload in sorted(stats["teacher_analysis"]["workload"].items()):
        teacher_table += f"<tr><td>{teacher}</td><td>{workload['batches']}</td><td>{workload['evaluations']}</td></tr>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Comprehensive School Statistics Report</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{
                font-family: 'Segoe UI', 'Noto Sans Ethiopic', Arial, sans-serif;
                background: #f0f2f5;
                padding: 20px;
                color: #202124;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 4px 30px rgba(0,0,0,0.08);
            }}
            .header {{
                text-align: center;
                padding: 20px 0 30px 0;
                border-bottom: 3px solid #1A73E8;
                margin-bottom: 30px;
            }}
            .header h1 {{
                font-size: 2.5rem;
                color: #1A73E8;
                margin-bottom: 5px;
            }}
            .header .subtitle {{
                color: #5F6368;
                font-size: 1.1rem;
            }}
            .header .date {{
                color: #5F6368;
                font-size: 0.9rem;
                margin-top: 5px;
            }}
            
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 15px;
                margin: 25px 0;
            }}
            .summary-card {{
                background: #F8F9FA;
                border-radius: 12px;
                padding: 20px;
                text-align: center;
                border: 1px solid #E8EAED;
                transition: all 0.3s;
            }}
            .summary-card:hover {{
                transform: translateY(-3px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.06);
                border-color: #1A73E8;
            }}
            .summary-card .number {{
                font-size: 2.2rem;
                font-weight: 700;
                color: #1A73E8;
                display: block;
            }}
            .summary-card .label {{
                font-size: 0.85rem;
                color: #5F6368;
                margin-top: 5px;
                display: block;
            }}
            .summary-card.pass .number {{ color: #34A853; }}
            .summary-card.fail .number {{ color: #EA4335; }}
            .summary-card.pending .number {{ color: #FBBC04; }}
            .summary-card.rate .number {{ 
                color: {'#34A853' if stats['summary']['pass_rate'] >= 70 else '#FBBC04' if stats['summary']['pass_rate'] >= 50 else '#EA4335'};
            }}
            
            .chart-container {{
                margin: 30px 0;
                padding: 20px;
                background: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E8EAED;
                box-shadow: 0 2px 8px rgba(0,0,0,0.04);
            }}
            .chart-container h2 {{
                color: #202124;
                font-size: 1.4rem;
                margin-bottom: 15px;
                border-bottom: 2px solid #E8EAED;
                padding-bottom: 10px;
            }}
            .chart-container img {{
                width: 100%;
                height: auto;
                border-radius: 8px;
            }}
            
            .two-col {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
            }}
            
            .data-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                font-size: 0.9rem;
            }}
            .data-table th {{
                background: #F1F3F4;
                padding: 12px 15px;
                text-align: left;
                font-weight: 600;
                border-bottom: 2px solid #DADCE0;
            }}
            .data-table td {{
                padding: 10px 15px;
                border-bottom: 1px solid #E8EAED;
            }}
            .data-table tr:hover {{
                background: #F8F9FA;
            }}
            .data-table .badge {{
                display: inline-block;
                padding: 2px 12px;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
            }}
            .badge-excellent {{ background: #E6F4EA; color: #34A853; }}
            .badge-good {{ background: #E8F0FE; color: #1A73E8; }}
            .badge-average {{ background: #FEF7E0; color: #F9AB00; }}
            .badge-poor {{ background: #FCE8E6; color: #EA4335; }}
            
            .footer {{
                margin-top: 40px;
                padding-top: 20px;
                border-top: 2px solid #E8EAED;
                text-align: center;
                color: #5F6368;
                font-size: 0.9rem;
            }}
            
            @media (max-width: 768px) {{
                .two-col {{ grid-template-columns: 1fr; }}
                .container {{ padding: 20px; }}
                .summary-grid {{ grid-template-columns: repeat(2, 1fr); }}
                .header h1 {{ font-size: 1.8rem; }}
            }}
            @media print {{
                body {{ background: white; padding: 10px; }}
                .container {{ box-shadow: none; border: 1px solid #ddd; }}
                .chart-container {{ break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
    <div class="container">
        <div class="header">
            <h1>📊 Comprehensive School Statistics Report</h1>
            <div class="subtitle">{st.session_state.school_name}</div>
            <div class="subtitle">City: {st.session_state.school_city}</div>
            <div class="date">Report Generated: {stats['generated_at']}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card"><span class="number">{stats['summary']['total_students']}</span><span class="label">👨‍🎓 Total Students</span></div>
            <div class="summary-card"><span class="number">{stats['summary']['total_teachers']}</span><span class="label">👨‍🏫 Total Teachers</span></div>
            <div class="summary-card"><span class="number">{stats['summary']['total_evaluations']}</span><span class="label">📝 Evaluations</span></div>
            <div class="summary-card pending"><span class="number">{stats['summary']['pending_approvals']}</span><span class="label">⏳ Pending Approvals</span></div>
            <div class="summary-card pass"><span class="number">{stats['summary']['passed']}</span><span class="label">✅ Passed</span></div>
            <div class="summary-card fail"><span class="number">{stats['summary']['failed']}</span><span class="label">❌ Failed</span></div>
            <div class="summary-card rate"><span class="number">{stats['summary']['pass_rate']}%</span><span class="label">📈 Pass Rate</span></div>
        </div>
        
        <div class="two-col">
            <div class="chart-container">
                <h2>Gender Distribution</h2>
                <img src="data:image/png;base64,{chart_images.get('gender_pie', '')}" alt="Gender Distribution">
            </div>
            <div class="chart-container">
                <h2>Overall Pass Rate</h2>
                <img src="data:image/png;base64,{chart_images.get('pass_rate_gauge', '')}" alt="Pass Rate">
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Student Distribution by Grade</h2>
            <img src="data:image/png;base64,{chart_images.get('grade_distribution', '')}" alt="Grade Distribution">
        </div>
        
        <div class="two-col">
            <div class="chart-container">
                <h2>Subject Performance Averages</h2>
                <img src="data:image/png;base64,{chart_images.get('subject_performance', '')}" alt="Subject Performance">
            </div>
            <div class="chart-container">
                <h2>Grade-wise Performance</h2>
                <img src="data:image/png;base64,{chart_images.get('grade_performance', '')}" alt="Grade Performance">
            </div>
        </div>
        
        <div class="two-col">
            <div class="chart-container">
                <h2>Pass/Fail Distribution by Grade</h2>
                <img src="data:image/png;base64,{chart_images.get('pass_fail', '')}" alt="Pass Fail">
            </div>
            <div class="chart-container">
                <h2>Section-wise Performance</h2>
                <img src="data:image/png;base64,{chart_images.get('section_performance', '')}" alt="Section Performance">
            </div>
        </div>
        
        <div class="chart-container">
            <h2>Teacher Workload Distribution</h2>
            <img src="data:image/png;base64,{chart_images.get('teacher_workload', '')}" alt="Teacher Workload">
        </div>
        
        <div class="two-col">
            <div class="chart-container">
                <h2>📖 Subject Performance Details</h2>
                <table class="data-table">
                    <thead><tr><th>Subject</th><th>Average Score</th><th>Performance</th></tr></thead>
                    <tbody>{subject_table}</tbody>
                </table>
            </div>
            <div class="chart-container">
                <h2>🎓 Grade-wise Performance</h2>
                <table class="data-table">
                    <thead><tr><th>Grade</th><th>Average Score</th></tr></thead>
                    <tbody>{grade_table}</tbody>
                </table>
            </div>
        </div>
        
        <div class="two-col">
            <div class="chart-container">
                <h2>📌 Section Performance</h2>
                <table class="data-table">
                    <thead><tr><th>Section</th><th>Average Score</th></tr></thead>
                    <tbody>{section_table}</tbody>
                </table>
            </div>
            <div class="chart-container">
                <h2>👨‍🏫 Teacher Workload</h2>
                <table class="data-table">
                    <thead><tr><th>Teacher</th><th>Batches</th><th>Evaluations</th></tr></thead>
                    <tbody>{teacher_table}</tbody>
                </table>
            </div>
        </div>
        
        <div class="footer">
            <p>Report generated by School Registration Portal v2.0</p>
            <p>© {datetime.now().year} {st.session_state.school_name} - All Rights Reserved</p>
            <p>Developed by Berhanu Mekonen, PhD - Arba Minch University</p>
        </div>
    </div>
    </body>
    </html>
    """
    return html

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="School Registration Portal",
    page_icon="SRP🏫@ET",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- CSS ----
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
        padding: 1.5rem 2rem !important;
        border-radius: 16px !important;
        border: 1px solid rgba(255, 215, 0, 0.3) !important;
        margin-bottom: 1rem !important;
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
        gap: 15px;
    }

    .main-header .logo-section {
        display: flex;
        align-items: center;
        gap: 15px;
    }

    .main-header .logo-icon {
        width: 60px;
        height: 60px;
        background: rgba(255, 215, 0, 0.2) !important;
        border: 2px solid #FFD700 !important;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.2rem;
        color: #FFFFFF;
        backdrop-filter: blur(10px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        animation: pulse 3s infinite;
        flex-shrink: 0;
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    .main-header .logo-text h1 {
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        background: none !important;
        -webkit-text-fill-color: #FFFFFF !important;
        margin: 0;
        text-shadow: 0 2px 30px rgba(0,0,0,0.3);
        white-space: nowrap;
    }

    .main-header .logo-text .subtitle {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.9rem !important;
        font-weight: 400 !important;
        margin: 2px 0 0 0;
        text-shadow: 0 1px 15px rgba(0,0,0,0.2);
    }

    .main-header .logo-text .subtitle .highlight {
        color: #FFD700 !important;
        font-weight: 600 !important;
    }

    .main-header .header-right {
        display: flex;
        align-items: center;
        gap: 15px;
        flex-wrap: wrap;
    }

    .main-header .header-stats {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        align-items: center;
    }

    .main-header .stat-item {
        background: rgba(255, 255, 255, 0.12) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        padding: 8px 16px;
        border-radius: 12px;
        text-align: center;
        min-width: 80px;
        transition: all 0.3s;
    }

    .main-header .stat-item:hover {
        border-color: #FFD700;
        transform: translateY(-2px);
        background: rgba(255, 255, 255, 0.2) !important;
    }

    .main-header .stat-item .number {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #FFD700 !important;
        display: block;
        line-height: 1.2;
    }

    .main-header .stat-item .label {
        font-size: 0.75rem !important;
        font-weight: 500 !important;
        color: rgba(255, 255, 255, 0.8) !important;
        display: block;
        margin-top: 2px;
    }

    .status-bar {
        background: #F8F9FA !important;
        border: 1px solid #E8EAED;
        border-radius: 16px;
        padding: 0.8rem 1.5rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 10px;
    }

    .status-bar .status-dot {
        width: 12px;
        height: 12px;
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
        font-size: 1rem !important;
        font-weight: 500 !important;
    }

    .stButton > button {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        padding: 0.7rem 1.8rem !important;
        background: linear-gradient(135deg, #1A73E8, #4285F4) !important;
        color: white !important;
        border-radius: 30px !important;
        border: none !important;
        width: 100%;
        transition: all 0.3s !important;
        box-shadow: 0 2px 8px rgba(26,115,232,0.25) !important;
        min-height: 48px !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 4px 16px rgba(26,115,232,0.35) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #F8F9FA !important;
        border-radius: 16px;
        padding: 6px;
        border: 1px solid #E8EAED;
        flex-wrap: wrap;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 12px;
        padding: 10px 20px;
        color: #5F6368 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
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
        padding: 12px 18px !important;
        font-size: 1.05rem !important;
        font-weight: 400 !important;
        min-height: 48px !important;
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
        padding: 1.2rem;
        margin-bottom: 1rem;
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

    .credential-box {
        background: #F8F9FA;
        border: 1px solid #E8EAED;
        border-radius: 8px;
        padding: 10px 14px;
        margin: 5px 0;
        font-family: 'Courier New', monospace;
    }
    .credential-box .label {
        font-weight: 600;
        color: #5F6368;
        font-size: 0.85rem;
    }
    .credential-box .value {
        font-weight: 700;
        color: #1A73E8;
        font-size: 1rem;
    }
    .credential-box .value.password {
        color: #EA4335;
        background: #FCE8E6;
        padding: 2px 8px;
        border-radius: 4px;
    }

    .student-row {
        display: grid;
        grid-template-columns: 60px 2fr 2fr 1.5fr 1fr;
        gap: 10px;
        align-items: center;
        padding: 10px;
        border-bottom: 1px solid #E8EAED;
        background: white;
        border-radius: 8px;
        margin-bottom: 5px;
    }
    .student-row:hover {
        background: #F8F9FA;
    }
    .student-row .photo { text-align: center; }
    .student-row .name { font-weight: 600; }
    .student-row .id { font-family: monospace; }
    .student-row .password { 
        font-family: monospace;
        background: #FCE8E6;
        padding: 2px 10px;
        border-radius: 4px;
        color: #EA4335;
        font-weight: 700;
    }

    .student-header {
        display: grid;
        grid-template-columns: 60px 2fr 2fr 1.5fr 1fr;
        gap: 10px;
        padding: 10px;
        background: #F1F3F4;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.85rem;
        color: #5F6368;
        margin-bottom: 8px;
    }

    .rank-card {
        background: #FFFFFF;
        border: 1px solid #E8EAED;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
    }
    .rank-card .rank-number {
        font-size: 2rem;
        font-weight: 800;
        color: #1A73E8;
        min-width: 60px;
    }
    .rank-card .student-name {
        font-weight: 600;
        font-size: 1.1rem;
        flex: 1;
        padding: 0 15px;
    }
    .rank-card .student-score {
        font-weight: 700;
        font-size: 1.2rem;
        color: #34A853;
    }

    .edit-delete-btn {
        display: inline-flex;
        gap: 5px;
    }
    .edit-delete-btn .stButton button {
        padding: 0.3rem 0.8rem !important;
        font-size: 0.8rem !important;
        min-height: 30px !important;
        width: auto !important;
    }
    .edit-delete-btn .edit-btn button {
        background: linear-gradient(135deg, #FBBC04, #F9AB00) !important;
    }
    .edit-delete-btn .delete-btn button {
        background: linear-gradient(135deg, #EA4335, #D33426) !important;
    }

    @media (max-width: 768px) {
        .student-row {
            grid-template-columns: 50px 1fr 1fr;
            grid-template-rows: auto auto;
        }
        .student-row .photo { grid-row: span 2; }
        .student-row .reset-btn { grid-column: span 2; }
        .student-header {
            grid-template-columns: 50px 1fr 1fr;
            grid-template-rows: auto auto;
        }
        .block-container { padding: 0.5rem 0.75rem !important; }
        .main-header .logo-text h1 { font-size: 1.4rem !important; white-space: normal !important; }
        .main-header .logo-text .subtitle { font-size: 0.8rem !important; }
        .main-header .header-stats .stat-item { min-width: 60px !important; padding: 6px 10px !important; }
        .main-header .header-stats .stat-item .number { font-size: 1.2rem !important; }
        .main-header .header-stats .stat-item .label { font-size: 0.65rem !important; }
        .main-header .logo-icon { width: 45px !important; height: 45px !important; font-size: 1.6rem !important; }
        .main-header { padding: 1rem !important; }
        .rank-card .rank-number { font-size: 1.5rem; min-width: 40px; }
        .rank-card .student-name { font-size: 0.95rem; }
        .rank-card .student-score { font-size: 1rem; }
    }

    @media (max-width: 480px) {
        .student-row {
            grid-template-columns: 1fr;
            grid-template-rows: auto;
            text-align: center;
        }
        .student-row .photo { grid-row: auto; }
        .student-row .reset-btn { grid-column: auto; }
        .student-header { display: none; }
        .block-container { padding: 0.25rem 0.5rem !important; }
        .main-header .logo-text h1 { font-size: 1.2rem !important; }
        .main-header .header-content { flex-direction: column !important; align-items: flex-start !important; }
        .main-header .header-right { width: 100% !important; flex-direction: column !important; align-items: stretch !important; }
        .main-header .header-stats { display: grid !important; grid-template-columns: 1fr 1fr 1fr !important; gap: 6px !important; }
        .main-header .stat-item { min-width: auto !important; padding: 4px 8px !important; }
        .main-header .stat-item .number { font-size: 1rem !important; }
        .main-header .stat-item .label { font-size: 0.55rem !important; }
        .main-header .logo-icon { width: 35px !important; height: 35px !important; font-size: 1.2rem !important; }
        .login-container { padding: 1.5rem !important; margin: 1rem !important; }
        .rank-card { flex-direction: column; text-align: center; gap: 5px; }
        .rank-card .student-name { padding: 5px 0; }
    }
</style>
""", unsafe_allow_html=True)

# ---- Helper functions continued ----
def get_grade_class(grade):
    grade_num = grade.replace("Grade ", "")
    try:
        num = int(grade_num)
        return "amharic-grade" if num <= 8 else "english-grade"
    except:
        return "english-grade"

def get_student_rank(student_id, grade, section):
    """Get student rank within their grade and section."""
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
    """Get rankings for students in a specific grade and section."""
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

# ---- DEEP STATISTICS SUMMARY ----
def generate_deep_summary():
    """Generate a comprehensive summary of the deep statistics in English and Amharic."""
    stats = generate_deep_statistics()
    
    # Calculate key metrics
    total_students = stats['summary']['total_students']
    pass_rate = stats['summary']['pass_rate']
    passed = stats['summary']['passed']
    failed = stats['summary']['failed']
    
    # Find best and worst subjects
    subject_avgs = stats['subject_analysis']['averages']
    best_subject = max(subject_avgs.items(), key=lambda x: x[1]) if subject_avgs else ("N/A", 0)
    worst_subject = min(subject_avgs.items(), key=lambda x: x[1]) if subject_avgs else ("N/A", 0)
    
    # Grade with best performance
    grade_avgs = stats['grade_analysis']['averages']
    best_grade = max(grade_avgs.items(), key=lambda x: x[1]) if grade_avgs else ("N/A", 0)
    
    # Gender distribution
    gender_data = stats['demographics']['gender']
    male = gender_data.get('Male', 0)
    female = gender_data.get('Female', 0)
    
    summary = {
        'en': f"""
### 📊 School Performance Overview

**Student Population:** The school serves {total_students} students across all grade levels (1-12), with a gender distribution of {male} male and {female} female students.

**Academic Performance:** 
- Overall Pass Rate: {pass_rate}%
- {passed} students passed, {failed} students failed
- Best Performing Subject: {best_subject[0]} ({best_subject[1]}%)
- Area for Improvement: {worst_subject[0]} ({worst_subject[1]}%)
- Best Performing Grade: {best_grade[0]} ({best_grade[1]}%)

**Key Strengths:**
1. Strong performance in core subjects
2. Consistent pass rates across grade levels
3. Balanced gender distribution
4. Effective teacher workload distribution

**Areas for Improvement:**
1. Subject-specific performance gaps
2. Section-wise achievement variations
3. Grade-level transition support needs

**Strategic Recommendations:**
1. Implement targeted support programs for subjects with lower average scores
2. Share successful teaching strategies from high-performing grades
3. Address workload imbalances among teachers
4. Develop intervention programs for sections with lower performance
5. Monitor grade-level transitions to ensure continuity of student progress

**Conclusion:** The school demonstrates strong overall academic performance with a {pass_rate}% pass rate. Continued focus on subject-specific improvements and targeted interventions will further enhance student achievement.
""",
        'am': f"""
### 📊 የትምህርት ቤቱ አጠቃላይ የአፈጻጸም ትንተና

**የተማሪዎች ብዛት:** ትምህርት ቤቱ {total_students} ተማሪዎችን ከ1ኛ እስከ 12ኛ ክፍል ያስተምራል። የፆታ ስርጭት {male} ወንድ እና {female} ሴት ተማሪዎች አሉ።

**አካዳሚክ አፈጻጸም:**
- አጠቃላይ የማለፊያ መቶኛ: {pass_rate}%
- {passed} ተማሪዎች አልፈዋል፣ {failed} ተማሪዎች ወድቀዋል
- ከፍተኛ ውጤት ያለው ትምህርት: {best_subject[0]} ({best_subject[1]}%)
- መሻሻል የሚፈልግ ትምህርት: {worst_subject[0]} ({worst_subject[1]}%)
- ከፍተኛ ውጤት ያለው ክፍል: {best_grade[0]} ({best_grade[1]}%)

**ዋና ዋና ጥንካሬዎች:**
1. በዋና ዋና ትምህርቶች ላይ ጠንካራ አፈጻጸም
2. በክፍሎች መካከል ወጥነት ያለው የማለፊያ መቶኛ
3. ሚዛናዊ የፆታ ስርጭት
4. ውጤታማ የመምህራን የስራ ጫና ስርጭት

**መሻሻል የሚፈልጉ ቦታዎች:**
1. በትምህርት ዓይነቶች መካከል ያለው የአፈጻጸም ልዩነት
2. በክፍሎች መካከል ያለው የአፈጻጸም ልዩነት
3. በክፍሎች መካከል ሽግግር ላይ ድጋፍ የሚያስፈልግባቸው ቦታዎች

**ስልታዊ ምክሮች:**
1. ዝቅተኛ ውጤት ላላቸው ትምህርቶች የድጋፍ ፕሮግራሞችን መተግበር
2. ከፍተኛ ውጤት ካላቸው ክፍሎች የተሻሉ የማስተማር ዘዴዎችን መጋራት
3. በመምህራን መካከል ያለውን የስራ ጫና ልዩነት መቅረፍ
4. ዝቅተኛ ውጤት ላላቸው ክፍሎች የጣልቃ ገብነት ፕሮግራሞችን ማዘጋጀት
5. የተማሪዎችን እድገት ለመከታተል በክፍሎች መካከል ያለውን ሽግግር መከታተል

**ማጠቃለያ:** ትምህርት ቤቱ {pass_rate}% የማለፊያ መቶኛ ያሳያል። በትምህርት ዓይነቶች ላይ የተደረጉ መሻሻሎች እና የታለሙ ጣልቃ ገብነቶች የተማሪዎችን አፈጻጸም የበለጠ ያሻሽላሉ።
"""
    }
    
    return summary

# ---- PROFILE UPDATE ----
def show_profile_update():
    """Allow users to update their own username, password, and profile photo."""
    st.markdown("### 👤 My Profile Settings")
    
    current_username = st.session_state.current_user
    user_data = st.session_state.user_db.get(current_username, {})
    display_name = user_data.get("name", current_username.title())
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown(display_profile_photo(current_username, 120), unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "📸 Update Profile Photo",
            type=["jpg", "jpeg", "png"],
            key="profile_photo_upload"
        )
        if uploaded_file:
            try:
                photo_data = uploaded_file.read()
                if save_profile_photo(current_username, photo_data):
                    st.success("✅ Profile photo updated!")
                    load_all_data()
                    st.rerun()
                else:
                    st.error("Failed to update photo. Please check database column.")
            except Exception as e:
                st.error(f"Error processing image: {e}")
    
    with col2:
        st.markdown(f"**Name:** {display_name}")
        st.markdown(f"**Username:** {current_username}")
        st.markdown(f"**Role:** {user_data.get('role', 'unknown').title()}")
        
        # Show password (for admin only)
        if st.session_state.current_role == "admin":
            st.markdown(f"""
            <div class="credential-box">
                <span class="label">🔑 Admin Password:</span>
                <span class="value password">adminbb</span>
                <span style="font-size:0.8rem;color:#5F6368;margin-left:10px;">(default)</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
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
                        supabase_admin.table("users").update({"username": new_username}).eq("username", current_username).execute()
                        for t in st.session_state.teachers:
                            if t.get("username") == current_username:
                                supabase_admin.table("teachers").update({"username": new_username}).eq("id", t["id"]).execute()
                        st.session_state.user_db[new_username] = st.session_state.user_db.pop(current_username)
                        st.session_state.current_user = new_username
                        add_notification(f"Username changed from {current_username} to {new_username}", "info")
                        st.success(f"✅ Username updated to {new_username}! Please log in again.")
                        logout_user()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update username: {e}")
    
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

# ---- CELEBRATION PAGE ----
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

    try:
        st.html(html_content)
    except AttributeError:
        st.components.v1.html(html_content, height=800, scrolling=False)

# ---- PENALTY LOG & NOTIFICATIONS ----
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

# ---- STUDENT CARD GENERATION ----
def generate_student_card(student, semester="Semester III"):
    name = student.get('name', '_________')
    gender = student.get('gender', '_________')
    age = student.get('age', '_________')
    address = student.get('address', '_________')
    grade = student.get('grade', 'Grade 1')
    section = student.get('section', 'A')
    parent_contact = student.get('parent_contact', '_________')
    academic_year = "2018"
    school_name = st.session_state.school_name

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

    rank_display, _, _ = get_student_rank(student['id'], grade, section)
    rank = rank_display
    amh_comment, eng_comment = get_homeroom_comment(overall_avg)
    absence = "3"
    conduct = "A"
    promoted = str(int(grade.replace("Grade ", "")) + 1) + "ኛ" if overall_avg >= 50 else "_________"

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
        @media (max-width: 768px) {{
            .column {{ flex: 1 1 100%; padding: 4px 6px; min-width: 0; }}
            .page-break {{ border-top: 2px solid #c9a84c; margin-top: 10px; padding-top: 10px; }}
            .info-table {{ font-size: 0.7rem; }}
            .info-table td {{ display: block; width: 100%; padding: 2px 0; }}
            .info-table .label {{ white-space: normal; }}
            .marks-table {{ font-size: 0.6rem; }}
            .marks-table th {{ font-size: 0.55rem; padding: 3px 2px; }}
            .marks-table td {{ font-size: 0.6rem; padding: 2px 2px; }}
        }}
        @media (max-width: 480px) {{
            .card-container {{ padding: 8px 6px; }}
        }}
    </style>
</head>
<body>
<div class="card-container">
    <!-- PAGE 1 -->
    <div class="page">
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
                <tr><td class="label">የወላጅ ስልክ / Parent Contact:</td><td class="value">{parent_contact}</td></tr>
                <tr><td class="label">የትምህርት ዘመን / Academic Year:</td><td class="value">{academic_year}</td></tr>
                <tr><td class="label">ክፍሉ / Grade:</td><td class="value">{grade}</td></tr>
                <tr><td class="label">ክፍል ተዛውሯል/ራለች / Promoted to grade:</td><td class="value">{promoted}</td></tr>
                <tr><td class="label">የት/ቤቱ ርዕሰ መምህር ስም / Director's Name:</td><td class="value">____________________</td></tr>
                <tr><td class="label">ፊርማ / Signature:</td><td class="value">____________________</td></tr>
            </table>
            <div class="motto-box">"ትውልድን የሚተካ ትውልድ በተሻለ ጥራት እናፈራለን"</div>
        </div>
    </div>

    <!-- PAGE 2 -->
    <div class="page page-break">
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
        <div class="column comments-section">
            <div class="section-title">የክፍል መምህሩ አስተያየት / Remarks from Home Room Teacher</div>
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
            <div class="director-sign">
                <span><strong>የርዕሰ መምህሩ ፊርማ / Director's Signature:</strong></span>
                <span class="line"></span>
            </div>
        </div>
    </div>
</div>
</body>
</html>"""
    return html

def show_student_card_panel():
    st.markdown("### 🎓 Student Report Cards")
    st.info("📄 Generate a two-page landscape report card for each student.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        grade_options = ["All"] + [f"Grade {i}" for i in range(1, 13)]
        selected_grade = st.selectbox("Select Grade", grade_options, index=0, key="card_grade")
    with col2:
        # Get sections for selected grade
        if selected_grade != "All":
            sections = sorted(set([s.get("section", "A") for s in st.session_state.students if s.get("grade") == selected_grade]))
            section_options = ["All"] + sections
        else:
            sections = sorted(set([s.get("section", "A") for s in st.session_state.students]))
            section_options = ["All"] + sections
        selected_section = st.selectbox("Select Section", section_options, index=0, key="card_section")
    with col3:
        semester_options = ["Semester I", "Semester II", "Semester III"]
        selected_semester = st.selectbox("Semester", semester_options, index=2, key="card_semester")
    
    # Filter students
    filtered_students = st.session_state.students
    if selected_grade != "All":
        filtered_students = [s for s in filtered_students if s.get("grade") == selected_grade]
    if selected_section != "All":
        filtered_students = [s for s in filtered_students if s.get("section") == selected_section]
    
    if not filtered_students:
        st.info("No students match the selection.")
        return
    
    st.markdown(f"**Found {len(filtered_students)} student(s)**")
    
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
            st.components.v1.html(html, height=600, scrolling=True)

# ---- SUBJECT ADMIN PANEL ----
def show_subject_admin_panel():
    st.markdown("### 📋 Subject Admin Dashboard")
    teacher = get_teacher_by_username(st.session_state.current_user)
    if not teacher:
        st.error("Subject admin profile not found.")
        return
    
    # Show which subjects this admin manages
    admin_assignments = get_subject_mapping_for_admin(teacher["id"])
    if admin_assignments:
        st.markdown("#### 📚 Subjects You Administer:")
        for assign in admin_assignments:
            grade_range = assign.get('grade_range', [])
            grade_str = ", ".join(grade_range) if grade_range else "All Grades"
            st.markdown(f"- **{assign.get('subject')}** (Grades: {grade_str})")
    else:
        st.warning("You are not assigned as a subject admin for any subject.")
    
    my_pending_batches = get_batches_for_subject_admin(teacher["id"])
    if not my_pending_batches:
        st.success("🎉 No pending batches for your subjects.")
        return
    
    for batch in my_pending_batches:
        st.markdown(f"""
        <div class="approval-card pending">
            <h4>📦 Batch from {batch.get('teacher_name', 'Unknown')} · {batch.get('subject', 'N/A')}</h4>
            <p><b>Grade:</b> {batch.get('grade', 'N/A')} · <b>Section:</b> {batch.get('section', 'N/A')}</p>
            <p><b>Semester:</b> {batch.get('semester', 'N/A')}</p>
            <p><b>Students:</b> {len(batch.get('students', []))}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Show student scores preview
        if batch.get('students'):
            with st.expander("📊 View Student Scores"):
                preview_data = []
                for s in batch['students']:
                    preview_data.append({
                        "Name": s.get('student_name', 'Unknown'),
                        "Overall": s.get('overall', 0)
                    })
                st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"✅ Approve", key=f"subj_approve_{batch['id']}", width='stretch'):
                supabase_admin = get_supabase_admin()
                supabase_admin.table("batches").update({"status": "subject_approved"}).eq("id", batch["id"]).execute()
                load_all_data()
                add_notification(f"Batch approved by subject admin", "success")
                st.balloons()
                st.success("✅ Batch approved! It will now go to school admin for final approval.")
                time.sleep(1)
                st.rerun()
        with col2:
            if st.button(f"❌ Reject", key=f"subj_reject_{batch['id']}", width='stretch'):
                supabase_admin = get_supabase_admin()
                supabase_admin.table("batches").update({"status": "rejected"}).eq("id", batch["id"]).execute()
                load_all_data()
                st.warning("❌ Batch rejected!")
                st.rerun()

# ---- TEACHER PANEL ----
def show_teacher_panel():
    st.markdown("### 👨‍🏫 Teacher Dashboard")
    teacher = get_teacher_by_username(st.session_state.current_user)
    if not teacher:
        st.error("❌ Teacher profile not found.")
        return
    
    teacher_id = teacher["id"]
    teacher_name = teacher["name"]
    teacher_subject = teacher.get("subject", "")
    assignments = safe_json_loads(teacher.get("assignments", "[]"))
    
    if not assignments:
        st.warning("No grade/section assignments. Contact admin.")
        return
    
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
    
    st.markdown("#### 📋 Assessment Components")
    comp_df = pd.DataFrame(components)
    st.dataframe(comp_df, use_container_width=True, hide_index=True)
    
    eligible_students = [s for s in st.session_state.students 
                         if s.get("grade") == selected_grade and s.get("section") == selected_section
                         and teacher_subject in s.get("subjects", [])]
    
    if not eligible_students:
        st.info(f"No students in {selected_grade} ({selected_section}) taking {teacher_subject}.")
        return
    
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
    
    st.markdown("#### ✏️ Enter Scores")
    df_edit = pd.DataFrame(student_data)
    
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
    
    for idx, row in edited_df.iterrows():
        total_weighted = 0
        total_weight = 0
        for c in components:
            score = row.get(c["name"], 0)
            total_weighted += score * weights[c["name"]]
            total_weight += weights[c["name"]]
        edited_df.at[idx, "overall"] = round(total_weighted / total_weight, 2) if total_weight > 0 else 0
    
    remarks = st.text_area("Batch Remarks / Comments", value=remarks)
    
    # Find subject admin for this subject and grade
    subject_admin_id = get_subject_admin(teacher_subject, selected_grade)
    
    if subject_admin_id:
        st.info(f"📤 This batch will be sent to the subject admin for approval.")
    else:
        st.warning(f"⚠️ No subject admin assigned for {teacher_subject}. Batch will go directly to school admin.")
    
    if st.button("💾 Submit Batch for Approval", width='stretch'):
        if not is_registration_open():
            st.error("⚠️ Registration period is closed. Cannot submit.")
        else:
            students_list = edited_df.to_dict(orient="records")
            
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

# ---- STUDENT PANEL ----
def show_student_panel():
    st.markdown("### 👨‍🎓 Student Dashboard")
    
    student = get_student_by_username(st.session_state.current_user)
    if not student:
        st.error("❌ Student profile not found. Please contact administrator.")
        return
    
    student_evals = [e for e in st.session_state.evaluations if e.get("student_id") == student["id"]]
    
    col1, col2 = st.columns([1, 3])
    with col1:
        st.markdown(display_student_photo(student["id"], 120), unsafe_allow_html=True)
        uploaded_photo = st.file_uploader("📸 Update Photo", type=["jpg", "jpeg", "png"], key="student_photo_upload")
        if uploaded_photo:
            if save_student_photo(student["id"], uploaded_photo.read()):
                load_all_data()
                st.success("✅ Photo updated!")
                st.rerun()
    
    with col2:
        grade_display = get_grade_display(student["grade"])
        grade_class = get_grade_class(student["grade"])
        st.markdown(f"""
        <div class="student-card">
            <h3>👤 {student['name']}</h3>
            <p><b>🆔 ID:</b> {student['id']}</p>
            <p><b>Age:</b> {student.get('age', 'N/A')}</p>
            <p><b>Grade:</b> <span class="{grade_class}">{grade_display}</span></p>
            <p><b>Section:</b> {student.get('section', 'N/A')}</p>
            <p><b>Subjects:</b> {', '.join(student.get('subjects', []))}</p>
            <p><b>Evaluations:</b> {len(student_evals)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    with st.expander("🔐 My Account Settings", expanded=False):
        st.markdown("#### Change Password")
        user_data = st.session_state.user_db.get(st.session_state.current_user, {})
        
        with st.form("student_change_password"):
            current_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password", width='stretch'):
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
                        supabase_admin.table("users").update({"password": hashed}).eq("username", st.session_state.current_user).execute()
                        st.session_state.user_db[st.session_state.current_user]["password"] = hashed
                        add_notification("Password changed successfully", "success")
                        st.success("✅ Password updated successfully!")
                        st.info("Please use your new password next time you log in.")
                    except Exception as e:
                        st.error(f"Failed to update password: {e}")
    
    if student_evals:
        st.markdown("#### 📝 My Evaluations")
        for eval_item in student_evals:
            status = eval_item.get("status", "pending")
            status_label = "✅ Approved" if status == "approved" else "❌ Rejected" if status == "rejected" else "⏳ Pending"
            status_class = "badge-approved" if status == "approved" else "badge-rejected" if status == "rejected" else "badge-pending"
            st.markdown(f"""
            <div class="eval-card">
                <p><b>📚 Subject:</b> {eval_item.get('subject', 'N/A')}</p>
                <p><b>👨‍🏫 Teacher:</b> {get_teacher_name(eval_item.get('teacher_id', ''))}</p>
                <p><b>📊 Overall Score:</b> {eval_item.get('overall_score', 0)}%</p>
                <p><b>Status:</b> <span class="{status_class}">{status_label}</span></p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No evaluations yet.")

# ---- LOGIN PAGE ----
def show_login_page():
    st.markdown("""
    <div style="text-align:center; padding:1rem 0;">
        <div style="font-size:4rem; margin-bottom:0.5rem;">📚✍️🌍SRP🏫ET ኢትዮጲያ🕊️🎓🚀</div>
        <h1 style="font-size:3rem; margin:0;">School Registration Portal</h1>
        <p style="color:#5F6368; font-size:1.2rem;">👨‍🏫📚 Admin-Controlled Student & Teacher Management</p>
        <p style="color:#5F6368; font-size:0.9rem;">👨‍🎓 Students: Use your ID as username</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        with st.form("login_form"):
            username = st.text_input("👤 Username", placeholder="Enter username (or Student ID)")
            password = st.text_input("🔐 Password", type="password", placeholder="Enter password")
            
            if st.form_submit_button("ET Sign In📚✍️🌍SRP🏫ኢትዮጲያ🕊️🎓🚀", width='stretch'):
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("❌ Please enter both username and password.")
        
        st.markdown("""
        <div style="text-align:center; margin-top:1rem; font-size:0.8rem; color:#5F6368;">
            <p>👨‍🎓 Students: Login with your <b>Student ID</b> as username</p>
            <p>👨‍🏫 Teachers: Login with your username</p>
            <p>👨‍💼 Admin: Use admin credentials</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ---- DEEP STATISTICS DISPLAY FUNCTION ----
def show_deep_statistics():
    """Display deep statistics with interactive charts."""
    st.markdown("## 📊 Deep Statistical Analysis")
    st.markdown("Comprehensive analysis with interactive charts and visualizations for office reporting.")
    
    if not PLOTLY_AVAILABLE:
        st.warning("⚠️ Plotly is not installed. Please add 'plotly' to your requirements.txt to enable charts.")
        st.info("You can still view the data tables and download the report.")
    
    with st.spinner("Generating statistics and charts..."):
        stats = generate_deep_statistics()
        charts = create_statistics_charts(stats) if PLOTLY_AVAILABLE else {}
    
    # Display Summary
    summary = generate_deep_summary()
    with st.expander("📋 Executive Summary - English", expanded=True):
        st.markdown(summary['en'])
    with st.expander("📋 ማጠቃለያ - አማርኛ", expanded=True):
        st.markdown(summary['am'])
    
    st.markdown("---")
    
    # Summary Cards
    st.markdown("### 📈 Key Metrics")
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
    with col1:
        st.metric("👨‍🎓 Students", stats['summary']['total_students'])
    with col2:
        st.metric("👨‍🏫 Teachers", stats['summary']['total_teachers'])
    with col3:
        st.metric("📝 Evaluations", stats['summary']['total_evaluations'])
    with col4:
        st.metric("📦 Batches", stats['summary']['total_batches'])
    with col5:
        st.metric("⏳ Pending", stats['summary']['pending_approvals'])
    with col6:
        st.metric("✅ Passed", stats['summary']['passed'])
    with col7:
        rate_color = "normal" if stats['summary']['pass_rate'] >= 70 else "inverse" if stats['summary']['pass_rate'] >= 50 else "off"
        st.metric("📈 Pass Rate", f"{stats['summary']['pass_rate']}%", delta_color=rate_color)
    
    st.markdown("---")
    
    # Charts in two columns
    if PLOTLY_AVAILABLE and charts:
        col1, col2 = st.columns(2)
        with col1:
            if charts.get('gender_pie'):
                st.plotly_chart(charts['gender_pie'], use_container_width=True)
        with col2:
            if charts.get('pass_rate_gauge'):
                st.plotly_chart(charts['pass_rate_gauge'], use_container_width=True)
        
        if charts.get('grade_distribution'):
            st.plotly_chart(charts['grade_distribution'], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if charts.get('subject_performance'):
                st.plotly_chart(charts['subject_performance'], use_container_width=True)
        with col2:
            if charts.get('grade_performance'):
                st.plotly_chart(charts['grade_performance'], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if charts.get('pass_fail'):
                st.plotly_chart(charts['pass_fail'], use_container_width=True)
        with col2:
            if charts.get('section_performance'):
                st.plotly_chart(charts['section_performance'], use_container_width=True)
            else:
                st.info("No section performance data available.")
        
        if charts.get('teacher_workload'):
            st.plotly_chart(charts['teacher_workload'], use_container_width=True)
    else:
        st.info("📊 Charts unavailable. Please install plotly to see visualizations.")
    
    st.markdown("---")
    
    # Download Report
    st.markdown("### 📄 Download Comprehensive Report")
    st.info("This report includes all charts, tables, and statistics in a professionally formatted HTML document.")
    
    html_report = generate_deep_report_html(stats, charts)
    st.download_button(
        label="📥 Download Deep Statistics Report (HTML)",
        data=html_report.encode('utf-8'),
        file_name=f"Deep_Statistics_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
        mime="text/html",
        width='stretch'
    )
    
    # Detailed Data Tables
    with st.expander("📋 View Detailed Data Tables"):
        st.markdown("#### Subject Performance Details")
        if stats["subject_analysis"]["averages"]:
            subject_df = pd.DataFrame([
                {"Subject": s, "Average": stats['subject_analysis']['averages'].get(s, 0)}
                for s in sorted(stats['subject_analysis']['averages'].keys(), key=lambda x: stats['subject_analysis']['averages'].get(x, 0), reverse=True)
            ])
            st.dataframe(subject_df, use_container_width=True, hide_index=True)
        else:
            st.info("No subject performance data available.")
        
        st.markdown("#### Grade Performance Details")
        if stats["grade_analysis"]["averages"]:
            grade_df = pd.DataFrame([
                {"Grade": g, "Average": stats['grade_analysis']['averages'].get(g, 0)}
                for g in sorted(stats['grade_analysis']['averages'].keys())
            ])
            st.dataframe(grade_df, use_container_width=True, hide_index=True)
        else:
            st.info("No grade performance data available.")
        
        st.markdown("#### Section Performance Details")
        if stats["grade_analysis"]["section_performance"]:
            section_df = pd.DataFrame([
                {"Section": s, "Average": stats['grade_analysis']['section_performance'].get(s, 0)}
                for s in sorted(stats['grade_analysis']['section_performance'].keys(), key=lambda x: stats['grade_analysis']['section_performance'].get(x, 0), reverse=True)
            ])
            st.dataframe(section_df, use_container_width=True, hide_index=True)
        else:
            st.info("No section performance data available.")
        
        st.markdown("#### Teacher Workload Details")
        if stats["teacher_analysis"]["workload"]:
            teacher_df = pd.DataFrame([
                {"Teacher": t, "Batches": stats['teacher_analysis']['workload'][t]['batches'], 
                 "Evaluations": stats['teacher_analysis']['workload'][t]['evaluations']}
                for t in stats['teacher_analysis']['workload'].keys()
            ])
            st.dataframe(teacher_df, use_container_width=True, hide_index=True)
        else:
            st.info("No teacher workload data available.")

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
        
        # Admin Credentials Display
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
            teacher_name = st.text_input("Teacher Full Name *", placeholder="e.g., Abebe Kebede")
            teacher_subject = st.selectbox("Subject Taught *", ALL_SUBJECTS)
            teacher_email = st.text_input("Email Address", placeholder="teacher@school.edu")
            
            # --- NEW: Subject Admin Assignment ---
            st.markdown("---")
            st.markdown("##### 📚 Subject Admin Assignment (Optional)")
            st.caption("If assigned as a Subject Admin, this teacher will approve batches for the selected subject(s) across all grades.")
            is_subject_admin = st.checkbox("Assign this teacher as a Subject Admin", value=False, key="is_subject_admin_check")
            
            subject_admin_subjects = []
            if is_subject_admin:
                subject_admin_subjects = st.multiselect(
                    "Select subjects this teacher will administer (all grades):",
                    options=ALL_SUBJECTS,
                    default=[],
                    key="subject_admin_subjects"
                )
                if subject_admin_subjects:
                    st.info(f"📌 This teacher will be a Subject Admin for: {', '.join(subject_admin_subjects)}")

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

                    supabase_admin = get_supabase_admin()
                    try:
                        # Determine role
                        user_role = "subject_admin" if is_subject_admin and subject_admin_subjects else "teacher"
                        
                        # Create user account
                        supabase_admin.table("users").insert({
                            "username": username,
                            "password": hashed_pw,
                            "role": user_role,
                            "name": teacher_name,
                            "profile_photo": ""
                        }).execute()
                        
                        # Create teacher record with admin_subjects as JSON array
                        supabase_admin.table("teachers").insert({
                            "id": teacher_id,
                            "name": teacher_name,
                            "subject": teacher_subject,
                            "email": teacher_email,
                            "username": username,
                            "password": password,
                            "added": added_time,
                            "assignments": json.dumps(st.session_state.assignments_list),
                            "admin_subjects": json.dumps(subject_admin_subjects) if subject_admin_subjects else json.dumps([])
                        }).execute()
                        
                        # If subject admin, create subject_admin_assignments entries
                        if is_subject_admin and subject_admin_subjects:
                            for subject in subject_admin_subjects:
                                assignment_data = {
                                    "id": str(uuid.uuid4())[:8],
                                    "teacher_id": teacher_id,
                                    "teacher_name": teacher_name,
                                    "subject": subject,
                                    "grade_range": []  # Empty means all grades
                                }
                                try:
                                    supabase_admin.table("subject_admin_assignments").insert(assignment_data).execute()
                                except Exception as e:
                                    if "PGRST204" in str(e) or "PGRST205" in str(e):
                                        st.warning(f"⚠️ Subject Admin Assignments table not found. Please create it in Supabase.")
                                    else:
                                        st.warning(f"Could not create subject admin assignment: {e}")
                        
                        load_all_data()
                        add_notification(f"👨‍🏫 New {'Subject Admin' if is_subject_admin else 'Teacher'} added: {teacher_name}", "success")
                        
                        st.balloons()
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #E8F0FE 0%, #D2E3FC 100%);
                                    padding: 1.5rem;
                                    border-radius: 16px;
                                    border: 3px solid #1A73E8;
                                    margin: 1rem 0;">
                            <h3 style="color: #1A73E8; margin: 0 0 0.5rem 0;">✅ {'Subject Admin' if is_subject_admin else 'Teacher'} Added Successfully!</h3>
                            <div style="background: white; padding: 1rem; border-radius: 10px; margin: 0.5rem 0;">
                                <p><b>👤 Name:</b> {teacher_name}</p>
                                <p><b>📚 Subject:</b> {teacher_subject}</p>
                                <p><b>👤 Role:</b> {'Subject Admin' if is_subject_admin else 'Teacher'}</p>
                                <p><b>🔑 Username:</b> <code style="font-size:1.2rem;background:#f0f0f0;padding:4px 12px;border-radius:4px;">{username}</code></p>
                                <p><b>🔐 Password:</b> <code style="font-size:1.2rem;background:#FCE8E6;padding:4px 12px;border-radius:4px;color:#EA4335;font-weight:700;">{password}</code></p>
                                {f'<p><b>📌 Admin Subjects:</b> {", ".join(subject_admin_subjects)}</p>' if is_subject_admin and subject_admin_subjects else ''}
                            </div>
                            <p style="color: #5F6368; margin-top: 0.5rem; font-size:0.9rem;">
                                ⚠️ Please share these credentials with the {'subject admin' if is_subject_admin else 'teacher'}.
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
                assignments = safe_json_loads(teacher.get("assignments", "[]"))
                assign_str = ", ".join([f"{a['grade']} ({a['section']}) - {a.get('semester', '')}" for a in assignments]) if assignments else "None"
                teacher_password = teacher.get('password', 'N/A')
                admin_subjects = safe_json_loads(teacher.get("admin_subjects", "[]"))
                is_admin = "subject_admin" in st.session_state.user_db.get(teacher.get("username", ""), {}).get("role", "")
                added_date = teacher.get('added', 'N/A')
                
                # Build the teacher card HTML as a single string
                html_card = f"""<div class="teacher-card">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                        <div>
                            <h4>👨‍🏫 {teacher['name']}</h4>
                            <p><b>📚 Subject:</b> {teacher['subject']}</p>
                            <p><b>📌 Assignments:</b> {assign_str}</p>
                            <p><b>✉️ Email:</b> {teacher.get('email', 'N/A')}</p>
                        </div>
                        <div style="text-align:right;">
                            <span style="background:{'#E8F0FE' if is_admin else '#E6F4EA'};padding:4px 12px;border-radius:20px;font-size:0.8rem;font-weight:600;">
                                {'📋 Subject Admin' if is_admin else '👨‍🏫 Teacher'}
                            </span>
                        </div>
                    </div>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-top:8px;background:#F8F9FA;padding:10px;border-radius:8px;">
                        <div><b>👤 Username:</b> <code>{teacher.get('username', 'N/A')}</code></div>
                        <div><b>🔑 Password:</b> <code style="background:#FCE8E6;padding:2px 10px;border-radius:4px;color:#EA4335;font-weight:700;">{teacher_password}</code></div>
                    </div>
                    {f'<div style="margin-top:6px;font-size:0.85rem;color:#1A73E8;"><b>📌 Admin Subjects:</b> {", ".join(admin_subjects)}</div>' if admin_subjects else ''}
                    <div style="margin-top:8px;font-size:0.85rem;color:#5F6368;">
                        <b>📅 Added:</b> {added_date}
                    </div>
                </div>"""
                
                st.markdown(html_card, unsafe_allow_html=True)

    # Tab 4: Subjects
    with tab5:
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
        st.markdown("#### ✅ Pending Batches for Final Approval")
        pending_batches = get_batches_awaiting_final_approval()
        if not pending_batches:
            st.success("🎉 No pending batches awaiting final approval.")
            st.balloons()
        else:
            for batch in pending_batches:
                st.markdown(f"""
                <div class="approval-card pending">
                    <h4>📦 Batch from {batch.get('teacher_name', 'Unknown')} · {batch.get('subject', 'N/A')}</h4>
                    <p><b>Grade:</b> {batch.get('grade', 'N/A')} · <b>Section:</b> {batch.get('section', 'N/A')}</p>
                    <p><b>Semester:</b> {batch.get('semester', 'N/A')}</p>
                    <p><b>Status:</b> {'Subject Approved' if batch.get('status') == 'subject_approved' else 'Pending'}</p>
                    <p><b>Students:</b> {len(batch.get('students', []))}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Show student scores preview
                if batch.get('students'):
                    with st.expander("📊 View Student Scores"):
                        preview_data = []
                        for s in batch['students']:
                            preview_data.append({
                                "Name": s.get('student_name', 'Unknown'),
                                "Overall": s.get('overall', 0)
                            })
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve", key=f"approve_{batch['id']}", width='stretch'):
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

    # Tab 7: Rankings
    with tab8:
        st.markdown("#### 📊 Grade and Section Rankings")
        
        col1, col2 = st.columns(2)
        with col1:
            grade_options = [f"Grade {i}" for i in range(1, 13)]
            selected_rank_grade = st.selectbox("Select Grade", grade_options, key="rank_grade")
        with col2:
            # Get sections for selected grade
            sections = sorted(set([s.get("section", "A") for s in st.session_state.students if s.get("grade") == selected_rank_grade]))
            section_options = ["All"] + sections
            selected_rank_section = st.selectbox("Select Section", section_options, key="rank_section")
        
        if selected_rank_section == "All":
            students_to_rank = [s for s in st.session_state.students if s.get("grade") == selected_rank_grade]
        else:
            students_to_rank = [s for s in st.session_state.students 
                               if s.get("grade") == selected_rank_grade and s.get("section") == selected_rank_section]
        
        if not students_to_rank:
            st.info(f"No students in {selected_rank_grade}{' - Section ' + selected_rank_section if selected_rank_section != 'All' else ''}")
        else:
            rankings = get_rankings_by_grade_section(selected_rank_grade, selected_rank_section if selected_rank_section != "All" else students_to_rank[0].get("section", "A"))
            
            # If "All" sections, combine all students
            if selected_rank_section == "All":
                all_students = []
                for s in students_to_rank:
                    evals = get_approved_evaluations_for_student(s["id"])
                    avg_score = round(sum(e.get("overall_score", 0) for e in evals) / len(evals), 2) if evals else 0
                    all_students.append({
                        "id": s["id"],
                        "name": s["name"],
                        "section": s.get("section", "A"),
                        "avg": avg_score,
                        "gender": s.get("gender", "N/A"),
                        "evaluations": len(evals)
                    })
                sorted_students = sorted(all_students, key=lambda x: x["avg"], reverse=True)
                for i, s in enumerate(sorted_students):
                    s["rank"] = i + 1
                rankings = sorted_students
            else:
                rankings = get_rankings_by_grade_section(selected_rank_grade, selected_rank_section)
            
            st.markdown(f"**📊 Rankings for {selected_rank_grade} - Section {selected_rank_section if selected_rank_section != 'All' else 'All Sections'}**")
            
            # Display rankings with medals
            for student in rankings:
                rank = student.get("rank", 0)
                medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
                st.markdown(f"""
                <div class="rank-card">
                    <div class="rank-number">{medal}</div>
                    <div class="student-name">👤 {student['name']}</div>
                    <div style="color:#5F6368;font-size:0.9rem;">Section: {student.get('section', 'A')}</div>
                    <div class="student-score">{student['avg']}%</div>
                </div>
                """, unsafe_allow_html=True)

    # Tab 8: Students
    with tab9:
        st.markdown("#### 👨‍🎓 Student Management")
        
        # Add Student with Photo and Parent Contact
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
                    parent_contact = st.text_input("Parent/Guardian Contact Number *")
                    section = st.text_input("Section", value="A")
                    student_photo = st.file_uploader("📸 Student Photo", type=["jpg", "jpeg", "png"])
                
                if st.form_submit_button("Add Student", width='stretch'):
                    if name and parent_contact:
                        existing_ids = [int(s['id'][1:]) for s in st.session_state.students if s['id'].startswith('S')]
                        next_num = max(existing_ids) + 1 if existing_ids else 1
                        student_id = f"S{next_num:04d}"
                        
                        photo_encoded = ""
                        if student_photo:
                            try:
                                img = Image.open(student_photo)
                                img.thumbnail((300, 300))
                                img_bytes = io.BytesIO()
                                img.save(img_bytes, format='PNG')
                                photo_encoded = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                            except:
                                pass
                        
                        new_student = {
                            "id": student_id,
                            "name": name,
                            "age": age,
                            "gender": gender,
                            "grade": grade,
                            "section": section,
                            "subjects": GRADE_SUBJECTS.get(grade, []),
                            "parent_name": parent,
                            "parent_contact": parent_contact,
                            "profile_photo": photo_encoded,
                            "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        supabase_admin = get_supabase_admin()
                        try:
                            supabase_admin.table("students").insert(new_student).execute()
                            load_all_data()
                            add_notification(f"👨‍🎓 Student {name} added", "success")
                            
                            # Create student user account with password
                            student_pw, msg = create_student_user(student_id, name)
                            if student_pw:
                                st.markdown(f"""
                                <div style="background: #E6F4EA; padding: 1rem; border-radius: 12px; 
                                            border: 2px solid #34A853; margin: 1rem 0;">
                                    <h4 style="color: #34A853; margin: 0;">✅ Student Account Created!</h4>
                                    <p><b>👤 Student ID:</b> <code>{student_id}</code></p>
                                    <p><b>🔑 Temporary Password:</b> <code style="font-size:1.1rem;background:#f0f0f0;padding:2px 10px;border-radius:4px;">{student_pw}</code></p>
                                    <p style="color: #5F6368; font-size:0.85rem;">⚠️ Student can change password after login.</p>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.success(f"✅ Student {name} added!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Failed to add student: {e}")
                    else:
                        st.error("Name and Parent Contact Number are required.")

        # List Students with Photos, Passwords and Parent Contact
        if st.session_state.students:
            st.markdown("#### 📋 All Students")
            
            search_student = st.text_input("🔍 Search Student", placeholder="Type name or ID...")
            
            # Filter by grade and section
            col1, col2 = st.columns(2)
            with col1:
                grade_filter = st.selectbox("Filter by Grade", ["All"] + [f"Grade {i}" for i in range(1, 13)])
            with col2:
                if grade_filter != "All":
                    sections = sorted(set([s.get("section", "A") for s in st.session_state.students if s.get("grade") == grade_filter]))
                    section_filter = st.selectbox("Filter by Section", ["All"] + sections)
                else:
                    sections = sorted(set([s.get("section", "A") for s in st.session_state.students]))
                    section_filter = st.selectbox("Filter by Section", ["All"] + sections)
            
            filtered_students = st.session_state.students
            if search_student:
                search_lower = search_student.lower()
                filtered_students = [s for s in filtered_students 
                                   if search_lower in s.get('name', '').lower() or 
                                      search_lower in s.get('id', '').lower()]
            if grade_filter != "All":
                filtered_students = [s for s in filtered_students if s.get("grade") == grade_filter]
            if section_filter != "All":
                filtered_students = [s for s in filtered_students if s.get("section") == section_filter]
            
            # Display header
            st.markdown("""
            <div class="student-header">
                <div>📷</div>
                <div>👤 Name</div>
                <div>📚 Grade</div>
                <div>📱 Contact</div>
                <div style="text-align:center;">Action</div>
            </div>
            """, unsafe_allow_html=True)
            
            for student in filtered_students:
                student_id = student.get('id', 'N/A')
                
                # Get password from session or student record
                student_password = get_student_password(student_id)
                if student_password == "Not set":
                    student_password = "🔑 Set Password"
                    color = "#F9AB00"
                else:
                    color = "#EA4335"
                
                col1, col2, col3, col4, col5 = st.columns([1, 2, 1.5, 1.5, 1])
                with col1:
                    st.markdown(display_student_photo(student_id, 50), unsafe_allow_html=True)
                with col2:
                    st.markdown(f"**{student.get('name', 'Unknown')}**")
                    # Edit and Delete buttons for student
                    col2a, col2b = st.columns([1, 1])
                    with col2a:
                        if st.button(f"✏️ Edit", key=f"edit_student_{student_id}", width='stretch'):
                            st.session_state.editing_student = student_id
                            st.rerun()
                    with col2b:
                        if st.button(f"🗑️ Delete", key=f"delete_student_{student_id}", width='stretch'):
                            if st.session_state.get('confirm_delete_student') == student_id:
                                # Actually delete
                                supabase_admin = get_supabase_admin()
                                try:
                                    supabase_admin.table("students").delete().eq("id", student_id).execute()
                                    # Also delete user account
                                    supabase_admin.table("users").delete().eq("username", student_id).execute()
                                    load_all_data()
                                    add_notification(f"Student {student.get('name', '')} deleted", "warning")
                                    st.session_state.confirm_delete_student = None
                                    st.success("✅ Student deleted successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error deleting student: {e}")
                            else:
                                st.session_state.confirm_delete_student = student_id
                                st.warning(f"⚠️ Click Delete again to confirm deletion of {student.get('name', '')}")
                                st.rerun()
                with col3:
                    st.markdown(f"{student.get('grade', 'N/A')} · {student.get('section', 'N/A')}")
                with col4:
                    st.markdown(f"""
                    <div style="font-size:0.85rem;">
                        <div><span style="font-weight:600;">Parent:</span> {student.get('parent_name', 'N/A')}</div>
                        <div><span style="font-weight:600;">📱:</span> {student.get('parent_contact', 'N/A')}</div>
                        <div style="font-size:0.7rem;margin-top:2px;">
                            <span style="background:#FCE8E6;padding:2px 8px;border-radius:4px;color:{color};font-weight:600;">{student_password}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with col5:
                    if st.button(f"🔄 Reset", key=f"reset_student_pw_{student_id}", width='stretch'):
                        new_pw = reset_student_password(student_id)
                        if new_pw:
                            st.success(f"✅ New password: `{new_pw}`")
                            add_notification(f"Password reset for student {student.get('name', '')}", "info")
                            st.rerun()
                        else:
                            st.error("Failed to reset password")

    # Tab 9: Import/Export
    with tab10:
        st.markdown("### 📥 Import / Export Data")
        uploaded_file = st.file_uploader("Upload Excel file (.xlsx)", type=["xlsx"])
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df, use_container_width=True)
                if st.button("Import Students", width='stretch'):
                    supabase = get_supabase_admin()
                    count = 0
                    for _, row in df.iterrows():
                        if pd.notna(row.get("Name")):
                            existing_ids = [int(s['id'][1:]) for s in st.session_state.students if s['id'].startswith('S')]
                            next_num = max(existing_ids) + 1 if existing_ids else 1
                            student_id = f"S{next_num:04d}"
                            student = {
                                "id": student_id,
                                "name": str(row.get("Name", "")),
                                "grade": str(row.get("Grade", "Grade 1")),
                                "section": str(row.get("Section", "A")),
                                "gender": str(row.get("Gender", "")),
                                "parent_name": str(row.get("Parent", "")),
                                "parent_contact": str(row.get("Parent Contact", "")),
                                "profile_photo": "",
                                "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "subjects": GRADE_SUBJECTS.get(str(row.get("Grade", "Grade 1")), [])
                            }
                            supabase.table("students").insert(student).execute()
                            create_student_user(student_id, student['name'])
                            count += 1
                    load_all_data()
                    st.success(f"✅ Imported {count} students with accounts!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Tab 10: Reports
    with tab11:
        st.markdown("### 📄 School Reports")
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
        
        html_report = generate_statistics_report()
        st.download_button(
            label="📥 Download Full Report (HTML)",
            data=html_report.encode('utf-8'),
            file_name=f"School_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
            mime="text/html",
            width='stretch'
        )

    # Tab 11: Penalty Log
    with tab12:
        show_penalty_log()

    # Tab 12: Settings
    with tab13:
        st.markdown("### 🏫 School Settings")
        new_name = st.text_input("School Name", value=st.session_state.school_name)
        new_city = st.text_input("City/Town", value=st.session_state.school_city)
        new_director = st.text_input("Director's Name", value=st.session_state.director_name)
        if st.button("💾 Update School Settings", width='stretch'):
            st.session_state.school_name = new_name
            st.session_state.school_city = new_city
            st.session_state.director_name = new_director
            st.success("✅ School settings updated!")

    # Tab 13: Homeroom
    with tab14:
        st.markdown("### 👨‍🏫 Homeroom Teacher Assignments")
        st.markdown("Assign a homeroom teacher to each grade and section.")
        
        # Add homeroom assignment
        with st.form("add_homeroom"):
            col1, col2, col3 = st.columns(3)
            with col1:
                grade_options = [f"Grade {i}" for i in range(1, 13)]
                homeroom_grade = st.selectbox("Grade", grade_options)
            with col2:
                # Get sections for the selected grade
                if homeroom_grade:
                    sections = sorted(set([s.get("section", "A") for s in st.session_state.students if s.get("grade") == homeroom_grade]))
                    if not sections:
                        sections = ["A"]
                    homeroom_section = st.selectbox("Section", sections)
                else:
                    homeroom_section = st.text_input("Section", "A")
            with col3:
                teacher_options = ["None"] + [f"{t['name']} ({t.get('username', '')})" for t in st.session_state.teachers]
                homeroom_teacher = st.selectbox("Homeroom Teacher", teacher_options)
            
            if st.form_submit_button("Assign Homeroom Teacher", width='stretch'):
                if homeroom_teacher != "None" and homeroom_grade:
                    teacher_name = homeroom_teacher.split(" (")[0]
                    teacher_id = None
                    for t in st.session_state.teachers:
                        if t['name'] == teacher_name:
                            teacher_id = t['id']
                            break
                    
                    if teacher_id:
                        supabase_admin = get_supabase_admin()
                        # Check if assignment already exists
                        existing = None
                        for h in st.session_state.homeroom_assignments:
                            if h.get('grade') == homeroom_grade and h.get('section') == homeroom_section:
                                existing = h
                                break
                        
                        if existing:
                            supabase_admin.table("homeroom_assignments").update({
                                "teacher_id": teacher_id,
                                "teacher_name": teacher_name
                            }).eq("id", existing["id"]).execute()
                        else:
                            supabase_admin.table("homeroom_assignments").insert({
                                "grade": homeroom_grade,
                                "section": homeroom_section,
                                "teacher_id": teacher_id,
                                "teacher_name": teacher_name
                            }).execute()
                        load_all_data()
                        add_notification(f"Homeroom teacher assigned for {homeroom_grade} - Section {homeroom_section}", "success")
                        st.success(f"✅ Homeroom teacher assigned for {homeroom_grade} - Section {homeroom_section}")
                        st.rerun()
                    else:
                        st.error("Teacher not found.")
                else:
                    st.warning("Please select a grade, section, and teacher.")
        
        st.markdown("---")
        st.markdown("#### 📋 Current Homeroom Assignments")
        
        if st.session_state.homeroom_assignments:
            assignments_data = []
            for h in st.session_state.homeroom_assignments:
                assignments_data.append({
                    "Grade": h.get('grade', ''),
                    "Section": h.get('section', ''),
                    "Homeroom Teacher": h.get('teacher_name', 'Unknown')
                })
            st.dataframe(pd.DataFrame(assignments_data), use_container_width=True, hide_index=True)
            
            # Option to remove assignment
            for h in st.session_state.homeroom_assignments:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                with col1:
                    st.markdown(f"**{h.get('grade', '')}**")
                with col2:
                    st.markdown(f"Section {h.get('section', '')}")
                with col3:
                    st.markdown(f"👨‍🏫 {h.get('teacher_name', 'Unknown')}")
                with col4:
                    if st.button("🗑️ Remove", key=f"remove_homeroom_{h.get('id', '')}", width='stretch'):
                        supabase_admin = get_supabase_admin()
                        supabase_admin.table("homeroom_assignments").delete().eq("id", h.get("id")).execute()
                        load_all_data()
                        st.rerun()
        else:
            st.info("No homeroom assignments yet.")

    # Tab 14: Student Cards
    with tab15:
        show_student_card_panel()

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
