import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 기본 설정
# ---------------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")

# ---------------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 날짜 계산
# ---------------------------------------------------------
# 배포 서버의 시간이 한국 시간이 아닐 수 있으므로
# UTC+9 시간대를 직접 사용합니다.

KST = timezone(timedelta(hours=9))
now_kst = datetime.now(KST)

# 오늘에서 하루를 빼면 '어제'가 됩니다.
yesterday = now_kst - timedelta(days=1)

# KOBIS API가 요구하는 날짜 형식: YYYYMMDD
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여줄 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")

st.subheader(f"📅 {display_date} 박스오피스")


# ---------------------------------------------------------
# 3. KOBIS 인증키 가져오기
# ---------------------------------------------------------
# Streamlit Cloud의 Secrets에
# KOBIS_KEY = "발급받은 인증키"
# 형태로 저장해 둡니다.
#
# 인증키를 코드에 직접 적지 않습니다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error(
        "❌ KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud의 Settings → Secrets에서 "
        "`KOBIS_KEY`가 정확하게 등록되어 있는지 확인하세요."
    )
    st.stop()


# ---------------------------------------------------------
# 4. KOBIS API 주소
# ---------------------------------------------------------

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# ---------------------------------------------------------
# 5. API에서 데이터 가져오는 함수
# ---------------------------------------------------------
# @st.cache_data를 사용하면 같은 날짜의 데이터를
# 일정 시간 동안 저장해 두었다가 다시 사용합니다.
#
# ttl=3600 → 3600초 = 약 1시간

@st.cache_data(ttl=3600)
def get_boxoffice(api_key, target_dt):

    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        # HTTP 요청 자체가 실패한 경우
        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:
        return None, (
            "KOBIS API에 접속하지 못했습니다.\n\n"
            "인터넷 연결이나 KOBIS API 서버 상태를 확인해 주세요.\n\n"
            f"오류 내용: {e}"
        )

    except ValueError:
        return None, (
            "KOBIS API에서 올바른 JSON 데이터를 받지 못했습니다.\n"
            "KOBIS API의 응답 상태를 확인해 주세요."
        )

    # -----------------------------------------------------
    # 6. 인증키 오류 등 faultInfo 확인
    # -----------------------------------------------------
    # KOBIS는 인증키가 잘못되어도 HTTP 상태코드가 200일 수 있습니다.
    # 따라서 반드시 faultInfo가 있는지 확인해야 합니다.

    if "faultInfo" in data:
        fault_info = data["faultInfo"]

        fault_code = fault_info.get("faultCode", "알 수 없음")
        fault_message = fault_info.get("message", "알 수 없는 오류")

        return None, (
            "KOBIS API에서 오류를 반환했습니다.\n\n"
            f"오류 코드: {fault_code}\n"
            f"오류 내용: {fault_message}\n\n"
            "Streamlit Secrets의 KOBIS_KEY가 정확한지 확인하세요."
        )

    # -----------------------------------------------------
    # 7. boxOfficeResult 확인
    # -----------------------------------------------------

    if "boxOfficeResult" not in data:
        return None, (
            "KOBIS API 응답에 boxOfficeResult가 없습니다.\n"
            "API 주소와 요청 날짜, KOBIS API 상태를 확인해 주세요."
        )

    boxoffice = data["boxOfficeResult"]

    # 영화 목록 가져오기
    movie_list = boxoffice.get("dailyBoxOfficeList", [])

    # 영화 목록이 비어 있는 경우
    if not movie_list:
        return None, (
            f"{display_date}의 박스오피스 영화 목록이 없습니다.\n\n"
            "조회 날짜가 정상적인지, KOBIS에서 해당 날짜의 "
            "일일 박스오피스가 집계되었는지 확인해 주세요."
        )

    return movie_list, None


# ---------------------------------------------------------
# 8. API 호출
# ---------------------------------------------------------

movies, error_message = get_boxoffice(KOBIS_KEY, target_date)


# ---------------------------------------------------------
# 9. 오류가 발생하면 사용자에게 안내
# ---------------------------------------------------------

if error_message:
    st.error(error_message)
    st.info(
        "💡 확인할 사항\n"
        "1. Streamlit Secrets에 KOBIS_KEY가 등록되어 있는지\n"
        "2. KOBIS 인증키가 유효한지\n"
        "3. KOBIS API 서버에 문제가 없는지\n"
        "4. 해당 날짜의 박스오피스 데이터가 존재하는지"
    )
    st.stop()


# ---------------------------------------------------------
# 10. 숫자 데이터를 숫자형으로 변환
# ---------------------------------------------------------
# KOBIS API는 숫자를 문자열로 보내기 때문에
# int()를 사용하여 실제 숫자로 바꿉니다.

for movie in movies:

    movie["rank"] = int(movie.get("rank", 0))
    movie["audiCnt"] = int(movie.get("audiCnt", 0))
    movie["audiAcc"] = int(movie.get("audiAcc", 0))
    movie["scrnCnt"] = int(movie.get("scrnCnt", 0))


# ---------------------------------------------------------
# 11. 순위 기준으로 정렬
# ---------------------------------------------------------

movies.sort(key=lambda x: x["rank"])


# ---------------------------------------------------------
# 12. 1위 영화 정보
# ---------------------------------------------------------

first_movie = movies[0]

movie_name = first_movie.get("movieNm", "알 수 없음")
today_audience = first_movie["audiCnt"]
total_audience = first_movie["audiAcc"]
screen_count = first_movie["scrnCnt"]

open_date = first_movie.get("openDt", "-")

st.markdown(f"## 🥇 1위: {movie_name}")

st.caption(f"개봉일: {open_date}")


# ---------------------------------------------------------
# 13. 1위 영화의 주요 지표 카드 3개
# ---------------------------------------------------------

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🎟️ 일일 관객수",
        f"{today_audience:,}명"
    )

with col2:
    st.metric(
        "👥 누적 관객수",
        f"{total_audience:,}명"
    )

with col3:
    st.metric(
        "🖥️ 스크린수",
        f"{screen_count:,}개"
    )


# ---------------------------------------------------------
# 14. 전체 영화 데이터를 표로 만들기
# ---------------------------------------------------------

st.markdown("## 📊 전체 박스오피스")

table_data = []

for movie in movies:
    table_data.append({
        "순위": movie["rank"],
        "영화명": movie.get("movieNm", "-"),
        "개봉일": movie.get("openDt", "-"),
        "관객수": movie["audiCnt"],
        "누적관객": movie["audiAcc"],
        "스크린수": movie["scrnCnt"]
    })

st.dataframe(
    table_data,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 15. 관객수 상위 5편 막대그래프
# ---------------------------------------------------------

st.markdown("## 📈 관객수 상위 5편")

# 관객수가 많은 순서로 정렬
top5 = sorted(
    movies,
    key=lambda x: x["audiCnt"],
    reverse=True
)[:5]

# Streamlit의 막대그래프에 사용할 데이터
chart_data = {
    movie["movieNm"]: movie["audiCnt"]
    for movie in top5
}

st.bar_chart(chart_data)

st.caption(
    "※ 막대그래프는 해당 날짜의 일일 관객수를 기준으로 "
    "상위 5편을 표시합니다."
)
