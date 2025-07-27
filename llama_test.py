from ollama import chat, ChatResponse

from google.adk.agents import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types


import asyncio

prompt = """You are a journalist in this climate change museum, ask a question about the crude oil exhibit.
"""

agent = LlmAgent(
	model=LiteLlm(model="ollama_chat/mistral"),
	name="first_agent",
	instruction="""From the input city, determine what country is it""",
	description="""From the input city, determine what country is it""",
)
agent2 = LlmAgent(
	model=LiteLlm(model="ollama_chat/mistral"),
	name="second_agent",
	instruction=prompt,
	description=prompt,
)

both_agents = SequentialAgent(
	name="seq", sub_agents=[agent, agent2])

APP_NAME = "ecogame"
USER_ID = "user"
SESSION_ID="session"

session_service = InMemorySessionService()
session = asyncio.run(session_service.create_session(
	app_name=APP_NAME,
	user_id=USER_ID,
	session_id=SESSION_ID,
	state={}
))


runner = Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

events = runner.run(user_id=USER_ID, session_id=SESSION_ID,
	new_message=types.Content(role="user", parts=[types.Part(text="Australia")])
)

for ev in events :
	print(ev, flush=True)
