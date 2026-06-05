import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="AI 자리 배치 챗봇", page_icon="🪑", layout="centered")
st.title("🪑 AI 자리 배치 챗봇")
st.caption("인원수, 조당 인원, 특별 조건(예: 특정인 분리 등)을 입력하시면 AI가 최적의 자리를 배치해 드립니다.")

# 2. Streamlit Secrets에서 API 키 로드 및 클라이언트 초기화
# Streamlit Community Cloud 환경 및 로컬 .streamlit/secrets.toml 대응
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    st.error("🔑 API 키가 설정되지 않았습니다. Streamlit Secrets에 GEMINI_API_KEY를 등록해주세요.")
    st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(class_name=f"클라이언트 초기화 실패: {e}")
    st.stop()

# 3. 세션 상태(Session State)로 채팅 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "안녕하세요! 어떤 방식으로 자리를 배치해 드릴까요?\n\n**예시:**\n- '20명을 4명씩 5개 조로 짜줘. 철수랑 영희는 같은 조로 해줘.'\n- '교실 자리 배치표를 4x5 형태로 만들어줘.'"
        }
    ]

# 4. 기존 대화 기록 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력 처리
if user_input := st.chat_input("자리 배치 요청 사항을 입력하세요..."):
    # 사용자 메시지 화면에 표시 및 저장
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # AI 응답 생성
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🔄 최적의 자리를 배치하는 중입니다...")
        
        try:
            # 대화 맥락을 유지하기 위해 시스템 프롬프트와 기존 대화 기록을 포함하여 API 호출
            # 시스템 프롬프트로 '자리 배치 전문가' 페르소나 부여
            system_instruction = (
                "당신은 공정하고 효율적인 자리 배치를 도와주는 전문가입니다. "
                "사용자의 요청(인원, 조건 등)을 정확히 반영하여 가독성이 좋은 표(Markdown 테이블 등)나 "
                "구분된 리스트 형태로 자리 배치 결과를 제공하세요. 필요하다면 간단한 이유나 팁도 덧붙여주세요."
            )
            
            # API 전송용 컨텐츠 리스트 구성
            contents = []
            for msg in st.session_state.messages[:-1]:  # 방금 넣은 user_input 직전까지의 기록
                role = "model" if msg["role"] == "assistant" else "user"
                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg["content"])]))
            
            # 마지막 사용자 입력 추가
            contents.append(types.Content(role="user", parts=[types.Part.from_text(text=user_input)]))
            
            # gemini-2.5-flash-lite 모델 호출
            response = client.models.generate_content(
                model='gemini-2.5-flash-lite',
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.7, # 적당한 창의성과 규칙 준수
                )
            )
            
            # 결과 출력 및 저장
            ai_response = response.text
            message_placeholder.markdown(ai_response)
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
        except APIError as ae:
            # Gemini API 관련 오류 처리
            error_msg = f"❌ Gemini API 오류가 발생했습니다: {ae.message}"
            message_placeholder.markdown(error_msg)
        except Exception as e:
            # 기타 일반 오류 처리
            error_msg = f"⚠️ 오류가 발생했습니다: {str(e)}"
            message_placeholder.markdown(error_msg)
