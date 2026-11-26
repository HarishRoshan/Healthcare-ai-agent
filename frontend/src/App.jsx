
import { useEffect, useState } from "react";

const API_URL = import.meta.env.VITE_API_URL ??
  (import.meta.env.DEV ? "http://localhost:8001" : "");
function App() {
  // Session authentication: the server owns the session cookie.
  const [authStatus, setAuthStatus] = useState("checking");
  const [username, setUsername] = useState("aura_demo");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  useEffect(() => {
    let active = true;
    async function checkSession() {
      try {
        const response = await fetch(`${API_URL}/auth/me`, {
          credentials: "include",
        });
        if (active) setAuthStatus(response.ok ? "authenticated" : "guest");
      } catch {
        if (active) {
          setAuthError("Cannot reach the authentication server. Check FastAPI.");
          setAuthStatus("guest");
        }
      }
    }
    checkSession();
    return () => { active = false; };
  }, []);

  async function handleLogin(event) {
    event.preventDefault();
    setAuthBusy(true);
    setAuthError("");
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!response.ok) {
        setAuthError(response.status === 401
          ? "Incorrect username or password."
          : `Login failed (HTTP ${response.status}). Check the backend login route.`);
        return;
      }
      const verify = await fetch(`${API_URL}/auth/me`, {
        credentials: "include",
      });
      if (!verify.ok) {
        setAuthError("Login responded successfully, but the session cookie was not accepted. Check FastAPI CORS and cookie settings.");
        return;
      }
      setPassword("");
      setAuthStatus("authenticated");
    } catch {
      setAuthError("Cannot connect to FastAPI at http://127.0.0.1:8001.");
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleLogout() {
    setAuthBusy(true);
    setAuthError("");
    try {
      const response = await fetch(`${API_URL}/auth/logout`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        setAuthError(`Logout failed (HTTP ${response.status}).`);
        return;
      }
      setPatients([]);
      setMessages([{ role: "assistant", text: "Hello! I'm AURA AI. How can I help you with fictional patient records today?" }]);
      setAuthStatus("guest");
    } catch {
      setAuthError("Could not contact FastAPI to log out.");
    } finally {
      setAuthBusy(false);
    }
  }

  // AI chat state
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Hello! I'm AURA AI. How can I help you with fictional patient records today?",
    },
  ]);

  // Patient dashboard state
  const [patients, setPatients] = useState([]);
  const [patientsLoading, setPatientsLoading] = useState(true);
  const [patientsError, setPatientsError] = useState("");

  // Fetch patient records from FastAPI
  async function loadPatients() {
    try {
      setPatientsLoading(true);
      setPatientsError("");

      const response = await fetch(`${API_URL}/patients`, { credentials: "include" });

      // NEW: Handle authentication errors
      if (response.status === 401) {
        setAuthStatus("guest");
        throw new Error("AUTH_REQUIRED");
      }

      if (!response.ok) {
        throw new Error(
          `Patient API returned status ${response.status}`
        );
      }

      const data = await response.json();

      if (!Array.isArray(data.patients)) {
        throw new Error("Invalid patient data received");
      }

      setPatients(data.patients);
    } catch (error) {
      console.error("Patient loading error:", error);

      // NEW: Show a specific authentication message
      setPatientsError(
        error.message === "AUTH_REQUIRED"
          ? "Access denied. Please sign in to view patient records."
          : "Unable to load patient records. Check FastAPI."
      );
    } finally {
      setPatientsLoading(false);
    }
  }

  // Load patients when the dashboard opens
  useEffect(() => {
    if (authStatus === "authenticated") loadPatients();
  }, [authStatus]);

  // Send a question to the AI agent
  async function handleSubmit(event) {
    event.preventDefault();

    const userQuestion = question.trim();

    if (!userQuestion || isLoading) return;

    setQuestion("");
    setIsLoading(true);

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        text: userQuestion,
      },
    ]);

    try {
      const response = await fetch(
        `${API_URL}/agent/ask`,
        {
          method: "POST",
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: userQuestion,
          }),
        }
      );

      // NEW: Handle authentication errors
      if (response.status === 401) {
        setAuthStatus("guest");
        throw new Error("AUTH_REQUIRED");
      }

      if (!response.ok) {
        throw new Error(
          `AI API returned status ${response.status}`
        );
      }

      const data = await response.json();

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text: data.answer,
        },
      ]);
    } catch (error) {
      console.error("AURA AI request failed:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          text:
            error.message === "AUTH_REQUIRED"
              ? "Access denied. Authentication is required to use AURA AI."
              : "Sorry, I couldn't get a response from the AI service. Please check your FastAPI server and try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  // Calculate total appointments
  const totalAppointments = patients.reduce(
    (total, patient) => total + patient.appointments,
    0
  );

  if (authStatus === "checking") {
    return <div className="flex min-h-screen items-center justify-center bg-[#060d1b] text-cyan-300">Checking AURA AI session...</div>;
  }

  if (authStatus === "guest") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#060d1b] px-4 text-slate-100">
        <form onSubmit={handleLogin} className="w-full max-w-md rounded-2xl border border-cyan-900/50 bg-[#101e33] p-8 shadow-2xl">
          <p className="mb-3 text-sm tracking-[0.25em] text-cyan-400">✦ AURA HEALTH</p>
          <h1 className="mb-2 text-3xl font-bold">Sign in to AURA AI</h1>
          <p className="mb-8 text-sm text-slate-400">Educational demo · Fictional patient data only</p>
          <label htmlFor="aura-username" className="mb-2 block text-sm">Username</label>
          <input id="aura-username" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} className="mb-5 w-full rounded-xl border border-cyan-900/50 bg-[#081525] px-4 py-3 outline-none focus:border-cyan-400" />
          <label htmlFor="aura-password" className="mb-2 block text-sm">Password</label>
          <input id="aura-password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} className="mb-5 w-full rounded-xl border border-cyan-900/50 bg-[#081525] px-4 py-3 outline-none focus:border-cyan-400" />
          {authError && <p role="alert" className="mb-4 text-sm text-red-400">{authError}</p>}
          <button type="submit" disabled={authBusy} className="w-full rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 disabled:opacity-50">{authBusy ? "Signing in..." : "Sign in"}</button>
        </form>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#060d1b] text-slate-100">
      <div className="flex min-h-screen">

        {/* SIDEBAR */}
        <aside className="hidden w-64 shrink-0 border-r border-cyan-900/30 bg-[#0a1526] p-6 md:block">

          <div className="mb-12 text-2xl font-bold tracking-wide text-cyan-400">
            ✦ AURA HEALTH
          </div>

          <nav className="space-y-3">
            <div className="rounded-xl bg-cyan-400/10 px-4 py-3 text-cyan-300">
              ◈ Dashboard
            </div>

            <div className="rounded-xl px-4 py-3 text-slate-400">
              ◉ AI Assistant
            </div>

            <div className="rounded-xl px-4 py-3 text-slate-400">
              ▦ Patients
            </div>
          </nav>

          <div className="mt-16 rounded-xl border border-cyan-800/40 bg-cyan-950/20 p-4 text-xs text-slate-400">
            Learning Environment

            <p className="mt-2 text-cyan-300">
              Fictional patient data only
            </p>
          </div>
        </aside>

        {/* MAIN DASHBOARD */}
        <main className="mx-auto w-full max-w-7xl flex-1 p-5 md:p-10">

          {/* HEADER */}
          <header className="mb-10 flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="mb-2 text-sm tracking-[0.3em] text-cyan-400">
                HEALTHCARE INTELLIGENCE
              </p>

              <h1 className="text-3xl font-bold md:text-4xl">
                AURA AI Command Center
              </h1>

              <p className="mt-3 text-slate-400">
                Intelligent insights for fictional patient records.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="rounded-full border border-cyan-700/50 bg-cyan-950/30 px-4 py-2 text-xs text-cyan-300">● Demo Environment</span>
              <button type="button" onClick={handleLogout} disabled={authBusy} className="rounded-xl border border-cyan-700/50 px-4 py-2 text-sm text-cyan-300 hover:bg-cyan-900/30 disabled:opacity-50">Sign out</button>
            </div>
          </header>

          {/* SUMMARY CARDS */}
          <section className="mb-8 grid gap-4 sm:grid-cols-3">
            {[
              {
                label: "Total Patients",
                value: patientsError
                  ? "—"
                  : patientsLoading
                  ? "..."
                  : patients.length,
                icon: "♧",
              },
              {
                label: "Appointments",
                value: patientsError
                  ? "—"
                  : patientsLoading
                  ? "..."
                  : totalAppointments,
                icon: "▦",
              },
              {
                label: "AURA AI",
                value: isLoading ? "Thinking..." : "Ready",
                icon: "✧",
              },
            ].map((card) => (
              <div
                key={card.label}
                className="rounded-2xl border border-cyan-900/40 bg-[#101e33] p-6 shadow-lg shadow-cyan-950/20 transition hover:border-cyan-500/50 hover:shadow-cyan-500/10"
              >
                <div className="mb-5 text-2xl text-cyan-400">
                  {card.icon}
                </div>

                <p className="text-sm text-slate-400">
                  {card.label}
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {card.value}
                </p>
              </div>
            ))}
          </section>

          {/* CHAT AND PATIENT OVERVIEW */}
          <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">

            {/* AURA AI CHAT */}
            <section className="flex min-h-[480px] flex-col rounded-2xl border border-cyan-900/40 bg-[#101e33] shadow-xl shadow-cyan-950/20">

              <div className="border-b border-cyan-900/40 p-5">
                <h2 className="text-xl font-semibold text-cyan-400">
                  ✧ AURA AI
                </h2>

                <p className="mt-1 text-xs text-slate-400">
                  Your Intelligent Healthcare Assistant
                </p>
              </div>

              {/* CHAT MESSAGES */}
              <div
                className="flex-1 space-y-4 overflow-y-auto p-5"
                aria-live="polite"
              >
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`max-w-[90%] rounded-2xl p-4 text-sm leading-relaxed ${
                      message.role === "user"
                        ? "ml-auto bg-cyan-500 text-slate-950"
                        : "border border-cyan-800/30 bg-[#182b43] text-slate-200"
                    }`}
                  >
                    {message.text}
                  </div>
                ))}

                {isLoading && (
                  <div className="max-w-[90%] rounded-2xl border border-cyan-800/30 bg-[#182b43] p-4 text-sm text-cyan-300">
                    ✧ AURA AI is thinking...
                  </div>
                )}
              </div>

              {/* CHAT INPUT */}
              <form
                onSubmit={handleSubmit}
                className="flex gap-3 border-t border-cyan-900/40 p-4"
              >
                <input
                  type="text"
                  value={question}
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                  placeholder="Ask AURA AI about a fictional patient..."
                  aria-label="Ask AURA AI about a fictional patient"
                  disabled={isLoading}
                  className="min-w-0 flex-1 rounded-xl border border-cyan-900/50 bg-[#081525] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-400 disabled:opacity-60"
                />

                <button
                  type="submit"
                  disabled={!question.trim() || isLoading}
                  className="rounded-xl bg-cyan-400 px-5 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isLoading ? "Thinking..." : "Send"}
                </button>
              </form>
            </section>

            {/* PATIENT OVERVIEW */}
            <section className="rounded-2xl border border-cyan-900/40 bg-[#101e33] p-6">

              <div className="mb-2 flex items-center justify-between gap-3">
                <h2 className="text-xl font-semibold">
                  Patient Overview
                </h2>

                <button
                  type="button"
                  onClick={loadPatients}
                  disabled={patientsLoading}
                  className="rounded-lg border border-cyan-700/50 px-3 py-2 text-xs text-cyan-300 transition hover:bg-cyan-900/30 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {patientsLoading
                    ? "Refreshing..."
                    : "↻ Refresh"}
                </button>
              </div>

              <p className="mb-6 text-xs text-slate-400">
                Fictional SQLite records loaded through FastAPI
              </p>

              <div className="space-y-4">

                {patientsLoading && (
                  <p className="text-sm text-cyan-300">
                    Loading patients...
                  </p>
                )}

                {patientsError && (
                  <p className="text-sm text-red-400">
                    {patientsError}
                  </p>
                )}

                {!patientsLoading &&
                  !patientsError &&
                  patients.length === 0 && (
                    <p className="text-sm text-slate-400">
                      No patient records found.
                    </p>
                  )}

                {!patientsLoading &&
                  !patientsError &&
                  patients.map((patient) => (
                    <div
                      key={patient.id}
                      className="rounded-xl border border-cyan-900/30 bg-[#0a192b] p-4 transition hover:border-cyan-500/40"
                    >
                      <div className="mb-3 flex items-center justify-between">
                        <span className="font-medium">
                          Patient #{patient.id}
                        </span>

                        <span
                          className={`rounded-full px-3 py-1 text-xs ${
                            patient.status === "Active"
                              ? "bg-emerald-500/10 text-emerald-300"
                              : "bg-slate-500/20 text-slate-400"
                          }`}
                        >
                          {patient.status}
                        </span>
                      </div>

                      <p className="text-sm text-slate-400">
                        {patient.appointments} appointments
                      </p>
                    </div>
                  ))}
              </div>
            </section>
          </div>

          {/* FOOTER */}
          <footer className="mt-10 text-center text-xs text-slate-500">
            AURA Health AI · Educational Prototype · No Real Patient Data
          </footer>

        </main>
      </div>
    </div>
  );
}

export default App;
