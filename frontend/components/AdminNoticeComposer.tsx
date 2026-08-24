"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import {
  publishAdminNoticeAction,
  type AdminNoticeState,
} from "@/app/admin/actions";


function PublishButton() {
  const { pending } = useFormStatus();
  return (
    <button className="primaryButton" type="submit" disabled={pending}>
      {pending ? "발행 중..." : "공지 발행"}
    </button>
  );
}

export function AdminNoticeComposer() {
  const [state, action] = useActionState<AdminNoticeState, FormData>(
    publishAdminNoticeAction,
    undefined,
  );

  return (
    <form action={action} className="adminNoticeForm">
      <label>
        공지 제목
        <input name="title" minLength={2} maxLength={80} required placeholder="예: 서비스 점검 안내" />
      </label>
      <label>
        공지 내용
        <textarea name="message" minLength={2} maxLength={500} rows={5} required placeholder="사용자에게 전달할 내용을 입력해 주세요." />
      </label>
      <div className="adminNoticeFormFooter">
        <label>
          공개 대상
          <select name="audience" defaultValue="ALL">
            <option value="ALL">전체 회원</option>
            <option value="ADMIN">관리자만</option>
          </select>
        </label>
        <PublishButton />
      </div>
      {state?.message ? (
        <p className={state.success ? "formSuccessText" : "formMessageText"} aria-live="polite">
          {state.message}
        </p>
      ) : null}
    </form>
  );
}
