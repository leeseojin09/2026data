import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
# 상위 5편의 날짜별 데이터
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
# 그래프 2 해석
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
st.header("📉 그래프 3. 날짜별 10위권 일관객 합계")
st.write(
    "매일 박스오피스 10위권에 오른 영화들의 일관객을 모두 합산하여 "
    "전체적인 영화 관람 규모가 시간에 따라 어떻게 변했는지 확인합니다."
)


# ---------------------------------------------------------
# 날짜별 10위권 일관객 합계
# ---------------------------------------------------------
daily_top10 = (
    df.groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)


# ---------------------------------------------------------
# 일관객 합계가 가장 큰 3일
# ---------------------------------------------------------
top3_days = (
    daily_top10
    .nlargest(3, "일관객")
    .sort_values("날짜")
)


# ---------------------------------------------------------
# 영역 그래프
# ---------------------------------------------------------
fig3 = go.Figure()

fig3.add_trace(
    go.Scatter(
        x=daily_top10["날짜"],
        y=daily_top10["일관객"],
        mode="lines",
        fill="tozeroy",
        name="10위권 일관객 합계",
        hovertemplate=
        "날짜: %{x|%Y-%m-%d}<br>"
        "10위권 일관객 합계: %{y:,.0f}명"
        "<extra></extra>"
    )
)


# ---------------------------------------------------------
# 가장 큰 3일 표시
# ---------------------------------------------------------
fig3.add_trace(
    go.Scatter(
        x=top3_days["날짜"],
        y=top3_days["일관객"],
        mode="markers+text",
        name="일관객 합계 TOP 3",
        text=[
            f"{date.strftime('%Y-%m-%d')}"
            for date in top3_days["날짜"]
        ],
        textposition="top center",
        marker=dict(
            size=12,
            symbol="circle"
        ),
        hovertemplate=
        "날짜: %{x|%Y-%m-%d}<br>"
        "10위권 일관객 합계: %{y:,.0f}명"
        "<extra></extra>"
    )
)


fig3.update_layout(
    title="날짜별 박스오피스 10위권 일관객 합계",
    height=600,
    hovermode="x unified",
    xaxis_title="날짜",
    yaxis_title="10위권 일관객 합계(명)",
    yaxis_tickformat=",",
    showlegend=True
)


st.plotly_chart(
    fig3,
    use_container_width=True
)


# ---------------------------------------------------------
# TOP 3 날짜 정보
# ---------------------------------------------------------
st.markdown("### 🏆 일관객 합계가 가장 컸던 날 TOP 3")

for i, row in enumerate(
    top3_days.sort_values(
        "일관객",
        ascending=False
    ).itertuples(),
    start=1
):
    st.write(
        f"**{i}위 — {row.날짜.strftime('%Y-%m-%d')}** "
        f": {row.일관객:,.0f}명"
    )


# ---------------------------------------------------------
# 그래프 3 해석
# ---------------------------------------------------------
st.markdown("### 💡 이 그래프로 알 수 있는 것")

st.write(
    "날짜별 10위권 일관객 합계를 비교하면 전체적인 영화 관람 규모가 "
    "어느 시기에 커지고 작아지는지와 관객이 가장 많이 몰린 날짜를 확인할 수 있습니다."
)


# =========================================================
# 그래프 4
# =========================================================
st.divider()
st.header("📊 그래프 4. 앞으로 추가할 그래프")
st.info("여기에 네 번째 그래프를 추가할 수 있습니다.")
# =========================================================
# 그래프 4
# =========================================================
st.divider()
st.header("🏆 그래프 4. 영화별 누적 일관객 TOP 10")
st.write(
    "전체 기간 동안 일관객의 합계가 가장 큰 영화 10편을 비교합니다. "
    "막대에 마우스를 올리면 10위권에 든 날수도 확인할 수 있습니다."
)


# ---------------------------------------------------------
# 영화별 일관객 합계 + 10위권 기록 일수 계산
# ---------------------------------------------------------
movie_summary = (
    df.groupby("영화명")
    .agg(
        일관객합계=("일관객", "sum"),
        **{"10위권_기록_일수": ("날짜", "nunique")}
    )
    .reset_index()
)


# ---------------------------------------------------------
# 일관객 합계 기준 TOP 10
# ---------------------------------------------------------
top10_movies = (
    movie_summary
    .sort_values("일관객합계", ascending=False)
    .head(10)
    .sort_values("일관객합계", ascending=True)
)


# ---------------------------------------------------------
# 가로 막대그래프
# ---------------------------------------------------------
fig4 = px.bar(
    top10_movies,
    x="일관객합계",
    y="영화명",
    orientation="h",
    text="일관객합계",
    title="기간 내 일관객 합계 TOP 10",
    labels={
        "일관객합계": "기간 내 일관객 합계(명)",
        "영화명": "영화"
    }
)


# 막대 위 숫자 표시
fig4.update_traces(
    texttemplate="%{text:,.0f}명",
    textposition="outside",

    # 마우스를 올렸을 때 표시되는 정보
    customdata=top10_movies[
        ["10위권_기록_일수"]
    ].values,

    hovertemplate=
    "영화: %{y}<br>"
    "기간 내 일관객 합계: %{x:,.0f}명<br>"
    "10위권에 든 날: %{customdata[0]}일"
    "<extra></extra>"
)


fig4.update_layout(
    height=600,
    xaxis_title="기간 내 일관객 합계(명)",
    yaxis_title="영화",
    xaxis_tickformat=",",
    yaxis=dict(
        categoryorder="total ascending"
    )
)


st.plotly_chart(
    fig4,
    use_container_width=True
)


# ---------------------------------------------------------
# TOP 10 표
# ---------------------------------------------------------
st.markdown("### 📋 TOP 10 영화 정보")

top10_table = (
    movie_summary
    .sort_values("일관객합계", ascending=False)
    .head(10)
    .copy()
)

top10_table.columns = [
    "영화명",
    "기간 내 일관객 합계",
    "10위권에 든 날"
]

top10_table["기간 내 일관객 합계"] = (
    top10_table["기간 내 일관객 합계"]
    .map(lambda x: f"{x:,.0f}명")
)

top10_table["10위권에 든 날"] = (
    top10_table["10위권에 든 날"]
    .map(lambda x: f"{x}일")
)

st.dataframe(
    top10_table,
    hide_index=True,
    use_container_width=True
)


# ---------------------------------------------------------
# 그래프 4 해석
# ---------------------------------------------------------
st.markdown("### 💡 이 그래프로 알 수 있는 것")

st.write(
    "기간 내 일관객 합계가 높은 영화를 비교하면 어떤 영화가 전체적으로 "
    "많은 관객을 모았는지 알 수 있으며, 10위권에 든 날수와 함께 보면 "
    "오랫동안 꾸준히 흥행한 영화와 짧은 기간에 많은 관객을 모은 영화를 비교할 수 있습니다."
)
# =========================================================
# 그래프 5
# =========================================================
st.divider()
st.header("🗓️ 그래프 5. 월 × 요일별 일관객 히트맵")
st.write(
    "월과 요일에 따라 박스오피스 10위권의 일관객 합계가 "
    "어떻게 달라지는지 확인합니다."
)


# ---------------------------------------------------------
# 월과 요일 추출
# ---------------------------------------------------------
heatmap_df = df.copy()

heatmap_df["월"] = heatmap_df["날짜"].dt.month

# weekday(): 월요일=0, 일요일=6
weekday_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일"
]

heatmap_df["요일"] = heatmap_df["날짜"].dt.weekday.map(
    lambda x: weekday_order[x]
)


# ---------------------------------------------------------
# 월 × 요일별 일관객 합계
# ---------------------------------------------------------
heatmap_data = (
    heatmap_df
    .groupby(["월", "요일"])["일관객"]
    .sum()
    .reset_index()
)


# ---------------------------------------------------------
# 피벗 테이블 생성
# ---------------------------------------------------------
heatmap_pivot = (
    heatmap_data
    .pivot(
        index="월",
        columns="요일",
        values="일관객"
    )
    .reindex(columns=weekday_order)
    .fillna(0)
)


# ---------------------------------------------------------
# 히트맵
# ---------------------------------------------------------
fig5 = px.imshow(
    heatmap_pivot,
    labels={
        "x": "요일",
        "y": "월",
        "color": "일관객 합계"
    },
    x=weekday_order,
    y=[f"{month}월" for month in heatmap_pivot.index],
    text_auto=".2s",
    aspect="auto",
    title="월 × 요일별 박스오피스 10위권 일관객 합계"
)


# 마우스를 올렸을 때 표시
fig5.update_traces(
    hovertemplate=
    "%{y} %{x}<br>"
    "일관객 합계: %{z:,.0f}명"
    "<extra></extra>"
)


fig5.update_layout(
    height=650,
    xaxis_title="요일",
    yaxis_title="월"
)


st.plotly_chart(
    fig5,
    use_container_width=True
)


# ---------------------------------------------------------
# 그래프 5 해석
# ---------------------------------------------------------
st.markdown("### 💡 이 그래프로 알 수 있는 것")

st.write(
    "월과 요일별 일관객 합계를 비교하면 어느 시기의 어떤 요일에 "
    "영화 관객이 많이 몰리는지 한눈에 확인할 수 있습니다."
)



