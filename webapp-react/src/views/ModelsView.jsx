import React from 'react';

function folderIcon(slug) {
  const s = String(slug || '').toLowerCase();
  if (s.includes('favorites') || s.includes('favoriten') || s.includes('favourites')) return '⭐';
  if (s.includes('google')) return '🧠';
  if (s.includes('flux')) return '✨';
  if (s.includes('openai')) return '🤖';
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
  if (s.includes('google')) return 'https://cdn.simpleicons.org/google/4285F4';
  if (s.includes('openai')) return 'https://cdn.simpleicons.org/openai/FFFFFF';
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

export default function ModelsView({ title, folders, models, freeLabel, loading, currentPath, onBack, onSelectFolder, onSelectModel }) {
  return (
    <div>
      <div className="back-btn" onClick={onBack} role="button" tabIndex={0}>
        ← <span>Zurück</span>
      </div>
      <div className="header">
        <h1>{title || 'Modelle'}</h1>
      </div>

      {loading ? <div className="loading">Laden...</div> : null}

      <div style={{ marginTop: 10 }}>
        {(folders || []).map((f) => {
          const fp = f.path || f.slug;
          const label = String(f.slug || fp || '').replace(/_/g, ' ');
          return (
            <div
              key={'folder-' + fp}
              className="model-card"
              style={{ cursor: 'pointer' }}
              onClick={() => onSelectFolder(fp)}
            >
              <div className="model-left">
                {folderLogoUrl(label) ? (
                  <img
                    className="model-logo"
                    src={folderLogoUrl(label)}
                    alt={label + ' logo'}
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                      const next = e.currentTarget.nextElementSibling;
                      if (next) next.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div
                  className="model-logo-fallback"
                  style={{
                    borderColor: 'rgba(99,102,241,0.35)',
                    display: folderLogoUrl(label) ? 'none' : 'flex',
                  }}
                >
                  {folderIcon(label)}
                </div>
                <span className="model-name">{label}</span>
              </div>
              <span className="model-cost">→</span>
            </div>
          );
        })}

        {(models || []).map((m) => {
          const isFree = (m.final_cost ?? 0) <= 0;
          const costLabel = isFree ? freeLabel : String(m.final_cost) + ' ⭐';
          return (
            <div
              key={m.key}
              className="model-card"
              style={{ cursor: 'pointer' }}
              onClick={() => onSelectModel(m.key)}
            >
              <div className="model-left">
                <ModelLogo model={m} />
                <span className="model-name">{m.name}</span>
              </div>
              <span className="model-cost">{costLabel}</span>
            </div>
          );
        })}

        {(!folders || folders.length === 0) && (!models || models.length === 0) && !loading ? (
          <div className="loading">Keine Modelle gefunden.</div>
        ) : null}
      </div>
    </div>
  );
}

