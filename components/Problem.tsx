import SectionHeading from "./SectionHeading";

const problems = [
  {
    tag: "8 a.m. – 5 p.m.",
    title: "Missed calls during jobs",
    body: "You're elbow-deep in a pump or running a trimmer. The phone rings out, and that homeowner calls the next company on Google.",
    icon: (
      <path d="M3 5a2 2 0 0 1 2-2h2.3a1 1 0 0 1 1 .8l.8 3.7a1 1 0 0 1-.4 1L7 9.6a12 12 0 0 0 7.4 7.4l1.1-1.7a1 1 0 0 1 1-.4l3.7.8a1 1 0 0 1 .8 1V19a2 2 0 0 1-2 2h-1C9.8 21 3 14.2 3 6V5Zm13-2 5 5m0-5-5 5" />
    ),
  },
  {
    tag: "After 5 p.m.",
    title: "After-hours leads go to voicemail",
    body: "Homeowners notice the cloudy pool or the dead sprinkler zone when they get home from work. Most won't leave a voicemail. They'll just call someone else.",
    icon: <path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8Z" />,
  },
  {
    tag: "June – September",
    title: "Summer and monsoon surges",
    body: "One dust storm drops palm fronds in every pool in Gilbert, and your phone lights up all at once. You can't hire a seasonal receptionist for that.",
    icon: <path d="M7 18a4.5 4.5 0 0 1-.6-9A6 6 0 0 1 18 8a4 4 0 0 1 0 8M13 13l-2 4h3l-2 4" />,
  },
];

export default function Problem() {
  return (
    <section className="border-y border-ink/5 bg-white py-20 sm:py-24">
      <div className="container-page">
        <SectionHeading
          eyebrow="The problem"
          title="Every missed call is a job someone else gets."
          intro="Running a service business in the Valley means your hands are full exactly when the phone rings."
        />
        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {problems.map((p) => (
            <article key={p.title} className="rounded-3xl bg-sand-50 p-6 ring-1 ring-ink/5 sm:p-7">
              <div className="flex items-center justify-between">
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white text-pool-500 ring-1 ring-ink/5">
                  <svg
                    viewBox="0 0 24 24"
                    className="h-6 w-6"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    aria-hidden="true"
                  >
                    {p.icon}
                  </svg>
                </span>
                <span className="text-xs font-semibold uppercase tracking-wider text-sun-dark">{p.tag}</span>
              </div>
              <h3 className="mt-5 text-xl font-bold">{p.title}</h3>
              <p className="mt-2 leading-relaxed text-ink-soft">{p.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
