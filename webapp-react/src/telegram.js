export function getTelegramWebApp() {
  try {
    return window.Telegram?.WebApp || null;
  } catch {
    return null;
  }
}

export function getInitData() {
  const tg = getTelegramWebApp();
  return tg?.initData || '';
}

export function applyTelegramTheme() {
  const tg = getTelegramWebApp();
  if (!tg?.themeParams) return;

  const tp = tg.themeParams || {};
  const rs = document.documentElement.style;
  rs.setProperty('--tg-theme-bg-color', tp.bg_color || '#0c1017');
  rs.setProperty('--tg-theme-text-color', tp.text_color || '#e8edf4');
  rs.setProperty('--tg-theme-button-color', tp.button_color || '#22d3d8');
  rs.setProperty('--tg-theme-button-text-color', tp.button_text_color || '#061016');
  if (tp.secondary_bg_color) rs.setProperty('--tg-secondary-bg', tp.secondary_bg_color);
  if (tp.hint_color) rs.setProperty('--tg-hint-color', tp.hint_color);

  // Some clients expose this, some throw.
  try {
    tg.setHeaderColor(tp.bg_color || tp.secondary_bg_color || '#0c1017');
  } catch {
    // ignore
  }
}

export function initTelegram() {
  const tg = getTelegramWebApp();
  if (!tg) return;
  tg.ready();
  tg.expand();
  applyTelegramTheme();
}

