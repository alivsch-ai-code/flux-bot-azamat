import React, { useEffect, useMemo, useState } from 'react';
import { initTelegram, getTelegramWebApp } from './telegram';
import { loadModels, loadModelDetail, loadShopPackages, loadStrings, loadUserInfo, sendWebappAction } from './apiClient';
import MainView from './views/MainView.jsx';
import ModelsView from './views/ModelsView.jsx';
import SettingsView from './views/SettingsView.jsx';
import ShopView from './views/ShopView.jsx';
import ProfileView from './views/ProfileView.jsx';
import ModelDetailView from './views/ModelDetailView.jsx';

function showToastError(msg) {
  const el = document.createElement('div');
  el.style.cssText =
    'position:fixed;bottom:20px;left:16px;right:16px;padding:12px;background:#c33;color:#fff;border-radius:8px;text-align:center;z-index:9999;';
  el.textContent = '⚠️ ' + (msg || 'Fehler') + ' – Bitte im Chat /start nutzen.';
  document.body.appendChild(el);
  setTimeout(() => {
    try {
      el.remove();
    } catch {
      // ignore
    }
  }, 4000);
}

export default function AppShell() {
  const apiBase = useMemo(() => window.location.origin, []);

  const [user, setUser] = useState({
    user_id: null,
    username: 'User',
    credits: 0,
    lang: 'de',
    auto_opt: true,
    daily_msg: true,
    bot_username: '',
  });
  const [strings, setStrings] = useState({});
  const [view, setView] = useState('main'); // main|models|detail|settings|shop|profile
  const [currentPath, setCurrentPath] = useState('root');
  const [modelKey, setModelKey] = useState('');

  const [modelsData, setModelsData] = useState({ title: '', folders: [], models: [] });
  const [loading, setLoading] = useState(false);

  function t(key, fallback) {
    return strings?.[key] || fallback || key;
  }

  async function fetchModelsForPath(path) {
    setLoading(true);
    try {
      const data = await loadModels(path || 'root', user.lang);
      const folders = data?.folders || [];
      const models = data?.models || [];
      setModelsData({
        title: data?.title || path || '',
        folders,
        models,
      });
      setCurrentPath(path || 'root');
      setView('models');
    } catch (e) {
      showToastError('Laden fehlgeschlagen');
    } finally {
      setLoading(false);
    }
  }

  function parseInitialView() {
    const params = new URLSearchParams(window.location.search);
    const viewParam = params.get('view');
    const modelParam = params.get('model');
    const pathParam = params.get('path');

    if (viewParam === 'shop') return { view: 'shop' };
    if (viewParam === 'settings') return { view: 'settings' };
    if (viewParam === 'profile') return { view: 'profile' };

    if (modelParam) return { view: 'detail', modelKey: modelParam };

    if (pathParam && pathParam !== 'root') return { view: 'models', path: pathParam };
    return { view: 'main' };
  }

  useEffect(() => {
    // Telegram init (theme)
    initTelegram();

    const initial = parseInitialView();
    if (initial.view === 'detail') {
      setModelKey(initial.modelKey || '');
      setView('detail');
    } else if (initial.view === 'models') {
      setCurrentPath(initial.path || 'root');
      setView('models');
    } else {
      setView(initial.view || 'main');
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadEverything() {
      const tg = getTelegramWebApp();
      const hasInitData = !!tg?.initData;
      if (!hasInitData) return;

      try {
        setLoading(true);
        const data = await loadUserInfo();
        if (cancelled) return;
        setUser((prev) => ({
          ...prev,
          user_id: data.user_id ?? prev.user_id,
          username: data.username || prev.username,
          credits: data.credits ?? prev.credits,
          lang: data.lang || prev.lang,
          auto_opt: !!data.auto_opt,
          daily_msg: !!data.daily_msg,
          bot_username: data.bot_username || prev.bot_username,
        }));

        const st = await loadStrings(data.lang || 'de');
        if (cancelled) return;
        setStrings(st || {});

        // If we already decided to show models from URL, fetch it now.
        const params = new URLSearchParams(window.location.search);
        const pathParam = params.get('path');
        const viewParam = params.get('view');
        const modelParam = params.get('model');
        if (viewParam !== 'shop' && viewParam !== 'settings' && viewParam !== 'profile' && modelParam == null) {
          if (pathParam && pathParam !== 'root') {
            await fetchModelsForPath(pathParam);
          }
        }
      } catch (e) {
        // In Telegram this should succeed; for browser debug we just keep defaults.
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadEverything();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const freeLabel = t('webapp_free', 'FREE');

  const topBarVisible = !!strings?.webapp_user || !!user?.username;

  return (
    <div className="app">
      {topBarVisible ? (
        <div className="top-bar" style={{ display: 'flex' }}>
          <span className="user" style={{ opacity: 0.92 }}>
            {(t('webapp_user', 'User') || 'User') + ': ' + (user.username || 'User')}
          </span>
          <span className="credits">
            💎 <b style={{ fontWeight: 800 }}>{user.credits || 0}</b> ⭐
          </span>
        </div>
      ) : null}

      {view === 'main' ? (
        <MainView
          t={t}
          onNavigateModels={(path) => fetchModelsForPath(path)}
          onOpenShop={() => setView('shop')}
          onOpenSettings={() => setView('settings')}
          onOpenProfile={() => setView('profile')}
        />
      ) : null}

      {view === 'models' ? (
        <ModelsView
          title={modelsData.title}
          folders={modelsData.folders}
          models={modelsData.models}
          freeLabel={freeLabel}
          loading={loading}
          currentPath={currentPath}
          onBack={() => {
            const parts = (currentPath || 'root').split('/');
            if (parts.length > 1) {
              parts.pop();
              const parent = parts.join('/') || 'root';
              fetchModelsForPath(parent);
            } else {
              setView('main');
            }
          }}
          onSelectFolder={(fp) => fetchModelsForPath(fp)}
          onSelectModel={(key) => {
            setModelKey(key);
            setView('detail');
          }}
        />
      ) : null}

      {view === 'settings' ? (
        <SettingsView
          lang={user.lang}
          auto_opt={user.auto_opt}
          daily_msg={user.daily_msg}
          t={t}
          onBack={() => setView('main')}
          onSetLang={async (lang) => {
            await sendWebappAction('set_lang_' + lang);
            setUser((u) => ({ ...u, lang }));
            try {
              const st = await loadStrings(lang);
              setStrings(st || {});
            } catch {
              // ignore
            }
          }}
          onToggleOpt={async () => {
            await sendWebappAction('toggle_opt');
            setUser((u) => ({ ...u, auto_opt: !u.auto_opt }));
          }}
          onToggleDaily={async () => {
            await sendWebappAction('toggle_daily');
            setUser((u) => ({ ...u, daily_msg: !u.daily_msg }));
          }}
        />
      ) : null}

      {view === 'shop' ? (
        <ShopView
          t={t}
          userCredits={user.credits}
          onBack={() => setView('main')}
          onBuy={(credits, price) => sendWebappAction('buy_credits_' + credits + '_' + price)}
        />
      ) : null}

      {view === 'profile' ? <ProfileView t={t} user={user} onBack={() => setView('main')} /> : null}

      {view === 'detail' ? (
        <ModelDetailView
          modelKey={modelKey}
          t={t}
          user={user}
          onUpdateCredits={(credits) => setUser((u) => ({ ...u, credits }))}
          onBackToModels={() => setView('models')}
        />
      ) : null}

      {loading && view !== 'detail' ? <div className="loading">Laden...</div> : null}

      <div style={{ display: 'none' }}>{apiBase}</div>
    </div>
  );
}

