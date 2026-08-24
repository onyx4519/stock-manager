"use server";

import { revalidatePath } from "next/cache";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import {
  ApiError,
  changePassword,
  SESSION_COOKIE_NAME,
  updateNotificationPreference,
} from "@/lib/api";


export type NotificationPreferenceState = { message?: string; success?: boolean } | undefined;

export async function updateNotificationPreferenceAction(
  _state: NotificationPreferenceState,
  formData: FormData,
): Promise<NotificationPreferenceState> {
  const enabled = formData.get("serviceNotificationConsent") === "on";
  try {
    await updateNotificationPreference(enabled);
    revalidatePath("/");
    revalidatePath("/account");
    revalidatePath("/notifications");
    return {
      message: enabled ? "서비스 알림을 켰습니다." : "서비스 알림을 껐습니다.",
      success: true,
    };
  } catch (error) {
    return {
      message: error instanceof ApiError && error.status === 401
        ? "로그인 세션을 다시 확인해 주세요."
        : "알림 설정을 변경하지 못했습니다.",
      success: false,
    };
  }
}

export type PasswordChangeState = { message?: string } | undefined;

export async function changePasswordAction(
  _state: PasswordChangeState,
  formData: FormData,
): Promise<PasswordChangeState> {
  const currentPassword = String(formData.get("currentPassword") ?? "");
  const newPassword = String(formData.get("newPassword") ?? "");
  const confirmation = String(formData.get("newPasswordConfirmation") ?? "");
  if (newPassword !== confirmation) {
    return { message: "새 비밀번호가 서로 일치하지 않습니다." };
  }
  if (newPassword.length < 8) {
    return { message: "새 비밀번호는 8자 이상이어야 합니다." };
  }

  try {
    await changePassword({ currentPassword, newPassword });
  } catch (error) {
    if (error instanceof ApiError && error.status === 400) {
      return {
        message: error.message.includes("12")
          ? "관리자 비밀번호는 12자 이상이어야 합니다."
          : error.message.includes("different")
            ? "현재 비밀번호와 다른 비밀번호를 입력해 주세요."
            : "현재 비밀번호가 올바르지 않습니다.",
      };
    }
    return { message: "비밀번호를 변경하지 못했습니다." };
  }

  (await cookies()).delete(SESSION_COOKIE_NAME);
  redirect("/login?passwordChanged=1");
}
