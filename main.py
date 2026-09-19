import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")
st.caption("영화의 관객·스크린·상영 성과 데이터를 이용해 비슷한 영화끼리 유형을 나눕니다.")

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

# ---------------------------------------------------------
# 2. 데이터 불러오기
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    return df


try:
    df = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()

total_count = len(df)

# ---------------------------------------------------------
# 3. 필요한 숫자형 데이터 변환
# ---------------------------------------------------------
numeric_columns = [
    "first_scrn",
    "first_show",
    "first_date",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# ---------------------------------------------------------
# 4. 분석용 속성 만들기
# ---------------------------------------------------------
# 스크린 수와 누적 관객 → 상용로그
df["스크린 수"] = df["first_scrn"].apply(
    lambda x: __import__("math").log10(x) if pd.notna(x) and x > 0 else None
)

df["누적 관객"] = df["total_audi"].apply(
    lambda x: __import__("math").log10(x) if pd.notna(x) and x > 0 else None
)

# 10위권 일수 그대로
df["10위권 일수"] = df["days_in_top10"]

# 롱런 지수 = 누적 관객 / 첫 주 관객
df["롱런 지수"] = (
    df["total_audi"] / df["first_week_audi"]
).clip(upper=20)

# ---------------------------------------------------------
# 5. 분석에 사용할 속성
# ---------------------------------------------------------
feature_map = {
    "스크린 수": "스크린 수",
    "누적 관객": "누적 관객",
    "10위권 일수": "10위권 일수",
    "롱런 지수": "롱런 지수"
}

feature_names = list(feature_map.keys())

# ---------------------------------------------------------
# 6. 속성 선택
# ---------------------------------------------------------
st.subheader("📌 영화 유형을 나눌 속성")

selected_features = st.multiselect(
    "두 개 이상 선택하세요.",
    options=feature_names,
    default=feature_names,
    help="선택한 속성을 표준화한 뒤 K-평균 군집화를 수행합니다."
)

if len(selected_features) < 2:
    st.warning("영화 유형을 나누려면 속성을 두 개 이상 선택해야 합니다.")
    st.stop()

# ---------------------------------------------------------
# 7. 결측치 및 첫 주 관객 0인 영화 제거
# ---------------------------------------------------------
analysis_df = df.copy()

# 첫 주 관객이 없거나 0인 영화 제거
analysis_df = analysis_df[
    analysis_df["first_week_audi"].notna()
    & (analysis_df["first_week_audi"] > 0)
]

# 선택한 속성 중 하나라도 값이 없는 영화 제거
analysis_df = analysis_df.dropna(
    subset=selected_features
).copy()

cluster_count = len(analysis_df)

# 전체 편수 / 묶은 편수
st.markdown(
    f"**전체 영화: {total_count}편　|　묶은 영화: {cluster_count}편**"
)

if cluster_count < 3:
    st.error("세 묶음으로 나누려면 분석 가능한 영화가 최소 3편 필요합니다.")
    st.stop()

# ---------------------------------------------------------
# 8. K-평균 군집화
# ---------------------------------------------------------
X = analysis_df[selected_features].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

analysis_df["cluster"] = kmeans.fit_predict(X_scaled)

# ---------------------------------------------------------
# 9. 누적 관객 평균이 높은 순서로 ㉮ ㉯ ㉰ 부여
# ---------------------------------------------------------
cluster_order = (
    analysis_df.groupby("cluster")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
    .tolist()
)

label_map = {
    cluster_order[0]: "㉮",
    cluster_order[1]: "㉯",
    cluster_order[2]: "㉰"
}

analysis_df["유형"] = analysis_df["cluster"].map(label_map)

# ---------------------------------------------------------
# 10. 2차원 산점도
# ---------------------------------------------------------
st.subheader("📊 2차원 산점도")

col1, col2 = st.columns(2)

with col1:
    x_feature = st.selectbox(
        "가로축 속성",
        feature_names,
        index=0
    )

with col2:
    y_feature = st.selectbox(
        "세로축 속성",
        feature_names,
        index=1 if len(feature_names) > 1 else 0
    )

fig_2d = px.scatter(
    analysis_df,
    x=x_feature,
    y=y_feature,
    color="유형",
    hover_name="movieNm",
    hover_data={
        x_feature: ":.2f",
        y_feature: ":.2f",
        "유형": True,
        "movieNm": False
    },
    category_orders={
        "유형": ["㉮", "㉯", "㉰"]
    },
    labels={
        x_feature: x_feature,
        y_feature: y_feature,
        "유형": "영화 유형"
    },
    title=f"{x_feature} × {y_feature}"
)

fig_2d.update_traces(
    marker=dict(size=8)
)

fig_2d.update_layout(
    height=550,
    legend_title_text="영화 유형"
)

st.plotly_chart(
    fig_2d,
    use_container_width=True
)

# ---------------------------------------------------------
# 11. 3차원 산점도
# ---------------------------------------------------------
st.subheader("🌐 3차원 산점도")

if len(selected_features) < 3:
    st.info(
        "3차원 산점도를 표시하려면 영화 유형을 나눌 속성을 "
        "3개 이상 선택하세요."
    )
else:
    col1, col2, col3 = st.columns(3)

    with col1:
        x3 = st.selectbox(
            "X축 속성",
            selected_features,
            index=0,
            key="x3"
        )

    with col2:
        y3 = st.selectbox(
            "Y축 속성",
            selected_features,
            index=1,
            key="y3"
        )

    with col3:
        z3 = st.selectbox(
            "Z축 속성",
            selected_features,
            index=2,
            key="z3"
        )

    fig_3d = px.scatter_3d(
        analysis_df,
        x=x3,
        y=y3,
        z=z3,
        color="유형",
        hover_name="movieNm",
        hover_data={
            x3: ":.2f",
            y3: ":.2f",
            z3: ":.2f",
            "유형": True,
            "movieNm": False
        },
        category_orders={
            "유형": ["㉮", "㉯", "㉰"]
        },
        labels={
            x3: x3,
            y3: y3,
            z3: z3,
            "유형": "영화 유형"
        },
        title=f"{x3} × {y3} × {z3}"
    )

    fig_3d.update_traces(
        marker=dict(size=3)
    )

    fig_3d.update_layout(
        height=700,
        legend_title_text="영화 유형"
    )

    st.plotly_chart(
        fig_3d,
        use_container_width=True
    )

# ---------------------------------------------------------
# 12. 유형별 요약
# ---------------------------------------------------------
st.subheader("📋 유형별 요약")

summary = (
    analysis_df
    .groupby("유형")
    .agg(
        편수=("movieNm", "count"),
        스크린수_평균=("first_scrn", "mean"),
        누적관객_평균=("total_audi", "mean"),
        십위권일수_평균=("days_in_top10", "mean"),
        롱런지수_평균=("롱런 지수", "mean")
    )
    .reset_index()
)

# ㉮ → ㉯ → ㉰ 순서
summary["순서"] = summary["유형"].map({
    "㉮": 0,
    "㉯": 1,
    "㉰": 2
})

summary = summary.sort_values("순서").drop(columns="순서")

summary = summary.rename(
    columns={
        "유형": "영화 유형",
        "편수": "편수",
        "스크린수_평균": "스크린 수 평균",
        "누적관객_평균": "누적 관객 평균",
        "십위권일수_평균": "10위권 일수 평균",
        "롱런지수_평균": "롱런 지수 평균"
    }
)

summary["스크린 수 평균"] = summary["스크린 수 평균"].round(1)
summary["누적 관객 평균"] = summary["누적 관객 평균"].round(0).astype(int)
summary["10위권 일수 평균"] = summary["10위권 일수 평균"].round(1)
summary["롱런 지수 평균"] = summary["롱런 지수 평균"].round(2)

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True
)

# ---------------------------------------------------------
# 13. 유형별 누적 관객 TOP 5
# ---------------------------------------------------------
st.subheader("🏆 유형별 누적 관객 TOP 5")

for label in ["㉮", "㉯", "㉰"]:
    st.markdown(f"### {label}")

    top_movies = (
        analysis_df[analysis_df["유형"] == label]
        .sort_values("total_audi", ascending=False)
        .head(5)
        [["movieNm", "total_audi"]]
        .copy()
    )

    top_movies = top_movies.rename(
        columns={
            "movieNm": "영화 제목",
            "total_audi": "누적 관객"
        }
    )

    top_movies["누적 관객"] = (
        top_movies["누적 관객"]
        .map(lambda x: f"{int(x):,}명")
    )

    if len(top_movies) > 0:
        st.dataframe(
            top_movies,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.write("해당 유형에 영화가 없습니다.")
