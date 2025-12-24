import streamlit as st
from supabase import create_client
from datetime import datetime, date, timedelta

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

if "mode" not in st.session_state:
    st.session_state.mode = "Normal"

if "daily_goal" not in st.session_state:
    st.session_state.daily_goal = 120  # minutes

# ---------------- UI ----------------
st.title("🎯 Focus & Deep Work Tracker")

task = st.text_input("What are you focusing on?")
category = st.selectbox(
    "Category",
    ["Work", "Study", "Learning", "Personal"]
)

# ---------------- MODES ----------------
st.subheader("⚙️ Focus Mode")

st.session_state.mode = st.radio(
    "Mode",
    ["Normal", "Pomodoro (25 min)"],
    horizontal=True
)

st.session_state.daily_goal = st.number_input(
    "Daily Focus Goal (minutes)",
    min_value=30,
    max_value=600,
    step=30,
    value=st.session_state.daily_goal
)

# ---------------- FOCUS TIMER ----------------
FOCUS_LIMIT = 25 if st.session_state.mode.startswith("Pomodoro") else None

if not st.session_state.running:
    if st.button("▶ Start Focus", use_container_width=True):
        if not task.strip():
            st.warning("Enter a task before starting.")
        else:
            st.session_state.running = True
            st.session_state.start_time = datetime.utcnow()
else:
    now = datetime.utcnow()
    elapsed = now - st.session_state.start_time
    elapsed_minutes = int(elapsed.total_seconds() // 60)

    if FOCUS_LIMIT:
        remaining = max(0, FOCUS_LIMIT - elapsed_minutes)
        st.metric("Pomodoro Remaining (min)", remaining)

        if remaining == 0:
            st.warning("Pomodoro complete! Take a 5-minute break.")

    else:
        st.metric("Focused Minutes", elapsed_minutes)

    if st.button("⏹ Stop & Save", use_container_width=True):
        end_time = datetime.utcnow()
        duration = max(1, int((end_time - st.session_state.start_time).total_seconds() // 60))

        supabase.table("focus_sessions").insert({
            "session_date": date.today().isoformat(),
            "task": task,
            "category": category,
            "start_time": st.session_state.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_minutes": duration,
            "notes": st.session_state.mode
        }).execute()

        st.session_state.running = False
        st.success("Session saved")

# ---------------- TODAY SUMMARY ----------------
st.divider()
st.subheader("📊 Today")

today_sessions = (
    supabase
    .table("focus_sessions")
    .select("duration_minutes")
    .eq("session_date", date.today().isoformat())
    .execute()
    .data
)

total_minutes = sum(s["duration_minutes"] for s in today_sessions) if today_sessions else 0

st.metric("Total Focus Time (minutes)", total_minutes)

# ---------------- GOAL PROGRESS ----------------
progress = min(total_minutes / st.session_state.daily_goal, 1.0)
st.progress(progress)

if total_minutes >= st.session_state.daily_goal:
    st.success("🎉 Daily focus goal achieved!")
else:
    st.caption(f"{st.session_state.daily_goal - total_minutes} minutes to reach today’s goal")

# ---------------- RECENT HISTORY ----------------
st.divider()
st.subheader("🗓 Recent Sessions")

history = (
    supabase
    .table("focus_sessions")
    .select("session_date, task, category, duration_minutes, notes")
    .order("start_time", desc=True)
    .limit(15)
    .execute()
    .data
)

if history:
    st.dataframe(history, use_container_width=True)
else:
    st.caption("No sessions yet")
