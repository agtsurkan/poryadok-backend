import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import * as api from "./api";
import type { Bundle, Task, Thought, Touch } from "./types";

interface Store {
  bundle: Bundle;
  touches: Touch[];
  loading: boolean;
  error: string | null;
  saveError: boolean;
  tasks: Task[];
  inbox: Thought[];
  toggleTask: (id: string) => void;
  addTask: (text: string) => void;
  addThought: (text: string) => void;
  removeThought: (id: string) => void;
  promoteThought: (id: string) => void;
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
  const [saveError, setSaveError] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const retry = useRef<number | undefined>(undefined);
  const pending = useRef<Bundle | null>(null);

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

  // Push the latest pending bundle to the server. On failure, keep it pending,
  // raise a calm flag, and retry — so a dropped request never silently strands
  // the optimistic UI ahead of the server.
  function flush() {
    const next = pending.current;
    if (!next) return;
    api
      .putState(next)
      .then(() => {
        pending.current = null;
        setSaveError(false);
      })
      .catch((e) => {
        if (e instanceof Error && e.message === "Сессия истекла") return onAuthLost();
        setSaveError(true);
        window.clearTimeout(retry.current);
        retry.current = window.setTimeout(flush, 3000);
      });
  }

  // Optimistic local update + debounced save of the whole bundle (backend
  // merges by presence, so sending the full bundle is safe).
  function save(next: Bundle) {
    setBundle(next);
    pending.current = next;
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(flush, 600);
  }

  const tasks = (bundle.tasks ?? []) as Task[];
  const inbox = (bundle.inbox ?? []) as Thought[];

  const store: Store = {
    bundle,
    touches,
    loading,
    error,
    saveError,
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
    removeThought: (id) => save({ ...bundle, inbox: inbox.filter((t) => t.id !== id) }),
    promoteThought: (id) => {
      const thought = inbox.find((t) => t.id === id);
      if (!thought) return;
      const tag: Task["tag"] =
        thought.link?.type === "project" ? "project" : thought.link?.type === "client" ? "client" : "note";
      const task: Task = {
        id: rid("t"),
        text: thought.text,
        tag,
        effort: 2,
        today: true,
        done: false,
        link: thought.link ?? null,
      };
      save({ ...bundle, tasks: [task, ...tasks], inbox: inbox.filter((t) => t.id !== id) });
    },
  };

  return <StoreCtx.Provider value={store}>{children}</StoreCtx.Provider>;
}
