import React from 'react';

export default function LegalDocsView({ doc, labels, privacyText, impressumText, onBack }) {
  const title = doc === 'privacy' ? labels?.doc_privacy_title : labels?.doc_impressum_title;
  const body = doc === 'privacy' ? privacyText : impressumText;
  return (
    <div>
      <div className="back-btn" onClick={onBack} role="button" tabIndex={0}>
        ← {labels?.back || 'Back'}
      </div>
      <div className="header">
        <h1>{title}</h1>
      </div>
      <pre
        className="legal-body"
        style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          fontSize: '0.88rem',
          lineHeight: 1.5,
          margin: '12px 0 24px',
          padding: '12px 14px',
          background: 'var(--surface-raised)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-sm)',
          fontFamily: 'inherit',
        }}
      >
        {body || '…'}
      </pre>
    </div>
  );
}
