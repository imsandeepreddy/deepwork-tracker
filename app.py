import streamlit as st
from supabase import create_client
from datetime import datetime, date

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Focus Tracker",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------- SUPABASE ----------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# ---------------- STATE ----------------
if "running" not in st.session_state:
    st.session_state.running = False

if "start_time" not in st.session_state:
    st.session_state.start_time = None

# ---------------- UI ----------------
st.title("🎯 Focus & Deep Work Tracker")

task = st.text_input("What are you focusing on?")
category = st.selectbox(
    "Category",
    ["Work", "Study", "Learning", "Personal"]
)

# ---------------- FOCUS TIMER ----------------
if not st.session_state.running:
    if st.button("▶ Start Focus", use_container_width=True):
        if not task.strip():
            st.warning("Enter a task before starting.")
        else:
            st.session_state.running = True
            st.session_state.start_time = datetime.utcnow()
else:
    elapsed = datetime.utcnow() - st.session_state.start_time
    minutes = int(elapsed.total_seconds() // 60)

    st.metric("Focused Minutes", minutes)

    if st.button("⏹ Stop Focus", use_container_width=True):
        end_time = datetime.utcnow()
        duration = max(1, int((end_time - st.session_state.start_time).total_seconds() // 60))

        supabase.table("focus_sessions").insert({
            "session_date": date.today().isoformat(),
            "task": task,
            "category": category,
            "start_time": st.session_state.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration,
            "notes": ""
        }).execute()

        st.session_state.running = False
        st.success("Session saved")

# ---------------- TODAY SUMMARY ----------------
st.divider()
st.subheader("📊 Today")

today_sessions = (
    supabase
    .table("focus_sessions")
    .select("duration_minutes, category")
    .eq("session_date", date.today().isoformat())
    .execute()
    .data
)

total_minutes = sum(s["duration_minutes"] for s in today_sessions) if today_sessions else 0
st.metric("Total Focus Time (minutes)", total_minutes)

# ---------------- CATEGORY BREAKDOWN ----------------
if today_sessions:
    breakdown = {}
    for s in today_sessions:
        breakdown[s["category"]] = breakdown.get(s["category"], 0) + s["duration_minutes"]

    st.subheader("By Category")
    for k, v in breakdown.items():
        st.write(f"**{k}**: {v} min")

# ---------------- HISTORY (LAST 7 DAYS) ----------------
st.divider()
st.subheader("🗓 Recent Sessions")

history = (
    supabase
    .table("focus_sessions")
    .select("session_date, task, category, duration_minutes")
    .order("start_time", desc=True)
    .limit(20)
    .execute()
    .data
)

if history:
    st.dataframe(history, use_container_width=True)
else:
    st.caption("No sessions yet")
