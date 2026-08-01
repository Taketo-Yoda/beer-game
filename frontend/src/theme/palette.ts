import { useEffect, useState } from "react";
import type { Role } from "../types";

// カテゴリカル配色（datavizスキルの検証済みパレットの先頭4色を固定順で使用）
const ROLE_COLORS: Record<Role, { light: string; dark: string }> = {
  factory: { light: "#2a78d6", dark: "#3987e5" }, // blue
  distributor: { light: "#eb6834", dark: "#d95926" }, // orange
  wholesaler: { light: "#1baf7a", dark: "#199e70" }, // aqua
  retailer: { light: "#eda100", dark: "#c98500" }, // yellow
};

export const MUTED_INK = { light: "#898781", dark: "#898781" };
export const GRIDLINE = { light: "#e1e0d9", dark: "#2c2c2a" };

export function useIsDarkMode(): boolean {
  const [isDark, setIsDark] = useState(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false,
  );

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const listener = (event: MediaQueryListEvent) => setIsDark(event.matches);
    media.addEventListener("change", listener);
    return () => media.removeEventListener("change", listener);
  }, []);

  return isDark;
}

export function roleColor(role: Role, isDark: boolean): string {
  return isDark ? ROLE_COLORS[role].dark : ROLE_COLORS[role].light;
}
