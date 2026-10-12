import CallTranscript from "./CallTranscript";

export default function Hero() {
  return (
    <section id="top" className="relative overflow-hidden">
      {/* Soft pool-water glow in the background */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-40 -top-40 h-[36rem] w-[36rem] rounded-full bg-pool-100/60 blur-3xl"
      />
      <div className="container-page relative grid gap-12 pb-20 pt-10 sm:pt-16 lg:grid-cols-[1.1fr_1fr] lg:items-center lg:gap-16 lg:pb-28 lg:pt-20">
        <div>
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border border-pool-500/20 bg-white/70 px-3 py-1 text-[0.8rem] font-medium text-pool-600 sm:text-sm">
            <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
            For Phoenix-area pool &amp; landscaping pros
          </p>
          <h1 className="text-[2.6rem] font-extrabold leading-[1.02] sm:text-6xl lg:text-[4.25rem]">
            Your crew&apos;s in the yard.{" "}
            <span className="text-pool-500">Your phone still gets answered.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-soft sm:text-xl">
            DesertDesk is an AI receptionist that answers every call, 24/7. It books
            estimates while you&apos;re on a job, and texts you a quick summary of every
            call so nothing slips through.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a href="#sample-call" className="btn-primary">
              <PlayIcon />
              Hear a sample call
            </a>
            <a href="#pricing" className="btn-secondary">
              See pricing
            </a>
          </div>
          <ul className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-sm text-ink-muted">
            <li>✓ Keep your number</li>
            <li>✓ No contracts</li>
            <li>✓ Live 24/7, holidays too</li>
          </ul>
        </div>

        <CallTranscript />
      </div>
    </section>
  );
}

function PlayIcon() {
  return (
    <svg viewBox="0 0 20 20" className="h-5 w-5" aria-hidden="true" fill="currentColor">
      <path d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16ZM8.5 6.9l4.8 2.7a.5.5 0 0 1 0 .8l-4.8 2.7A.5.5 0 0 1 7.8 12.7V7.3a.5.5 0 0 1 .7-.4Z" />
    </svg>
  );
}
