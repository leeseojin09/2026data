import pandas as pd
import plotly.express as px
import streamlit as st

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(
    page_title="서울 일별 평균기온 분포",
    page_icon="🌡️",
    layout="wide",
)

st.title("서울의 일별 평균기온 분포")
st.write("100년간 서울의 일별 평균기온이 어느 온도 구간에 얼마나 몰려 있는지 보여줍니다.")


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"])

    return df


try:
    df = load_data()

    min_year = df["날짜"].dt.year.min()
    max_year = df["날짜"].dt.year.max()

    fig = px.histogram(
        df,
        x="평균기온",
        nbins=40,
        labels={
            "평균기온": "평균기온 (℃)",
            "count": "일수",
        },
        title=f"{min_year}년~{max_year}년 서울 일별 평균기온 분포",
    )

    fig.update_layout(
        xaxis_title="평균기온 (℃)",
        yaxis_title="일수",
        bargap=0.05,
        height=550,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "※ 가로축은 일별 평균기온 구간, 세로축은 해당 구간에 포함되는 날짜의 수입니다."
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "분석 기간",
            f"{min_year}~{max_year}년",
        )

    with col2:
        st.metric(
            "평균기온 평균",
            f"{df['평균기온'].mean():.1f} ℃",
        )

    with col3:
        st.metric(
            "전체 관측 일수",
            f"{len(df):,}일",
        )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.exception(e)
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="서울 최저·최고기온 관계",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울의 최저기온과 최고기온 관계")
st.write("각 날짜의 최저기온과 최고기온이 어떤 관계를 가지는지 산점도로 나타냅니다.")

# 데이터 불러오기
url = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

df = pd.read_csv(url, encoding="utf-8")

# 열 이름 지정
df.columns = ["날짜", "지점", "평균기온", "최저기온", "최고기온"]

# 기온을 숫자로 변환
df["최저기온"] = pd.to_numeric(df["최저기온"], errors="coerce")
df["최고기온"] = pd.to_numeric(df["최고기온"], errors="coerce")

# 결측값 제거
scatter_df = df.dropna(subset=["최저기온", "최고기온"])

# 산점도
st.subheader("최저기온과 최고기온의 관계")

st.scatter_chart(
    scatter_df,
    x="최저기온",
    y="최고기온",
    x_label="최저기온 (℃)",
    y_label="최고기온 (℃)"
)

st.write(
    f"총 {len(scatter_df):,}일의 기온 데이터를 이용했습니다."
)
