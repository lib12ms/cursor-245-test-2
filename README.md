# ISBN -> KORMARC 자동 생성기

ISBN을 입력하면 **알라딘 API**를 조회해서  
KORMARC `245  00`, `700`, `900  10` 필드를 자동 생성하는 도구입니다.

## 출력 규칙

- `245  00`
  - 서명: `$a`
  - 부제: `:$b`
  - 권차/편차기호: `.$n` (부제 뒤)
  - 첫 번째 저자: `/$d`
  - 두 번째 저자부터: `,$e`
  - 번역자/그린이/디자이너 등: `;$e`
- `700  1`
  - 개인명은 `700  1$a이름`
  - 협의회/기관/위원회 등 단체명은 `700  0$a이름`
  - 역할어 `$e`는 생성하지 않음
- 외국인 원저자 처리
  - 알라딘 API에 원어명이 없으면 저자 개요 페이지를 추가 조회해 원어명을 보완
  - 원어명이 확인되면 `700  1$a성, 이름`으로 도치 출력
    - 예: `Rami Kaminski` -> `Kaminski, Rami`
  - 같은 저자의 한글 표기는 `900  10$a성, 이름`으로 도치 출력
    - 예: `라미 카민스키` -> `카민스키, 라미`

예시:

```text
245  00$a서명:$b부제.$n1권/$d첫저자,$e둘째저자;$e번역자;$e그린이
700  1$a첫저자
700  1$a둘째저자
700  1$a번역자
700  0$aOO협의회
700  1$aKaminski, Rami
900  10$a카민스키, 라미
```

## 사전 준비 (알라딘 API)

기본 내장 TTBKey: `ttbboyeong09010919001`

필요하면 환경변수 `ALADIN_TTB_KEY`로 덮어쓸 수 있습니다.

### PowerShell 설정 예시

```powershell
$env:ALADIN_TTB_KEY = "내_알라딘_TTBKey"
```

## 실행 방법

### 1) CLI

```powershell
python komarc_from_isbn.py 9788998139766
```

또는 인자 없이 실행 후 ISBN 입력:

```powershell
python komarc_from_isbn.py
```

> 기본 소스는 `aladin`입니다.
> 실행 시 `komarc_<ISBN>.md` 파일을 자동으로 생성합니다.

### 2) 백엔드 API (Render/로컬)

백엔드는 FastAPI로 동작하며, Render에 배포할 수 있습니다.

로컬 실행:

```powershell
uvicorn backend_api:app --host 0.0.0.0 --port 8000
```

헬스체크:

```text
GET /health
```

KORMARC 생성:

```text
POST /komarc
{
  "isbn": "9788998139766",
  "source": "aladin"
}
```

Render 배포:

- 저장소 루트의 `render.yaml` 사용
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn backend_api:app --host 0.0.0.0 --port $PORT`
- 환경변수(필요 시)
  - `ALADIN_TTB_KEY`
  - `NL_SEOKJI_CERT_KEY`
- 배포 후 백엔드 URL 예시
  - `https://isbn-komarc-backend.onrender.com`

### 3) Streamlit 프론트엔드 (고정)

설치:

```powershell
pip install -r requirements.txt
```

프론트는 Streamlit으로 고정하고, 반드시 백엔드 API를 호출합니다.

실행:

```powershell
python -m streamlit run app.py
```

필수 환경변수:

- `BACKEND_URL` (예: `https://isbn-komarc-backend.onrender.com`)

로컬/배포용 샘플 파일:

- `.env.example`
- `.streamlit/secrets.toml.example`

### 4) Streamlit Cloud 배포 체크리스트

- GitHub 저장소 루트에 아래 파일이 있어야 합니다.
  - `app.py`
  - `backend_api.py`
  - `render.yaml`
  - `requirements.txt`
  - `runtime.txt` (현재 `python-3.11.9`)
- Streamlit Cloud 앱 설정
  - Repository: 이 프로젝트 저장소
  - Branch: 배포할 브랜치(보통 `main`)
  - Main file path: `app.py`
- Streamlit Cloud Secrets
  - `BACKEND_URL = "Render에 배포한 백엔드 URL"`

## 실배포 빠른 순서

1. GitHub에 현재 코드를 push
2. Render에서 `New +` -> `Blueprint`로 저장소 연결
3. `render.yaml` 기반으로 `isbn-komarc-backend` 배포
4. Render 대시보드에서 환경변수 입력
   - `ALADIN_TTB_KEY` (권장)
   - `NL_SEOKJI_CERT_KEY` (선택)
5. 배포 완료 후 `https://...onrender.com/health` 확인 (`{"status":"ok"}`)
6. Streamlit Cloud에서 같은 저장소의 `app.py` 배포
7. Streamlit Cloud Secrets에 아래 추가:
   - `BACKEND_URL = "https://...onrender.com"`
8. Streamlit 앱에서 ISBN 입력 후 결과/다운로드 동작 확인

## 생성 파일

- 텍스트 출력: `komarc_<ISBN>.txt` (Streamlit 다운로드)
- 마크다운 출력: `komarc_<ISBN>.md` (CLI 자동 생성 + Streamlit 다운로드)

## 파일 구성

- `komarc_from_isbn.py`: ISBN 조회 + 245/700/900 생성 + Markdown 생성
- `backend_api.py`: Render 배포용 FastAPI 백엔드
- `app.py`: Streamlit 프론트엔드(백엔드 API 호출)
- `requirements.txt`: 의존성
