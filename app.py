import streamlit as st
from openai import OpenAI

# 1. 사이트 제목 설정
st.title("🦙 우리가 만든 무료 AI 챗봇")
st.caption("Llama3 모델을 사용한 100% 무료 챗봇입니다!")

# 2. 사이드바: API 키 입력받기
with st.sidebar:
    st.header("설정")
    # 여기서 입력받은 키를 사용합니다
    groq_api_key = st.text_input("Groq API Key 입력", type="password")
    st.markdown("[무료 키 발급받으러 가기](https://console.groq.com/keys)")
    st.info("이 챗봇은 Groq API를 사용하여 돈이 들지 않습니다.")

# 3. 대화 기록(기억력) 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "안녕하세요! 무료라서 마음껏 대화할 수 있어요. 무엇을 도와드릴까요?"}]

# 4. 이전 대화 내용을 화면에 출력
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 5. 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요..."):
    # 키가 없으면 경고 메시지 띄우고 중단
    if not groq_api_key:
        st.error("왼쪽 사이드바에 Groq API Key를 먼저 넣어주세요!")
        st.stop()

    # 사용자 메시지 화면에 표시 및 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # 6. AI에게 답변 요청 (여기가 핵심!)
    try:
        # OpenAI 대신 Groq 서버로 연결하는 설정
        client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1" 
        )
        
        # 최신 무료 모델 'llama-3.3-70b-versatile' 사용
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=st.session_state.messages
        )
        
        msg = response.choices[0].message.content

        # AI 메시지 화면에 표시 및 저장
        st.session_state.messages.append({"role": "assistant", "content": msg})
        st.chat_message("assistant").write(msg)

    except Exception as e:
        # 에러가 나면 이유를 알려줌
        st.error(f"오류가 발생했습니다: {e}")