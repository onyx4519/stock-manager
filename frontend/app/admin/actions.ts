"use server";

import { revalidatePath } from "next/cache";
import {
  ApiError,
  createAdminNotice,
  requireUserPasswordChange,
  revokeUserSessions,
} from "@/lib/api";
import { requireAdmin } from "@/lib/auth";


export type AdminNoticeState =
  | { message: string; success: boolean }
  | undefined;

export async function publishAdminNoticeAction(
  _state: AdminNoticeState,
  formData: FormData,
): Promise<AdminNoticeState> {
  await requireAdmin();
  const title = String(formData.get("title") ?? "").trim();
  const message = String(formData.get("message") ?? "").trim();
  const audience = formData.get("audience") === "ADMIN" ? "ADMIN" : "ALL";

  if (title.length < 2 || title.length > 80) {
    return { message: "제목은 2~80자로 입력해 주세요.", success: false };
  }
  if (message.length < 2 || message.length > 500) {
    return { message: "공지 내용은 2~500자로 입력해 주세요.", success: false };
  }

  try {
    await createAdminNotice({ title, message, audience });
    revalidatePath("/");
    revalidatePath("/admin");
    revalidatePath("/notifications");
    return { message: "공지를 발행했습니다.", success: true };
  } catch (error) {
    return {
      message: error instanceof ApiError ? error.message : "공지를 발행하지 못했습니다.",
      success: false,
    };
  }
}

function getUserId(formData: FormData): string | null {
  const userId = String(formData.get("userId") ?? "").trim();
  return userId.length > 0 && userId.length <= 64 ? userId : null;
}

export async function requirePasswordChangeAction(formData: FormData): Promise<void> {
  await requireAdmin();
  const userId = getUserId(formData);
  if (!userId) return;
  await requireUserPasswordChange(userId);
  revalidatePath("/admin");
}

export async function revokeSessionsAction(formData: FormData): Promise<void> {
  await requireAdmin();
  const userId = getUserId(formData);
  if (!userId) return;
  await revokeUserSessions(userId);
  revalidatePath("/admin");
}
