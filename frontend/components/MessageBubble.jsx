"use client";

export default function MessageBubble({ role, text }) {
  return (
    <div style={{ textAlign: role === "user" ? "right" : "left", margin: "8px 0" }}>
      <b>{role}:</b> {text}
    </div>
  );
}
