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

    # 날짜를 실제 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d"
    )

    # 숫자형 데이터 변환
    numeric_columns = [
        "순위",
        "영화코드",
        "일관객",
        "누적관객",
        "스크린수",
        "상영횟수"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    return df


try:
    df = load_data()

except Exception:
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
# 그래프 1
# =========================================================
st.divider()
st.header("📈 그래프 1. 영화별 일관객 변화")
st.write(
    "영화를 선택하면 시간에 따른 해당 영화의 일관객 변화를 확인할 수 있습니다."
)

movie_list = sorted(
    df["영화명"].dropna().unique()
)

selected_movie = st.selectbox(
    "🎬 영화를 선택하세요",
    movie_list
)

movie_df = df[
    df["영화명"] == selected_movie
].copy()

movie_df = (
    movie_df
    .groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)

fig1 = px.line(
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

fig1.update_traces(
    hovertemplate=
    "날짜: %{x|%Y-%m-%d}<br>"
    "일관객: %{y:,.0f}명"
    "<extra></extra>"
)

fig1.update_layout(
    hovermode="x unified",
    height=500,
    xaxis_title="날짜",
    yaxis_title="일관객 수(명)",
    yaxis_tickformat=","
)

st.plotly_chart(
    fig1,
    use_container_width=True
)

st.markdown("### 💡 이 그래프로 알 수 있는 것")

st.write(
    f"「{selected_movie}」의 일관객 변화를 통해 "
    "시간이 지남에 따라 영화의 관객 수가 어떻게 증가하거나 감소했는지 확인할 수 있습니다."
)


# =========================================================
# 그래프 2
# =========================================================
st.divider()
st.header("📊 그래프 2. 일관객 합계 상위 5편의 변화")
st.write(
    "전체 기간 동안 일관객 합계가 가장 큰 5편을 선정하여 "
    "날짜별 관객 변화를 비교합니다."
)


# ---------------------------------------------------------
# 전체 기간 일관객 합계 계산
# ---------------------------------------------------------
top5_movies = (
    df.groupby("영화명")["일관객"]
    .sum()
    .sort_values(ascending=False)
    .head(5)
)


# ---------------------------------------------------------
# 상위 5편의 날짜별 데이터 만들기
# ---------------------------------------------------------
top5_df = df[
    df["영화명"].isin(top5_movies.index)
].copy()

top5_df = (
    top5_df
    .groupby(
        ["날짜", "영화명"],
        as_index=False
    )["일관객"]
    .sum()
    .sort_values("날짜")
)


# ---------------------------------------------------------
# 상위 5편 선 그래프
# ---------------------------------------------------------
fig2 = px.line(
    top5_df,
    x="날짜",
    y="일관객",
    color="영화명",
    markers=True,
    title="일관객 합계 상위 5편의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수",
        "영화명": "영화"
    }
)


# 마우스를 올렸을 때 날짜와 관객수 표시
fig2.update_traces(
    hovertemplate=
    "영화: %{fullData.name}<br>"
    "날짜: %{x|%Y-%m-%d}<br>"
    "일관객: %{y:,.0f}명"
    "<extra></extra>"
)


fig2.update_layout(
    height=600,
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="일관객 수(명)",
    yaxis_tickformat=",",
    legend_title="영화",
    legend=dict(
        itemclick="toggle",
        itemdoubleclick="toggleothers"
    )
)


st.plotly_chart(
    fig2,
    use_container_width=True
)


# ---------------------------------------------------------
# 상위 5편 정보
# ---------------------------------------------------------
st.markdown("### 🏆 일관객 합계 상위 5편")

top5_display = top5_movies.reset_index()
top5_display.columns = ["영화명", "기간 내 일관객 합계"]

top5_display["기간 내 일관객 합계"] = (
    top5_display["기간 내 일관객 합계"]
    .map(lambda x: f"{x:,.0f}명")
)

st.dataframe(
    top5_display,
    hide_index=True,
    use_container_width=True
)


# ---------------------------------------------------------
# 그래프 해석 문구
# ---------------------------------------------------------
st.markdown("### 💡 이 그래프로 알 수 있는 것")

st.write(
    "전체 기간의 일관객 합계를 기준으로 관객이 많이 찾은 상위 5편의 "
    "날짜별 관객 변화를 비교하면 영화마다 흥행이 진행되는 시기와 "
    "관객 수의 변화 양상이 서로 다를 수 있음을 확인할 수 있습니다."
)


# =========================================================
# 그래프 3
# =========================================================
st.divider()
st.header("📊 그래프 3. 앞으로 추가할 그래프")
st.info("여기에 세 번째 그래프를 추가할 수 있습니다.")


# =========================================================
# 그래프 4
# =========================================================
st.divider()
st.header("📊 그래프 4. 앞으로 추가할 그래프")
st.info("여기에 네 번째 그래프를 추가할 수 있습니다.")
