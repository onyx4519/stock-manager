import { registerAction } from "@/app/auth-actions";
import { AuthForm } from "@/components/AuthForm";


export default function RegisterPage() {
  return (
    <div className="authPage">
      <div className="authIntro">
        <div className="eyebrow">Create account</div>
        <h1>개인 계정 만들기</h1>
        <p className="muted">첫 번째 계정에는 기존 로컬 거래·관심종목 데이터가 자동 이전됩니다.</p>
      </div>
      <AuthForm action={registerAction} mode="register" />
    </div>
  );
}
