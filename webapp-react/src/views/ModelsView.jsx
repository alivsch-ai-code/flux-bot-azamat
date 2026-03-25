import React from 'react';

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
                <div className="model-logo-fallback" style={{ borderColor: 'rgba(99,102,241,0.35)' }}>
                  📁
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

