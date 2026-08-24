import Link from "next/link";
import { logoutAction } from "@/app/auth-actions";
import { getCurrentUser, getNotifications } from "@/lib/api";


export async function AccountStatus() {
  const user = await getCurrentUser().catch(() => null);
  if (!user) return <Link className="accountLink" href="/login">로그인</Link>;
  const notifications = await getNotifications().catch(() => ({ items: [], unreadCount: 0 }));
  return (
    <div className="accountStatus">
      <Link
        aria-label={user.serviceNotificationConsent && notifications.unreadCount > 0
          ? `알림센터, 읽지 않은 알림 ${notifications.unreadCount}개`
          : "알림센터"}
        className="notificationLink"
        href="/notifications"
      >
        <svg aria-hidden="true" viewBox="0 0 24 24">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4" />
        </svg>
        {user.serviceNotificationConsent && notifications.unreadCount > 0 && (
          <span className="notificationCount">
            {notifications.unreadCount > 99 ? "99+" : notifications.unreadCount}
          </span>
        )}
      </Link>
      <Link className="accountNameLink" href="/account">
        {user.displayName}
      </Link>
      <form action={logoutAction}>
        <button className="accountButton" type="submit">로그아웃</button>
      </form>
    </div>
  );
}
