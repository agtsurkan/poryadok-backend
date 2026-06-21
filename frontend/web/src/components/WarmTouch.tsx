import type { Touch } from "../types";

const initials = (name: string) =>
  name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");

export function WarmTouch({ touches }: { touches: Touch[] }) {
  const touch = touches[0];
  return (
    <div className="card touch">
      <h2>Тёплое касание</h2>
      {!touch && <p className="muted">Со всеми на связи. Можно выдохнуть.</p>}
      {touch && (
        <>
          <div className="who">
            <div className="ava">{initials(touch.name)}</div>
            <div>
              <div className="name">{touch.name}</div>
              <div className="since">
                {touch.state === "cold" ? "Давно без связи" : "Понемногу остывает"}
                {touch.days_since != null ? ` · ${touch.days_since} дн.` : ""}
              </div>
            </div>
          </div>
          {touch.next && <div className="next">{touch.next}</div>}
          <button className="btn-ghost">Написать</button>
        </>
      )}
    </div>
  );
}
