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
# Streamlit Cloud 서버가 한국 시간이 아닐 수 있기 때문에
# UTC+9를 직접 사용합니다.

KST = timezone(timedelta(hours=9))


# =========================================================
# 3. KOBIS 인증키 가져오기
# =========================================================
# Streamlit Cloud의 Secrets에 아래처럼 등록합니다.
#
# KOBIS_KEY = "본인의 인증키"
#
# 인증키를 코드에 직접 적지 않습니다.

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        "❌ KOBIS 인증키를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud → Settings → Secrets에서 "
        "`KOBIS_KEY`가 정확하게 등록되어 있는지 확인하세요."
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
# 같은 날짜를 다시 요청하면 약 1시간 동안
# 저장된 데이터를 사용합니다.
#
# ttl=3600 → 3600초 = 1시간

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
            "인터넷 연결 또는 KOBIS API 서버 상태를 "
            "확인해 주세요.\n\n"
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
    # KOBIS는 인증키가 틀려도 HTTP 200을 반환할 수 있으므로
    # faultInfo가 있는지 반드시 확인합니다.

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
            "KOBIS API 상태를 확인해 주세요."
        )


    result = data["boxOfficeResult"]


    # 영화 목록 가져오기
    movie_list = result.get(
        "dailyBoxOfficeList",
        []
    )


    # 영화 목록이 비어 있는 경우
    if not movie_list:

        return None, "EMPTY"


    # =====================================================
    # 8. 숫자 데이터를 숫자로 변환
    # =====================================================
    # KOBIS API에서는 숫자도 문자열로 전달됩니다.
    # int()를 이용하여 실제 숫자로 바꿉니다.

    for movie in movie_list:

        movie["rank"] = int(
            movie.get("rank", 0)
        )

        movie["rankInten"] = int(
            movie.get("rankInten", 0)
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
# 9. 한국 시간 기준 오늘과 어제 계산
# =========================================================

now_kst = datetime.now(KST)

today_kst = now_kst.date()

yesterday_kst = today_kst - timedelta(days=1)


# =========================================================
# 10. 메뉴
# =========================================================

menu = st.sidebar.radio(
    "📌 보고 싶은 통계를 선택하세요",
    [
        "날짜별 박스오피스",
        "2025년 8월 통계"
    ]
)


# =========================================================
# =========================================================
# 11. 날짜별 박스오피스
# =========================================================
# =========================================================

if menu == "날짜별 박스오피스":

    st.header("📅 날짜별 박스오피스")


    # -----------------------------------------------------
    # 날짜 선택
    # -----------------------------------------------------
    # 가장 최근에 선택할 수 있는 날짜는 어제입니다.
    # 오늘 날짜의 데이터는 아직 집계 전이므로 선택할 수 없습니다.

    selected_date = st.date_input(
        "조회할 날짜를 선택하세요.",
        value=yesterday_kst,
        min_value=datetime(
            2000,
            1,
            1
        ).date(),
        max_value=yesterday_kst
    )


    # 선택한 날짜를 KOBIS 형식으로 변환
    target_date = selected_date.strftime(
        "%Y%m%d"
    )

    display_date = selected_date.strftime(
        "%Y년 %m월 %d일"
    )


    st.subheader(
        f"🎬 {display_date} 박스오피스"
    )


    # -----------------------------------------------------
    # API 호출
    # -----------------------------------------------------

    movies, error_message = get_boxoffice(
        KOBIS_KEY,
        target_date
    )


    # -----------------------------------------------------
    # 데이터가 없는 경우
    # -----------------------------------------------------

    if error_message == "EMPTY":

        st.warning(
            "📭 그날은 아직 집계 전입니다."
        )

        st.info(
            "KOBIS에서 해당 날짜의 일일 박스오피스 "
            "데이터가 아직 제공되지 않았을 수 있습니다."
        )

        st.stop()


    # -----------------------------------------------------
    # API 오류
    # -----------------------------------------------------

    if error_message:

        st.error(error_message)

        st.info(
            "💡 다음 사항을 확인해 보세요.\n\n"
            "1. KOBIS_KEY가 정확한지 확인\n"
            "2. KOBIS API 서버 상태 확인\n"
            "3. 선택한 날짜가 정상적인 날짜인지 확인"
        )

        st.stop()


    # 순위순으로 정렬
    movies.sort(
        key=lambda x: x["rank"]
    )


    # =====================================================
    # 12. 1위 영화
    # =====================================================

    first_movie = movies[0]

    first_movie_name = first_movie["movieNm"]


    # 누적관객 100만 명 이상이면 👍 표시
    if first_movie["audiAcc"] > 1_000_000:

        first_movie_name += " 👍"


    st.subheader(
        f'🥇 1위: {first_movie_name}'
    )


    st.caption(
        f'개봉일: {first_movie.get("openDt", "-")}'
    )


    # =====================================================
    # 13. 1위 영화 지표 카드
    # =====================================================

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


    # =====================================================
    # 14. 전체 박스오피스 표
    # =====================================================

    st.subheader("📋 전체 박스오피스")


    table = []


    for movie in movies:

        # -------------------------------------------------
        # 순위 증감 표시
        # -------------------------------------------------
        #
        # rankInten > 0 : 순위가 오른 경우
        # rankInten < 0 : 순위가 내려간 경우
        # rankInten == 0 : 변동 없음
        #
        # 예:
        # ▲ 2
        # ▼ 1
        # -

        rank_change = movie["rankInten"]

        if rank_change > 0:

            rank_change_display = (
                f"🔺 {rank_change}"
            )

        elif rank_change < 0:

            rank_change_display = (
                f"🔻 {abs(rank_change)}"
            )

        else:

            rank_change_display = "-"


        # -------------------------------------------------
        # 누적관객 100만 명 이상이면 👍 표시
        # -----------------------------------------------------

        movie_name = movie["movieNm"]

        if movie["audiAcc"] > 1_000_000:

            movie_name += " 👍"


        # -------------------------------------------------
        # 표에 들어갈 데이터
        # -------------------------------------------------

        table.append({

            "순위":
                movie["rank"],

            "순위 변동":
                rank_change_display,

            "영화명":
                movie_name,

            "개봉일":
                movie.get(
                    "openDt",
                    "-"
                ),

            "관객수":
                movie["audiCnt"],

            "누적관객":
                movie["audiAcc"],

            "스크린수":
                movie["scrnCnt"]
        })


    df = pd.DataFrame(table)


    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


    st.caption(
        "🔺 빨간 위 화살표: 전날보다 순위 상승  "
        " | 🔻 파란 아래 화살표: 전날보다 순위 하락  "
        " | 👍 누적관객 100만 명 초과"
    )


    # =====================================================
    # 15. 관객수 상위 5편
    # =====================================================

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


    chart_data = chart_data.set_index(
        "영화명"
    )


    st.bar_chart(
        chart_data
    )


# =========================================================
# =========================================================
# 16. 2025년 8월 통계
# =========================================================
# =========================================================

else:

    st.header(
        "📊 2025년 8월 박스오피스 통계"
    )

    st.write(
        "2025년 8월 1일부터 8월 31일까지의 "
        "일별 박스오피스 데이터를 분석합니다."
    )


    # -----------------------------------------------------
    # 날짜 설정
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


    daily_results = []

    all_movies = []


    # -----------------------------------------------------
    # 진행률 표시
    # -----------------------------------------------------

    progress = st.progress(0)

    current_date = start_date

    day_number = 0

    total_days = 31


    # -----------------------------------------------------
    # 8월 1일 ~ 31일 데이터 가져오기
    # -----------------------------------------------------

    while current_date <= end_date:

        target_date = current_date.strftime(
            "%Y%m%d"
        )

        display_date = current_date.strftime(
            "%m월 %d일"
        )


        movies, error_message = get_boxoffice(
            KOBIS_KEY,
            target_date
        )


        # 오류가 있으면 해당 날짜를 건너뜁니다.
        if error_message:

            st.warning(
                f"⚠️ {display_date} 데이터를 "
                "가져오지 못했습니다."
            )

        else:

            movies.sort(
                key=lambda x: x["rank"]
            )


            # ---------------------------------------------
            # 해당 날짜의 1위 영화
            # ---------------------------------------------

            first_movie = movies[0]


            daily_results.append({

                "날짜":
                    display_date,

                "1위 영화":
                    first_movie["movieNm"],

                "관객수":
                    first_movie["audiCnt"],

                "스크린수":
                    first_movie["scrnCnt"]
            })


            # ---------------------------------------------
            # 모든 영화 데이터 저장
            # ---------------------------------------------

            for movie in movies:

                all_movies.append({

                    "날짜":
                        display_date,

                    "영화명":
                        movie["movieNm"],

                    "순위":
                        movie["rank"],

                    "관객수":
                        movie["audiCnt"],

                    "누적관객":
                        movie["audiAcc"],

                    "스크린수":
                        movie["scrnCnt"]
                })


        # 진행률 업데이트
        day_number += 1

        progress.progress(
            day_number / total_days
        )


        # 다음 날짜
        current_date += timedelta(days=1)


    progress.empty()


    # -----------------------------------------------------
    # 데이터가 하나도 없는 경우
    # -----------------------------------------------------

    if not daily_results:

        st.error(
            "❌ 2025년 8월 박스오피스 데이터를 "
            "가져오지 못했습니다."
        )

        st.info(
            "KOBIS_KEY와 KOBIS API 서버 상태를 "
            "확인해 주세요."
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
    # 17. 8월 핵심 통계
    # =====================================================

    st.subheader("🏆 8월 핵심 통계")


    # 영화별 일일 관객수 합계
    movie_audience = (
        all_movies_df
        .groupby("영화명")["관객수"]
        .sum()
        .sort_values(
            ascending=False
        )
    )


    top_movie = movie_audience.index[0]

    top_movie_audience = movie_audience.iloc[0]


    # 가장 많이 1위를 한 영화
    first_place_count = (
        daily_df["1위 영화"]
        .value_counts()
    )


    first_place_movie = (
        first_place_count.index[0]
    )

    first_place_days = (
        first_place_count.iloc[0]
    )


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
    # 18. 8월 관객수 TOP 10
    # =====================================================

    st.subheader(
        "🎬 2025년 8월 관객수 TOP 10"
    )


    top10_df = (
        movie_audience
        .head(10)
        .reset_index()
    )


    top10_df.columns = [
        "영화명",
        "8월 일일 관객수 합계"
    ]


    # 100만 명을 넘은 영화에는 👍 표시
    display_top10 = top10_df.copy()


    display_top10["영화명"] = (
        display_top10["영화명"]
        .apply(
            lambda name:
            name + " 👍"
            if movie_audience[name] > 1_000_000
            else name
        )
    )


    display_top10[
        "8월 일일 관객수 합계"
    ] = (
        display_top10[
            "8월 일일 관객수 합계"
        ]
        .map(
            lambda x: f"{x:,}명"
        )
    )


    st.dataframe(
        display_top10,
        use_container_width=True,
        hide_index=True
    )


    # 그래프
    chart_top10 = top10_df.copy()

    chart_top10 = chart_top10.set_index(
        "영화명"
    )


    st.bar_chart(
        chart_top10
    )


    # =====================================================
    # 19. 날짜별 총 관객수
    # =====================================================

    st.subheader(
        "📈 날짜별 박스오피스 관객수"
    )


    daily_total = (
        all_movies_df
        .groupby("날짜")["관객수"]
        .sum()
    )


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
    # 20. 날짜별 1위 영화
    # =====================================================

    st.subheader(
        "🥇 날짜별 1위 영화"
    )


    st.dataframe(
        daily_df,
        use_container_width=True,
        hide_index=True
    )


    # =====================================================
    # 21. 8월 1위 영화 횟수
    # =====================================================

    st.subheader(
        "🔄 8월 1위 영화 횟수"
    )


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
    # 22. 안내
    # =====================================================

    st.info(
        "ℹ️ 8월 일일 관객수 합계는 KOBIS에서 제공하는 "
        "각 날짜의 일일 관객수(audiCnt)를 영화별로 "
        "합산한 값입니다. "
        "KOBIS의 누적관객(audiAcc)과는 다른 지표입니다."
    )
