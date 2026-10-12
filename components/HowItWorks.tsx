import SectionHeading from "./SectionHeading";

const steps = [
  {
    title: "We set it up",
    body: "We learn your services, service area, hours, and how you like to quote. You approve how it greets callers. You don't need to learn any software.",
  },
  {
    title: "Forward your calls",
    body: "Keep your existing number. Forward calls to DesertDesk all the time, only after hours, or only when you don't pick up. It's your call.",
  },
  {
    title: "Get booked jobs",
    body: "Estimates land on your calendar, and you get a text summary of every call: who called, where they are, what they need, and what was booked.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 sm:py-24">
      <div className="container-page">
        <SectionHeading
          eyebrow="How it works"
          title="Up and running without lifting a finger."
          intro="Three steps. We do the setup, so you can stay on the route."
        />
        <ol className="relative mt-12 grid gap-8 md:grid-cols-3 md:gap-6">
          {/* Connector line on desktop */}
          <div
            aria-hidden="true"
            className="absolute left-6 right-6 top-6 hidden border-t-2 border-dashed border-pool-500/25 md:block"
          />
          {steps.map((s, i) => (
            <li key={s.title} className="relative flex gap-5 md:block">
              <span className="relative z-10 flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-pool-500 font-display text-xl font-extrabold text-white ring-8 ring-sand-50">
                {i + 1}
              </span>
              <div className="md:mt-6">
                <h3 className="text-xl font-bold">{s.title}</h3>
                <p className="mt-2 leading-relaxed text-ink-soft">{s.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
