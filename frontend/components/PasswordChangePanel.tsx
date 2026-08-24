"use client";

import {
  type MouseEvent,
  useActionState,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  changePasswordAction,
  type PasswordChangeState,
} from "@/app/account/actions";


export function PasswordChangeForm({
  minimumLength,
  onCancel,
}: {
  minimumLength: number;
  onCancel?: () => void;
}) {
  const [state, action, pending] = useActionState<PasswordChangeState, FormData>(
    changePasswordAction,
    undefined,
  );

  return (
    <form action={action} className="passwordChangeForm">
      <label>
        현재 비밀번호
        <input autoComplete="current-password" name="currentPassword" required type="password" />
      </label>
      <label>
        새 비밀번호
        <input autoComplete="new-password" minLength={minimumLength} name="newPassword" required type="password" />
      </label>
      <label>
        새 비밀번호 확인
        <input autoComplete="new-password" minLength={minimumLength} name="newPasswordConfirmation" required type="password" />
      </label>
      <p className="dataNotice">새 비밀번호는 {minimumLength}자 이상이어야 합니다.</p>
      {state?.message && <p className="formMessageText" role="alert">{state.message}</p>}
      <div className="deletionActions">
        {onCancel && (
          <button className="accountTextButton" disabled={pending} onClick={onCancel} type="button">
            취소
          </button>
        )}
        <button className="primaryButton" disabled={pending} type="submit">
          {pending ? "변경 중" : "비밀번호 변경"}
        </button>
      </div>
    </form>
  );
}


export function PasswordChangePanel({ minimumLength }: { minimumLength: number }) {
  const [open, setOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  const close = () => {
    setOpen(false);
  };

  const closeFromBackdrop = (event: MouseEvent<HTMLDialogElement>) => {
    if (event.target === event.currentTarget) close();
  };

  return (
    <>
      <section className="passwordChangeArea">
        <button className="accountTextButton" onClick={() => setOpen(true)} type="button">
          비밀번호 변경
        </button>
      </section>
      <dialog
        aria-labelledby="password-change-title"
        className="passwordChangeModal"
        onCancel={(event) => {
          event.preventDefault();
          close();
        }}
        onClick={closeFromBackdrop}
        ref={dialogRef}
      >
        <div className="accountDeletionHeading">
          <h2 id="password-change-title">비밀번호 변경</h2>
          <p className="muted">
            변경 후 모든 기기에서 로그아웃되며 새 비밀번호로 다시 로그인해야 합니다.
          </p>
        </div>
        <PasswordChangeForm minimumLength={minimumLength} onCancel={close} />
      </dialog>
    </>
  );
}
