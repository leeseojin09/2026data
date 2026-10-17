
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🩺",
    layout="wide",
)

# 각 페이지 파일을 등록합니다.
탐색 = st.Page(
    "pages/1_탐색.py",
    title="데이터 탐색",
    icon="🔎",
    default=True,
)

분류모델 = st.Page(
    "pages/2_분류_모델.py",
    title="분류 모델",
    icon="🧠",
)

채점표 = st.Page(
    "pages/3_채점표.py",
    title="모델 채점표",
    icon="📊",
)

전처리 = st.Page(
    "pages/4_전처리.py",
    title="데이터 전처리",
    icon="🧹",
)

모델소개 = st.Page(
    "pages/5_내가_만든_모델_소개.py",
    title="내가 만든 모델 소개",
    icon="📝",
)

# 사이드바 네비게이션 구성
페이지 = st.navigation(
    {
        "뇌졸중 예측 실습실": [
            탐색,
            분류모델,
            채점표,
            전처리,
            모델소개,
        ]
    },
    position="sidebar",
)

# 공통 시작 화면 정보
st.sidebar.caption("뇌졸중 데이터를 활용한 머신러닝 실습")

# 선택한 페이지 실행
페이지.run()
