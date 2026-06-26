import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from database import init_db
from scheduler import run_pipeline
from routes import users, feed, browse, ratings, categories, articles

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    run_pipeline()  # fetch + categorize + embed
    scheduler.add_job(run_pipeline, "interval", hours=1, next_run_time=datetime.now())
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Ukrainian News Recommender API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://holamundoo.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(feed.router)
app.include_router(browse.router)
app.include_router(ratings.router)
app.include_router(categories.router)

app.include_router(articles.router)


@app.get("/health")
def health():
    return {"status": "ok"}
