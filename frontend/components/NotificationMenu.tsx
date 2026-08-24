"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import type { NotificationList } from "@/types/market";


function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Asia/Seoul",
  }).format(new Date(value));
}

export function NotificationMenu({
  notifications,
  showBadge,
}: {
  notifications: NotificationList;
  showBadge: boolean;
}) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const closeFromOutside = (event: PointerEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeFromEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };

    document.addEventListener("pointerdown", closeFromOutside);
    document.addEventListener("keydown", closeFromEscape);
    return () => {
      document.removeEventListener("pointerdown", closeFromOutside);
      document.removeEventListener("keydown", closeFromEscape);
    };
  }, [open]);

  return (
    <div className="notificationMenu" ref={menuRef}>
      <button
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-label={showBadge
          ? `알림센터, 읽지 않은 알림 ${notifications.unreadCount}개`
          : "알림센터"}
        className="notificationLink"
        onClick={() => setOpen((current) => !current)}
        type="button"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
        </svg>
        {showBadge && (
          <span className="notificationCount">
            {notifications.unreadCount > 99 ? "99+" : notifications.unreadCount}
          </span>
        )}
      </button>

      {open && (
        <section aria-label="알림센터 미리보기" className="notificationPopover">
          <header className="notificationPopoverHeader">
            <strong>알림센터</strong>
            <Link href="/notifications" onClick={() => setOpen(false)}>
              전체 보기
            </Link>
          </header>
          <div className="notificationPreviewList">
            {notifications.items.length === 0 ? (
              <p className="notificationPreviewEmpty">현재 확인할 알림이 없습니다.</p>
            ) : notifications.items.slice(0, 4).map((item) => (
              <article
                className={`notificationPreviewItem${item.readAt ? " notificationPreviewItemRead" : ""}`}
                key={item.id}
              >
                <div>
                  {!item.readAt && <span aria-label="읽지 않음" className="notificationUnreadDot" />}
                  <strong>{item.title}</strong>
                </div>
                <p>{item.message}</p>
                <time dateTime={item.createdAt}>{formatDateTime(item.createdAt)}</time>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
