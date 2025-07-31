import streamlit as st
import requests
import json

# --- API 호출 함수 ---
def get_refocus_plan_from_gemini(api_key, situation):
    """
    Gemini API를 호출하여 재집중 계획을 생성합니다.

    Args:
        api_key (str): Gemini API 키.
        situation (str): 사용자가 입력한 상황 텍스트.

    Returns:
        str: API로부터 받은 텍스트 응답.
    """
    prompt = f"""
        당신은 선수의 심리를 코칭하는 전문 스포츠 심리학자입니다.

        '재집중 계획(Refocusing Plan)'은 시합 중 예상치 못한 일이 일어날 때를 대비해 미리 대비책을 마련해두는 것입니다. 집중은 과거(화, 불만)나 미래(걱정)가 아닌 '현재(present)'에 해야 합니다. 훌륭한 선수들은 모두 자신만의 재집중 계획을 갖고 있습니다. 재집중 계획은 '결과목표'와 '과정목표'로 구성됩니다.

        - '결과목표(Outcome Goal)'는 상황을 인지적으로 재해석하여 마음을 다스리는 생각의 목표입니다. '화가 나는 것은 과거의 일일 뿐, 도움이 안 된다'와 같이 이성적인 문장으로 제시해야 합니다.
        - '과정목표(Process Goal)'는 즉시 실행할 수 있는 짧고 명료한 행동의 목표입니다. '물 마시고, 스트레칭하자' 또는 '과거다. 다시 집중!'처럼 구체적인 행동 단서를 제시해야 합니다.

        이제 다음 사용자가 입력한 상황에 맞는 '결과목표'와 '과정목표' 그리고 각각에 대한 간단한 해설을 생성해주세요. 응답은 반드시 한국어로 해주세요.

        응답 형식은 아래와 같이 반드시 지켜주세요:
        [결과목표]
        {{생성된 결과목표}}
        [결과목표 해설]
        {{생성된 결과목표 해설}}
        [과정목표]
        {{생성된 과정목표}}
        [과정목표 해설]
        {{생성된 과정목표 해설}}

        상황: "{situation}"
    """

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(data), timeout=120)
        response.raise_for_status()
        result = response.json()
        
        if 'candidates' in result and result['candidates']:
            part = result['candidates'][0].get('content', {}).get('parts', [{}])[0]
            return part.get('text', '오류: 응답에서 텍스트를 찾을 수 없습니다.')
        else:
            return f"오류: API 응답이 비어있거나 예상치 못한 형식입니다.\n응답 내용: {result}"
    except requests.exceptions.RequestException as e:
        return f"API 요청 중 오류가 발생했습니다: {e}"
    except Exception as e:
        return f"알 수 없는 오류가 발생했습니다: {e}"

# --- UI 스타일링 ---
def page_styling():
    """페이지에 적용할 CSS 스타일을 정의합니다."""
    st.markdown("""
        <style>
            .stTextArea textarea {
                height: 150px;
            }
            .result-card {
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                border: 1px solid;
            }
            .outcome-card {
                background-color: #e0f2fe;
                border-color: #7dd3fc;
            }
            .process-card {
                background-color: #fff7ed;
                border-color: #fdba74;
            }
            .result-card h3 {
                margin-top: 0;
                font-weight: bold;
            }
            .result-card p {
                font-size: 1.1rem;
                font-weight: 500;
            }
            .result-card .explanation {
                font-size: 0.9rem;
                color: #4b5563;
                font-weight: 400;
            }
        </style>
    """, unsafe_allow_html=True)

# --- 메인 애플리케이션 로직 ---
def main():
    st.set_page_config(page_title="나만의 재집중 계획 생성기", page_icon="🚀")
    page_styling()

    # --- 세션 상태 초기화 ---
    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None

    # --- 헤더 ---
    st.title("나만의 재집중 계획 수립하기 🚀")
    st.markdown("예상치 못한 상황에 흔들리지 않도록, 현재에 집중하는 방법을 찾아보세요.")
    st.divider()

    # --- API 키 입력 ---
    # Streamlit secrets에서 API 키를 가져옵니다.
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.warning("API 키를 찾을 수 없습니다. 아래 입력란에 Gemini API 키를 입력해주세요.")
        api_key = st.text_input("Gemini API 키를 입력하세요:", type="password")

    # --- 사용자 입력 ---
    st.subheader("1. When: 어떤 상황에서 재집중이 필요한가요?")
    st.markdown("시합 중 실수, 예상치 못한 방해 등 구체적인 상황과 그때 겪는 어려움을 적어주세요.")
    situation = st.text_area(
        "situation_input", 
        height=150, 
        placeholder="예시) 중요한 발표 중에 갑자기 머릿속이 하얘지고 준비한 내용이 기억나지 않았습니다. 당황해서 말을 더듬기 시작했습니다.",
        label_visibility="collapsed"
    )

    # --- 생성 버튼 ---
    if st.button("재집중 계획 생성하기", type="primary", use_container_width=True):
        if not api_key:
            st.error("Gemini API 키를 입력해야 계획을 생성할 수 있습니다.")
        elif not situation.strip():
            st.warning("재집중이 필요한 상황을 입력해주세요.")
        else:
            with st.spinner("AI가 맞춤형 계획을 세우고 있습니다... 잠시만 기다려주세요."):
                result_text = get_refocus_plan_from_gemini(api_key, situation)
                
                try:
                    if result_text.startswith("오류:") or result_text.startswith("API 요청 중"):
                        raise ValueError(result_text)

                    outcome_goal = result_text.split('[결과목표]')[1].split('[결과목표 해설]')[0].strip()
                    outcome_explanation = result_text.split('[결과목표 해설]')[1].split('[과정목표]')[0].strip()
                    process_goal = result_text.split('[과정목표]')[1].split('[과정목표 해설]')[0].strip()
                    process_explanation = result_text.split('[과정목표 해설]')[1].strip()
                    
                    st.session_state.generated_plan = {
                        "outcome_goal": outcome_goal,
                        "outcome_explanation": outcome_explanation,
                        "process_goal": process_goal,
                        "process_explanation": process_explanation
                    }
                except (IndexError, ValueError) as e:
                    st.error(f"결과를 처리하는 중 오류가 발생했습니다. 다시 시도해주세요.\n\n오류 내용: {e}")
                    st.session_state.generated_plan = None

    # --- 결과 표시 ---
    if st.session_state.generated_plan:
        plan = st.session_state.generated_plan
        st.divider()
        
        # 결과목표
        st.markdown(f"""
        <div class="result-card outcome-card">
            <h3>2. 결과목표 (생각의 전환)</h3>
            <p>{plan['outcome_goal']}</p>
            <p class="explanation"><strong>해설:</strong> {plan['outcome_explanation']}</p>
        </div>
        """, unsafe_allow_html=True)

        # 과정목표
        st.markdown(f"""
        <div class="result-card process-card">
            <h3>3. 과정목표 (즉각적 행동)</h3>
            <p>"{plan['process_goal']}"</p>
            <p class="explanation"><strong>해설:</strong> {plan['process_explanation']}</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()