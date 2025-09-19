import os
import requests
from fastapi import FastAPI, Request
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sharperdragon.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Suggestion(BaseModel):
    suggestion: str

GITHUB_TOKEN = os.getenv("GH_TOKEN")
REPO = "sharperdragon/study_tables"

@app.post("/api/suggest")
def create_suggestion(s: Suggestion):
    url = f"https://api.github.com/repos/{REPO}/issues"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    data = {
        "title": "User Suggestion",
        "body": s.suggestion
    }
    r = requests.post(url, json=data, headers=headers)
    return {"status": r.status_code, "detail": r.json()}