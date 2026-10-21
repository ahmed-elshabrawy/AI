import os
import html

import streamlit as st

from database import (
    search_documents,
    create_conversation,
    save_message,
    get_conversations,
    get_conversation_messages,
    get_ai_settings,
)


# =========================================================
# إعدادات المشروع
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="منصة دراستك",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# إعدادات قاعدة البيانات
# =========================================================

DB_SETTINGS = get_ai_settings()


# =========================================================
# Session State
# =========================================================

if "conversation_id" not in st.session_state:
    st.session_state["conversation_id"] = None

if "selected_conversation_id" not in st.session_state:
    st.session_state["selected_conversation_id"] = None

if "submitted_question" not in st.session_state:
    st.session_state["submitted_question"] = ""


# =========================================================
# تحميل ملف CSS
# =========================================================

css_path = os.path.join(BASE_DIR, "style.css")

if os.path.exists(css_path):
    with open(css_path, encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True,
        )


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            منصة دراستك 🎓
        </div>

        <div class="sidebar-subtitle">
            رائدة التعليم الإلكتروني في الأردن
        </div>

        <hr>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### 💬 الشاتات القديمة")

    conversations = get_conversations(20)

    if not conversations:
        st.info("لا توجد شاتات محفوظة حتى الآن.")

    for cid, title in conversations:

        if st.button(
            f"💬 {title}",
            key=f"conversation_{cid}",
            use_container_width=True,
        ):
            st.session_state["selected_conversation_id"] = cid
            st.session_state["conversation_id"] = cid

            st.rerun()


# =========================================================
# الصفحة الرئيسية
# =========================================================

st.markdown(
    """
    <div class="logo-circle">
        🎓
    </div>

    <div class="main-title">
        منصة دراستك
    </div>

    <div class="main-subtitle">
        اسأل أي سؤال وسيبحث النظام ويجيبك
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# عرض المحادثة المختارة
# =========================================================

selected_id = st.session_state.get(
    "selected_conversation_id"
)

if selected_id:

    messages = get_conversation_messages(selected_id)

    if messages:

        st.markdown(
            '<div class="answer-title">💬 المحادثة</div>',
            unsafe_allow_html=True,
        )

        for m in messages:

            content = (
                html.escape(str(m[2] or ""))
                .replace("\n", "<br>")
            )

            role = (
                str(m[3] or "").lower()
                if len(m) > 3
                else ""
            )

            if role == "user":
                cls = "question-box"
            else:
                cls = "answer-box"

            st.markdown(
                f'<div class="{cls}">{content}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")


# =========================================================
# إنشاء محادثة جديدة
# =========================================================

def new_chat_callback():
    """بدء محادثة جديدة."""

    st.session_state["question_input"] = ""
    st.session_state["conversation_id"] = None
    st.session_state["selected_conversation_id"] = None
    st.session_state["submitted_question"] = ""


# =========================================================
# إرسال السؤال
# =========================================================

def ask_callback():
    """حفظ السؤال الذي تم إدخاله."""

    st.session_state["submitted_question"] = (
        st.session_state
        .get("question_input", "")
        .strip()
    )

    st.session_state["question_input"] = ""


# =========================================================
# Input السؤال
# =========================================================

question = st.text_input(
    "",
    placeholder="?.....Ask Me",
    key="question_input",
)


# =========================================================
# الأزرار
# =========================================================

c1, c2 = st.columns(2)


# زر اسأل
with c1:

    ask = st.button(
        "🚀 اسأل",
        use_container_width=True,
        key="ask_button",
        type="primary",
        on_click=ask_callback,
    )


# زر محادثة جديدة
with c2:

    st.button(
        "🆕 محادثة جديدة",
        use_container_width=True,
        key="new_chat_button",
        on_click=new_chat_callback,
    )


# =========================================================
# معالجة السؤال
# =========================================================

submitted = (
    st.session_state
    .get("submitted_question", "")
    .strip()
)


if ask and submitted:

    # -----------------------------------------------------
    # عرض السؤال
    # -----------------------------------------------------

    st.markdown(
        '<div class="question-title">💬 السؤال</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="question-box">
            {html.escape(submitted)}
        </div>
        """,
        unsafe_allow_html=True,
    )


    # -----------------------------------------------------
    # البحث في قاعدة البيانات
    # -----------------------------------------------------

    with st.spinner(
        "🔍 جاري البحث داخل قاعدة البيانات..."
    ):

        try:

            rows = search_documents(
                submitted,
                1,
            )

        except Exception as e:

            st.error(
                f"""
                ❌ حدث خطأ أثناء البحث في قاعدة البيانات:

                {e}
                """
            )

            st.stop()


    # -----------------------------------------------------
    # عدم وجود إجابة
    # -----------------------------------------------------

    if not rows:

        st.warning(
            "⚠️ لا أجد الإجابة داخل قاعدة البيانات."
        )

        st.stop()


    # -----------------------------------------------------
    # استخراج الإجابة
    # -----------------------------------------------------

    answer = str(
        rows[0][2] or ""
    ).strip()


    # -----------------------------------------------------
    # إنشاء المحادثة
    # -----------------------------------------------------

    if st.session_state["conversation_id"] is None:

        st.session_state["conversation_id"] = (
            create_conversation(submitted)
        )


    # -----------------------------------------------------
    # حفظ الرسائل
    # -----------------------------------------------------

    cid = st.session_state["conversation_id"]

    save_message(
        cid,
        submitted,
        role="user",
    )

    save_message(
        cid,
        answer,
        role="assistant",
    )


    # -----------------------------------------------------
    # عرض الإجابة
    # -----------------------------------------------------

    st.markdown(
        '<div class="answer-title">📖 الإجابة</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="answer-box">
            {html.escape(answer).replace(chr(10), "<br>")}
        </div>
        """,
        unsafe_allow_html=True,
    )