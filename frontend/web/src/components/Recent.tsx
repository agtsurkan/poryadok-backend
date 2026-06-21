import type { ActivityEvent } from "../types";

export function Recent({ events }: { events: ActivityEvent[] }) {
  return (
    <div className="card">
      <h2>Недавнее</h2>
      {events.length === 0 && <p className="muted">Пока тихо.</p>}
      <div className="recent">
        {events.slice(0, 6).map((e) => (
          <div className="item" key={e.id}>
            <span className="when">{e.when}</span>
            <span className="what">{e.text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
