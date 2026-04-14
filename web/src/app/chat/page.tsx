"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useMemo, useEffect, useRef } from "react";
import { useChat } from "@/hooks/useChat";
import { MessageList } from "@/components/chat/MessageList";
import { ChatInput } from "@/components/chat/ChatInput";

function ChatContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sessionId = useMemo(() => {
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      return payload.session_id;
    } catch {
      return null;
    }
  }, [token]);

  const { messages, streaming, connected, sendMessage } = useChat(sessionId, token);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (!token) {
    return (
      <main className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-800">Academe Tutor</h1>
          <p className="mt-2 text-slate-500">Please launch from Canvas LMS.</p>
        </div>
      </main>
    );
  }

  return (
    <main className="flex h-screen flex-col">
      <header className="border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-slate-800">Academe Tutor</h1>
          <span className={`text-xs ${connected ? "text-green-600" : "text-red-500"}`}>
            {connected ? "Connected" : "Disconnected"}
          </span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl">
          {messages.length === 0 && (
            <div className="text-center text-slate-400 mt-20">
              <p className="text-lg">Welcome to Academe Tutor</p>
              <p className="text-sm mt-1">Ask me anything about your course materials.</p>
            </div>
          )}
          <MessageList messages={messages} />
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white p-4">
        <div className="mx-auto max-w-3xl">
          <ChatInput onSend={sendMessage} disabled={!connected || streaming} />
        </div>
      </div>
    </main>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center">Loading...</div>}>
      <ChatContent />
    </Suspense>
  );
}
