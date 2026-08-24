import Link from "next/link";
import { logoutAction } from "@/app/auth-actions";
import { NotificationMenu } from "@/components/NotificationMenu";
import { getCurrentUser, getNotifications } from "@/lib/api";


export async function AccountStatus() {
  const user = await getCurrentUser().catch(() => null);
  if (!user) return <Link className="accountLink" href="/login">로그인</Link>;
  const notifications = await getNotifications().catch(() => ({ items: [], unreadCount: 0 }));
  return (
    <div className="accountStatus">
      <NotificationMenu
        notifications={notifications}
        showBadge={user.serviceNotificationConsent && notifications.unreadCount > 0}
      />
      <Link className="accountNameLink" href="/account">
        {user.displayName}
      </Link>
      <form action={logoutAction}>
        <button className="accountButton" type="submit">로그아웃</button>
      </form>
    </div>
  );
}
