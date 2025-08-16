from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# from myapp import run_agent   # 🔹 keep it commented for now
# from starlette.concurrency import run_in_threadpool

app = FastAPI()

# Enable CORS so frontend (Railway domain) can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all domains for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return FileResponse("index.html")

class UserMessage(BaseModel):
    message: str

@app.post("/chat")
async def chat(user_message: UserMessage):
    # 🔹 Dummy response to test if connection works
    return {"response": f"✅ Backend is working! You said: {user_message.message}"}
