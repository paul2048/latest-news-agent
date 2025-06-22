from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Literal
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


class ChatMessage(BaseModel):
    author: Literal["user", "agent"]
    message: str


class UserInput(BaseModel):
    userInput: str = Field(..., min_length=1)


CHAT_HISTORY: List[ChatMessage] = []


PREFERENCES_QUESTIONS = [
    "First, what's your preferred tone of voice (e.g., formal, casual, enthusiastic)?",
    "Got it. What's your preferred response format (e.g., bullet points, paragraphs)?",
    "Okay. What's your language preference?",
    "Next, what's your interaction style (e.g., concise, detailed)?",
    "Almost done! What are your preferred news topics?",
    "Thank you! I have all your preferences. What news can I get for you?",
]

NEWS_REQUEST_PROMPT = """
You are a helpful assistant that provides news updates based on user preferences.
The user hass the following preferences:
  - preferred tone of voice: {tone_of_voice}
  - preferred response format: {response_format}
  - language preference: {language_preference}
  - interaction style: {interaction_style}
  - preferred news topics: {news_topics}
"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting up. Initializing chat history...")
    CHAT_HISTORY.clear()
    CHAT_HISTORY.append(ChatMessage(author="agent", message=PREFERENCES_QUESTIONS[0]))
    yield
    print("Server shutting down.")

app = FastAPI(lifespan=lifespan)


origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/chat/history", response_model=List[ChatMessage])
async def get_history():
    """Returns the current state of the global chat history."""
    return CHAT_HISTORY


@app.post("/chat", response_model=List[ChatMessage])
async def chat(request: UserInput):
    """Appends a user message and an agent response to the global history."""
    user_input = request.userInput

    CHAT_HISTORY.append(ChatMessage(author="user", message=user_input))

    # Determine agent's response (either a preference question or a response from the API request)
    num_user_responses = sum(1 for msg in CHAT_HISTORY if msg.author == 'user')
    agent_response_text = ""
    if num_user_responses < len(PREFERENCES_QUESTIONS):
        agent_response_text = PREFERENCES_QUESTIONS[num_user_responses]
    else:
        # TODO: API REQUEST
        ...

    CHAT_HISTORY.append(ChatMessage(author="agent", message=agent_response_text))

    return CHAT_HISTORY
