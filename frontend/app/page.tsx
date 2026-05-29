"use client";

import { useState } from "react";

export default function Home() {
  const [loading, setLoading] = useState(false);

  async function handleLogin() {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`);
      const data = await res.json();
      window.location.href = data.auth_url;
    } catch {
      // The free-tier backend may still be waking up; let the user retry.
      setLoading(false);
    }
  }

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#0C0C0F", color: "#F0EDE8", fontFamily: "'DM Sans', sans-serif", overflow: "hidden" }}>
      {/* Load fonts */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        .btn:not(:disabled):hover { background: rgba(255,255,255,0.09) !important; border-color: rgba(255,255,255,0.15) !important; transform: translateY(-1px); }
        @keyframes pulse { 0%,100%{transform:scale(1);opacity:1} 50%{transform:scale(1.1);opacity:0.7} }
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>

      {/* Left panel */}
      <div style={{ width: "52%", padding: "3rem", display: "flex", flexDirection: "column", justifyContent: "space-between", position: "relative", borderRight: "1px solid rgba(255,255,255,0.06)" }}>
        <div style={{ position: "absolute", width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.15) 0%, transparent 70%)", top: -100, left: -100, animation: "pulse 6s ease-in-out infinite" }} />
        <div style={{ position: "absolute", width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle, rgba(168,85,247,0.08) 0%, transparent 70%)", bottom: 50, right: 50, animation: "pulse 8s ease-in-out infinite reverse" }} />

        <div style={{ fontSize: 13, fontWeight: 500, letterSpacing: "0.08em", color: "rgba(240,237,232,0.4)", textTransform: "uppercase" }}>Meeting Prep</div>

        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(240,237,232,0.35)", marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ display: "block", width: 20, height: 1, background: "rgba(240,237,232,0.25)" }} />
            AI-powered preparation
          </div>
          <h1 style={{ fontFamily: "'DM Serif Display', serif", fontSize: "3.5rem", lineHeight: 1.1, fontWeight: 400, marginBottom: "1.5rem" }}>
            Walk in<br />
            <em style={{ fontStyle: "italic", color: "rgba(240,237,232,0.5)" }}>ready for</em><br />
            anything.
          </h1>
          <p style={{ fontSize: 15, fontWeight: 300, color: "rgba(240,237,232,0.45)", lineHeight: 1.7, maxWidth: 360 }}>
            Automatically researches your attendees, surfaces relevant emails, and drafts your talking points — 30 minutes before every meeting.
          </p>
        </div>

        <div style={{ fontSize: 12, color: "rgba(240,237,232,0.2)", fontWeight: 300 }}>Powered by Claude · Google Calendar · Gmail</div>
      </div>

      {/* Right panel */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "3rem" }}>
        <div style={{ width: "100%", maxWidth: 360 }}>
          <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(240,237,232,0.3)", marginBottom: "2rem" }}>Get started</div>

          <div style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "2.5rem" }}>
            {[
              { icon: "📅", title: "Calendar sync", desc: "Reads your upcoming events automatically" },
              { icon: "🔍", title: "Attendee research", desc: "Finds context on who you're meeting" },
              { icon: "✉️", title: "Email context", desc: "Surfaces relevant recent threads" },
            ].map((f) => (
              <div key={f.title} style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                <div style={{ width: 28, height: 28, borderRadius: 6, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.07)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, flexShrink: 0 }}>{f.icon}</div>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500, color: "rgba(240,237,232,0.8)", marginBottom: 2 }}>{f.title}</div>
                  <div style={{ fontSize: 12, color: "rgba(240,237,232,0.3)", fontWeight: 300, lineHeight: 1.5 }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ height: 1, background: "rgba(255,255,255,0.06)", marginBottom: "2rem" }} />

          <button
            className="btn"
            onClick={handleLogin}
            disabled={loading}
            style={{ width: "100%", padding: "13px 20px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.1)", background: "rgba(255,255,255,0.05)", color: "rgba(240,237,232,0.9)", fontFamily: "'DM Sans', sans-serif", fontSize: 14, fontWeight: 500, cursor: loading ? "default" : "pointer", opacity: loading ? 0.65 : 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 10, transition: "all 0.2s", letterSpacing: "0.01em" }}
          >
            {loading ? (
              <>
                <span style={{ width: 15, height: 15, borderRadius: "50%", border: "2px solid rgba(240,237,232,0.25)", borderTopColor: "rgba(240,237,232,0.9)", animation: "spin 0.7s linear infinite", flexShrink: 0 }} />
                Waking up the server…
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Sign in with Google
              </>
            )}
          </button>

          <p style={{ textAlign: "center", fontSize: 11, color: "rgba(240,237,232,0.2)", marginTop: "1rem", fontWeight: 300, lineHeight: 1.6 }}>
            {loading
              ? "First load can take up to a minute while the free-tier server starts up."
              : <>Read-only access to Calendar and Gmail.<br />Your data is never stored or shared.</>}
          </p>
        </div>
      </div>
    </div>
  );
}