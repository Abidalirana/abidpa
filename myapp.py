import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from db import SessionLocal, UserRequest, ChatHistory  # your DB models

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please define it in your .env file.")

# External client
external_client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

# Model
model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

# Run config
config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# Agent instructions
instructions = """
You are 'Abid Ali AI Engineer Assistant', representing Abid Ali.

Collect user details: name, phone, email, business type, location, purpose, days needed
Store in PostgreSQL table `user_requests`
Save full chat history in `chat_history` table linked to `user_request_id`
Respond concisely in English, Urdu, or Punjabi.
"""

agent = Agent(
    name="Abid Ali Engineer Assistant",
    instructions=instructions,
    model=model
)

# ------------------ Async agent runner ------------------
async def run_agent_async(user_input: str, user_details: dict = None):
    db = SessionLocal()
    try:
        # Save user request
        user_request = UserRequest(
            name=user_details.get("name", "Unknown") if user_details else "Unknown",
            phone=user_details.get("phone", "Unknown") if user_details else "Unknown",
            email=user_details.get("email") if user_details else None,
            business_type=user_details.get("business_type", "Unknown") if user_details else "Unknown",
            location=user_details.get("location", "Unknown") if user_details else "Unknown",
            purpose=user_input,
            days_needed=user_details.get("days_needed") if user_details else None
        )
        db.add(user_request)
        db.commit()
        db.refresh(user_request)

        history = [{"role": "user", "content": user_input}]

        # Run the agent asynchronously
        result = await Runner.run(starting_agent=agent, input=history, run_config=config)
        response = result.final_output

        # Save chat history
        chat_entry = ChatHistory(
            user_request_id=user_request.id,
            role="assistant",
            content=response
        )
        db.add(chat_entry)
        db.commit()

        return response
    finally:
        db.close()

# ------------------ Sync wrapper for FastAPI ------------------
def run_agent(user_input: str, user_details: dict = None):
    import asyncio
    return asyncio.run(run_agent_async(user_input, user_details))
