import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 1 - 시간")
st.write("1년간 영화의 일별 관객 변화를 시간의 흐름에 따라 살펴봅니다.")

# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜: YYYYMMDD → 실제 날짜 형식
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d"
    )

    # 숫자형으로 변환
    numeric_columns = [
        "순위",
        "영화코드",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.stop()


# ---------------------------------------------------------
# 데이터 정보
# ---------------------------------------------------------
st.info(
    f"📊 전체 데이터: {len(df):,}개 기록 | "
    f"기간: {df['날짜'].min().strftime('%Y-%m-%d')} ~ "
    f"{df['날짜'].max().strftime('%Y-%m-%d')}"
)


# =========================================================
# 그래프 1. 날짜에 따른 일관객 변화
# =========================================================
st.divider()
st.header("📈 그래프 1. 영화별 일관객 변화")
st.write("시간이 지나면서 특정 영화의 하루 관객 수가 어떻게 변했는지 확인합니다.")

# 영화 목록
movie_list = sorted(df["영화명"].dropna().unique())

selected_movie = st.selectbox(
    "🎬 영화를 선택하세요",
    movie_list
)

# 선택한 영화 데이터
movie_df = df[df["영화명"] == selected_movie].copy()

# 같은 영화가 같은 날짜에 여러 번 기록될 가능성을 고려
movie_df = (
    movie_df
    .groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)

# Plotly 선 그래프
fig = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"「{selected_movie}」 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수"
    }
)

# 마우스를 올렸을 때 날짜 + 관객수 표시
fig.update_traces(
    hovertemplate=
    "날짜: %{x|%Y-%m-%d}<br>"
    "일관객: %{y:,.0f}명"
    "<extra></extra>"
)

fig.update_layout(
    hovermode="x unified",
    height=500,
    xaxis=dict(
        title="날짜",
        tickformat="%Y-%m-%d"
    ),
    yaxis=dict(
        title="일관객 수(명)",
        tickformat=","
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# 그래프 해석 문구
st.markdown("### 💡 이 그래프로 알 수 있는 것")
st.write(
    f"「{selected_movie}」의 날짜별 일관객 변화를 통해 "
    "시간에 따라 영화의 관객 수가 증가하거나 감소하는 흐름을 확인할 수 있습니다."
)


# =========================================================
# 앞으로 추가할 그래프 공간
# =========================================================

st.divider()
st.header("📊 그래프 2. 앞으로 추가할 그래프")
st.info("여기에 두 번째 그래프를 추가할 수 있습니다.")

# ---------------------------------------------------------
# 그래프 2 자리
# ---------------------------------------------------------
# 여기에 새로운 그래프 코드를 작성하세요.


st.divider()
st.header("📊 그래프 3. 앞으로 추가할 그래프")
st.info("여기에 세 번째 그래프를 추가할 수 있습니다.")

# ---------------------------------------------------------
# 그래프 3 자리
# ---------------------------------------------------------
# 여기에 새로운 그래프 코드를 작성하세요.


st.divider()
st.header("📊 그래프 4. 앞으로 추가할 그래프")
st.info("여기에 네 번째 그래프를 추가할 수 있습니다.")

# ---------------------------------------------------------
# 그래프 4 자리
# ---------------------------------------------------------
# 여기에 새로운 그래프 코드를 작성하세요.
