import Link from "next/link";
import { logoutAction } from "@/app/auth-actions";
import { NotificationMenu } from "@/components/NotificationMenu";
import { getCurrentUser, getNotifications } from "@/lib/api";


export async function AccountStatus() {
  const user = await getCurrentUser().catch(() => null);
  if (!user) return <Link className="accountLink" href="/login">로그인</Link>;
  if (user.passwordChangeRequired) {
    return (
      <div className="accountStatus">
        <Link className="accountLink" href="/change-password">
          비밀번호 변경 필요
        </Link>
        <form action={logoutAction}>
          <button className="accountButton" type="submit">로그아웃</button>
        </form>
      </div>
    );
  }
  const notifications = await getNotifications().catch(() => ({ items: [], unreadCount: 0 }));
  return (
    <div className="accountStatus">
      <NotificationMenu
        notifications={notifications}
        showBadge={user.serviceNotificationConsent && notifications.unreadCount > 0}
      />
      {user.role === "ADMIN" && (
        <Link className="adminDashboardLink" href="/admin">
          관리자
        </Link>
      )}
      <Link className="accountNameLink" href="/account">
        {user.displayName}
      </Link>
      <form action={logoutAction}>
        <button className="accountButton" type="submit">로그아웃</button>
      </form>
    </div>
  );
}
