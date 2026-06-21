// Wire shapes (subset) — mirror the backend bundle (brief §3).
export type EntityLink = { type: string; id: string } | null;

export interface Task {
  id: string;
  text: string;
  tag: "project" | "client" | "mail" | "note";
  effort: 1 | 2 | 3;
  today: boolean;
  done: boolean;
  due?: string | null;
  link?: EntityLink;
}

export interface Thought {
  id: string;
  text: string;
  when?: string;
  kind?: "note" | "idea";
  link?: EntityLink;
}

export interface ActivityEvent {
  id: string;
  kind: "done" | "note" | "add" | "client" | "move" | string;
  text: string;
  when: string;
}

export interface QuickLink {
  id: string;
  type: string;
  label: string;
}

// GET/PUT /state — frontend keys (drop-in contract). Extra keys preserved.
export interface Bundle {
  ver?: number;
  tasks?: Task[];
  inbox?: Thought[]; // мысли
  events?: ActivityEvent[]; // лог активности
  quickLinks?: QuickLink[];
  [key: string]: unknown;
}

// GET /suggestions/touches
export interface Touch {
  id: string;
  name: string;
  state: "cold" | "warm" | "active";
  last_touch_at: string | null;
  days_since: number | null;
  next: string;
  suggestion: string;
  note: string;
}

export type Energy = "low" | "mid" | "high";
