import type { Metadata } from "next";
import { Suspense } from "react";
import { DataModeBadge } from "@/components/DataModeBadge";
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
              <input aria-label="종목 검색" className="search" placeholder="기업명·티커·종목코드 검색" />
              <Suspense fallback={<span className="testBanner">API 확인 중</span>}>
                <DataModeBadge />
              </Suspense>
            </header>
            {children}
          </main>
        </div>
        <MobileNav />
      </body>
    </html>
  );
}
