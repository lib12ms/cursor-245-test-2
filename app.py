import os

import requests
import streamlit as st

st.set_page_config(page_title="ISBN -> 245/700", page_icon="📚", layout="centered")
st.title("ISBN -> 24500/7001 자동 생성")
st.caption(
    "Render에 배포된 백엔드를 호출해 "
    "KORMARC `245  00`과 `700  1` 필드를 자동 생성합니다."
)

isbn_input = st.text_input("ISBN 입력", placeholder="예: 9788998139766")
run = st.button("24500/7001 생성", type="primary")
backend_base = os.getenv("BACKEND_URL", "").strip().rstrip("/")
if not backend_base:
    backend_base = "http://localhost:8000"
    st.warning("`BACKEND_URL`이 없어 로컬 기본값(`http://localhost:8000`)을 사용합니다.")
st.info(f"현재 백엔드 URL: `{backend_base}`")

if run:
    try:
        response = requests.post(
            f"{backend_base}/komarc",
            json={"isbn": isbn_input.strip(), "source": "aladin"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        isbn = payload["isbn"]
        result_text = payload["result_text"]
        markdown_text = payload["markdown_text"]

        st.success("24500/7001 생성 완료")
        st.code(result_text, language="text")
        st.download_button(
            label="결과 다운로드 (.txt)",
            data=result_text,
            file_name=f"komarc_{isbn}.txt",
            mime="text/plain",
        )
        st.download_button(
            label="마크다운 다운로드 (.md)",
            data=markdown_text,
            file_name=f"komarc_{isbn}.md",
            mime="text/markdown",
        )
    except requests.HTTPError:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        st.error(f"생성 실패: {detail}")
    except Exception as exc:  # noqa: BLE001 - 사용자 입력 도구이므로 예외 메시지 직접 노출
        st.error(f"생성 실패: {exc}")


