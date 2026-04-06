import React from 'react';

function folderIcon(slug) {
  const s = String(slug || '').toLowerCase();
  if (s.includes('favorites') || s.includes('favoriten') || s.includes('favourites')) return '⭐';
  if (s.includes('avatar')) return '🗣️';
  if (s.includes('motioncontrol') || s.includes('motion control')) return '🎞️';
  if (s.includes('seedance')) return '🌱';
  if (s.includes('google')) return '🧠';
  if (s.includes('flux')) return '✨';
  if (s.includes('openai')) return '🤖';
  if (s.includes('anthropic')) return '🧠';
  if (s.includes('deepseek')) return '🔎';
  if (s.includes('xai')) return '❌';
  if (s.includes('meta')) return 'Ⓜ️';
  if (s.includes('qwen')) return '🛰️';
  if (s.includes('minimax')) return '🎞️';
  if (s.includes('tencent')) return '🟦';
  if (s.includes('bytedance') || s.includes('byte_dance')) return '🎬';
  if (s.includes('kling')) return '⚡';
  if (s.includes('ideogram')) return '🧩';
  if (s.includes('recraft')) return '🪄';
  if (s.includes('stability')) return '🌀';
  if (s.includes('video')) return '🎬';
  if (s.includes('image')) return '🎨';
  if (s.includes('audio')) return '🎙️';
  return '📁';
}

function folderLogoUrl(slug) {
  const s = String(slug || '').toLowerCase();
  // Official brand marks via Simple Icons CDN.
  if (s.includes('seedance')) return 'https://cdn.simpleicons.org/bytedance/3C8CFF';
  if (s.includes('google')) return 'https://cdn.simpleicons.org/google/4285F4';
  if (s.includes('openai')) return 'https://cdn.simpleicons.org/openai/FFFFFF';
  if (s.includes('anthropic')) return 'https://cdn.simpleicons.org/anthropic/FFFFFF';
  if (s.includes('deepseek')) return 'https://cdn.simpleicons.org/deepseek/64D2FF';
  if (s.includes('xai')) return 'https://cdn.simpleicons.org/x/FFFFFF';
  if (s.includes('meta')) return 'https://cdn.simpleicons.org/meta/5AC8FA';
  if (s.includes('qwen')) return 'https://cdn.simpleicons.org/alibabadotcom/FF6A00';
  if (s.includes('minimax')) return 'https://cdn.simpleicons.org/minutemailer/7DE7FF';
  if (s.includes('tencent')) return 'https://cdn.simpleicons.org/tencentqq/5AC8FA';
  if (s.includes('bytedance') || s.includes('byte_dance')) return 'https://cdn.simpleicons.org/bytedance/3C8CFF';
  if (s.includes('kling')) return 'https://cdn.simpleicons.org/lightning/64D2FF';
  if (s.includes('flux')) return 'https://cdn.simpleicons.org/lightning/64D2FF';
  if (s.includes('ideogram')) return 'https://cdn.simpleicons.org/pictureinpicture/64D2FF';
  if (s.includes('recraft')) return 'https://cdn.simpleicons.org/figma/FFFFFF';
  if (s.includes('stability')) return 'https://cdn.simpleicons.org/stabilityai/FFFFFF';
  if (s.includes('favorites') || s.includes('favoriten') || s.includes('favourites')) return 'https://cdn.simpleicons.org/apple/FFD60A';
  return '';
}

function fallbackEmojiForModel(model) {
  const types = Array.isArray(model?.model_type) ? model.model_type : [];
  const typeStr = String(types.join(' ')).toLowerCase();
  const nameStr = String(model?.name || '').toLowerCase();

  if (typeStr.includes('text') || nameStr.includes('text') || nameStr.includes('chat')) return '💬';
  if (typeStr.includes('video') || nameStr.includes('video') || nameStr.includes('veo') || nameStr.includes('kling') || nameStr.includes('sora') || nameStr.includes('hunyuan') || nameStr.includes('runway')) return '🎬';
  if (typeStr.includes('audio') || nameStr.includes('audio') || nameStr.includes('bark') || nameStr.includes('whisper')) return '🎙️';
  if (typeStr.includes('image') || nameStr.includes('image') || nameStr.includes('flux') || nameStr.includes('sdxl')) return '🖼️';
  if (typeStr.includes('tool') || typeStr.includes('tools')) return '🛠️';
  return '✨';
}

function ModelLogo({ model }) {
  const logoUrl = model?.example_image_url || '';
  if (logoUrl) {
    return <img className="model-logo" src={logoUrl} alt={model?.name || 'Model'} onError={(e) => (e.currentTarget.style.display = 'none')} />;
  }
  return <div className="model-logo-fallback" title="No logo">{fallbackEmojiForModel(model)}</div>;
}

export default function ModelsView({ title, folders, models, favoritesModels, freeLabel, loading, currentPath, onBack, onSelectFolder, onSelectModel, t }) {
  const favoriteModels = Array.isArray(favoritesModels) ? favoritesModels : [];
  const regularModels = models || [];
  const path = String(currentPath || '').toLowerCase();
  const isStudioTopLevel = ['image', 'video', 'audio', 'text', 'tools'].includes(path);
  const visibleFavoriteModels = isStudioTopLevel ? favoriteModels : [];
  const activateOnKey = (e, fn) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      fn && fn();
    }
  };

  return (
    <div>
      <div className="back-btn" onClick={onBack} onKeyDown={(e) => activateOnKey(e, onBack)} role="button" tabIndex={0}>
        ← <span>{t ? t('webapp_back', 'Zurück') : 'Zurück'}</span>
      </div>
      <div className="header">
        <h1>{title || (t ? t('webapp_models', 'Modelle') : 'Modelle')}</h1>
      </div>

      {loading ? <div className="loading">{t ? t('webapp_loading', 'Laden...') : 'Laden...'}</div> : null}

      <div style={{ marginTop: 10 }}>
        {(folders || []).length ? (
          <div className="section-title" style={{ marginTop: 8, marginBottom: 8 }}>
            📁 {t ? t('webapp_folders', 'Ordner') : 'Ordner'}
          </div>
        ) : null}
        {(folders || []).length ? <div className="folder-grid">
          {(folders || []).map((f) => {
            const fp = f.path || f.slug;
            const label = String(f.slug || fp || '').replace(/_/g, ' ');
            return (
              <div
                key={'folder-' + fp}
                className="folder-tile"
                onClick={() => onSelectFolder(fp)}
                onKeyDown={(e) => activateOnKey(e, () => onSelectFolder(fp))}
                role="button"
                tabIndex={0}
              >
                {folderLogoUrl(label) ? (
                  <img
                    className="folder-logo"
                    src={folderLogoUrl(label)}
                    alt={label + ' logo'}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      const next = e.currentTarget.nextElementSibling;
                      if (next) next.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div className="folder-logo-fallback" style={{ display: folderLogoUrl(label) ? 'none' : 'flex' }}>
                  {folderIcon(label)}
                </div>
                <div className="folder-title">{label}</div>
              </div>
            );
          })}
        </div> : null}

        {visibleFavoriteModels.length ? (
          <div className="section-title" style={{ marginTop: 12, marginBottom: 8 }}>
            ⭐ {t ? t('webapp_favorites', 'Favoriten') : 'Favoriten'}
          </div>
        ) : null}

        {visibleFavoriteModels.length ? <div className="favorites-grid">{visibleFavoriteModels.map((m) => {
          const isFree = (m.final_cost ?? 0) <= 0;
          const costLabel = isFree ? freeLabel : String(m.final_cost) + ' ⭐';
          return (
            <div
              key={m.key}
              className="favorite-tile"
              onClick={() => onSelectModel(m.key)}
              onKeyDown={(e) => activateOnKey(e, () => onSelectModel(m.key))}
              role="button"
              tabIndex={0}
            >
              <div className="favorite-head">
                <ModelLogo model={m} />
                <span className="favorite-name">{m.name}</span>
              </div>
              <span className="favorite-cost">{costLabel}</span>
            </div>
          );
        })}</div> : null}

        {regularModels.map((m) => {
          const isFree = (m.final_cost ?? 0) <= 0;
          const costLabel = isFree ? freeLabel : String(m.final_cost) + ' ⭐';
          return (
            <div
              key={m.key}
              className="model-card"
              style={{ cursor: 'pointer' }}
              onClick={() => onSelectModel(m.key)}
              onKeyDown={(e) => activateOnKey(e, () => onSelectModel(m.key))}
              role="button"
              tabIndex={0}
            >
              <div className="model-left">
                <ModelLogo model={m} />
                <span className="model-name">{m.name}</span>
              </div>
              <span className="model-cost">{costLabel}</span>
            </div>
          );
        })}

        {(!folders || folders.length === 0) && (!regularModels || regularModels.length === 0) && (!visibleFavoriteModels || visibleFavoriteModels.length === 0) && !loading ? (
          <div className="loading">{t ? t('webapp_no_models', 'Keine Modelle gefunden.') : 'Keine Modelle gefunden.'}</div>
        ) : null}
      </div>
    </div>
  );
}

