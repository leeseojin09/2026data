
import streamlit as st
import pandas as pd

# 페이지 설정: 브라우저 탭 제목과 아이콘
st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🧠",
    layout="wide"
)

# 데이터 주소
DATA_URL = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)


@st.cache_data
def load_data():
    """CSV 데이터를 UTF-8로 불러오기"""
    return pd.read_csv(DATA_URL, encoding="utf-8")


# 데이터 불러오기
st.title("🧠 뇌졸중 예측 실습실")
st.caption("데이터를 살펴보고 각 열의 의미를 알아보는 공간입니다.")

try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오지 못했습니다. 인터넷 연결과 데이터 주소를 확인해 주세요.")
    st.code(str(e))
    st.stop()


# 기본 정보 계산
total_people = len(df)
column_count = len(df.columns)

if "stroke" in df.columns:
    stroke_count = int((df["stroke"] == 1).sum())
    stroke_rate = (
        stroke_count / total_people * 100
        if total_people > 0
        else 0
    )
else:
    stroke_count = 0
    stroke_rate = 0


# 1. 큰 숫자 카드 네 개
st.subheader("📊 데이터 한눈에 보기")

col1, col2, col3, col4 = st.columns(4)

col1.metric("전체 사람 수", f"{total_people:,}명")
col2.metric("열 개수", f"{column_count}개")
col3.metric("stroke가 1인 사람 수", f"{stroke_count:,}명")
col4.metric("stroke가 1인 비율", f"{stroke_rate:.2f}%")


# 2. 열 이름, 우리말 뜻, 값의 종류, 빈 값 개수
st.subheader("📋 열 정보 살펴보기")

column_info = []

for column in df.columns:
    # 값의 종류: 숫자형 또는 문자형으로 표시
    if pd.api.types.is_numeric_dtype(df[column]):
        value_type = "숫자형"
    else:
        value_type = "문자형"

    # 서로 다른 값의 개수
    unique_count = df[column].nunique(dropna=True)

    # 빈 값 개수
    missing_count = int(df[column].isna().sum())

    column_info.append({
        "열 이름": column,
        "우리말 뜻": "",
        "값의 종류": f"{value_type} (고유값 {unique_count}종류)",
        "빈 값 개수": missing_count
    })

info_df = pd.DataFrame(column_info)

st.dataframe(
    info_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "열 이름": st.column_config.TextColumn(
            "열 이름",
            help="CSV 파일에 들어 있는 원래 열 이름"
        ),
        "우리말 뜻": st.column_config.TextColumn(
            "우리말 뜻",
            help="교재를 참고해 직접 뜻을 적어 보세요."
        ),
        "값의 종류": st.column_config.TextColumn("값의 종류"),
        "빈 값 개수": st.column_config.NumberColumn(
            "빈 값 개수",
            format="%d"
        )
    }
)

st.caption(
    "참고: 값의 종류는 숫자형·문자형과 고유값 개수를 표시합니다. "
    "빈 값은 데이터가 비어 있는 셀의 개수입니다."
)


# 3. 데이터 처음 다섯 줄
st.subheader("🔎 데이터 처음 다섯 줄")

st.dataframe(
    df.head(5),
    use_container_width=True,
    hide_index=True
)


# 4. 데이터 출처
st.subheader("📚 데이터 출처")

st.text_area(
    "교재를 참고해 데이터 출처를 적어 보세요.",
    value="",
    placeholder="예: 교재에 제시된 데이터 출처를 여기에 입력하세요.",
    height=100,
    key="data_source"
)
