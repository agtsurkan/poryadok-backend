import { clearToken } from "../api";

// «Главная» is live; deeper sections are stubs (extensible next).
const PRIMARY: [string, string, string][] = [
  ["home", "Главная", "◎"],
  ["inbox", "Мысли", "✶"],
  ["tasks", "Задачи", "✓"],
  ["plan", "Планирование", "▦"],
];
const DEEP: [string, string, string][] = [
  ["projects", "Проекты", "◆"],
  ["clients", "Клиенты", "♥"],
  ["map", "Карта связей", "⌥"],
];

export function Sidebar({ onLogout }: { onLogout: () => void }) {
  return (
    <aside className="aside">
      <div className="brand">
        <div className="logo">◎</div>
        <div>
          <div className="name">Порядок</div>
          <div className="sub">в порядке</div>
        </div>
      </div>

      <nav className="nav">
        {PRIMARY.map(([id, label, ico]) => (
          <button key={id} className={id === "home" ? "active" : ""} disabled={id !== "home"}>
            <span className="ico">{ico}</span>
            {label}
          </button>
        ))}
        <div className="group-label">Глубже</div>
        {DEEP.map(([id, label, ico]) => (
          <button key={id} disabled>
            <span className="ico">{ico}</span>
            {label}
          </button>
        ))}
      </nav>

      <div className="foot">
        <button
          className="linkbtn"
          onClick={() => {
            clearToken();
            onLogout();
          }}
        >
          Выйти
        </button>
      </div>
    </aside>
  );
}
