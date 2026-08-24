"use server";

import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import {
  ApiError,
  loginUser,
  logoutUser,
  registerUser,
  SESSION_COOKIE_NAME,
} from "@/lib/api";


export type AuthActionState = { message?: string } | undefined;

const cookieOptions = {
  httpOnly: true,
  maxAge: 60 * 60 * 24 * 30,
  path: "/",
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
};

function credentials(formData: FormData) {
  return {
    email: String(formData.get("email") ?? "").trim(),
    password: String(formData.get("password") ?? ""),
  };
}

export async function loginAction(
  _state: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  try {
    const session = await loginUser(credentials(formData));
    (await cookies()).set(SESSION_COOKIE_NAME, session.accessToken, cookieOptions);
  } catch (error) {
    return {
      message: error instanceof ApiError && error.status === 401
        ? "이메일 또는 비밀번호가 올바르지 않습니다."
        : "로그인 요청을 처리하지 못했습니다.",
    };
  }
  redirect("/");
}

export async function registerAction(
  _state: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const password = String(formData.get("password") ?? "");
  if (password.length < 8) return { message: "비밀번호는 8자 이상이어야 합니다." };
  try {
    const session = await registerUser({
      ...credentials(formData),
      display_name: String(formData.get("displayName") ?? "").trim(),
      personalization_consent: formData.get("personalizationConsent") === "on",
    });
    (await cookies()).set(SESSION_COOKIE_NAME, session.accessToken, cookieOptions);
  } catch (error) {
    return {
      message: error instanceof ApiError && error.status === 409
        ? "이미 등록된 이메일입니다."
        : "회원가입 요청을 처리하지 못했습니다.",
    };
  }
  redirect("/");
}

export async function logoutAction(): Promise<void> {
  try {
    await logoutUser();
  } catch {
    // Expire the browser session even if the backend session already expired.
  }
  (await cookies()).delete(SESSION_COOKIE_NAME);
  redirect("/login");
}
