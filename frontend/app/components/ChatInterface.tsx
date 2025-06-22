"use client";

import { useState, useEffect, useRef, useTransition } from "react";
import { sendUserInput } from "../actions/chat";
import type { ChatMessage } from "../actions/chat";
import ChatForm from "./ChatForm";

export default function ChatInterface() {
  const listEndRef = useRef<HTMLDivElement>(null);
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    async function getInitialHistory() {
      try {
        const response = await fetch("http://localhost:8000/chat/history");
        const initialHistory = await response.json();
        setHistory(initialHistory);
        console.log("Initial history fetched:", initialHistory);
      } catch {
        setError("Failed to connect to the chat server.");
      }
    }
    getInitialHistory();
  }, []);

  const handleFormSubmit = async (formData: FormData) => {
    const userInput = formData.get("userInput") as string;
    setError(null);

    startTransition(async () => {
      try {
        const newHistory = await sendUserInput(userInput);
        setHistory(newHistory);
      } catch (e) {
        setError((e as Error).message);
      }
    });
  };

  // Scroll to bottom when the history changes
  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  return (
    <main className="flex flex-col h-screen">
      <div className="flex-none h-24 flex items-center justify-center">
        <h1 className="text-4xl font-bold">Latest News Agent</h1>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <ul className="text-lg space-y-4">
          {history.length === 0 && !error && <li className="text-center text-gray-400">Loading...</li>}
          {history.map((item, index) => (
            <li
              key={index}
              className={`p-4 rounded-lg max-w-xl ${
                item.author === 'user' ? 'bg-blue-900/50 ml-auto' : 'bg-gray-800 mr-auto'
              }`}
            >
              {item.message}
            </li>
          ))}
          {error && <li className="text-red-500 text-center">{error}</li>}
          <div ref={listEndRef} />
        </ul>
      </div>
      <div className="flex bg-gray-800 flex-none justify-center items-center">
        <ChatForm action={handleFormSubmit} isPending={isPending} />

        <button
          type="button"
          className="flex-none ml-2 bg-red-400 hover:bg-red-700 text-black font-bold py-2 px-4 rounded m-2"
          onClick={() => {
            fetch("http://localhost:8000/chat/clear", { method: "POST" })
              .then((response) => response.json())
              .then(() => {
                setHistory([
                  {
                    author: "agent", 
                    message: "First, what's your preferred tone of voice (e.g., formal, casual, enthusiastic)?"
                  }
                ]);
              })
              .catch((error) => console.error("Error clearing chat history:", error));
          }}>
            Clear history
          </button>
      </div>
    </main>
  );
}