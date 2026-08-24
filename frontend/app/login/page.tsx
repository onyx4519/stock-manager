import { loginAction } from "@/app/auth-actions";
import { AuthForm } from "@/components/AuthForm";


export default function LoginPage() {
  return (
    <div className="authPage">
      <div className="authIntro">
        <div className="eyebrow">Account</div>
        <h1>내 투자 기록에 로그인</h1>
        <p className="muted">거래 기록과 관심종목은 로그인한 계정별로 분리됩니다.</p>
      </div>
      <AuthForm action={loginAction} mode="login" />
    </div>
  );
}
