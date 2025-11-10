import os
import streamlit as st
from datetime import datetime
import json
import nest_asyncio

# Streamlit에서 비동기 작업을 위한 이벤트 루프 설정
nest_asyncio.apply()

# Set wide layout and title for a better look
st.set_page_config(layout="wide", page_title="마음 힐링 상담 요정 봇")

# -----------------------------------------------------
# 🎶 배경 음악 (MP3) 및 제어 버튼 구현
# -----------------------------------------------------
import streamlit.components.v1 as components
import base64

# 로컬 MP3 파일 경로 설정 (파일 이름을 확인하고 수정하세요!)
AUDIO_FILE_PATH = "ambient_music.mp3" 

# Tone.js 대신 HTML Audio를 사용합니다.
# base64 인코딩을 사용하여 Streamlit 환경에서 로컬 파일에 접근합니다.
try:
    with open(AUDIO_FILE_PATH, "rb") as f:
        audio_bytes = f.read()
        audio_b64 = base64.b64encode(audio_bytes).decode()
        audio_src = f"data:audio/mp3;base64,{audio_b64}"
except FileNotFoundError:
    # 파일이 없으면 재생 기능을 비활성화
    st.warning(f"⚠️ 경고: '{AUDIO_FILE_PATH}' 파일을 찾을 수 없어 배경음악 기능이 작동하지 않습니다. 파일을 추가해 주세요.")
    audio_src = ""

# 오디오 제어 HTML/JavaScript
audio_control_html = f"""
<script src="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/js/all.min.js"></script>
<audio id="background-audio" loop preload="auto" src="{audio_src}" style="display: none;"></audio>

<div id="music-control-container" style="
    position: absolute; 
    top: 20px; 
    left: 20px; 
    z-index: 1000;
    display: flex;
    align-items: center;
">
    <button id="music-toggle-btn" 
            onclick="toggleMusic()" 
            style="
                background: #9370DB; 
                color: white; 
                border: none; 
                border-radius: 50%; 
                width: 40px; 
                height: 40px; 
                cursor: pointer; 
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
                transition: background 0.2s;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1rem;
            ">
        <i class="fa-solid fa-play"></i>
    </button>
    <span id="music-status" style="
        color: #4A4A68;
        font-weight: 600;
        margin-left: 10px;
        font-size: 0.9rem;
    ">음악 멈춤</span>
</div>


<script>
    const audio = document.getElementById('background-audio');
    const button = document.getElementById('music-toggle-btn');
    const icon = button.querySelector('i');
    const statusText = document.getElementById('music-status');
    
    audio.volume = 0.3; 

    function toggleMusic() {{
        if (audio.paused) {{
            audio.play().then(() => {{
                icon.className = 'fa-solid fa-pause';
                button.style.background = '#FF6347'; 
                statusText.innerText = '음악 재생 중';
            }}).catch(error => {{
                console.error('Playback failed:', error);
                alert('음악 재생에 실패했습니다. 브라우저 정책상 상호작용이 필요합니다.');
            }});
        }} else {{
            audio.pause();
            icon.className = 'fa-solid fa-play';
            button.style.background = '#9370DB'; 
            statusText.innerText = '음악 멈춤';
        }}
    }}
    
    // 초기 상태 반영
    if (audio.paused) {{
        icon.className = 'fa-solid fa-play';
        button.style.background = '#9370DB';
        statusText.innerText = '음악 멈춤';
    }} else {{
        icon.className = 'fa-solid fa-pause';
        button.style.background = '#FF6347';
        statusText.innerText = '음악 재생 중';
    }}
</script>
"""
# -----------------------------------------------------


# Custom CSS for theme - 상담소 분위기와 명확한 대화 정렬을 위해 CSS 수정
st.markdown("""
<style>
/* Font Awesome 로드 */
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css');

/* 전체 페이지 배경을 부드러운 파스텔 톤(연한 라벤더)으로 */
.stApp {
    background-color: #F8F4FF; 
    color: #4A4A68;
}

/* 헤더 스타일 - ✨ 간판 스타일로 대폭 수정 ✨ */
.header-container h1 {
    color: #4A4A68; 
    font-weight: 900; 
    font-size: 3rem; 
    text-shadow: 2px 2px 5px rgba(180, 150, 200, 0.5);
    text-align: center; 
    
    /* ✨ 배경 및 입체감 유지 */
    background: linear-gradient(145deg, #FFFFFF 90%, #E0F7FA 100%); 
    border: 3px solid #E0CDEB; 
    border-radius: 20px; 
    box-shadow: 0 6px 15px rgba(147, 112, 219, 0.4); 
    
    padding: 20px 30px; 
    margin: 0; /* st.header 기본 마진 제거 */
}

/* GIF 컨테이너 중앙 정렬을 위한 CSS 추가 */
[data-testid="stImage"] {
    display: flex; /* Flexbox 활성화 */
    justify-content: center; /* 내부 콘텐츠 중앙 정렬 */
    margin-top: 20px;
    margin-bottom: 20px;
}

/* st.image 내부의 이미지에 직접 스타일 적용 */
[data-testid="stImage"] img {
    border-radius: 50%; 
    border: 5px solid #9370DB; 
    box-shadow: 0 4px 10px rgba(147, 112, 219, 0.6); 
    object-fit: cover;
}
/* GIF 캡션 가운데 정렬 */
[data-testid="caption"] {
    text-align: center;
}

/* 챗 메시지 컨테이너의 기본 마진을 초기화 */
[data-testid="stChatMessage"] {
    padding: 0; 
    margin-bottom: 10px;
    max-width: 100%;
}

/* 1. 요정 봇 (AI/Assistant) 메시지 - 왼쪽 정렬 유지 */
[data-testid="stChatMessageContent"] {
    margin-left: 0 !important;
    margin-right: auto !important; 
    max-width: 80%;
}
/* AI 메시지 내용 박스 스타일 */
[data-testid="stChatMessage"] [data-testid="stChatMessageContent"] {
    background-color: #F0E6FF; 
    border-radius: 15px;
    padding: 10px;
    border-left: 5px solid #9370DB; 
    box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.15); 
    text-align: left;
}


/* 2. 사용자 (User) 메시지 - ✨ 오른쪽 정렬 강제 적용 ✨ */
[data-testid="stChatMessage"][role="user"] {
    display: flex;
    flex-direction: row-reverse; 
    justify-content: flex-start; 
}

/* 사용자 메시지 내용 박스 스타일 */
[data-testid="stChatMessage"][role="user"] [data-testid="stChatMessageContent"] {
    background-color: #E6FFFA; 
    border-radius: 15px;
    padding: 10px;
    border-right: 5px solid #20B2AA; 
    box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.15); 
    
    margin-left: 20% !important; 
    margin-right: 15px !important; 
    max-width: 80%; 
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
    margin-left: 0 !important; 
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
""", unsafe_allow_html=True)

# -----------------------------------------------------
# ✨ 음악 버튼은 이제 HTML 컴포넌트 삽입 코드가 됩니다.
# -----------------------------------------------------
# HTML 컴포넌트 (음악 버튼)을 삽입합니다.
components.html(audio_control_html, height=100)
# -----------------------------------------------------

# -----------------------------------------------------
# 💖 제목과 GIF 레이아웃 (중앙 정렬) - 동일한 컬럼 비율 적용
# -----------------------------------------------------
CENTERING_RATIO = [1, 4, 1] # 1:4:1 비율로 가운데 40%를 중앙 컨텐츠 블록으로 사용

# 1. 제목 (간판) 중앙 정렬
title_col1, title_col2, title_col3 = st.columns(CENTERING_RATIO)
with title_col2:
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.header("💖 마음 건강 힐링 상담소 💖")
    st.markdown('</div>', unsafe_allow_html=True)

# 2. GIF 이미지 추가 (중앙 정렬)
GIF_FILE_PATH = "cute_fairy.gif" 
gif_col1, gif_col2, gif_col3 = st.columns(CENTERING_RATIO)

with gif_col2:
    st.image(
        GIF_FILE_PATH, 
        caption="안녕! 나는 힐링 요정이야 ✨",
        width=150,
        use_column_width=False 
    )
# -----------------------------------------------------

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
# 🚨🚨🚨 에러 수정: chat_history_handler를 LLM 초기화 직후로 이동 🚨🚨🚨
from langchain_community.chat_message_histories.streamlit import StreamlitChatMessageHistory 
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
        role = "assistant" if msg.type == "ai" else "user"
        
        # 아바타를 이모지로 설정
        if role == "assistant":
            st.chat_message(role, avatar="✨").write(msg.content)
        else:
            st.chat_message(role, avatar="🙂").write(msg.content)


# 감정 기록 및 통계 표시 영역
with st.expander("💖 나의 마음 기록 보기", expanded=False):
    if st.session_state["emotion_logs"]:
        st.subheader(f"총 {len(st.session_state['emotion_logs'])}개의 기록이 있어.") # 반말로 수정
        
        # 감정별 개수 계산 (UI 개선 후 이 부분은 간소화)
        emotion_counts = {}
        
        # 전체 기록 표시
        for log in reversed(st.session_state["emotion_logs"]): # 최신 기록부터 표시
            st.markdown(f"**[{log['time'].strftime('%m/%d %H:%M')}]** {log['content']}")
    else:
        st.info("아직 기록된 마음의 이야기가 없어. 요정이와 대화하며 마음을 정리해 봐! 😊") # 반말로 수정

# 챗봇과의 대화 처리
if prompt_message := st.chat_input("오늘 기분이나 고민을 적어줘."):
    st.chat_message("user", avatar="🙂").write(prompt_message)
    
    # 1. 챗봇의 응답 생성
    with st.chat_message("ai", avatar="✨"):
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
                st.session_state["emotion_logs"].append({
                    "time": current_time,
                    "content": f"마음 기록: {prompt_message}" 
                })
            
            # 3. 히스토리 업데이트
            chat_history_handler.add_message(HumanMessage(content=prompt_message, name="user"))
            # LLM 응답은 AIMessage 객체이므로 content만 추출하여 저장
            chat_history_handler.add_message(AIMessage(content=ai_answer))
