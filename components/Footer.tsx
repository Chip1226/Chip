import Logo from "./Logo";

const cities = ["Phoenix", "Scottsdale", "Mesa", "Chandler", "Gilbert", "Tempe", "Glendale", "Peoria", "Queen Creek", "Surprise"];

export default function Footer() {
  return (
    <footer className="bg-sand-100 py-12">
      <div className="container-page flex flex-col gap-8 md:flex-row md:items-start md:justify-between">
        <div className="max-w-sm">
          <Logo />
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            The 24/7 AI receptionist for pool service and landscaping companies across the Phoenix metro.
          </p>
        </div>
        <div>
          <p className="text-sm font-semibold">Serving the Valley</p>
          <p className="mt-2 max-w-md text-sm leading-relaxed text-ink-soft">{cities.join(" · ")}</p>
        </div>
      </div>
      <div className="container-page mt-10">
        <div className="flex flex-col gap-2 border-t border-ink/10 pt-6 text-xs text-ink-muted sm:flex-row sm:justify-between">
        <p>© {new Date().getFullYear()} DesertDesk. All rights reserved.</p>
        <p>Made in Arizona ☀️</p>
        </div>
      </div>
    </footer>
  );
}
