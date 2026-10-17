
# main.py — 뇌졸중 예측 실습실

import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------------------------
# 네비게이션 페이지 등록
# --------------------------------------------------

홈페이지 = st.Page(
    "main.py",
    title="뇌졸중 예측 실습실",
    icon="🩺",
    default=True
)

탐색페이지 = st.Page(
    "pages/1_탐색.py",
    title="데이터 탐색",
    icon="🔎"
)

분류페이지 = st.Page(
    "pages/2_분류_모델.py",
    title="분류 모델",
    icon="🧠"
)

채점페이지 = st.Page(
    "pages/3_채점표.py",
    title="모델 채점표",
    icon="📊"
)

전처리페이지 = st.Page(
    "pages/4_전처리.py",
    title="데이터 전처리",
    icon="🧹"
)

소개페이지 = st.Page(
    "pages/5_내가_만든_모델_소개.py",
    title="내가 만든 모델 소개",
    icon="📝"
)

페이지 = st.navigation(
    {
        "🩺 뇌졸중 예측 실습실": [
            홈페이지,
            탐색페이지,
            분류페이지,
            채점페이지,
            전처리페이지,
            소개페이지,
        ]
    },
    position="sidebar"
)

st.sidebar.caption("뇌졸중 데이터를 활용한 머신러닝 실습")

# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------

데이터주소 = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)


@st.cache_data
def 데이터_읽기():
    """UTF-8로 저장된 CSV 파일을 읽습니다."""
    return pd.read_csv(데이터주소, encoding="utf-8")


# --------------------------------------------------
# 홈 화면
# --------------------------------------------------

if 페이지 == 홈페이지:

    st.title("🩺 뇌졸중 예측 실습실")

    st.write(
        "건강 기록 데이터를 살펴보고, 모델을 만들고, "
        "평가 결과를 비교하는 실습 공간입니다. "
        "왼쪽 메뉴에서 원하는 페이지를 선택하세요."
    )

    try:
        df = 데이터_읽기()

        st.subheader("한눈에 보기")

        칸1, 칸2, 칸3, 칸4 = st.columns(4)

        칸1.metric("전체 사람 수", f"{len(df):,}명")
        칸2.metric("열 개수", f"{df.shape[1]}개")

        if "stroke" in df.columns:
            뇌졸중수 = int(df["stroke"].fillna(0).sum())
            비율 = df["stroke"].mean() * 100

            칸3.metric("뇌졸중을 겪은 사람", f"{뇌졸중수:,}명")
            칸4.metric("그 비율", f"{비율:.2f}%")
        else:
            칸3.metric("뇌졸중 변수", "없음")
            칸4.metric("그 비율", "계산 불가")

        # ------------------------------------------
        # 열 설명표
        # ------------------------------------------

        st.subheader("열마다 무엇이 들어 있는가")

        st.caption(
            "우리말 뜻 칸을 직접 채워 보세요. "
            "입력 내용은 이 화면에서 사용하는 세션에 유지되며, "
            "별도로 파일에 저장되지는 않습니다."
        )

        def 값의_종류(열):
            """숫자 열은 범위를, 문자 열은 값의 종류를 표시합니다."""
            칸 = df[열].dropna()

            if 칸.empty:
                return "값 없음"

            if (
                pd.api.types.is_numeric_dtype(칸)
                and 칸.nunique() > 2
            ):
                return f"숫자 {칸.min():g} ~ {칸.max():g}"

            값들 = sorted(칸.astype(str).unique())
            return f"{len(값들)}가지 · " + " · ".join(값들[:10])

        열설명 = pd.DataFrame({
            "열 이름": df.columns,
            "우리말 뜻": [""] * df.shape[1],
            "값의 종류": [값의_종류(열) for 열 in df.columns],
            "빈 값 개수": [
                int(df[열].isna().sum())
                for 열 in df.columns
            ],
        })

        st.data_editor(
            열설명,
            width="stretch",
            hide_index=True,
            disabled=[
                "열 이름",
                "값의 종류",
                "빈 값 개수"
            ],
            key="열설명표",
        )

        # ------------------------------------------
        # 데이터 미리 보기
        # ------------------------------------------

        st.subheader("앞 다섯 줄 그대로 보기")

        st.dataframe(
            df.head(5),
            width="stretch",
            hide_index=True
        )

        # ------------------------------------------
        # 출처
        # ------------------------------------------

        st.subheader("이 데이터는 어디서 왔는가")

        출처_기본값 = """출처: Kaggle Stroke Prediction Dataset
게시자: fedesoriano
원본 주소: https://www.kaggle.com/datasets/fedesoriano/stroke-prediction-dataset

원본 데이터의 출처와 이용 조건을 별도로 확인해야 합니다.
교육 목적의 분석 결과를 실제 의료 판단에 사용해서는 안 됩니다."""

        st.text_area(
            "데이터 출처와 참고 사항",
            value=출처_기본값,
            height=170,
            key="출처"
        )

        st.warning(
            "이 데이터는 교육용 분석 자료입니다. "
            "모델의 예측 결과만으로 실제 환자의 뇌졸중 여부를 "
            "판단하거나 의료 결정을 내려서는 안 됩니다."
        )

        # ------------------------------------------
        # 실습 순서
        # ------------------------------------------

        st.divider()
        st.subheader("📚 실습 순서")

        st.markdown("""
        1. **데이터 탐색** — 데이터의 열과 값 확인하기
        2. **분류 모델** — 선택한 속성을 사용해 모델 만들기
        3. **모델 채점표** — 예측 성능 평가하기
        4. **데이터 전처리** — 수정 전후 결과 비교하기
        5. **내가 만든 모델 소개** — 결과와 한계 정리하기
        """)

    except Exception as 오류:
        st.error(
            "데이터를 불러오는 중 문제가 발생했습니다. "
            "인터넷 연결과 CSV 주소를 확인해 주세요."
        )
        st.caption(f"오류 내용: {오류}")

# --------------------------------------------------
# 선택된 페이지 실행
# --------------------------------------------------

페이지.run()
