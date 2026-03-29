import React from 'react';

function LangButton({ lang, label, active, onClick }) {
  return (
    <button
      type="button"
      className="lang-btn"
      style={{
        width: '100%',
        padding: '14px 18px',
        marginBottom: 10,
        background: 'var(--surface-raised)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-sm)',
        color: 'inherit',
        fontSize: '1rem',
        fontFamily: 'inherit',
        cursor: 'pointer',
        textAlign: 'left',
        fontWeight: 500,
        opacity: active ? 1 : 0.92,
      }}
      onClick={() => onClick(lang)}
    >
      {label}
    </button>
  );
}

const LEGAL_UI = {
  de: { section: 'Rechtliches', privacy: 'Datenschutz', impressum: 'Impressum' },
  en: { section: 'Legal', privacy: 'Privacy policy', impressum: 'Legal notice (Impressum)' },
  ru: { section: 'Правовая информация', privacy: 'Конфиденциальность', impressum: 'Правовые сведения' },
  kk: { section: 'Құқықтық ақпарат', privacy: 'Құпиялылық', impressum: 'Заңды мәліметтер' },
};

export default function SettingsView({
  lang,
  auto_opt,
  daily_msg,
  t,
  onBack,
  onSetLang,
  onToggleOpt,
  onToggleDaily,
  onOpenPrivacy,
  onOpenImpressum,
}) {
  const leg = LEGAL_UI[lang] || LEGAL_UI.de;
  return (
    <div>
      <div className="back-btn" onClick={onBack} role="button" tabIndex={0}>
        ← {t('webapp_back', 'Zurück')}
      </div>
      <div className="header">
        <h1>{t('webapp_settings', 'Einstellungen')}</h1>
      </div>

      <div className="section">
        <div className="section-title">{t('webapp_language', 'Sprache')}</div>
        <LangButton lang="de" label="🇩🇪 Deutsch" active={lang === 'de'} onClick={onSetLang} />
        <LangButton lang="en" label="🇬🇧 English" active={lang === 'en'} onClick={onSetLang} />
        <LangButton lang="ru" label="🇷🇺 Русский" active={lang === 'ru'} onClick={onSetLang} />
        <LangButton lang="kk" label="🇰🇿 Қазақша" active={lang === 'kk'} onClick={onSetLang} />
      </div>

      <div className="section">
        <div className="section-title">{t('webapp_prompt_magic', '✨ Prompt Magie')}</div>
        <div className="gen-row" style={{ marginTop: 8 }}>
          <button type="button" className="btn-secondary" onClick={onToggleOpt}>
            {auto_opt ? '✨ Prompt Magic: ON' : '⚪️ Prompt Magic: OFF'}
          </button>
        </div>
      </div>

      <div className="section">
        <div className="section-title">{t('webapp_daily_news', '📰 Daily News')}</div>
        <div className="gen-row" style={{ marginTop: 8 }}>
          <button type="button" className="btn-secondary" onClick={onToggleDaily}>
            {daily_msg ? '📰 Daily News: ON' : '🔕 Daily News: OFF'}
          </button>
        </div>
      </div>

      <div className="section">
        <div className="section-title">{leg.section}</div>
        <div className="gen-row" style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <button type="button" className="btn-secondary" onClick={onOpenPrivacy}>
            🔒 {leg.privacy}
          </button>
          <button type="button" className="btn-secondary" onClick={onOpenImpressum}>
            📋 {leg.impressum}
          </button>
        </div>
      </div>
    </div>
  );
}

