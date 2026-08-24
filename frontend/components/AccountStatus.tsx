import Link from "next/link";
import { logoutAction } from "@/app/auth-actions";
import { getCurrentUser } from "@/lib/api";


export async function AccountStatus() {
  const user = await getCurrentUser().catch(() => null);
  if (!user) return <Link className="accountLink" href="/login">로그인</Link>;
  return (
    <div className="accountStatus">
      <span>{user.displayName}</span>
      <form action={logoutAction}>
        <button className="accountButton" type="submit">로그아웃</button>
      </form>
    </div>
  );
}
