import re
import requests

# 1. 급식 데이터 요청 (예시)
url = "https://open.neis.go.kr/hub/mealServiceDietInfo"
params = {
    "Type": "json",
    "ATPT_OFCDC_SC_CODE": "E10",  # 인천광역시교육청
    "SD_SCHUL_CODE": "학교코드입력",
    "MMEAL_SC_CODE": "2",  # 중식
    "MLSV_FROM_YMD": "20240101",
    "MLSV_TO_YMD": "20241231",
}

# 2. 메뉴 분석 예시
# DDISH_NM 예시: "발아현미밥<br/>해물탕 (7.8.9.)<br/>배추김치 (9.)<br/>조각케이크 (1.2.5.6.)"
# - (7.8)과 같이 7(새우), 8(게) 번호가 들어있는지 확인하여 갑각류 알레르기 메뉴 카운트
# - '김치'가 들어간 메뉴만 따로 추출하여 종류별 빈도 집계
