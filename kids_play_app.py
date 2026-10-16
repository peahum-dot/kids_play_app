"""
[바이브코딩 두 번째 프로젝트] 딸아이와 함께하는 '오늘 뭐 하고 놀까?' 일일 가챠 웹앱
- 주요 기능:
  1) 🎨 오늘의 그림 그리기 주제 뽑기 (상상력 주제 + 3단계 그리기 가이드)
  2) 🎲 오늘의 보드게임 추천 & 랜덤 뽑기 (우리 집 보드게임 목록 관리 + 오늘의 승리 미션)
  3) 🎈 오늘 어디서 놀까? 코스 추천 (날씨·시간별 실내/야외 놀이 & 작은 탐험 미션)
- 실행 방법: 터미널에서 `streamlit run kids_play_app.py` 입력
"""

import json
from pathlib import Path
import random
import streamlit as st

# ---------------------------------------------------------
# 0. API 키 설정 불러오기 (기존 .gemini_config.json 및 클라우드 Secrets 공유 가능!)
# ---------------------------------------------------------
CONFIG_FILE = Path(".gemini_config.json")


def load_saved_config() -> dict:
    """클라우드 Secrets 또는 로컬 .gemini_config.json에서 API 키 로드"""
    cloud_key = ""
    try:
        if "GEMINI_API_KEY" in st.secrets:
            cloud_key = str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        cloud_key = ""

    local_cfg = {}
    if CONFIG_FILE.exists():
        try:
            local_cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            local_cfg = {}

    return {
        "api_key": cloud_key or local_cfg.get("api_key", ""),
        "model_name": local_cfg.get("model_name", "gemini-3.8-flash"),
    }


# ---------------------------------------------------------
# 1. 화면 기본 설정 및 아이 눈높이에 맞춘 따뜻한 파스텔 톤 스타일(CSS)
# ---------------------------------------------------------
st.set_page_config(
    page_title="오늘 뭐 하고 놀까? 우리 가족 놀이 뽑기",
    page_icon="🎈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 3.5rem;
        max-width: 620px;
        word-break: keep-all;
    }
    .kids-header {
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%);
        color: #ffffff;
        padding: 1.3rem 1.4rem;
        border-radius: 20px;
        margin-bottom: 1.1rem;
        box-shadow: 0 6px 16px rgba(255, 117, 140, 0.25);
        text-align: center;
    }
    .kids-badge {
        display: inline-block;
        background: rgba(255, 255, 255, 0.25);
        color: #ffffff;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 0.2rem 0.7rem;
        border-radius: 999px;
        margin-bottom: 0.4rem;
    }
    .kids-title {
        font-size: 1.45rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.3;
        color: #ffffff;
    }
    .kids-sub {
        font-size: 0.88rem;
        color: #fff0f5;
        margin-top: 0.35rem;
        margin-bottom: 0;
    }
    .result-card {
        background: #fff9fb;
        border: 2px dashed #ff9ebb;
        border-radius: 16px;
        padding: 1.2rem;
        margin-top: 0.8rem;
        margin-bottom: 0.8rem;
    }
    .result-headline {
        font-size: 1.2rem;
        font-weight: 800;
        color: #d6336c;
        margin-bottom: 0.5rem;
    }
    div.stButton > button[kind="primary"] {
        width: 100%;
        height: 3.3rem;
        background: linear-gradient(135deg, #ff6b8b 0%, #ff8e53 100%);
        color: #ffffff;
        border: none;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(255, 107, 139, 0.28);
    }
    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

saved_cfg = load_saved_config()

st.markdown(
    """
    <div class="kids-header">
        <div class="kids-badge">✨ 신나는 일일 놀이 가챠 ✨</div>
        <p class="kids-title">오늘 우리 뭐 하고 놀까?</p>
        <p class="kids-sub">그림 그리기 · 보드게임 · 오늘 놀 곳을 뽑아보세요!</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2. 기본 추천 데이터 (API 키 없이도 즉시 작동하는 랜덤 뽑기 풀)
# ---------------------------------------------------------
DRAWING_POOL = {
    "동물 친구들": [
        {
            "title": "무지개 구름 위에서 딸기 아이스크림을 먹는 아기 고양이",
            "steps": [
                "1단계: 도화지 가운데에 동그란 고양이 얼굴과 뾰족한 두 귀를 그려요.",
                "2단계: 고양이 두 손에 커다란 3단 딸기 아이스크림 콘을 들려줘요.",
                "3단계: 아래쪽에 몽글몽글한 구름을 그리고 일곱 빛깔 무지개로 색칠해요!",
            ],
            "secret_mission": "고양이 머리 위에 작은 왕관이나 리본을 하나 숨겨서 그려보세요!",
        },
        {
            "title": "우주복을 입고 달나라에서 방방 뛰는 강아지 탐험대",
            "steps": [
                "1단계: 동그란 투명 헬멧을 쓴 귀여운 강아지를 그려요.",
                "2단계: 발아래에 치즈처럼 구멍이 뽕뽕 뚫린 노란 달 표면을 그려요.",
                "3단계: 배경에 반짝이는 별들과 알록달록한 행성을 색칠해요!",
            ],
            "secret_mission": "달 뒷편에 몰래 구경하고 있는 귀여운 외계인 친구를 한 명 그려보세요!",
        },
    ],
    "달콤 간식·마법": [
        {
            "title": "초콜릿 강이 흐르는 마법의 과자 집",
            "steps": [
                "1단계: 와플 모양 벽과 생크림 지붕이 있는 집을 크게 그려요.",
                "2단계: 창문은 도넛으로, 문은 초콜릿 바로 꾸며줘요.",
                "3단계: 집 앞마당에 막대사탕 나무와 솜사탕 구름을 가득 채워요!",
            ],
            "secret_mission": "내가 가장 좋아하는 과자 하나를 지붕 꼭대기에 크게 그려보세요!",
        },
        {
            "title": "하늘을 나는 마법 양탄자와 꼬마 마법사",
            "steps": [
                "1단계: 멋진 무늬가 있는 마법 양탄자를 비스듬히 그려요.",
                "2단계: 양탄자 위에 고깔모자와 요술봉을 든 내 모습을 그려요.",
                "3단계: 요술봉 끝에서 반짝이는 별빛 가루가 쏟아지게 색칠해요!",
            ],
            "secret_mission": "마법 양탄자 옆을 함께 날아가는 새나 나비를 그려보세요!",
        },
    ],
}

DEFAULT_BOARDGAMES = [
    "스플렌더 (보석 모으기)",
    "루미큐브 (숫자 타일 조합)",
    "할리갈리 (과일 종 치기)",
    "도블 (같은 그림 빨리 찾기)",
    "카탄 (섬 개척하기)",
    "다빈치 코드 (숫자 추리)",
    "펭귄 얼음 깨기",
    "부루마블 / 모두의 마블",
]

WIN_REWARDS = [
    "🏆 오늘 저녁 간식 메뉴 결정권 갖기!",
    "🏆 진 사람이 이긴 사람 어깨 1분 동안 시원하게 안마해 주기!",
    "🏆 이긴 사람이 내일 아침에 들을 신나는 노래 1곡 고르기!",
    "🏆 진 사람이 이긴 사람에게 칭찬 3가지 크게 해 주기!",
]

PLAY_PLACES = {
    "집콕 실내 놀이": [
        {
            "place": "거실 텐트 & 이불 요새 캠핑장",
            "activity": "식탁이나 의자에 담요를 덮어 비밀 아지트를 만들고, 손전등을 켜서 책 읽기 & 간식 소풍!",
            "mission": "비밀 아지트 입구 문패를 종이에 직접 그려서 붙이기",
        },
        {
            "place": "우리 집 거실 보물찾기 탐험대",
            "activity": "작은 쪽지 5개를 거실 곳곳에 숨기고 힌트 지도를 그려서 보물 찾아내기!",
            "mission": "아빠가 먼저 숨기고, 다음 판은 딸이 숨겨서 아빠가 찾기",
        },
    ],
    "동네 산책·야외": [
        {
            "place": "동네 공원 자연 보물 도감 만들기",
            "activity": "공원을 산책하며 가장 특이한 모양의 나뭇잎, 예쁜 돌멩이, 꽃 사진을 찍어 탐험 도감 완성하기!",
            "mission": "하트 모양이나 별 모양을 닮은 자연물 1개 찾아내기",
        },
        {
            "place": "자전거·킥보드 타고 동네 한 바퀴 & 편의점 간식 데이트",
            "activity": "시원한 바람을 맞으며 공원 트랙을 달리고, 돌아오는 길에 각자 고른 간식 1개씩 사 오기!",
            "mission": "평소 안 먹어본 새로운 과자나 음료수 1가지 도전해 보기",
        },
    ],
    "주말 나들이": [
        {
            "place": "국립중앙과학관 / 어린이 과학체험관 나들이",
            "activity": "신기한 과학 원리 체험 전시물도 직접 눌러보고 야외 광장에서 뛰어놀기!",
            "mission": "오늘 본 것 중 가장 신기했던 전시물 앞에서 재미있는 포즈로 사진 찍기",
        },
        {
            "place": "대형 서점·도서관 북카페 데이트",
            "activity": "서로에게 추천하고 싶은 재미있는 그림책·만화책 1권씩 골라 나란히 앉아 읽기!",
            "mission": "책 속에서 가장 마음에 드는 캐릭터 1명 집에 와서 그려보기",
        },
    ],
}


# ---------------------------------------------------------
# 3. Gemini AI로 맞춤형 놀이 추천 생성 함수 (API 키 연결 시 작동)
# ---------------------------------------------------------
def generate_ai_play_idea(api_key_str: str, model_str: str, mode_type: str, user_pref: str) -> dict:
    """Gemini API를 호출해 아이 눈높이에 맞춘 새로운 그림 주제/보드게임 미션/놀이 코스를 생성"""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key_str)
    prompt = f"""
당신은 초등학생 딸아이와 아빠가 주말/일상에 함께 신나게 놀 수 있도록 아이디어를 주는 다정한 놀이 요정 AI입니다.
요청 분야: {mode_type}
사용자 선택 조건: {user_pref}

아이의 상상력과 호기심을 자극하도록 아래 JSON 형식으로만 응답하세요:
{{
  "headline": "한눈에 신나는 추천 제목 (이모지 포함, 1줄)",
  "description": "어떻게 놀면 재미있는지 아이 눈높이에서 다정하게 설명 (2~3문장)",
  "steps": [
    "1단계 또는 첫 번째 팁",
    "2단계 또는 두 번째 팁",
    "3단계 또는 세 번째 팁"
  ],
  "bonus_mission": "오늘 놀이를 더 특별하게 만들어 줄 귀여운 보너스 미션 1문장"
}}
"""
    response = client.models.generate_content(
        model=model_str,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.8,
        ),
    )
    return json.loads(response.text)


# ---------------------------------------------------------
# 4. 3대 놀이 탭 구성 (🎨 그림 그리기 / 🎲 보드게임 / 🎈 오늘 놀 곳)
# ---------------------------------------------------------
tab_draw, tab_board, tab_place = st.tabs(
    ["🎨 무슨 그림 그릴까?", "🎲 어떤 보드게임 할까?", "🎈 어디서 놀까?"]
)

# [탭 1] 오늘의 그림 그리기 주제 뽑기
with tab_draw:
    with st.container(border=True):
        st.markdown("##### 🎨 오늘의 상상 그림 주제 뽑기")
        draw_theme = st.selectbox(
            "오늘 그리고 싶은 테마를 골라보세요!",
            options=["동물 친구들", "달콤 간식·마법", "우주·공룡 대모험", "우리 가족 이야기"],
        )
        draw_tool = st.radio(
            "오늘 사용할 그리기 도구",
            options=["색연필 · 사인펜", "물감 · 크레파스", "연필 스케치", "태블릿 그리기"],
            horizontal=True,
        )

        if st.button("🎰 오늘의 그림 주제 가챠 뽑기!", type="primary", key="btn_draw"):
            st.balloons()
            if saved_cfg.get("api_key"):
                try:
                    with st.spinner("놀이 요정이 재미있는 그림 주제를 만들고 있어요..."):
                        st.session_state["draw_result"] = generate_ai_play_idea(
                            saved_cfg["api_key"],
                            saved_cfg["model_name"],
                            "초등학생 딸과 함께 그릴 상상화 그림 주제",
                            f"테마: {draw_theme}, 도구: {draw_tool}",
                        )
                except Exception:
                    pool = DRAWING_POOL.get(draw_theme, DRAWING_POOL["동물 친구들"])
                    picked = random.choice(pool)
                    st.session_state["draw_result"] = {
                        "headline": f"🎨 {picked['title']}",
                        "description": f"오늘은 {draw_tool}을 사용해서 재미있게 그려볼까요?",
                        "steps": picked["steps"],
                        "bonus_mission": picked["secret_mission"],
                    }
            else:
                pool = DRAWING_POOL.get(draw_theme, DRAWING_POOL["동물 친구들"])
                picked = random.choice(pool)
                st.session_state["draw_result"] = {
                    "headline": f"🎨 {picked['title']}",
                    "description": f"오늘은 [{draw_tool}]로 나만의 멋진 작품을 완성해 보세요!",
                    "steps": picked["steps"],
                    "bonus_mission": picked["secret_mission"],
                }

    if "draw_result" in st.session_state:
        res = st.session_state["draw_result"]
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-headline">{res['headline']}</div>
                <p style="margin-bottom:0.6rem;">{res['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            st.markdown("**🖍️ 쑥쑥 따라 그리는 3단계 팁**")
            for s in res.get("steps", []):
                st.markdown(f"- {s}")
            st.info(f"🌟 **비밀 보너스 미션:** {res.get('bonus_mission', '')}")

# [탭 2] 오늘의 보드게임 추천 & 랜덤 뽑기
with tab_board:
    with st.container(border=True):
        st.markdown("##### 🎲 우리 집 보드게임 뽑기")
        my_games = st.multiselect(
            "오늘 후보에 넣을 우리 집 보드게임 목록 (추가·제외 가능)",
            options=DEFAULT_BOARDGAMES,
            default=DEFAULT_BOARDGAMES[:5],
        )
        custom_game = st.text_input(
            "우리 집에 있는 다른 보드게임 직접 추가 (쉼표 `,`로 구분)",
            placeholder="예: 젠가, 바퀴벌레 포커, 쿼리도",
        )
        game_mood = st.radio(
            "오늘 원하는 게임 분위기",
            options=["아무거나 랜덤 뽑기!", "두뇌 회전 전략 게임", "순발력 · 웃음 폭발 게임"],
            horizontal=True,
        )

        if st.button("🎲 오늘의 보드게임 & 승리 미션 뽑기!", type="primary", key="btn_board"):
            candidate_list = list(my_games)
            if custom_game.strip():
                for g in custom_game.split(","):
                    if g.strip():
                        candidate_list.append(g.strip())

            if not candidate_list:
                st.warning("후보 보드게임을 최소 1개 이상 선택하거나 입력해 주세요!")
            else:
                st.balloons()
                chosen_game = random.choice(candidate_list)
                chosen_reward = random.choice(WIN_REWARDS)
                st.session_state["board_result"] = {
                    "game": chosen_game,
                    "reward": chosen_reward,
                    "mood": game_mood,
                }

    if "board_result" in st.session_state:
        b_res = st.session_state["board_result"]
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-headline">🎲 오늘의 당첨 게임: {b_res['game']}</div>
                <p style="margin-bottom:0.3rem;">선택 분위기: <b>{b_res['mood']}</b></p>
                <p style="margin-bottom:0;"><b>{b_res['reward']}</b></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# [탭 3] 오늘 어디서 놀까?
with tab_place:
    with st.container(border=True):
        st.markdown("##### 🎈 오늘 어디서 뭐 하고 놀까?")
        place_type = st.selectbox(
            "오늘의 날씨와 컨디션은 어떤가요?",
            options=["집콕 실내 놀이", "동네 산책·야외", "주말 나들이"],
        )
        play_time = st.radio(
            "놀 수 있는 시간",
            options=["1시간 반짝 놀이", "2~3시간 알차게", "반나절 신나게"],
            horizontal=True,
        )

        if st.button("🎈 오늘의 놀이 장소 & 탐험 미션 뽑기!", type="primary", key="btn_place"):
            st.balloons()
            if saved_cfg.get("api_key"):
                try:
                    with st.spinner("신나는 놀이 코스를 찾고 있어요..."):
                        st.session_state["place_result"] = generate_ai_play_idea(
                            saved_cfg["api_key"],
                            saved_cfg["model_name"],
                            "초등학생 딸과 아빠가 함께 놀 장소와 활동 추천",
                            f"구분: {place_type}, 시간: {play_time}",
                        )
                except Exception:
                    p_pool = PLAY_PLACES.get(place_type, PLAY_PLACES["집콕 실내 놀이"])
                    picked_p = random.choice(p_pool)
                    st.session_state["place_result"] = {
                        "headline": f"🎈 {picked_p['place']}",
                        "description": picked_p["activity"],
                        "steps": [f"예상 소요 시간: {play_time}"],
                        "bonus_mission": picked_p["mission"],
                    }
            else:
                p_pool = PLAY_PLACES.get(place_type, PLAY_PLACES["집콕 실내 놀이"])
                picked_p = random.choice(p_pool)
                st.session_state["place_result"] = {
                    "headline": f"🎈 {picked_p['place']}",
                    "description": picked_p["activity"],
                    "steps": [
                        f"추천 시간: {play_time}",
                        "출발 전 물통과 작은 간식을 챙기면 즐거움이 두 배!",
                    ],
                    "bonus_mission": picked_p["mission"],
                }

    if "place_result" in st.session_state:
        p_res = st.session_state["place_result"]
        st.markdown(
            f"""
            <div class="result-card">
                <div class="result-headline">{p_res['headline']}</div>
                <p style="margin-bottom:0.5rem;">{p_res['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.container(border=True):
            for tip in p_res.get("steps", []):
                st.markdown(f"- {tip}")
            st.success(f"🚩 **오늘의 작은 탐험 미션:** {p_res.get('bonus_mission', '')}")

# ---------------------------------------------------------
# 5. 하단 AI 키 설정 (선택사항 - 평소엔 접혀 있음)
# ---------------------------------------------------------
st.write("")
with st.expander("⚙️ 부모님용 AI 설정 (선택사항)", expanded=False):
    st.caption(
        "API 키가 없어도 기본 랜덤 뽑기 모드로 모든 기능이 작동하며, Gemini API 키가 연결되면 매번 새로운 AI 그림 주제와 놀이 코스를 무한 생성합니다."
    )
    input_key = st.text_input(
        "Gemini API Key",
        value=saved_cfg.get("api_key", ""),
        type="password",
    )
    if st.button("API 키 저장"):
        CONFIG_FILE.write_text(
            json.dumps({"api_key": input_key.strip(), "model_name": "gemini-3.8-flash"}),
            encoding="utf-8",
        )
        st.success("저장되었습니다! 새로고침하면 AI 모드가 켜집니다.")