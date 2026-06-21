import { clearToken } from "../api";

export type View = "home" | "inbox";

// Live sections are enabled; deeper ones are stubs (extensible next).
const ENABLED = new Set<string>(["home", "inbox"]);
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

export function Sidebar({
  current,
  onNavigate,
  onLogout,
}: {
  current: View;
  onNavigate: (view: View) => void;
  onLogout: () => void;
}) {
  const item = ([id, label, ico]: [string, string, string]) => {
    const enabled = ENABLED.has(id);
    return (
      <button
        key={id}
        className={current === id ? "active" : ""}
        disabled={!enabled}
        onClick={enabled ? () => onNavigate(id as View) : undefined}
      >
        <span className="ico">{ico}</span>
        {label}
      </button>
    );
  };

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
        {PRIMARY.map(item)}
        <div className="group-label">Глубже</div>
        {DEEP.map(item)}
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
