
# main.py — 뇌졸중 예측 실습실

import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

데이터주소 = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)


@st.cache_data
def 데이터_읽기():
    return pd.read_csv(데이터주소, encoding="utf-8")


# --------------------------------------------------
# 홈 페이지
# --------------------------------------------------

def 홈화면():
    st.title("🩺 뇌졸중 예측 실습실")

    st.write(
        "건강 기록 데이터를 살펴보고, 분류 모델을 만들고, "
        "채점하고, 전처리 결과를 비교하는 실습 공간입니다."
    )

    try:
        df = 데이터_읽기()

        st.subheader("한눈에 보기")

        칸1, 칸2, 칸3, 칸4 = st.columns(4)

        칸1.metric("전체 사람 수", f"{len(df):,}명")
        칸2.metric("열 개수", f"{df.shape[1]}개")

        if "stroke" in df.columns:
            칸3.metric(
                "뇌졸중을 겪은 사람",
                f"{int(df['stroke'].fillna(0).sum()):,}명",
            )
            칸4.metric(
                "그 비율",
                f"{df['stroke'].mean() * 100:.2f}%",
            )

        st.subheader("열마다 무엇이 들어 있는가")

        def 값의_종류(열):
            값 = df[열].dropna()

            if 값.empty:
                return "값 없음"

            if (
                pd.api.types.is_numeric_dtype(값)
                and 값.nunique() > 2
            ):
                return f"숫자 {값.min():g} ~ {값.max():g}"

            종류 = sorted(값.astype(str).unique())
            return f"{len(종류)}가지 · " + " · ".join(종류[:10])

        열설명 = pd.DataFrame({
            "열 이름": df.columns,
            "우리말 뜻": [""] * len(df.columns),
            "값의 종류": [
                값의_종류(열) for 열 in df.columns
            ],
            "빈 값 개수": [
                int(df[열].isna().sum()) for 열 in df.columns
            ],
        })

        st.data_editor(
            열설명,
            width="stretch",
            hide_index=True,
            disabled=["열 이름", "값의 종류", "빈 값 개수"],
            key="홈_열설명표",
        )

        st.subheader("앞 다섯 줄 그대로 보기")
        st.dataframe(df.head(5), width="stretch", hide_index=True)

        st.subheader("데이터 출처")

        st.text_area(
            "출처 및 참고 사항",
            value=(
                "Kaggle Stroke Prediction Dataset\n"
                "게시자: fedesoriano\n"
                "원본 주소: "
                "https://www.kaggle.com/datasets/fedesoriano/"
                "stroke-prediction-dataset\n\n"
                "교육용 데이터 분석에 사용합니다. "
                "실제 의료 판단에 모델의 결과만 사용해서는 안 됩니다."
            ),
            height=150,
            key="홈_출처",
        )

        st.warning(
            "이 앱은 교육용 실습입니다. "
            "예측 결과는 의료 진단을 대신할 수 없습니다."
        )

    except Exception as 오류:
        st.error("데이터를 불러오지 못했습니다.")
        st.caption(str(오류))


# --------------------------------------------------
# 페이지 1~5 등록
# --------------------------------------------------

홈페이지 = st.Page(
    홈화면,
    title="홈",
    icon="🩺",
    default=True,
)

페이지정보 = [
    (
        "pages/1_탐색.py",
        "1. 데이터 탐색",
        "🔎",
    ),
    (
        "pages/2_분류_모델.py",
        "2. 분류 모델",
        "🧠",
    ),
    (
        "pages/3_채점표.py",
        "3. 모델 채점표",
        "📊",
    ),
    (
        "pages/4_전처리.py",
        "4. 데이터 전처리",
        "🧹",
    ),
    (
        "pages/5_내가_만든_모델_소개.py",
        "5. 내가 만든 모델 소개",
        "📝",
    ),
]

등록페이지 = []

for 경로, 제목, 아이콘 in 페이지정보:
    if Path(경로).is_file():
        등록페이지.append(
            st.Page(
                경로,
                title=제목,
                icon=아이콘,
            )
        )
    else:
        # 파일이 아직 없으면 오류를 발생시키지 않고
        # 아래의 안내 페이지를 대신 등록합니다.
        def 안내화면(파일경로=경로, 페이지제목=제목):
            st.title(페이지제목)
            st.warning(
                f"아직 페이지 파일이 없습니다: {파일경로}"
            )
            st.write(
                "GitHub 저장소의 해당 경로에 파일을 추가하면 "
                "이 메뉴에서 해당 페이지를 열 수 있습니다."
            )

        등록페이지.append(
            st.Page(
                안내화면,
                title=제목,
                icon=아이콘,
            )
        )


# --------------------------------------------------
# 네비게이션 실행
# --------------------------------------------------

페이지 = st.navigation(
    {
        "🩺 뇌졸중 예측 실습실": [
            홈페이지,
            *등록페이지,
        ]
    },
    position="sidebar",
)

st.sidebar.caption("데이터 탐색부터 모델 소개까지")

페이지.run()
