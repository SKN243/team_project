import json
import re
import streamlit as st

AEA_PATH = "aea_faq_final.json"      
JEVS_PATH = "jevs_faq_final.json"   



def load_faq(path: str, source: str, q_prefix: str = ""):
    with open(path, "r", encoding="utf-8") as f:
        # JSON -> 파이썬 리스트/딕셔너리로 변환
        data = json.load(f)

    faq = []

    for item in data:
        # question/answer 키가 없을 수도 있으므로 get으로 가져옴
        q = str(item.get("question", "")).strip()
        a = str(item.get("answer", "")).strip()

        # 질문과 답변이 둘 다 있을 때만 저장(빈 데이터 제외)
        if q and a:
            faq.append({
                "question": q_prefix + q,
                "answer": a,               
                "source": source           
            })

    return faq


# 크롤링으로 가져온 답변에서 불필요한 텍스트 제거
def clean_answer(answer: str, source: str) -> str:
    # 답변 양 끝 공백/줄바꿈 정리
    a = answer.strip()

    if source == "AEA":
        # 해당 키워드가 나오면 그 지점부터 뒤는 잘라냄
        cut_keywords = [
            "전기차 충전인프라",
            "지방자치단체 바로가기",
            "관계기관 바로가기",
            "협회소개",
            "개인정보보호방침",
            "Copyright",
            "상호명:",
        ]

        # 키워드를 순서대로 찾다가 처음 발견되는 지점에서 잘라내기
        for kw in cut_keywords:
            idx = a.find(kw)  # kw가 등장하는 위치(없으면 -1)
            if idx != -1:
                a = a[:idx].rstrip()  # kw가 시작되기 전까지만 남김
                break

        return a

    if source == "JEVS":
        # "검색" 줄 다음에 "Previous"가 와서 이 지점부터 뒤를 잘라냄
        cutting_point = "\n검색\nPrevious"
        idx = a.find(cutting_point)

        # 패턴이 있으면 해당 위치 전까지만 남김
        if idx != -1:
            return a[:idx].rstrip()

        # 정규식으로 "다음 글 목록" 같은 형태를 찾음
        # ex) \n7\n고장\n..., \n8\n사용법\n... 같은 불필요한 리스트가 답변 뒤에 붙는 경우
        m = re.search(r"\n\d+\n(고장|사용법)\n", a)

        # 패턴을 찾으면 그 패턴 시작 전까지만 남김
        if m:
            return a[:m.start()].rstrip()

        # 위 조건에 안 걸리면(불필요한 꼬리 없음) 그대로 반환
        return a

    # source가 AEA/JEVS가 아니면 원본 그대로 반환
    return a


st.set_page_config(page_title="EV FAQ", layout="wide")
st.title("전기차 FAQ")


try:
    aea_list = load_faq(AEA_PATH, source="AEA")

    # JEVS FAQ 로드 (질문 앞에 [충전기 관련] 라벨 추가) / AEA 와 JEVS 라벨의 통일성을 위해서
    jevs_list = load_faq(JEVS_PATH, source="JEVS", q_prefix="[충전기 관련] ")
except Exception as e:
    # 파일이 없거나 JSON이 깨졌거나 하면 화면에 에러 표시 후 중단
    st.error(f"JSON 로딩 실패: {e}")
    st.stop()

faq_list = aea_list + jevs_list

keyword = st.text_input("검색어", value="").strip()

# 체크하면 질문에서만 검색 / 체크 해제하면 질문+답변에서 검색
only_in_question = st.checkbox("질문에서만 검색", value=False)


for item in faq_list:
    item["answer_view"] = clean_answer(item["answer"], item["source"])

# 검색어가 없으면 전체를 보여줌
if keyword == "":
    filtered = faq_list
else:
    filtered = []
    for item in faq_list:
        if only_in_question:
            # 질문에서만 검색
            if keyword in item["question"]:
                filtered.append(item)
        else:
            # 질문 또는 답변에서 검색
            if (keyword in item["question"]) or (keyword in item["answer_view"]):
                filtered.append(item)


st.write(f"총 **{len(faq_list)}개** / 검색 결과 **{len(filtered)}개**")
st.divider()

if len(filtered) == 0:
    st.info("검색어에 맞는 FAQ가 없습니다.")
else:
    for i, item in enumerate(filtered, start=1):
        title = f"{i}. {item['question']}"
        with st.expander(title, expanded=False):
            st.write(item["answer_view"])
