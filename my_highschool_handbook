import os
import streamlit as st
import nest_asyncio

# Streamlit에서 비동기 작업을 위한 이벤트 루프 설정
nest_asyncio.apply()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.history_aware_retriever import create_history_aware_retriever
from langchain_community.chat_message_histories.streamlit import StreamlitChatMessageHistory

# LangChain ChromaDB에서 발생하는 sqlite3 버전 문제 해결
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
from langchain_chroma import Chroma


# Gemini API 키 설정
try:
    # 사용자 환경에 따라 st.secrets 대신 os.environ.get("GOOGLE_API_KEY")를 사용할 수도 있습니다.
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception as e:
    st.error("⚠️ GOOGLE_API_KEY를 Streamlit Secrets에 설정해주세요!")
    st.stop()

# cache_resource로 한번 실행한 결과 캐싱해두기
@st.cache_resource
def load_and_split_pdf(file_path):
    # 주의: 이 파일은 사용자 환경에 있어야 합니다.
    loader = PyPDFLoader(file_path)
    return loader.load_and_split()

# 텍스트 청크들을 Chroma 안에 임베딩 벡터로 저장
@st.cache_resource
def create_vector_store(_docs):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(_docs)
    st.info(f"📄 {len(split_docs)}개의 텍스트 청크로 분할했어요. (규정집 분석 완료!)")

    persist_directory = "./chroma_db"
    st.info("🤖 임베딩 모델 로드 중... (첫 실행 시 모델 다운로드로 시간이 걸릴 수 있어요)")
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

    st.info("🔢 벡터 임베딩 생성 및 저장 중...")
    vectorstore = Chroma.from_documents(
        split_docs,
        embeddings,
        persist_directory=persist_directory
    )
    st.success("💾 학교 규정 데이터베이스 생성 완료! 이제 질문해도 돼요! 🥳")
    return vectorstore

# 만약 기존에 저장해둔 ChromaDB가 있는 경우, 이를 로드
@st.cache_resource
def get_vectorstore(_docs):
    persist_directory = "./chroma_db"
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    if os.path.exists(persist_directory):
        return Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings
        )
    else:
        return create_vector_store(_docs)
    
# PDF 문서 로드-벡터 DB 저장-검색기-히스토리 모두 합친 Chain 구축
@st.cache_resource
def initialize_components(selected_model):
    # 🌟🌟🌟 이 부분을 실제 학교 규정집 PDF 파일 경로로 변경해 주세요! 🌟🌟🌟
    # 예시: file_path = "우리학교_생활규정집.pdf"
    file_path = "my_highschool_handbook.pdf" 
    
    # ⚠️ 파일이 없으면 오류가 발생합니다.
    try:
        pages = load_and_split_pdf(file_path)
    except FileNotFoundError:
        # 친절한 안내 메시지를 출력
        st.error(f"❌ 오류: 지정된 경로에 파일 '{file_path}'이 없습니다. 파일을 추가하거나 경로를 수정해주세요.")
        st.info("💡 PDF 파일을 앱이 실행되는 환경에 넣은 후, 89번째 줄의 파일명을 정확히 일치시켜주세요!")
        st.stop()
        
    vectorstore = get_vectorstore(pages)
    retriever = vectorstore.as_retriever()

    # 채팅 히스토리 요약 시스템 프롬프트
    contextualize_q_system_prompt = """주어진 대화 기록과 최신 사용자 질문을 참고하여, \
    대화 기록 없이도 이해할 수 있는 독립적인 질문을 새롭게 구성해주세요. \
    질문에 대답하지 마세요. 필요한 경우 질문을 다시 구성하고, 그렇지 않으면 그대로 반환하세요."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )

    # 질문-답변 시스템 프롬프트 - **고등학생 챗봇 컨셉 유지**
    qa_system_prompt = """당신은 발랄하고 친절한 고등학교 선배 도우미 챗봇입니다. \
    사용자가 제공하는 학교 규정(context)을 참고하여 질문에 명확하고 신속하게 한국어로 답변해주세요. \
    답변은 항상 '친근한 요체'를 사용하며, 내용이 완벽하고 정확하도록 노력해주세요. \
    답변에는 적절하고 귀여운 이모티콘 (💖, 🥳, ✨ 등)을 꼭 포함시켜 활력을 더해주세요! \
    만약 주어진 context에서 답을 찾을 수 없다면, '음... 제가 가진 정보로는 확실히 알 수 없는 내용인걸요 🧐'라고 솔직하게 말해주세요.\

    {context}"""
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", qa_system_prompt),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )

    try:
        llm = ChatGoogleGenerativeAI(
            model=selected_model,
            temperature=0.7,
            convert_system_message_to_human=True # 시스템 메시지를 LLM에게 더 잘 전달
        )
    except Exception as e:
        st.error(f"❌ Gemini 모델 '{selected_model}' 로드 실패: {str(e)}")
        st.info("💡 'gemini-2.5-flash' 모델을 사용해보세요.")
        raise
        
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    return rag_chain

# Streamlit UI - **고등학생 챗봇 컨셉 유지**
st.header("✨ 교내 생활 만렙 찍기! 똑똑한 스쿨 플래너 봇 🤖")
st.markdown("_{tip: PDF 파일을 실제 학교 규정집으로 교체하면 더 유용하게 사용할 수 있어요!}_")

# 첫 실행 안내 메시지
if not os.path.exists("./chroma_db"):
    st.info("🔄 첫 실행입니다. 임베딩 모델 다운로드 및 규정집 분석 중... (조금만 기다려주세요!)")
    st.info("💡 다음 실행부터는 훨씬 빠르게 챗봇을 만날 수 있어요! 🥳")

# Gemini 모델 선택
option = st.selectbox("Select Gemini Model",
    ("gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash-exp"),
    index=0,
    help="Gemini 2.5 Flash가 가장 빠르고 효율적입니다"
)

try:
    with st.spinner("🔧 챗봇 초기화 중... 잠시만 기다려주세요"):
        rag_chain = initialize_components(option)
    st.success("✅ 챗봇이 준비되었습니다! 궁금한 걸 물어봐요! 💖")
except Exception as e:
    # initialize_components에서 이미 에러를 출력했지만, 혹시 모를 경우를 대비하여 한 번 더 출력
    st.error(f"⚠️ 초기화 중 오류 발생: {str(e)}")
    st.info("PDF 파일 경로와 GOOGLE_API_KEY를 확인해주세요.")
    st.stop()

chat_history = StreamlitChatMessageHistory(key="chat_messages")

# 대화 기록이 통합된 RAG 체인 구축
conversational_rag_chain = RunnableWithMessageHistory(
    rag_chain,
    lambda session_id: chat_history,
    input_messages_key="input",
    history_messages_key="history",
    output_messages_key="answer",
)


if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", 
                                     # **초기 인사말 수정**
                                     "content": "안녕! ✨ 학교생활 마스터 봇이야! 궁금한 규정이나 학사 꿀팁이 있다면 뭐든지 물어봐! 💖"}]

# 기존 대화 기록 출력
for msg in chat_history.messages:
    st.chat_message(msg.type).write(msg.content)


if prompt_message := st.chat_input("규정에 대해 궁금한 것을 질문해보세요."):
    st.chat_message("human").write(prompt_message)
    with st.chat_message("ai"):
        with st.spinner("생각 중... 잠시만요! 🤔"):
            config = {"configurable": {"session_id": "any"}}
            response = conversational_rag_chain.invoke(
                {"input": prompt_message},
                config)
            
            answer = response['answer']
            st.write(answer)
            with st.expander("참고 문서 확인 👀"):
                for doc in response['context']:
                    st.markdown(f"**출처:** {doc.metadata.get('source', '알 수 없음')} (페이지: {doc.metadata.get('page', '알 수 없음')})", help=doc.page_content)
