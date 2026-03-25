import React, { useEffect, useState } from 'react';
import { loadShopPackages } from '../apiClient';

export default function ShopView({ t, userCredits, onBack, onBuy }) {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function run() {
      try {
        setLoading(true);
        const data = await loadShopPackages();
        if (cancelled) return;
        setPackages(data?.packages || []);
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div>
      <div className="back-btn" onClick={onBack} role="button" tabIndex={0}>
        ← {t('webapp_back', 'Zurück')}
      </div>
      <div className="header">
        <h1>{t('webapp_shop_title', '💳 Buy Credits')}</h1>
        <p style={{ marginTop: 10, color: 'var(--tg-theme-text-color)', opacity: 0.9 }}>
          {t('webapp_credits_remaining', 'Credits')}: {userCredits} ⭐
        </p>
      </div>

      <div className="section">
        {loading ? (
          <div className="loading">Laden...</div>
        ) : (
          <div>
            {(packages || []).map((p, idx) => (
              <div
                key={'pkg-' + idx}
                className="model-card"
                style={{ cursor: 'pointer' }}
                onClick={() => onBuy(p.credits, p.price)}
              >
                <div className="model-left">
                  <div className="model-logo-fallback" style={{ fontSize: 18 }}>
                    💎
                  </div>
                  <span className="model-name">{p.desc}</span>
                </div>
                <span className="model-cost">
                  {p.price} ⭐
                </span>
              </div>
            ))}
            {(!packages || packages.length === 0) && !loading ? <div className="loading">Keine Pakete gefunden.</div> : null}
          </div>
        )}
      </div>
    </div>
  );
}

