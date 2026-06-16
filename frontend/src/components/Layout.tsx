import { Link, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Project Chronicler</p>
          <h1>RolePBP</h1>
        </div>
        <nav>
          <Link to="/">Inicio</Link>
          <Link to="/chat">Chat</Link>
          <Link to="/master">Panel Máster</Link>
        </nav>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  );
}
