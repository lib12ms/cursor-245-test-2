import os
import time
from typing import Optional

import requests
import streamlit as st
from komarc_from_isbn import (
    DEFAULT_ALADIN_TTB_KEY,
    build_komarc,
    build_markdown_output,
    fetch_book_info_by_isbn,
    normalize_isbn,
)

st.set_page_config(page_title="ISBN -> 245/700", page_icon="📚", layout="centered")
st.title("ISBN -> 24500/7001 자동 생성")
st.caption(
    "ISBN 메타데이터를 조회해 "
    "KORMARC `245  00`과 `700  1` 필드를 자동 생성합니다."
)

isbn_input = st.text_input("ISBN 입력", placeholder="예: 9788998139766")
run = st.button("24500/7001 생성", type="primary")
use_backend_api = os.getenv("USE_BACKEND_API", "").strip().lower() in {"1", "true", "yes"}
backend_base = os.getenv("BACKEND_URL", "").strip().rstrip("/")
if use_backend_api:
    if not backend_base:
        backend_base = "http://localhost:8000"
        st.warning("`BACKEND_URL`이 없어 로컬 기본값(`http://localhost:8000`)을 사용합니다.")
    st.info(f"동작 모드: API 호출 (`{backend_base}`)")
else:
    st.info("동작 모드: 앱 내부 직접 처리 (백엔드 서비스 기동 불필요)")

def _post_komarc(isbn: str) -> requests.Response:
    """Render 무료 티어 슬립 직후 첫 요청이 실패할 수 있어 짧게 재시도합니다."""
    url = f"{backend_base}/komarc"
    body = {"isbn": isbn, "source": "aladin"}
    last_exc: Optional[BaseException] = None
    for attempt in range(3):
        try:
            return requests.post(url, json=body, timeout=45)
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
            last_exc = exc
            if attempt < 2:
                time.sleep(6)
    assert last_exc is not None
    raise last_exc


def _build_komarc_locally(isbn: str) -> dict:
    normalized = normalize_isbn(isbn)
    nl_raw = os.getenv("NL_SEOKJI_CERT_KEY") or os.getenv("NL_ISBN_CERT_KEY") or ""
    aladin_key = os.getenv("ALADIN_TTB_KEY", "").strip() or DEFAULT_ALADIN_TTB_KEY
    book = fetch_book_info_by_isbn(
        isbn=normalized,
        source="aladin",
        aladin_ttb_key=aladin_key,
        nl_seokji_cert_key=nl_raw.strip() or None,
    )
    komarc_lines = build_komarc(book)
    result_text = "\n".join(komarc_lines)
    markdown_text = build_markdown_output(book, komarc_lines)
    return {
        "isbn": normalized,
        "result_text": result_text,
        "markdown_text": markdown_text,
    }


if run:
    try:
        if not isbn_input.strip():
            st.error("ISBN을 입력해 주세요.")
            st.stop()

        if use_backend_api:
            with st.spinner("백엔드에 요청 중입니다… (Render 무료 호스트는 잠에서 깨는 데 1분 가까이 걸릴 수 있습니다)"):
                response = _post_komarc(isbn_input.strip())
            response.raise_for_status()
            payload = response.json()
        else:
            with st.spinner("도서 정보를 조회하고 KORMARC를 생성 중입니다…"):
                payload = _build_komarc_locally(isbn_input.strip())

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
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        st.error(
            "백엔드에 연결하지 못했습니다. Render 무료 서비스는 잠시 멈춘 뒤 첫 접속 때 깨어나며, "
            "그동안 시간이 걸리거나 한 번 실패할 수 있습니다. 잠시 후 버튼을 다시 눌러 보세요."
        )
        st.caption(str(exc))
    except Exception as exc:  # noqa: BLE001 - 사용자 입력 도구이므로 예외 메시지 직접 노출
        st.error(f"생성 실패: {exc}")


