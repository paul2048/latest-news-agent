from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import List, Literal
from fastapi.middleware.cors import CORSMiddleware
import os
import openai
from exa_py import Exa
from dotenv import load_dotenv
import json


class ChatMessage(BaseModel):
    author: Literal["user", "agent"]
    message: str


class UserInput(BaseModel):
    userInput: str = Field(..., min_length=1)


chat_history: List[ChatMessage] = []

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
exa = Exa(api_key=os.getenv("EXA_API_KEY"))


SYSTEM_PROMPT = """
You are a helpful assistant that provides news updates based on user preferences.
You need to collect the following user preferences by asking to provide their preferred:
    1. tone of voice (e.g., formal, casual, enthusiastic)
    2. response format (e.g., bullet points, paragraphs)
    3. language
    4. interaction style (e.g., concise, detailed)?
    5. news topics (e.g., politics, technology, sports)
once at a time (e.g. start with "What is your preferred tone of voice? (e.g., formal, casual, enthusiastic)")
    
Once all preferences are collected, the user can start asking specific news questions.
After each of these questions, execute the fetch_news function.
"""
MODEL = "gpt-4o-mini"
DEFAULT_MESSAGES = [
    {"role": "system", "content": SYSTEM_PROMPT},
]

def fetch_news(query: str):
    """
    Uses the Exa API to search for news and returns the results as a string.
    """
    print(f"--- Fetching news for query: {query} ---")
    try:
        search_response = exa.search_and_contents(query, text=True)
        results_str = ""
        for result in search_response.results:
            results_str += f"URL: {result.url}\nTitle: {result.title}\n\n{result.text}\n\n---\n\n"
        return results_str
    except Exception as e:
        print(f"Error fetching news: {e}")
        return f"An error occurred while fetching the news: {str(e)}"

tools = [
    {
        "type": "function",
        "function": {
            "name": "fetch_news",
            "description": "Fetches news articles based on a specific topic or query. Use this for any news-related request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The news topic to search for, e.g., 'latest AI developments' or 'US election updates'.",
                    },
                },
                "required": ["query"],
            },
        },
    }
]

# ### This is the actual function we defined earlier
available_functions = {
    "fetch_news": fetch_news,
}

messages = DEFAULT_MESSAGES.copy()
initial_completion = client.chat.completions.create(
    model=MODEL,
    messages=messages,
)
initial_response = initial_completion.choices[0].message
messages.append(initial_response)
chat_history.append(ChatMessage(author="agent", message=initial_response.content))


app = FastAPI()


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
    global chat_history, messages, completion
    messages = DEFAULT_MESSAGES
    completion = openai.chat.completions.create(
        model=MODEL,
        messages=messages,
    )
    chat_history.clear()
    chat_history.append(
        ChatMessage(author="agent", message=completion.choices[0].message.content)
    )
    return {"message": "Chat history cleared."}


@app.post("/chat", response_model=List[ChatMessage])
async def chat(request: UserInput):
    """Appends a user message and an agent response to the global history."""
    global chat_history, messages
    user_input = request.userInput
    messages.append({"role": "user", "content": user_input})
    chat_history.append(ChatMessage(author="user", message=user_input))

    completion = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )
    response_message = completion.choices[0].message

    # Check if the LLM wants to call a function
    if response_message.tool_calls:
        messages.append(response_message)

        # Execute the function(s)
        for tool_call in response_message.tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)

            function_response = function_to_call(
                query=function_args.get("query")
            )

            # Send the function's result back to the model
            messages.append(
                {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            )

        final_completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
        )
        agent_response_text = final_completion.choices[0].message.content
    else:
        agent_response_text = response_message.content

    messages.append({"role": "assistant", "content": agent_response_text})
    chat_history.append(ChatMessage(author="agent", message=agent_response_text))

    return chat_history
