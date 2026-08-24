"use client";

import Link from "next/link";
import {
  type FormEvent,
  type MouseEvent,
  useActionState,
  useEffect,
  useRef,
  useState,
} from "react";
import type { AuthActionState } from "@/app/auth-actions";


export function AuthForm({
  action,
  mode,
}: {
  action: (state: AuthActionState, formData: FormData) => Promise<AuthActionState>;
  mode: "login" | "register";
}) {
  const [state, formAction, pending] = useActionState(action, undefined);
  const formRef = useRef<HTMLFormElement>(null);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [consentModalOpen, setConsentModalOpen] = useState(false);
  const [accountCreationConsent, setAccountCreationConsent] = useState(false);
  const [privacyCollectionConsent, setPrivacyCollectionConsent] = useState(false);
  const [personalizationConsent, setPersonalizationConsent] = useState(false);
  const [serviceNotificationConsent, setServiceNotificationConsent] = useState(false);
  const registering = mode === "register";

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (consentModalOpen && !dialog.open) dialog.showModal();
    if (!consentModalOpen && dialog.open) dialog.close();
  }, [consentModalOpen]);

  const openConsentModal = () => {
    if (!formRef.current?.reportValidity()) return;
    setConsentModalOpen(true);
  };

  const closeConsentModal = () => {
    if (pending) return;
    setConsentModalOpen(false);
    setAccountCreationConsent(false);
    setPrivacyCollectionConsent(false);
    setPersonalizationConsent(false);
    setServiceNotificationConsent(false);
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    if (!registering) return;
    if (!consentModalOpen) {
      event.preventDefault();
      openConsentModal();
      return;
    }
    if (!accountCreationConsent || !privacyCollectionConsent) event.preventDefault();
  };

  const closeFromBackdrop = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === event.currentTarget) closeConsentModal();
  };

  return (
    <form
      action={formAction}
      className="card authForm"
      onSubmit={handleSubmit}
      ref={formRef}
    >
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
      {state?.message && (!registering || !consentModalOpen) && (
        <p className="formMessageText" role="alert">{state.message}</p>
      )}
      <button
        className="primaryButton"
        disabled={pending}
        onClick={registering ? openConsentModal : undefined}
        type={registering ? "button" : "submit"}
      >
        {pending ? "처리 중" : registering ? "계정 만들기" : "로그인"}
      </button>
      <p className="authSwitch">
        {registering ? "이미 계정이 있나요?" : "처음 사용하시나요?"}{" "}
        <Link className="inlineLink" href={registering ? "/login" : "/register"}>
          {registering ? "로그인" : "회원가입"}
        </Link>
      </p>

      {registering && (
        <dialog
          aria-labelledby="account-consent-title"
          className="accountConsentModal"
          onCancel={(event) => {
            event.preventDefault();
            closeConsentModal();
          }}
          onClick={closeFromBackdrop}
          ref={dialogRef}
        >
          <div className="accountConsentHeading">
            <h2 id="account-consent-title">가입 동의</h2>
            <p className="muted">
              필수 동의와 선택 동의를 확인한 후 계정을 생성해 주세요.
            </p>
          </div>

          <div className="accountConsentList">
            <section className="accountConsentSection">
              <label className="consentOption">
                <input
                  checked={accountCreationConsent}
                  name="accountCreationConsent"
                  onChange={(event) => setAccountCreationConsent(event.target.checked)}
                  type="checkbox"
                />
                <span>
                  <strong>[필수]</strong> 서비스 이용약관에 동의합니다.
                </span>
              </label>
              <div className="consentDetails">
                <ul>
                  <li>서비스는 주식 정보 탐색과 개인 포트폴리오 관리 기능을 제공합니다.</li>
                  <li>표시되는 정보는 투자 권유가 아니며 최종 판단과 책임은 사용자에게 있습니다.</li>
                  <li>사용자는 타인의 계정을 침해하거나 서비스를 부정하게 이용해서는 안 됩니다.</li>
                </ul>
                <p><Link className="inlineLink" href="/terms" target="_blank">서비스 이용약관 전체 보기</Link></p>
              </div>
            </section>

            <section className="accountConsentSection">
              <label className="consentOption">
                <input
                  checked={privacyCollectionConsent}
                  name="privacyCollectionConsent"
                  onChange={(event) => setPrivacyCollectionConsent(event.target.checked)}
                  type="checkbox"
                />
                <span>
                  <strong>[필수]</strong> 개인정보 수집·이용에 동의합니다.
                </span>
              </label>
              <div className="consentDetails">
                <ul>
                  <li>목적: 계정 생성, 로그인, 본인 식별 및 회원 서비스 제공</li>
                  <li>항목: 이메일, 사용자명, 생년월일, 성별, 암호화된 인증정보</li>
                  <li>보유 기간: 회원 탈퇴 시까지 또는 관계 법령상 보존 기간</li>
                </ul>
                <p>동의하지 않으면 계정을 생성할 수 없습니다. <Link className="inlineLink" href="/privacy" target="_blank">개인정보 처리방침 보기</Link></p>
              </div>
            </section>

            <section className="accountConsentSection">
              <label className="consentOption">
                <input
                  checked={serviceNotificationConsent}
                  name="serviceNotificationConsent"
                  onChange={(event) => setServiceNotificationConsent(event.target.checked)}
                  type="checkbox"
                />
                <span>
                  <strong>[선택]</strong> 서비스 알림 수신에 동의합니다.
                </span>
              </label>
              <div className="consentDetails">
                <ul>
                  <li>목적: 서비스 공지와 계정 관련 알림의 미확인 표시 제공</li>
                  <li>적용 범위: 현재 앱 내부 알림 배지 및 향후 별도 안내되는 알림 기능</li>
                  <li>보유 기간: 동의 철회 또는 회원 탈퇴 시까지</li>
                </ul>
                <p>동의하지 않아도 알림센터에서 공지를 직접 확인할 수 있습니다.</p>
              </div>
            </section>

            <section className="accountConsentSection">
              <label className="consentOption">
                <input
                  checked={personalizationConsent}
                  name="personalizationConsent"
                  onChange={(event) => setPersonalizationConsent(event.target.checked)}
                  type="checkbox"
                />
                <span>
                  <strong>[선택]</strong> 이용 기록을 활용한 맞춤형 관심 종목 제공에
                  동의합니다.
                </span>
              </label>
              <div className="consentDetails">
                <ul>
                  <li>목적: 사용자의 관심에 맞는 종목 탐색 정보 제공</li>
                  <li>활용 기록: 검색어, 조회 종목, 관심종목 및 서비스 이용 기록</li>
                  <li>보유·이용 기간: 동의 철회 또는 회원 탈퇴 시까지</li>
                </ul>
                <p>동의하지 않아도 계정 생성과 기본 기능 이용이 가능합니다.</p>
              </div>
            </section>
          </div>

          <div className="accountConsentActions">
            {state?.message && (
              <p className="formMessageText accountConsentMessage" role="alert">
                {state.message}
              </p>
            )}
            <button
              className="accountTextButton"
              disabled={pending}
              onClick={closeConsentModal}
              type="button"
            >
              취소
            </button>
            <button
              className="primaryButton"
              disabled={!accountCreationConsent || !privacyCollectionConsent || pending}
              type="submit"
            >
              {pending ? "처리 중" : "동의하고 계정 만들기"}
            </button>
          </div>
        </dialog>
      )}
    </form>
  );
}
