"use server";

export interface ChatMessage {
  author: 'user' | 'agent';
  message: string;
}

export async function sendUserInput(userInput: string): Promise<ChatMessage[]> {
  try {
    const response = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ userInput }),
    });

    if (!response.ok) {
      throw new Error("Server returned an error.");
    }

    return await response.json();
  } catch (error) {
    console.error("Action error:", error);
    throw new Error("Failed to send message. Please try again.");
  }
}