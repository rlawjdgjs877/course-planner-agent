from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# backend/.env 파일이 있으면 환경변수(OPENAI_API_KEY 등)를 읽어 온다.
load_dotenv()

app = FastAPI(title="Course Planner Agent API")

# 프론트엔드(Next.js 개발 서버)에서 이 API를 호출할 수 있도록 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """서버가 살아 있는지 확인하는 엔드포인트."""
    return {"status": "ok"}
