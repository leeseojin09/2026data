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

st.title("🌡️ 기온 예측기")
st.caption("서울의 연평균기온 데이터를 이용한 선형회귀 기반 기온 예측")

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

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 필요한 열 숫자형 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 결측값 제거
    df = df.dropna(subset=["날짜", "평균기온"])

    # 연도 생성
    df["연도"] = df["날짜"].dt.year

    return df


df = load_data()

# ---------------------------------------------------------
# 연도별 데이터 계산
# ---------------------------------------------------------

# 2025년까지의 데이터만 사용
df = df[df["연도"] <= 2025].copy()

# 연도별 관측일 수와 평균기온 계산
yearly = (
    df.groupby("연도")
    .agg(
        관측일수=("평균기온", "count"),
        연평균기온=("평균기온", "mean")
    )
    .reset_index()
)

# 관측일이 300일 미만인 연도 제거
yearly = yearly[yearly["관측일수"] >= 300].copy()

# 1908년 이후만 회귀분석에 사용
yearly = yearly[yearly["연도"] >= 1908].copy()

# 정렬
yearly = yearly.sort_values("연도").reset_index(drop=True)

# ---------------------------------------------------------
# 독립변수: 1908년부터 지난 연수
# ---------------------------------------------------------
yearly["지난연수"] = yearly["연도"] - 1908

# ---------------------------------------------------------
# 선형회귀 계산
# y = a*x + b
# ---------------------------------------------------------
x = yearly["지난연수"].to_numpy()
y = yearly["연평균기온"].to_numpy()

slope, intercept = np.polyfit(x, y, 1)

# 회귀선 예측값
yearly["회귀예측기온"] = slope * yearly["지난연수"] + intercept

# 상관계수
correlation = np.corrcoef(x, y)[0, 1]

# 결정계수
r_squared = correlation ** 2

# 회귀식
if intercept >= 0:
    equation = f"y = {slope:.4f}x + {intercept:.4f}"
else:
    equation = f"y = {slope:.4f}x - {abs(intercept):.4f}"

# ---------------------------------------------------------
# 화면 상단 정보
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "회귀에 사용한 연도 수",
        f"{len(yearly)}개"
    )

with col2:
    st.metric(
        "시작 연도",
        f"{yearly['연도'].min()}년"
    )

with col3:
    st.metric(
        "끝 연도",
        f"{yearly['연도'].max()}년"
    )

with col4:
    st.metric(
        "상관계수",
        f"{correlation:.4f}"
    )

# ---------------------------------------------------------
# 선택 연도
# ---------------------------------------------------------
st.subheader("🔎 연도별 예상 기온")

selected_year = st.slider(
    "예측할 연도를 선택하세요",
    min_value=1900,
    max_value=2100,
    value=2026,
    step=1
)

# 선택한 연도의 예측값
selected_x = selected_year - 1908
predicted_temp = slope * selected_x + intercept

st.metric(
    label=f"{selected_year}년 예상 연평균기온",
    value=f"{predicted_temp:.2f} °C"
)

st.caption(
    "※ 예상 기온은 1908년부터의 경과 연수를 독립변수로 한 "
    "선형회귀 결과입니다."
)

# ---------------------------------------------------------
# 그래프
# ---------------------------------------------------------
st.subheader("📈 연도별 평균기온과 회귀 직선")

fig = go.Figure()

# 실제 연평균기온 산점도
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

# 회귀 직선
fig.add_trace(
    go.Scatter(
        x=yearly["연도"],
        y=yearly["회귀예측기온"],
        mode="lines",
        name="회귀 직선",
        hovertemplate=(
            "연도: %{x}년<br>"
            "회귀 예측값: %{y:.2f} °C"
            "<extra></extra>"
        )
    )
)

# 선택한 연도의 예측 위치
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
# 회귀분석 결과
# ---------------------------------------------------------
st.subheader("📊 회귀분석 결과")

col1, col2 = st.columns(2)

with col1:
    st.write("**회귀식**")
    st.code(
        f"연평균기온 = {slope:.4f} × (연도 - 1908) + {intercept:.4f}"
    )

with col2:
    st.write("**결정계수 (R²)**")
    st.metric(
        "R²",
        f"{r_squared:.4f}"
    )

st.write(
    f"상관계수 r = **{correlation:.4f}**"
)

st.info(
    f"회귀분석에는 **{len(yearly)}개 연도**가 사용되었으며, "
    f"**{yearly['연도'].min()}년부터 {yearly['연도'].max()}년까지**의 "
    f"연평균기온을 사용했습니다."
)

# ---------------------------------------------------------
# 데이터 확인
# ---------------------------------------------------------
with st.expander("📋 회귀분석에 사용된 연도별 데이터 보기"):
    display_df = yearly[
        ["연도", "관측일수", "연평균기온", "지난연수", "회귀예측기온"]
    ].copy()

    display_df["연평균기온"] = display_df["연평균기온"].round(2)
    display_df["회귀예측기온"] = display_df["회귀예측기온"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
