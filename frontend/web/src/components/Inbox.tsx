import { useState } from "react";
import { useStore } from "../store";
import type { Thought } from "../types";

const KIND_ICON: Record<string, string> = { note: "✶", idea: "✦" };
const LINK_LABEL: Record<string, string> = { project: "Проект", client: "Клиент" };

function Item({
  t,
  onPromote,
  onRemove,
}: {
  t: Thought;
  onPromote: (id: string) => void;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="thought">
      <span className="kind">{KIND_ICON[t.kind ?? "note"] ?? "✶"}</span>
      <div className="body">
        <div className="t">{t.text}</div>
        <div className="meta">
          {t.when && <span>{t.when}</span>}
          {t.link && <span className="link-chip">{LINK_LABEL[t.link.type] ?? t.link.type}</span>}
        </div>
      </div>
      <div className="acts">
        <button className="btn-ghost sm" onClick={() => onPromote(t.id)}>
          В задачи
        </button>
        <button className="iconbtn" aria-label="Убрать" title="Убрать" onClick={() => onRemove(t.id)}>
          ✕
        </button>
      </div>
    </div>
  );
}

export function Inbox() {
  const { loading, error, inbox, addThought, removeThought, promoteThought } = useStore();
  const [text, setText] = useState("");

  if (loading) return <main className="main"><div className="center-note">Загружаю…</div></main>;
  if (error) return <main className="main"><div className="center-note">Не вышло загрузить: {error}</div></main>;

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    addThought(value);
    setText("");
  }

  return (
    <main className="main">
      <header className="head">
        <h1>Мысли</h1>
        <span className="date">{inbox.length} в инбоксе</span>
      </header>
      <div className="grid">
        <div className="col">
          <div className="card capture">
            <form className="field" onSubmit={submit}>
              <input
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="Записать мысль, без спешки…"
              />
              <button className="btn-primary" type="submit">
                +
              </button>
            </form>
          </div>

          <div className="card">
            <h2>Инбокс</h2>
            {inbox.length === 0 && <p className="muted">Пусто. Голова чистая.</p>}
            <div className="thoughts">
              {inbox.map((t) => (
                <Item key={t.id} t={t} onPromote={promoteThought} onRemove={removeThought} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
