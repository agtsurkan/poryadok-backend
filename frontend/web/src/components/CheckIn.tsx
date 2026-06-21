import { useState } from "react";
import type { Energy } from "../types";

const ENERGY: [Energy, string, string][] = [
  ["low", "Тихо", "мягкий старт"],
  ["mid", "Ровно", "как обычно"],
  ["high", "На подъёме", "есть силы"],
];
const TIMES = [15, 30, 60];

export function CheckIn({ onStart }: { onStart: (energy: Energy, minutes: number) => void }) {
  const [energy, setEnergy] = useState<Energy | null>(null);
  const [minutes, setMinutes] = useState<number | null>(null);

  return (
    <div className="card checkin">
      <h2>Навести порядок</h2>

      <p className="q">Сколько сейчас энергии?</p>
      <div className="chips">
        {ENERGY.map(([key, label, hint]) => (
          <button key={key} className={`chip ${energy === key ? "on" : ""}`} onClick={() => setEnergy(key)}>
            {label}
            <small>{hint}</small>
          </button>
        ))}
      </div>

      <p className="q">Сколько есть времени?</p>
      <div className="chips">
        {TIMES.map((m) => (
          <button key={m} className={`chip ${minutes === m ? "on" : ""}`} onClick={() => setMinutes(m)}>
            {m} мин
          </button>
        ))}
      </div>

      <button
        className="btn-primary"
        disabled={!energy || !minutes}
        onClick={() => energy && minutes && onStart(energy, minutes)}
      >
        Навести
      </button>
    </div>
  );
}
