"use client";
import { useState, useEffect } from "react";

type Meeting = {
  id: string;
  title: string;
  start: string;
  attendees: string[];
  agenda: string;
};

function formatTime(iso: string) {
  if (!iso) return "Time TBD";
  const d = new Date(iso);
  const today = new Date();
  const tomorrow = new Date();
  tomorrow.setDate(today.getDate() + 1);
  const isToday = d.toDateString() === today.toDateString();
  const isTomorrow = d.toDateString() === tomorrow.toDateString();
  const day = isToday ? "Today" : isTomorrow ? "Tomorrow" : d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  return `${day} · ${time}`;
}

function parseBriefSections(brief: string) {
  const sectionTitles = ["Meeting Overview", "Attendee Profiles", "Recent Email Context", "Suggested Talking Points", "Open Items"];
  const sections: { title: string; body: string }[] = [];
  sectionTitles.forEach((title, i) => {
    const nextTitle = sectionTitles[i + 1];
    const regex = new RegExp(`(?:#+\\s*)?(?:\\d+\\.\\s*)?\\*{0,2}${title}\\*{0,2}[:\\s]*(.*?)(?=${nextTitle ? `(?:#+\\s*)?(?:\\d+\\.\\s*)?\\*{0,2}${nextTitle}` : "$"})`, "si");
    const match = brief.match(regex);
    if (match) {
      sections.push({ title, body: match[1].replace(/\*\*/g, "").trim() });
    }
  });
  if (sections.length === 0) {
    sections.push({ title: "Meeting Brief", body: brief.replace(/\*\*/g, "").replace(/#{1,3} /g, "") });
  }
  return sections;
}

export default function MeetingsPage() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [selected, setSelected] = useState<Meeting | null>(null);
  const [brief, setBrief] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [fetchingMeetings, setFetchingMeetings] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/meetings")
      .then((r) => r.json())
      .then((d) => {
        if (d.meetings) setMeetings(d.meetings);
        setFetchingMeetings(false);
      });
  }, []);

  async function generateBrief(meeting: Meeting) {
    setSelected(meeting);
    setBrief("");
    setLoading(true);
    const res = await fetch(`http://localhost:8000/meetings/${meeting.id}/brief`, { method: "POST" });
    const data = await res.json();
    setBrief(data.brief);
    setLoading(false);
  }

  const sections = brief ? parseBriefSections(brief) : [];

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif", background: "#0C0C0F", color: "#F0EDE8", minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');
        * { margin: 0; padding: 0; box-sizing: border-box; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }
        @keyframes shimmer { to { left: 100%; } }
        @keyframes fadein { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        .meeting-card:hover { background: rgba(255,255,255,0.05) !important; border-color: rgba(255,255,255,0.08) !important; }
      `}</style>

      {/* Topbar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1.25rem 2rem", borderBottom: "1px solid rgba(255,255,255,0.06)", flexShrink: 0 }}>
        <div style={{ fontSize: 12, fontWeight: 500, letterSpacing: "0.08em", color: "rgba(240,237,232,0.35)", textTransform: "uppercase" }}>Meeting Prep</div>
        <div style={{ fontSize: 12, color: "rgba(240,237,232,0.2)", fontWeight: 300 }}>
          {new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}
        </div>
      </div>

      {/* Main layout */}
      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", flex: 1, overflow: "hidden", height: "calc(100vh - 57px)" }}>

        {/* Sidebar */}
        <div style={{ borderRight: "1px solid rgba(255,255,255,0.06)", overflowY: "auto", padding: "1.5rem" }}>
          <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(240,237,232,0.2)", marginBottom: "1rem", padding: "0 0.25rem" }}>
            Upcoming · 72hrs
          </div>

          {fetchingMeetings && (
            <div style={{ padding: "0.5rem 0.25rem", fontSize: 13, color: "rgba(240,237,232,0.2)", fontWeight: 300 }}>Loading...</div>
          )}

          {!fetchingMeetings && meetings.length === 0 && (
            <div style={{ padding: "0.5rem 0.25rem", fontSize: 13, color: "rgba(240,237,232,0.2)", fontWeight: 300 }}>No upcoming meetings</div>
          )}

          {meetings.map((m) => (
            <div
              key={m.id}
              className="meeting-card"
              onClick={() => generateBrief(m)}
              style={{
                padding: "0.875rem 1rem",
                borderRadius: 12,
                border: `1px solid ${selected?.id === m.id ? "rgba(255,255,255,0.12)" : "rgba(255,255,255,0.05)"}`,
                background: selected?.id === m.id ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.02)",
                marginBottom: 8,
                cursor: "pointer",
                transition: "all 0.15s",
              }}
            >
              <div style={{ fontSize: 11, color: "rgba(240,237,232,0.3)", marginBottom: 5, display: "flex", alignItems: "center", gap: 6 }}>
                <div style={{ width: 5, height: 5, borderRadius: "50%", background: "rgba(99,102,241,0.7)", flexShrink: 0 }} />
                {formatTime(m.start)}
              </div>
              <div style={{ fontSize: 14, fontWeight: 500, color: "rgba(240,237,232,0.85)", marginBottom: 4, lineHeight: 1.3 }}>{m.title}</div>
              <div style={{ fontSize: 12, color: "rgba(240,237,232,0.25)", fontWeight: 300, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {m.attendees.length > 0 ? m.attendees.join(", ") : "No external attendees"}
              </div>
            </div>
          ))}
        </div>

        {/* Content panel */}
        <div style={{ overflowY: "auto", padding: "2.5rem", position: "relative" }}>
          {/* Background orbs */}
          <div style={{ position: "fixed", width: 400, height: 400, borderRadius: "50%", background: "radial-gradient(circle, rgba(99,102,241,0.08) 0%, transparent 70%)", top: -100, right: -100, pointerEvents: "none" }} />
          <div style={{ position: "fixed", width: 300, height: 300, borderRadius: "50%", background: "radial-gradient(circle, rgba(168,85,247,0.05) 0%, transparent 70%)", bottom: 0, left: 400, pointerEvents: "none" }} />

          {/* Empty state */}
          {!selected && !loading && (
            <div style={{ position: "relative", zIndex: 1, height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", minHeight: 400 }}>
              <div style={{ fontSize: 40, marginBottom: "1rem", opacity: 0.2 }}>📋</div>
              <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "1.5rem", color: "rgba(240,237,232,0.35)", fontWeight: 400, marginBottom: "0.5rem" }}>Select a meeting</div>
              <div style={{ fontSize: 13, color: "rgba(240,237,232,0.18)", fontWeight: 300 }}>Choose one from the left to generate a brief</div>
            </div>
          )}

          {/* Loading state */}
          {loading && (
            <div style={{ position: "relative", zIndex: 1, animation: "fadein 0.3s ease" }}>
              <div style={{ marginBottom: "2rem" }}>
                <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(240,237,232,0.2)", marginBottom: "0.5rem" }}>Meeting Brief</div>
                <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "1.8rem", fontWeight: 400, color: "rgba(240,237,232,0.7)" }}>{selected?.title}</div>
              </div>
              <div style={{ fontSize: 12, color: "rgba(240,237,232,0.2)", fontWeight: 300, marginBottom: "1.5rem" }}>Researching attendees and generating brief...</div>
              {["70%", "50%", "85%", "60%"].map((w, i) => (
                <div key={i} style={{ height: 3, background: "rgba(255,255,255,0.04)", borderRadius: 2, marginBottom: 10, overflow: "hidden", position: "relative", width: w }}>
                  <div style={{ position: "absolute", top: 0, left: "-100%", width: "100%", height: "100%", background: "linear-gradient(90deg, transparent, rgba(99,102,241,0.4), transparent)", animation: `shimmer 1.5s infinite ${i * 0.2}s` }} />
                </div>
              ))}
            </div>
          )}

          {/* Brief */}
          {!loading && brief && sections.length > 0 && (
            <div style={{ position: "relative", zIndex: 1, animation: "fadein 0.4s ease" }}>
              <div style={{ marginBottom: "2rem" }}>
                <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(240,237,232,0.25)", marginBottom: "0.5rem" }}>Meeting Brief</div>
                <div style={{ fontFamily: "'DM Serif Display', serif", fontSize: "1.8rem", fontWeight: 400, color: "rgba(240,237,232,0.9)", lineHeight: 1.2 }}>{selected?.title}</div>
              </div>

              {sections.map((s, i) => (
                <div key={i} style={{ marginBottom: "1rem", padding: "1.25rem 1.5rem", background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.06)", borderRadius: 12 }}>
                  <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: "0.1em", textTransform: "uppercase", color: "rgba(240,237,232,0.28)", marginBottom: "0.75rem" }}>{s.title}</div>
                  <div style={{ fontSize: 13, color: "rgba(240,237,232,0.6)", fontWeight: 300, lineHeight: 1.75, whiteSpace: "pre-wrap" }}>{s.body}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}