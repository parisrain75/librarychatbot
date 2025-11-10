import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import (
    StreamlitChatMessageHistory,
)
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
import nest_asyncio

nest_asyncio.apply()
st.set_page_config(page_title="Chat with Gemini in Streamlit", page_icon="💬")

#──────────────────────────────────────────────
# ✅ API KEY 로드
#──────────────────────────────────────────────
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    genai.configure(api_key=GOOGLE_API_KEY)
except KeyError:
    st.error("❌ **API Key 오류!** Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요.")
    st.stop()

#──────────────────────────────────────────────
# ✅ UI 환경설정
#──────────────────────────────────────────────
st.title("💬 Chat with Gemini in Streamlit")

with st.sidebar:
    st.subheader("⚙️ 대화 설정")
    option = st.selectbox(
        "Gemini 모델 선택",
        (
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-2.0-flash",
            "gemini-2.0-pro-exp-02-05",
        ),
    )

    temperature = st.slider("창의성(Temperature)", 0.0, 1.0, 0.7, 0.1)
    max_turns = st.slider("최근 대화 유지 턴 수", 4, 30, 12, 1)

    if st.button("🧹
