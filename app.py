import streamlit as st
import requests
import json
import base64
from pathlib import Path
import re

# --- 이미지 파일을 Base64로 인코딩하는 함수 ---
def img_to_base_64(image_path):
    """로컬 이미지 파일을 Base64 문자열로 변환합니다."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        st.warning(f"아이콘 파일을 찾을 수 없습니다: {image_path}. 아이콘 없이 앱을 실행합니다.")
        return None

# --- API 호출 함수 ---
def get_refocus_plan_from_gemini(api_key, situation):
    """Gemini API를 호출하여 재집중 계획을 생성합니다."""
    prompt = f"""
        당신은 선수의 심리를 코칭하는 전문 스포츠 심리학자입니다.

        '재집중 계획(Refocusing Plan)'은 선수가 예상치 못한 상황에 부딪혔을 때, 부정적인 생각의 고리를 끊고 현재에 다시 집중하도록 돕는 구체적인 행동 계획입니다.

        이제 사용자가 입력한 상황을 분석하여 '재집중 계획'을 세워주세요. 결과물은 반드시 [상황 요약], [결과목표], [과정목표] 세 부분으로 구성되어야 합니다.

        1.  **[상황 요약]**: 사용자가 입력한 '상황'을 "어떤 상황에서 어떤 감정을 느끼고 있다"는 형식으로 한 문장으로 명확하게 요약해주세요.
        2.  **[결과목표]**: 요약된 상황을 바탕으로, 선수가 가져야 할 인지적 관점의 전환, 즉 '생각의 목표'를 이성적인 문장으로 제시해주세요.
        3.  **[과정목표]**: 선수가 즉시 실행할 수 있는 구체적이고 명료한 '행동의 목표'를 제시해주세요.

        - 중요: 결과목표와 과정목표에서 가장 핵심적인 키워드나 구절을 Markdown 볼드체 형식(`**키워드**`)으로 감싸서 강조해주세요.
        - 각 목표 뒤에는 간단한 해설을 덧붙여주세요.

        응답 형식은 아래 예시를 반드시 지켜주세요:
        [상황 요약]
        {{AI가 생성한 상황 요약}}
        [결과목표]
        {{생성된 결과목표}}
        [결과목표 해설]
        {{생성된 결과목표 해설}}
        [과정목표]
        {{생성된 과정목표}}
        [과정목표 해설]
        {{생성된 과정목표 해설}}

        ---
        사용자 입력 상황: "{situation}"
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

# --- UI 스타일링 및 컴포넌트 함수 ---
def apply_ui_styles():
    """앱 전체에 적용될 CSS 스타일을 정의합니다."""
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
            
            :root {
                --primary-color: #2BA7D1;
                --black-color: #0D1628;
                --secondary-color: #86929A;
                --gray-color: #898D99;
                --divider-color: #F1F1F1;
                --icon-bg-color: rgba(12, 124, 162, 0.04);
            }

            .stApp {
                background-color: #f0f2f5;
            }
            
            /* Streamlit 헤더와 기본 여백 완전히 제거 */
            div.block-container {
                padding-top: 2rem !important;
                padding-bottom: 1.5rem;
            }
            
            header[data-testid="stHeader"] {
                display: none !important;
            }

            body, .stTextArea, .stButton>button {
                font-family: 'Noto Sans KR', sans-serif;
            }

            .main-container {
                background-color: white;
                padding: 2rem;
                border-radius: 32px;
            }

            .icon-container {
                width: 68px;
                height: 68px;
                background-color: var(--icon-bg-color);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 12px;
            }
            .icon-container img {
                width: 52px;
                height: 52px;
            }

            .title {
                font-size: 24px;
                font-weight: 700;
                color: var(--black-color);
                line-height: 36px;
                margin-bottom: 8px;
            }
            .subtitle {
                font-size: 16px;
                color: var(--secondary-color);
                line-height: 24px;
                margin-bottom: 28px; /* 여백 30% 감소 (40px -> 28px) */
            }
            
            /* 텍스트 입력창 스타일 */
            .stTextArea textarea {
                background-color: #f9fafb;
                border: 1px solid #D1D5DB;
                border-radius: 12px;
            }

            .section {
                border-bottom: 1px solid var(--divider-color);
                padding-bottom: 20px;
                margin-bottom: 20px;
            }
            
            .last-section {
                border-bottom: none;
                margin-bottom: 0;
                padding-bottom: 0;
            }

            .section-header {
                font-size: 12px;
                font-weight: 400;
                color: var(--gray-color);
                margin-bottom: 4px;
            }
            .section-title {
                font-size: 18px;
                font-weight: 700;
                color: var(--black-color);
                line-height: 28px;
                margin-bottom: 12px;
            }
            
            .goal-text {
                font-size: 18px;
                font-weight: 700;
                color: var(--black-color);
                line-height: 28px;
            }
            .goal-text span {
                color: var(--primary-color);
            }
            
            .explanation-text {
                font-size: 13px;
                color: var(--secondary-color);
                line-height: 20px;
                margin-top: 12px;
            }
            
            .stButton>button {
                background-color: var(--primary-color);
                color: white;
                font-size: 14px;
                font-weight: 400;
                border-radius: 12px;
                padding: 14px 0;
                border: none;
                box-shadow: 0px 5px 10px rgba(26, 26, 26, 0.10);
            }
            
            /* 모바일 반응형 스타일 */
            @media (max-width: 600px) {
                .main-container {
                    padding: 1.5rem;
                    border-radius: 20px;
                }
                 div.block-container {
                    padding-top: 1rem !important;
                }
            }
        </style>
    """, unsafe_allow_html=True)

def display_and_save_card(plan):
    """생성된 계획을 카드 형태로 표시하고 이미지 저장 버튼을 추가합니다."""
    
    # AI 응답에서 **text** 부분을 <span> 태그로 변환
    highlighted_outcome = re.sub(r'\*\*(.*?)\*\*', r'<span>\1</span>', plan['outcome_goal'])
    highlighted_process = re.sub(r'\*\*(.*?)\*\*', r'<span>\1</span>', plan['process_goal'])

    # HTML 컴포넌트 내부에 스타일을 직접 포함하여 iframe 문제를 해결
    card_html = f"""
    <style>
        /* 이 컴포넌트에 필요한 스타일만 복사 */
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&display=swap');
        :root {{
            --primary-color: #2BA7D1;
            --black-color: #0D1628;
            --secondary-color: #86929A;
            --gray-color: #898D99;
            --divider-color: #F1F1F1;
        }}
        body {{
            font-family: 'Noto Sans KR', sans-serif;
            margin: 0;
        }}
        .card-container {{
            background-color: white;
            padding: 2rem;
            border-radius: 32px;
        }}
        .section {{
            border-bottom: 1px solid var(--divider-color);
            padding-bottom: 20px;
            margin-bottom: 20px;
        }}
        .last-section {{
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }}
        .section-header {{
            font-size: 14px; /* 글씨 크기 증가 */
            font-weight: 700; /* 굵게 변경 */
            color: var(--gray-color);
            margin-bottom: 4px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: var(--black-color);
            line-height: 28px;
            margin-bottom: 12px;
        }}
        .goal-text {{
            font-size: 18px;
            font-weight: 700;
            color: var(--black-color);
            line-height: 28px;
        }}
        .goal-text span {{
            color: var(--primary-color);
        }}
        .explanation-text {{
            font-size: 13px;
            color: var(--secondary-color);
            line-height: 20px;
            margin-top: 12px;
        }}
        #save-btn {{
            width: 100%;
            padding: 14px;
            margin-top: 1rem;
            font-size: 14px;
            font-weight: 400;
            color: white;
            background-color: #2BA7D1;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            text-align: center;
            box-shadow: 0px 5px 10px rgba(26, 26, 26, 0.10);
        }}
    </style>

    <div id="refocus-plan-card" class="card-container">
        <div class="section">
            <p class="section-header">When</p>
            <p class="section-title">어떤 상황에서<br>재집중이 필요한가요?</p>
            <p class="explanation-text">{plan['when_summary']}</p>
        </div>

        <div class="section">
            <p class="section-header">결과 목표</p>
            <p class="goal-text">"{highlighted_outcome}"</p>
            <p class="explanation-text">{plan['outcome_explanation']}</p>
        </div>

        <div class="section last-section">
            <p class="section-header">과정 목표</p>
            <p class="goal-text">"{highlighted_process}"</p>
            <p class="explanation-text">{plan['process_explanation']}</p>
        </div>
    </div>
    
    <button id="save-btn">결과 저장하기</button>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const cardElement = document.getElementById("refocus-plan-card");
        const saveButton = this;
        
        saveButton.innerHTML = "저장 중...";
        saveButton.disabled = true;

        html2canvas(cardElement, {{
            useCORS: true,
            scale: 2,
            backgroundColor: 'white'
        }}).then(canvas => {{
            const image = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = image;
            link.download = "refocus-plan-card.png";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            saveButton.innerHTML = "결과 저장하기";
            saveButton.disabled = false;
        }});
    }}
    </script>
    """
    st.components.v1.html(card_html, height=850, scrolling=True)

# --- 메인 애플리케이션 로직 ---
def main():
    st.set_page_config(page_title="재집중 카드 생성기", layout="centered")
    apply_ui_styles()

    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None

    icon_path = Path(__file__).parent / "icon.png"
    icon_base64 = img_to_base_64(icon_path)

    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    if icon_base64:
        st.markdown(f"""
            <div class="icon-container">
                <img src="data:image/png;base64,{icon_base64}" alt="icon">
            </div>
        """, unsafe_allow_html=True)
    st.markdown('<p class="title">재집중 카드</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">나만의 재집중 카드는 흔들린 집중력을 되찾기 위해<br>스스로 활용할 수 있는 훈련 도구입니다.</p>', unsafe_allow_html=True)

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다.")
        st.markdown('</div>', unsafe_allow_html=True)
        st.stop()

    with st.container():
      st.markdown('<div class="section">', unsafe_allow_html=True)
      st.markdown('<p class="section-header">When</p>', unsafe_allow_html=True)
      st.markdown('<p class="section-title">어떤 상황에서<br>재집중이 필요한가요?</p>', unsafe_allow_html=True)
      situation = st.text_area(
          "situation_input",
          height=120,
          placeholder="1점차 아슬아슬한 승부 상황에서 ‘내가 잘못 하면 어쩌지'라는 불안감이 앞서서 제대로 집중을 할 수가 없어",
          label_visibility="collapsed"
      )
      st.markdown('</div>', unsafe_allow_html=True)


    if st.button("나만의 재집중 계획 만들기", use_container_width=True):
        if not situation.strip():
            st.warning("재집중이 필요한 상황을 입력해주세요.")
            st.session_state.generated_plan = None
        else:
            with st.spinner("AI가 당신만을 위한 재집중 카드를 만들고 있습니다..."):
                result_text = get_refocus_plan_from_gemini(api_key, situation)
                try:
                    if result_text.startswith("오류:") or result_text.startswith("API 요청 중"):
                        raise ValueError(result_text)
                    
                    when_summary = result_text.split('[상황 요약]')[1].split('[결과목표]')[0].strip()
                    outcome_goal = result_text.split('[결과목표]')[1].split('[결과목표 해설]')[0].strip()
                    outcome_explanation = result_text.split('[결과목표 해설]')[1].split('[과정목표]')[0].strip()
                    process_goal = result_text.split('[과정목표]')[1].split('[과정목표 해설]')[0].strip()
                    process_explanation = result_text.split('[과정목표 해설]')[1].strip()
                    
                    st.session_state.generated_plan = {
                        "when_summary": when_summary,
                        "outcome_goal": outcome_goal,
                        "outcome_explanation": outcome_explanation,
                        "process_goal": process_goal,
                        "process_explanation": process_explanation
                    }
                except (IndexError, ValueError) as e:
                    st.error(f"결과 처리 중 오류가 발생했습니다: {e}")
                    st.session_state.generated_plan = None
    
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.generated_plan:
        st.write("")
        display_and_save_card(st.session_state.generated_plan)

if __name__ == "__main__":
    main()

