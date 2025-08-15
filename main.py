import os
import json  # <-- import json
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
    external_client = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )

    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client
    )

    config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    instructions = """
You are 'Abid Ali Artificial Intelligence Engineer Assistant', representing Abid Ali.
...
"""
    agent: Agent = Agent(name="Abid Ali Engineer Assistant",     instructions = """
You are 'Abid Ali Artificial Intelligence Engineer Assistant', representing Abid Ali.

Abid Ali is a highly skilled AI Engineer and Developer with expertise in:
- Python programming (1 year intensive study and projects)
- Machine Learning (6 months intensive training and practical projects)
- Artificial Intelligence (6 months intensive training and practical projects)
- Deep Learning (6 months hands-on experience)
- Data Science (8 months hands-on projects and analysis)
- AI Agents and Autonomous Systems development
- Building chatbots, AI assistants, and custom websites
- Data Analysis, WordPress development, and delivering full-stack solutions

Data collection:
- Collect user details: name, phone, email, business type, location, purpose, days needed
- Store in PostgreSQL table `user_requests`
- Save full chat history in `chat_history` table linked to `user_request_id`
- Confirm to the user that their request has been saved
- Speak politely and naturally in English, Urdu, or Punjabi

Services:
- AI Agents, autonomous systems, custom websites
- Appointment booking bots, automation, marketing tools
- Solve business issues quickly via AI solutions

Assistant behavior:
- Persuasive, human-like, engaging, and concise
- Introduce Abid Ali’s skills, services, solutions, and achievements
- Provide fallback guidance for unsure users
"""
, model=model)
    cl.user_session.set("agent", agent)

    await cl.Message(
        content= "Welcome! I am Abid Ali AI Engineer Assistant. We provide AI agents, autonomous systems, "
                 "and websites for all kinds of businesses, small or large. We can solve any business issue "
                 "fast and efficiently. How can I help you today?"
    ).send()

# ------------------ On Message ------------------
@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="Thinking...")
    await msg.send()

    agent: Agent = cast(Agent, cl.user_session.get("agent"))
    config: RunConfig = cast(RunConfig, cl.user_session.get("config"))
    history = cl.user_session.get("chat_history") or []

    # Append user message
    history.append({"role": "user", "content": message.content})

    session = SessionLocal()
    user_request_id = None

    try:
        # Run agent
        result = Runner.run_sync(starting_agent=agent, input=history, run_config=config)
        response_content = result.final_output
        msg.content = response_content
        await msg.update()

        # Save user request if first time
        if not cl.user_session.get("user_request_id"):
            user_request = UserRequest(
                name="Sample Name",
                phone="123456789",
                email="sample@example.com",
                business_type="clinic",
                location="Faisalabad",
                purpose="AI automation",
                days_needed="7"
            )
            session.add(user_request)
            session.commit()
            user_request_id = user_request.id
            cl.user_session.set("user_request_id", user_request_id)
            await cl.Message(content="✅ Your request has been saved successfully!").send()
        else:
            user_request_id = cl.user_session.get("user_request_id")

        # Save full conversation
        for entry in history[-2:]:  # last user + assistant messages
            # Convert content to JSON string if it's a dict/list
            content_to_save = entry["content"]
            if isinstance(content_to_save, (dict, list)):
                content_to_save = json.dumps(content_to_save)

            chat_entry = ChatHistory(
                user_request_id=user_request_id,
                role=entry["role"],
                content=content_to_save
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
