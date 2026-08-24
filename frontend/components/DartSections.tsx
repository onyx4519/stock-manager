import type {
  DartDisclosure,
  DartDisclosureList,
  DartFinancialAccount,
  DartFinancialStatement,
} from "@/types/market";


const keyAccountTerms = [
  "자산총계",
  "부채총계",
  "자본총계",
  "매출액",
  "영업이익",
  "당기순이익",
];


function selectKeyAccounts(accounts: DartFinancialAccount[]) {
  const selected = keyAccountTerms
    .map((term) => accounts.find((account) => account.accountName.includes(term)))
    .filter((account): account is DartFinancialAccount => account !== undefined);
  return selected.length > 0 ? selected : accounts.slice(0, 8);
}


function amount(value: number | null, currency: string | null) {
  if (value === null) return "-";
  return `${value.toLocaleString("ko-KR")} ${currency ?? ""}`.trim();
}


export function DartFinancialSection({
  data,
  error,
}: {
  data: DartFinancialStatement | null;
  error: string | null;
}) {
  return (
    <section>
      <div className="rowBetween gap sectionTitleRow">
        <h2>주요 재무계정</h2>
        {data && (
          <span className="sourceBadge">
            OpenDART · {data.businessYear} 사업보고서 · {data.financialStatementDivision === "CFS" ? "연결" : data.financialStatementDivision === "OFS" ? "별도" : "구분 없음"}
          </span>
        )}
      </div>
      {error ? (
        <div className="card emptyState">{error}</div>
      ) : !data || data.accounts.length === 0 ? (
        <div className="card emptyState">해당 사업연도의 주요 재무계정이 없습니다.</div>
      ) : (
        <div className="card financialTableWrap">
          <table className="financialTable">
            <thead>
              <tr>
                <th>계정</th>
                <th>{data.accounts[0].currentTermName ?? "당기"}</th>
                <th>{data.accounts[0].previousTermName ?? "전기"}</th>
              </tr>
            </thead>
            <tbody>
              {selectKeyAccounts(data.accounts).map((account) => (
                <tr key={`${account.statementDivision}-${account.accountName}`}>
                  <td>{account.accountName}</td>
                  <td>{amount(account.currentTermAmount ?? account.currentTermCumulativeAmount, account.currency)}</td>
                  <td>{amount(account.previousTermAmount, account.currency)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="dataNotice">공시 제출인이 작성한 XBRL 재무정보이며 정정 공시에 따라 변경될 수 있습니다.</p>
        </div>
      )}
    </section>
  );
}


export function DisclosureItems({ items }: { items: DartDisclosure[] }) {
  if (items.length === 0) {
    return <div className="card emptyState">조회 기간에 등록된 공시가 없습니다.</div>;
  }
  return (
    <div className="disclosureList">
      {items.map((item) => (
        <a
          className="card disclosureRow"
          href={item.viewerUrl}
          key={item.receiptNumber}
          rel="noreferrer"
          target="_blank"
        >
          <div>
            <strong>{item.reportName}</strong>
            <div className="meta">{item.corporationName} · 제출인 {item.filerName}</div>
          </div>
          <div className="disclosureMeta">
            <span>{new Date(`${item.receiptDate}T00:00:00+09:00`).toLocaleDateString("ko-KR")}</span>
            {item.remarks && <span className="sourceBadge">{item.remarks}</span>}
            <span className="externalMark">DART 원문</span>
          </div>
        </a>
      ))}
    </div>
  );
}


export function DartDisclosureSection({
  data,
  error,
}: {
  data: DartDisclosureList | null;
  error: string | null;
}) {
  return (
    <section>
      <div className="rowBetween gap sectionTitleRow">
        <h2>최근 공시</h2>
        {data && <span className="muted">최근 1년 {data.totalCount.toLocaleString("ko-KR")}건</span>}
      </div>
      {error ? <div className="card emptyState">{error}</div> : <DisclosureItems items={data?.items ?? []} />}
    </section>
  );
}
