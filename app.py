import streamlit as st
from openai import OpenAI

import streamlit as st
import sqlite3
from openai import OpenAI
import hashlib

# ==========================================
# 1. 데이터베이스(DB) 관리 함수들
# ==========================================

# DB 연결 및 테이블 생성 (처음 실행 시 자동 생성)
def init_db():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    # 사용자 정보 테이블 (아이디, 비밀번호)
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    # 대화 기록 테이블 (사용자, 역할, 메시지)
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            username TEXT,
            role TEXT,
            content TEXT,
            FOREIGN KEY(username) REFERENCES users(username)
        )
    ''')
    conn.commit()
    conn.close()

# 비밀번호 암호화 (보안을 위해 비밀번호를 알 수 없는 문자로 변환)
def make_hashes(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

# 회원가입 함수
def add_user(username, password):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users(username, password) VALUES (?,?)', 
                  (username, make_hashes(password)))
        conn.commit()
        result = True
    except:
        result = False # 이미 존재하는 아이디일 경우
    conn.close()
    return result

# 로그인 확인 함수
def check_login(username, password):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
              (username, make_hashes(password)))
    data = c.fetchall()
    conn.close()
    return data

# 메시지 저장 함수
def save_message(username, role, content):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute('INSERT INTO messages(username, role, content) VALUES (?,?,?)', 
              (username, role, content))
    conn.commit()
    conn.close()

# 메시지 불러오기 함수
def load_messages(username):
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute('SELECT role, content FROM messages WHERE username = ?', (username,))
    data = c.fetchall()
    conn.close()
    return data

# ==========================================
# 2. 메인 앱 화면 구성
# ==========================================

# DB 초기화 실행
init_db()

st.title("🔐 나만의 시크릿 AI 챗봇")

# 사이드바 설정 (API 키 등)
with st.sidebar:
    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
    else:
        groq_api_key = st.text_input("Groq API Key", type="password")
        st.markdown("[키 발급받기](https://console.groq.com/keys)")

# 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

# ==========================================
# 3. 로그인 / 회원가입 화면 (로그인 안 했을 때)
# ==========================================
if not st.session_state.logged_in:
    menu = ["로그인", "회원가입"]
    choice = st.sidebar.selectbox("메뉴 선택", menu)

    if choice == "로그인":
        st.subheader("로그인 상태가 아닙니다")
        id_input = st.text_input("아이디")
        pw_input = st.text_input("비밀번호", type="password")
        
        if st.button("로그인 하기"):
            if check_login(id_input, pw_input):
                st.session_state.logged_in = True
                st.session_state.username = id_input
                st.success(f"{id_input}님 환영합니다! 잠시 후 대화창이 열립니다.")
                st.rerun() # 화면 새로고침
            else:
                st.error("아이디 또는 비밀번호가 틀렸습니다.")

    elif choice == "회원가입":
        st.subheader("새 계정 만들기")
        new_user = st.text_input("사용할 아이디")
        new_password = st.text_input("사용할 비밀번호", type="password")

        if st.button("가입하기"):
            if add_user(new_user, new_password):
                st.success("가입 성공! 로그인 메뉴로 이동해서 로그인해주세요.")
            else:
                st.warning("이미 존재하는 아이디입니다.")

# ==========================================
# 4. 채팅 화면 (로그인 성공했을 때)
# ==========================================
else:
    username = st.session_state.username
    st.sidebar.success(f"로그인 됨: **{username}**")
    
    if st.sidebar.button("로그아웃"):
        st.session_state.logged_in = False
        st.rerun()

    # DB에서 이전 대화 기록 가져오기
    saved_history = load_messages(username)
    
    # 세션에 대화 기록이 없으면 DB에서 가져온 것 채워넣기
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = []
        if saved_history:
            for role, content in saved_history:
                st.session_state.messages.append({"role": role, "content": content})
        else:
            # 처음 가입한 사람이면 인사말 추가
            welcome_msg = f"안녕하세요 {username}님! 무엇을 도와드릴까요?"
            st.session_state.messages.append({"role": "assistant", "content": welcome_msg})
            save_message(username, "assistant", welcome_msg)

    # 화면에 대화 내용 출력
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # 사용자 입력 처리
    if prompt := st.chat_input():
        if not groq_api_key:
            st.error("API 키가 필요합니다.")
            st.stop()

        # 1. 사용자 메시지 화면 표시 & 저장
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)
        save_message(username, "user", prompt) # DB에 영구 저장

        # 2. AI 답변 요청
        try:
            client = OpenAI(
                api_key=groq_api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            msg = response.choices[0].message.content
            
            # 3. AI 답변 화면 표시 & 저장
            st.session_state.messages.append({"role": "assistant", "content": msg})
            st.chat_message("assistant").write(msg)
            save_message(username, "assistant", msg) # DB에 영구 저장

        except Exception as e:
            st.error(f"오류: {e}")