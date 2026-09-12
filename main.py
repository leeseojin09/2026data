import streamlit as st
import requests
import pandas as pd
import re
from datetime import date

# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="🏫 세 학교 급식 비교",
    page_icon="🍱",
    layout="wide"
)

st.title("🏫 산곡고 · 세일고 · 부평고 급식 비교")
st.caption("2026년 전체 중식 데이터를 이용한 갑각류 알레르기 · 디저트 · 김치 분석")

# 나이스 API
NEIS_BASE_URL = "https://open.neis.go.kr/hub"

SCHOOL_API = f"{NEIS_BASE_URL}/schoolInfo"
MEAL_API = f"{NEIS_BASE_URL}/mealServiceDietInfo"

# 분석 대상 학교
SCHOOL_NAMES = [
    "산곡고등학교",
    "세일고등학교",
    "부평고등학교"
]

# 2026년 전체
START_DATE = "20260101"
END_DATE = "20261231"


# =========================================================
# 2. 공통 함수
# =========================================================

def safe_get_json(url, params):
    """
    나이스 API 호출
    """
    try:
        response = requests.get(
            url,
            params=params,
            timeout=20
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        st.error(f"API 요청 오류: {e}")
        return None

    except ValueError:
        st.error("API에서 올바른 JSON 데이터를 받지 못했습니다.")
        return None


# =========================================================
# 3. 학교 정보 검색
# =========================================================

@st.cache_data(ttl=86400)
def find_school(school_name):
    """
    학교 이름으로 나이스 학교 정보를 검색한다.
    """

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "SCHUL_NM": school_name
    }

    data = safe_get_json(SCHOOL_API, params)

    if not data:
        return None

    if "schoolInfo" not in data:
        return None

    try:
        rows = data["schoolInfo"][1]["row"]
    except (IndexError, KeyError, TypeError):
        return None

    # 정확한 학교명 우선
    exact_match = None

    for row in rows:
        name = row.get("SCHUL_NM", "").strip()

        if name == school_name:
            exact_match = row
            break

    # 정확히 일치하는 학교가 있으면 사용
    if exact_match:
        row = exact_match
    elif rows:
        # 없으면 첫 번째 결과
        row = rows[0]
    else:
        return None

    return {
        "school_name": row.get("SCHUL_NM", ""),
        "office_code": row.get("ATPT_OFCDC_SC_CODE", ""),
        "school_code": row.get("SD_SCHUL_CODE", ""),
        "region": row.get("LCTN_SC_NM", "")
    }


# =========================================================
# 4. 급식 데이터 가져오기
# =========================================================

@st.cache_data(ttl=3600)
def get_meals(school_info, start_date, end_date):
    """
    특정 학교의 지정 기간 중식 데이터를 가져온다.
    """

    if not school_info:
        return []

    params = {
        "Type": "json",
        "pIndex": 1,
        "pSize": 1000,
        "ATPT_OFCDC_SC_CODE": school_info["office_code"],
        "SD_SCHUL_CODE": school_info["school_code"],
        "MMEAL_SC_CODE": "2",
        "MLSV_FROM_YMD": start_date,
        "MLSV_TO_YMD": end_date
    }

    data = safe_get_json(MEAL_API, params)

    if not data:
        return []

    if "mealServiceDietInfo" not in data:
        return []

    try:
        rows = data["mealServiceDietInfo"][1]["row"]
        return rows

    except (IndexError, KeyError, TypeError):
        return []


# =========================================================
# 5. 메뉴 정리
# =========================================================

def clean_menu(menu_text):
    """
    <br/> 등을 줄바꿈으로 바꾸고 불필요한 공백을 제거한다.
    """

    if not menu_text:
        return ""

    text = menu_text.replace("<br/>", "\n")
    text = text.replace("<br>", "\n")
    text = text.replace("<BR/>", "\n")

    return text.strip()


def split_menus(menu_text):
    """
    하나의 급식 문자열을 개별 메뉴로 분리한다.
    """

    text = clean_menu(menu_text)

    if not text:
        return []

    menus = text.split("\n")

    result = []

    for menu in menus:
        menu = menu.strip()

        if menu:
            result.append(menu)

    return result


# =========================================================
# 6. 알레르기 번호 추출
# =========================================================

def extract_allergy_numbers(menu):
    """
    메뉴 뒤의 괄호 안 알레르기 번호를 추출한다.

    예:
    새우볶음밥(1.5.6.9)
    -> ['1', '5', '6', '9']
    """

    numbers = set()

    matches = re.findall(r"\(([^()]*)\)", menu)

    for match in matches:

        # 1.5.6.9 형태
        found = re.findall(r"\d+", match)

        for number in found:
            numbers.add(number)

    return numbers


# =========================================================
# 7. 갑각류 판단
# =========================================================

def get_crustacean_info(menu):
    """
    갑각류 알레르기 여부를 판단한다.

    8 = 게
    9 = 새우
    """

    allergies = extract_allergy_numbers(menu)

    result = []

    if "8" in allergies:
        result.append("게")

    if "9" in allergies:
        result.append("새우")

    return result


# =========================================================
# 8. 디저트 판별
# =========================================================

DESSERT_KEYWORDS = [
    "케이크",
    "케익",
    "쿠키",
    "과자",
    "빵",
    "롤",
    "파이",
    "머핀",
    "도넛",
    "도너츠",
    "아이스크림",
    "요거트",
    "요구르트",
    "푸딩",
    "젤리",
    "마카롱",
    "초콜릿",
    "사탕",
    "떡",
    "송편",
    "약과",
    "호떡",
    "와플",
    "팬케이크",
    "핫케이크",
    "과일",
    "사과",
    "배",
    "귤",
    "오렌지",
    "딸기",
    "포도",
    "수박",
    "참외",
    "바나나",
    "키위",
    "복숭아",
    "파인애플",
    "메론",
    "멜론",
    "음료",
    "주스",
    "쥬스",
    "에이드",
    "차",
    "식혜",
    "수정과",
    "요구르트",
    "두유",
    "우유"
]


def is_dessert(menu):
    """
    메뉴명에 디저트 관련 키워드가 포함되어 있는지 확인한다.
    """

    menu_clean = re.sub(r"\([^)]*\)", "", menu)

    for keyword in DESSERT_KEYWORDS:
        if keyword in menu_clean:
            return True

    return False


# =========================================================
# 9. 김치 판별
# =========================================================

KIMCHI_KEYWORDS = [
    "김치",
    "깍두기",
    "총각김치",
    "열무김치",
    "백김치",
    "배추김치",
    "겉절이",
    "동치미",
    "나박김치",
    "갓김치",
    "파김치",
    "오이김치",
    "부추김치",
    "깻잎김치",
    "무김치"
]


def is_kimchi(menu):
    """
    김치류 메뉴인지 확인한다.
    """

    for keyword in KIMCHI_KEYWORDS:
        if keyword in menu:
            return True

    return False


def classify_kimchi(menu):
    """
    김치의 구체적인 종류를 추정한다.
    """

    priority = [
        "총각김치",
        "배추김치",
        "깍두기",
        "열무김치",
        "백김치",
        "동치미",
        "나박김치",
        "갓김치",
        "파김치",
        "오이김치",
        "부추김치",
        "깻잎김치",
        "무김치",
        "겉절이",
        "김치"
    ]

    for keyword in priority:
        if keyword in menu:
            return keyword

    return "기타"


# =========================================================
# 10. 전체 데이터 분석
# =========================================================

def make_dataframe(all_school_meals):

    records = []

    for school_name, rows in all_school_meals.items():

        for row in rows:

            meal_date = row.get("MLSV_YMD", "")
            menu_text = row.get("DDISH_NM", "")
            calories = row.get("CAL_INFO", "")

            menus = split_menus(menu_text)

            for menu in menus:

                crustaceans = get_crustacean_info(menu)

                record = {
                    "학교": school_name,
                    "날짜": meal_date,
                    "메뉴": menu,
                    "칼로리": calories,
                    "갑각류": ", ".join(crustaceans),
                    "갑각류알레르기": len(crustaceans) > 0,
                    "디저트": is_dessert(menu),
                    "김치": is_kimchi(menu),
                    "김치종류": classify_kimchi(menu) if is_kimchi(menu) else ""
                }

                records.append(record)

    if not records:
        return pd.DataFrame()

    df = pd.DataFrame(records)

    df["날짜"] = pd.to_datetime(
        df["날짜"],
        format="%Y%m%d",
        errors="coerce"
    )

    return df


# =========================================================
# 11. 학교 정보 확인
# =========================================================

st.subheader("🏫 학교 정보")

school_infos = {}

info_cols = st.columns(3)

for idx, school_name in enumerate(SCHOOL_NAMES):

    with info_cols[idx]:

        info = find_school(school_name)

        if info:

            school_infos[school_name] = info

            st.success(f"**{school_name}**")
            st.write(f"교육청 코드: `{info['office_code']}`")
            st.write(f"학교 코드: `{info['school_code']}`")
            st.write(f"지역: {info['region']}")

        else:

            st.error(
                f"{school_name}의 학교 정보를 찾지 못했습니다."
            )


# =========================================================
# 12. 데이터 가져오기 버튼
# =========================================================

st.divider()

st.subheader("📥 2026년 급식 데이터")

st.info(
    "2026년 1월 1일부터 12월 31일까지의 **중식** 데이터를 조회합니다."
)

load_data = st.button(
    "🚀 급식 데이터 불러오기",
    type="primary",
    use_container_width=True
)


# =========================================================
# 13. 데이터 불러오기
# =========================================================

if load_data:

    if len(school_infos) == 0:

        st.error("학교 정보를 가져오지 못했습니다.")

    else:

        progress = st.progress(0)
        status = st.empty()

        all_school_meals = {}

        total = len(school_infos)

        for idx, school_name in enumerate(school_infos):

            status.info(
                f"🔎 {school_name} 급식 데이터를 가져오는 중..."
            )

            rows = get_meals(
                school_infos[school_name],
                START_DATE,
                END_DATE
            )

            all_school_meals[school_name] = rows

            progress.progress(
                (idx + 1) / total
            )

        status.success("✅ 모든 학교의 데이터를 불러왔습니다.")

        df = make_dataframe(all_school_meals)

        if df.empty:

            st.warning(
                "조회된 급식 데이터가 없습니다."
            )

        else:

            st.session_state["meal_df"] = df


# =========================================================
# 14. 데이터 표시
# =========================================================

if "meal_df" in st.session_state:

    df = st.session_state["meal_df"]

    st.divider()

    st.subheader("📊 전체 데이터")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "학교 수",
            df["학교"].nunique()
        )

    with col2:
        st.metric(
            "급식 메뉴 수",
            len(df)
        )

    with col3:
        st.metric(
            "갑각류 포함 메뉴",
            int(df["갑각류알레르기"].sum())
        )

    with col4:
        st.metric(
            "김치 메뉴",
            int(df["김치"].sum())
        )


    # =====================================================
    # 15. 갑각류 알레르기 분석
    # =====================================================

    st.divider()

    st.header("🦀 1. 갑각류 알레르기 분석")

    crust_df = (
        df[df["갑각류알레르기"]]
        .groupby(["학교", "갑각류"])
        .size()
        .reset_index(name="횟수")
    )

    if crust_df.empty:

        st.info(
            "갑각류 알레르기 번호(8=게, 9=새우)가 포함된 메뉴가 없습니다."
        )

    else:

        chart_crust = (
            crust_df
            .pivot(
                index="학교",
                columns="갑각류",
                values="횟수"
            )
            .fillna(0)
        )

        st.bar_chart(chart_crust)

        st.dataframe(
            crust_df,
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "※ 나이스 급식 데이터에서 8은 게, 9는 새우를 의미합니다."
        )


    # =====================================================
    # 16. 디저트 분석
    # =====================================================

    st.divider()

    st.header("🍰 2. 디저트 종류 비교")

    dessert_df = df[df["디저트"]].copy()

    if dessert_df.empty:

        st.info("디저트로 분류된 메뉴가 없습니다.")

    else:

        dessert_count = (
            dessert_df
            .groupby("학교")
            .size()
            .reset_index(name="횟수")
        )

        st.subheader("학교별 디저트 제공 횟수")

        st.bar_chart(
            dessert_count.set_index("학교")
        )

        st.subheader("학교별 디저트 메뉴")

        dessert_menu_count = (
            dessert_df
            .groupby(["학교", "메뉴"])
            .size()
            .reset_index(name="횟수")
            .sort_values(
                ["학교", "횟수"],
                ascending=[True, False]
            )
        )

        st.dataframe(
            dessert_menu_count,
            use_container_width=True,
            hide_index=True
        )


    # =====================================================
    # 17. 김치 분석
    # =====================================================

    st.divider()

    st.header("🥬 3. 김치 종류 비교")

    kimchi_df = df[df["김치"]].copy()

    if kimchi_df.empty:

        st.info("김치로 분류된 메뉴가 없습니다.")

    else:

        kimchi_count = (
            kimchi_df
            .groupby(["학교", "김치종류"])
            .size()
            .reset_index(name="횟수")
        )

        st.subheader("학교별 김치 종류")

        kimchi_chart = (
            kimchi_count
            .pivot(
                index="학교",
                columns="김치종류",
                values="횟수"
            )
            .fillna(0)
        )

        st.bar_chart(kimchi_chart)

        st.dataframe(
            kimchi_count.sort_values(
                ["학교", "횟수"],
                ascending=[True, False]
            ),
            use_container_width=True,
            hide_index=True
        )


    # =====================================================
    # 18. 학교별 종합 비교
    # =====================================================

    st.divider()

    st.header("📈 4. 세 학교 종합 비교")

    summary = []

    for school in SCHOOL_NAMES:

        school_df = df[df["학교"] == school]

        summary.append({
            "학교": school,
            "전체 메뉴 수": len(school_df),
            "갑각류 포함": int(
                school_df["갑각류알레르기"].sum()
            ),
            "디저트": int(
                school_df["디저트"].sum()
            ),
            "김치": int(
                school_df["김치"].sum()
            )
        })

    summary_df = pd.DataFrame(summary)

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("학교별 비교 그래프")

    comparison_df = summary_df.set_index("학교")

    st.bar_chart(comparison_df)


    # =====================================================
    # 19. 날짜별 급식 조회
    # =====================================================

    st.divider()

    st.header("📅 5. 날짜별 급식 확인")

    available_dates = sorted(
        df["날짜"].dropna().dt.date.unique()
    )

    if available_dates:

        selected_date = st.date_input(
            "조회할 날짜",
            value=available_dates[0],
            min_value=min(available_dates),
            max_value=max(available_dates)
        )

        date_df = df[
            df["날짜"].dt.date == selected_date
        ]

        for school in SCHOOL_NAMES:

            st.subheader(f"🏫 {school}")

            school_date_df = date_df[
                date_df["학교"] == school
            ]

            if school_date_df.empty:

                st.info("해당 날짜의 급식 정보가 없습니다.")

            else:

                for _, row in school_date_df.iterrows():

                    menu = row["메뉴"]

                    badges = []

                    if row["갑각류알레르기"]:
                        badges.append(
                            f"🦀 {row['갑각류']}"
                        )

                    if row["디저트"]:
                        badges.append("🍰 디저트")

                    if row["김치"]:
                        badges.append(
                            f"🥬 {row['김치종류']}"
                        )

                    badge_text = " · ".join(badges)

                    if badge_text:
                        st.write(
                            f"- **{menu}**  \n"
                            f"  {badge_text}"
                        )
                    else:
                        st.write(f"- {menu}")


    # =====================================================
    # 20. 원본 데이터
    # =====================================================

    st.divider()

    st.header("📋 6. 전체 분석 데이터")

    display_df = df.copy()

    display_df["날짜"] = display_df["날짜"].dt.strftime(
        "%Y-%m-%d"
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        height=500,
        hide_index=True
    )


    # =====================================================
    # 21. CSV 다운로드
    # =====================================================

    st.divider()

    st.header("📥 7. 데이터 다운로드")

    csv_data = df.copy()

    csv_data["날짜"] = csv_data["날짜"].dt.strftime(
        "%Y-%m-%d"
    )

    csv_bytes = csv_data.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")

    st.download_button(
        label="⬇️ 분석 결과 CSV 다운로드",
        data=csv_bytes,
        file_name="2026_세학교_급식_분석.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================================================
# 22. 안내
# =========================================================

st.divider()

with st.expander("ℹ️ 분석 방법 및 주의사항"):

    st.markdown(
        """
### 데이터 출처

교육부·시도교육청 **나이스 교육정보 개방 포털(NEIS)**의
급식식단정보 API를 사용합니다.

### 갑각류 알레르기

나이스 급식 데이터의 알레르기 번호를 이용합니다.

- **8 = 게**
- **9 = 새우**

따라서 메뉴 뒤 괄호에 `8` 또는 `9`가 있으면
갑각류 알레르기 관련 메뉴로 분류합니다.

### 디저트

메뉴명에 과일, 빵, 떡, 아이스크림, 음료,
케이크, 쿠키 등의 키워드가 포함되어 있는지를
기준으로 분류합니다.

### 김치

메뉴명에 김치, 깍두기, 총각김치, 열무김치,
백김치, 동치미 등의 표현이 포함되어 있는지를
기준으로 분류합니다.

### 주의

디저트와 김치 분류는 메뉴 이름을 기준으로 한
**키워드 기반 분석**입니다.

따라서 실제 학교에서 후식으로 제공한 음식이나
김치류와 완전히 일치하지 않을 수 있습니다.
"""
    )
