import { DeleteAccountPanel } from "@/components/DeleteAccountPanel";
import { NotificationSettingsForm } from "@/components/NotificationSettingsForm";
import { PasswordChangePanel } from "@/components/PasswordChangePanel";
import { requireCurrentUser } from "@/lib/auth";


export const dynamic = "force-dynamic";

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
}

function genderLabel(value: "UNSPECIFIED" | "MALE" | "FEMALE") {
  if (value === "MALE") return "남성";
  if (value === "FEMALE") return "여성";
  return "선택 안함";
}

export default async function AccountPage() {
  const user = await requireCurrentUser();

  return (
    <div className="page accountPage">
      <header className="pageHeader">
        <div>
          <div className="eyebrow">My account</div>
          <h1>내 정보</h1>
          <p className="muted accountIntro">
            로그인한 계정의 기본 정보와 알림 설정을 관리합니다.
          </p>
        </div>
      </header>

      <section className="card accountDetailsCard">
        <h2>계정 정보</h2>
        <dl className="accountDetails">
          <div>
            <dt>사용자명</dt>
            <dd>{user.displayName}</dd>
          </div>
          <div>
            <dt>이메일</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>계정 유형</dt>
            <dd>{user.role === "ADMIN" ? "관리자" : "일반 사용자"}</dd>
          </div>
          <div>
            <dt>생년월일</dt>
            <dd>{user.birthDate ? formatDate(user.birthDate) : "기존 계정 정보 없음"}</dd>
          </div>
          <div>
            <dt>성별</dt>
            <dd>{genderLabel(user.gender)}</dd>
          </div>
          <div>
            <dt>가입일</dt>
            <dd>{formatDate(user.createdAt)}</dd>
          </div>
          <div>
            <dt>맞춤형 정보</dt>
            <dd>
              {user.personalizationConsent
                ? `선택 동의함 · ${formatDate(user.personalizationConsentAt ?? user.createdAt)}`
                : "선택 동의하지 않음"}
            </dd>
          </div>
        </dl>
        <PasswordChangePanel minimumLength={user.role === "ADMIN" ? 12 : 8} />
        <NotificationSettingsForm enabled={user.serviceNotificationConsent} />
        <DeleteAccountPanel userId={user.id} />
      </section>
    </div>
  );
}
