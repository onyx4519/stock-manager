import { cookies } from "next/headers";
import {
  ApiError,
  deleteAccount,
  SESSION_COOKIE_NAME,
} from "@/lib/api";


const DELETION_REASONS = [
  "MISSING_CONTENT",
  "DIFFICULT_TO_USE",
  "DATA_QUALITY",
  "PRIVACY_CONCERN",
  "NO_LONGER_NEEDED",
] as const;

type DeletionReason = (typeof DELETION_REASONS)[number];

function isDeletionReason(value: unknown): value is DeletionReason {
  return typeof value === "string" && DELETION_REASONS.includes(value as DeletionReason);
}

export async function DELETE(request: Request) {
  let payload: { confirmed?: unknown; reason?: unknown };
  try {
    payload = (await request.json()) as { confirmed?: unknown; reason?: unknown };
  } catch {
    return Response.json({ message: "탈퇴 요청 형식이 올바르지 않습니다." }, { status: 400 });
  }

  if (payload.confirmed !== true || !isDeletionReason(payload.reason)) {
    return Response.json(
      { message: "탈퇴 동의와 탈퇴 사유 선택이 필요합니다." },
      { status: 400 },
    );
  }

  try {
    await deleteAccount({ confirmed: true, reason: payload.reason });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) {
      (await cookies()).delete(SESSION_COOKIE_NAME);
      return Response.json(
        { message: "로그인 정보가 만료되었습니다. 다시 로그인해 주세요." },
        { status: 401 },
      );
    }
    return Response.json(
      { message: "회원 탈퇴를 처리하지 못했습니다. 잠시 후 다시 시도해 주세요." },
      { status: 502 },
    );
  }

  (await cookies()).delete(SESSION_COOKIE_NAME);
  return new Response(null, { status: 204 });
}
