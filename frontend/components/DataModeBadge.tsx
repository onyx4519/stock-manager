import { getHealth } from "@/lib/api";

export async function DataModeBadge() {
  const health = await getHealth().catch(() => null);
  const modeLabel = health
    ? health.mock_mode
      ? "MOCK DATA MODE"
      : `${health.market_provider.toUpperCase()} · EOD DATA`
    : "API OFFLINE";

  return (
    <span className={`testBanner ${health?.mock_mode === false ? "liveBanner" : ""}`}>
      {modeLabel}
    </span>
  );
}
