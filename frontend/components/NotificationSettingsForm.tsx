"use client";

import { useActionState, useState } from "react";
import {
  type NotificationPreferenceState,
  updateNotificationPreferenceAction,
} from "@/app/account/actions";


export function NotificationSettingsForm({ enabled }: { enabled: boolean }) {
  const [checked, setChecked] = useState(enabled);
  const [state, action, pending] = useActionState<
    NotificationPreferenceState,
    FormData
  >(updateNotificationPreferenceAction, undefined);

  return (
    <form action={action} className="card notificationSettingsCard">
      <div>
        <h2>서비스 알림</h2>
        <p className="muted">
          켜면 읽지 않은 공지와 계정 알림 수를 상단에 표시합니다.
          꺼도 알림센터에서 직접 확인할 수 있습니다.
        </p>
      </div>
      <label className="notificationSettingToggle">
        <input
          checked={checked}
          name="serviceNotificationConsent"
          onChange={(event) => setChecked(event.target.checked)}
          type="checkbox"
        />
        <span>{checked ? "알림 켜짐" : "알림 꺼짐"}</span>
      </label>
      <div className="notificationSettingActions">
        {state?.message && (
          <p className={state.success ? "formSuccessText" : "formMessageText"} role="status">
            {state.message}
          </p>
        )}
        <button className="primaryButton" disabled={pending} type="submit">
          {pending ? "저장 중" : "설정 저장"}
        </button>
      </div>
    </form>
  );
}
