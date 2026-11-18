import os

# 이 API 를 부를 수 있는 다른 주소 (프론트엔드 개발 서버).
# 환경변수 FRONTEND_ORIGINS 에 쉼표로 여러 주소를 적으면 그것을 쓴다. 예: http://localhost:3001
FRONTEND_ORIGINS = [
    origin.strip().rstrip("/")
    for origin in os.environ.get("FRONTEND_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]
