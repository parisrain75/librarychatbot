import os
import time
from datetime import datetime, timedelta
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import StreamlitChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
import nest_asyncio

# ──────────────────────────────────────────────
# 초기 설정
# ──────────────────────────────────────────────
nest_asyncio.apply()
st.set_page_config(page_title="수험생 챗봇 (Student Edition)", page_icon="🎓", layout="wide")

# ──────────────────────────────────────────────
# API KEY
# ──────────────────────────────────────────────
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    genai.configure(api_key=GOOGLE_API_KEY)
except KeyError:
    st.error("❌ API Key 오류! Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

# ──────────────────────────────────────────────
# 스타일 (간단 테마 + 배지)
# ──────────────────────────────────────────────
st.markdown("""
<style>
.app-hero {
  padding: 12px 16px; border-radius: 14px;
  background: linear-gradient(135deg, #f9ecff 0%, #e8f3ff 100%);
  border: 1px solid #eef;
}
.badge {display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px; margin-right:6px;
  background:#fff; border:1px solid #ddd;
}
.small-muted {color:#666; font-size:12px;}
.stChatMessage .stMarkdown { font-size: 16px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-hero">
  <div class="badge">수험생 전용</div>
  <div class="badge">입시/학습/멘탈</div>
  <div class="badge">빠른 프롬프트</div>
  <div class="small-muted">TIP: 좌측 사이드바에서 톤·모델·모드를 조정할 수 있어요.</div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# 사이드바: 모델/톤/대화설정
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 설정")
    option = st.selectbox(
        "Gemini 모델",
        ("gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-pro-exp-02-05"),
        index=0
    )
    temperature = st.slider("창의성(Temperature)", 0.0, 1.0, 0.7, 0.1)
    max_turns = st.slider("최근 대화 유지 턴 수", 4, 30, 12, 1)

    st.markdown("---")
    st.subheader("🗣️ 톤 프리셋")
    tone = st.radio("말투 선택", ["따뜻·격려형", "간결·시험집중형", "면접·자소서 코치형"], index=0)

    st.markdown("---")
    if st.button("🧹 새 대화 시작"):
        st.session_state.clear()
        st.rerun()

# ──────────────────────────────────────────────
# 톤 프롬프트 프리셋
# ──────────────────────────────────────────────
TONE_MAP = {
    "따뜻·격려형": """당신은 따뜻하고 격려하는 수험생 코치입니다.
항상 존댓말로 대답하고, 학생이 스스로 할 수 있다는 확신을 주는 말투를 사용합니다.
핵심은 부드럽고 힘이 나는 조언입니다.""",

    "간결·시험집중형": """당신은 시험 직전 컨시어지입니다.
과
