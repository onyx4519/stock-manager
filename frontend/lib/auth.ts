import "server-only";

import { redirect } from "next/navigation";
import { getCurrentUser } from "@/lib/api";


export async function requireCurrentUser() {
  const user = await getCurrentUser();
  if (!user) redirect("/login");
  return user;
}
