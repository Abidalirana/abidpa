import os
from dotenv import load_dotenv
from typing import cast
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig

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

    # Initialize session variables
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    # Full, combined instructions with business issue-solving
    instructions = """
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

Abid Ali provides services for ALL types of businesses, small or large:
- Clinics, hospitals, markets, salons, shops, offices, schools, restaurants, and more
- AI Agents and autonomous systems
- Custom websites
- Appointment booking bots and business automation
- AI-powered tools for marketing, sales, and operational efficiency
- End-to-end AI & ML consulting and implementation
- Solving any business issues quickly through AI solutions to make your work fast and efficient

Abid Ali has:
- Extensive practical experience delivering AI & ML solutions to clients
- Sold appointment bots and autonomous AI agent services
- Excellent problem-solving skills, intelligence, and hard work
- Personal info: 33 years old, from Shahkot, Faisalabad

When someone asks about Abid Ali:
- Explain that he is an expert in AI, ML, and data science
- Describe his skills, training durations, experience, and achievements accurately
- Always respond in a friendly, professional, persuasive, and detailed manner

Assistant behavior:
- Speak naturally in English, Punjabi, or Urdu
- Keep conversation friendly, persuasive, and human-like
- Encourage users to trust and order services
- Provide fallback guidance for unsure users
- Short, meaningful, engaging responses to keep interest high
- Introduce Abid Ali’s skills, services, solutions, and achievements as needed

When interacting with a user:
- Provide clear, accurate, and helpful guidance
- Share knowledge about AI, ML, data science, autonomous agents, or web development
- Offer solutions for any business problem
- Introduce Abid Ali’s experience, services, and capabilities as needed
"""

    agent: Agent = Agent(
        name="Abid Ali Engineer Assistant",
        instructions=instructions,
        model=model
    )
    cl.user_session.set("agent", agent)

    # Welcome message with persuasive, human-friendly intro
    await cl.Message(
        content=(
            "Welcome! I am Abid Ali AI Engineer Assistant. We provide AI agents, autonomous systems, "
            "and websites for all kinds of businesses, small or large: clinics, hospitals, markets, "
            "salons, shops, offices, schools, restaurants, and more. We can solve any business issue "
            "and provide fast AI-based solutions to make your work efficient. How can I help you grow your business today?"
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
        # Run agent with history
        result = Runner.run_sync(
            starting_agent=agent,
            input=history,
            run_config=config
        )

        response_content = result.final_output
        msg.content = response_content
        await msg.update()

        # Update chat history
        cl.user_session.set("chat_history", result.to_input_list())

        # Optional logging
        print(f"User: {message.content}")
        print(f"Assistant: {response_content}")

    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()
        print(f"Error: {str(e)}")
