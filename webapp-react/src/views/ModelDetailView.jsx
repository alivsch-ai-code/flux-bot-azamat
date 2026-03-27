import React, { useEffect, useMemo, useRef, useState } from 'react';
import { loadModelDetail, sendWebappAction, uploadReferenceFiles } from '../apiClient';

function fallbackEmojiForModelDetail(modelType, name) {
  const types = Array.isArray(modelType) ? modelType : [];
  const typeStr = String(types.join(' ')).toLowerCase();
  const nameStr = String(name || '').toLowerCase();
  if (typeStr.includes('text') || nameStr.includes('text') || typeStr.includes('chat')) return '💬';
  if (
    typeStr.includes('video') ||
    nameStr.includes('video') ||
    typeStr.includes('veo') ||
    nameStr.includes('veo') ||
    nameStr.includes('kling') ||
    nameStr.includes('sora') ||
    nameStr.includes('hunyuan') ||
    nameStr.includes('runway')
  )
    return '🎬';
  if (typeStr.includes('audio') || nameStr.includes('audio') || nameStr.includes('bark') || nameStr.includes('whisper')) return '🎙️';
  if (typeStr.includes('image') || nameStr.includes('image') || typeStr.includes('flux') || nameStr.includes('sdxl')) return '🖼️';
  if (typeStr.includes('tool') || typeStr.includes('tools')) return '🛠️';
  return '✨';
}

function showErrorOverlay(msg) {
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

export default function ModelDetailView({ modelKey, t, user, onUpdateCredits, onBackToModels }) {
  const [loading, setLoading] = useState(true);
  const [model, setModel] = useState(null);
  const [error, setError] = useState('');

  // Prompt inputs
  const [promptText, setPromptText] = useState('');
  const [negativePromptText, setNegativePromptText] = useState('');

  // Generation options
  const [duration, setDuration] = useState(5);
  const [resolution, setResolution] = useState('');
  const [aspectRatio, setAspectRatio] = useState('');
  const [generateAudio, setGenerateAudio] = useState(false);
  const [referenceImagesText, setReferenceImagesText] = useState('');

  // Dynamic schema-driven fields
  const [dynamicValues, setDynamicValues] = useState({});

  const [uploadStatusMap, setUploadStatusMap] = useState({});
  const [uploadingMap, setUploadingMap] = useState({});
  const dynamicFileInputRefs = useRef({});

  const [referenceUploadStatus, setReferenceUploadStatus] = useState('');
  const [referenceUploading, setReferenceUploading] = useState(false);
  const referenceFileInputRef = useRef(null);

  const [submitting, setSubmitting] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [submitInfo, setSubmitInfo] = useState('');

  useEffect(() => {
    let cancelled = false;
    async function run() {
      setLoading(true);
      setError('');
      setModel(null);
      try {
        if (!modelKey) throw new Error('missing_model_key');
        const data = await loadModelDetail(modelKey);
        if (cancelled) return;
        if (!data || !data.ok) {
          setError('Model not found');
          setModel(data || null);
          return;
        }
        setModel(data);
      } catch (e) {
        if (!cancelled) setError('Failed to load model');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    run();
    return () => {
      cancelled = true;
    };
  }, [modelKey]);

  const isText = useMemo(() => Array.isArray(model?.model_type) && model.model_type.includes('text'), [model]);

  const opt = model?.generation_options_schema || {};
  const inputSchema = model?.input_schema || {};
  const schemaProps = (inputSchema && inputSchema.properties) ? inputSchema.properties : {};
  const schemaRequired = Array.isArray(inputSchema?.required) ? inputSchema.required : [];

  const dynamicKeys = useMemo(() => {
    const props = schemaProps || {};
    return Object.keys(props).filter((k) => {
      const p = props[k] || {};
      const kl = String(k).toLowerCase();
      if (['prompt', 'negative_prompt', 'image', 'images', 'start_image', 'end_image', 'reference_images', 'duration', 'resolution', 'aspect_ratio', 'generate_audio', 'messages', 'system_prompt'].includes(kl))
        return false;
      if (p.readOnly) return false;
      // Include uri-like arrays as dynamic fields (e.g. image_input for Nano Banana Pro).
      const isArrayUriLike =
        p.type === 'array' &&
        (
          String(p.format || '').toLowerCase().includes('uri') ||
          String(p.items?.format || '').toLowerCase().includes('uri') ||
          String(p.items?.type || '').toLowerCase() === 'string'
        );
      const looksConfigLikeWithoutType =
        !p.type &&
        (
          p.default !== undefined ||
          Array.isArray(p.enum) ||
          Array.isArray(p.anyOf) ||
          Array.isArray(p.oneOf) ||
          Array.isArray(p.allOf)
        );
      return ['string', 'number', 'integer', 'boolean'].includes(p.type) || Array.isArray(p.enum) || isArrayUriLike || looksConfigLikeWithoutType;
    });
  }, [schemaProps]);

  const hasGenOptions = useMemo(() => {
    return !!(
      (opt.duration && opt.duration.enabled) ||
      (opt.resolution && opt.resolution.enabled) ||
      (opt.aspect_ratio && opt.aspect_ratio.enabled) ||
      (opt.reference_images && opt.reference_images.enabled) ||
      (opt.generate_audio && opt.generate_audio.enabled)
    );
  }, [opt]);

  const hasNegativeInSchema = useMemo(() => !!(schemaProps && schemaProps.negative_prompt), [schemaProps]);

  const dynamicMediaLikeKeys = useMemo(() => {
    return dynamicKeys.filter((k) => {
      const kl = String(k).toLowerCase();
      return (
        kl.includes('image') ||
        kl.includes('img') ||
        kl.includes('mask') ||
        kl.includes('input_image') ||
        kl.includes('input_reference') ||
        kl.includes('inputreference') ||
        kl.includes('first_frame') ||
        kl.includes('last_frame') ||
        kl.includes('frame_image')
      );
    });
  }, [dynamicKeys]);

  const dynamicAdvancedKeys = useMemo(() => dynamicKeys.filter((k) => !dynamicMediaLikeKeys.includes(k)), [dynamicKeys, dynamicMediaLikeKeys]);

  const promptPlaceholder = useMemo(() => {
    const exRaw = model?.example_prompt != null && String(model.example_prompt).trim() ? String(model.example_prompt).trim() : '';
    const exShort = exRaw.slice(0, 200);
    if (exShort) return 'z. B.: ' + exShort + (exRaw.length > 200 ? '...' : '');
    return isText ? 'Erste Nachricht optional...' : 'Beschreibe Szenenbild, Stil, Details...';
  }, [model, isText]);

  // Initialize defaults when the model loads / changes
  useEffect(() => {
    if (!model) return;

    const params = new URLSearchParams(window.location.search || '');
    const prefillPrompt = (params.get('prompt') || '').trim();
    setPromptText(prefillPrompt);
    setNegativePromptText('');

    const durEnum = (opt.duration && Array.isArray(opt.duration.enum) && opt.duration.enum.length) ? opt.duration.enum : [5, 6, 7, 8];
    const durDefault = Number((opt.duration && opt.duration.default) || 5);
    setDuration(Number.isFinite(durDefault) ? durDefault : (durEnum[0] || 5));

    const resolutionProp = schemaProps?.resolution || {};
    const resEnum = Array.isArray(resolutionProp.enum) ? resolutionProp.enum : [];
    const resDefault =
      resolutionProp.default != null && String(resolutionProp.default).trim()
        ? String(resolutionProp.default)
        : resEnum.length
          ? String(resEnum[0])
          : '';
    setResolution(resDefault);

    const aspectRatioProp = schemaProps?.aspect_ratio || {};
    const ratioEnum = Array.isArray(aspectRatioProp.enum) ? aspectRatioProp.enum : [];
    const ratioDefault =
      aspectRatioProp.default != null && String(aspectRatioProp.default).trim()
        ? String(aspectRatioProp.default)
        : ratioEnum.length
          ? String(ratioEnum[0])
          : '';
    setAspectRatio(ratioDefault);

    setGenerateAudio(opt.generate_audio && opt.generate_audio.enabled ? opt.generate_audio.default !== false : false);
    setReferenceImagesText('');

    const initDyn = {};
    for (const k of dynamicKeys) {
      const p = schemaProps?.[k] || {};
      let defVal = p?.default ?? '';
      if (Array.isArray(p.enum) && p.enum.length) {
        defVal = p.default ?? p.enum[0];
      } else if (p.type === 'boolean') {
        defVal = p.default !== false;
      }
      initDyn[k] = defVal;
    }
    setDynamicValues(initDyn);

    setUploadStatusMap({});
    setUploadingMap({});
    setReferenceUploadStatus('');
    setReferenceUploading(false);
    setSubmitting(false);
    setOptimizing(false);
    setSubmitInfo('');
  }, [modelKey, model]); // eslint-disable-line react-hooks/exhaustive-deps

  const baseCost = Number(model?.final_cost || 0);
  const durationEnabled = !!(opt.duration && opt.duration.enabled);
  const computedDurationForCost = durationEnabled ? Math.max(1, Number(duration || 5)) : 5;
  const computedCost = durationEnabled ? Math.round(baseCost * (computedDurationForCost / 5)) : baseCost;
  const startButtonLabel = baseCost <= 0 ? t('webapp_free', 'FREE') : computedCost + ' ★';

  function castForPayload(k, raw) {
    const p = schemaProps?.[k] || {};
    const type = p?.type;
    if (type === 'boolean') {
      if (typeof raw === 'boolean') return raw;
      return String(raw) === 'true';
    }
    if (type === 'integer') return Number.parseInt(raw, 10);
    if (type === 'number') return Number(raw);
    if (!type) {
      // Fallback when schema omits "type" but provides defaults/ref blocks.
      if (typeof p?.default === 'boolean') {
        if (typeof raw === 'boolean') return raw;
        return String(raw) === 'true';
      }
      if (typeof p?.default === 'number') return Number(raw);
    }
    return raw;
  }

  function getFieldOptions(p) {
    if (!p || typeof p !== 'object') return [];
    if (Array.isArray(p.enum) && p.enum.length) return p.enum;
    const fromBlocks = [];
    for (const blockName of ['oneOf', 'anyOf', 'allOf']) {
      const arr = p[blockName];
      if (!Array.isArray(arr)) continue;
      for (const item of arr) {
        if (!item || typeof item !== 'object') continue;
        if (Array.isArray(item.enum) && item.enum.length) fromBlocks.push(...item.enum);
        if (Object.prototype.hasOwnProperty.call(item, 'const')) fromBlocks.push(item.const);
      }
    }
    return [...new Set(fromBlocks)];
  }

  function buildGenerationOptionsPayload() {
    const g = {};
    if (durationEnabled) g.duration = Math.max(1, Number(duration || 5));
    if (opt.resolution && opt.resolution.enabled && resolution) g.resolution = resolution;
    if (opt.aspect_ratio && opt.aspect_ratio.enabled && aspectRatio) g.aspect_ratio = aspectRatio;
    if (opt.generate_audio && opt.generate_audio.enabled) g.generate_audio = !!generateAudio;
    if (opt.reference_images && opt.reference_images.enabled) {
      const urls = (referenceImagesText || '')
        .split(/\n|,/)
        .map((s) => s.trim())
        .filter((s) => s.startsWith('http://') || s.startsWith('https://'));
      g.reference_images = urls;
    }

    for (const k of dynamicKeys) {
      const raw = dynamicValues?.[k];
      const p = schemaProps?.[k] || {};
      if (!p) continue;
      if (raw === '' || raw === null || raw === undefined) continue;
      if (Array.isArray(raw) && raw.length === 0) continue;
      if (typeof raw === 'number' && Number.isNaN(raw)) continue;

      const casted = castForPayload(k, raw);
      if (casted === '' || casted === null || casted === undefined) continue;
      if (typeof casted === 'number' && Number.isNaN(casted)) continue;
      g[k] = casted;
    }

    return g;
  }

  async function handleOptimizePaid() {
    if (optimizing) return;
    const promptVal = (promptText || '').trim();
    if (!promptVal) {
      showErrorOverlay('Bitte Prompt eingeben.');
      return;
    }
    setOptimizing(true);
    try {
      const res = await sendWebappAction('optimize_prompt_paid', { prompt: promptVal });
      if (!res?.ok) {
        showErrorOverlay(res?.error || 'Fehler');
        return;
      }
      if (res.optimized_prompt) setPromptText(res.optimized_prompt);
      if (res.credits != null && onUpdateCredits) onUpdateCredits(res.credits);
    } catch {
      showErrorOverlay('Prompt Optimierung fehlgeschlagen');
    } finally {
      setOptimizing(false);
    }
  }

  async function handleUploadDynamicKey(k, file) {
    if (!file || !k) return;
    setUploadingMap((prev) => ({ ...prev, [k]: true }));
    setUploadStatusMap((prev) => ({ ...prev, [k]: '⏳ Upload...' }));
    try {
      const res = await uploadReferenceFiles([file]);
      const data = await res.json().catch(() => ({}));
      if (!data?.ok || !Array.isArray(data.urls) || !data.urls.length) {
        showErrorOverlay(data?.error || 'Upload fehlgeschlagen');
        return;
      }
      const url = data.urls[0];
      setDynamicValues((prev) => ({ ...prev, [k]: url }));
      setUploadStatusMap((prev) => ({ ...prev, [k]: '✓ 1 URL' }));
      setTimeout(() => setUploadStatusMap((prev) => ({ ...prev, [k]: '' })), 2500);
    } catch {
      showErrorOverlay('Verbindungsfehler');
    } finally {
      setUploadingMap((prev) => ({ ...prev, [k]: false }));
    }
  }

  async function handleUploadDynamicKeyMultiple(k, files) {
    if (!k) return;
    const arr = Array.isArray(files) ? files : [];
    if (arr.length === 0) return;
    setUploadingMap((prev) => ({ ...prev, [k]: true }));
    setUploadStatusMap((prev) => ({ ...prev, [k]: '⏳ Upload...' }));
    try {
      const res = await uploadReferenceFiles(arr);
      const data = await res.json().catch(() => ({}));
      if (!data?.ok || !Array.isArray(data.urls) || !data.urls.length) {
        showErrorOverlay(data?.error || 'Upload fehlgeschlagen');
        return;
      }
      setDynamicValues((prev) => {
        const oldVal = prev?.[k];
        const oldArr = Array.isArray(oldVal) ? oldVal : (oldVal ? [oldVal] : []);
        return { ...prev, [k]: [...oldArr, ...data.urls] };
      });
      setUploadStatusMap((prev) => ({ ...prev, [k]: `✓ ${data.urls.length} URL(s)` }));
      setTimeout(() => setUploadStatusMap((prev) => ({ ...prev, [k]: '' })), 2500);
    } catch {
      showErrorOverlay('Verbindungsfehler');
    } finally {
      setUploadingMap((prev) => ({ ...prev, [k]: false }));
    }
  }

  async function handleUploadReferenceImages(files) {
    if (referenceUploading) return;
    const arr = Array.isArray(files) ? files : [];
    if (arr.length === 0) return;
    setReferenceUploading(true);
    setReferenceUploadStatus('⏳ Upload...');
    try {
      const res = await uploadReferenceFiles(arr);
      const data = await res.json().catch(() => ({}));
      if (!data?.ok || !Array.isArray(data.urls)) {
        showErrorOverlay(data?.error || 'Upload fehlgeschlagen');
        return;
      }
      const toAdd = data.urls || [];
      setReferenceImagesText((cur) => {
        const curTrim = (cur || '').trim();
        const joined = toAdd.join('\n');
        return curTrim ? curTrim + '\n' + joined : joined;
      });
      setReferenceUploadStatus('✓ ' + toAdd.length + ' URL(s)');
      setTimeout(() => setReferenceUploadStatus(''), 2800);
    } catch {
      showErrorOverlay('Verbindungsfehler');
    } finally {
      setReferenceUploading(false);
    }
  }

  async function handleSubmit(action) {
    if (submitting) return;
    const isAnyUploadInProgress =
      referenceUploading || Object.values(uploadingMap || {}).some(Boolean);
    if (isAnyUploadInProgress) {
      showErrorOverlay('Bitte warte bis alle Uploads fertig sind.');
      return;
    }
    const promptTrim = (promptText || '').trim();

    if (!isText && schemaRequired.includes('prompt') && !promptTrim) {
      showErrorOverlay('Bitte einen Prompt eingeben.');
      return;
    }

    setSubmitting(true);
    setSubmitInfo(t('webapp_generation_started', '⏳ Generierung gestartet. Wir informieren dich, sobald sie fertig ist.'));
    try {
      const payload = {};
      if (promptTrim) payload.prompt = promptTrim;

      const negTrim = (negativePromptText || '').trim();
      if (negTrim) payload.negative_prompt = negTrim;

      if (hasGenOptions || dynamicKeys.length > 0) {
        payload.generation_options = buildGenerationOptionsPayload();
      }

      await sendWebappAction(action, payload);
    } catch {
      showErrorOverlay('Fehler');
      setSubmitInfo('');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="loading">Lade Modell...</div>;
  if (error) return <div className="loading">{error}</div>;
  if (!model || !model.ok) return <div className="loading">Model not found</div>;

  const types = model.model_type || [];
  const fallbackEmoji = fallbackEmojiForModelDetail(types, model.name);
  const imgHtml = model.example_image_url ? (
    <img className="detail-preview" src={model.example_image_url} alt="Beispiel" onError={(e) => (e.currentTarget.style.display = 'none')} />
  ) : (
    <div className="detail-preview-fallback">{fallbackEmoji}</div>
  );

  const exRaw = model?.example_prompt != null && String(model.example_prompt).trim() ? String(model.example_prompt).trim() : '';
  const exShort = exRaw.slice(0, 200);
  const exampleBlock = exShort ? (
    <div className="detail-example" style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', margin: '10px 0', lineHeight: 1.4 }}>
      Beispiel-Prompt: {exShort}
      {exRaw.length > 200 ? '...' : ''}
    </div>
  ) : null;

  const resolutionProp = schemaProps?.resolution || {};
  const resEnum = Array.isArray(resolutionProp.enum) ? resolutionProp.enum : [];
  const aspectRatioProp = schemaProps?.aspect_ratio || {};
  const ratioEnum = Array.isArray(aspectRatioProp.enum) ? aspectRatioProp.enum : [];

  const durEnum = (opt.duration && Array.isArray(opt.duration.enum) && opt.duration.enum.length) ? opt.duration.enum : [5, 6, 7, 8];
  const durDefault = Number((opt.duration && opt.duration.default) || 5);
  const durationValue = durationEnabled ? (Number.isFinite(duration) ? duration : (durDefault || durEnum[0] || 5)) : (durDefault || durEnum[0] || 5);

  function renderDynamicField(k) {
    const p = schemaProps?.[k] || {};
    const requiredMark = schemaRequired.includes(k) ? ' *' : '';
    const label = String(k) + requiredMark;

    const fmt = String(p.format || '').toLowerCase();
    const typeStr = String(p.type || '').toLowerCase();
    const isUriLikeInputType = !p.type || typeStr === 'string' || typeStr === 'array' || typeStr === 'any' || typeStr === 'object';
    const kl = String(k).toLowerCase();

    const wantsImage =
      kl.includes('image') ||
      kl.includes('img') ||
      kl.includes('mask') ||
      kl.includes('input_reference') ||
      kl.includes('inputreference') ||
      kl.includes('input_image') ||
      kl.includes('first_frame') ||
      kl.includes('last_frame') ||
      kl.includes('frame_image');

    const wantsUriLike = fmt.includes('uri') || fmt.includes('url') || fmt.includes('path') || fmt === '' || fmt === 'uri' || fmt === 'url';
    const wantsUriImageUpload = wantsImage && (isUriLikeInputType || wantsUriLike);

    const currentValue = dynamicValues?.[k] ?? '';

    if (wantsUriImageUpload) {
      const status = uploadStatusMap?.[k] || '';
      const uploading = !!uploadingMap?.[k];
      const isArrayField = String(p?.type || '').toLowerCase() === 'array';
      const currentUrls = Array.isArray(currentValue) ? currentValue : (currentValue ? [currentValue] : []);
      const displayVal = currentUrls.length ? `✓ ${currentUrls.length} URL(s)` : '';

      return (
        <div className="gen-row" key={k}>
          <label>{label}</label>
          <div className="ref-upload-toolbar">
            <input
              type="file"
              multiple={isArrayField}
              style={{ position: 'absolute', width: 0, height: 0, opacity: 0, pointerEvents: 'none' }}
              accept="image/jpeg,image/png,image/webp"
              ref={(el) => {
                dynamicFileInputRefs.current[k] = el;
              }}
              onChange={(e) => {
                const files = e.target.files;
                if (!files || !files.length) return;
                if (isArrayField) {
                  handleUploadDynamicKeyMultiple(k, Array.from(files));
                } else {
                  handleUploadDynamicKey(k, files[0]);
                }
                e.target.value = '';
              }}
            />
            <button
              type="button"
              className="btn-ref-upload"
              disabled={uploading || submitting || optimizing}
              onClick={() => {
                const el = dynamicFileInputRefs.current[k];
                el?.click();
              }}
            >
              📎 Upload
            </button>
            <span className="gen-hint" style={{ display: status ? 'inline' : 'none', margin: 0 }}>
              {status}
            </span>
          </div>
          <input
            readOnly
            type="text"
            value={displayVal}
            style={{
              width: '100%',
              marginTop: 8,
              padding: 10,
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.2)',
              background: 'rgba(0,0,0,0.2)',
              color: 'var(--tg-theme-text-color)',
              fontSize: '0.9rem',
            }}
          />
        </div>
      );
    }

    const fieldOptions = getFieldOptions(p);
    if (fieldOptions.length) {
      const opts = fieldOptions;
      const selected = (currentValue === '' || currentValue === null || currentValue === undefined) ? (p.default ?? opts[0]) : currentValue;
      return (
        <div className="gen-row" key={k}>
          <label>{label}</label>
          <select value={String(selected)} onChange={(e) => setDynamicValues((prev) => ({ ...prev, [k]: e.target.value }))}>
            {opts.map((v, idx) => (
              <option value={String(v)} key={idx}>
                {String(v)}
              </option>
            ))}
          </select>
        </div>
      );
    }

    if (p.type === 'boolean') {
      const def = p.default !== false;
      const val = (currentValue === '' || currentValue === null || currentValue === undefined) ? def : currentValue;
      return (
        <div className="gen-row" key={k}>
          <label>{label}</label>
          <select value={val ? 'true' : 'false'} onChange={(e) => setDynamicValues((prev) => ({ ...prev, [k]: e.target.value === 'true' }))}>
            <option value="true">true</option>
            <option value="false">false</option>
          </select>
        </div>
      );
    }

    const inputType = p.type === 'number' || p.type === 'integer' ? 'number' : 'text';
    const step = p.type === 'integer' ? '1' : 'any';
    return (
      <div className="gen-row" key={k}>
        <label>{label}</label>
        <input type={inputType} step={step} value={currentValue} onChange={(e) => setDynamicValues((prev) => ({ ...prev, [k]: e.target.value }))} />
      </div>
    );
  }

  const shouldShowGenBlock = hasGenOptions || dynamicKeys.length > 0;

  return (
    <div className="detail-view">
      <div className="back-btn" onClick={() => onBackToModels && onBackToModels()} role="button" tabIndex={0}>
        ← <span>{t('webapp_back', 'Zurück')}</span>
      </div>

      <div className="header">
        <h1>🤖 {model.name}</h1>
      </div>

      {imgHtml}
      <div className="detail-desc">{model.description}</div>
      {exampleBlock}

      <div className="detail-cost">💰 Kosten: {baseCost} Credits</div>

      <div className="gen-options" id="model-input-block">
        <h3>✍️ {isText ? 'Eingabe (optional)' : 'Prompt'}</h3>
        <div className="gen-row">
          <label>{isText ? 'Prompt / erste Nachricht' : 'Prompt' + (schemaRequired.includes('prompt') ? ' *' : '')}</label>
          <textarea rows={isText ? 3 : 4} placeholder={promptPlaceholder} value={promptText} onChange={(e) => setPromptText(e.target.value)} />
        </div>
        <div className="gen-row">
          <button type="button" className="btn-secondary btn-optimize-paid" onClick={handleOptimizePaid} disabled={optimizing}>
            {optimizing ? '⏳ …' : '✨ Optimize (+3 ⭐)'}
          </button>
        </div>
        {!isText && hasNegativeInSchema ? (
          <div className="gen-row">
            <label>Negative prompt (optional)</label>
            <textarea rows={2} placeholder="Was vermeiden..." value={negativePromptText} onChange={(e) => setNegativePromptText(e.target.value)} />
          </div>
        ) : null}
      </div>

      {shouldShowGenBlock ? (
        <div className="gen-options" id="generation-options">
          <h3>⚙️ Generation Optionen</h3>

          {opt.duration && opt.duration.enabled ? (
            <div className="gen-row">
              <label>Duration</label>
              <select value={durationValue} onChange={(e) => setDuration(Number(e.target.value || 5))}>
                {durEnum.map((v) => (
                  <option value={v} key={v}>
                    {v}s
                  </option>
                ))}
              </select>
            </div>
          ) : null}

          {opt.reference_images && opt.reference_images.enabled ? (
            <div className="gen-row">
              <label>Reference Images (URLs oder Upload)</label>
              <div className="ref-upload-toolbar">
                <input
                  type="file"
                  multiple
                  style={{ position: 'absolute', width: 0, height: 0, opacity: 0, pointerEvents: 'none' }}
                  ref={referenceFileInputRef}
                  accept="image/jpeg,image/png,image/webp"
                  onChange={(e) => {
                    const files = e.target.files;
                    if (!files || !files.length) return;
                    handleUploadReferenceImages(Array.from(files));
                    e.target.value = '';
                  }}
                />
                <button type="button" className="btn-ref-upload" id="gen-reference-upload-btn" disabled={referenceUploading || submitting || optimizing} onClick={() => referenceFileInputRef.current?.click()}>
                  📎 Bilder hochladen
                </button>
                <span className="gen-hint" style={{ display: referenceUploadStatus ? 'inline' : 'none', margin: 0 }}>
                  {referenceUploadStatus}
                </span>
              </div>
              <textarea
                rows={2}
                placeholder={'https://...\noder URLs erscheinen nach Upload hier'}
                value={referenceImagesText}
                onChange={(e) => setReferenceImagesText(e.target.value)}
              />
            </div>
          ) : null}

          <details className="advanced-details" id="advanced-gen-settings">
            <summary>⚙️ Erweiterte Einstellungen</summary>

            {resEnum.length ? (
              <div className="gen-row">
                <label>Resolution</label>
                <select value={resolution} onChange={(e) => setResolution(e.target.value)}>
                  {resEnum.map((v, idx) => (
                    <option value={String(v)} key={idx}>
                      {String(v)}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            {ratioEnum.length ? (
              <div className="gen-row">
                <label>Aspect Ratio</label>
                <select value={aspectRatio} onChange={(e) => setAspectRatio(e.target.value)}>
                  {ratioEnum.map((v, idx) => (
                    <option value={String(v)} key={idx}>
                      {String(v)}
                    </option>
                  ))}
                </select>
              </div>
            ) : null}

            {opt.generate_audio && opt.generate_audio.enabled ? (
              <div className="gen-row">
                <label>Generate Audio</label>
                <select value={generateAudio ? 'true' : 'false'} onChange={(e) => setGenerateAudio(e.target.value === 'true')}>
                  <option value="true">true</option>
                  <option value="false">false</option>
                </select>
              </div>
            ) : null}

            {dynamicAdvancedKeys.map((k) => renderDynamicField(k))}
          </details>

          {dynamicMediaLikeKeys.map((k) => renderDynamicField(k))}

          <div className="detail-cost" style={{ marginTop: 12 }}>
            💰 Kosten: {computedCost} Credits
          </div>
        </div>
      ) : null}

      <div style={{ marginTop: 12 }}>
        {isText ? (
          <div className="chat-mode-btns">
            <button type="button" className="btn-start" disabled={submitting} onClick={() => handleSubmit(`chat_mode_yes_${model.key}`)}>
              ✅ Chat starten
            </button>
            <button type="button" className="btn-secondary" disabled={submitting} onClick={() => handleSubmit(`chat_mode_no_${model.key}`)}>
              ❌ Einmaliger Prompt
            </button>
          </div>
        ) : (
          <button type="button" className="btn-start" disabled={submitting} onClick={() => handleSubmit(`start_gen_${model.key}`)}>
            🚀 Start ({startButtonLabel})
          </button>
        )}
        {submitInfo ? <div className="submit-hint">{submitInfo}</div> : null}
      </div>
    </div>
  );
}

