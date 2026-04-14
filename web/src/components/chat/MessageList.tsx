import { ChatMessage } from "@/lib/api";
import { StreamingMessage } from "./StreamingMessage";

export function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="space-y-4">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
              msg.role === "user"
                ? "bg-blue-600 text-white"
                : "bg-white text-slate-800 border border-slate-200"
            }`}
          >
            {msg.streaming ? (
              <StreamingMessage content={msg.content} />
            ) : (
              <div className="whitespace-pre-wrap">{msg.content}</div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
