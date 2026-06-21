import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import * as api from "./api";
import type { Bundle, Task, Thought, Touch } from "./types";

interface Store {
  bundle: Bundle;
  touches: Touch[];
  loading: boolean;
  error: string | null;
  tasks: Task[];
  inbox: Thought[];
  toggleTask: (id: string) => void;
  addTask: (text: string) => void;
  addThought: (text: string) => void;
}

const StoreCtx = createContext<Store | null>(null);

export function useStore(): Store {
  const ctx = useContext(StoreCtx);
  if (!ctx) throw new Error("useStore must be used within StoreProvider");
  return ctx;
}

const rid = (p: string) => p + Math.random().toString(36).slice(2, 10);

export function StoreProvider({ children, onAuthLost }: { children: ReactNode; onAuthLost: () => void }) {
  const [bundle, setBundle] = useState<Bundle>({});
  const [touches, setTouches] = useState<Touch[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const b = await api.getState();
        if (alive) setBundle(b);
        try {
          const t = await api.getTouches();
          if (alive) setTouches(t);
        } catch {
          /* proactivity optional */
        }
      } catch (e) {
        if (e instanceof Error && e.message === "Сессия истекла") return onAuthLost();
        if (alive) setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [onAuthLost]);

  // Optimistic local update + debounced save of the whole bundle (backend
  // merges by presence, so sending the full bundle is safe).
  function save(next: Bundle) {
    setBundle(next);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => {
      api.putState(next).catch((e) => {
        if (e instanceof Error && e.message === "Сессия истекла") onAuthLost();
      });
    }, 600);
  }

  const tasks = (bundle.tasks ?? []) as Task[];
  const inbox = (bundle.inbox ?? []) as Thought[];

  const store: Store = {
    bundle,
    touches,
    loading,
    error,
    tasks,
    inbox,
    toggleTask: (id) =>
      save({ ...bundle, tasks: tasks.map((t) => (t.id === id ? { ...t, done: !t.done } : t)) }),
    addTask: (text) =>
      save({
        ...bundle,
        tasks: [{ id: rid("t"), text, tag: "note", effort: 2, today: true, done: false, link: null }, ...tasks],
      }),
    addThought: (text) =>
      save({ ...bundle, inbox: [{ id: rid("i"), text, when: "сейчас", kind: "note", link: null }, ...inbox] }),
  };

  return <StoreCtx.Provider value={store}>{children}</StoreCtx.Provider>;
}
