import Link from "next/link";

const items = [
  ["홈", "/"],
  ["시장", "/market"],
  ["종목", "/stocks"],
  ["포트", "/portfolio"],
  ["이벤트", "/events"],
] as const;

export function MobileNav() {
  return (
    <nav className="mobileNav" aria-label="모바일 메뉴">
      {items.map(([label, href]) => (
        <Link key={href} href={href} className="mobileNavItem">{label}</Link>
      ))}
    </nav>
  );
}
