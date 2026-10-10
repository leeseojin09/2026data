
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

st.title("🍱 급식 규칙 찾기")
st.write(
    "우리 학교 급식 데이터를 분석해 함께 나오는 메뉴의 규칙을 찾아봅니다."
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "teacher188-netizen/2026-datascience/"
    "refs/heads/main/sangok_meals.csv"
)


# --------------------------------------------------
# 메뉴 이름 정리
# 괄호와 괄호 안의 내용 제거
# --------------------------------------------------
def clean_menu(menu):
    menu = str(menu).strip()

    # 일반 괄호 및 전각 괄호 안의 내용 제거
    menu = re.sub(r"\([^()]*\)|（[^（）]*）", "", menu)

    # 괄호 제거 후 공백 정리
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

    # 한 행을 하나의 급식 식단으로 취급
    transactions = []

    for _, row in df.iterrows():
        raw_menus = str(row["메뉴"]).split("|")

        # 괄호 제거 후 빈 이름 제외
        menus = [
            clean_menu(menu)
            for menu in raw_menus
        ]
        menus = sorted(set(
            menu for menu in menus if menu
        ))

        transactions.append({
            "날짜": row["날짜"],
            "식사": row["식사"],
            "메뉴목록": menus,
        })

    # 분석할 수 있는 식단만 유지
    transactions = [
        item for item in transactions
        if item["메뉴목록"]
    ]

    return transactions


# --------------------------------------------------
# 연관 규칙 계산
# --------------------------------------------------
def analyze_rules(transactions):
    total_days = len(transactions)

    if total_days == 0:
        return [], [], 0

    # 각 메뉴가 나온 식단 수
    menu_counts = {}

    # 두 메뉴가 함께 나온 식단 수
    pair_counts = {}

    for transaction in transactions:
        menus = transaction["메뉴목록"]

        for menu in menus:
            menu_counts[menu] = (
                menu_counts.get(menu, 0) + 1
            )

        # 하루 안에서 같은 메뉴는 한 번만 계산
        for menu_a, menu_b in combinations(menus, 2):
            pair = (menu_a, menu_b)
            pair_counts[pair] = (
                pair_counts.get(pair, 0) + 1
            )

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

    menu_names = sorted(menu_counts.keys())
    unique_pair_count = len(pair_counts)

    return rules, menu_names, unique_pair_count


# --------------------------------------------------
# 데이터 불러오기
# --------------------------------------------------
try:
    transactions = load_data()
except Exception as e:
    st.error(f"급식 데이터를 불러오지 못했습니다: {e}")
    st.info(
        "CSV 주소와 파일의 열 이름(날짜, 식사, 메뉴)을 확인해 주세요."
    )
    st.stop()

if not transactions:
    st.warning("분석할 수 있는 급식 데이터가 없습니다.")
    st.stop()

rules, menu_names, unique_pair_count = analyze_rules(
    transactions
)

if not rules:
    st.warning("함께 나온 메뉴 쌍이 없습니다.")
    st.stop()


# --------------------------------------------------
# 요약 지표
# --------------------------------------------------
st.subheader("분석 요약")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("급식 일수", f"{len(transactions):,}일")

with col2:
    st.metric("메뉴 종류 수", f"{len(menu_names):,}종")

with col3:
    st.metric(
        "함께 나온 메뉴 쌍 수",
        f"{unique_pair_count:,}쌍",
    )

st.caption(
    "메뉴 쌍 수는 방향을 구분하지 않은 고유 쌍의 수입니다. "
    "규칙 표에는 각 쌍의 양방향 규칙이 모두 표시됩니다."
)


# --------------------------------------------------
# 메뉴 선택 및 정렬
# --------------------------------------------------
st.divider()
st.subheader("1. 메뉴와 정렬 기준 선택")

col_filter, col_sort = st.columns([2, 1])

with col_filter:
    selected_menu = st.selectbox(
        "특정 메뉴의 규칙만 보기",
        options=["전체 메뉴"] + menu_names,
        index=0,
    )

with col_sort:
    sort_option = st.selectbox(
        "정렬 기준",
        options=["향상도 순", "신뢰도 순", "동시 순"],
        index=0,
    )

rules_df = pd.DataFrame(rules)

# 메뉴를 선택하면 조건 또는 결과에 해당 메뉴가 포함된 규칙만 표시
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
st.subheader("2. 함께 나오는 메뉴 규칙")

st.caption(
    "지지도·신뢰도는 백분율(%)로, 향상도는 배수로 표시합니다."
)

if rules_df.empty:
    st.info("선택한 메뉴에 해당하는 규칙이 없습니다.")
else:
    display_df = rules_df[
        ["조건", "결과", "동시", "지지도", "신뢰도", "향상도"]
    ].copy()

    display_df["지지도"] = display_df["지지도"] * 100
    display_df["신뢰도"] = display_df["신뢰도"] * 100

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

    st.caption(f"표시 중인 규칙: {len(display_df):,}개")


# --------------------------------------------------
# 향상도 상위 10개 가로 막대그래프
# --------------------------------------------------
st.divider()
st.subheader("3. 향상도 상위 10개 규칙")

if rules_df.empty:
    st.info("그래프를 그릴 규칙이 없습니다.")
else:
    top10 = rules_df.sort_values(
        by=["향상도", "신뢰도", "동시"],
        ascending=[False, False, False],
        kind="mergesort",
    ).head(10).copy()

    # 조건 -> 결과 형태로 표시
    top10["규칙"] = (
        top10["조건"] + " → " + top10["결과"]
    )

    # 높은 향상도가 위쪽에 오도록 표시
    top10 = top10.sort_values(
        "향상도",
        ascending=True,
    )

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
            "규칙": "메뉴 규칙",
        },
        title="함께 등장하는 정도가 높은 메뉴 규칙",
    )

    fig.update_traces(
        texttemplate="%{text:.3f}",
        textposition="outside",
        cliponaxis=False,
    )

    fig.update_layout(
        xaxis_title="향상도",
        yaxis_title="조건 메뉴 → 결과 메뉴",
        margin=dict(l=20, r=70, t=60, b=30),
        height=max(400, len(top10) * 42),
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "메뉴를 선택하면 표와 그래프가 함께 필터링됩니다. "
        "그래프는 필터링된 규칙 중 향상도 상위 10개를 보여 줍니다."
    )


# --------------------------------------------------
# 지표 설명
# --------------------------------------------------
st.divider()

with st.expander("지지도·신뢰도·향상도 계산 방법"):
    st.markdown(
        """
        **기호 정의**

        - A: 조건 메뉴
        - B: 결과 메뉴
        - N: 전체 급식 식단 수
        - count(A): A가 나온 식단 수
        - count(A, B): A와 B가 함께 나온 식단 수

        **1. 지지도**

        두 메뉴가 함께 나온 식단 수를 전체 식단 수로 나눕니다.

        `지지도 = count(A, B) / N`

        **2. 신뢰도**

        조건 메뉴가 나온 식단 중 결과 메뉴도 나온 비율입니다.

        `신뢰도 = count(A, B) / count(A)`

        **3. 향상도**

        결과 메뉴의 전체 출현 비율과 비교해,
        조건 메뉴가 있을 때 결과 메뉴가 얼마나 더 자주 나오는지 나타냅니다.

        `향상도 = 신뢰도(A → B) / (count(B) / N)`

        - 향상도 > 1: 양의 연관성
        - 향상도 = 1: 독립적인 출현 관계
        - 향상도 < 1: 음의 연관성

        향상도는 인과관계를 의미하지 않습니다.
        또한 이 앱은 같은 날 중복된 메뉴 이름을 한 번만 계산하며,
        괄호와 괄호 안의 내용은 메뉴 이름에서 제거합니다.
        """
    )
