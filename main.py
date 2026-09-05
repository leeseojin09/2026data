import pandas as pd
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(
    page_title="서울 연평균 기온 변화",
    page_icon="🌡️",
    layout="wide",
)

st.title("서울의 100년 연평균 기온 변화")
st.write("서울의 일별 기온 데이터를 연도별로 집계하여 연평균 기온의 변화를 보여줍니다.")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온을 숫자로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 날짜와 평균기온이 정상적인 데이터만 사용
    df = df.dropna(subset=["날짜", "평균기온"])

    return df


try:
    df = load_data()

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 연도별 평균기온 계산
    yearly_temp = (
        df.groupby("연도", as_index=False)["평균기온"]
        .mean()
        .rename(columns={"평균기온": "연평균 기온"})
        .sort_values("연도")
    )

    # 분석 기간
    min_year = int(yearly_temp["연도"].min())
    max_year = int(yearly_temp["연도"].max())

    st.subheader(f"{min_year}년~{max_year}년 서울 연평균 기온")

    st.line_chart(
        yearly_temp,
        x="연도",
        y="연평균 기온",
        x_label="연도",
        y_label="기온 (℃)",
        height=500,
    )

    # 요약 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "분석 기간",
            f"{min_year}~{max_year}년",
        )

    with col2:
        st.metric(
            "가장 낮은 연평균 기온",
            f"{yearly_temp['연평균 기온'].min():.1f} ℃",
        )

    with col3:
        st.metric(
            "가장 높은 연평균 기온",
            f"{yearly_temp['연평균 기온'].max():.1f} ℃",
        )

    st.caption(
        "※ 연평균 기온은 해당 연도의 일별 평균기온을 평균하여 계산했습니다."
    )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
