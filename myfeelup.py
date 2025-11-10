import os
import streamlit as st
from datetime import datetime
import json
import nest_asyncio

# Streamlit에서 비동기 작업을 위한 이벤트 루프 설정
nest_asyncio.apply()

# Set wide layout and title for a better look
st.set_page_config(layout="wide", page_title="마음 힐링 상담 요정 봇")

# Custom CSS for theme - 상담소 분위기와 명확한 대화 정렬을 위해 CSS 수정
custom_css = """
<style>
/* 전체 페이지 배경을 부드러운 파스텔 톤(연한 라벤더)으로 */
.stApp {
    background-color: #F8F4FF; 
    color: #4A4A68;
}
/* 헤더 스타일 - ✨ 간판 스타일로 대폭 수정 ✨ */
h1 {
    color: #4A4A68; /* 진한 회색 톤으로 변경하여 이미지와 유사하게 */
    font-weight: 900; /* 매우 굵게 */
    font-size: 3rem; /* 글자 크기 키우기 */
    text-shadow: 2px 2px 5px rgba(180, 150, 200, 0.5);
    text-align: center; /* 텍스트 가운데 정렬 */
    
    /* ✨ 배경 및 입체감 유지 */
    background: linear-gradient(145deg, #FFFFFF 90%, #E0F7FA 100%); /* 그라데이션 배경 */
    border: 3px solid #E0CDEB; /* 은은한 보라색 테두리 */
    border-radius: 20px; /* 둥근 모서리 강화 */
    box-shadow: 0 6px 15px rgba(147, 112, 219, 0.4); /* 연보라색 그림자 강화 */
    
    padding: 20px 30px; /* 상하좌우 패딩 크게 추가 */
    margin-bottom: 30px; /* 아래쪽 마진 추가 */
}

/* GIF container styling for centering and customizing st.image */
/* st.image가 생성하는 figure 태그를 중앙 정렬 */
[data-testid="stImage"] {
    text-align: center;
    margin: 0 auto 20px auto; /* 중앙 정렬 및 하단 마진 */
}
/* st.image 내부의 이미지에 직접 스타일 적용 */
[data-testid="stImage"] img {
    border-radius: 50%; 
    border: 5px solid #9370DB; /* 요정 테두리 색상 */
    box-shadow: 0 4px 10px rgba(147, 112, 219, 0.6); /* 그림자 추가 */
    object-fit: cover;
}

/* 챗 메시지 컨테이너의 기본 마진을 초기화 */
[data-testid="stChatMessage"] {
    padding: 0; 
    margin-bottom: 10px;
    max-width: 100%;
}

/* 1. 요정 봇 (AI/Assistant) 메시지 - 왼쪽 정렬 유지 */
[data-testid="stChatMessageContent"] {
    /* AI 메시지: 왼쪽 정렬 (기본값) */
    margin-left: 0 !important;
    margin-right: auto !important; 
    max-width: 80%;
}
/* AI 메시지 내용 박스 스타일 */
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
    background-color: #F0E6FF; /* Soft Lavender */ 
    border-radius: 15px;
    padding: 10px;
    border-left: 5px solid #9370DB; /* Medium Purple */
    box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.15); 
    text-align: left;
}


/* 2. 사용자 (User) 메시지 - ✨ 오른쪽 정렬 강제 적용 ✨ */
/* --- 핵심: 챗 메시지 전체 컨테이너를 오른쪽으로 정렬 --- */
[data-testid="stChatMessage"][role="user"] {
    display: flex;
    flex-direction: row-reverse; /* 아이콘을 오른쪽으로 이동 */
    justify-content: flex-start; /* 전체 메시지 박스를 오른쪽 끝에 붙임 */
}

/* 사용자 메시지 내용 박스 스타일 */
[data-testid="stChatMessage"][role="user"] [data-testid="stChatMessageContent"] {
    background-color: #E6FFFA; /* Soft Mint */ 
    border-radius: 15px;
    padding: 10px;
    border-right: 5px solid #20B2AA; /* Light Sea Green */
    box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.15); 
    
    /* 오른쪽 정렬을 위한 마진 조정 */
    margin-left: 20% !important; /* 왼쪽 여백을 크게 줘서 오른쪽으로 밀어냄 */
    margin-right: 15px !important; /* 아이콘과의 간격 */
    max-width: 80%; /* 대화창 폭 제한 */
}

/* 사용자 메시지 안의 텍스트 오른쪽 정렬 */
[data-testid="stChatMessage"][role="user"] [data-testid="stChatMessageContent"] p {
    text-align: right; 
}


/* 3. 챗봇 아이콘 컨테이너 (입체적인 느낌 유지) */
/* 어시스턴트 아이콘 (왼쪽) */
[data-testid="stChatMessage"][role="assistant"] [data-testid="stChatMessageAvatar"] {
    background-color: #FFFFFF;
    border: 3px solid #8C4799; 
    border-radius: 50%;
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2); 
    font-size: 1.5rem;
    padding: 5px; 
}
/* 사용자 아이콘 컨테이너 (오른쪽) */
[data-testid="stChatMessage"][role="user"] [data-testid="stChatMessageAvatar"] {
    background-color: #FFFFFF; 
    border: 3px solid #20B2AA; 
    border-radius: 50%; 
    box-shadow: 0px 2px 5px rgba(0, 0, 0, 0.2); 
    padding: 5px;
    margin-left: 0 !important; /* 오른쪽 정렬 시 좌측 여백 제거 */
    margin-right: 0 !important;
}

/* 감정 기록 expander 스타일 */
.stExpander {
    border: 2px solid #E0CDEB;
    border-radius: 10px;
    background-color: #FFFFFF;
    padding: 10px;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# LangChain 관련 컴포넌트는 제거하고, 순수 Gemini Chat만 사용
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage # AIMessage도 import
from langchain_community.chat_message_histories.streamlit import StreamlitChatMessageHistory

# Gemini API 키 설정
try:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("⚠️ GOOGLE_API_KEY를 Streamlit Secrets에 설정해주세요!")
    st.stop()

# 챗봇의 따뜻한 페르소나 설정 - **상담 컨셉으로 수정 (반말 유지)**
HEALING_SYSTEM_PROMPT = """
너는 따뜻하고 전문적인 '마음 건강 상담 요정' 챗봇이야. 
사용자가 이야기하는 고민이나 감정을 깊이 있게 경청하고, 그 감정의 뿌리를 함께 탐색하도록 부드럽게 질문하는 것이 너의 주된 역할이지. 
단순한 위로가 아닌, 사용자가 스스로 생각하고 마음을 정리할 수 있도록 도와줘.
답변은 항상 친근하고 발랄한 반말(해체)을 사용하고, 신뢰감과 긍정적인 에너지를 전달하는 예쁜 이모티콘(💖, ✨, 😌, 🌱 등)을 사용하여 활기를 불어넣어 줘. 
사용자의 기분을 개선하는 데 도움이 되는 구체적인 행동 팁(예: 심호흡 3회 하기, 5분 동안 좋아하는 음악 듣기, 잠시 창밖 바라보기)을 자주 추천해 줘.
"""

# Streamlit UI
st.header("🧚‍♀️ 마음 건강 힐링 상담소 💖")

# 💖 [수정] st.image에 use_column_width=True를 추가하여 GIF 애니메이션 활성화를 시도합니다. 💖
GIF_FILE_PATH = "cute_fairy.gif" 

# st.image를 사용하여 로컬 파일 경로에 있는 GIF를 로드
st.image(
    GIF_FILE_PATH, 
    caption="안녕! 나는 힐링 요정이야 ✨", # 캡션을 설명 텍스트로 사용
    width=150,
    # 💡 이 옵션을 추가하여 Streamlit이 GIF 파일을 다시 처리하고 애니메이션을 활성화하도록 유도합니다.
    use_column_width=False 
)

st.markdown("_{tip: 네 마음의 이야기를 편하게 털어놔 봐. 요정이가 귀 기울여 들을게!}_")

# 세션 상태에 감정 기록 리스트 초기화
if "emotion_logs" not in st.session_state:
    st.session_state["emotion_logs"] = []

# 모델 선택 (단일 채팅 모델)
option = st.selectbox("Select Gemini Model",
    ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp"),
    index=0,
    help="Gemini 2.5 Flash가 가장 빠르고 효율적입니다"
)

# 컴포넌트 초기화
@st.cache_resource
def initialize_llm(selected_model):
    try:
        llm = ChatGoogleGenerativeAI(
            model=selected_model,
            temperature=0.8, # 감성적인 답변을 위해 온도를 높임
            convert_system_message_to_human=True
        )
        return llm
    except Exception as e:
        st.error(f"❌ Gemini 모델 '{selected_model}' 로드 실패: {str(e)}")
        st.info("💡 'gemini-2.5-flash' 모델을 사용해보세요.")
        st.stop()
        
llm = initialize_llm(option)
chat_history_handler = StreamlitChatMessageHistory(key="chat_messages")


if not chat_history_handler.messages:
    # 초기 인사말 설정 - **반말로 수정**
    chat_history_handler.add_message(HumanMessage(content=HEALING_SYSTEM_PROMPT, name="system"))
    initial_message = "안녕! ✨ 나는 너의 마음을 살펴주는 힐링 요정이야. 오늘 네 마음속은 어떤 이야기로 가득 차 있어? 편하게 시작해 봐. 😌"
    chat_history_handler.add_message(AIMessage(content=initial_message)) # 초기 메시지는 AIMessage로 변경

# 기존 대화 기록 출력
for msg in chat_history_handler.messages:
    # 시스템 메시지는 사용자에게 표시하지 않음
    if msg.type != "system":
        # StreamlitChatMessageHistory는 role 대신 type으로 'human'/'ai'를 사용
        # 초기 메시지가 AIMessage이므로 type이 'ai'로 잘 나옴
        role = "assistant" if msg.type == "ai" else "user"
        st.chat_message(role).write(msg.content)

# 감정 기록 및 통계 표시 영역
with st.expander("💖 나의 마음 기록 보기", expanded=False):
    if st.session_state["emotion_logs"]:
        st.subheader(f"총 {len(st.session_state['emotion_logs'])}개의 기록이 있어.") # 반말로 수정
        
        # 감정별 개수 계산 (UI 개선 후 이 부분은 간소화)
        emotion_counts = {}
        # 여기서 LLM의 도움 없이 정확한 감정을 카운트하기 어려워, 단순 기록만 보여줍니다.
        
        # 전체 기록 표시
        for log in reversed(st.session_state["emotion_logs"]): # 최신 기록부터 표시
            st.markdown(f"**[{log['time'].strftime('%m/%d %H:%M')}]** {log['content']}")
    else:
        st.info("아직 기록된 마음의 이야기가 없어. 요정이와 대화하며 마음을 정리해 봐! 😊") # 반말로 수정

# 챗봇과의 대화 처리
if prompt_message := st.chat_input("오늘 기분이나 고민을 적어줘."):
    st.chat_message("user").write(prompt_message)
    
    # 1. 챗봇의 응답 생성
    with st.chat_message("ai"):
        with st.spinner("요정이가 네 마음에 귀 기울이는 중... 🧚‍♀️"):
            
            # 챗 히스토리를 메시지 목록으로 구성
            messages = [
                SystemMessage(content=HEALING_SYSTEM_PROMPT)
            ]
            # 기존 대화 기록 추가
            for msg in chat_history_handler.messages:
                # 시스템 메시지(초기 프롬프트)는 다시 추가할 필요 없음
                if msg.type != "system":
                     messages.append(msg)
            
            # 사용자 메시지 추가
            messages.append(HumanMessage(content=prompt_message, name="user"))
            
            # 💡 수정된 부분: llm.invoke 대신 llm.predict_messages를 사용하여 동기식 호출 (이전 오류 해결)
            response = llm.predict_messages(messages)
            ai_answer = response.content
            st.write(ai_answer)
            
            # 2. 감정 기록 
            current_time = datetime.now()
            
            if len(prompt_message) > 5: # 너무 짧은 메시지는 기록 제외
                # 🚨 [오류 수정] f-string 안에 중괄호가 깨지지 않도록 수정했습니다.
                st.session_state["emotion_logs"].append({
                    "time": current_time,
                    "content": f"마음 기록: {prompt_message}" 
                })
            
            # 3. 히스토리 업데이트
            chat_history_handler.add_message(HumanMessage(content=prompt_message, name="user"))
            # LLM 응답은 AIMessage 객체이므로 content만 추출하여 저장
            chat_history_handler.add_message(AIMessage(content=ai_answer))
