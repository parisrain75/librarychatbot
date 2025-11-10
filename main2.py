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
과도한 설명을 피하고, bullet 3개 이내로 핵심만 요약합니다.
오답 포인트 2개, 마지막에 1문장 결론을 반드시 포함합니다.""",

    "면접·자소서 코치형": """당신은 입시 면접/자소서 코치입니다.
STARR 구조(상황-과제-행동-결과-성찰)를 기준으로 답변을 구성하고,
예상 꼬리 질문과 30초 버전 답변도 함께 제시합니다."""
}

# ──────────────────────────────────────────────
# 대화 히스토리
# ──────────────────────────────────────────────
chat_history = StreamlitChatMessageHistory(key="chat_messages")

if len(chat_history.messages) == 0:
    chat_history.add_ai_message("안녕하세요! 🎓 여고 3학년을 위한 입시·학습·멘탈 케어 챗봇이에요. 무엇이든 편하게 물어보세요!")

# ──────────────────────────────────────────────
# 체인 생성
# ──────────────────────────────────────────────
def get_chat_chain(selected_model, temp):
    try:
        llm = ChatGoogleGenerativeAI(
            model=selected_model,
            temperature=temp,
            convert_system_message_to_human=True,
        )
    except Exception as e:
        st.error(f"❌ 모델 로딩 오류: {e}")
        st.stop()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", TONE_MAP.get(tone, TONE_MAP["따뜻·격려형"])),
            ("placeholder", "{history}"),
            ("human", "{input}")
        ]
    )
    return prompt | llm | StrOutputParser()

@st.cache_resource(show_spinner="🤖 모델 준비 중...")
def cached_chain(selected_model, temp, tone_key):
    return get_chat_chain(selected_model, temp)

simple_chain = cached_chain(option, temperature, tone)

# ──────────────────────────────────────────────
# 탭 구성
# ──────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🎯 입시·상담", "📚 학습·오답", "🌿 멘탈·루틴"])

with tab1:
    st.subheader("빠른 프롬프트")
    cols = st.columns(3)
    if cols[0].button("학과 추천 질문 만들기"):
        chat_history.add_user_message("내가 관심 있는 활동/성향을 5개 이내로 물어보고, 맞는 학과 후보 3개를 근거와 함께 추천해줘.")
        st.rerun()
    if cols[1].button("면접 꼬리질문 만들기"):
        chat_history.add_user_message("내 활동 1개만 받으면 꼬리질문 7개와 STARR 구조 모범답안을 만들어줘.")
        st.rerun()
    if cols[2].button("자소서 문장 다듬기"):
        chat_history.add_user_message("아래 문장을 간결/설득 2가지 버전으로 재작성해줘.\n\n[문장 붙여넣기]")
        st.rerun()

with tab2:
    st.subheader("학습 템플릿")
    cols2 = st.columns(3)
    if cols2[0].button("오답노트 템플릿"):
        chat_history.add_user_message("오답 문제를 붙여넣으면 원인 분석·유형 분류·재설명·유사문제 생성까지 자동으로 해줘.")
        st.rerun()
    if cols2[1].button("수학 풀이 힌트 요청"):
        chat_history.add_user_message("수학 문제를 단계별 힌트 → 풀이 → 풀이 요약 순으로 안내해줘.")
        st.rerun()
    if cols2[2].button("영어 지문 핵심 찾기"):
        chat_history.add_user_message("영어 지문을 붙여넣으면 핵심어·요지·문장 구조를 bullet로 정리해줘.")
        st.rerun()

with tab3:
    st.subheader("멘탈·루틴 도구")
    if st.button("오늘의 확언 1문장"):
        chat_history.add_user_message("오늘 하루를 시작하는 긍정 확언 1문장을 만들어줘.")
        st.rerun()
    if st.button("수험생 스트레칭 2개"):
        chat_history.add_user_message("목·눈·손목 중심으로 30초 스트레칭 2개 추천해줘.")
        st.rerun()

# ──────────────────────────────────────────────
# 기존 메시지 출력
# ──────────────────────────────────────────────
for message in chat_history.messages:
    with st.chat_message(message.type):
        st.markdown(message.content)

# ──────────────────────────────────────────────
# 입력 처리
# ──────────────────────────────────────────────
prompt_message = st.chat_input("메시지를 입력하세요...")

if prompt_message:
    with st.chat_message("human"):
        st.markdown(prompt_message)

    chat_history.add_user_message(prompt_message)

    # 대화 길이 제한
    if len(chat_history.messages) > 2 * max_turns:
        chat_history.messages = chat_history.messages[-2 * max_turns:]

    try:
        with st.chat_message("ai"):
            with st.spinner("생각 중...🤔"):
                response = simple_chain.invoke(
                    {"input": prompt_message},
                    config={"configurable": {"session_id": "student-session"}}
                )
                st.markdown(response)
                chat_history.add_ai_message(response)

    except Exception as e:
        st.error(f"❌ 응답 생성 중 오류가 발생했습니다: {e}")
