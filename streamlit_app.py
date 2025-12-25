import streamlit as st
import pandas as pd
import random
import time
import os
import streamlit as st

st.write("FILES STREAMLIT SEES:")
st.write(os.listdir("."))

# ================= CONFIG =================
st.set_page_config(page_title="Govt Exam Practice Test", layout="centered")

DATA_PATH = "govt_exam_3000_questions_SYNTHETIC_FIXED_TIME.csv"
LEVELS = ["Easy", "Medium", "Hard"]

# ================= LOAD DATA =================
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    return df.fillna("")

df = load_data()

# ================= SESSION STATE INIT =================
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.q_no = 0
    st.session_state.score = 0
    st.session_state.current_level = "Easy"
    st.session_state.block_answers = []     # store last 3 results
    st.session_state.used_ids = set()
    st.session_state.used_concepts = set()

# ================= START PAGE =================
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
        st.rerun()

# ================= QUESTION SELECTOR =================
def get_next_question():
    level = st.session_state.current_level

    pool = df[
        (df["subject"] == st.session_state.subject) &
        (df["difficulty"] == level) &
        (~df["question_id"].isin(st.session_state.used_ids))
    ]

    # rotate concepts within block
    if st.session_state.used_concepts:
        pool = pool[~pool["concept"].isin(st.session_state.used_concepts)]

    if pool.empty:
        st.session_state.used_concepts.clear()
        pool = df[
            (df["subject"] == st.session_state.subject) &
            (df["difficulty"] == level) &
            (~df["question_id"].isin(st.session_state.used_ids))
        ]

    return pool.sample(1).iloc[0]

# ================= TEST PAGE =================
if st.session_state.started:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = st.session_state.time_limit - elapsed

    if remaining <= 0 or st.session_state.q_no >= st.session_state.total_qs:
        st.subheader("✅ Test Completed")
        st.write(f"Score: {st.session_state.score} / {st.session_state.total_qs}")
        st.write(f"Final Level Reached: {st.session_state.current_level}")
        st.stop()

    q = get_next_question()

    st.session_state.used_ids.add(q["question_id"])
    st.session_state.used_concepts.add(q["concept"])

    st.subheader(f"Question {st.session_state.q_no + 1}")
    st.info(f"Difficulty Level: {st.session_state.current_level}")
    st.write(q["question_text"])

    options = {
        "A": q["option_a"],
        "B": q["option_b"],
        "C": q["option_c"],
        "D": q["option_d"]
    }

    choice = st.radio(
        "Choose one option:",
        list(options.keys()),
        format_func=lambda x: f"{x}. {options[x]}",
        index=None
    )

    if st.button("Submit Answer"):
        correct = q["correct_option"]

        if choice == correct:
            st.success("✅ Correct")
            st.session_state.score += 1
            st.session_state.block_answers.append(True)
        else:
            st.error(f"❌ Wrong | Correct answer: {correct}")
            st.session_state.block_answers.append(False)

        st.session_state.q_no += 1

        # ===== BLOCK LOGIC (3 QUESTIONS) =====
        if len(st.session_state.block_answers) == 3:
            if all(st.session_state.block_answers):
                idx = LEVELS.index(st.session_state.current_level)
                if idx < len(LEVELS) - 1:
                    st.session_state.current_level = LEVELS[idx + 1]
                    st.info(f"⬆ Level Up → {st.session_state.current_level}")

            st.session_state.block_answers.clear()
            st.session_state.used_concepts.clear()

        st.rerun()
