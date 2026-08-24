import type { Metadata } from "next";
import { Suspense } from "react";
import { DataModeBadge } from "@/components/DataModeBadge";
import { AccountStatus } from "@/components/AccountStatus";
import { Sidebar } from "@/components/Sidebar";
import { MobileNav } from "@/components/MobileNav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Stock Manager MVP",
  description: "초보자용 개인 주식 관리 웹 MVP",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>
        <div className="appShell">
          <Sidebar />
          <main className="mainContent">
            <header className="topbar">
              <form action="/stocks" className="topbarSearch">
                <input
                  aria-label="종목 검색"
                  className="search"
                  name="q"
                  placeholder="기업명·티커·종목코드 검색"
                  type="search"
                />
                <button aria-label="검색" className="searchSubmit" type="submit">
                  <span aria-hidden="true" className="searchIcon" />
                </button>
              </form>
              <div className="topbarActions">
                <Suspense fallback={<span className="testBanner">API 확인 중</span>}>
                  <DataModeBadge />
                </Suspense>
                <Suspense fallback={<span className="accountLink">계정 확인 중</span>}>
                  <AccountStatus />
                </Suspense>
              </div>
            </header>
            {children}
          </main>
        </div>
        <MobileNav />
      </body>
    </html>
  );
}
