import SectionHeading from "./SectionHeading";

const plans = [
  {
    name: "Starter",
    price: "99",
    cents: "",
    blurb: "For owner-operators who need every call answered.",
    calls: "Up to 100 calls / month",
    features: [
      "Answers every call, 24/7",
      "Captures name, address, and job details",
      "Text summary of every call",
      "Custom greeting with your business name",
    ],
    featured: false,
  },
  {
    name: "Full-Time",
    price: "149",
    cents: ".99",
    blurb: "For busy crews that want jobs booked, not just messages.",
    calls: "Up to 300 calls / month",
    features: [
      "Everything in Starter",
      "Books estimates on your calendar",
      "Urgent-call transfer to your cell",
      "Built to handle monsoon-season call surges",
    ],
    featured: true,
  },
];

export default function Pricing() {
  return (
    <section id="pricing" className="py-20 sm:py-24">
      <div className="container-page">
        <SectionHeading
          eyebrow="Pricing"
          title="Less than one missed job a month."
          intro="Simple monthly plans. Month to month, no contracts."
        />

        <div className="mt-12 grid gap-5 lg:grid-cols-2">
          {plans.map((p) => (
            <article
              key={p.name}
              className={`relative flex flex-col rounded-[2rem] p-7 sm:p-9 ${
                p.featured
                  ? "bg-pool-500 text-white shadow-[0_24px_60px_-28px_rgba(10,110,140,0.8)]"
                  : "bg-white ring-1 ring-ink/10"
              }`}
            >
              {p.featured && (
                <span className="absolute right-6 top-6 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold uppercase tracking-wider">
                  Most popular
                </span>
              )}
              <h3 className={`text-2xl font-extrabold ${p.featured ? "!text-white" : ""}`}>
                {p.name}
              </h3>
              <p className={`mt-2 ${p.featured ? "text-white/80" : "text-ink-soft"}`}>{p.blurb}</p>

              <p className="mt-6 flex items-start font-display">
                <span className="mt-2 text-2xl font-bold">$</span>
                <span className="text-6xl font-extrabold tracking-tight">{p.price}</span>
                {p.cents && <span className="mt-2 text-2xl font-bold">{p.cents}</span>}
                <span className={`ml-2 self-end pb-2 text-base font-sans ${p.featured ? "text-white/75" : "text-ink-muted"}`}>
                  / month
                </span>
              </p>
              <p
                className={`mt-2 inline-flex self-start rounded-full px-3 py-1 text-sm font-semibold ${
                  p.featured ? "bg-white text-pool-600" : "bg-pool-50 text-pool-600"
                }`}
              >
                {p.calls}
              </p>

              <ul className="mt-7 flex-1 space-y-3">
                {p.features.map((f) => (
                  <li key={f} className="flex gap-3">
                    <svg
                      viewBox="0 0 20 20"
                      className={`mt-0.5 h-5 w-5 shrink-0 ${p.featured ? "text-white" : "text-pool-500"}`}
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.7-9.3-4.2 4.2a1 1 0 0 1-1.4 0l-2-2a1 1 0 1 1 1.4-1.4l1.3 1.3 3.5-3.5a1 1 0 1 1 1.4 1.4Z" />
                    </svg>
                    <span className={p.featured ? "text-white/95" : ""}>{f}</span>
                  </li>
                ))}
              </ul>

              <a
                href="#demo"
                className={`mt-8 ${
                  p.featured ? "btn bg-white text-pool-600 hover:bg-sand-100" : "btn-primary"
                }`}
              >
                Get started with {p.name}
              </a>
            </article>
          ))}
        </div>

        <div className="mt-6 flex flex-col gap-2 rounded-3xl border border-dashed border-ink/15 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-ink">
            <strong className="font-semibold">One-time setup fee: $299.99.</strong>{" "}
            <span className="text-ink-soft">We build and test your call flow for you.</span>
          </p>
          <p className="text-sm font-semibold text-pool-600">Month to month · No contracts</p>
        </div>
      </div>
    </section>
  );
}
