
# main.py — 뇌졸중 예측 실습실
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 네비게이션 페이지 설정
탐색페이지 = st.Page(
    "pages/1_탐색.py",
    title="데이터 탐색",
    icon="🔎",
    default=False
)

홈페이지 = st.Page(
    "main.py",
    title="홈",
    icon="🏠",
    default=True
)

페이지 = st.navigation(
    {
        "뇌졸중 예측 실습실": [
            홈페이지,
            탐색페이지
        ]
    },
    position="sidebar"
)

# 현재 페이지 실행
페이지.run()
