
import re
from itertools import combinations

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 페이지 설정
# --------------------------------------------------
st.set_page_config(
    page_title="급식 규칙 찾기",
    page_icon="🍱",
    layout="wide",
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "teacher188-netizen/2026-datascience/"
    "refs/heads/main/sangok_meals.csv"
)

st.title("🍱 급식 규칙 찾기")
st.write(
    "우리 학교 급식 데이터를 분석해 함께 나오는 메뉴와 "
    "한 번도 함께 나오지 않은 메뉴를 찾아봅니다."
)


# --------------------------------------------------
# 메뉴 이름 정리
# --------------------------------------------------
def clean_menu(menu):
    menu = str(menu).strip()

    # 괄호 및 괄호 안의 내용 제거
    menu = re.sub(r"\([^()]*\)|（[^（）]*）", "", menu)

    # 공백 정리
    menu = re.sub(r"\s+", " ", menu).strip()

    return menu


# --------------------------------------------------
# CSV 불러오기
# --------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")

    required_columns = ["날짜", "식사", "메뉴"]
    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "필요한 열이 없습니다: " + ", ".join(missing)
        )

    df = df[required_columns].copy()
    df = df.dropna(subset=["날짜", "메뉴"])

    df["날짜"] = df["날짜"].astype(str).str.strip()
    df["식사"] = df["식사"].astype(str).str.strip()

    transactions = []

    for _, row in df.iterrows():
        raw_menus = str(row["메뉴"]).split("|")

        menus = [
            clean_menu(menu)
            for menu in raw_menus
        ]

        # 같은 식단 안에서 메뉴 중복 제거
        menus = sorted(set(menu for menu in menus if menu))

        if menus:
            transactions.append({
                "날짜": row["날짜"],
                "식사": row["식사"],
                "메뉴목록": menus,
            })

    return transactions


# --------------------------------------------------
# 메뉴별 출현 횟수와 메뉴 쌍 계산
# --------------------------------------------------
def analyze_rules(transactions):
    total_days = len(transactions)

    menu_counts = {}
    pair_counts = {}

    for transaction in transactions:
        menus = transaction["메뉴목록"]

        for menu in menus:
            menu_counts[menu] = menu_counts.get(menu, 0) + 1

        for menu_a, menu_b in combinations(menus, 2):
            pair = (menu_a, menu_b)
            pair_counts[pair] = pair_counts.get(pair, 0) + 1

    rules = []

    for (menu_a, menu_b), count in pair_counts.items():
        support = count / total_days

        # A -> B
        confidence_ab = count / menu_counts[menu_a]
        support_b = menu_counts[menu_b] / total_days
        lift_ab = confidence_ab / support_b

        rules.append({
            "조건": menu_a,
            "결과": menu_b,
            "동시": count,
            "지지도": support,
            "신뢰도": confidence_ab,
            "향상도": lift_ab,
        })

        # B -> A
        confidence_ba = count / menu_counts[menu_b]
        support_a = menu_counts[menu_a] / total_days
        lift_ba = confidence_ba / support_a

        rules.append({
            "조건": menu_b,
            "결과": menu_a,
            "동시": count,
            "지지도": support,
            "신뢰도": confidence_ba,
            "향상도": lift_ba,
        })

    return rules, menu_counts, pair_counts


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
try:
    transactions = load_data()
except Exception as e:
    st.error(f"급식 데이터를 불러오지 못했습니다: {e}")
    st.info(
        "CSV 주소와 열 이름(날짜, 식사, 메뉴)을 확인해 주세요."
    )
    st.stop()

if not transactions:
    st.warning("분석할 수 있는 급식 데이터가 없습니다.")
    st.stop()

rules, menu_counts, pair_counts = analyze_rules(transactions)

menu_names = sorted(menu_counts.keys())
unique_pair_count = len(pair_counts)


# --------------------------------------------------
# 요약 지표
# --------------------------------------------------
st.subheader("분석 요약")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("급식 식단 수", f"{len(transactions):,}일")

with col2:
    st.metric("메뉴 종류 수", f"{len(menu_names):,}종")

with col3:
    st.metric("함께 나온 메뉴 쌍 수", f"{unique_pair_count:,}쌍")

st.caption(
    "한 행의 식단을 한 건으로 계산합니다. 메뉴 쌍 수는 방향을 "
    "구분하지 않은 고유 쌍의 수이며, 규칙 표에는 양방향 규칙이 표시됩니다."
)


# --------------------------------------------------
# 최소 동시 일수
# --------------------------------------------------
st.divider()
st.subheader("1. 분석 조건")

min_cooccurrence = st.slider(
    "최소 동시 일수",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    help="이 횟수보다 적게 함께 나온 규칙은 표와 그래프에서 제외합니다.",
)

st.caption(
    f"현재 최소 동시 일수: {min_cooccurrence}일"
)


# --------------------------------------------------
# 메뉴 필터 및 정렬
# --------------------------------------------------
col_filter, col_sort = st.columns([2, 1])

with col_filter:
    selected_menu = st.selectbox(
        "규칙 좁혀 보기",
        options=["전체 메뉴"] + menu_names,
        index=0,
        key="rule_menu_filter",
    )

with col_sort:
    sort_option = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0,
        key="rule_sort_option",
    )


# --------------------------------------------------
# 규칙 필터링
# --------------------------------------------------
rules_df = pd.DataFrame(
    rules,
    columns=["조건", "결과", "동시", "지지도", "신뢰도", "향상도"],
)

# 최소 동시 일수 적용
rules_df = rules_df[
    rules_df["동시"] >= min_cooccurrence
].copy()

# 선택한 메뉴가 조건 또는 결과에 있는 규칙만 표시
if selected_menu != "전체 메뉴":
    rules_df = rules_df[
        (rules_df["조건"] == selected_menu)
        | (rules_df["결과"] == selected_menu)
    ].copy()

sort_columns = {
    "향상도 순": ["향상도", "신뢰도", "동시"],
    "신뢰도 순": ["신뢰도", "향상도", "동시"],
    "동시 순": ["동시", "향상도", "신뢰도"],
}

rules_df = rules_df.sort_values(
    by=sort_columns[sort_option],
    ascending=[False, False, False],
    kind="mergesort",
).reset_index(drop=True)


# --------------------------------------------------
# 규칙 표
# --------------------------------------------------
st.divider()
st.subheader("2. 함께 나오는 메뉴 규칙")

st.write(
    f"현재 조건에 맞는 규칙은 **{len(rules_df):,}개**입니다."
)

st.caption(
    "지지도와 신뢰도는 백분율(%)로 표시하고, 향상도는 배수로 표시합니다."
)

if rules_df.empty:
    st.info(
        "조건에 맞는 규칙이 없습니다. 최소 동시 일수를 낮추거나 "
        "다른 메뉴를 선택해 보세요."
    )
else:
    display_df = rules_df[
        ["조건", "결과", "동시", "지지도", "신뢰도", "향상도"]
    ].copy()

    display_df["지지도"] *= 100
    display_df["신뢰도"] *= 100

    display_df = display_df.rename(columns={
        "지지도": "지지도 (%)",
        "신뢰도": "신뢰도 (%)",
    })

    st.dataframe(
        display_df.style.format({
            "동시": "{:,.0f}",
            "지지도 (%)": "{:.2f}%",
            "신뢰도 (%)": "{:.2f}%",
            "향상도": "{:.3f}",
        }),
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 향상도 상위 10개 그래프
# --------------------------------------------------
st.divider()
st.subheader("3. 향상도 상위 10개 규칙")

if rules_df.empty:
    st.info("그래프에 표시할 규칙이 없습니다.")
else:
    top10 = rules_df.sort_values(
        by=["향상도", "신뢰도", "동시"],
        ascending=[False, False, False],
        kind="mergesort",
    ).head(10).copy()

    top10["규칙"] = top10["조건"] + " → " + top10["결과"]

    top10 = top10.sort_values("향상도", ascending=True)

    fig = px.bar(
        top10,
        x="향상도",
        y="규칙",
        orientation="h",
        text="향상도",
        hover_data={
            "조건": True,
            "결과": True,
            "동시": True,
            "지지도": ":.2%",
            "신뢰도": ":.2%",
            "향상도": ":.3f",
            "규칙": False,
        },
        labels={
            "향상도": "향상도",
            "규칙": "조건 메뉴 → 결과 메뉴",
        },
        title="향상도 상위 10개 규칙",
    )

    fig.update_traces(
        texttemplate="%{text:.3f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title="향상도",
        yaxis_title="메뉴 규칙",
        margin=dict(l=20, r=70, t=60, b=30),
        height=max(400, len(top10) * 42),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "위에서 선택한 최소 동시 일수와 메뉴 필터가 그래프에도 적용됩니다."
    )


# --------------------------------------------------
# 함께 나온 적 없는 짝
# --------------------------------------------------
st.divider()
st.subheader("4. 함께 나온 적 없는 짝")

st.write(
    "메뉴 하나를 고르면, 그 메뉴와 같은 식단에 한 번도 함께 나오지 않았지만 "
    "각각 10회 이상 나온 메뉴를 찾아봅니다."
)

selected_menu_absent = st.selectbox(
    "함께 나온 적 없는 짝을 찾을 기준 메뉴",
    options=menu_names,
    index=0,
    key="absent_pair_menu_selector",
)

selected_menu_days = menu_counts[selected_menu_absent]

# 기준 메뉴와 같은 식단에 함께 나온 적이 있는 메뉴 집합
cooccurring_menus = set()

for (menu_a, menu_b), count in pair_counts.items():
    if count <= 0:
        continue

    if menu_a == selected_menu_absent:
        cooccurring_menus.add(menu_b)
    elif menu_b == selected_menu_absent:
        cooccurring_menus.add(menu_a)

# 기준 메뉴 자체는 제외하고,
# 한 번도 함께 나오지 않았으며 단독 출현 횟수가 10회 이상인 메뉴 찾기
absent_candidates = []

for menu, days in menu_counts.items():
    if menu == selected_menu_absent:
        continue

    if menu in cooccurring_menus:
        continue

    if days < 10:
        continue

    absent_candidates.append({
        "메뉴": menu,
        "나온 날 수": days,
    })

absent_df = pd.DataFrame(
    absent_candidates,
    columns=["메뉴", "나온 날 수"],
)

if not absent_df.empty:
    absent_df = absent_df.sort_values(
        by=["나온 날 수", "메뉴"],
        ascending=[False, True],
        kind="mergesort",
    ).reset_index(drop=True)

st.write(
    f"선택한 메뉴 **{selected_menu_absent}**는 "
    f"전체 식단 중 **{selected_menu_days:,}일**에 나왔습니다."
)

st.write(
    f"함께 나온 적 없는 메뉴 중 10회 이상 나온 메뉴는 "
    f"**{len(absent_df):,}종**입니다."
)

if absent_df.empty:
    st.info(
        "조건에 맞는 메뉴가 없습니다. 다른 기준 메뉴를 선택해 보세요."
    )
else:
    st.dataframe(
        absent_df,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# 계산 방법
# --------------------------------------------------
st.divider()

with st.expander("지지도·신뢰도·향상도 계산 방법"):
    st.markdown(
        """
        - **지지도** = 두 메뉴가 함께 나온 식단 수 / 전체 식단 수
        - **신뢰도(A → B)** = A와 B가 함께 나온 식단 수 / A가 나온 식단 수
        - **향상도(A → B)** = 신뢰도(A → B) / B가 나온 식단 비율

        향상도는 두 메뉴의 연관성을 나타내며 인과관계를 의미하지 않습니다.

        함께 나온 적 없는 짝은 기준 메뉴와 후보 메뉴의 동시 출현 횟수가
        0이고, 후보 메뉴가 10회 이상 나온 경우에만 표시합니다.
        """
    )
