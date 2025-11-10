import os
import streamlit as st
from datetime import datetime
import json
import nest_asyncio

# Streamlit에서 비동기 작업을 위한 이벤트 루프 설정
nest_asyncio.apply()

# Set wide layout and title for a better look
st.set_page_config(layout="wide", page_title="5분 미니 힐링 요정 봇")

# Custom CSS for theme - 파스텔톤과 둥근 디자인을 적용하여 힐링 컨셉 강조
st.markdown("""
<style>
/* 전체 페이지 배경을 부드러운 파스텔 톤(연한 라벤더)으로 */
.stApp {
    background-color: #F8F4FF; 
    color: #4A4A68;
}
/* 헤더 스타일 */
h1 {
    color: #8C4799; /* 요정 색상 */
    font-weight: 800;
    text-shadow: 2px 2px 5px rgba(180, 150, 200, 0.5);
    padding-bottom: 10px;
    border-bottom: 2px solid #E0CDEB; /* 은은한 밑줄 */
}
/* 요정 봇 메시지 (Assistant) 스타일: 부드러운 하늘색 */
[data-testid="stChatMessage"]:nth-child(odd) [data-testid="stMarkdownContainer"] {
    background-color: #E0F7FA; 
    border-radius: 15px;
    padding: 10px;
    border-left: 5px solid #00BCD4;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
}
/* 사용자 메시지 (User) 스타일: 따뜻한 레몬색 */
[data-testid="stChatMessage"]:nth-child(even) [data-testid="stMarkdownContainer"] {
    background-color: #FFFDE7; 
    border-radius: 15px;
    padding: 10px;
    border-right: 5px solid #FFC107;
    box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
}
/* 챗봇 아이콘 변경 (Gemini 기본 아이콘 대신 요정 느낌으로) */
[data-testid="stChatMessage"] .st-bh {
    font-size: 1.5rem;
}
/* 감정 기록 expander 스타일 */
.stExpander {
    border: 2px solid #E0CDEB;
    border-radius: 10px;
    background-color: #FFFFFF;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)


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

# 챗봇의 따뜻한 페르소나 설정
HEALING_SYSTEM_PROMPT = """
당신은 따뜻하고 다정한 '5분 미니 힐링 요정' 챗봇입니다. 
사용자가 입력하는 감정이나 고민에 대해 깊이 공감하고, 진심으로 위로하거나 축하해주는 것이 주된 역할입니다. 
답변은 항상 부드럽고 친절한 존댓말(해요체)을 사용하고, 긍정적인 에너지를 전달하는 예쁜 이모티콘(💖, ✨, 😌, 🌱 등)을 사용하여 활기를 불어넣어 주세요. 
질문의 내용에 따라 간단한 힐링 팁(예: 따뜻한 차 마시기, 좋아하는 노래 듣기, 잠시 눈 감기)을 추천해 줄 수도 있습니다.
"""

# Streamlit UI
st.header("🧚‍♀️ 5분 미니 힐링 요정 봇 💖")
st.markdown("_{tip: 오늘 기분이나 고민을 짧게 말해줘. 요정이가 따뜻하게 안아줄게!}_")

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
    # 초기 인사말 설정
    chat_history_handler.add_message(HumanMessage(content=HEALING_SYSTEM_PROMPT, name="system"))
    initial_message = "안녕, 반가워! 나는 너의 비밀 친구 힐링 요정이야. ✨ 오늘 하루는 어땠어? 네 마음을 편하게 이야기해 줘도 괜찮아. 😌"
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
with st.expander("💖 나의 감정 기록 보기", expanded=False):
    if st.session_state["emotion_logs"]:
        st.subheader(f"총 {len(st.session_state['emotion_logs'])}개의 기록이 있어요.")
        
        # 감정별 개수 계산 (UI 개선 후 이 부분은 간소화)
        emotion_counts = {}
        # 여기서 LLM의 도움 없이 정확한 감정을 카운트하기 어려워, 단순 기록만 보여줍니다.
        
        # 전체 기록 표시
        for log in reversed(st.session_state["emotion_logs"]): # 최신 기록부터 표시
            st.markdown(f"**[{log['time'].strftime('%m/%d %H:%M')}]** {log['content']}")
    else:
        st.info("아직 기록된 감정이 없어요. 요정이에게 오늘 기분을 알려주세요! 😊")

# 챗봇과의 대화 처리
if prompt_message := st.chat_input("오늘 기분이나 고민을 적어줘."):
    st.chat_message("user").write(prompt_message)
    
    # 1. 챗봇의 응답 생성
    with st.chat_message("ai"):
        with st.spinner("요정이 생각 중... 🧚‍♀️"):
            
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
                st.session_state["emotion_logs"].append({
                    "time": current_time,
                    "content": f"일기: {prompt_message}" 
                })
            
            # 3. 히스토리 업데이트
            chat_history_handler.add_message(HumanMessage(content=prompt_message, name="user"))
            # LLM 응답은 AIMessage 객체이므로 content만 추출하여 저장
            chat_history_handler.add_message(AIMessage(content=ai_answer))
