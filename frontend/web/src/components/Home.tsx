import { useState } from "react";
import { useStore } from "../store";
import type { ActivityEvent, Energy, Task } from "../types";
import { CheckIn } from "./CheckIn";
import { Focus, AllDone } from "./Focus";
import { TodayTasks } from "./TodayTasks";
import { QuickCapture } from "./QuickCapture";
import { WarmTouch } from "./WarmTouch";
import { Recent } from "./Recent";

const todayLabel = () =>
  new Date().toLocaleDateString("ru-RU", { weekday: "long", day: "numeric", month: "long" });

export function Home() {
  const { loading, error, tasks, touches, bundle, toggleTask, addTask, addThought } = useStore();
  const [started, setStarted] = useState(false);
  const [energy, setEnergy] = useState<Energy>("mid");
  const [minutes, setMinutes] = useState(30);
  const [focusId, setFocusId] = useState<string | null>(null);

  if (loading) return <main className="main"><div className="center-note">Загружаю…</div></main>;
  if (error) return <main className="main"><div className="center-note">Не вышло загрузить: {error}</div></main>;

  // Pick one task under the check-in: tasks over the time budget sink, then
  // rank by closeness to the chosen energy (low→light, high→demanding).
  const open = tasks.filter((t) => t.today && !t.done);
  const maxEffort = minutes <= 15 ? 1 : minutes <= 30 ? 2 : 3;
  const target = energy === "low" ? 1 : energy === "high" ? 3 : 2;
  const score = (t: Task) => {
    const e = t.effort ?? 2;
    return (e > maxEffort ? 10 : 0) + Math.abs(e - target);
  };
  const ranked = [...open].sort((a, b) => score(a) - score(b));
  // Hold focus on a task by id, so completing something in the list below
  // doesn't make the focus card jump to a different task.
  const focusTask = open.find((t) => t.id === focusId) ?? ranked[0] ?? null;
  const events = (bundle.events as ActivityEvent[] | undefined) ?? [];

  const skipFocus = () => {
    if (ranked.length <= 1) return;
    const idx = ranked.findIndex((t) => t.id === focusTask?.id);
    setFocusId(ranked[(idx + 1) % ranked.length].id);
  };

  const hero = !started ? (
    <CheckIn
      onStart={(e, m) => {
        setEnergy(e);
        setMinutes(m);
        setFocusId(null);
        setStarted(true);
      }}
    />
  ) : focusTask ? (
    <Focus
      task={focusTask}
      onDone={(id) => {
        toggleTask(id);
        setFocusId(null);
      }}
      onSkip={ranked.length > 1 ? skipFocus : undefined}
    />
  ) : (
    <AllDone />
  );

  return (
    <main className="main">
      <header className="head">
        <h1>Главная</h1>
        <span className="date">{todayLabel()}</span>
      </header>
      <div className="grid two">
        <div className="col">
          {hero}
          <TodayTasks tasks={tasks} onToggle={toggleTask} />
          <Recent events={events} />
        </div>
        <div className="col">
          <QuickCapture onAddTask={addTask} onAddThought={addThought} />
          <WarmTouch touches={touches} />
        </div>
      </div>
    </main>
  );
}
