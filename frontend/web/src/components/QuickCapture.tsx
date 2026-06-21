import { useState } from "react";

export function QuickCapture({
  onAddTask,
  onAddThought,
}: {
  onAddTask: (text: string) => void;
  onAddThought: (text: string) => void;
}) {
  const [text, setText] = useState("");
  const [dest, setDest] = useState<"task" | "thought">("task");

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const value = text.trim();
    if (!value) return;
    if (dest === "task") onAddTask(value);
    else onAddThought(value);
    setText("");
  }

  return (
    <div className="card capture">
      <h2>Что добавить</h2>
      <div className="seg">
        <button className={dest === "task" ? "on" : ""} onClick={() => setDest("task")}>
          В задачи
        </button>
        <button className={dest === "thought" ? "on" : ""} onClick={() => setDest("thought")}>
          В Мысли
        </button>
      </div>
      <form className="field" onSubmit={submit}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={dest === "task" ? "Новая задача…" : "Мысль, без спешки…"}
        />
        <button className="btn-primary" type="submit">
          +
        </button>
      </form>
    </div>
  );
}
