import streamlit as st
import pandas as pd
import random
import time

# ===================== CONFIG =====================
st.set_page_config(page_title="Government Exam Practice Test", layout="centered")

DATA_PATH = "govt_exam_3000_questions_CORRECTED.csv"
LEVELS = ["Easy", "Medium", "Hard"]

# ===================== LOAD DATA =====================
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.fillna("")

    # 🔍 Auto-detect difficulty column
    if "difficulty" in df.columns:
        df["__difficulty__"] = df["difficulty"]
    elif "difficulty_level" in df.columns:
        df["__difficulty__"] = df["difficulty_level"]
    elif "level" in df.columns:
        df["__difficulty__"] = df["level"]
    else:
        # If no difficulty column, assume ALL Easy
        df["__difficulty__"] = "Easy"

    return df

df = load_data()

# ===================== SESSION STATE =====================
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.q_no = 0
    st.session_state.score = 0
    st.session_state.current_level = "Easy"
    st.session_state.block_answers = []
    st.session_state.used_ids = set()
    st.session_state.used_concepts = set()

# ===================== START PAGE =====================
if not st.session_state.started:
    st.title("📝 Government Exam Practice Test")

    subject = st.selectbox("Select Subject", df["subject"].unique())
    total_qs = st.selectbox("Number of Questions", [30, 50, 100])

    if st.button("Start Test"):
        st.session_state.started = True
        st.session_state.subject = subject
        st.session_state.total_qs = total_qs
        st.session_state.start_time = time.time()
        st.session_state.time_limit = total_qs * 60
        st.session_state.q_no = 0
        st.session_state.score = 0
        st.session_state.current_level = "Easy"
        st.session_state.block_answers = []
        st.session_state.used_ids = set()
        st.session_state.used_concepts = set()
        st.rerun()

# ===================== QUESTION SELECTOR =====================
def get_next_question():
    level = st.session_state.current_level

    pool = df[
        (df["subject"] == st.session_state.subject) &
        (df["__difficulty__"] == level) &
        (~df["question_id"].isin(st.session_state.used_ids))
    ]

    # Rotate concepts inside a block
    if st.session_state.used_concepts and "concept" in df.columns:
        pool = pool[~pool["concept"].isin(st.session_state.used_concepts)]

    # Reset concept filter if empty
    if pool.empty:
        st.session_state.used_concepts.clear()
        pool = df[
            (df["subject"] == st.session_state.subject) &
            (df["__difficulty__"] == level) &
            (~df["question_id"].isin(st.session_state.used_ids))
        ]

    return pool.sample(1).iloc[0]

# ===================== TEST PAGE =====================
if st.session_state.started:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = st.session_state.time_limit - elapsed

    if remaining <= 0 or st.session_state.q_no >= st.session_state.total_qs:
        st.subheader("✅ Test Completed")
        st.write(f"Score: **{st.session_state.score} / {st.session_state.total_qs}**")
        st.write(f"Final Difficulty Level: **{st.session_state.current_level}**")
        st.stop()

    def get_next_question():
    level = st.session_state.current_level
    subject = st.session_state.subject

    # 1️⃣ Strict filter: subject + level + unused + new concept
    pool = df[
        (df["subject"] == subject) &
        (df["__difficulty__"] == level) &
        (~df["question_id"].isin(st.session_state.used_ids))
    ]

    if st.session_state.used_concepts and "concept" in df.columns:
        pool = pool[~pool["concept"].isin(st.session_state.used_concepts)]

    # 2️⃣ Relax concept constraint
    if pool.empty:
        pool = df[
            (df["subject"] == subject) &
            (df["__difficulty__"] == level) &
            (~df["question_id"].isin(st.session_state.used_ids))
        ]

    # 3️⃣ Relax difficulty constraint (last resort)
    if pool.empty:
        pool = df[
            (df["subject"] == subject) &
            (~df["question_id"].isin(st.session_state.used_ids))
        ]

    # 4️⃣ Absolute fallback
    if pool.empty:
        st.error("⚠️ No more questions available.")
        st.stop()

    return pool.sample(1).iloc[0]
