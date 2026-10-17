
# pages/4_전처리.py — 뇌졸중 데이터 전처리와 클래스 무게 조정 비교
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

st.title("🧹 뇌졸중 데이터 전처리")
st.write(
    "BMI 결측값 처리와 클래스 무게 조정이 분류 결과에 미치는 영향을 "
    "같은 채점용 데이터로 비교합니다."
)

DATA_URL = (
    "https://raw.githubusercontent.com/"
    "greatsong/modudata/main/data/stroke.csv"
)

ATTRIBUTES = [
    "age",
    "avg_glucose_level",
    "bmi",
    "hypertension",
    "heart_disease",
]

LABELS = {
    "age": "나이",
    "avg_glucose_level": "평균 혈당",
    "bmi": "체질량지수(BMI)",
    "hypertension": "고혈압 여부",
    "heart_disease": "심장병 여부",
}


@st.cache_data
def load_data():
    return pd.read_csv(DATA_URL, encoding="utf-8")


def confusion(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    return {
        "TN": int(((y_true == 0) & (y_pred == 0)).sum()),
        "FP": int(((y_true == 0) & (y_pred == 1)).sum()),
        "FN": int(((y_true == 1) & (y_pred == 0)).sum()),
        "TP": int(((y_true == 1) & (y_pred == 1)).sum()),
    }


def metrics(c):
    tp, fp, fn, tn = c["TP"], c["FP"], c["FN"], c["TN"]
    total = tp + fp + fn + tn

    return {
        "정확도": (tp + tn) / total if total else 0.0,
        "정밀도": tp / (tp + fp) if tp + fp else None,
        "재현율": tp / (tp + fn) if tp + fn else None,
        "F1": (
            2 * tp / (2 * tp + fp + fn)
            if 2 * tp + fp + fn
            else 0.0
        ),
    }


def percent(value):
    return "계산할 수 없음" if value is None else f"{value * 100:.1f}%"


def matrix_table(c):
    tn, fp, fn, tp = c["TN"], c["FP"], c["FN"], c["TP"]
    return pd.DataFrame(
        [
            [f"TN: {tn}명", f"FP: {fp}명", f"{tn + fp}명"],
            [f"FN: {fn}명", f"TP: {tp}명", f"{fn + tp}명"],
            [f"{tn + fn}명", f"{fp + tp}명", f"{tn + fp + fn + tp}명"],
        ],
        index=["실제 0", "실제 1", "열 합계"],
        columns=["예측 0", "예측 1", "행 합계"],
    )


try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 읽지 못했습니다: {e}")
    st.stop()

if not set(ATTRIBUTES + ["stroke"]).issubset(df.columns):
    st.error("데이터에 필요한 열이 없습니다.")
    st.stop()

if "id" in df.columns:
    df = df.sort_values("id", kind="stable").reset_index(drop=True)
else:
    df = df.reset_index(drop=True)

df["stroke"] = pd.to_numeric(df["stroke"], errors="coerce")
df = df[df["stroke"].isin([0, 1])].reset_index(drop=True)

if len(df) <= 3:
    st.error("채점용 3명과 훈련용 데이터를 나눌 자료가 부족합니다.")
    st.stop()


# --------------------------------------------------
# 화면 맨 위: 클래스 무게, BMI 결측값, 입력 속성
# --------------------------------------------------
st.subheader("전처리 설정")

무게조정 = st.toggle(
    "클래스 무게 조정 켜기",
    value=False,
    help=(
        "켜면 두 모델의 class_weight='balanced' 결과를 "
        "놓친 환자 목록에 사용합니다. 전후 비교 결과는 항상 모두 표시합니다."
    ),
    key="preprocess_balance_toggle",
)

결측처리 = st.radio(
    "BMI가 비어 있는 사람",
    options=["그대로 두기", "삭제하기"],
    horizontal=True,
    index=0,
    key="preprocess_bmi_missing",
)

선택속성 = st.multiselect(
    "모델 입력 속성",
    options=ATTRIBUTES,
    default=[
        "age",
        "avg_glucose_level",
        "hypertension",
        "heart_disease",
    ],
    format_func=lambda x: f"{x} — {LABELS[x]}",
    key="preprocess_features",
)

if len(선택속성) < 2:
    st.warning("입력 속성을 두 개 이상 선택해 주세요.")
    st.stop()


# --------------------------------------------------
# 데이터 분리: 번호 순 첫 3명은 채점용으로 고정
# BMI 삭제는 분리 후 양쪽 데이터에 동일하게 적용
# --------------------------------------------------
test_original = df.iloc[:3].copy()
train_original = df.iloc[3:].copy()

삭제인원 = 0
삭제뇌졸중 = 0

if 결측처리 == "삭제하기":
    train_missing = train_original["bmi"].isna()
    test_missing = test_original["bmi"].isna()

    삭제인원 = int(train_missing.sum() + test_missing.sum())
    삭제뇌졸중 = int(
        train_original.loc[train_missing, "stroke"].sum()
        + test_original.loc[test_missing, "stroke"].sum()
    )

    train_df = train_original.loc[~train_missing].copy()
    test_df = test_original.loc[~test_missing].copy()
else:
    train_df = train_original.copy()
    test_df = test_original.copy()

st.caption(
    f"원래 채점용: {len(test_original)}명 · "
    f"원래 훈련용: {len(train_original)}명"
)

if 결측처리 == "삭제하기":
    st.info(
        f"BMI 결측으로 삭제된 사람: {삭제인원}명 · "
        f"그중 뇌졸중 환자: {삭제뇌졸중}명"
    )
else:
    st.info(
        "BMI 결측값을 유지합니다. BMI를 입력 속성으로 선택한 경우에만 "
        "훈련용 BMI의 중앙값으로 결측값을 대체합니다."
    )

if len(train_df) == 0:
    st.error("전처리 후 훈련용 데이터가 없습니다.")
    st.stop()

if len(test_df) == 0:
    st.error(
        "BMI 결측값 삭제 후 채점용 사람이 남지 않았습니다. "
        "결측값을 그대로 두도록 변경해 주세요."
    )
    st.stop()

X_train_raw = train_df[선택속성].apply(pd.to_numeric, errors="coerce")
X_test_raw = test_df[선택속성].apply(pd.to_numeric, errors="coerce")

y_train = train_df["stroke"].astype(int)
y_test = test_df["stroke"].astype(int)

# 훈련용 데이터에서만 중앙값을 계산한다.
imputer = SimpleImputer(strategy="median")
X_train = pd.DataFrame(
    imputer.fit_transform(X_train_raw),
    columns=선택속성,
    index=train_df.index,
)
X_test = pd.DataFrame(
    imputer.transform(X_test_raw),
    columns=선택속성,
    index=test_df.index,
)

if y_train.nunique() < 2:
    st.error(
        "전처리 후 훈련용 데이터에 뇌졸중과 비뇌졸중 사례가 "
        "모두 있어야 합니다."
    )
    st.stop()


# --------------------------------------------------
# 전후 모델 학습
# 두 결과를 항상 계산하므로 스위치 상태와 관계없이 비교 가능
# --------------------------------------------------
def fit_models(class_weight):
    probability_model = Pipeline([
        ("scale", StandardScaler()),
        ("model", LogisticRegression(
            max_iter=2000,
            random_state=42,
            class_weight=class_weight,
        )),
    ])

    question_model = DecisionTreeClassifier(
        max_depth=3,
        min_samples_leaf=5,
        random_state=42,
        class_weight=class_weight,
    )

    probability_model.fit(X_train, y_train)
    question_model.fit(X_train, y_train)

    classes = list(probability_model.named_steps["model"].classes_)
    probability = probability_model.predict_proba(X_test)[
        :, classes.index(1)
    ]
    probability_prediction = (probability >= 0.5).astype(int)
    question_prediction = question_model.predict(X_test).astype(int)

    return (
        probability_model,
        question_model,
        probability,
        probability_prediction,
        question_prediction,
    )


try:
    (
        prob_before,
        tree_before,
        prob_before_values,
        prob_before_pred,
        tree_before_pred,
    ) = fit_models(None)

    (
        prob_after,
        tree_after,
        prob_after_values,
        prob_after_pred,
        tree_after_pred,
    ) = fit_models("balanced")
except Exception as e:
    st.error(f"모델 학습 중 오류가 발생했습니다: {e}")
    st.stop()


# --------------------------------------------------
# 전후 결과 비교
# --------------------------------------------------
st.subheader("1. 전처리 전후 비교")

st.write(
    f"**현재 채점용: {len(test_df)}명 · "
    f"실제 뇌졸중: {int(y_test.sum())}명**"
)

predictions = {
    "확률 모델": {
        "전": prob_before_pred,
        "후": prob_after_pred,
    },
    "질문형 모델": {
        "전": tree_before_pred,
        "후": tree_after_pred,
    },
}

confusions = {
    model: {
        stage: confusion(y_test.to_numpy(), pred)
        for stage, pred in stages.items()
    }
    for model, stages in predictions.items()
}

for model_name in ["확률 모델", "질문형 모델"]:
    st.markdown(f"### {model_name} 혼동행렬")
    before_col, after_col = st.columns(2)

    with before_col:
        st.markdown("**무게 조정 전**")
        st.dataframe(
            matrix_table(confusions[model_name]["전"]),
            use_container_width=True,
        )

    with after_col:
        st.markdown("**무게 조정 후**")
        st.dataframe(
            matrix_table(confusions[model_name]["후"]),
            use_container_width=True,
        )

    metric_rows = []
    for stage in ["전", "후"]:
        c = confusions[model_name][stage]
        m = metrics(c)
        metric_rows.append({
            "상태": "무게 조정 전" if stage == "전" else "무게 조정 후",
            "정확도": percent(m["정확도"]),
            "정밀도": percent(m["정밀도"]),
            "재현율": percent(m["재현율"]),
            "F1": percent(m["F1"]),
        })

    st.dataframe(
        pd.DataFrame(metric_rows),
        use_container_width=True,
        hide_index=True,
    )

st.caption(
    "TP: 실제 뇌졸중을 뇌졸중으로 예측 · "
    "TN: 실제 비뇌졸중을 비뇌졸중으로 예측 · "
    "FP: 실제 비뇌졸중을 뇌졸중으로 예측 · "
    "FN: 실제 뇌졸중을 놓침. "
    "정밀도는 TP/(TP+FP), 재현율은 TP/(TP+FN), "
    "F1은 2TP/(2TP+FP+FN)으로 계산합니다."
)


def change_text(model_name):
    before = confusions[model_name]["전"]
    after = confusions[model_name]["후"]

    before_found = before["TP"]
    after_found = after["TP"]
    before_missed = before["FN"]
    after_missed = after["FN"]
    before_false = before["FP"]
    after_false = after["FP"]

    return (
        f"{model_name}: 찾아낸 환자 {before_found}명 → {after_found}명 · "
        f"놓친 환자 {before_missed}명 → {after_missed}명 · "
        f"헛짚은 사람 {before_false}명 → {after_false}명"
    )


st.markdown("**전처리 전후 변화 요약**")
st.write(change_text("확률 모델"))
st.write(change_text("질문형 모델"))


# --------------------------------------------------
# 시각화에 사용할 축 선택
# --------------------------------------------------
st.subheader("2. 실제 결과와 분류 경계 시각화")

st.caption(
    "점의 색은 실제 결과를 나타냅니다. 경계는 채점용 사람이 아니라 "
    "훈련용 데이터로 학습한 확률 모델의 뇌졸중 확률 0.5 기준입니다."
)

if len(선택속성) >= 3:
    x_axis = st.selectbox(
        "가로축",
        선택속성,
        index=0,
        format_func=lambda x: LABELS[x],
        key="preprocess_x",
    )
    y_candidates = [x for x in 선택속성 if x != x_axis]
    y_axis = st.selectbox(
        "세로축",
        y_candidates,
        index=0,
        format_func=lambda x: LABELS[x],
        key="preprocess_y",
    )
    z_candidates = [
        x for x in 선택속성
        if x not in [x_axis, y_axis]
    ]
    z_axis = st.selectbox(
        "세 번째 축",
        z_candidates,
        index=0,
        format_func=lambda x: LABELS[x],
        key="preprocess_z",
    )
else:
    x_axis = st.selectbox(
        "가로축",
        선택속성,
        index=0,
        format_func=lambda x: LABELS[x],
        key="preprocess_x",
    )
    y_candidates = [x for x in 선택속성 if x != x_axis]
    y_axis = st.selectbox(
        "세로축",
        y_candidates,
        index=0,
        format_func=lambda x: LABELS[x],
        key="preprocess_y",
    )
    z_axis = None

# 색상은 실제 정답에 따라 구분
actual_colors = np.where(y_test.to_numpy() == 1, "#D62728", "#1F77B4")
actual_names = np.where(
    y_test.to_numpy() == 1,
    "실제 뇌졸중",
    "실제 뇌졸중 아님",
)

# 훈련용 범위를 기준으로 격자 생성
def axis_range(series):
    low = float(series.min())
    high = float(series.max())
    pad = max((high - low) * 0.08, 0.1)
    return low - pad, high + pad


xlo, xhi = axis_range(X_train[x_axis])
ylo, yhi = axis_range(X_train[y_axis])

x_values = np.linspace(xlo, xhi, 100)
y_values = np.linspace(ylo, yhi, 100)
xx, yy = np.meshgrid(x_values, y_values)

# 다른 입력 속성은 훈련용 중앙값에 고정해 2D 경계를 계산한다.
def make_grid(x_name, y_name, x_grid, y_grid):
    grid = pd.DataFrame({
        feature: np.full(x_grid.size, float(X_train[feature].median()))
        for feature in 선택속성
    })
    grid[x_name] = x_grid.ravel()
    grid[y_name] = y_grid.ravel()
    return grid


grid2d = make_grid(x_axis, y_axis, xx, yy)

def positive_probability(model, data):
    classes = list(model.named_steps["model"].classes_)
    return model.predict_proba(data)[:, classes.index(1)]


before_surface = positive_probability(
    prob_before, grid2d
).reshape(xx.shape)

after_surface = positive_probability(
    prob_after, grid2d
).reshape(xx.shape)

# 2차원 산점도와 두 경계선
fig2d = go.Figure()

fig2d.add_trace(go.Scatter(
    x=X_test[x_axis],
    y=X_test[y_axis],
    mode="markers+text",
    text=[f"사람 {i + 1}" for i in range(len(test_df))],
    textposition="top center",
    marker=dict(
        size=13,
        color=actual_colors,
        line=dict(color="white", width=1),
    ),
    customdata=np.column_stack([
        actual_names,
        prob_before_pred,
        prob_after_pred,
    ]),
    name="채점용 사람",
    hovertemplate=(
        "가로축: %{x:.3f}<br>"
        "세로축: %{y:.3f}<br>"
        "실제 결과: %{customdata[0]}<br>"
        "무게 조정 전 예측: %{customdata[1]}<br>"
        "무게 조정 후 예측: %{customdata[2]}"
        "<extra></extra>"
    ),
))

# 실제 정답 범례
fig2d.add_trace(go.Scatter(
    x=[None], y=[None], mode="markers",
    marker=dict(size=10, color="#1F77B4"),
    name="실제 뇌졸중 아님",
))
fig2d.add_trace(go.Scatter(
    x=[None], y=[None], mode="markers",
    marker=dict(size=10, color="#D62728"),
    name="실제 뇌졸중",
))

# 확률 0.5 경계선을 contour로 표시
for surface, color, label in [
    (before_surface, "#2CA02C", "무게 조정 전 · 확률 0.5"),
    (after_surface, "#9467BD", "무게 조정 후 · 확률 0.5"),
]:
    fig2d.add_trace(go.Contour(
        x=x_values,
        y=y_values,
        z=surface,
        contours=dict(
            start=0.5,
            end=0.5,
            size=1,
            coloring="none",
            showlabels=False,
        ),
        line=dict(color=color, width=3),
        showscale=False,
        hoverinfo="skip",
        name=label,
    ))

fig2d.update_layout(
    title="2차원 산점도와 확률 0.5 경계선",
    xaxis_title=f"{LABELS[x_axis]} ({x_axis})",
    yaxis_title=f"{LABELS[y_axis]} ({y_axis})",
    template="plotly_white",
    height=650,
    legend_title="실제 결과 / 경계선",
)

st.plotly_chart(fig2d, use_container_width=True)

for label, surface in [
    ("무게 조정 전", before_surface),
    ("무게 조정 후", after_surface),
]:
    if np.nanmin(surface) > 0.5 or np.nanmax(surface) < 0.5:
        st.info(
            f"{label} 확률 0.5 경계선은 현재 그림 범위 안에 나타나지 않습니다."
        )
    else:
        st.caption(f"{label} 확률 0.5 경계선이 그림 범위와 만납니다.")


# --------------------------------------------------
# 선택 속성이 3개 이상이면 회전 가능한 3D 산점도와 평면
# --------------------------------------------------
if len(선택속성) >= 3:
    st.subheader("3. 3차원 산점도와 확률 0.5 평면")

    st.caption(
        "세 축은 위에서 선택한 세 속성입니다. "
        "마우스로 드래그하여 회전하고 확대할 수 있습니다."
    )

    x3lo, x3hi = axis_range(X_train[x_axis])
    y3lo, y3hi = axis_range(X_train[y_axis])
    z3lo, z3hi = axis_range(X_train[z_axis])

    x3 = np.linspace(x3lo, x3hi, 35)
    y3 = np.linspace(y3lo, y3hi, 35)
    xx3, yy3 = np.meshgrid(x3, y3)

    # 나머지 속성은 훈련용 중앙값으로 고정
    grid3d = pd.DataFrame({
        feature: np.full(xx3.size, float(X_train[feature].median()))
        for feature in 선택속성
    })
    grid3d[x_axis] = xx3.ravel()
    grid3d[y_axis] = yy3.ravel()

    # 평면의 z 좌표를 계산하기 위해 로지스틱 회귀식을 원래 단위로 변환
    def plane_z(model, x_name, y_name, z_name, gx, gy):
        scaler = model.named_steps["scale"]
        logistic = model.named_steps["model"]

        coefficients = logistic.coef_[0] / scaler.scale_
        intercept = logistic.intercept_[0] - np.sum(
            logistic.coef_[0] * scaler.mean_ / scaler.scale_
        )

        ix = 선택속성.index(x_name)
        iy = 선택속성.index(y_name)
        iz = 선택속성.index(z_name)

        if abs(coefficients[iz]) < 1e-12:
            return None

        # logit(p=0.5) = 0
        gz = -(
            intercept
            + coefficients[ix] * gx
            + coefficients[iy] * gy
        ) / coefficients[iz]

        return gz

    fig3d = go.Figure()

    fig3d.add_trace(go.Scatter3d(
        x=X_test[x_axis],
        y=X_test[y_axis],
        z=X_test[z_axis],
        mode="markers+text",
        text=[f"사람 {i + 1}" for i in range(len(test_df))],
        marker=dict(
            size=6,
            color=actual_colors,
            line=dict(color="white", width=1),
        ),
        customdata=np.column_stack([actual_names]),
        name="채점용 사람",
        hovertemplate=(
            f"{LABELS[x_axis]}: %{{x:.3f}}<br>"
            f"{LABELS[y_axis]}: %{{y:.3f}}<br>"
            f"{LABELS[z_axis]}: %{{z:.3f}}<br>"
            "실제 결과: %{customdata[0]}<extra></extra>"
        ),
    ))

    fig3d.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="markers",
        marker=dict(size=6, color="#1F77B4"),
        name="실제 뇌졸중 아님",
    ))
    fig3d.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode="markers",
        marker=dict(size=6, color="#D62728"),
        name="실제 뇌졸중",
    ))

    for model, color, label in [
        (prob_before, "#2CA02C", "무게 조정 전 0.5 평면"),
        (prob_after, "#9467BD", "무게 조정 후 0.5 평면"),
    ]:
        zz = plane_z(model, x_axis, y_axis, z_axis, xx3, yy3)

        if zz is None:
            st.info(
                f"{label}: 세 번째 축의 계수가 0에 가까워 "
                "이 방식으로 평면을 표시할 수 없습니다."
            )
            continue

        visible = np.isfinite(zz) & (zz >= z3lo) & (zz <= z3hi)

        if not visible.any():
            st.info(f"{label}은 현재 3차원 그림 범위 밖에 있습니다.")
            continue

        zz_plot = np.where(visible, zz, np.nan)

        fig3d.add_trace(go.Surface(
            x=xx3,
            y=yy3,
            z=zz_plot,
            opacity=0.35,
            showscale=False,
            surfacecolor=np.zeros_like(zz_plot),
            colorscale=[[0, color], [1, color]],
            name=label,
            hoverinfo="skip",
        ))

    fig3d.update_layout(
        title="세 속성의 3차원 산점도와 전후 경계 평면",
        scene=dict(
            xaxis_title=LABELS[x_axis],
            yaxis_title=LABELS[y_axis],
            zaxis_title=LABELS[z_axis],
        ),
        template="plotly_white",
        height=750,
        legend_title="실제 결과 / 경계 평면",
    )

    st.plotly_chart(fig3d, use_container_width=True)


# --------------------------------------------------
# 확률 모델이 놓친 환자 목록
# --------------------------------------------------
st.subheader("4. 확률 모델이 놓친 환자")

if 무게조정:
    선택예측 = prob_after_pred
    선택모델이름 = "무게 조정 후"
else:
    선택예측 = prob_before_pred
    선택모델이름 = "무게 조정 전"

놓친환자 = test_df.loc[
    (y_test.to_numpy() == 1) & (선택예측 == 0)
].copy()

st.caption(
    f"현재 스위치: {'켜짐' if 무게조정 else '꺼짐'} · "
    f"목록 기준: 확률 모델 {선택모델이름}"
)

st.markdown(f"**놓친 환자: {len(놓친환자)}명**")

if 놓친환자.empty:
    st.success("이 설정에서는 놓친 환자가 없습니다.")
else:
    번호 = (
        놓친환자["id"].to_numpy()
        if "id" in 놓친환자.columns
        else 놓친환자.index.to_numpy() + 1
    )

    목록 = pd.DataFrame({
        "번호": 번호,
        "나이": pd.to_numeric(
            놓친환자["age"], errors="coerce"
        ).to_numpy(),
        "고혈압 여부": 놓친환자["hypertension"].to_numpy(),
        "심장병 여부": 놓친환자["heart_disease"].to_numpy(),
    })

    목록 = 목록.sort_values(
        "나이",
        ascending=True,
        na_position="last",
    ).reset_index(drop=True)

    st.dataframe(
        목록,
        use_container_width=True,
        hide_index=True,
    )

st.warning(
    "이 페이지는 교육용 분류 실습입니다. 채점용 인원이 매우 적을 수 있으며, "
    "이 결과를 실제 의학적 진단이나 치료 결정에 사용해서는 안 됩니다."
)
