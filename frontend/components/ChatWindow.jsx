"use client";

import { useEffect, useRef, useState } from "react";
import MessageBubble from "./MessageBubble";

const SUGGESTIONS = [
  "What is the name of the applicant?",
  "What is the date of birth?",
  "Summarize the educational details.",
];

export default function ChatWindow({ messages, busy, onSend }) {
  const [q, setQ] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  const submit = (e) => {
    e.preventDefault();
    if (!q.trim() || busy) return;
    onSend(q);
    setQ("");
  };

  return (
    <>
      <div className="chat-messages">
        {messages.length === 0 && !busy ? (
          <div className="empty-state">
            <div className="empty-mark" aria-hidden>
              &#10022;
            </div>
            <h2>Ask anything about your PDFs</h2>
            <p>Pick a suggestion or type your own question below.</p>
            <div className="sugg-row">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  className="sugg-chip"
                  onClick={() => onSend(s)}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m, i) => <MessageBubble key={i} {...m} />)
        )}
        {busy && (
          <div className="msg-row bot">
            <div className="avatar" aria-hidden>
              &#10022;
            </div>
            <div className="bubble typing" aria-label="Thinking">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="composer">
        <form onSubmit={submit}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Ask about your PDF..."
            disabled={busy}
          />
          <button type="submit" disabled={busy || !q.trim()} aria-label="Send">
            &#10148;
          </button>
        </form>
      </div>
    </>
  );
}
