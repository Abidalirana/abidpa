from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from myapp import run_agent   # ✅ this is the code you showed
from starlette.concurrency import run_in_threadpool

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
    try:
        # ✅ Run agent in thread pool so async is safe
        response = await run_in_threadpool(run_agent, user_message.message)
        return {"response": response}
    except Exception as e:
        # ✅ Add safe error handling (useful for Railway deploys)
        return {"response": f"⚠️ Server Error: {str(e)}"}
