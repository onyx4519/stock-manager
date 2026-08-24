"use client";

import { type InputHTMLAttributes, useState } from "react";


type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type">;


export function PasswordInput(props: PasswordInputProps) {
  const [visible, setVisible] = useState(false);
  const label = visible ? "비밀번호 가리기" : "비밀번호 보기";

  return (
    <div className="passwordInputField">
      <input {...props} type={visible ? "text" : "password"} />
      <button
        aria-label={label}
        aria-pressed={visible}
        className="passwordVisibilityButton"
        onClick={() => setVisible((current) => !current)}
        title={label}
        type="button"
      >
        <span
          aria-hidden="true"
          className={`passwordEyeIcon${visible ? " passwordEyeIconOpen" : ""}`}
        />
      </button>
    </div>
  );
}
