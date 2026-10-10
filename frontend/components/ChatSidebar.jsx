"use client";

export default function ChatSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
  username,
  onLogout,
  open,
  onClose,
}) {
  return (
    <>
      <div
        className={`side-backdrop ${open ? "show" : ""}`}
        onClick={onClose}
        aria-hidden
      />
      <aside className={`chat-sidebar ${open ? "open" : ""}`}>
        <div className="side-head">
          <span className="brand">
            <span className="brand-mark" aria-hidden />
            Simple&nbsp;RAG
          </span>
          <button type="button" className="btn-new" onClick={onNew}>
            + New chat
          </button>
        </div>

        <div className="side-list">
          {conversations.length === 0 && (
            <p className="side-empty">No conversations yet.</p>
          )}
          {conversations.map((c) => (
            <div
              key={c.id}
              className={`side-item ${c.id === activeId ? "active" : ""}`}
            >
              <button
                type="button"
                className="side-title"
                onClick={() => onSelect(c.id)}
                title={c.title}
              >
                {c.title}
              </button>
              <button
                type="button"
                className="side-del"
                title="Delete conversation"
                onClick={() => onDelete(c.id)}
              >
                &#10005;
              </button>
            </div>
          ))}
        </div>

        <div className="side-foot">
          <span className="nav-user">{username}</span>
          <button type="button" className="btn-small" onClick={onLogout}>
            Logout
          </button>
        </div>
      </aside>
    </>
  );
}
