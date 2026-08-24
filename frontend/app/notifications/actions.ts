"use server";

import { revalidatePath } from "next/cache";
import { markAllNotificationsRead, markNotificationRead } from "@/lib/api";


export async function markNotificationReadAction(formData: FormData): Promise<void> {
  const id = Number(formData.get("notificationId"));
  if (!Number.isSafeInteger(id) || id < 1) return;
  await markNotificationRead(id);
  revalidatePath("/");
  revalidatePath("/notifications");
}

export async function markAllNotificationsReadAction(): Promise<void> {
  await markAllNotificationsRead();
  revalidatePath("/");
  revalidatePath("/notifications");
}
