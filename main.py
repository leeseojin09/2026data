import streamlit as st
import requests
import re
from datetime import datetime, timedelta

# 페이지 기본 설정
st.set_page_config(
    page_title="인천 3개 고교 급식 비교 분석기",
    page_icon="🍱",
    layout="wide"
)

st.title("🍱 부평고 · 산곡고 · 세일고 급식 비교 분석기")
st.caption("나이스(NEIS) 오픈 API를 활용하여 디저트, 갑각류 알레르기(9, 17번), 김치 종류를 분석합니다.")

# 사이드바 설정
st.sidebar.header("⚙️ 조회 설정")

# 1. API 키 입력 (선택)
api_key = st.sidebar.text_input("나이스 OPEN API KEY (선택)", type="password", help="인증키가 없으면 1회 요청당 5건으로 제한됩니다.")

# 2. 날짜 범위 선택
today = datetime.today()
start_date = st.sidebar.date_input("조회 시작일", today - timedelta(days=30))
end_date = st.sidebar.date_input("조회 종료일", today)

from_ymd = start_date.strftime("%Y%m%d")
to_ymd = end_date.strftime("%Y%m%d")

# 학교 정보 사전 정의 (인천광역시교육청: E10)
SCHOOL_INFO = {
    "부평고등학교": {"office_code": "E10", "school_code": "7310058"},
    "산곡고등학교": {"office_code": "E10", "school_code": "7310243"},
    "세일고등학교": {"office_code": "E10", "school_code": "7310060"}
}

# 급식 데이터 가져오는 함수
@st.cache_data(ttl=3600)
def fetch_meal_data(office_code, school_code, from_date, to_date, key=None):
    url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
    params = {
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": office_code,
        "SD_SCHUL_CODE": school_code,
        "MMEAL_SC_CODE": "2",  # 중식
        "MLSV_FROM_YMD": from_date,
        "MLSV_TO_YMD": to_date,
        "pSize": 1000,
        "pIndex": 1
    }
    if key:
        params["KEY"] = key

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "mealServiceDietInfo" in data:
            rows = data["mealServiceDietInfo"][1]["row"]
            return rows
        else:
            return []
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return []

# 분석 함수
def analyze_meals(meals):
    kimchi_list = []
    shellfish_count = 0
    shellfish_menus = []
    dessert_list = []

    # 김치 패턴 (김치, 깍두기, 석박지, 겉절이 등)
    kimchi_pattern = re.compile(r'.*(김치|깍두기|석박지|겉절이|동치미).*')
    
    # 디저트 패턴 (음료, 케이크, 푸딩, 과일, 빵, 아이스크림, 와플 등)
    dessert_pattern = re.compile(r'.*(에이드|주스|음료|요구르트|라떼|케이크|파이|빵|와플|푸딩|아이스크림|슈|쿠키|떡|과일|사과|귤|바나나|멜론|포도|수박).*')

    for meal in meals:
        ddish_nm = meal.get("DDISH_NM", "")
        # <br/> 태그 기준으로 요리 분리
        dishes = ddish_nm.split("<br/>")
        
        for dish in dishes:
            dish_clean = dish.strip()
            
            # 1. 갑각류 알레르기 검사 (9: 새우, 17: 게)
            # 예: 새우튀김 (1.5.6.9)
            allergy_match = re.search(r'\(([\d\.]+)\)', dish_clean)
            if allergy_match:
                allergies = allergy_match.group(1).split('.')
                if '9' in allergies or '17' in allergies:
                    shellfish_count += 1
                    shellfish_menus.append(dish_clean)

            # 2. 김치 종류 수집
            dish_name_only = re.sub(r'\([\d\.]+\)', '', dish_clean).strip()
            if kimchi_pattern.match(dish_name_only):
                kimchi_list.append(dish_name_only)

            # 3. 디저트 종류 수집
            if dessert_pattern.match(dish_name_only) and not kimchi_pattern.match(dish_name_only):
                # 밥류/국류/반찬류 제외 보완
                if not any(keyword in dish_name_only for keyword in ["밥", "국", "찌개", "볶음", "무침", "조림"]):
                    dessert_list.append(dish_name_only)

    return {
        "kimchi": list(set(kimchi_list)),
        "shellfish_count": shellfish_count,
        "shellfish_menus": list(set(shellfish_menus)),
        "dessert": list(set(dessert_list)),
        "total_days": len(meals)
    }

# 실행 버튼
if st.sidebar.button("급식 정보 비교 조회"):
    st.subheader(f"📅 조회 기간: {start_date} ~ {end_date}")
    
    results = {}
    
    # 데이터 조회 및 분석
    for school_name, info in SCHOOL_INFO.items():
        meals = fetch_meal_data(info["office_code"], info["school_code"], from_ymd, to_ymd, api_key)
        results[school_name] = analyze_meals(meals)

    # 3개 학교 비교 컬럼 출력
    cols = st.columns(3)
    
    for idx, (school_name, result) in enumerate(results.items()):
        with cols[idx]:
            st.markdown(f"### 🏫 {school_name}")
            st.write(f"총 조회된 급식일: **{result['total_days']}일**")
            
            st.markdown("---")
            
            # 1. 갑각류 알레르기 정보
            st.markdown("#### 🦐 갑각류 알레르기 (9, 17번)")
            st.write(f"갑각류 포함 식단 횟수: **{result['shellfish_count']}회**")
            with st.expander("포함된 메뉴 보기"):
                if result['shellfish_menus']:
                    for menu in result['shellfish_menus']:
                        st.write(f"- {menu}")
                else:
                    st.write("해당 기간 내 갑각류 포함 메뉴가 없습니다.")

            st.markdown("---")

            # 2. 김치 종류
            st.markdown("#### 🥬 자주 나오는 김치 종류")
            if result['kimchi']:
                for k in result['kimchi'][:8]:  # 상위 8개만 표시
                    st.write(f"- {k}")
            else:
                st.write("조회된 김치 정보가 없습니다.")

            st.markdown("---")

            # 3. 디저트 종류
            st.markdown("#### 🍰 제공된 디저트 종류")
            if result['dessert']:
                for d in result['dessert'][:8]:  # 상위 8개만 표시
                    st.write(f"- {d}")
            else:
                st.write("조회된 디저트 정보가 없습니다.")

else:
    st.info("👈 왼쪽 사이드바에서 조회 기간을 설정한 후 **'급식 정보 비교 조회'** 버튼을 눌러주세요.")
