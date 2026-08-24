"use server";

import { revalidatePath } from "next/cache";
import { ApiError, updateNotificationPreference } from "@/lib/api";


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
