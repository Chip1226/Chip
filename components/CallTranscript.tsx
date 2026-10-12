"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Line = { who: "ai" | "caller"; text: string };

// Example call. Business name, caller, and phone number are made up.
const lines: Line[] = [
  { who: "ai", text: "Thanks for calling Sonoran Clear Pools, how can I help?" },
  {
    who: "caller",
    text: "Hi, my pool went totally green after that storm. I'm in Chandler, near Ray and Alma School.",
  },
  {
    who: "ai",
    text: "Monsoon storms will do that. We can send a tech out to quote a green-to-clean. Is this a one-time cleanup, or are you looking for weekly service too?",
  },
  { who: "caller", text: "Cleanup first. Maybe weekly after that." },
  { who: "ai", text: "Got it. I have Thursday between 8 and 10 a.m. open in Chandler. Does that work?" },
  { who: "caller", text: "Thursday morning's perfect." },
  { who: "ai", text: "Great. What's your name and the best number to text a confirmation to?" },
  { who: "caller", text: "Maria Lopez, 480-555-0142." },
  {
    who: "ai",
    text: "You're all set, Maria: Thursday, 8 to 10 a.m., green pool estimate. Your confirmation text is on its way.",
  },
];

export default function CallTranscript() {
  // How many lines are revealed. Starts at "all" so the text is in the page
  // before JavaScript runs (good for search engines and slow connections).
  const [shown, setShown] = useState(lines.length + 1);
  const [playing, setPlaying] = useState(false);
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const rootRef = useRef<HTMLDivElement>(null);
  const threadRef = useRef<HTMLOListElement>(null);
  const hasAutoPlayed = useRef(false);

  const clearTimers = () => {
    timers.current.forEach(clearTimeout);
    timers.current = [];
  };

  const play = useCallback(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(lines.length + 1);
      return;
    }
    clearTimers();
    setShown(0);
    setPlaying(true);
    let t = 400;
    lines.forEach((line, i) => {
      timers.current.push(setTimeout(() => setShown(i + 1), t));
      // Longer lines stay on screen a little longer before the reply
      t += 700 + line.text.length * 22;
    });
    // Finally, the owner text summary
    timers.current.push(
      setTimeout(() => {
        setShown(lines.length + 1);
        setPlaying(false);
      }, t + 200),
    );
  }, []);

  // Auto-play the first time the transcript scrolls into view
  useEffect(() => {
    const el = rootRef.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !hasAutoPlayed.current) {
          hasAutoPlayed.current = true;
          play();
        }
      },
      { threshold: 0.35 },
    );
    io.observe(el);
    return () => {
      io.disconnect();
      clearTimers();
    };
  }, [play]);

  // Replay when someone clicks "Hear a sample call"
  useEffect(() => {
    const onHash = () => {
      if (window.location.hash === "#sample-call") {
        hasAutoPlayed.current = true;
        play();
      }
    };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, [play]);

  // Keep the newest line in view, like a text thread
  useEffect(() => {
    const el = threadRef.current;
    if (el && playing) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [shown, playing]);

  const nextIsAi = shown < lines.length && lines[shown]?.who === "ai";

  return (
    <div id="sample-call" ref={rootRef} className="relative mx-auto w-full max-w-md lg:max-w-none">
      <div className="rounded-[1.75rem] border border-ink/10 bg-white p-4 shadow-[0_20px_60px_-25px_rgba(10,110,140,0.45)] sm:p-5">
        {/* Call header */}
        <div className="flex items-center justify-between rounded-2xl bg-ink px-4 py-3 text-white">
          <div className="flex items-center gap-3">
            <span className="relative flex h-2.5 w-2.5">
              {playing && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              )}
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-emerald-400" />
            </span>
            <div className="leading-tight">
              <p className="text-sm font-semibold">
                Incoming call<span className="hidden sm:inline"> · (480) 555-0142</span>
              </p>
              <p className="text-xs text-white/60" aria-live="off">
                {playing && shown < lines.length
                  ? nextIsAi
                    ? "DesertDesk is speaking…"
                    : "Caller is speaking…"
                  : "Tuesday, 6:47 p.m. · answered by DesertDesk"}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={play}
            className="rounded-full bg-white/10 px-3 py-1.5 text-xs font-semibold transition hover:bg-white/20"
          >
            {playing ? "Playing…" : "Replay"}
          </button>
        </div>

        {/* Transcript */}
        <ol
          ref={threadRef}
          className="mt-3 h-[21rem] space-y-2.5 overflow-y-auto overscroll-contain pb-1 pt-3 sm:h-[23rem]"
          style={{ maskImage: "linear-gradient(to bottom, transparent, #000 1.25rem)" }}
          aria-label="Sample call transcript"
        >
          {lines.map((line, i) => {
            const visible = i < shown;
            const ai = line.who === "ai";
            return (
              <li
                key={i}
                className={`flex transition-all duration-300 ${ai ? "justify-start" : "justify-end"} ${
                  visible ? "translate-y-0 opacity-100" : "hidden"
                }`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl px-3.5 py-2 text-[0.94rem] leading-snug ${
                    ai
                      ? "rounded-bl-md bg-pool-50 text-ink"
                      : "rounded-br-md bg-sand-100 text-ink"
                  }`}
                >
                  <span className="mb-0.5 block text-[0.7rem] font-semibold uppercase tracking-wider text-ink-muted">
                    {ai ? "DesertDesk" : "Caller"}
                  </span>
                  {line.text}
                </div>
              </li>
            );
          })}
        </ol>

        {/* Owner text summary */}
        <div
          className={`mt-4 rounded-2xl border border-pool-500/25 bg-pool-500 p-4 text-white transition-all duration-500 ${
            shown > lines.length ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"
          }`}
        >
          <p className="text-xs font-semibold uppercase tracking-wider text-white/70">
            Text to owner · just now
          </p>
          <p className="mt-1.5 text-[0.95rem] leading-snug">
            <strong>New estimate booked:</strong> Maria Lopez, Chandler (Ray &amp; Alma School).
            Green pool after storm, wants cleanup, open to weekly service.{" "}
            <strong>Thu 8–10 a.m.</strong> · 480-555-0142
          </p>
        </div>
      </div>
    </div>
  );
}
