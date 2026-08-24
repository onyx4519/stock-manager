"use client";

import { useState } from "react";


const DELETION_REASONS = [
  { value: "MISSING_CONTENT", label: "원하는 종목·정보가 부족해요" },
  { value: "DIFFICULT_TO_USE", label: "사용 방법이 어렵거나 불편해요" },
  { value: "DATA_QUALITY", label: "데이터 정확도·속도가 아쉬워요" },
  { value: "PRIVACY_CONCERN", label: "개인정보·보안 안내가 부족해요" },
  { value: "NO_LONGER_NEEDED", label: "계속 사용할 필요성을 느끼지 못했어요" },
] as const;

type DeletionReason = (typeof DELETION_REASONS)[number]["value"];
type DeletionStep = "idle" | "confirm" | "reason";


export function DeleteAccountPanel({ userId }: { userId: string }) {
  const [step, setStep] = useState<DeletionStep>("idle");
  const [reason, setReason] = useState<DeletionReason | "">("");
  const [pending, setPending] = useState(false);
  const [message, setMessage] = useState<string>();

  const cancel = () => {
    setStep("idle");
    setReason("");
    setMessage(undefined);
  };

  const submitDeletion = async () => {
    if (!reason || pending) return;
    setPending(true);
    setMessage(undefined);
    try {
      const response = await fetch("/api/account", {
        method: "DELETE",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ confirmed: true, reason }),
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as
          | { message?: unknown }
          | null;
        throw new Error(
          typeof payload?.message === "string"
            ? payload.message
            : "회원 탈퇴를 처리하지 못했습니다.",
        );
      }

      try {
        window.localStorage.removeItem(`stock-manager:recent-stocks:${userId}`);
      } catch {
        // Account deletion remains successful when device storage is unavailable.
      }
      window.location.assign("/login");
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "회원 탈퇴를 처리하지 못했습니다.",
      );
      setPending(false);
    }
  };

  const expanded = step !== "idle";

  return (
    <section
      className={expanded
        ? "accountDeletionArea accountDeletionExpanded"
        : "accountDeletionArea"}
    >
      {step === "idle" && (
        <button
          className="accountDeleteLink"
          onClick={() => setStep("confirm")}
          type="button"
        >
          회원 탈퇴
        </button>
      )}

      {expanded && (
        <div className="accountDeletionHeading">
          <h2>회원 탈퇴</h2>
          <p className="muted">
            계정과 저장된 거래·관심종목 데이터가 삭제되며 복구할 수 없습니다.
          </p>
        </div>
      )}

      {step === "confirm" && (
        <div className="deletionStep" role="alert">
          <strong>정말 회원 탈퇴에 동의하시나요?</strong>
          <p>탈퇴를 계속하면 다음 단계에서 서비스의 부족했던 점을 선택합니다.</p>
          <div className="deletionActions">
            <button className="accountTextButton" onClick={cancel} type="button">
              취소
            </button>
            <button
              className="accountTextButton accountTextDanger"
              onClick={() => setStep("reason")}
              type="button"
            >
              동의하고 계속
            </button>
          </div>
        </div>
      )}

      {step === "reason" && (
        <div className="deletionStep">
          <fieldset className="deletionReasons">
            <legend>가장 부족했던 점 한 가지를 선택해 주세요.</legend>
            {DELETION_REASONS.map((item) => (
              <label className="deletionReason" key={item.value}>
                <input
                  checked={reason === item.value}
                  name="deletionReason"
                  onChange={() => setReason(item.value)}
                  type="radio"
                  value={item.value}
                />
                <span>{item.label}</span>
              </label>
            ))}
          </fieldset>
          <p className="dataNotice">
            선택한 사유는 계정 정보와 연결하지 않고 익명 통계로만 저장됩니다.
          </p>
          {message && <p className="formMessageText" role="alert">{message}</p>}
          <div className="deletionActions">
            <button
              className="accountTextButton"
              disabled={pending}
              onClick={cancel}
              type="button"
            >
              취소
            </button>
            <button
              className="accountTextButton accountTextDanger"
              disabled={!reason || pending}
              onClick={submitDeletion}
              type="button"
            >
              {pending ? "탈퇴 처리 중" : "사유 제출 후 계정 삭제"}
            </button>
          </div>
        </div>
      )}
    </section>
  );
}
