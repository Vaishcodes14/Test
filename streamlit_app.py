import streamlit as st
import pandas as pd
import time
import random

# ===================== CONFIG =====================
st.set_page_config(page_title="Government Exam Practice Test", layout="centered")

DATA_PATH = "govt_exam_3000_questions_CORRECTED.csv"
LEVELS = ["Easy", "Medium", "Hard"]

# ===================== LOAD DATA =====================
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df = df.fillna("")

    # Normalize subject & concept
    for col in ["subject", "concept"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # Normalize difficulty
    if "difficulty" in df.columns:
        df["__difficulty__"] = df["difficulty"].astype(str).str.title()
    elif "difficulty_level" in df.columns:
        df["__difficulty__"] = df["difficulty_level"].astype(str).str.title()
    elif "level" in df.columns:
        df["__difficulty__"] = df["level"].astype(str).str.title()
    else:
        df["__difficulty__"] = "Easy"

    return df

df = load_data()

# ===================== SESSION STATE =====================
if "started" not in st.session_state:
    st.session_state.started = False
    st.session_state.q_no = 0
    st.session_state.score = 0
    st.session_state.current_level = "Easy"
    st.session_state.block_answers = []      # last 3 answers
    st.session_state.used_ids = set()
    st.session_state.used_concepts = set()

# ===================== START PAGE =====================
if not st.session_state.started:
    st.title("📝 Government Exam Practice Test")

    subject = st.selectbox("Select Subject", sorted(df["subject"].unique()))
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

# ===================== SAFE QUESTION PICKER =====================
def get_next_question():
    subject = st.session_state.subject
    level = st.session_state.current_level

    base_pool = df[df["subject"] == subject]

    if base_pool.empty:
        st.error("❌ No questions found for selected subject.")
        st.stop()

    # 1️⃣ subject + level + unused + new concept
    pool = base_pool[
        (base_pool["__difficulty__"] == level) &
        (~base_pool["question_id"].isin(st.session_state.used_ids))
    ]

    if "concept" in df.columns and st.session_state.used_concepts:
        pool = pool[~pool["concept"].isin(st.session_state.used_concepts)]

    # 2️⃣ relax concept
    if pool.empty:
        pool = base_pool[
            (base_pool["__difficulty__"] == level)
        ]

    # 3️⃣ relax difficulty
    if pool.empty:
        pool = base_pool

    # 4️⃣ guaranteed safety
    q = pool.sample(1, replace=True).iloc[0]
    return q

# ===================== TEST PAGE =====================
if st.session_state.started:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = st.session_state.time_limit - elapsed

    if remaining <= 0 or st.session_state.q_no >= st.session_state.total_qs:
        st.subheader("✅ Test Completed")
        st.write(f"Score: **{st.session_state.score} / {st.session_state.total_qs}**")
        st.write(f"Final Difficulty Level: **{st.session_state.current_level}**")
        st.stop()

    q = get_next_question()

    st.session_state.used_ids.add(q["question_id"])
    if "concept" in q:
        st.session_state.used_concepts.add(q["concept"])

    st.progress((st.session_state.q_no + 1) / st.session_state.total_qs)
    st.info(f"Difficulty Level: {st.session_state.current_level}")

    st.subheader(f"Question {st.session_state.q_no + 1}")
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
        index=None,
        key=f"q_{st.session_state.q_no}"
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

        # ===================== 3-QUESTION BLOCK LOGIC =====================
        if len(st.session_state.block_answers) == 3:
            if all(st.session_state.block_answers):
                idx = LEVELS.index(st.session_state.current_level)
                if idx < len(LEVELS) - 1:
                    st.session_state.current_level = LEVELS[idx + 1]
                    st.info(f"⬆ Level Up → {st.session_state.current_level}")

            # reset block
            st.session_state.block_answers.clear()
            st.session_state.used_concepts.clear()

        st.rerun()
