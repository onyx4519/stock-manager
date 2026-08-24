import { loginAction } from "@/app/auth-actions";
import { AuthForm } from "@/components/AuthForm";


export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ passwordChanged?: string }>;
}) {
  const params = await searchParams;
  return (
    <div className="authPage">
      <div className="authIntro">
        <div className="eyebrow">Account</div>
        <h1>내 투자 기록에 로그인</h1>
        <p className="muted">거래 기록과 관심종목은 로그인한 계정별로 분리됩니다.</p>
      </div>
      {params.passwordChanged === "1" && (
        <p className="card authSuccessNotice" role="status">
          비밀번호가 변경되었습니다. 새 비밀번호로 다시 로그인해 주세요.
        </p>
      )}
      <AuthForm action={loginAction} mode="login" />
    </div>
  );
}
