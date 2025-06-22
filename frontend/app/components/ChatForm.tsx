"use client";

import { useRef } from "react";

interface ChatFormProps {
  action: (formData: FormData) => void;
  isPending: boolean;
}

export default function ChatForm({ action, isPending }: ChatFormProps) {
  const formRef = useRef<HTMLFormElement>(null);

  return (
    <form
      ref={formRef}
      action={(formData) => {
        action(formData);
        formRef.current?.reset();
      }}
      className="p-4 flex items-center"
    >
      <input
        type="text"
        name="userInput"
        required
        className="flex-1 p-2 rounded-l bg-gray-700 text-white border border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
        placeholder="Type your response..."
        disabled={isPending}
      />
      <button
        type="submit"
        disabled={isPending}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-r disabled:bg-gray-500"
      >
        {isPending ? "Sending..." : "Send"}
      </button>
    </form>
  );
}