import streamlit as st
import requests
import json
import re

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

        '재집중 계획(Refocusing Plan)'은 선수가 예상치 못한 상황에 부딪혔을 때, 부정적인 생각의 고리를 끊고 현재에 다시 집중하도록 돕는 구체적인 행동 계획입니다.

        이제 사용자가 입력한 상황을 분석하여 '재집중 계획'을 세워주세요. 결과물은 반드시 [상황 요약], [결과목표], [과정목표] 세 부분으로 구성되어야 합니다.

        1.  **[상황 요약]**: 사용자가 입력한 '상황'을 "어떤 상황에서 어떤 감정을 느끼고 있다"는 형식으로 한 문장으로 명확하게 요약해주세요.
        2.  **[결과목표]**: 요약된 상황을 바탕으로, 선수가 가져야 할 인지적 관점의 전환, 즉 '생각의 목표'를 이성적인 문장으로 제시해주세요.
        3.  **[과정목표]**: 선수가 즉시 실행할 수 있는 구체적이고 명료한 '행동의 목표'를 제시해주세요.

        각 목표 뒤에는 간단한 해설을 덧붙여주세요.

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

# --- 결과 표시 및 이미지 저장 컴포넌트 함수 ---
def display_and_save_card(plan):
    """
    생성된 계획을 카드 형태로 표시하고 이미지 저장 버튼을 추가하는 HTML 컴포넌트를 생성합니다.
    """
    card_html = f"""
    <div id="refocus-plan-card">
        <div class="result-card when-card">
            <h3>1. When (상황 및 심리 요약)</h3>
            <p>{plan['when_summary']}</p>
        </div>
        <div class="result-card outcome-card">
            <h3>2. 결과목표 (생각의 전환)</h3>
            <p>{plan['outcome_goal']}</p>
            <p class="explanation"><strong>해설:</strong> {plan['outcome_explanation']}</p>
        </div>
        <div class="result-card process-card">
            <h3>3. 과정목표 (즉각적 행동)</h3>
            <p>"{plan['process_goal']}"</p>
            <p class="explanation"><strong>해설:</strong> {plan['process_explanation']}</p>
        </div>
    </div>
    <br>
    <button id="save-btn">이미지로 저장 📸</button>

    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap');
        
        #refocus-plan-card, #save-btn {{
            font-family: 'Noto Sans KR', sans-serif;
        }}

        .result-card {{
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 20px;
            border: 1px solid;
            background-color: #f8f9fa;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .when-card {{
            background-color: #f3f4f6;
            border-color: #d1d5db;
        }}
        .outcome-card {{
            background-color: #e0f2fe;
            border-color: #7dd3fc;
        }}
        .process-card {{
            background-color: #fff7ed;
            border-color: #fdba74;
        }}
        .result-card h3 {{
            font-family: 'Noto Sans KR', sans-serif;
            font-weight: 700;
            margin-top: 0;
            color: #1f2937;
            border-bottom: 2px solid #6b7280;
            padding-bottom: 10px;
        }}
        .result-card p {{
            font-size: 1.1rem;
            font-weight: 500;
            color: #333;
        }}
        .result-card .explanation {{
            font-size: 0.9rem;
            color: #4b5563;
            font-weight: 400;
            line-height: 1.6;
        }}
        #save-btn {{
            display: block;
            width: 100%;
            padding: 12px;
            font-size: 18px;
            font-weight: bold;
            color: white;
            background-color: #28a745;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            text-align: center;
        }}
        #save-btn:hover {{
            background-color: #218838;
        }}
    </style>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script>
    document.getElementById("save-btn").onclick = function() {{
        const cardElement = document.getElementById("refocus-plan-card");
        const saveButton = this;
        
        const originalButtonText = saveButton.innerHTML;
        saveButton.innerHTML = "저장 중...";
        saveButton.disabled = true;

        html2canvas(cardElement, {{
            useCORS: true,
            scale: 2 // 해상도를 높여 이미지 품질 개선
        }}).then(canvas => {{
            const image = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.href = image;
            link.download = "refocus-plan-card.png";
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            saveButton.innerHTML = originalButtonText;
            saveButton.disabled = false;
        }});
    }}
    </script>
    """
    st.components.v1.html(card_html, height=800, scrolling=True)

# --- 메인 애플리케이션 로직 ---
def main():
    st.set_page_config(page_title="나만의 재집중 계획 생성기", page_icon="🚀")

    # --- 세션 상태 초기화 ---
    if 'generated_plan' not in st.session_state:
        st.session_state.generated_plan = None

    # --- 헤더 ---
    st.title("나만의 재집중 계획 수립하기 🚀")
    st.markdown("예상치 못한 상황에 흔들리지 않도록, 현재에 집중하는 방법을 찾아보세요.")
    st.divider()

    # --- API 키 설정 (Secrets에서만 가져오기) ---
    api_key = None
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except (FileNotFoundError, KeyError):
        st.error("Streamlit Secrets에 'GEMINI_API_KEY'가 설정되지 않았습니다. 앱 관리자에게 문의하거나, 앱 설정에서 API 키를 추가해주세요.")
        st.stop()

    # --- 사용자 입력 ---
    st.subheader("1. When: 어떤 상황에서 재집중이 필요한가요?")
    st.markdown("시합 중 실수, 예상치 못한 방해 등 구체적인 상황과 그때 겪는 어려움을 적어주세요.")
    situation = st.text_area(
        "situation_input", 
        height=150, 
        placeholder="예시) 축구 경기 막판, 결정적인 페널티킥을 차야 하는 상황입니다. '이걸 놓치면 우리 팀이 진다'는 생각에 다리가 무거워지고 심장이 너무 빨리 뜁니다.",
        label_visibility="collapsed"
    )

    # --- 생성 버튼 ---
    if st.button("재집중 계획 생성하기", type="primary", use_container_width=True):
        if not situation.strip():
            st.warning("재집중이 필요한 상황을 입력해주세요.")
        else:
            with st.spinner("AI가 맞춤형 계획을 세우고 있습니다... 잠시만 기다려주세요."):
                result_text = get_refocus_plan_from_gemini(api_key, situation)
                
                try:
                    if result_text.startswith("오류:") or result_text.startswith("API 요청 중"):
                        raise ValueError(result_text)

                    # 응답 텍스트 파싱
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
                    st.error(f"결과를 처리하는 중 오류가 발생했습니다. 다시 시도해주세요.\n\n오류 내용: {e}")
                    st.session_state.generated_plan = None

    # --- 결과 표시 ---
    if st.session_state.generated_plan:
        plan = st.session_state.generated_plan
        st.divider()
        st.success("카드가 완성되었습니다! 필요할 때마다 꺼내보거나 이미지로 저장하여 활용하세요.")
        display_and_save_card(plan)


if __name__ == "__main__":
    main()