"use client";

import { useState } from "react";

type Status = "idle" | "sending" | "sent" | "error";
type Errors = Partial<Record<"name" | "company" | "businessType" | "phone" | "email", string>>;

const businessTypes = [
  { value: "pool", label: "Pool" },
  { value: "landscaping", label: "Landscaping" },
  { value: "both", label: "Both" },
];

const inputClass =
  "mt-1.5 block w-full rounded-2xl border border-ink/15 bg-white px-4 py-3 text-base text-ink placeholder:text-ink-muted/70 transition focus:border-pool-500 focus:outline-none focus:ring-4 focus:ring-pool-500/15 aria-[invalid=true]:border-red-500";

export default function DemoForm() {
  const [status, setStatus] = useState<Status>("idle");
  const [errors, setErrors] = useState<Errors>({});
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setStatus("sending");
    setErrors({});
    setMessage("");
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      const res = await fetch("/api/demo-request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      const json = await res.json().catch(() => ({}));
      if (res.ok) {
        setStatus("sent");
        return;
      }
      setErrors(json.errors ?? {});
      setMessage(json.error ?? (json.errors ? "Please fix the highlighted fields." : "Something went wrong."));
      setStatus("error");
    } catch {
      setMessage("Couldn't reach the server. Check your connection and try again.");
      setStatus("error");
    }
  }

  return (
    <section id="demo" className="relative overflow-hidden bg-pool-500 py-20 text-white sm:py-24">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-48 -left-32 h-[30rem] w-[30rem] rounded-full bg-white/10 blur-3xl"
      />
      <div className="container-page relative grid gap-10 lg:grid-cols-[1fr_1.15fr] lg:gap-16">
        <div>
          <p className="eyebrow !text-pool-100">Book a demo</p>
          <h2 className="mt-3 text-3xl font-extrabold leading-[1.08] !text-white sm:text-[2.75rem]">
            Hear it answer <em className="not-italic underline decoration-white/40 decoration-4 underline-offset-[6px]">your</em> calls.
          </h2>
          <p className="mt-4 max-w-md text-lg leading-relaxed text-white/80">
            Tell us a little about your business. We&apos;ll call you back, set up a sample
            line with your company&apos;s name, and let you call it yourself.
          </p>
          <ul className="mt-8 space-y-3 text-white/90">
            <li className="flex gap-3"><Check /> 15-minute call, no pressure</li>
            <li className="flex gap-3"><Check /> Sample built for pool or landscaping calls</li>
            <li className="flex gap-3"><Check /> Local to the Phoenix metro</li>
          </ul>
        </div>

        <div className="rounded-[2rem] bg-sand-50 p-6 text-ink shadow-2xl sm:p-9">
          {status === "sent" ? (
            <div className="py-10 text-center" role="status">
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-pool-50 text-pool-500">
                <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                  <path d="m5 12 5 5 9-10" />
                </svg>
              </span>
              <h3 className="mt-5 text-2xl font-extrabold">Got it, thanks!</h3>
              <p className="mt-2 text-ink-soft">We&apos;ll reach out within one business day to set up your demo.</p>
            </div>
          ) : (
            <form onSubmit={onSubmit} noValidate className="grid gap-5">
              <Field label="Your name" name="name" autoComplete="name" error={errors.name} />
              <Field label="Company name" name="company" autoComplete="organization" error={errors.company} />

              <fieldset>
                <legend className="text-sm font-semibold">Business type</legend>
                <div className="mt-1.5 grid grid-cols-3 gap-2">
                  {businessTypes.map((t) => (
                    <label key={t.value} className="relative cursor-pointer">
                      <input
                        type="radio"
                        name="businessType"
                        value={t.value}
                        required
                        className="peer sr-only"
                        aria-invalid={!!errors.businessType}
                      />
                      <span className="flex min-h-[48px] items-center justify-center rounded-2xl border border-ink/15 bg-white px-2 text-center text-sm font-semibold text-ink-soft transition peer-checked:border-pool-500 peer-checked:bg-pool-50 peer-checked:text-pool-600 peer-focus-visible:ring-4 peer-focus-visible:ring-pool-500/25">
                        {t.label}
                      </span>
                    </label>
                  ))}
                </div>
                {errors.businessType && <p className="mt-1.5 text-sm text-red-600">{errors.businessType}</p>}
              </fieldset>

              <div className="grid gap-5 sm:grid-cols-2">
                <Field label="Phone" name="phone" type="tel" inputMode="tel" autoComplete="tel" placeholder="(480) 555-0123" error={errors.phone} />
                <Field label="Email" name="email" type="email" inputMode="email" autoComplete="email" placeholder="you@company.com" error={errors.email} />
              </div>

              {/* Spam trap, hidden from people */}
              <div aria-hidden="true" className="absolute -left-[9999px] h-0 w-0 overflow-hidden">
                <label>
                  Website
                  <input type="text" name="website" tabIndex={-1} autoComplete="off" />
                </label>
              </div>

              {message && (
                <p className="rounded-2xl bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
                  {message}
                </p>
              )}

              <button type="submit" disabled={status === "sending"} className="btn-primary w-full disabled:opacity-60">
                {status === "sending" ? "Sending…" : "Request my demo"}
              </button>
              <p className="text-center text-xs text-ink-muted">
                We&apos;ll only use your info to contact you about DesertDesk.
              </p>
            </form>
          )}
        </div>
      </div>
    </section>
  );
}

function Field({
  label,
  name,
  error,
  ...props
}: { label: string; name: string; error?: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  const errorId = `${name}-error`;
  return (
    <label className="block">
      <span className="text-sm font-semibold">{label}</span>
      <input
        name={name}
        type="text"
        required
        className={inputClass}
        aria-invalid={!!error}
        aria-describedby={error ? errorId : undefined}
        {...props}
      />
      {error && (
        <span id={errorId} className="mt-1.5 block text-sm text-red-600">
          {error}
        </span>
      )}
    </label>
  );
}

function Check() {
  return (
    <svg viewBox="0 0 20 20" className="mt-0.5 h-5 w-5 shrink-0 text-white" fill="currentColor" aria-hidden="true">
      <path d="M10 18a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm3.7-9.3-4.2 4.2a1 1 0 0 1-1.4 0l-2-2a1 1 0 1 1 1.4-1.4l1.3 1.3 3.5-3.5a1 1 0 1 1 1.4 1.4Z" />
    </svg>
  );
}
