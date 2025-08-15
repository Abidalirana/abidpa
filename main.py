import os
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from db import SessionLocal, UserRequest, ChatHistory

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is not set. Please define it in your .env file.")

# ------------------ Chat Start ------------------
@cl.on_chat_start
async def start():
    # Initialize OpenAI / Gemini client
    external_client = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client
    )

    config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )

    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    instructions = """
Your detailed agent instructions here, including collecting user details and solving business issues.
"""
    agent: Agent = Agent(
        name="Abid Ali Engineer Assistant",
        instructions=instructions,
        model=model
    )
    cl.user_session.set("agent", agent)

    await cl.Message(
        content=(
            "Welcome! I am Abid Ali AI Engineer Assistant. "
            "We provide AI agents, autonomous systems, and websites for all businesses. "
            "We can solve any business issue fast and efficiently. How can I help you today?"
        )
    ).send()

# ------------------ On Message ------------------
@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="Thinking...")
    await msg.send()

    agent: Agent = cast(Agent, cl.user_session.get("agent"))
    config: RunConfig = cast(RunConfig, cl.user_session.get("config"))
    history = cl.user_session.get("chat_history") or []

    # Append user message to history
    history.append({"role": "user", "content": message.content})

    try:
        result = Runner.run_sync(
            starting_agent=agent,
            input=history,
            run_config=config
        )

        response_content = result.final_output
        msg.content = response_content
        await msg.update()

        # Save user request if detected
        save_user = "name" in message.content.lower() or "phone" in message.content.lower()
        session = SessionLocal()
        user_request_id = None

        if save_user:
            user_request = UserRequest(
                name="Sample Name",  # Replace with extraction logic
                phone="123456789",   # Replace with extraction logic
                email="sample@example.com",
                business_type="clinic",
                location="Faisalabad",
                purpose="AI automation",
                days_needed="7"
            )
            session.add(user_request)
            session.commit()
            user_request_id = user_request.id
            await cl.Message(content="✅ Your request has been saved successfully!").send()

        # Save full chat history
        for entry in history:
            chat_entry = ChatHistory(
                user_request_id=user_request_id,
                role=entry["role"],
                content=entry["content"]
            )
            session.add(chat_entry)
        session.commit()
        session.close()

        # Update session history
        cl.user_session.set("chat_history", result.to_input_list())

        print(f"User: {message.content}")
        print(f"Assistant: {response_content}")

    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()
        print(f"Error: {str(e)}")


#     uv run chainlit run main.py -w