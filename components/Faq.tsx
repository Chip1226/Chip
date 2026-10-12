import SectionHeading from "./SectionHeading";

const faqs = [
  {
    q: "Will my customers know they're talking to AI?",
    a: "It sounds natural and friendly, like a good front desk. But it's honest: if a caller asks whether they're talking to a real person, it tells them it's an AI assistant for your business and keeps helping them, or takes a message for you.",
  },
  {
    q: "Do I keep my business phone number?",
    a: "Yes. Your number stays the same, on your truck, your yard signs, and your Google listing. You just forward calls to DesertDesk, either all the time, only after hours, or only when you don't pick up. You can turn forwarding off anytime.",
  },
  {
    q: "What happens with emergencies?",
    a: "You decide what counts as urgent, like a pump down in July or a broken irrigation line flooding a yard. On the Full-Time plan, those calls get transferred straight to your cell. Routine calls get booked or summarized so they don't interrupt you on a job.",
  },
  {
    q: "Does it work with Google Calendar?",
    a: "Yes. On the Full-Time plan, DesertDesk books estimates directly into your Google Calendar, only in the time slots you've set aside, so it won't double-book you.",
  },
  {
    q: "Am I locked into a contract?",
    a: "No. Both plans are month to month. There's a one-time $299.99 setup fee, and after that you can cancel whenever you want.",
  },
];

export default function Faq() {
  return (
    <section id="faq" className="border-t border-ink/5 bg-white py-20 sm:py-24">
      <div className="container-page grid gap-10 lg:grid-cols-[1fr_1.6fr] lg:gap-16">
        <SectionHeading
          eyebrow="FAQ"
          title="Questions owners ask us."
          intro={
            <>
              Something else on your mind?{" "}
              <a href="#demo" className="font-semibold text-pool-500 underline-offset-4 hover:underline">
                Ask us on a demo call.
              </a>
            </>
          }
        />
        <div className="divide-y divide-ink/10 border-y border-ink/10">
          {faqs.map((f) => (
            <details key={f.q} className="group py-1">
              <summary className="flex min-h-[56px] cursor-pointer list-none items-center justify-between gap-4 py-4 font-display text-lg font-bold text-ink [&::-webkit-details-marker]:hidden">
                {f.q}
                <span
                  aria-hidden="true"
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-pool-50 text-pool-500 transition group-open:rotate-45"
                >
                  <svg viewBox="0 0 20 20" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
                    <path d="M10 4v12M4 10h12" />
                  </svg>
                </span>
              </summary>
              <p className="pb-5 pr-10 leading-relaxed text-ink-soft">{f.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
