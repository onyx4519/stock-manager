import Link from "next/link";

const items = [
  ["Dashboard", "/"],
  ["Market", "/market"],
  ["Stocks", "/stocks"],
  ["Portfolio", "/portfolio"],
  ["Watchlist", "/watchlist"],
  ["Events", "/events"],
] as const;

export function Sidebar() {
  return (
    <aside className="sidebar" aria-label="주요 메뉴">
      <Link aria-label="메인 화면으로 이동" className="brand" href="/">
        Stock Manager
      </Link>
      <nav>
        {items.map(([label, href]) => (
          <Link key={href} href={href} className="navItem">
            {label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
