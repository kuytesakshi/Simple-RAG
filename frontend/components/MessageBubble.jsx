"use client";

export default function MessageBubble({ role, text, sources }) {
  const isUser = role === "user";
  return (
    <div className={`msg-row ${isUser ? "user" : "bot"}`}>
      <div className="avatar" aria-hidden>
        {isUser ? "You" : "\u2726"}
      </div>
      <div className="bubble">
        <p>{text}</p>
        {!isUser && sources?.length > 0 && (
          <div className="src-chips">
            {sources.map((s) => (
              <span key={s} className="chip" title={s}>
                {s}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
