
import pandas as pd
import streamlit as st

st.title("📝 내가 만든 모델 소개")

st.write(
    "분석한 데이터와 모델의 결과를 정리해 보세요. "
    "아래 내용을 직접 작성할 수 있습니다."
)

질문들 = [
    "무슨 데이터입니까",
    "무엇을 보고 맞힙니까",
    "무엇을 고쳤습니까",
    "이 모델을 검진센터가 사용해도 됩니까",
    "이 모델이 못 하는 것 한 가지",
]

for 질문 in 질문들:
    st.text_area(질문, key=질문, height=120)

st.subheader("📊 모델 점수 비교")

점수표 = pd.DataFrame({
    "항목": ["정확도", "재현율", "F1", "찾아낸 환자", "헛짚은 사람"],
    "고치기 전": [""] * 5,
    "고친 뒤": [""] * 5,
})

st.data_editor(
    점수표,
    hide_index=True,
    disabled=["항목"],
    num_rows="fixed",
    width="stretch",
    key="모델점수",
)

st.subheader("📄 한 장으로 보기")

for 질문 in 질문들:
    st.markdown(f"### {질문}")
    답변 = st.session_state.get(질문, "").strip()
    st.write(답변 if 답변 else "아직 적지 않았습니다.")

st.markdown("### 점수 비교")
st.dataframe(
    st.session_state.get("모델점수", 점수표),
    hide_index=True,
    width="stretch",
)
