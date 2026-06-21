import { useState } from "react";
import { apiBase, login, setSession } from "../api";

export function Login({ onDone }: { onDone: () => void }) {
  const [email, setEmail] = useState("demo@poryadok.app");
  const [password, setPassword] = useState("");
  const [base, setBase] = useState(apiBase());
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    setBusy(true);
    try {
      const token = await login(email.trim(), password, base);
      setSession(base, token);
      onDone();
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Сервер недоступен");
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login" onSubmit={submit}>
        <h1>Порядок</h1>
        <p className="sub">Войдите, чтобы продолжить</p>

        <label>Email</label>
        <input type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />

        <label>Пароль</label>
        <input
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />

        <button className="btn-primary" type="submit" disabled={busy}>
          {busy ? "Вход…" : "Войти"}
        </button>
        <div className="err">{err}</div>

        <details>
          <summary>Сервер</summary>
          <label>Адрес API</label>
          <input type="text" value={base} onChange={(e) => setBase(e.target.value)} />
        </details>
      </form>
    </div>
  );
}
