import type { Task } from "../types";

export function Focus({ task, onDone, onSkip }: { task: Task; onDone: (id: string) => void; onSkip: () => void }) {
  return (
    <div className="card focus">
      <span className="label">Сегодня в фокусе</span>
      <div className="task">{task.text}</div>
      <div className="row">
        <button className="btn-primary" onClick={() => onDone(task.id)}>
          Сделано
        </button>
        <button className="btn-ghost" onClick={onSkip}>
          Не сейчас
        </button>
      </div>
    </div>
  );
}

export function AllDone() {
  return (
    <div className="card alldone">
      <div className="enso" />
      <h2>Все дела в порядке.</h2>
      <p>Ты молодец — можно отдыхать.</p>
    </div>
  );
}
