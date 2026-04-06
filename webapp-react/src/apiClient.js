import { getInitData, getTelegramWebApp } from './telegram';

export function getApiBase() {
  return window.location.origin;
}

export async function postJSON(path, body) {
  const res = await fetch(getApiBase() + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body ?? {}),
  });
  return res;
}

export async function getJSON(path) {
  const res = await fetch(getApiBase() + path);
  return res;
}

export async function loadUserInfo() {
  const initData = getInitData();
  if (!initData) throw new Error('Missing init_data');
  const res = await postJSON('/api/user_info', { init_data: initData });
  const data = await res.json();
  if (!data?.ok) throw new Error(data?.error || 'user_info_failed');
  return data;
}

export async function loadStrings(lang) {
  const res = await getJSON('/api/strings?lang=' + encodeURIComponent(lang || 'de'));
  const data = await res.json();
  return data || {};
}

export async function loadVersion() {
  const res = await getJSON('/api/version');
  const data = await res.json();
  return data || {};
}

/** Datenschutz + Impressum (src/legal auf dem Server). */
export async function loadLegal(lang) {
  const res = await getJSON('/api/legal?lang=' + encodeURIComponent(lang || 'de'));
  const data = await res.json();
  if (!data?.ok) throw new Error(data?.error || 'legal_failed');
  return data;
}

export async function loadModels(path, lang) {
  const qs = new URLSearchParams();
  if (path) qs.set('path', path);
  if (lang) qs.set('lang', lang);
  const res = await getJSON('/api/models?' + qs.toString());
  const data = await res.json();
  return data || {};
}

export async function loadModelDetail(key) {
  const qs = new URLSearchParams();
  qs.set('key', key);
  const res = await getJSON('/api/model?' + qs.toString());
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return {
      ok: false,
      error: data?.error || 'model_detail_failed',
      status: res.status,
    };
  }
  return data || {};
}

export async function loadShopPackages() {
  const res = await getJSON('/api/shop_packages');
  const data = await res.json();
  return data || {};
}

export async function sendWebappAction(action, payload = {}) {
  const tg = getTelegramWebApp();
  const initData = getInitData();

  // Diese Actions sollen die Telegram Mini App nicht automatisch schließen.
  // Mini App soll z. B. bei Sprachwechsel offen bleiben.
  const noClose =
    action?.startsWith('set_lang_') ||
    action === 'toggle_opt' ||
    action === 'toggle_daily' ||
    action === 'optimize_prompt_paid';
  const body = { action, ...payload };
  if (initData) body.init_data = initData;

  // When initData isn't available (debug in browser), Telegram may accept tg.sendData.
  if (initData) {
    const res = await postJSON('/api/webapp_action', body);
    const data = await res.json().catch(() => ({}));
    if (data?.ok) {
      if (!noClose && tg?.close) tg.close();
    } else {
      if (!noClose) throw new Error(data?.error || 'webapp_action_failed');
    }
    return data;
  }

  if (!noClose && tg?.sendData) {
    tg.sendData(JSON.stringify({ action }));
    return { ok: true };
  }
  if (!noClose && tg?.close) tg.close();
  return { ok: true };
}

export async function uploadReferenceFiles(files) {
  const tgInit = getInitData();
  if (!tgInit) throw new Error('Missing init_data');
  const fd = new FormData();
  fd.append('init_data', tgInit);
  for (const f of files || []) fd.append('files', f);
  const res = await fetch(getApiBase() + '/api/webapp_upload_reference', {
    method: 'POST',
    body: fd,
  });
  return res;
}

