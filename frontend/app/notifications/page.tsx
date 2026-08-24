import {
  markAllNotificationsReadAction,
  markNotificationReadAction,
} from "@/app/notifications/actions";
import { requireCurrentUser } from "@/lib/auth";
import { getNotifications } from "@/lib/api";
import type { NotificationCategory } from "@/types/market";


export const dynamic = "force-dynamic";

function categoryLabel(category: NotificationCategory) {
  if (category === "ACCOUNT") return "계정";
  if (category === "SERVICE") return "서비스";
  return "공지";
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Seoul",
  }).format(new Date(value));
}

export default async function NotificationsPage() {
  const user = await requireCurrentUser();
  const notifications = await getNotifications();

  return (
    <div className="page notificationPage">
      <header className="pageHeader">
        <div>
          <div className="eyebrow">Notifications</div>
          <h1>알림센터</h1>
          <p className="muted notificationIntro">
            {user.displayName}님의 서비스 공지와 계정 알림입니다.
          </p>
        </div>
        {notifications.unreadCount > 0 && (
          <form action={markAllNotificationsReadAction}>
            <button className="secondaryButton" type="submit">모두 읽음</button>
          </form>
        )}
      </header>

      {!user.serviceNotificationConsent && (
        <section className="card notificationPreferenceNotice">
          <strong>상단 미확인 알림 표시가 꺼져 있습니다.</strong>
          <p>알림 내용은 계속 보관되며 내 정보에서 표시 설정을 켤 수 있습니다.</p>
        </section>
      )}

      <section className="notificationList" aria-label="알림 목록">
        {notifications.items.length === 0 ? (
          <div className="card emptyState">현재 확인할 알림이 없습니다.</div>
        ) : notifications.items.map((item) => (
          <article
            className={`card notificationCard${item.readAt ? " notificationCardRead" : ""}`}
            key={item.id}
          >
            <div className="notificationCardHeader">
              <span className={`notificationCategory notificationCategory-${item.category.toLowerCase()}`}>
                {categoryLabel(item.category)}
              </span>
              <time dateTime={item.createdAt}>{formatDateTime(item.createdAt)}</time>
            </div>
            <h2>{item.title}</h2>
            <p>{item.message}</p>
            {!item.readAt && (
              <form action={markNotificationReadAction}>
                <input name="notificationId" type="hidden" value={item.id} />
                <button className="accountTextButton" type="submit">읽음으로 표시</button>
              </form>
            )}
          </article>
        ))}
      </section>
    </div>
  );
}
