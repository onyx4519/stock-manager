import { DeleteAccountPanel } from "@/components/DeleteAccountPanel";
import { requireCurrentUser } from "@/lib/auth";


export const dynamic = "force-dynamic";

function formatJoinedAt(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(value));
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
            로그인한 계정의 기본 정보와 회원 탈퇴 기능을 관리합니다.
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
            <dt>가입일</dt>
            <dd>{formatJoinedAt(user.createdAt)}</dd>
          </div>
        </dl>
      </section>

      <DeleteAccountPanel userId={user.id} />
    </div>
  );
}
