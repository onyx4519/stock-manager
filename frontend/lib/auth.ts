import "server-only";

import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/api";


export async function requireCurrentUser() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  if (user.passwordChangeRequired) redirect("/change-password");
  return user;
}
