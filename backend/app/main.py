from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.routers import chat, courses, knu_import, timetables, tools
from app.services.knu_session import manager as knu_manager
from app.settings import FRONTEND_ORIGINS

# backend/.env 파일이 있으면 환경변수(OPENAI_API_KEY 등)를 읽어 온다.
load_dotenv()

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    # 서버를 끄거나 코드 변경으로 다시 시작할 때, 열려 있는 원격 브라우저를 모두 닫는다.
    knu_manager.shutdown()


app = FastAPI(title="Course Planner Agent API", lifespan=lifespan)

# 프론트엔드(Next.js 개발 서버)에서 이 API를 호출할 수 있도록 허용한다.
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(courses.router)
app.include_router(knu_import.router)
app.include_router(timetables.router)
app.include_router(tools.router)


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    """조건을 고르면 시간표를 그려 주는 시연용 화면."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    """서버가 살아 있는지 확인하는 엔드포인트."""
    return {"status": "ok"}
