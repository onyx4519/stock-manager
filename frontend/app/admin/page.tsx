import { getAdminDashboard, getHealth } from "@/lib/api";
import { requireAdmin } from "@/lib/auth";


export const dynamic = "force-dynamic";

const DELETION_REASON_LABELS = {
  MISSING_CONTENT: "원하는 정보 부족",
  DIFFICULT_TO_USE: "사용이 어려움",
  DATA_QUALITY: "데이터 품질",
  PRIVACY_CONCERN: "개인정보·보안",
  NO_LONGER_NEEDED: "사용 필요성 없음",
  NO_REASON: "사유 없음",
} as const;

function formatDate(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "Asia/Seoul",
  }).format(new Date(value));
}

function consentRate(count: number, total: number) {
  if (total === 0) return "0%";
  return `${Math.round((count / total) * 100)}%`;
}

export default async function AdminDashboardPage() {
  const admin = await requireAdmin();
  const [summary, health] = await Promise.all([
    getAdminDashboard(),
    getHealth().catch(() => null),
  ]);

  return (
    <div className="page adminDashboardPage">
      <header className="pageHeader">
        <div>
          <div className="eyebrow">Administrator</div>
          <h1>관리자 대시보드</h1>
          <p className="muted adminDashboardIntro">
            {admin.displayName} 관리자 계정으로 서비스 현황을 확인하고 있습니다.
          </p>
        </div>
        <span className="adminAccessBadge">관리자 전용</span>
      </header>

      <section className="adminMetricGrid" aria-label="서비스 주요 현황">
        <article className="card adminMetricCard">
          <span>전체 회원</span>
          <strong>{summary.totalUsers.toLocaleString("ko-KR")}</strong>
          <small>관리자 {summary.adminUsers} · 일반 {summary.regularUsers}</small>
        </article>
        <article className="card adminMetricCard">
          <span>활성 세션</span>
          <strong>{summary.activeSessions.toLocaleString("ko-KR")}</strong>
          <small>현재 만료되지 않은 로그인</small>
        </article>
        <article className="card adminMetricCard">
          <span>전체 거래 기록</span>
          <strong>{summary.totalTransactions.toLocaleString("ko-KR")}</strong>
          <small>회원 계정에 저장된 기록</small>
        </article>
        <article className="card adminMetricCard">
          <span>전체 관심종목</span>
          <strong>{summary.totalWatchlistItems.toLocaleString("ko-KR")}</strong>
          <small>모든 회원의 저장 항목</small>
        </article>
      </section>

      <section className="adminDashboardGrid">
        <article className="card adminOverviewCard">
          <div className="rowBetween gap">
            <div>
              <div className="eyebrow">Accounts</div>
              <h2>계정·동의 현황</h2>
            </div>
            <span className="countBadge">회원 {summary.totalUsers}</span>
          </div>
          <dl className="adminOverviewList">
            <div>
              <dt>서비스 알림 동의</dt>
              <dd>{summary.serviceNotificationUsers}명 · {consentRate(summary.serviceNotificationUsers, summary.totalUsers)}</dd>
            </div>
            <div>
              <dt>맞춤형 정보 동의</dt>
              <dd>{summary.personalizationUsers}명 · {consentRate(summary.personalizationUsers, summary.totalUsers)}</dd>
            </div>
            <div>
              <dt>비밀번호 변경 필요</dt>
              <dd className={summary.passwordChangeRequiredUsers > 0 ? "adminAttention" : undefined}>
                {summary.passwordChangeRequiredUsers}명
              </dd>
            </div>
            <div>
              <dt>등록된 알림</dt>
              <dd>{summary.totalNotifications.toLocaleString("ko-KR")}건</dd>
            </div>
          </dl>
        </article>

        <article className="card adminServiceCard">
          <div className="eyebrow">System</div>
          <h2>서비스 상태</h2>
          <div className="adminServiceStatus">
            <span className={health?.status === "ok" ? "adminStatusDot adminStatusOk" : "adminStatusDot"} />
            <strong>{health?.status === "ok" ? "정상 작동 중" : "상태 확인 필요"}</strong>
          </div>
          <dl className="adminServiceDetails">
            <div><dt>시장 데이터 공급자</dt><dd>{health?.market_provider ?? "확인 불가"}</dd></div>
            <div><dt>테스트 데이터 모드</dt><dd>{health?.mock_mode ? "사용 중" : "사용 안 함"}</dd></div>
            <div><dt>현황 생성 시각</dt><dd>{formatDate(summary.generatedAt)}</dd></div>
          </dl>
        </article>
      </section>

      <section className="adminDashboardGrid adminLowerGrid">
        <article className="card adminRecentUsersCard">
          <div className="eyebrow">Recent accounts</div>
          <h2>최근 가입 계정</h2>
          {summary.recentUsers.length > 0 ? (
            <div className="adminTableWrap">
              <table className="adminTable">
                <thead><tr><th>사용자</th><th>권한</th><th>가입일</th></tr></thead>
                <tbody>
                  {summary.recentUsers.map((user) => (
                    <tr key={user.id}>
                      <td><strong>{user.displayName}</strong><small>{user.email}</small></td>
                      <td><span className={`adminRole adminRole-${user.role.toLowerCase()}`}>{user.role === "ADMIN" ? "관리자" : "일반"}</span></td>
                      <td>{formatDate(user.createdAt)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <p className="muted">표시할 가입 계정이 없습니다.</p>}
        </article>

        <article className="card adminDeletionStatsCard">
          <div className="eyebrow">Feedback</div>
          <h2>회원 탈퇴 사유</h2>
          {summary.deletionReasons.length > 0 ? (
            <ul className="adminReasonList">
              {summary.deletionReasons.map((item) => (
                <li key={item.reason}>
                  <span>{DELETION_REASON_LABELS[item.reason]}</span>
                  <strong>{item.count}건</strong>
                </li>
              ))}
            </ul>
          ) : <p className="muted">수집된 탈퇴 사유가 없습니다.</p>}
        </article>
      </section>
    </div>
  );
}
