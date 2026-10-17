
# pages/4_전처리.py — 뇌졸중 예측 실습실 전처리 비교
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

st.set_page_config(
    page_title="뇌졸중 예측 실습실",
    page_icon="🩺",
    layout="wide",
)

st.title("🧹 전처리 전후 비교 실험실")
st.write(
    "최대 1,000명을 채점용 데이터로 고정하고 나머지 자료로 모델을 학습합니다. "
    "클래스 균형 조정과 BMI 결측값 처리에 따라 예측 결과가 어떻게 달라지는지 비교합니다."
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


@st.cache_data
def 데이터_읽기():
    return pd.read_csv(DATA_URL, encoding="utf-8")


try:
    df = 데이터_읽기()
except Exception as e:
    st.error(f"데이터를 불러오지 못했습니다: {e}")
    st.stop()

필수열 = set(속성목록 + ["stroke"])

if not 필수열.issubset(df.columns):
    st.error("데이터에 필요한 열이 없습니다.")
    st.stop()

# 데이터 번호 순으로 정렬
if "id" in df.columns:
    df = df.sort_values("id", kind="stable").reset_index(drop=True)
else:
    df = df.reset_index(drop=True)

df["stroke"] = pd.to_numeric(df["stroke"], errors="coerce")
df = df[df["stroke"].isin([0, 1])].reset_index(drop=True)

if len(df) < 2:
    st.error("학습용 데이터와 채점용 데이터를 나눌 자료가 부족합니다.")
    st.stop()

# 앞 1,000명은 채점용, 나머지는 학습용
채점용_인원 = min(1000, len(df) - 1)

test_original = df.iloc[:채점용_인원].copy()
train_original = df.iloc[채점용_인원:].copy()

# --------------------------------------------------
# 1. 전처리 설정
# --------------------------------------------------
st.subheader("1. 전처리 설정")

설정1, 설정2 = st.columns(2)

with 설정1:
    균형조정 = st.toggle(
        "클래스 무게 조정 켜기",
        value=False,
        help=(
            "켜면 두 모델의 전처리 후 버전에 "
            "class_weight='balanced'를 적용합니다. "
            "데이터 행 자체를 늘리거나 줄이는 방법은 아닙니다."
        ),
    )

with 설정2:
    BMI처리 = st.radio(
        "BMI 결측값 처리 방법",
        options=["그대로 두기", "삭제하기"],
        horizontal=True,
        help=(
            "삭제하기를 선택하면 BMI가 비어 있는 행을 "
            "학습용과 채점용에서 각각 제거합니다."
        ),
    )

선택속성 = st.multiselect(
    "모델에 사용할 입력 속성을 선택하세요.",
    options=속성목록,
    default=[
        "age",
        "avg_glucose_level",
        "hypertension",
        "heart_disease",
    ],
    format_func=lambda x: f"{x} — {속성뜻[x]}",
    key="전처리_속성선택",
)

if len(선택속성) < 2:
    st.warning("입력 속성을 두 개 이상 선택해 주세요.")
    st.stop()

# BMI 결측값 삭제 전 개수 기록
BMI결측_학습 = int(train_original["bmi"].isna().sum())
BMI결측_채점 = int(test_original["bmi"].isna().sum())

삭제된_뇌졸중인원 = 0
삭제된_전체인원 = 0

train_df = train_original.copy()
test_df = test_original.copy()

# BMI 삭제 설정은 입력 속성에 BMI가 선택되지 않았더라도 적용
if BMI처리 == "삭제하기":
    삭제대상_학습 = train_df["bmi"].isna()
    삭제대상_채점 = test_df["bmi"].isna()

    삭제된_전체인원 = int(
        삭제대상_학습.sum() + 삭제대상_채점.sum()
    )

    삭제된_뇌졸중인원 = int(
        train_df.loc[삭제대상_학습, "stroke"].sum()
        + test_df.loc[삭제대상_채점, "stroke"].sum()
    )

    train_df = train_df.loc[~삭제대상_학습].copy()
    test_df = test_df.loc[~삭제대상_채점].copy()

st.subheader("2. 데이터 전처리 결과")

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("원본 전체 데이터", f"{len(df):,}명")

with m2:
    st.metric("채점용 원본", f"{len(test_original):,}명")

with m3:
    st.metric("학습용 원본", f"{len(train_original):,}명")

with m4:
    st.metric("BMI 결측 행 삭제", f"{삭제된_전체인원:,}명")

if BMI처리 == "삭제하기":
    st.info(
        f"BMI 결측 행을 삭제했습니다. "
        f"삭제된 행은 총 {삭제된_전체인원:,}명이며, "
        f"그중 실제 뇌졸중(stroke=1)인 사람은 "
        f"{삭제된_뇌졸중인원:,}명입니다. "
        f"최종 채점용은 {len(test_df):,}명, "
        f"학습용은 {len(train_df):,}명입니다."
    )
else:
    st.info(
        "BMI 결측 행을 유지합니다. "
        "모델 학습 시 선택한 입력 속성의 결측값은 "
        "학습용 데이터에서 계산한 중앙값으로 대체합니다."
    )

if len(train_df) == 0 or len(test_df) == 0:
    st.error("전처리 후 학습용 또는 채점용 데이터가 없습니다.")
    st.stop()

st.caption(
    "데이터 번호 순으로 앞 최대 1,000명을 채점용으로 고정했습니다. "
    "나머지는 학습용입니다. BMI 결측 행 삭제를 선택하면 "
    "실제 채점 인원이 1,000명보다 적어질 수 있습니다."
)

# --------------------------------------------------
# 3. 입력 데이터 구성
# --------------------------------------------------
X_train_raw = train_df[선택속성].apply(
    pd.to_numeric, errors="coerce"
)

X_test_raw = test_df[선택속성].apply(
    pd.to_numeric, errors="coerce"
)

y_train = train_df["stroke"].astype(int)
y_test = test_df["stroke"].astype(int)

if y_train.nunique() < 2:
    st.error(
        "학습용 데이터에 stroke=0과 stroke=1이 모두 있어야 합니다."
    )
    st.stop()

if y_test.nunique() < 2:
    st.warning(
        "채점용 데이터에 실제 뇌졸중 여부 한 종류만 있습니다. "
        "일부 평가 지표가 계산되지 않거나 0으로 표시될 수 있습니다."
    )

# 결측값 대체 기준은 학습용에서만 계산
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

# --------------------------------------------------
# 4. 모델 학습 및 예측
# --------------------------------------------------
def 모델학습_예측(class_weight):
    """같은 학습/채점 데이터에서 두 모델을 학습하고 결과를 반환한다."""

    확률모델 = Pipeline([
        ("표준화", StandardScaler()),
        (
            "분류",
            LogisticRegression(
                max_iter=2000,
                random_state=42,
                class_weight=class_weight,
            ),
        ),
    ])

    확률모델.fit(X_train, y_train)

    확률클래스 = list(
        확률모델.named_steps["분류"].classes_
    )

    확률값 = 확률모델.predict_proba(X_test)[
        :, 확률클래스.index(1)
    ]

    확률분류 = (확률값 >= 0.5).astype(int)

    질문모델 = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=5,
        random_state=42,
        class_weight=class_weight,
    )

    질문모델.fit(X_train, y_train)
    질문분류 = 질문모델.predict(X_test).astype(int)

    return {
        "확률 모델": {
            "model": 확률모델,
            "probability": 확률값,
            "prediction": 확률분류,
        },
        "질문형 모델": {
            "model": 질문모델,
            "probability": None,
            "prediction": 질문분류,
        },
    }


# 전처리 전 모델은 균형 조정 미적용
전처리전 = 모델학습_예측(None)

# 전처리 후 모델은 토글 설정을 적용
전처리후 = 모델학습_예측(
    "balanced" if 균형조정 else None
)

# --------------------------------------------------
# 5. 혼동행렬과 지표
# --------------------------------------------------
def 혼동수(실제, 예측):
    실제 = np.asarray(실제, dtype=int)
    예측 = np.asarray(예측, dtype=int)

    tn = int(((실제 == 0) & (예측 == 0)).sum())
    fp = int(((실제 == 0) & (예측 == 1)).sum())
    fn = int(((실제 == 1) & (예측 == 0)).sum())
    tp = int(((실제 == 1) & (예측 == 1)).sum())

    return {"TP": tp, "FP": fp, "FN": fn, "TN": tn}


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
    return "계산할 수 없음" if 값 is None else f"{값 * 100:.2f}%"


def 혼동행렬표(혼동):
    tp = 혼동["TP"]
    fp = 혼동["FP"]
    fn = 혼동["FN"]
    tn = 혼동["TN"]

    return pd.DataFrame(
        [
            [f"TN = {tn}명", f"FP = {fp}명"],
            [f"FN = {fn}명", f"TP = {tp}명"],
        ],
        index=[
            "실제 0 · 뇌졸중 아님",
            "실제 1 · 뇌졸중",
        ],
        columns=[
            "예측 0 · 뇌졸중 아님",
            "예측 1 · 뇌졸중",
        ],
    )


혼동_전 = {}
혼동_후 = {}
지표_전 = {}
지표_후 = {}

for 이름 in ["확률 모델", "질문형 모델"]:
    혼동_전[이름] = 혼동수(
        y_test.to_numpy(),
        전처리전[이름]["prediction"],
    )

    혼동_후[이름] = 혼동수(
        y_test.to_numpy(),
        전처리후[이름]["prediction"],
    )

    지표_전[이름] = 지표계산(혼동_전[이름])
    지표_후[이름] = 지표계산(혼동_후[이름])

# --------------------------------------------------
# 6. 전처리 전후 혼동행렬
# --------------------------------------------------
st.subheader("3. 전처리 전후 혼동행렬 비교")

st.caption(
    "전처리 전과 후 모두 같은 채점용 원본을 기준으로 비교합니다. "
    "BMI 결측 삭제를 선택하면 결측 BMI 행은 양쪽 비교에서 제외됩니다."
)

for 이름 in ["확률 모델", "질문형 모델"]:
    st.markdown(f"### {이름}")

    왼쪽, 오른쪽 = st.columns(2)

    with 왼쪽:
        st.markdown("#### 전처리 전")
        st.dataframe(
            혼동행렬표(혼동_전[이름]),
            use_container_width=True,
        )

    with 오른쪽:
        st.markdown("#### 전처리 후")
        st.dataframe(
            혼동행렬표(혼동_후[이름]),
            use_container_width=True,
        )

# --------------------------------------------------
# 7. 정확도, 정밀도, 재현율, F1
# --------------------------------------------------
st.subheader("4. 분류 지표 비교")

비교자료 = []

for 이름 in ["확률 모델", "질문형 모델"]:
    for 구분, 지표 in [
        ("전처리 전", 지표_전[이름]),
        ("전처리 후", 지표_후[이름]),
    ]:
        비교자료.append({
            "모델": 이름,
            "구분": 구분,
            "정확도": 백분율(지표["정확도"]),
            "정밀도": 백분율(지표["정밀도"]),
            "재현율": 백분율(지표["재현율"]),
            "F1": 백분율(지표["F1"]),
        })

st.dataframe(
    pd.DataFrame(비교자료),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    "정밀도 = TP / (TP + FP), 재현율 = TP / (TP + FN), "
    "F1 = 2TP / (2TP + FP + FN)입니다."
)

# --------------------------------------------------
# 8. TP, FN, FP 변화
# --------------------------------------------------
st.subheader("5. 전처리 전후 예측 인원 변화")

변화자료 = []

for 이름 in ["확률 모델", "질문형 모델"]:
    전 = 혼동_전[이름]
    후 = 혼동_후[이름]

    변화자료.append({
        "모델": 이름,
        "구분": "전처리 전 → 후",
        "맞게 찾은 뇌졸중 환자(TP)": (
            f"{전['TP']:,}명 → {후['TP']:,}명"
        ),
        "놓친 환자(FN)": (
            f"{전['FN']:,}명 → {후['FN']:,}명"
        ),
        "헛짚은 사람(FP)": (
            f"{전['FP']:,}명 → {후['FP']:,}명"
        ),
        "TP 변화": 후["TP"] - 전["TP"],
        "FN 변화": 후["FN"] - 전["FN"],
        "FP 변화": 후["FP"] - 전["FP"],
    })

st.dataframe(
    pd.DataFrame(변화자료),
    use_container_width=True,
    hide_index=True,
)

# --------------------------------------------------
# 9. 그래프용 속성 선택
# --------------------------------------------------
st.subheader("6. Plotly 결정 경계 시각화")

st.write(
    "두 속성을 선택하면 2차원 그래프에서 0.5 결정 경계를 비교합니다. "
    "세 속성 이상을 선택하면 세 속성을 이용한 회전 가능한 3차원 그래프를 표시합니다."
)

if len(선택속성) == 2:
    x축 = 선택속성[0]
    y축 = 선택속성[1]
    z축 = None
else:
    g1, g2, g3 = st.columns(3)

    with g1:
        x축 = st.selectbox(
            "X축 속성",
            선택속성,
            index=0,
            key="전처리_x축",
        )

    나머지_y = [x for x in 선택속성 if x != x축]

    with g2:
        y축 = st.selectbox(
            "Y축 속성",
            나머지_y,
            index=0,
            key="전처리_y축",
        )

    나머지_z = [x for x in 선택속성 if x not in [x축, y축]]

    with g3:
        z축 = st.selectbox(
            "Z축 속성",
            나머지_z,
            index=0,
            key="전처리_z축",
        )

# 색상은 실제 정답에 따라 구분
색상_실제 = np.where(y_test.to_numpy() == 1, "red", "blue")

# --------------------------------------------------
# 10. 2차원 결정 경계
# --------------------------------------------------
if len(선택속성) == 2:
    st.markdown("#### 2차원 산점도와 0.5 결정 경계")

    x값 = X_test[x축].to_numpy()
    y값 = X_test[y축].to_numpy()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=x값[y_test.to_numpy() == 0],
            y=y값[y_test.to_numpy() == 0],
            mode="markers",
            name="실제 뇌졸중 아님",
            marker=dict(color="blue", size=7, opacity=0.65),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x값[y_test.to_numpy() == 1],
            y=y값[y_test.to_numpy() == 1],
            mode="markers",
            name="실제 뇌졸중",
            marker=dict(color="red", size=8, opacity=0.8),
        )
    )

    x_min, x_max = float(X_train[x축].min()), float(X_train[x축].max())
    y_min, y_max = float(X_train[y축].min()), float(X_train[y축].max())

    if x_min == x_max:
        x_min -= 1
        x_max += 1

    if y_min == y_max:
        y_min -= 1
        y_max += 1

    x_grid = np.linspace(x_min, x_max, 100)
    y_grid = np.linspace(y_min, y_max, 100)
    xx, yy = np.meshgrid(x_grid, y_grid)

    그리드자료 = pd.DataFrame(
        np.tile(X_train.median().to_numpy(), (xx.size, 1)),
        columns=선택속성,
    )

    그리드자료[x축] = xx.ravel()
    그리드자료[y축] = yy.ravel()

    경계_정보 = []

    for 구분, 결과, 선색, 선모양 in [
        ("전처리 전", 전처리전, "green", "solid"),
        ("전처리 후", 전처리후, "orange", "dash"),
    ]:
        모델 = 결과["확률 모델"]["model"]
        클래스 = list(모델.named_steps["분류"].classes_)

        확률 = 모델.predict_proba(그리드자료)[
            :, 클래스.index(1)
        ].reshape(xx.shape)

        최소확률 = float(np.nanmin(확률))
        최대확률 = float(np.nanmax(확률))

        경계_정보.append(
            (구분, 최소확률, 최대확률)
        )

        fig.add_trace(
            go.Contour(
                x=x_grid,
                y=y_grid,
                z=확률,
                contours=dict(
                    start=0.5,
                    end=0.5,
                    size=1,
                    coloring="none",
                    showlabels=False,
                ),
                line=dict(color=선색, width=3, dash=선모양),
                name=f"{구분} 0.5 경계",
                showscale=False,
                hovertemplate=(
                    f"{구분}<br>"
                    + x축 + ": %{x:.2f}<br>"
                    + y축 + ": %{y:.2f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        xaxis_title=f"{x축} ({속성뜻[x축]})",
        yaxis_title=f"{y축} ({속성뜻[y축]})",
        height=650,
        legend_title="범례",
    )

    st.plotly_chart(fig, use_container_width=True)

    for 구분, 최소확률, 최대확률 in 경계_정보:
        if 최소확률 > 0.5 or 최대확률 < 0.5:
            st.info(
                f"{구분}: 현재 그래프 범위 안에 0.5 결정 경계가 "
                "없을 수 있습니다. 경계가 표시되지 않는 것은 "
                "해당 범위에서 예측 확률이 모두 0.5보다 높거나 낮기 때문입니다."
            )

# --------------------------------------------------
# 11. 3차원 산점도 및 결정 평면
# --------------------------------------------------
else:
    st.markdown("#### 3차원 산점도와 결정 평면")

    fig3 = go.Figure()

    for 실제값, 이름, 색 in [
        (0, "실제 뇌졸중 아님", "blue"),
        (1, "실제 뇌졸중", "red"),
    ]:
        마스크 = y_test.to_numpy() == 실제값

        fig3.add_trace(
            go.Scatter3d(
                x=X_test.loc[마스크, x축],
                y=X_test.loc[마스크, y축],
                z=X_test.loc[마스크, z축],
                mode="markers",
                name=이름,
                marker=dict(size=4, color=색, opacity=0.7),
            )
        )

    축범위 = {}
    for 축 in [x축, y축, z축]:
        최소 = float(X_train[축].min())
        최대 = float(X_train[축].max())

        if 최소 == 최대:
            최소 -= 1
            최대 += 1

        축범위[축] = (최소, 최대)

    gx = np.linspace(*축범위[x축], 35)
    gy = np.linspace(*축범위[y축], 35)
    xx3, yy3 = np.meshgrid(gx, gy)

    for 구분, 결과, 색 in [
        ("전처리 전 0.5 평면", 전처리전, "green"),
        ("전처리 후 0.5 평면", 전처리후, "orange"),
    ]:
        모델 = 결과["확률 모델"]["model"]
        로지스틱 = 모델.named_steps["분류"]
        표준화 = 모델.named_steps["표준화"]

        클래스 = list(로지스틱.classes_)
        양성위치 = 클래스.index(1)

        계수_표준화 = 로지스틱.coef_[양성위치]
        절편_표준화 = 로지스틱.intercept_[양성위치]

        계수_원본 = 계수_표준화 / 표준화.scale_
        절편_원본 = (
            절편_표준화
            - np.sum(
                계수_표준화
                * 표준화.mean_
                / 표준화.scale_
            )
        )

        계수 = dict(zip(선택속성, 계수_원본))

        분모 = 계수[z축]

        if abs(분모) < 1e-10:
            st.info(
                f"{구분}: {속성뜻[z축]}의 계수가 0에 가까워 "
                "이 축을 기준으로 결정 평면을 그릴 수 없습니다."
            )
            continue

        zz3 = -(
            계수[x축] * xx3
            + 계수[y축] * yy3
            + 절편_원본
        ) / 분모

        z_min, z_max = 축범위[z축]

        # 현재 학습 데이터 범위 안에 있는 평면만 표시
        zz3 = np.where(
            (zz3 >= z_min) & (zz3 <= z_max),
            zz3,
            np.nan,
        )

        if not np.isfinite(zz3).any():
            st.info(
                f"{구분}: 결정 평면이 현재 그래프의 "
                f"{속성뜻[z축]} 범위 밖에 있습니다."
            )
            continue

        fig3.add_trace(
            go.Surface(
                x=xx3,
                y=yy3,
                z=zz3,
                name=구분,
                opacity=0.45,
                showscale=False,
                colorscale=[
                    [0, 색],
                    [1, 색],
                ],
                hovertemplate=(
                    f"{구분}<br>"
                    + x축 + ": %{x:.2f}<br>"
                    + y축 + ": %{y:.2f}<br>"
                    + z축 + ": %{z:.2f}<extra></extra>"
                ),
            )
        )

    fig3.update_layout(
        scene=dict(
            xaxis_title=f"{x축} ({속성뜻[x축]})",
            yaxis_title=f"{y축} ({속성뜻[y축]})",
            zaxis_title=f"{z축} ({속성뜻[z축]})",
        ),
        height=750,
        legend_title="범례",
    )

    st.plotly_chart(fig3, use_container_width=True)

# --------------------------------------------------
# 12. 놓친 환자 목록
# --------------------------------------------------
st.subheader("7. 놓친 환자 목록")

if 균형조정:
    목록기준 = 전처리후
    목록설명 = "클래스 균형 조정이 적용된 전처리 후 확률 모델"
else:
    목록기준 = 전처리전
    목록설명 = "클래스 균형 조정이 적용되지 않은 전처리 전 확률 모델"

목록예측 = 목록기준["확률 모델"]["prediction"]

목록원본 = test_df.copy()
목록원본["실제"] = y_test.to_numpy()
목록원본["예측"] = 목록예측

놓친환자 = 목록원본[
    (목록원본["실제"] == 1)
    & (목록원본["예측"] == 0)
].copy()

if "id" in 놓친환자.columns:
    번호열 = 놓친환자["id"].to_numpy()
else:
    번호열 = 놓친환자.index.to_numpy() + 1

놓친표 = pd.DataFrame({
    "번호": 번호열,
    "나이": pd.to_numeric(
        놓친환자["age"], errors="coerce"
    ).to_numpy(),
    "고혈압 여부": 놓친환자["hypertension"].to_numpy(),
    "심장병 여부": 놓친환자["heart_disease"].to_numpy(),
})

놓친표 = 놓친표.sort_values(
    "나이",
    ascending=True,
    na_position="last",
).reset_index(drop=True)

st.caption(
    f"목록 기준: {목록설명}. "
    "나이가 적은 순서로 정렬합니다."
)

st.write(f"**놓친 환자 전체: {len(놓친표):,}명**")

st.dataframe(
    놓친표,
    use_container_width=True,
    hide_index=True,
)

st.warning(
    "이 페이지는 교육용 분류 실험입니다. "
    "데이터 번호 순으로 앞 최대 1,000명을 채점용으로 사용하므로 "
    "무작위 표본 평가와 결과가 다를 수 있습니다. "
    "실제 환자의 진단이나 치료 판단에 사용해서는 안 됩니다."
)
