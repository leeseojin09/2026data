
# pages/3_채점표.py — 뇌졸중 분류 모델 채점표
import numpy as np
import pandas as pd
import streamlit as st

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

st.title("📋 뇌졸중 분류 모델 채점표")
st.write(
    "채점용 사람들의 실제 결과와 모델의 예측을 비교합니다. "
    "혼동행렬, 분류 지표, 놓친 환자와 헛짚은 사람을 확인할 수 있습니다."
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)

속성목록 = [
    "age",
    "avg_glucose_level",
    "bmi",
    "hypertension",
    "heart_disease",
]

속성뜻 = {
    "age": "나이",
    "avg_glucose_level": "평균 혈당",
    "bmi": "체질량지수(BMI)",
    "hypertension": "고혈압 여부",
    "heart_disease": "심장병 여부",
}

# 채점용 인원 설정
채점용_목표인원 = 1000


@st.cache_data
def 데이터_읽기():
    return pd.read_csv(DATA_URL, encoding="utf-8")


try:
    df = 데이터_읽기()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

if not set(속성목록 + ["stroke"]).issubset(df.columns):
    st.error("데이터에 필요한 열이 없습니다.")
    st.stop()

# 번호 순으로 정렬
if "id" in df.columns:
    df = df.sort_values("id", kind="stable").reset_index(drop=True)
else:
    df = df.reset_index(drop=True)

df["stroke"] = pd.to_numeric(df["stroke"], errors="coerce")
df = df[df["stroke"].isin([0, 1])].reset_index(drop=True)

if len(df) < 2:
    st.error("채점용 데이터와 학습용 데이터를 나눌 자료가 부족합니다.")
    st.stop()

# 앞 1,000명은 채점용, 나머지는 학습용
채점용_인원 = min(채점용_목표인원, len(df) - 1)

test_df = df.iloc[:채점용_인원].copy()
train_df = df.iloc[채점용_인원:].copy()

st.subheader("1. 입력 속성")

선택속성 = st.multiselect(
    "두 모델에 사용할 입력 속성을 선택하세요.",
    options=속성목록,
    default=[
        "age",
        "avg_glucose_level",
        "hypertension",
        "heart_disease",
    ],
    format_func=lambda x: f"{x} — {속성뜻[x]}",
    key="분류_속성선택",
)

if len(선택속성) < 2:
    st.warning("입력 속성을 두 개 이상 선택해 주세요.")
    st.stop()

# 입력 속성의 숫자형 변환
X_train_raw = train_df[선택속성].apply(
    pd.to_numeric, errors="coerce"
)
X_test_raw = test_df[선택속성].apply(
    pd.to_numeric, errors="coerce"
)

y_train = train_df["stroke"].astype(int)
y_test = test_df["stroke"].astype(int)

# 결측값 대체 기준은 학습용 데이터에서만 계산
중앙값채우기 = SimpleImputer(strategy="median")

X_train = pd.DataFrame(
    중앙값채우기.fit_transform(X_train_raw),
    columns=선택속성,
    index=train_df.index,
)

X_test = pd.DataFrame(
    중앙값채우기.transform(X_test_raw),
    columns=선택속성,
    index=test_df.index,
)

if y_train.nunique() < 2:
    st.error("훈련용 데이터에 0과 1이 모두 있어야 모델을 학습할 수 있습니다.")
    st.stop()

# 확률 모델: 로지스틱 회귀
확률모델 = Pipeline([
    ("크기맞추기", StandardScaler()),
    ("분류", LogisticRegression(max_iter=2000, random_state=42)),
])

확률모델.fit(X_train, y_train)

확률클래스 = list(확률모델.named_steps["분류"].classes_)
확률예측값 = 확률모델.predict_proba(X_test)[
    :, 확률클래스.index(1)
]
확률분류 = (확률예측값 >= 0.5).astype(int)

# 질문형 모델: 결정 트리
질문모델 = DecisionTreeClassifier(
    max_depth=3,
    min_samples_leaf=5,
    random_state=42,
)
질문모델.fit(X_train, y_train)
질문분류 = 질문모델.predict(X_test).astype(int)

# 기준 모델: 학습 데이터에서 더 많은 정답만 예측
다수정답 = int(y_train.value_counts().idxmax())
기준분류 = np.full(len(y_test), 다수정답, dtype=int)

예측결과 = {
    "확률 모델": 확률분류,
    "질문형 모델": 질문분류,
    "훈련용 다수 클래스 기준 모델": 기준분류,
}


# 혼동행렬 계산
def 혼동수(실제, 예측):
    실제 = np.asarray(실제, dtype=int)
    예측 = np.asarray(예측, dtype=int)

    tn = int(((실제 == 0) & (예측 == 0)).sum())
    fp = int(((실제 == 0) & (예측 == 1)).sum())
    fn = int(((실제 == 1) & (예측 == 0)).sum())
    tp = int(((실제 == 1) & (예측 == 1)).sum())

    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn}


# 분류 지표 계산
def 지표계산(혼동):
    tp = 혼동["TP"]
    fp = 혼동["FP"]
    fn = 혼동["FN"]
    tn = 혼동["TN"]
    전체 = tp + fp + fn + tn

    정확도 = (tp + tn) / 전체 if 전체 else 0.0

    정밀도 = (
        tp / (tp + fp)
        if tp + fp > 0
        else None
    )

    재현율 = (
        tp / (tp + fn)
        if tp + fn > 0
        else None
    )

    f1분모 = 2 * tp + fp + fn
    f1 = 2 * tp / f1분모 if f1분모 > 0 else 0.0

    return {
        "정확도": 정확도,
        "정밀도": 정밀도,
        "재현율": 재현율,
        "F1": f1,
    }


def 백분율(값):
    if 값 is None:
        return "계산할 수 없음"
    return f"{값 * 100:.1f}%"


혼동결과 = {
    이름: 혼동수(y_test.to_numpy(), 예측)
    for 이름, 예측 in 예측결과.items()
}

지표결과 = {
    이름: 지표계산(혼동)
    for 이름, 혼동 in 혼동결과.items()
}

st.subheader("2. 채점용 데이터 요약")

실제_뇌졸중인원 = int(y_test.sum())

왼쪽지표, 오른쪽지표, 세번째지표 = st.columns(3)

with 왼쪽지표:
    st.metric("채점용 인원", f"{len(test_df):,}명")

with 오른쪽지표:
    st.metric("실제 뇌졸중 인원", f"{실제_뇌졸중인원:,}명")

with 세번째지표:
    st.metric("학습용 인원", f"{len(train_df):,}명")

st.caption(
    f"데이터 번호 순으로 앞 {len(test_df):,}명을 채점용으로 고정했습니다. "
    f"나머지 {len(train_df):,}명만 모델 학습 및 결측값 처리 기준 계산에 사용합니다."
)

st.subheader("3. 두 모델의 혼동행렬")

st.caption(
    "행은 실제 결과, 열은 모델의 예측입니다. "
    "TP는 뇌졸중을 맞게 예측, TN은 뇌졸중이 아님을 맞게 예측, "
    "FP는 아닌데 뇌졸중이라고 예측, FN은 뇌졸중인데 놓친 경우입니다."
)


def 혼동행렬표(혼동):
    tp = 혼동["TP"]
    fp = 혼동["FP"]
    fn = 혼동["FN"]
    tn = 혼동["TN"]

    return pd.DataFrame(
        [
            [
                f"TN = {tn}명",
                f"FP = {fp}명",
                f"{tn + fp}명",
            ],
            [
                f"FN = {fn}명",
                f"TP = {tp}명",
                f"{fn + tp}명",
            ],
            [
                f"{tn + fn}명",
                f"{fp + tp}명",
                f"{tn + fp + fn + tp}명",
            ],
        ],
        index=[
            "실제 0 · 뇌졸중 아님",
            "실제 1 · 뇌졸중",
            "열 합계",
        ],
        columns=[
            "예측 0 · 뇌졸중 아님",
            "예측 1 · 뇌졸중",
            "행 합계",
        ],
    )


왼쪽, 오른쪽 = st.columns(2)

with 왼쪽:
    st.markdown("#### 확률 모델")
    st.dataframe(
        혼동행렬표(혼동결과["확률 모델"]),
        use_container_width=True,
    )

with 오른쪽:
    st.markdown("#### 질문형 모델")
    st.dataframe(
        혼동행렬표(혼동결과["질문형 모델"]),
        use_container_width=True,
    )

st.subheader("4. 정확도 · 정밀도 · 재현율 · F1 비교")

비교표 = []

for 이름 in [
    "확률 모델",
    "질문형 모델",
    "훈련용 다수 클래스 기준 모델",
]:
    지표 = 지표결과[이름]
    비교표.append({
        "모델": 이름,
        "정확도": 백분율(지표["정확도"]),
        "정밀도": 백분율(지표["정밀도"]),
        "재현율": 백분율(지표["재현율"]),
        "F1": 백분율(지표["F1"]),
    })

st.dataframe(
    pd.DataFrame(비교표),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "정밀도 = TP / (TP + FP), 재현율 = TP / (TP + FN), "
    "F1 = 2TP / (2TP + FP + FN)입니다. "
    "F1의 분모가 0이면 0.0%로 표시합니다. "
    "실제 뇌졸중 사례가 0명이면 재현율을 계산할 수 없습니다."
)

st.subheader("5. 놓친 환자와 헛짚은 사람")

선택모델 = st.selectbox(
    "목록을 확인할 모델을 선택하세요.",
    options=[
        "확률 모델",
        "질문형 모델",
        "훈련용 다수 클래스 기준 모델",
    ],
    key="채점표_목록모델",
)

선택예측 = 예측결과[선택모델]

목록원본 = test_df.copy()
목록원본["실제"] = y_test.to_numpy()
목록원본["예측"] = 선택예측

놓친환자 = 목록원본[
    (목록원본["실제"] == 1)
    & (목록원본["예측"] == 0)
].copy()

헛짚은사람 = 목록원본[
    (목록원본["실제"] == 0)
    & (목록원본["예측"] == 1)
].copy()


def 목록용표(자료):
    if 자료.empty:
        return pd.DataFrame(
            columns=[
                "번호",
                "나이",
                "평균 혈당",
                "고혈압 여부",
                "심장병 여부",
            ]
        )

    번호열 = (
        자료["id"].to_numpy()
        if "id" in 자료.columns
        else 자료.index.to_numpy() + 1
    )

    결과 = pd.DataFrame({
        "번호": 번호열,
        "나이": pd.to_numeric(
            자료["age"], errors="coerce"
        ).to_numpy(),
        "평균 혈당": pd.to_numeric(
            자료["avg_glucose_level"], errors="coerce"
        ).to_numpy(),
        "고혈압 여부": 자료["hypertension"].to_numpy(),
        "심장병 여부": 자료["heart_disease"].to_numpy(),
    })

    return (
        결과.sort_values(
            "나이",
            ascending=False,
            na_position="last",
        )
        .head(20)
        .reset_index(drop=True)
    )


FN = 혼동결과[선택모델]["FN"]
FP = 혼동결과[선택모델]["FP"]

왼쪽목록, 오른쪽목록 = st.columns(2)

with 왼쪽목록:
    st.markdown(f"#### 놓친 환자 (FN) · 전체 {len(놓친환자):,}명")
    st.caption(
        "실제 뇌졸중이지만 모델은 뇌졸중이 아니라고 예측한 사람"
    )
    st.dataframe(
        목록용표(놓친환자),
        use_container_width=True,
        hide_index=True,
    )

with 오른쪽목록:
    st.markdown(f"#### 헛짚은 사람 (FP) · 전체 {len(헛짚은사람):,}명")
    st.caption(
        "실제 뇌졸중이 아니지만 모델은 뇌졸중이라고 예측한 사람"
    )
    st.dataframe(
        목록용표(헛짚은사람),
        use_container_width=True,
        hide_index=True,
    )

st.info(
    f"선택한 모델: {선택모델} · "
    f"놓친 환자 {len(놓친환자):,}명 = 혼동행렬 FN {FN:,}명 · "
    f"헛짚은 사람 {len(헛짚은사람):,}명 = 혼동행렬 FP {FP:,}명. "
    "목록은 나이가 많은 순서이며, 각 목록은 최대 20명까지 표시합니다."
)

st.warning(
    "이 자료는 교육용 데이터에 대한 분류 실습입니다. "
    "채점용 데이터는 앞에서부터 최대 1,000명을 사용합니다. "
    "실제 환자의 진단이나 치료 판단에 사용해서는 안 됩니다."
)
