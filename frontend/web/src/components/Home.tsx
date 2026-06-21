import { useState } from "react";
import { useStore } from "../store";
import type { ActivityEvent, Energy } from "../types";
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
  const [skip, setSkip] = useState(0);

  if (loading) return <main className="main"><div className="center-note">Загружаю…</div></main>;
  if (error) return <main className="main"><div className="center-note">Не вышло загрузить: {error}</div></main>;

  // Pick one task under the chosen energy (low→light, high→demanding).
  const open = tasks.filter((t) => t.today && !t.done);
  const target = energy === "low" ? 1 : energy === "high" ? 3 : 2;
  const ranked = [...open].sort((a, b) => Math.abs((a.effort ?? 2) - target) - Math.abs((b.effort ?? 2) - target));
  const focusTask = ranked.length ? ranked[skip % ranked.length] : null;
  const events = (bundle.events as ActivityEvent[] | undefined) ?? [];

  const hero = !started ? (
    <CheckIn
      onStart={(e) => {
        setEnergy(e);
        setSkip(0);
        setStarted(true);
      }}
    />
  ) : focusTask ? (
    <Focus task={focusTask} onDone={(id) => { toggleTask(id); setSkip(0); }} onSkip={() => setSkip((s) => s + 1)} />
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
