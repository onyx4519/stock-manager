"use client";

import { useEffect, useState } from "react";


type ThemeMode = "light" | "dark" | "system";

const STORAGE_KEY = "stock_manager_theme";
const MODES: { label: string; value: ThemeMode }[] = [
  { label: "화이트 모드", value: "light" },
  { label: "블랙 모드", value: "dark" },
  { label: "시스템 기준", value: "system" },
];

function isThemeMode(value: string | null): value is ThemeMode {
  return value === "light" || value === "dark" || value === "system";
}

function applyTheme(mode: ThemeMode) {
  document.documentElement.dataset.theme = mode;
  localStorage.setItem(STORAGE_KEY, mode);
}

export function ThemeModeSelector() {
  const [mode, setMode] = useState<ThemeMode>("dark");

  useEffect(() => {
    const savedMode = localStorage.getItem(STORAGE_KEY);
    const initialMode = isThemeMode(savedMode) ? savedMode : "dark";
    setMode(initialMode);
    applyTheme(initialMode);
  }, []);

  const selectMode = (nextMode: ThemeMode) => {
    setMode(nextMode);
    applyTheme(nextMode);
  };

  return (
    <section className="themeSettingsCard">
      <div>
        <h2>화면 모드</h2>
        <p className="muted">
          선택한 화면 색상은 이 브라우저에 자동 저장됩니다.
        </p>
      </div>
      <div aria-label="화면 모드 선택" className="themeModeOptions" role="group">
        {MODES.map((item) => (
          <button
            aria-pressed={mode === item.value}
            className="themeModeButton"
            key={item.value}
            onClick={() => selectMode(item.value)}
            type="button"
          >
            {item.label}
          </button>
        ))}
      </div>
    </section>
  );
}
