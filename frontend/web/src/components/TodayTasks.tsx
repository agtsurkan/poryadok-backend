import type { Task } from "../types";

const TAG_VAR: Record<string, string> = {
  project: "var(--tag-p)",
  client: "var(--tag-c)",
  mail: "var(--tag-m)",
  note: "var(--tag-n)",
};

function Row({ task, onToggle }: { task: Task; onToggle: (id: string) => void }) {
  return (
    <div className={`task-row ${task.done ? "is-done" : ""}`}>
      <button
        className={`check ${task.done ? "done" : ""}`}
        aria-label={task.done ? "Вернуть" : "Сделано"}
        onClick={() => onToggle(task.id)}
      >
        {task.done ? "✓" : ""}
      </button>
      <span className="dot" style={{ background: TAG_VAR[task.tag] ?? "var(--tag-n)" }} />
      <span className="t">{task.text}</span>
    </div>
  );
}

export function TodayTasks({ tasks, onToggle }: { tasks: Task[]; onToggle: (id: string) => void }) {
  const today = tasks.filter((t) => t.today);
  const open = today.filter((t) => !t.done);
  const done = today.filter((t) => t.done);

  return (
    <div className="card">
      <h2>Сегодня</h2>
      {open.length === 0 && done.length === 0 && <p className="muted">На сегодня дел нет. Тихо.</p>}
      <div className="tasks">
        {open.map((t) => (
          <Row key={t.id} task={t} onToggle={onToggle} />
        ))}
      </div>
      {done.length > 0 && (
        <>
          <div className="section-label">Сделано сегодня</div>
          <div className="tasks">
            {done.map((t) => (
              <Row key={t.id} task={t} onToggle={onToggle} />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
