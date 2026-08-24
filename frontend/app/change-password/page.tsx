import { redirect } from "next/navigation";
import { PasswordChangeForm } from "@/components/PasswordChangePanel";
import { getCurrentUser } from "@/lib/api";


export const dynamic = "force-dynamic";


export default async function ForcedPasswordChangePage() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (!user.passwordChangeRequired) redirect("/account");

  return (
    <div className="page forcedPasswordPage">
      <section className="card forcedPasswordCard">
        <div>
          <div className="eyebrow">Security</div>
          <h1>비밀번호 변경이 필요합니다</h1>
          <p className="muted">
            비밀번호 입력을 연속 5회 실패하여 계정 보호를 위해 변경이 필요합니다.
          </p>
        </div>
        <p className="forcedPasswordNotice">
          비밀번호를 변경하기 전까지 관심종목, 포트폴리오 및 알림센터 등 개인 기능을 이용할 수 없습니다.
        </p>
        <PasswordChangeForm minimumLength={user.role === "ADMIN" ? 12 : 8} />
      </section>
    </div>
  );
}
