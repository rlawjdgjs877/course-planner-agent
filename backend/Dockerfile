# Plann 백엔드 (FastAPI). 공개 배포용: 학교 로그인 불러오기(Playwright)는 넣지 않고 끈다.
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 KNU_IMPORT_ENABLED=0
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# Render 등은 PORT 환경변수로 포트를 알려 준다.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
