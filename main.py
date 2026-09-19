import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="영화 흥행 예측기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 흥행 예측기")
st.caption(
    "영화 정보 데이터를 이용해 총 관객 수를 다중 회귀로 예측합니다."
)


# =========================================================
# 2. 데이터 주소
# =========================================================

DAILY_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_daily.csv"
)

MOVIES_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


# =========================================================
# 3. 데이터 불러오기
# =========================================================

@st.cache_data
def load_data():

    daily = pd.read_csv(
        DAILY_URL,
        encoding="utf-8-sig"
    )

    movies = pd.read_csv(
        MOVIES_URL,
        encoding="utf-8-sig"
    )

    return daily, movies


try:
    daily, movies = load_data()

except Exception as e:

    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.stop()


# =========================================================
# 4. 데이터 기간 계산
# =========================================================

daily["날짜"] = pd.to_datetime(
    daily["날짜"].astype(str),
    format="%Y%m%d",
    errors="coerce"
)

min_date = daily["날짜"].min()
max_date = daily["날짜"].max()

st.info(
    f"📅 박스오피스 일별 데이터 기준 기간: "
    f"**{min_date.strftime('%Y년 %m월 %d일')} ~ "
    f"{max_date.strftime('%Y년 %m월 %d일')}**"
)


# =========================================================
# 5. 영화코드 정리
# =========================================================

movies["movieCd"] = movies["movieCd"].astype(str).str.strip()

# 총 관객 수 숫자 변환
movies["total_audi"] = pd.to_numeric(
    movies["total_audi"],
    errors="coerce"
)

# 영화코드 순으로 정렬
movies = movies.sort_values(
    "movieCd"
).reset_index(drop=True)


# =========================================================
# 6. 영화 정보 표의 맨 위 행 표시
# =========================================================

st.subheader("🎞️ 영화 정보 표의 첫 번째 행")

st.dataframe(
    movies.head(1),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 7. 영화 수
# =========================================================

total_movies = len(movies)

st.write(
    f"영화 정보 표에 있는 영화는 총 **{total_movies}편**입니다."
)


# =========================================================
# 8. 변수 설명
# =========================================================

st.subheader("⚙️ 예측에 사용할 변수 선택")

st.write(
    "체크한 변수만 다중 회귀 모델의 입력값으로 사용합니다. "
    "`total_audi`는 예측 대상이므로 선택할 수 없습니다."
)


# 사용할 수 있는 변수
variable_info = {
    "first_scrn": "첫 관측일 스크린수",
    "first_show": "첫 관측일 상영횟수",
    "first_week_audi": "첫 주 관객",
    "days_in_top10": "10위권에 있었던 일수",
    "peak": "성수기 개봉 여부",
    "genre": "장르",
    "nation": "국가",
    "openDt": "개봉일",
    "first_date": "10위권 첫 등장일"
}


# 기본 선택값
default_variables = [
    "first_scrn",
    "first_show",
    "first_week_audi",
    "days_in_top10",
    "peak"
]

selected_variables = []

col1, col2, col3 = st.columns(3)

columns = [col1, col2, col3]

for i, (column_name, label) in enumerate(
    variable_info.items()
):

    with columns[i % 3]:

        checked = st.checkbox(
            label,
            value=column_name in default_variables,
            key=f"check_{column_name}"
        )

        if checked:
            selected_variables.append(column_name)


if len(selected_variables) == 0:

    st.warning(
        "최소 하나의 변수를 선택해야 합니다."
    )

    st.stop()


st.write(
    "**선택된 변수:** "
    + ", ".join(selected_variables)
)


# =========================================================
# 9. 날짜 변수에서 연도/월 파생
# =========================================================

model_df = movies.copy()

# 날짜 변수 처리
for date_col in ["openDt", "first_date"]:

    if date_col in model_df.columns:

        date_values = pd.to_datetime(
            model_df[date_col],
            errors="coerce"
        )

        model_df[f"{date_col}_year"] = (
            date_values.dt.year
        )

        model_df[f"{date_col}_month"] = (
            date_values.dt.month
        )

        model_df[f"{date_col}_day"] = (
            date_values.dt.day
        )


# =========================================================
# 10. 실제 모델 변수 만들기
# =========================================================

X_columns = []

for variable in selected_variables:

    if variable in ["openDt", "first_date"]:

        X_columns.extend([
            f"{variable}_year",
            f"{variable}_month",
            f"{variable}_day"
        ])

    else:

        X_columns.append(variable)


X = model_df[X_columns].copy()
y = model_df["total_audi"].copy()


# =========================================================
# 11. 영화코드 순으로 10편마다 앞의 3편을 테스트
# =========================================================

# index:
# 0,1,2 -> 테스트
# 3,4,5,6,7,8,9 -> 학습
# 10,11,12 -> 테스트
# 13~19 -> 학습
# ...

test_mask = (
    model_df.index % 10 < 3
)

train_mask = ~test_mask


X_train = X.loc[train_mask].copy()
X_test = X.loc[test_mask].copy()

y_train = y.loc[train_mask].copy()
y_test = y.loc[test_mask].copy()

test_movies = model_df.loc[test_mask].copy()


# =========================================================
# 12. 숫자형 / 문자형 변수 구분
# =========================================================

numeric_features = X_train.select_dtypes(
    include=["number"]
).columns.tolist()

categorical_features = X_train.select_dtypes(
    exclude=["number"]
).columns.tolist()


# =========================================================
# 13. 전처리
# =========================================================

transformers = []


if numeric_features:

    numeric_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        )
    ])

    transformers.append(
        (
            "numeric",
            numeric_pipeline,
            numeric_features
        )
    )


if categorical_features:

    categorical_pipeline = Pipeline([
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore"
            )
        )
    ])

    transformers.append(
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        )
    )


preprocessor = ColumnTransformer(
    transformers=transformers
)


# =========================================================
# 14. 다중 회귀 모델
# =========================================================

model = Pipeline([
    (
        "preprocessor",
        preprocessor
    ),
    (
        "regression",
        LinearRegression()
    )
])


# =========================================================
# 15. 학습
# =========================================================

try:

    model.fit(
        X_train,
        y_train
    )

except Exception as e:

    st.error(
        "모델 학습 중 오류가 발생했습니다."
    )

    st.code(str(e))

    st.stop()


# =========================================================
# 16. 테스트 데이터 예측
# =========================================================

predictions = model.predict(
    X_test
)

test_movies = test_movies.copy()

test_movies["예측_총관객"] = predictions
test_movies["실제_총관객"] = y_test.values

test_movies["오차"] = (
    test_movies["예측_총관객"]
    - test_movies["실제_총관객"]
)

test_movies["절대오차"] = (
    test_movies["오차"].abs()
)


# =========================================================
# 17. 평가 점수
# =========================================================

r2 = r2_score(
    y_test,
    predictions
)

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        predictions
    )
)


# =========================================================
# 18. 화면에 학습/평가 정보 표시
# =========================================================

st.subheader("📊 모델 평가")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "학습에 사용한 영화",
        f"{len(X_train)}편"
    )

with col2:

    st.metric(
        "평가한 영화",
        f"{len(X_test)}편"
    )

with col3:

    st.metric(
        "R² 점수",
        f"{r2:.3f}"
    )

with col4:

    st.metric(
        "평균 절대 오차",
        f"{mae:,.0f}명"
    )


st.caption(
    f"RMSE: {rmse:,.0f}명"
)


# =========================================================
# 19. 실제값 vs 예측값 산점도
# =========================================================

st.subheader(
    "🎯 실제 총 관객 수와 예측 총 관객 수"
)


# 로그 그래프에서는 0 이하를 표현할 수 없으므로
# 표시용으로 최소 1명을 사용
plot_actual = np.maximum(
    test_movies["실제_총관객"].to_numpy(),
    1
)

plot_predicted = np.maximum(
    test_movies["예측_총관객"].to_numpy(),
    1
)


fig = go.Figure()


# 실제 vs 예측 산점도
fig.add_trace(
    go.Scatter(
        x=plot_actual,
        y=plot_predicted,
        mode="markers",
        name="테스트 영화",
        text=test_movies["movieNm"],
        customdata=np.column_stack([
            test_movies["movieCd"],
            test_movies["실제_총관객"],
            test_movies["예측_총관객"],
            test_movies["오차"]
        ]),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "영화코드: %{customdata[0]}<br>"
            "실제 관객: %{customdata[1]:,.0f}명<br>"
            "예측 관객: %{customdata[2]:,.0f}명<br>"
            "오차: %{customdata[3]:,.0f}명"
            "<extra></extra>"
        )
    )
)


# =========================================================
# 20. 실제값 = 예측값 대각선
# =========================================================

max_value = max(
    plot_actual.max(),
    plot_predicted.max()
)

min_value = min(
    plot_actual.min(),
    plot_predicted.min()
)

fig.add_trace(
    go.Scatter(
        x=[min_value, max_value],
        y=[min_value, max_value],
        mode="lines",
        name="실제값 = 예측값",
        line=dict(
            dash="dash"
        ),
        hoverinfo="skip"
    )
)


# =========================================================
# 21. 예측 1,000명 미만 영화
# =========================================================

low_prediction_mask = (
    test_movies["예측_총관객"] < 1000
)

low_prediction_count = int(
    low_prediction_mask.sum()
)

# 그래프 바닥에 붙여 표시하기 위해 y=1 사용
if low_prediction_count > 0:

    low_movies = test_movies[
        low_prediction_mask
    ].copy()

    fig.add_trace(
        go.Scatter(
            x=np.maximum(
                low_movies["실제_총관객"],
                1
            ),
            y=np.ones(
                low_prediction_count
            ),
            mode="markers",
            name="예측 1,000명 미만",
            marker=dict(
                symbol="triangle-down",
                size=10
            ),
            text=low_movies["movieNm"],
            customdata=np.column_stack([
                low_movies["movieCd"],
                low_movies["예측_총관객"],
                low_movies["실제_총관객"]
            ]),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "영화코드: %{customdata[0]}<br>"
                "예측: %{customdata[1]:,.0f}명<br>"
                "실제: %{customdata[2]:,.0f}명"
                "<extra></extra>"
            )
        )
    )


fig.update_layout(
    height=650,

    xaxis=dict(
        title="실제 총 관객 수",
        type="log"
    ),

    yaxis=dict(
        title="예측한 총 관객 수",
        type="log"
    ),

    hovermode="closest"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


st.write(
    f"🔻 **예측이 1,000명보다 작게 나온 영화: "
    f"{low_prediction_count}편**"
)

if low_prediction_count > 0:

    st.caption(
        "그래프에서는 로그 축을 사용할 수 있도록 "
        "이 영화들의 표시 위치를 그래프 바닥(y=1)에 두었습니다."
    )


# =========================================================
# 22. 테스트 영화별 결과
# =========================================================

st.subheader("🎬 테스트 영화별 예측 결과")

result_table = test_movies[
    [
        "movieCd",
        "movieNm",
        "실제_총관객",
        "예측_총관객",
        "오차",
        "절대오차"
    ]
].copy()

result_table = result_table.sort_values(
    "movieCd"
)

result_table = result_table.rename(
    columns={
        "movieCd": "영화코드",
        "movieNm": "영화명",
        "실제_총관객": "실제 총 관객",
        "예측_총관객": "예측 총 관객",
        "오차": "오차",
        "절대오차": "절대오차"
    }
)

for column in [
    "실제 총 관객",
    "예측 총 관객",
    "오차",
    "절대오차"
]:

    result_table[column] = (
        result_table[column]
        .round(0)
        .astype(int)
    )

st.dataframe(
    result_table,
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 23. 사용한 변수
# =========================================================

st.subheader("🧩 모델에 사용한 변수")

st.write(
    ", ".join(selected_variables)
)

st.caption(
    "영화코드(movieCd)는 영화 식별용으로만 사용하며 "
    "예측 변수에는 넣지 않았습니다."
)


# =========================================================
# 24. 데이터 분할 방법 설명
# =========================================================

with st.expander("📚 학습·테스트 데이터 분할 방법"):

    st.write(
        """
        영화 정보 표를 영화코드(movieCd) 순으로 정렬한 뒤,
        10편씩 묶어서 각 묶음의 앞 3편을 테스트용으로 사용하고
        나머지 7편을 학습용으로 사용했습니다.

        예:

        1~3번 → 테스트
        4~10번 → 학습

        11~13번 → 테스트
        14~20번 → 학습

        이 방식을 전체 영화에 반복하여 모든 영화를
        학습 또는 테스트에 한 번씩 사용했습니다.
        """
    )
