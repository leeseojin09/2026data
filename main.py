
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="KOBIS 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 KOBIS 박스오피스 분석")


# =========================================================
# 2. 한국 시간 설정
# =========================================================
# 배포 서버가 한국 시간이 아닐 수 있기 때문에
# UTC+9를 직접 지정합니다.

KST = timezone(timedelta(hours=9))


# =========================================================
# 3. KOBIS 인증키 가져오기
# =========================================================
# Streamlit Cloud의 Secrets에
#
# KOBIS_KEY = "본인의 인증키"
#
# 를 등록해 둡니다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        "❌ KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud → Settings → Secrets에서 "
        "`KOBIS_KEY`가 등록되어 있는지 확인하세요."
    )
    st.stop()


# =========================================================
# 4. KOBIS API 주소
# =========================================================

API_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)


# =========================================================
# 5. 하루 박스오피스 데이터를 가져오는 함수
# =========================================================
# 같은 날짜를 다시 요청하면 1시간 동안 캐시된 데이터를 사용합니다.
#
# ttl=3600
# → 3600초 = 1시간

@st.cache_data(ttl=3600)
def get_boxoffice(api_key, target_date):

    params = {
        "key": api_key,
        "targetDt": target_date
    }

    try:
        response = requests.get(
            API_URL,
            params=params,
            timeout=10
        )

        # 인터넷 연결 등의 문제가 있으면 오류 발생
        response.raise_for_status()

        data = response.json()

    except requests.exceptions.RequestException as e:

        return None, (
            "KOBIS API에 접속하지 못했습니다.\n\n"
            "인터넷 연결 또는 KOBIS API 서버 상태를 확인하세요.\n\n"
            f"오류 내용: {e}"
        )

    except ValueError:

        return None, (
            "KOBIS API에서 올바른 JSON 데이터를 "
            "받지 못했습니다."
        )


    # =====================================================
    # 6. faultInfo 확인
    # =====================================================
    # KOBIS는 인증키가 틀려도 HTTP 상태코드가 200일 수 있습니다.
    # 따라서 faultInfo가 있는지 반드시 확인합니다.

    if "faultInfo" in data:

        fault = data["faultInfo"]

        code = fault.get(
            "faultCode",
            "알 수 없음"
        )

        message = fault.get(
            "message",
            "알 수 없는 오류"
        )

        return None, (
            "KOBIS API에서 오류를 반환했습니다.\n\n"
            f"오류 코드: {code}\n"
            f"오류 내용: {message}\n\n"
            "KOBIS_KEY가 정확한지 확인하세요."
        )


    # =====================================================
    # 7. boxOfficeResult 확인
    # =====================================================

    if "boxOfficeResult" not in data:

        return None, (
            "API 응답에 boxOfficeResult가 없습니다.\n"
            "KOBIS API 상태를 확인하세요."
        )


    result = data["boxOfficeResult"]


    # 영화 목록 가져오기
    movie_list = result.get(
        "dailyBoxOfficeList",
        []
    )


    # 영화 목록이 비어 있으면 안내
    if not movie_list:

        return None, (
            f"{target_date}의 박스오피스 데이터가 없습니다.\n\n"
            "해당 날짜의 박스오피스가 집계되었는지 "
            "확인하세요."
        )


    # =====================================================
    # 8. 숫자 데이터를 숫자로 변환
    # =====================================================
    # KOBIS API에서는 숫자가 문자열로 들어옵니다.
    # 따라서 int()를 이용해 숫자로 변환합니다.

    for movie in movie_list:

        movie["rank"] = int(
            movie.get("rank", 0)
        )

        movie["audiCnt"] = int(
            movie.get("audiCnt", 0)
        )

        movie["audiAcc"] = int(
            movie.get("audiAcc", 0)
        )

        movie["scrnCnt"] = int(
            movie.get("scrnCnt", 0)
        )

        movie["showCnt"] = int(
            movie.get("showCnt", 0)
        )


    return movie_list, None


# =========================================================
# 9. 어제 날짜 계산
# =========================================================

now_kst = datetime.now(KST)

yesterday = now_kst - timedelta(days=1)

yesterday_string = yesterday.strftime("%Y%m%d")

yesterday_display = yesterday.strftime(
    "%Y년 %m월 %d일"
)


# =========================================================
# 10. 메뉴
# =========================================================

menu = st.sidebar.radio(
    "📌 보고 싶은 통계를 선택하세요",
    [
        "어제의 박스오피스",
        "2025년 8월 통계"
    ]
)


# =========================================================
# =========================================================
# 11. 어제의 박스오피스
# =========================================================
# =========================================================

if menu == "어제의 박스오피스":

    st.header(
        f"📅 {yesterday_display} 박스오피스"
    )


    # API 호출
    movies, error_message = get_boxoffice(
        KOBIS_KEY,
        yesterday_string
    )


    # 오류 처리
    if error_message:

        st.error(error_message)

        st.info(
            "💡 다음 사항을 확인해 보세요.\n\n"
            "1. KOBIS_KEY가 정확한지 확인\n"
            "2. KOBIS API 서버 상태 확인\n"
            "3. 해당 날짜의 박스오피스 집계 여부 확인"
        )

        st.stop()


    # 순위순으로 정렬
    movies.sort(
        key=lambda x: x["rank"]
    )


    # -----------------------------------------------------
    # 1위 영화
    # -----------------------------------------------------

    first_movie = movies[0]

    movie_name = first_movie["movieNm"]

    st.subheader(
        f"🥇 1위: {movie_name}"
    )


    # -----------------------------------------------------
    # 3개의 지표 카드
    # -----------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🎟️ 일일 관객수",
            f'{first_movie["audiCnt"]:,}명'
        )


    with col2:

        st.metric(
            "👥 누적 관객수",
            f'{first_movie["audiAcc"]:,}명'
        )


    with col3:

        st.metric(
            "🖥️ 스크린수",
            f'{first_movie["scrnCnt"]:,}개'
        )


    # -----------------------------------------------------
    # 전체 영화 표
    # -----------------------------------------------------

    st.subheader("📋 전체 박스오피스")

    table = []

    for movie in movies:

        table.append({
            "순위": movie["rank"],
            "영화명": movie["movieNm"],
            "개봉일": movie["openDt"],
            "관객수": movie["audiCnt"],
            "누적관객": movie["audiAcc"],
            "스크린수": movie["scrnCnt"]
        })


    df = pd.DataFrame(table)


    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


    # -----------------------------------------------------
    # 관객수 TOP 5
    # -----------------------------------------------------

    st.subheader("📈 관객수 상위 5편")

    top5 = sorted(
        movies,
        key=lambda x: x["audiCnt"],
        reverse=True
    )[:5]


    chart_data = pd.DataFrame({
        "영화명": [
            movie["movieNm"]
            for movie in top5
        ],
        "관객수": [
            movie["audiCnt"]
            for movie in top5
        ]
    })


    # 영화명을 인덱스로 설정
    chart_data = chart_data.set_index("영화명")


    st.bar_chart(
        chart_data
    )


# =========================================================
# =========================================================
# 12. 2025년 8월 통계
# =========================================================
# =========================================================

else:

    st.header("📊 2025년 8월 박스오피스 통계")

    st.write(
        "2025년 8월 1일부터 8월 31일까지의 "
        "일별 박스오피스 데이터를 분석합니다."
    )


    # -----------------------------------------------------
    # 2025년 8월 날짜 만들기
    # -----------------------------------------------------

    start_date = datetime(
        2025,
        8,
        1
    )

    end_date = datetime(
        2025,
        8,
        31
    )


    # 날짜별 결과를 저장할 리스트
    daily_results = []

    # 모든 영화 데이터를 저장할 리스트
    all_movies = []


    # -----------------------------------------------------
    # 8월 1일부터 31일까지 반복
    # -----------------------------------------------------

    current_date = start_date


    progress = st.progress(0)

    total_days = 31

    day_number = 0


    while current_date <= end_date:

        target_date = current_date.strftime(
            "%Y%m%d"
        )

        display_date = current_date.strftime(
            "%m월 %d일"
        )


        # 하루의 데이터 가져오기
        movies, error_message = get_boxoffice(
            KOBIS_KEY,
            target_date
        )


        # -------------------------------------------------
        # 특정 날짜에 문제가 생긴 경우
        # -------------------------------------------------

        if error_message:

            st.warning(
                f"⚠️ {display_date} 데이터를 가져오지 못했습니다.\n\n"
                f"{error_message}"
            )

        else:

            # 순위순 정렬
            movies.sort(
                key=lambda x: x["rank"]
            )


            # ---------------------------------------------
            # 해당 날짜의 1위 영화
            # ---------------------------------------------

            first_movie = movies[0]


            daily_results.append({
                "날짜": display_date,
                "1위 영화": first_movie["movieNm"],
                "관객수": first_movie["audiCnt"],
                "스크린수": first_movie["scrnCnt"]
            })


            # ---------------------------------------------
            # 모든 영화 데이터 저장
            # ---------------------------------------------

            for movie in movies:

                all_movies.append({
                    "날짜": display_date,
                    "영화명": movie["movieNm"],
                    "순위": movie["rank"],
                    "관객수": movie["audiCnt"],
                    "누적관객": movie["audiAcc"],
                    "스크린수": movie["scrnCnt"]
                })


        # 진행률 업데이트
        day_number += 1

        progress.progress(
            day_number / total_days
        )


        # 다음 날짜로 이동
        current_date += timedelta(days=1)


    # 진행률 표시 제거
    progress.empty()


    # -----------------------------------------------------
    # 데이터가 하나도 없는 경우
    # -----------------------------------------------------

    if not daily_results:

        st.error(
            "❌ 2025년 8월 박스오피스 데이터를 "
            "하나도 가져오지 못했습니다."
        )

        st.info(
            "KOBIS_KEY, API 서버 상태, "
            "네트워크 연결을 확인하세요."
        )

        st.stop()


    # -----------------------------------------------------
    # DataFrame으로 변환
    # -----------------------------------------------------

    daily_df = pd.DataFrame(
        daily_results
    )

    all_movies_df = pd.DataFrame(
        all_movies
    )


    # =====================================================
    # 13. 8월 핵심 통계
    # =====================================================

    st.subheader("🏆 8월 핵심 통계")


    # 영화별 8월 일일 관객수 합계
    movie_audience = (
        all_movies_df
        .groupby("영화명")["관객수"]
        .sum()
        .sort_values(
            ascending=False
        )
    )


    # 8월 동안 가장 많은 일일 관객수를 기록한 영화
    top_movie = movie_audience.index[0]

    top_movie_audience = movie_audience.iloc[0]


    # 1위 영화가 차지한 날짜 수
    first_place_count = (
        daily_df["1위 영화"]
        .value_counts()
    )


    first_place_movie = first_place_count.index[0]

    first_place_days = first_place_count.iloc[0]


    # 전체 일일 관객수
    total_daily_audience = (
        all_movies_df["관객수"].sum()
    )


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "🥇 8월 관객수 TOP 1",
            top_movie
        )

        st.caption(
            f"일일 관객수 합계: "
            f"{top_movie_audience:,}명"
        )


    with col2:

        st.metric(
            "🏆 1위 최다 기록",
            first_place_movie
        )

        st.caption(
            f"1위 기록: {first_place_days}일"
        )


    with col3:

        st.metric(
            "👥 8월 전체 일일 관객수",
            f"{total_daily_audience:,}명"
        )


    # =====================================================
    # 14. 영화별 8월 관객수 TOP 10
    # =====================================================

    st.subheader("🎬 2025년 8월 관객수 TOP 10")


    top10_df = (
        movie_audience
        .head(10)
        .reset_index()
    )


    top10_df.columns = [
        "영화명",
        "8월 일일 관객수 합계"
    ]


    # 표로 보여주기
    display_top10 = top10_df.copy()

    display_top10[
        "8월 일일 관객수 합계"
    ] = display_top10[
        "8월 일일 관객수 합계"
    ].map(
        lambda x: f"{x:,}명"
    )


    st.dataframe(
        display_top10,
        use_container_width=True,
        hide_index=True
    )


    # -----------------------------------------------------
    # TOP 10 막대그래프
    # -----------------------------------------------------

    chart_top10 = top10_df.set_index(
        "영화명"
    )


    st.bar_chart(
        chart_top10
    )


    # =====================================================
    # 15. 날짜별 총 관객수
    # =====================================================

    st.subheader("📈 날짜별 박스오피스 관객수")


    daily_total = (
        all_movies_df
        .groupby("날짜")["관객수"]
        .sum()
    )


    # 날짜 순서를 8월 1일 → 31일 순으로 맞춤
    date_order = daily_df["날짜"].tolist()

    daily_total = daily_total.reindex(
        date_order
    )


    daily_total_df = pd.DataFrame({
        "총 관객수": daily_total
    })


    st.line_chart(
        daily_total_df
    )


    # =====================================================
    # 16. 날짜별 1위 영화
    # =====================================================

    st.subheader("🥇 날짜별 1위 영화")


    st.dataframe(
        daily_df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # 17. 날짜별 1위 영화 변화
    # =====================================================

    st.subheader("🔄 8월 1위 영화 변화")


    # 영화별로 1위를 차지한 횟수 계산
    winner_count = (
        daily_df["1위 영화"]
        .value_counts()
        .reset_index()
    )


    winner_count.columns = [
        "영화명",
        "1위 횟수"
    ]


    st.dataframe(
        winner_count,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # 18. 안내
    # =====================================================

    st.info(
        "ℹ️ '8월 일일 관객수 합계'는 KOBIS에서 제공하는 "
        "각 날짜의 일일 관객수를 영화별로 합산한 값입니다. "
        "KOBIS의 '누적관객'과는 다른 지표입니다."
    )
```
