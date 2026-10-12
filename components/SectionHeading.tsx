export default function SectionHeading({
  eyebrow,
  title,
  intro,
  light = false,
}: {
  eyebrow: string;
  title: React.ReactNode;
  intro?: React.ReactNode;
  light?: boolean;
}) {
  return (
    <div className="max-w-2xl">
      <p className={`eyebrow ${light ? "!text-pool-100" : ""}`}>{eyebrow}</p>
      <h2
        className={`mt-3 text-3xl font-extrabold leading-[1.08] sm:text-[2.75rem] ${
          light ? "!text-white" : ""
        }`}
      >
        {title}
      </h2>
      {intro && (
        <p className={`mt-4 text-lg leading-relaxed ${light ? "text-white/75" : "text-ink-soft"}`}>
          {intro}
        </p>
      )}
    </div>
  );
}
