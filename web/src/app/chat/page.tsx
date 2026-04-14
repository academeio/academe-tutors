"use client";

/**
 * Chat page — the main tutor interface.
 * Launched via LTI with session_id and token in query params.
 *
 * TODO:
 * - Parse session_id from URL search params
 * - Establish WebSocket connection to backend
 * - Render chat UI with message history
 * - Stream tutor responses in real-time
 * - Display RAG citations inline
 * - Show competency alignment badges
 */
export default function ChatPage() {
  return (
    <main className="flex h-screen flex-col">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-slate-800">Academe Tutor</h1>
            <p className="text-sm text-slate-500">Course: Loading...</p>
          </div>
          <div className="text-sm text-slate-400">Session placeholder</div>
        </div>
      </header>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-3xl">
          <div className="rounded-lg bg-blue-50 p-4 text-blue-800">
            Chat interface not yet implemented. Connect via LTI launch.
          </div>
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-slate-200 bg-white p-4">
        <div className="mx-auto flex max-w-3xl gap-3">
          <input
            type="text"
            placeholder="Ask your tutor a question..."
            className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm focus:border-blue-500 focus:outline-none"
            disabled
          />
          <button
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white opacity-50"
            disabled
          >
            Send
          </button>
        </div>
      </div>
    </main>
  );
}
