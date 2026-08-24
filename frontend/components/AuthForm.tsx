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
        <>
          <label>
            사용자명
            <input autoComplete="name" minLength={2} name="displayName" required />
          </label>
          <fieldset className="birthDateField">
            <legend>생년월일</legend>
            <div className="birthDateInputs">
              <label>
                <span>연도</span>
                <input
                  autoComplete="bday-year"
                  inputMode="numeric"
                  maxLength={4}
                  name="birthYear"
                  pattern="[0-9]{4}"
                  placeholder="YYYY"
                  required
                  type="text"
                />
              </label>
              <label>
                <span>월</span>
                <select
                  autoComplete="bday-month"
                  defaultValue=""
                  name="birthMonth"
                  required
                >
                  <option disabled value="">MM</option>
                  {Array.from({ length: 12 }, (_, index) => index + 1).map((month) => (
                    <option key={month} value={month}>{month}월</option>
                  ))}
                </select>
              </label>
              <label>
                <span>일</span>
                <input
                  autoComplete="bday-day"
                  inputMode="numeric"
                  maxLength={2}
                  name="birthDay"
                  pattern="[0-9]{1,2}"
                  placeholder="DD"
                  required
                  type="text"
                />
              </label>
            </div>
          </fieldset>
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
        <div className="requiredConsent">
          <label className="consentOption">
            <input name="accountCreationConsent" required type="checkbox" />
            <span>
              <strong>[필수]</strong> 계정 생성 및 서비스 이용에 동의합니다.
            </span>
          </label>
          <details className="consentDetails">
            <summary>필수 동의 내용 보기</summary>
            <ul>
              <li>목적: 회원 계정 생성 및 로그인·회원 서비스 제공</li>
              <li>처리 정보: 이메일, 사용자명, 생년월일, 성별 및 암호화된 인증정보</li>
              <li>보유·이용 기간: 회원 탈퇴 시까지</li>
            </ul>
            <p>동의하지 않으면 계정을 생성할 수 없습니다.</p>
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
