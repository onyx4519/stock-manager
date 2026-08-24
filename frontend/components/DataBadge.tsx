import type { DataStatus } from "@/types/market";

export function DataBadge({ status }: { status: DataStatus }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status}</span>;
}
