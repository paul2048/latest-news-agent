from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Literal
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
from exa_py import Exa
from dotenv import load_dotenv


class ChatMessage(BaseModel):
    author: Literal["user", "agent"]
    message: str


class UserInput(BaseModel):
    userInput: str = Field(..., min_length=1)


chat_history: List[ChatMessage] = []


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
The user has the following preferences:
  - preferred tone of voice: {tone_of_voice}
  - preferred response format: {response_format}
  - language preference: {language_preference}
  - interaction style: {interaction_style}
  - preferred news topics: {news_topics}
"""

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
exa = Exa(api_key=os.getenv("EXA_API_KEY"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server starting up. Initializing chat history...")
    chat_history.clear()
    chat_history.append(
        ChatMessage(author="agent", message=PREFERENCES_QUESTIONS[0])
    )
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
    return chat_history

# Clear chat history endpoint
@app.post("/chat/clear")
async def clear_history():
    """Clears the global chat history."""
    chat_history.clear()
    chat_history.append(
        ChatMessage(author="agent", message=PREFERENCES_QUESTIONS[0])
    )
    return {"message": "Chat history cleared."}


@app.post("/chat", response_model=List[ChatMessage])
async def chat(request: UserInput):
    """Appends a user message and an agent response to the global history."""
    user_input = request.userInput

    chat_history.append(ChatMessage(author="user", message=user_input))

    # Determine agent's response (either a preference question or a response from the API request)
    num_user_responses = sum(1 for msg in chat_history if msg.author == "user")
    agent_response_text = ""
    if num_user_responses < len(PREFERENCES_QUESTIONS):
        agent_response_text = PREFERENCES_QUESTIONS[num_user_responses]
    else:
        # Fetch the news
        search_response = exa.search_and_contents(user_input)

        user_preferences = {
            "tone_of_voice": chat_history[1].message,
            "response_format": chat_history[3].message,
            "language_preference": chat_history[5].message,
            "interaction_style": chat_history[7].message,
            "news_topics": chat_history[9].message,
        }
        # Summarize the news
        completion = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": NEWS_REQUEST_PROMPT.format(**user_preferences)},
                {"role": "user", "content": "\n\n".join([article.text for article in search_response.results])},
            ],
        )
        agent_response_text = completion.choices[0].message.content

    chat_history.append(ChatMessage(author="agent", message=agent_response_text))

    return chat_history
