# -*- coding: utf-8 -*-
"""
Refactored main.py
- 모든 버튼/라벨/문자열을 변수로 분리하여 줄바꿈으로 인한 SyntaxError 방지
- 파일 업로드 없이 '붙여넣기 오답풀이' 기능 포함
- 모델/톤/대화설정, 탭 UI, 대화 길이 제한, 예외 처리, 캐싱 유지
"""

import os
import streamlit as st
from datetime import datetime, timedelta
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import StreamlitChatMessageHistory
from langchain_core.output_parsers import StrOutputParser
import google.generativeai as genai
import nest_asyncio

# ──────────────────────────────────────────────
# 0) 상수/라벨(한 줄 문자열로만 정의) ─ 줄바꿈 금지
# ──────────────────────────────────────────────
APP_TITLE                 = "수험생 챗봇 (Student Edition)"
APP_ICON                  = "🎓"
SIDEBAR_HEADER            = "⚙️ 설정"
MODEL_SELECT_LABEL        = "Gemini 모델"
TEMPERATURE_LABEL         = "창의성(Temperature)"
TURNS_LABEL               = "최근 대화 유지 턴 수"
TONE_HEADER               = "🗣️ 톤 프리셋"
TONE_SELECT_LABEL         = "말투 선택"
NEW_CHAT_BUTTON           = "🧹 새 대화 시작"

TONE_WARM                 = "따뜻·격려형"
TONE_CONCISE              = "간결·시험집중형"
TONE_INTERVIEW            = "면접·자소서 코치형"

TAB_ADMISSION             = "🎯 입시·상담"
TAB_STUDY                 = "📚 학습·오답"
TAB_MENTAL                = "🌿 멘탈·루틴"
TAB_PASTE_WRONG           = "📝 오답풀이(붙여넣기)"

BTN_MAJOR_QUESTIONS       = "학과 추천 질문 만들기"
BTN_INTERVIEW_QUESTIONS   = "면접 꼬리질문 만들기"
BTN_EDIT_SELF_INTRO       = "자소서 문장 다듬기"

BTN_WRONG_NOTE_TEMPLATE   = "오답노트 템플릿"
BTN_MATH_HINTS            = "수학 풀이 힌트 요청"
BTN_ENG_KEYPOINTS         = "영어 지문 핵심 찾기"

BTN_DAILY_AFFIRM          = "오늘의 확언 1문장"
BTN_STRETCH               = "수험생 스트레칭 2개"

PASTE_TAB_TITLE           = "파일 없이 바로 오답풀이 (여러 문항 한 번에 가능)"
PASTE_GUIDE_LINE1         = "- 아래 붙여넣기 박스에 문제·선지·내가 고른 답·정답·해설(있다면)을 붙여넣으세요."
PASTE_GUIDE_LINE2         = "- 여러 문항은 `---` 한 줄로 구분합니다."
PASTE_GUIDE_LINE3         = "- 과목(국어/영어/수학/사회/과학)을 지정하면 해당 과목 스타일로 풀이합니다."
PASTE_TEXTAREA_LABEL      = "여기에 붙여넣기 (문항 구분: ---)"
BTN_SAMPLE_PASTE          = "샘플 템플릿 붙여넣기"
SUBJECT_SELECT_LABEL      = "과목(선택)"
FORMAT_RADIO_LABEL        = "출력 형식"
FORMAT_SUMMARY            = "요약형"
FORMAT_DETAIL             = "상세형"
QUIZ_CHECKBOX_LABEL       = "유사문항 1개 생성"
RUN_WRONG_BTN             = "🚀 오답풀이 실행"
WARN_EMPTY_PASTE          = "붙여넣기 내용이 없습니다."
SUCCESS_ANALYZED          = "오답 분석이 완료되었습니다."
RESULT_TITLE              = "🔎 오답 분석 결과"
RESULT_COPY_EXPANDER      = "📋 결과 텍스트 복사"

CHAT_PLACEHOLDER          = "메시지를 입력하세요..."
WELCOME_MSG               = "안녕하세요! 🎓 여고 3학년을 위한 입시·학습·멘탈 케어 챗봇이에요. 무엇이든 편하게 물어보세요!"

API_ERR                   = "❌ API Key 오류! Streamlit Secrets에 GOOGLE_API_KEY를 등록해주세요."
MODEL_LOAD_ERR_PREFIX     = "❌ 모델 로딩 오류: "
RESP_ERR_PREFIX           = "❌ 응답 생성 중 오류가 발생했습니다: "
WRONG_ANALYZE_ERR_PREFIX  = "❌ 오답 분석 중 오류가 발생했습니다: "

HERO_TIP                  = "TIP: 좌측 사이드바에서 톤·모델·모드를 조정할 수 있어요."
HERO_BADGE1               = "수험생 전용"
HERO_BADGE2               = "입시/학습/멘탈"
HERO_BADGE3               = "빠른 프롬프트"

MAJOR_QUESTIONS_PROMPT    = "내가 관심 있는 활동/성향을 5개 이내로 물어보고, 맞는 학과 후보 3개를 근거와 함께 추천해줘."
INTERVIEW_QUESTIONS_PROMPT= "내 활동 1개만 받으면 꼬리질문 7개와 STARR 구조 모범답안을 만들어줘."
EDIT_SELF_INTRO_PROMPT    = "아래 문장을 간결/설득 2가지 버전으로 재작성해줘.\n\n[문장 붙여넣기]"
WRONG_NOTE_PROMPT         = "오답 문제를 붙여넣으면 원인 분석·유형 분류·재설명·유사문제 생성까지 자동으로 해줘."
MATH_HINTS_PROMPT         = "수학 문제를 단계별 힌트 → 풀이 → 풀이 요약 순으로 안내해줘."
ENG_KEYPOINTS_PROMPT      = "영어 지문을 붙여넣으면 핵심어·요지·문장 구조를 bullet로 정리해줘."
DAILY_AFFIRM_PROMPT       = "오늘 하루를 시작하는 긍정 확언 1문장을 만들어줘."
STRETCH_PROMPT            = "목·눈·손목 중심으로 30초 스트레칭 2개 추천해줘."

SAMPLE_BUTTON_LABEL       = "샘플 템플릿 붙여넣기"
SAMPLE_PASTE_VALUE        = "[과목] 수학\n[문제] 함수 f(x)=x^2-4x+5의 최솟값을 구하라.\n[선지] ①1 ②2 ③3 ④4 ⑤5\n[내가 고른 답] ⑤\n[정답] ③\n[해설(있다면)] 완전제곱식으로 전개하면...\n---\n[과목] 영어\n[지문] The committee reached a consensus, which...\n[문제] 밑줄 친 which가 가리키는 것은?\n[선지] ①decision ②committee ③consensus ④argument ⑤result\n[내가 고른 답] ②\n[정답] ③\n"

GUIDE_HEADER               = "다음은 수험생의 오답 기록입니다. 파일 업로드 없이 텍스트만 제공됩니다."
GUIDE_RULES                = "요구사항:\n1) 각 문항을 '---' 로 분리하여 처리하세요.\n2) 각 문항마다 아래 형식으로 출력하세요:\n   - [정답] (근거 1~2문장)\n   - [오답 이유] (내가 고른 답이 왜 틀렸는지, 흔한 함정 1개)\n   - [핵심 개념] (bullet 2~3개)\n   - [다음엔 이렇게] (재발 방지 3문장, 짧고 실천가능)\n   - [리마인더] (24시간 후 복습용 1문장 / 7일 후 복습용 1문장)"
GUIDE_SUBJECT_HINT         = "3) 과목이 '{subject}'이면 해당 과목 스타일을 우선 적용하고, '자동감지'면 문항 내용으로 과목을 추론하세요."
GUIDE_FORMAT_HINT          = "4) '{format_choice}'이면 '요약형'은 간결하게, '상세형'은 근거/풀이 단계를 더 구체적으로 제시하세요."
GUIDE_NO_SEP               = "반드시 문항 순서를 유지하고, 문항 사이에 구분선(—)을 넣지 마세요."
USER_PASTE_PREFIX          = "[오답 텍스트 붙여넣기]\n"

# 시스템 톤 프롬프트(한 줄 또는 삼중 따옴표 사용, 내부 줄바꿈은 이 블록에서만 관리)
TONE_MAP = {
    TONE_WARM: """당신은 따뜻하고 격려하는 수험생 코치입니다.
항상 존댓말로 대답하고, 학생이 스스로 할 수 있다는 확신을 주는 말투를 사용합니다.
핵심은 부드럽고 힘이 나는 조언입니다.""",
    TONE_CONCISE: """당신은 시험 직전 컨시어지입니다.
과도한 설명을 피하고, bullet 3개 이내로 핵심만 요약합니다.
오답 포인트 2개, 마지막에 1문장 결론을 반드시 포함합니다.""",
    TONE_INTERVIEW: """당신은 입시 면접/자소서 코치입니다.
STARR 구조(상황-과제-행동-결과-성찰)를 기준으로 답변을 구성하고,
예상 꼬리 질문과 30초 버전 답변도 함께 제시합니다."""
}

# ──────────────────────────────────────────────
# 1) 초기 설정
# ──────────────────────────────────────────────
nest_asyncio.apply()
st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")

# ──────────────────────────────────────────────
# 2) API Key
# ──────────────────────────────────────────────
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    genai.configure(api_key=Google_API_KEY if (Google_API_KEY:=GOOGLE_API_KEY) else GOOGLE_API_KEY)
except KeyError:
    st.error(API_ERR)
    st.stop()

# ──────────────────────────────────────────────
# 3) 스타일/CSS
# ──────────────────────────────────────────────
st.markdown(
    """
<style>
.app-hero { padding: 12px 16px; border-radius: 14px; background: linear-gradient(135deg, #f9ecff 0%, #e8f3ff 100%); border: 1px solid #eef; }
.badge { display:inline-block; padding:2px 10px; border-radius:999px; font-size:12px; margin-right:6px; background:#fff; border:1px solid #ddd; }
.small-muted { color:#666; font-size:12px; }
.stChatMessage .stMarkdown { font-size: 16px; line-height: 1.6; }
textarea { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
</style>
""",
    unsafe_allow_html=True
)

st.markdown(
    f"""
<div class="app-hero">
  <div class="badge">{HERO_BADGE1}</div>
  <div class="badge">{HERO_BADGE2}</div>
  <div class="badge">{HERO_BADGE3}</div>
  <div class="small-muted">{HERO_TIP}</div>
</div>
""",
    unsafe_allow_html=True
)

# ──────────────────────────────────────────────
# 4) 사이드바: 모델/톤/대화설정
# ──────────────────────────────────────────────
with st.sidebar:
    st.header(SIDEBAR_HEADER)
    option = st.selectbox(
        MODEL_SELECT_LABEL,
        ("gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash", "gemini-2.0-pro-exp-02-05"),
        index=0
    )
    temperature = st.slider(TEMPERATURE_LABEL, 0.0, 1.0, 0.7, 0.1)
    max_turns = st.slider(TURNS_LABEL, 4, 30, 12, 1)

    st.markdown("---")
    st.subheader(TONE_HEADER)
    tone = st.radio(TONE_SELECT_LABEL, [TONE_WARM, TONE_CONCISE, TONE_INTERVIEW], index=0)

    st.markdown("---")
    if st.button(NEW_CHAT_BUTTON):
        st.session_state.clear()
        st.rerun()

# ──────────────────────────────────────────────
# 5) 대화 히스토리
# ──────────────────────────────────────────────
chat_history = StreamlitChatMessageHistory(key="chat_messages")
if len(chat_history.messages) == 0:
    chat_history.add_ai_message(WELCOME_MSG)

# ──────────────────────────────────────────────
# 6) 체인 생성/캐싱
# ──────────────────────────────────────────────
def get_chat_chain(selected_model: str, temp: float):
    try:
        llm = ChatGoogleGenerativeAI(
            model=selected_model,
            temperature=temp,
            convert_system_message_to_human=True,
        )
    except Exception as e:
        st.error(f"{MODEL_LOAD_ERR_PREFIX}{e}")
        st.stop()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", TONE_MAP.get(tone, TONE_MAP[TONE_WARM])),
            ("placeholder", "{history}"),
            ("human", "{input}")
        ]
    )
    return prompt | llm | StrOutputParser()

@st.cache_resource(show_spinner="🤖 모델 준비 중...")
def cached_chain(selected_model: str, temp: float, tone_key: str):
    return get_chat_chain(selected_model, temp)

simple_chain = cached_chain(option, temperature, tone)

# ──────────────────────────────────────────────
# 7) 탭 UI
# ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([TAB_ADMISSION, TAB_STUDY, TAB_MENTAL, TAB_PASTE_WRONG])

with tab1:
    st.subheader("빠른 프롬프트")
    c1, c2, c3 = st.columns(3)
    if c1.button(BTN_MAJOR_QUESTIONS):
        chat_history.add_user_message(MAJOR_QUESTIONS_PROMPT)
        st.rerun()
    if c2.button(BTN_INTERVIEW_QUESTIONS):
        chat_history.add_user_message(INTERVIEW_QUESTIONS_PROMPT)
        st.rerun()
    if c3.button(BTN_EDIT_SELF_INTRO):
        chat_history.add_user_message(EDIT_SELF_INTRO_PROMPT)
        st.rerun()

with tab2:
    st.subheader("학습 템플릿")
    c21, c22, c23 = st.columns(3)
    if c21.button(BTN_WRONG_NOTE_TEMPLATE):
        chat_history.add_user_message(WRONG_NOTE_PROMPT)
        st.rerun()
    if c22.button(BTN_MATH_HINTS):
        chat_history.add_user_message(MATH_HINTS_PROMPT)
        st.rerun()
    if c23.button(BTN_ENG_KEYPOINTS):
        chat_history.add_user_message(ENG_KEYPOINTS_PROMPT)
        st.rerun()

with tab3:
    st.subheader("멘탈·루틴 도구")
    if st.button(BTN_DAILY_AFFIRM):
        chat_history.add_user_message(DAILY_AFFIRM_PROMPT)
        st.rerun()
    if st.button(BTN_STRETCH):
        chat_history.add_user_message(STRETCH_PROMPT)
        st.rerun()

with tab4:
    st.subheader(PASTE_TAB_TITLE)
    st.markdown(PASTE_GUIDE_LINE1)
    st.markdown(PASTE_GUIDE_LINE2)
    st.markdown(PASTE_GUIDE_LINE3)

    col_a, col_b = st.columns([3, 1])
    pasted = col_a.text_area(PASTE_TEXTAREA_LABEL, height=260, value="")
    if col_b.button(BTN_SAMPLE_PASTE):
        st.session_state["__sample_paste__"] = SAMPLE_PASTE_VALUE
        st.rerun()

    if "__sample_paste__" in st.session_state and not pasted:
        pasted = st.session_state["__sample_paste__"]

    col1, col2, col3 = st.columns(3)
    subject = col1.selectbox(SUBJECT_SELECT_LABEL, ["자동감지", "국어", "영어", "수학", "사회", "과학"], index=0)
    format_choice = col2.radio(FORMAT_RADIO_LABEL, [FORMAT_SUMMARY, FORMAT_DETAIL], index=0)
    make_quiz = col3.checkbox(QUIZ_CHECKBOX_LABEL, value=True)

    if st.button(RUN_WRONG_BTN):
        if not pasted.strip():
            st.warning(WARN_EMPTY_PASTE)
        else:
            extra_quiz = "(유사문항 1개 포함)" if make_quiz else ""
            guide_subject = GUIDE_SUBJECT_HINT.format(subject=subject)
            guide_format  = GUIDE_FORMAT_HINT.format(format_choice=format_choice)
            guidelines = f"{GUIDE_HEADER}\n{GUIDE_RULES}\n{extra_quiz}\n{guide_subject}\n{guide_format}\n{GUIDE_NO_SEP}"
            user_input = f"{USER_PASTE_PREFIX}{pasted.strip()}"

            try:
                with st.spinner("오답을 분석 중입니다…"):
                    analysis = simple_chain.invoke(
                        {"input": f"{guidelines}\n\n{user_input}"},
                        config={"configurable": {"session_id": "wrong-ans-session"}}
                    )
                chat_history.add_user_message("(오답풀이 요청)\n" + pasted[:500] + ("..." if len(pasted) > 500 else ""))
                chat_history.add_ai_message(analysis)

                st.success(SUCCESS_ANALYZED)
                st.markdown(f"### {RESULT_TITLE}")
                st.markdown(analysis)

                with st.expander(RESULT_COPY_EXPANDER):
                    st.code(analysis)

            except Exception as e:
                st.error(f"{WRONG_ANALYZE_ERR_PREFIX}{e}")

# ──────────────────────────────────────────────
# 8) 기존 메시지 출력
# ──────────────────────────────────────────────
for message in chat_history.messages:
    with st.chat_message(message.type):
        st.markdown(message.content)

# ──────────────────────────────────────────────
# 9) 입력 처리
# ──────────────────────────────────────────────
prompt_message = st.chat_input(CHAT_PLACEHOLDER)

if prompt_message:
    with st.chat_message("human"):
        st.markdown(prompt_message)

    chat_history.add_user_message(prompt_message)

    # 대화 길이 제한(최근 max_turns 쌍 유지)
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
        st.error(f"{RESP_ERR_PREFIX}{e}")
