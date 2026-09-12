import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감 2 - 분포와 관계")
st.markdown("1년간 박스오피스 10위권에 든 영화 가운데 해당 기간에 개봉한 216편의 데이터를 살펴봅니다.")

# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 개봉일: 여덟 자리 숫자 → 날짜
    df["openDt"] = pd.to_datetime(
        df["openDt"].astype(str).str.replace(r"\.0$", "", regex=True),
        format="%Y%m%d",
        errors="coerce"
    )

    # 여러 장르가 세로막대(|)로 연결된 경우 첫 번째 장르만 사용
    df["genre_first"] = (
        df["genre"]
        .fillna("미상")
        .astype(str)
        .str.split("|")
        .str[0]
        .str.strip()
    )

    return df

try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.exception(e)
    st.stop()

# ---------------------------------------------------------
# 데이터 요약
# ---------------------------------------------------------
st.subheader("📋 데이터 요약")

col1, col2, col3 = st.columns(3)
col1.metric("영화 수", f"{len(df):,}편")
col2.metric("장르 수", f"{df['genre_first'].nunique():,}개")
col3.metric("평균 총 관객", f"{df['total_audi'].mean():,.0f}명")

st.divider()

# ---------------------------------------------------------
# 첫 번째 그래프: 장르별 영화 편수 도넛 그래프
# ---------------------------------------------------------
st.subheader("① 장르별 영화 편수")

genre_counts = (
    df["genre_first"]
    .value_counts()
    .rename_axis("장르")
    .reset_index(name="영화 편수")
)

fig = px.pie(
    genre_counts,
    names="장르",
    values="영화 편수",
    hole=0.48,
    title="장르별 영화 편수 분포",
    hover_data={"영화 편수": True}
)

# 마우스를 올렸을 때 편수와 비율 표시
fig.update_traces(
    textinfo="percent",
    hovertemplate="<b>%{label}</b><br>편수: %{value}편<br>비율: %{percent}<extra></extra>"
)

fig.update_layout(
    legend_title_text="장르",
    margin=dict(t=60, b=20, l=20, r=20)
)

st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------
# 그래프 설명 영역
# ---------------------------------------------------------
with st.container(border=True):
    st.markdown("### 💡 이 그래프로 알 수 있는 것")
    st.text_input(
        "한 문장으로 정리해 보세요.",
        placeholder="예: 전체 영화에서 어떤 장르의 영화가 가장 많은지 알 수 있다.",
        key="graph1_observation"
    )

st.divider()

# ---------------------------------------------------------
# 원본 데이터 일부 확인
# ---------------------------------------------------------
with st.expander("📊 사용한 데이터 확인하기"):
    display_df = df.copy()
    display_df["openDt"] = display_df["openDt"].dt.strftime("%Y-%m-%d")
    display_df = display_df[
        [
            "movieCd", "movieNm", "openDt", "genre_first", "nation",
            "first_scrn", "first_show", "first_week_audi",
            "total_audi", "days_in_top10"
        ]
    ].rename(
        columns={
            "movieCd": "영화코드",
            "movieNm": "영화명",
            "openDt": "개봉일",
            "genre_first": "장르",
            "nation": "제작 국가",
            "first_scrn": "개봉일 스크린수",
            "first_show": "개봉일 상영횟수",
            "first_week_audi": "개봉 첫 주 관객",
            "total_audi": "총 관객",
            "days_in_top10": "10위권 머문 날수"
        }
    )
    st.dataframe(display_df, use_container_width=True, hide_index=True)
