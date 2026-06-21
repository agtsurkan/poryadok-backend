import { useCallback, useState } from "react";
import { getToken } from "./api";
import { StoreProvider } from "./store";
import { Login } from "./components/Login";
import { Sidebar } from "./components/Sidebar";
import { Home } from "./components/Home";

export default function App() {
  const [authed, setAuthed] = useState(() => !!getToken());
  const logout = useCallback(() => setAuthed(false), []);

  if (!authed) return <Login onDone={() => setAuthed(true)} />;

  return (
    <StoreProvider onAuthLost={logout}>
      <div className="app">
        <Sidebar onLogout={logout} />
        <Home />
      </div>
    </StoreProvider>
  );
}
