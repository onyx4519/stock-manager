"use client";

import { useFormStatus } from "react-dom";
import { deleteAdminNoticeAction } from "@/app/admin/actions";


function DeleteButton() {
  const { pending } = useFormStatus();
  return (
    <button type="submit" className="adminNoticeDeleteButton" disabled={pending}>
      {pending ? "삭제 중..." : "삭제"}
    </button>
  );
}

export function AdminNoticeDeleteButton({
  noticeId,
  noticeTitle,
}: {
  noticeId: number;
  noticeTitle: string;
}) {
  return (
    <form
      action={deleteAdminNoticeAction}
      onSubmit={(event) => {
        if (!window.confirm(`'${noticeTitle}' 공지를 삭제하시겠습니까?`)) {
          event.preventDefault();
        }
      }}
    >
      <input type="hidden" name="noticeId" value={noticeId} />
      <DeleteButton />
    </form>
  );
}
