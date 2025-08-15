from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
import os

# Initialize your Gemini/OpenAI agent once
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)

instructions = "Your full agent instructions here..."  # copy your detailed instructions
agent = Agent(name="Abid Ali Engineer Assistant", instructions=instructions, model=model)

app = FastAPI()

class MessageRequest(BaseModel):
    messages: List[Dict]  # [{"role": "user", "content": "Hello"}]

@app.post("/chat")
async def chat_endpoint(request: MessageRequest):
    history = request.messages
    result = Runner.run_sync(starting_agent=agent, input=history, run_config=config)
    return {"response": result.final_output}
