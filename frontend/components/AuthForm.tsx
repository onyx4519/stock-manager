"use client";

import Link from "next/link";
import { useActionState } from "react";
import type { AuthActionState } from "@/app/auth-actions";


function todayInKorea() {
  return new Intl.DateTimeFormat("en-CA", {
    day: "2-digit",
    month: "2-digit",
    timeZone: "Asia/Seoul",
    year: "numeric",
  }).format(new Date());
}

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
        <>
          <label>
            사용자명
            <input autoComplete="name" minLength={2} name="displayName" required />
          </label>
          <label>
            생년월일
            <input
              max={todayInKorea()}
              min="1900-01-01"
              name="birthDate"
              required
              type="date"
            />
          </label>
          <label>
            성별
            <select defaultValue="UNSPECIFIED" name="gender">
              <option value="UNSPECIFIED">선택 안함</option>
              <option value="MALE">남성</option>
              <option value="FEMALE">여성</option>
            </select>
          </label>
          <p className="profileDataNotice">
            생년월일과 성별은 계정 기본정보로만 저장됩니다.
          </p>
        </>
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
      {registering && (
        <div className="optionalConsent">
          <label className="consentOption">
            <input name="personalizationConsent" type="checkbox" />
            <span>
              <strong>[선택]</strong> 검색·조회·관심종목 기록을 활용한 맞춤형
              관심 종목 제공에 동의합니다.
            </span>
          </label>
          <details className="consentDetails">
            <summary>동의 내용 보기</summary>
            <ul>
              <li>목적: 사용자의 관심에 맞는 종목 탐색 정보 제공</li>
              <li>활용 기록: 검색어, 조회 종목, 관심종목 및 서비스 이용 기록</li>
              <li>보유·이용 기간: 동의 철회 또는 회원 탈퇴 시까지</li>
            </ul>
            <p>
              동의하지 않아도 회원가입과 기본 기능 이용이 가능하며, 본 동의는
              투자자문이나 매매 추천에 대한 동의가 아닙니다.
            </p>
          </details>
        </div>
      )}
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
