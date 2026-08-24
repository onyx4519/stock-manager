import { ApiMessage } from "@/components/ApiMessage";
import { PortfolioManager } from "@/components/PortfolioManager";
import {
  getPortfolioPositions,
  getPortfolioSummary,
  getQuotes,
  getTransactions,
} from "@/lib/api";

export default async function PortfolioPage() {
  try {
    const [positions, summary, transactions, quotes] = await Promise.all([
      getPortfolioPositions(),
      getPortfolioSummary(),
      getTransactions(),
      getQuotes(),
    ]);
    return (
      <PortfolioManager
        positions={positions}
        quotes={quotes}
        summary={summary}
        transactions={transactions}
      />
    );
  } catch (error) {
    return (
      <div className="page">
        <ApiMessage
          title="포트폴리오를 불러오지 못했습니다"
          message={error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."}
        />
      </div>
    );
  }
}
