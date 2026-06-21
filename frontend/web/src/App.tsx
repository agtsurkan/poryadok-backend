import { useCallback, useState } from "react";
import { getToken } from "./api";
import { StoreProvider, useStore } from "./store";
import { Login } from "./components/Login";
import { Sidebar, type View } from "./components/Sidebar";
import { Home } from "./components/Home";
import { Inbox } from "./components/Inbox";

// Quiet signal that an autosave didn't land (it keeps retrying in the store).
function SaveToast() {
  const { saveError } = useStore();
  if (!saveError) return null;
  return <div className="save-toast">Не удалось сохранить — повторяю…</div>;
}

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());
  const [view, setView] = useState<View>("home");
  const logout = useCallback(() => setAuthed(false), []);

  if (!authed) return <Login onDone={() => setAuthed(true)} />;

  return (
    <StoreProvider onAuthLost={logout}>
      <div className="app">
        <Sidebar current={view} onNavigate={setView} onLogout={logout} />
        {view === "inbox" ? <Inbox /> : <Home />}
      </div>
      <SaveToast />
    </StoreProvider>
  );
}
