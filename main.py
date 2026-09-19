import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import math


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 유형 나누기")
st.caption(
    "영화의 관객·스크린·상영 성과 데이터를 이용해 "
    "비슷한 영화끼리 유형으로 나눕니다."
)

DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


# =========================================================
# 2. 데이터 불러오기
# =========================================================

@st.cache_data
def load_data():
    return pd.read_csv(
        DATA_URL,
        encoding="utf-8"
    )


try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


total_count = len(df)


# =========================================================
# 3. 숫자형 데이터 변환
# =========================================================

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
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# =========================================================
# 4. 군집화에 사용할 네 가지 속성 만들기
# =========================================================

# 스크린 수 → 상용로그
df["스크린 수"] = df["first_scrn"].apply(
    lambda x: math.log10(x)
    if pd.notna(x) and x > 0
    else None
)

# 누적 관객 → 상용로그
df["누적 관객"] = df["total_audi"].apply(
    lambda x: math.log10(x)
    if pd.notna(x) and x > 0
    else None
)

# 10위권 일수 → 그대로 사용
df["10위권 일수"] = df["days_in_top10"]


# 롱런 지수
# = 누적 관객 / 첫 주 관객
# 최대 20으로 제한
df["롱런 지수"] = (
    df["total_audi"] / df["first_week_audi"]
).clip(upper=20)


# =========================================================
# 5. 속성 이름
# =========================================================

feature_names = [
    "스크린 수",
    "누적 관객",
    "10위권 일수",
    "롱런 지수"
]


# =========================================================
# 6. 사용할 속성 선택
# =========================================================

st.subheader("📌 영화 유형을 나눌 속성")

selected_features = st.multiselect(
    "묶는 데 사용할 속성을 선택하세요. 두 개 이상 선택해야 합니다.",
    options=feature_names,
    default=feature_names
)

if len(selected_features) < 2:
    st.warning(
        "영화 유형을 나누려면 속성을 두 개 이상 선택해야 합니다."
    )
    st.stop()


# =========================================================
# 7. 묶음 수 선택
# =========================================================

st.subheader("🔢 묶음 수 정하기")

n_clusters = st.selectbox(
    "영화를 몇 개의 묶음으로 나눌까요?",
    options=list(range(2, 8)),
    index=1
)


# =========================================================
# 8. 분석 대상 데이터 정리
# =========================================================

analysis_df = df.copy()

# 첫 주 관객이 없거나 0인 영화 제외
analysis_df = analysis_df[
    analysis_df["first_week_audi"].notna()
    & (analysis_df["first_week_audi"] > 0)
]

# 선택한 속성 중 하나라도 값이 없으면 제외
analysis_df = analysis_df.dropna(
    subset=selected_features
).copy()

cluster_count = len(analysis_df)


# =========================================================
# 9. 전체 편수 / 묶은 편수
# =========================================================

st.markdown(
    f"**전체 영화: {total_count}편　|　묶은 영화: {cluster_count}편**"
)

if cluster_count < n_clusters:
    st.error(
        f"선택한 묶음 수가 분석 가능한 영화 수보다 많습니다. "
        f"현재 분석 가능한 영화는 {cluster_count}편입니다."
    )
    st.stop()


# =========================================================
# 10. 표준화
# =========================================================

X = analysis_df[selected_features].values

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# =========================================================
# 11. 묶음 표시 기호
# =========================================================

cluster_symbols = [
    "㉮",
    "㉯",
    "㉰",
    "㉱",
    "㉲",
    "㉳",
    "㉴"
]


# =========================================================
# 12. 선택한 묶음 수로 K-평균 군집화
# =========================================================

kmeans = KMeans(
    n_clusters=n_clusters,
    random_state=42,
    n_init=10
)

analysis_df["cluster"] = kmeans.fit_predict(X_scaled)


# =========================================================
# 13. 누적 관객 평균이 높은 묶음부터
#     ㉮ → ㉯ → ㉰ ... 순서 지정
# =========================================================

cluster_order = (
    analysis_df
    .groupby("cluster")["total_audi"]
    .mean()
    .sort_values(ascending=False)
    .index
    .tolist()
)

label_map = {
    cluster_id: cluster_symbols[i]
    for i, cluster_id in enumerate(cluster_order)
}

analysis_df["유형"] = analysis_df["cluster"].map(
    label_map
)


# =========================================================
# 14. 2차원 산점도
# =========================================================

st.subheader("📊 2차원 산점도")

col1, col2 = st.columns(2)

with col1:
    x_feature = st.selectbox(
        "가로축 속성",
        feature_names,
        index=0,
        key="x_feature"
    )

with col2:
    y_feature = st.selectbox(
        "세로축 속성",
        feature_names,
        index=1,
        key="y_feature"
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
        "유형": cluster_symbols[:n_clusters]
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


# =========================================================
# 15. 3차원 산점도
# =========================================================

st.subheader("🌐 3차원 산점도")

if len(selected_features) < 3:

    st.info(
        "3차원 산점도를 표시하려면 영화 유형을 나눌 "
        "속성을 3개 이상 선택하세요."
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
            "유형": cluster_symbols[:n_clusters]
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


# =========================================================
# 16. 묶음별 요약표
# =========================================================

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

summary["순서"] = summary["유형"].map({
    symbol: i
    for i, symbol in enumerate(
        cluster_symbols[:n_clusters]
    )
})

summary = (
    summary
    .sort_values("순서")
    .drop(columns="순서")
)

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

summary["스크린 수 평균"] = (
    summary["스크린 수 평균"]
    .round(1)
)

summary["누적 관객 평균"] = (
    summary["누적 관객 평균"]
    .round(0)
    .astype(int)
)

summary["10위권 일수 평균"] = (
    summary["10위권 일수 평균"]
    .round(1)
)

summary["롱런 지수 평균"] = (
    summary["롱런 지수 평균"]
    .round(2)
)

st.dataframe(
    summary,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 17. 유형별 누적 관객 TOP 5
# =========================================================

st.subheader("🏆 유형별 누적 관객 TOP 5")

for label in cluster_symbols[:n_clusters]:

    st.markdown(f"### {label}")

    top_movies = (
        analysis_df[
            analysis_df["유형"] == label
        ]
        .sort_values(
            "total_audi",
            ascending=False
        )
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
        .map(
            lambda x: f"{int(x):,}명"
        )
    )

    st.dataframe(
        top_movies,
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 18. K = 1 ~ 7 WCSS 계산
# =========================================================
#
# WCSS
# = 각 묶음 안에서 각 점이 중심에서 떨어진 거리의
#   제곱을 모두 더한 값
#
# sklearn KMeans의 inertia_가 WCSS이다.
# =========================================================

st.subheader("📉 묶음 수에 따른 중심으로부터의 거리 제곱합")

wcss_results = []

max_k = min(7, cluster_count)

for k in range(1, max_k + 1):

    model = KMeans(
        n_clusters=k,
        random_state=42,
        n_init=10
    )

    model.fit(X_scaled)

    wcss_results.append({
        "묶음 수": k,
        "거리 제곱합": model.inertia_
    })

wcss_df = pd.DataFrame(wcss_results)


# =========================================================
# 19. WCSS 꺾은선 그래프
# =========================================================

fig_wcss = px.line(
    wcss_df,
    x="묶음 수",
    y="거리 제곱합",
    markers=True,
    title="묶음 수에 따른 중심으로부터의 거리 제곱합"
)

# 현재 선택한 묶음 수에 세로선
fig_wcss.add_vline(
    x=n_clusters,
    line_dash="dash",
    annotation_text=f"현재 선택: {n_clusters}개",
    annotation_position="top"
)

fig_wcss.update_layout(
    height=500,
    xaxis=dict(
        dtick=1
    ),
    yaxis_title="거리 제곱합"
)

st.plotly_chart(
    fig_wcss,
    use_container_width=True
)


# =========================================================
# 20. WCSS 값과 바로 앞 값 대비 감소량
# =========================================================

wcss_table = wcss_df.copy()

wcss_table["바로 앞 값에서 감소"] = (
    wcss_table["거리 제곱합"].shift(1)
    - wcss_table["거리 제곱합"]
)

# 첫 번째 값은 비교할 앞 값이 없으므로 빈칸
wcss_table.loc[
    wcss_table.index[0],
    "바로 앞 값에서 감소"
] = None

wcss_table["거리 제곱합"] = (
    wcss_table["거리 제곱합"]
    .round(2)
)

wcss_table["바로 앞 값에서 감소"] = (
    wcss_table["바로 앞 값에서 감소"]
    .round(2)
)

st.dataframe(
    wcss_table,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 21. 선택한 묶음 수의 실루엣 점수
# =========================================================

selected_model = KMeans(
    n_clusters=n_clusters,
    random_state=42,
    n_init=10
)

selected_labels = selected_model.fit_predict(
    X_scaled
)

# 실루엣 점수는 2개 이상의 묶음에서 계산 가능
if (
    n_clusters >= 2
    and len(set(selected_labels)) >= 2
    and cluster_count > n_clusters
):

    silhouette = silhouette_score(
        X_scaled,
        selected_labels
    )

    st.markdown(
        f"**실루엣 점수: {silhouette:.3f}**"
        "　(-1~1 범위이며, 1에 가까울수록 묶음이 뚜렷합니다.)"
    )

else:

    st.markdown(
        "**실루엣 점수: 계산할 수 없습니다.**"
    )
