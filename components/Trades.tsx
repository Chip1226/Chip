"use client";

import { useState } from "react";
import SectionHeading from "./SectionHeading";

type Outcome = "Books estimate" | "Transfers to you" | "Takes details" | "Answers & books";

type CallType = { caller: string; title: string; outcome: Outcome };

const trades: Record<"pool" | "landscaping", { label: string; calls: CallType[] }> = {
  pool: {
    label: "Pool service",
    calls: [
      {
        title: "Green or cloudy pool",
        caller: "“My pool turned green after the storm. Can someone come out?”",
        outcome: "Books estimate",
      },
      {
        title: "Weekly service quotes",
        caller: "“What do you charge for weekly service in Gilbert?”",
        outcome: "Answers & books",
      },
      {
        title: "Pump or equipment down",
        caller: "“My pump stopped running and it's 112 out.”",
        outcome: "Transfers to you",
      },
      {
        title: "Filter, heater & repairs",
        caller: "“The heater won't kick on and the filter's making a noise.”",
        outcome: "Books estimate",
      },
      {
        title: "New homeowner / move-in",
        caller: "“We just bought a house in Mesa with a pool. Where do we start?”",
        outcome: "Books estimate",
      },
      {
        title: "Existing customer questions",
        caller: "“Is my tech still coming Friday?”",
        outcome: "Takes details",
      },
    ],
  },
  landscaping: {
    label: "Landscaping",
    calls: [
      {
        title: "Irrigation & drip leaks",
        caller: "“There's water bubbling up by the driveway. I think a line broke.”",
        outcome: "Transfers to you",
      },
      {
        title: "Monthly maintenance quotes",
        caller: "“How much for monthly yard maintenance in Scottsdale?”",
        outcome: "Answers & books",
      },
      {
        title: "Monsoon storm cleanup",
        caller: "“The storm dropped half a mesquite in the backyard.”",
        outcome: "Books estimate",
      },
      {
        title: "Tree trimming",
        caller: "“I want the palms trimmed before monsoon season.”",
        outcome: "Books estimate",
      },
      {
        title: "Fall overseeding",
        caller: "“Do you do winter rye overseeding? When should we start?”",
        outcome: "Answers & books",
      },
      {
        title: "Desert landscape & gravel installs",
        caller: "“We want to rip out the grass and go xeriscape.”",
        outcome: "Books estimate",
      },
    ],
  },
};

const outcomeStyles: Record<Outcome, string> = {
  "Books estimate": "bg-pool-100 text-pool-700",
  "Answers & books": "bg-pool-100 text-pool-700",
  "Transfers to you": "bg-sun text-ink",
  "Takes details": "bg-sand-200 text-ink-soft",
};

export default function Trades() {
  const [active, setActive] = useState<"pool" | "landscaping">("pool");

  return (
    <section className="bg-ink py-20 text-white sm:py-24">
      <div className="container-page">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
          <SectionHeading
            light
            eyebrow="Built for your trade"
            title="It knows a pump from a drip line."
            intro="DesertDesk is set up for the calls you actually get, not generic office calls."
          />
          <div
            role="tablist"
            aria-label="Choose your trade"
            className="inline-flex w-full rounded-full bg-white/10 p-1 sm:w-auto"
          >
            {(Object.keys(trades) as (keyof typeof trades)[]).map((key) => (
              <button
                key={key}
                role="tab"
                id={`tab-${key}`}
                aria-selected={active === key}
                aria-controls={`panel-${key}`}
                onClick={() => setActive(key)}
                className={`min-h-[44px] flex-1 rounded-full px-5 text-sm font-semibold transition sm:flex-none ${
                  active === key ? "bg-white text-ink" : "text-white/75 hover:text-white"
                }`}
              >
                {trades[key].label}
              </button>
            ))}
          </div>
        </div>

        {(Object.keys(trades) as (keyof typeof trades)[]).map((key) => (
          <div
            key={key}
            role="tabpanel"
            id={`panel-${key}`}
            aria-labelledby={`tab-${key}`}
            hidden={active !== key}
            className={`mt-10 gap-4 sm:grid-cols-2 lg:grid-cols-3 ${active === key ? "grid" : "hidden"}`}
          >
            {trades[key].calls.map((c) => (
              <article
                key={c.title}
                className="flex flex-col rounded-3xl bg-white/[0.06] p-6 ring-1 ring-white/10"
              >
                <h3 className="text-lg font-bold !text-white">{c.title}</h3>
                <p className="mt-2 flex-1 leading-relaxed text-white/70">{c.caller}</p>
                <span
                  className={`mt-5 inline-flex self-start rounded-full px-3 py-1 text-xs font-semibold ${outcomeStyles[c.outcome]}`}
                >
                  {c.outcome}
                </span>
              </article>
            ))}
          </div>
        ))}

        <p className="mt-8 text-sm text-white/55">
          You decide what counts as urgent. Urgent-call transfer is included on the Full-Time plan.
        </p>
      </div>
    </section>
  );
}
