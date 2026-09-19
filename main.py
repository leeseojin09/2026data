import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울 기온 예측기")
st.caption("서울 연평균기온의 장기 변화와 최근 20년 변화 비교")

# ---------------------------------------------------------
# 데이터 주소
# ---------------------------------------------------------
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"
)

# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8-sig")

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    df = df.dropna(subset=["날짜", "평균기온"])

    df["연도"] = df["날짜"].dt.year

    return df


df = load_data()

# ---------------------------------------------------------
# 2025년까지의 데이터만 사용
# ---------------------------------------------------------
df = df[df["연도"] <= 2025].copy()

# ---------------------------------------------------------
# 연도별 평균기온 및 관측일수 계산
# ---------------------------------------------------------
yearly = (
    df.groupby("연도")
    .agg(
        관측일수=("평균기온", "count"),
        연평균기온=("평균기온", "mean")
    )
    .reset_index()
)

# 관측일이 300일 미만인 해 제거
yearly = yearly[yearly["관측일수"] >= 300].copy()

# 1908년 이후만 사용
yearly = yearly[yearly["연도"] >= 1908].copy()

yearly = yearly.sort_values("연도").reset_index(drop=True)

# ---------------------------------------------------------
# 전체 기간 회귀분석
# 독립변수 = 1908년부터 지난 연수
# ---------------------------------------------------------
yearly["지난연수"] = yearly["연도"] - 1908

x_all = yearly["지난연수"].to_numpy()
y_all = yearly["연평균기온"].to_numpy()

slope_all, intercept_all = np.polyfit(x_all, y_all, 1)

# 1년에 몇 도 변화하는지
annual_slope_all = slope_all

# 100년에 몇 도 변화하는지
hundred_year_slope_all = slope_all * 100

# 상관계수
correlation_all = np.corrcoef(x_all, y_all)[0, 1]

# 결정계수
r_squared_all = correlation_all ** 2

# 전체 회귀선
yearly["전체회귀예측"] = (
    slope_all * yearly["지난연수"] + intercept_all
)

# ---------------------------------------------------------
# 최근 20년 데이터
# 2006년 ~ 2025년
# ---------------------------------------------------------
recent_start = 2025 - 19
recent_end = 2025

recent = yearly[
    (yearly["연도"] >= recent_start) &
    (yearly["연도"] <= recent_end)
].copy()

# 최근 20년 회귀분석
# 연도 자체를 x로 사용
x_recent = recent["연도"].to_numpy()
y_recent = recent["연평균기온"].to_numpy()

slope_recent, intercept_recent = np.polyfit(
    x_recent,
    y_recent,
    1
)

# 100년에 몇 도 변화하는지
hundred_year_slope_recent = slope_recent * 100

# 최근 20년 상관계수
correlation_recent = np.corrcoef(
    x_recent,
    y_recent
)[0, 1]

r_squared_recent = correlation_recent ** 2

# 최근 20년 회귀선
recent["최근20년회귀예측"] = (
    slope_recent * recent["연도"] + intercept_recent
)

# ---------------------------------------------------------
# 상단 기본 정보
# ---------------------------------------------------------
st.subheader("📊 기온 상승 속도")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "전체 기간",
        f"{hundred_year_slope_all:+.2f} °C / 100년"
    )
    st.caption(
        f"{yearly['연도'].min()}~{yearly['연도'].max()}년"
    )

with col2:
    st.metric(
        "최근 20년",
        f"{hundred_year_slope_recent:+.2f} °C / 100년"
    )
    st.caption(
        f"{recent_start}~{recent_end}년"
    )

# ---------------------------------------------------------
# 비교 설명
# ---------------------------------------------------------
st.info(
    "기울기는 '1년 동안 몇 °C 변하는가'를 100배하여 "
    "'100년에 몇 °C 변하는가'로 나타낸 값입니다."
)

# ---------------------------------------------------------
# 회귀분석 상세 비교
# ---------------------------------------------------------
st.subheader("🔎 회귀분석 비교")

comparison = pd.DataFrame({
    "구분": [
        "전체 기간",
        "최근 20년"
    ],
    "기간": [
        f"{yearly['연도'].min()}~{yearly['연도'].max()}",
        f"{recent_start}~{recent_end}"
    ],
    "사용 연도 수": [
        len(yearly),
        len(recent)
    ],
    "100년당 변화": [
        f"{hundred_year_slope_all:+.2f} °C",
        f"{hundred_year_slope_recent:+.2f} °C"
    ],
    "상관계수": [
        f"{correlation_all:.4f}",
        f"{correlation_recent:.4f}"
    ],
    "결정계수 R²": [
        f"{r_squared_all:.4f}",
        f"{r_squared_recent:.4f}"
    ]
})

st.dataframe(
    comparison,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------------
# 연도 선택
# ---------------------------------------------------------
st.subheader("🔮 연도별 예상 기온")

selected_year = st.slider(
    "예측할 연도를 선택하세요",
    min_value=1900,
    max_value=2100,
    value=2026,
    step=1
)

# 전체 기간 회귀식으로 예측
selected_x = selected_year - 1908

predicted_temp = (
    slope_all * selected_x + intercept_all
)

st.metric(
    label=f"{selected_year}년 예상 연평균기온",
    value=f"{predicted_temp:.2f} °C"
)

st.caption(
    "※ 2026년 이후의 값은 실제 관측값이 아니라 "
    "전체 기간 회귀식을 미래로 연장한 예측값입니다."
)

# ---------------------------------------------------------
# 그래프
# ---------------------------------------------------------
st.subheader("📈 연평균기온과 회귀선")

fig = go.Figure()

# 실제 연평균기온
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["연평균기온"],
        mode="markers",
        name="실제 연평균기온",
        text=yearly["연도"].astype(str) + "년",
        customdata=yearly["관측일수"],
        hovertemplate=(
            "<b>%{text}</b><br>"
            "연평균기온: %{y:.2f} °C<br>"
            "관측일수: %{customdata}일"
            "<extra></extra>"
        ),
        marker=dict(size=7)
    )
)

# 전체 기간 회귀선
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["전체회귀예측"],
        mode="lines",
        name="전체 기간 회귀선",
        hovertemplate=(
            "연도: %{x}년<br>"
            "회귀값: %{y:.2f} °C"
            "<extra></extra>"
        )
    )
)

# 최근 20년 회귀선
fig.add_trace(
    go.Scatter(
        x=recent["연도"],
        y=recent["최근20년회귀예측"],
        mode="lines",
        name="최근 20년 회귀선",
        hovertemplate=(
            "연도: %{x}년<br>"
            "회귀값: %{y:.2f} °C"
            "<extra></extra>"
        )
    )
)

# 선택한 연도의 예측값
fig.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name=f"{selected_year}년 예측",
        marker=dict(
            size=15,
            symbol="star"
        ),
        hovertemplate=(
            f"<b>{selected_year}년</b><br>"
            f"예상 연평균기온: {predicted_temp:.2f} °C"
            "<extra></extra>"
        )
    )
)

fig.update_layout(
    xaxis_title="연도",
    yaxis_title="연평균기온 (°C)",
    xaxis=dict(
        dtick=10,
        tickformat="d"
    ),
    hovermode="x unified",
    height=600,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0
    )
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ---------------------------------------------------------
# 회귀식
# ---------------------------------------------------------
st.subheader("📐 회귀식")

col1, col2 = st.columns(2)

with col1:
    st.write("**전체 기간 회귀식**")
    st.code(
        f"연평균기온 = {slope_all:.4f} × (연도 - 1908) "
        f"+ {intercept_all:.4f}"
    )
    st.write(
        f"→ 100년당 **{hundred_year_slope_all:+.2f} °C**"
    )

with col2:
    st.write("**최근 20년 회귀식**")
    st.code(
        f"연평균기온 = {slope_recent:.4f} × 연도 "
        f"+ {intercept_recent:.4f}"
    )
    st.write(
        f"→ 100년당 **{hundred_year_slope_recent:+.2f} °C**"
    )

# ---------------------------------------------------------
# 사용 데이터
# ---------------------------------------------------------
with st.expander("📋 회귀분석에 사용된 연도별 데이터"):
    display_df = yearly[
        [
            "연도",
            "관측일수",
            "연평균기온",
            "지난연수",
            "전체회귀예측"
        ]
    ].copy()

    display_df["연평균기온"] = (
        display_df["연평균기온"].round(2)
    )

    display_df["전체회귀예측"] = (
        display_df["전체회귀예측"].round(2)
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True

