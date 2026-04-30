#!/usr/bin/env bash
set -euo pipefail
# Render 동일 리전 웹 서비스 간 사설망 주소 (무료 티어에서 공개 URL 대신 사용)
export BACKEND_URL="http://${BACKEND_INTERNAL_HOST}:${BACKEND_INTERNAL_PORT}"
exec streamlit run app.py --server.headless true --server.port "${PORT}" --server.address 0.0.0.0
