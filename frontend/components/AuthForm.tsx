"use client";

import Link from "next/link";
import { useActionState } from "react";
import type { AuthActionState } from "@/app/auth-actions";


export function AuthForm({
  action,
  mode,
}: {
  action: (state: AuthActionState, formData: FormData) => Promise<AuthActionState>;
  mode: "login" | "register";
}) {
  const [state, formAction, pending] = useActionState(action, undefined);
  const registering = mode === "register";
  return (
    <form action={formAction} className="card authForm">
      {registering && (
        <label>
          사용자명
          <input autoComplete="name" minLength={2} name="displayName" required />
        </label>
      )}
      <label>
        이메일
        <input autoComplete="email" name="email" required type="email" />
      </label>
      <label>
        비밀번호
        <input
          autoComplete={registering ? "new-password" : "current-password"}
          minLength={8}
          name="password"
          required
          type="password"
        />
      </label>
      {state?.message && <p className="formMessageText" role="alert">{state.message}</p>}
      <button className="primaryButton" disabled={pending} type="submit">
        {pending ? "처리 중" : registering ? "계정 만들기" : "로그인"}
      </button>
      <p className="authSwitch">
        {registering ? "이미 계정이 있나요?" : "처음 사용하시나요?"}{" "}
        <Link className="inlineLink" href={registering ? "/login" : "/register"}>
          {registering ? "로그인" : "회원가입"}
        </Link>
      </p>
    </form>
  );
}
