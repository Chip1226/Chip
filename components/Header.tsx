import Logo from "./Logo";

const links = [
  { href: "#how-it-works", label: "How it works" },
  { href: "#pricing", label: "Pricing" },
  { href: "#faq", label: "FAQ" },
];

export default function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-ink/5 bg-sand-50/85 backdrop-blur-md">
      <div className="container-page flex h-16 items-center justify-between gap-4">
        <a href="#top" aria-label="DesertDesk home">
          <Logo />
        </a>
        <nav aria-label="Main" className="hidden items-center gap-8 md:flex">
          {links.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm font-medium text-ink-soft transition hover:text-ink"
            >
              {l.label}
            </a>
          ))}
        </nav>
        <a href="#demo" className="btn-primary min-h-[40px] px-4 py-2 text-sm">
          Book a demo
        </a>
      </div>
    </header>
  );
}
