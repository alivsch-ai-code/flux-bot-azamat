import React from 'react';

function Card({ icon, label, desc, tone = 'default', onClick }) {
  const onKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onClick && onClick();
    }
  };
  return (
    <div className={`card card-tone-${tone}`} onClick={onClick} onKeyDown={onKeyDown} role="button" tabIndex={0}>
      <div className="card-animated-bg" aria-hidden="true" />
      <div className="card-icon">{icon}</div>
      <div className="card-label">{label}</div>
      <div className="card-desc">{desc}</div>
    </div>
  );
}

export default function MainView({ t, onNavigateModels, onOpenShop, onOpenSettings, onOpenProfile }) {
  return (
    <div>
      <div className="header">
        <h1>
          🤖 <span>{t('webapp_title', 'AZAMAT AI Hub')}</span>
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginTop: '8px' }}>
          {t('webapp_choose_category', 'Wähle eine Kategorie')}
        </p>
        <div className="credits-badge" style={{ display: 'none' }}>
          💎 <span>0</span> Credits
        </div>
      </div>

      <div className="section">
        <div className="section-title">{t('webapp_categories', 'Kategorien')}</div>
        <div className="grid">
          <Card icon="🎨" tone="image" label={t('menu_image', 'Bild Studio')} desc={t('webapp_desc_image', 'Flux, DALL-E, SD')} onClick={() => onNavigateModels('image')} />
          <Card icon="🎬" tone="video" label={t('menu_video', 'Video Studio')} desc={t('webapp_desc_video', 'Kling, Wan, Hunyuan')} onClick={() => onNavigateModels('video')} />
          <Card icon="🎙️" tone="audio" label={t('menu_audio', 'Audio Studio')} desc={t('webapp_desc_audio', 'Music & Voice')} onClick={() => onNavigateModels('audio')} />
          <Card icon="📝" tone="text" label={t('menu_text', 'Text / Chat')} desc={t('webapp_desc_text', 'LLMs & Chat')} onClick={() => onNavigateModels('text')} />
          <Card icon="🛠️" tone="tools" label={t('menu_tools', 'Werkzeuge')} desc={t('webapp_desc_tools', 'Profi Tools')} onClick={() => onNavigateModels('tools')} />

          <Card icon="💎" tone="shop" label={t('webapp_credits_buy', 'Credits kaufen')} desc={t('webapp_shop_sub', 'Sicher per Telegram Stars')} onClick={onOpenShop} />
          <Card icon="⚙️" tone="settings" label={t('webapp_settings', 'Einstellungen')} desc={''} onClick={onOpenSettings} />
          <Card icon="👤" tone="profile" label={t('menu_profile', 'Profil')} desc={''} onClick={onOpenProfile} />
        </div>
      </div>
    </div>
  );
}

