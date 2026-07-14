const state = {
  mediaRecorder: null,
  chunks: [],
  recordingBlob: null,
  recordingUrl: null,
  startedAt: 0,
  timerId: null,
  meterId: null,
  audioContext: null,
  analyser: null,
  stream: null,
};

const els = {
  sourceLanguage: document.querySelector("#sourceLanguage"),
  targetLanguage: document.querySelector("#targetLanguage"),
  swapLanguages: document.querySelector("#swapLanguages"),
  recordButton: document.querySelector("#recordButton"),
  resetButton: document.querySelector("#resetButton"),
  recordTimer: document.querySelector("#recordTimer"),
  recordState: document.querySelector("#recordState"),
  recordingPreview: document.querySelector("#recordingPreview"),
  inputAudio: document.querySelector("#inputAudio"),
  translateRecording: document.querySelector("#translateRecording"),
  toggleUpload: document.querySelector("#toggleUpload"),
  uploadPanel: document.querySelector("#uploadPanel"),
  fileInput: document.querySelector("#fileInput"),
  selectedFileName: document.querySelector("#selectedFileName"),
  uploadHint: document.querySelector("#uploadHint"),
  translateUpload: document.querySelector("#translateUpload"),
  textMode: document.querySelector("#textMode"),
  textInput: document.querySelector("#textInput"),
  translateText: document.querySelector("#translateText"),
  modeTabs: document.querySelectorAll(".mode-tab"),
  recordMode: document.querySelector("#recordMode"),
  uploadMode: document.querySelector("#uploadMode"),
  progressPanel: document.querySelector("#progressPanel"),
  progressTitle: document.querySelector("#progressTitle"),
  progressPercent: document.querySelector("#progressPercent"),
  progressBar: document.querySelector("#progressBar"),
  progressCopy: document.querySelector("#progressCopy"),
  resultPanel: document.querySelector("#resultPanel"),
  resultTitle: document.querySelector("#resultTitle"),
  warningList: document.querySelector("#warningList"),
  outputAudio: document.querySelector("#outputAudio"),
  speakTranslation: document.querySelector("#speakTranslation"),
  downloadActions: document.querySelector("#downloadActions"),
  zipDownload: document.querySelector("#zipDownload"),
  originalText: document.querySelector("#originalText"),
  translatedText: document.querySelector("#translatedText"),
  errorPanel: document.querySelector("#errorPanel"),
  errorText: document.querySelector("#errorText"),
  meterCanvas: document.querySelector("#meterCanvas"),
  recordVisual: document.querySelector("#recordVisual"),
  healthChip: document.querySelector("#healthChip"),
  readinessList: document.querySelector("#readinessList"),
  recentCount: document.querySelector("#recentCount"),
  recentList: document.querySelector("#recentList"),
  outputSummary: document.querySelector("#outputSummary"),
  makeTts: document.querySelector("#makeTts"),
  makeSubtitles: document.querySelector("#makeSubtitles"),
  burnCaptions: document.querySelector("#burnCaptions"),
  mergeTranslatedAudio: document.querySelector("#mergeTranslatedAudio"),
};

const uploadLimits = {
  audio: {
    compressedMaxMb: 50,
    uncompressedMaxMb: 150,
    compressedExtensions: [".aac", ".m4a", ".mp3", ".ogg", ".wma"],
    uncompressedExtensions: [".flac", ".wav"],
  },
  video: { maxMb: 200, extensions: [".avi", ".flv", ".mkv", ".mov", ".mp4", ".webm", ".wmv"] },
  text: { maxMb: 10, extensions: [".md", ".text", ".txt"] },
  document: { maxMb: 50, extensions: [".csv", ".docx", ".pdf", ".pptx", ".tsv", ".xlsx"] },
};

const progressSteps = [
  "Preparing input",
  "Reading content",
  "Translating meaning",
  "Generating speech",
  "Packaging outputs",
];

const MAX_RECORDING_SECONDS = 30 * 60;

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, "0");
  const seconds = Math.floor(totalSeconds % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function setProgress(value, copy) {
  const bounded = Math.max(0, Math.min(100, value));
  els.progressBar.style.width = `${bounded}%`;
  els.progressPercent.textContent = `${Math.round(bounded)}%`;
  if (copy) els.progressCopy.textContent = copy;
}

function showError(message) {
  els.errorText.textContent = message;
  els.errorPanel.classList.remove("hidden");
  els.progressPanel.classList.add("hidden");
}

function clearError() {
  els.errorPanel.classList.add("hidden");
  els.errorText.textContent = "";
}

function setInputMode(mode) {
  const isUpload = mode === "upload";
  const isText = mode === "text";
  els.recordMode.classList.toggle("hidden", isUpload || isText);
  els.textMode.classList.toggle("hidden", !isText);
  els.uploadMode.classList.toggle("hidden", !isUpload);
  els.modeTabs.forEach((tab) => {
    const active = tab.dataset.mode === mode;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
  });
  clearError();
}

function languagesMatch() {
  return els.sourceLanguage.value === els.targetLanguage.value;
}

function validateLanguagePair() {
  if (els.sourceLanguage.value === "Auto detect") return "";
  if (!languagesMatch()) return "";
  return "Choose two different languages before translating.";
}

function mimeToExtension(mimeType) {
  if (mimeType.includes("ogg")) return "ogg";
  if (mimeType.includes("mp4")) return "m4a";
  if (mimeType.includes("mpeg")) return "mp3";
  if (mimeType.includes("wav")) return "wav";
  return "webm";
}

function supportedMimeType() {
  const candidates = [
    "audio/webm;codecs=opus",
    "audio/webm",
    "audio/ogg;codecs=opus",
    "audio/mp4",
  ];
  return candidates.find((type) => window.MediaRecorder?.isTypeSupported(type)) || "";
}

function fileExtension(filename) {
  const index = filename.lastIndexOf(".");
  return index >= 0 ? filename.slice(index).toLowerCase() : "";
}

function maxUploadMbForFile(file) {
  const extension = fileExtension(file.name);
  if (uploadLimits.audio.compressedExtensions.includes(extension)) return uploadLimits.audio.compressedMaxMb;
  if (uploadLimits.audio.uncompressedExtensions.includes(extension)) return uploadLimits.audio.uncompressedMaxMb;
  if (uploadLimits.video.extensions.includes(extension)) return uploadLimits.video.maxMb;
  if (uploadLimits.text.extensions.includes(extension)) return uploadLimits.text.maxMb;
  if (uploadLimits.document.extensions.includes(extension)) return uploadLimits.document.maxMb;
  return 0;
}

function isMediaFile(file) {
  const extension = fileExtension(file.name);
  return (
    uploadLimits.audio.compressedExtensions.includes(extension) ||
    uploadLimits.audio.uncompressedExtensions.includes(extension) ||
    uploadLimits.video.extensions.includes(extension)
  );
}

function isVideoFile(file) {
  return uploadLimits.video.extensions.includes(fileExtension(file.name));
}

function refreshOutputOptions(file = null) {
  const video = Boolean(file && isVideoFile(file));
  els.burnCaptions.disabled = !video;
  els.mergeTranslatedAudio.disabled = !video;
  if (!video) {
    els.burnCaptions.checked = false;
    els.mergeTranslatedAudio.checked = false;
  }
  const outputs = ["Translated text"];
  if (els.makeTts.checked) outputs.push("voice");
  if (els.makeSubtitles.checked) outputs.push("subtitles");
  if (els.burnCaptions.checked) outputs.push("captioned video");
  if (els.mergeTranslatedAudio.checked) outputs.push("translated-audio video");
  els.outputSummary.textContent = outputs.join(", ");
}

function validateSelectedFile(file) {
  const limitMb = maxUploadMbForFile(file);
  if (!limitMb) return "Unsupported file type.";
  const sizeMb = file.size / (1024 * 1024);
  if (sizeMb > limitMb) return `File is too large. Maximum allowed size is ${limitMb} MB.`;
  return "";
}

async function loadServerLimits() {
  try {
    const response = await fetch("/limits");
    if (!response.ok) return;
    const limits = await response.json();
    uploadLimits.audio.compressedMaxMb = limits.audio.compressed_max_mb;
    uploadLimits.audio.uncompressedMaxMb = limits.audio.uncompressed_max_mb;
    uploadLimits.audio.compressedExtensions = limits.audio.compressed_extensions;
    uploadLimits.audio.uncompressedExtensions = limits.audio.uncompressed_extensions;
    uploadLimits.video.maxMb = limits.video.max_mb;
    uploadLimits.video.extensions = limits.video.extensions;
    uploadLimits.text.maxMb = limits.text.max_mb;
    uploadLimits.text.extensions = limits.text.extensions;
    uploadLimits.document.maxMb = limits.document?.max_mb || uploadLimits.document.maxMb;
    uploadLimits.document.extensions = limits.document?.extensions || uploadLimits.document.extensions;
    els.uploadHint.textContent = "Audio up to 30 min. Video up to 15 min. TXT, PDF, DOCX, PPTX, XLSX, CSV.";
  } catch {
    // Static fallback limits above keep client validation useful if this request fails.
  }
}

function resetResult() {
  els.resultPanel.classList.add("hidden");
  els.outputAudio.removeAttribute("src");
  els.speakTranslation.classList.add("hidden");
  els.downloadActions.innerHTML = "";
  els.zipDownload.classList.add("hidden");
  els.warningList.classList.add("hidden");
  els.warningList.innerHTML = "";
  els.originalText.textContent = "";
  els.translatedText.textContent = "";
}

function resetRecording() {
  if (state.recordingUrl) URL.revokeObjectURL(state.recordingUrl);
  state.recordingBlob = null;
  state.recordingUrl = null;
  state.chunks = [];
  els.inputAudio.removeAttribute("src");
  els.recordingPreview.classList.add("hidden");
  els.resetButton.disabled = true;
  els.recordTimer.textContent = "00:00";
  els.recordState.textContent = "Ready";
  drawIdleMeter();
}

function drawIdleMeter() {
  const canvas = els.meterCanvas;
  const ctx = canvas.getContext("2d");
  const width = canvas.width;
  const height = canvas.height;
  ctx.clearRect(0, 0, width, height);
  for (let i = 0; i < 72; i += 1) {
    const x = (i / 72) * width;
    const barHeight = 16 + Math.sin(i * 0.7) * 10 + Math.cos(i * 0.19) * 18;
    ctx.fillStyle = i % 3 === 0 ? "rgba(22, 107, 104, 0.32)" : "rgba(237, 79, 67, 0.26)";
    ctx.fillRect(x, height / 2 - barHeight / 2, 7, barHeight);
  }
}

function drawLiveMeter() {
  if (!state.analyser) return;
  const canvas = els.meterCanvas;
  const ctx = canvas.getContext("2d");
  const data = new Uint8Array(state.analyser.frequencyBinCount);
  state.analyser.getByteFrequencyData(data);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const step = Math.max(1, Math.floor(data.length / 72));
  for (let i = 0; i < 72; i += 1) {
    const value = data[i * step] || 0;
    const barHeight = 18 + (value / 255) * 145;
    const x = (i / 72) * canvas.width;
    ctx.fillStyle = value > 90 ? "rgba(237, 79, 67, 0.78)" : "rgba(22, 107, 104, 0.66)";
    ctx.fillRect(x, canvas.height / 2 - barHeight / 2, 8, barHeight);
  }
  state.meterId = requestAnimationFrame(drawLiveMeter);
}

async function startRecording() {
  clearError();
  resetResult();
  resetRecording();

  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    showError("Recording is not available in this browser. Use the file option instead.");
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    state.stream = stream;
    state.audioContext = new AudioContext();
    state.analyser = state.audioContext.createAnalyser();
    state.analyser.fftSize = 512;
    state.audioContext.createMediaStreamSource(stream).connect(state.analyser);

    const mimeType = supportedMimeType();
    state.mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    state.chunks = [];
    state.mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) state.chunks.push(event.data);
    };
    state.mediaRecorder.onstop = onRecordingStop;
    state.mediaRecorder.start();

    state.startedAt = Date.now();
    state.timerId = window.setInterval(() => {
      const elapsed = (Date.now() - state.startedAt) / 1000;
      els.recordTimer.textContent = formatTime(elapsed);
      if (elapsed >= MAX_RECORDING_SECONDS) {
        stopRecording();
        els.recordState.textContent = "30 minute limit reached";
      }
    }, 250);
    els.recordButton.textContent = "Stop recording";
    els.recordButton.classList.add("recording");
    els.recordState.textContent = "Recording";
    drawLiveMeter();
  } catch (error) {
    showError(error.name === "NotAllowedError" ? "Microphone permission was blocked." : "Could not start recording.");
  }
}

function stopRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state !== "inactive") {
    state.mediaRecorder.stop();
  }
}

function onRecordingStop() {
  window.clearInterval(state.timerId);
  window.cancelAnimationFrame(state.meterId);
  state.stream?.getTracks().forEach((track) => track.stop());
  state.audioContext?.close();
  state.stream = null;
  state.audioContext = null;
  state.analyser = null;

  const type = state.mediaRecorder?.mimeType || "audio/webm";
  state.recordingBlob = new Blob(state.chunks, { type });
  state.recordingUrl = URL.createObjectURL(state.recordingBlob);
  els.inputAudio.src = state.recordingUrl;
  els.recordingPreview.classList.remove("hidden");
  els.resetButton.disabled = false;
  els.recordButton.textContent = "Record again";
  els.recordButton.classList.remove("recording");
  els.recordState.textContent = "Voice note captured";
  drawIdleMeter();
}

function beginProgress(inputLabel) {
  els.progressPanel.classList.remove("hidden");
  const label =
    inputLabel === "file"
      ? "Uploading your file."
      : inputLabel === "text"
        ? "Preparing your text."
        : "Uploading your recording.";
  setProgress(7, label);
}

async function waitForJob(statusUrl) {
  while (true) {
    const response = await fetch(statusUrl, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not read translation status.");
    setProgress((payload.progress || 0) * 100, payload.message || "Processing...");
    if (payload.status === "succeeded") return payload.result;
    if (payload.status === "failed") throw new Error(payload.error || "Translation could not be completed.");
    await new Promise((resolve) => window.setTimeout(resolve, 800));
  }
}

async function submitJob(url, options) {
  const response = await fetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Translation could not be queued.");
  return waitForJob(payload.status_url);
}

function artifactMap(artifacts) {
  return Object.fromEntries(artifacts.map((artifact) => [artifact.key, artifact]));
}

function artifactUrl(artifact) {
  return artifact.download_url;
}

function artifactDownloadUrl(jobId, artifactKey) {
  return `/jobs/${jobId}/artifacts/${artifactKey}`;
}

function renderDownloads(artifacts) {
  const labels = {
    tts_mp3: "MP3",
    tts_wav: "WAV",
    captioned_video: "Captioned video",
    translated_video: "Translated-audio video",
    translated_txt: "Text",
    translated_markdown: "Markdown",
    translated_table: "Table",
    source_txt: "Source",
    srt: "SRT",
    vtt: "VTT",
    job_report: "Details",
  };
  els.downloadActions.innerHTML = "";
  ["tts_mp3", "tts_wav", "captioned_video", "translated_video", "translated_txt", "translated_markdown", "translated_table", "source_txt", "srt", "vtt", "job_report"].forEach((key) => {
    if (!artifacts[key]) return;
    const link = document.createElement("a");
    link.className = "download-pill";
    link.href = artifactUrl(artifacts[key]);
    link.download = artifacts[key].filename;
    link.textContent = labels[key];
    els.downloadActions.appendChild(link);
  });
}

function renderWarnings(warnings) {
  els.warningList.innerHTML = "";
  if (!warnings?.length) {
    els.warningList.classList.add("hidden");
    return;
  }
  warnings.forEach((warning) => {
    const item = document.createElement("p");
    item.textContent = warning;
    els.warningList.appendChild(item);
  });
  els.warningList.classList.remove("hidden");
}

function renderResult(payload) {
  els.progressPanel.classList.add("hidden");
  const artifacts = artifactMap(payload.artifacts || []);
  const voice = artifacts.tts_mp3 || artifacts.tts_wav;
  if (voice) {
    els.outputAudio.src = artifactUrl(voice);
    els.outputAudio.classList.remove("hidden");
    els.speakTranslation.classList.add("hidden");
  } else {
    els.outputAudio.classList.add("hidden");
    els.speakTranslation.classList.remove("hidden");
  }
  if (artifacts.bundle_zip) {
    els.zipDownload.href = artifactUrl(artifacts.bundle_zip);
    els.zipDownload.download = artifacts.bundle_zip.filename;
    els.zipDownload.classList.remove("hidden");
  }
  els.resultTitle.textContent = `${payload.source_language} to ${payload.target_language}`;
  els.originalText.textContent = payload.original_text || "No transcript returned.";
  els.translatedText.textContent = payload.translated_text || "No translation returned.";
  renderWarnings(payload.warnings || []);
  renderDownloads(artifacts);
  els.resultPanel.classList.remove("hidden");
  loadHistory();
}

function renderHistory(items) {
  els.recentList.innerHTML = "";
  els.recentCount.textContent = `${items.length} saved`;
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "recent-empty";
    empty.textContent = "Completed translations will appear here.";
    els.recentList.appendChild(empty);
    return;
  }
  items.slice(0, 6).forEach((item) => {
    const row = document.createElement("article");
    row.className = "recent-item";

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `${item.source_language} to ${item.target_language}`;
    const meta = document.createElement("span");
    meta.textContent = `${item.input_type} · ${new Date(item.created_at).toLocaleString()}`;
    copy.append(title, meta);
    row.appendChild(copy);

    if (item.artifacts?.bundle_zip) {
      const link = document.createElement("a");
      link.className = "download-pill";
      link.href = artifactDownloadUrl(item.job_id, "bundle_zip");
      link.download = "vaanisetu_outputs.zip";
      link.textContent = "Package";
      row.appendChild(link);
    }
    els.recentList.appendChild(row);
  });
}

async function loadHistory() {
  try {
    const response = await fetch("/history?limit=6");
    if (!response.ok) return;
    const payload = await response.json();
    renderHistory(payload.items || []);
  } catch {
    renderHistory([]);
  }
}

function renderReadiness(checks) {
  els.readinessList.innerHTML = "";
  const importantChecks = checks.filter((check) =>
    [
      "Model quality profile",
      "FFmpeg",
      "faster-whisper package",
      "Whisper model",
      "Local translation route",
      "NLLB local translation",
      "NLLB optimized CPU runtime",
      "PDF text extraction",
      "Automatic OCR",
      "eSpeak NG",
      "Local speech fallback",
    ].includes(check.name)
  );
  importantChecks.slice(0, 9).forEach((check) => {
    const row = document.createElement("div");
    row.className = "readiness-item";

    const dot = document.createElement("span");
    dot.className = `readiness-dot${check.ok ? " ok" : ""}`;
    dot.setAttribute("aria-hidden", "true");

    const copy = document.createElement("div");
    const title = document.createElement("p");
    title.textContent = check.name;
    const detail = document.createElement("span");
    detail.textContent = check.detail;
    copy.append(title, detail);
    row.append(dot, copy);
    els.readinessList.appendChild(row);
  });
}

async function loadHealth() {
  try {
    const response = await fetch("/health?allow_model_download=false");
    if (!response.ok) throw new Error("Health request failed");
    const payload = await response.json();
    const operationalReady = payload.ok && payload.portable_speech_ready;
    els.healthChip.textContent = payload.production_ready
      ? "Production ready"
      : operationalReady
        ? "Ready to translate"
        : "Needs setup";
    els.healthChip.classList.toggle("ready", operationalReady);
    els.healthChip.classList.toggle("attention", !operationalReady);
    renderReadiness(payload.checks || []);
  } catch {
    els.healthChip.textContent = "Unavailable";
    els.healthChip.classList.add("attention");
    els.readinessList.innerHTML = "";
    const row = document.createElement("div");
    row.className = "readiness-item";
    row.innerHTML = '<span class="readiness-dot"></span><div><p>Backend health</p><span>Start the API server to see model readiness.</span></div>';
    els.readinessList.appendChild(row);
  }
}

function bestSpeechVoice(languageName) {
  const targetLang = {
    English: "en",
    Hindi: "hi",
    Marathi: "mr",
  }[languageName] || "en";
  const voices = window.speechSynthesis?.getVoices?.() || [];
  const normalizedTarget = targetLang.toLowerCase();
  return (
    voices.find((voice) => voice.lang?.toLowerCase().startsWith(`${normalizedTarget}-`)) ||
    voices.find((voice) => voice.lang?.toLowerCase() === normalizedTarget) ||
    voices.find((voice) => targetLang === "mr" && voice.name?.toLowerCase().includes("lekha")) ||
    voices.find((voice) => targetLang === "hi" && voice.name?.toLowerCase().includes("lekha")) ||
    voices.find((voice) => voice.lang?.toLowerCase().startsWith("en-in")) ||
    voices[0]
  );
}

async function processBlob(blob, filename, inputLabel = "voice note") {
  clearError();
  if (els.sourceLanguage.value === "Auto detect" && (inputLabel === "voice note" || isMediaFile({ name: filename }))) {
    showError("For audio/video, choose the spoken source language for best transcription accuracy.");
    return;
  }
  const languageError = validateLanguagePair();
  if (languageError) {
    showError(languageError);
    return;
  }
  resetResult();
  beginProgress(inputLabel);
  els.translateRecording.disabled = true;
  els.translateUpload.disabled = true;

  const form = new FormData();
  form.append("file", blob, filename);
  form.append("source_language", els.sourceLanguage.value);
  form.append("target_language", els.targetLanguage.value);
  form.append("make_subtitles", String(els.makeSubtitles.checked));
  form.append("make_tts", String(els.makeTts.checked));
  form.append("burn_captions", String(els.burnCaptions.checked));
  form.append("merge_translated_audio", String(els.mergeTranslatedAudio.checked));
  form.append("allow_preview_translation", "false");
  form.append("allow_model_download", "false");

  try {
    const payload = await submitJob("/jobs/file", { method: "POST", body: form });
    setProgress(100, "Your translation is ready.");
    renderResult(payload);
  } catch (error) {
    showError(error.message || "Translation failed.");
  } finally {
    els.translateRecording.disabled = false;
    els.translateUpload.disabled = !els.fileInput.files.length;
  }
}

async function processTextInput() {
  clearError();
  const text = els.textInput.value.trim();
  if (!text) {
    showError("Paste or type text to translate.");
    return;
  }
  const languageError = validateLanguagePair();
  if (languageError) {
    showError(languageError);
    return;
  }
  resetResult();
  beginProgress("text");
  els.translateText.disabled = true;

  try {
    const payload = await submitJob("/jobs/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        source_language: els.sourceLanguage.value,
        target_language: els.targetLanguage.value,
        make_subtitles: els.makeSubtitles.checked,
        make_tts: els.makeTts.checked,
        allow_preview_translation: false,
        allow_model_download: false,
      }),
    });
    setProgress(100, "Your translation is ready.");
    renderResult(payload);
  } catch (error) {
    showError(error.message || "Translation failed.");
  } finally {
    els.translateText.disabled = false;
  }
}

els.recordButton.addEventListener("click", () => {
  if (state.mediaRecorder?.state === "recording") stopRecording();
  else startRecording();
});

els.resetButton.addEventListener("click", () => {
  resetRecording();
  resetResult();
  clearError();
});

els.translateRecording.addEventListener("click", () => {
  if (!state.recordingBlob) {
    showError("Record a voice note first.");
    return;
  }
  const extension = mimeToExtension(state.recordingBlob.type || "");
  processBlob(state.recordingBlob, `voice-note.${extension}`, "voice note");
});

els.toggleUpload.addEventListener("click", () => {
  setInputMode("upload");
});

els.modeTabs.forEach((tab) => {
  tab.addEventListener("click", () => setInputMode(tab.dataset.mode));
});

els.translateText.addEventListener("click", processTextInput);

els.fileInput.addEventListener("change", () => {
  clearError();
  const file = els.fileInput.files[0];
  refreshOutputOptions(file || null);
  if (!file) {
    els.translateUpload.disabled = true;
    els.selectedFileName.textContent = "Choose a file";
    return;
  }
  els.selectedFileName.textContent = file.name;
  const error = validateSelectedFile(file);
  if (error) {
    showError(error);
    els.translateUpload.disabled = true;
    return;
  }
  if (els.sourceLanguage.value === "Auto detect" && isMediaFile(file)) {
    showError("For audio/video, choose the spoken source language for best transcription accuracy.");
    els.translateUpload.disabled = true;
    return;
  }
  els.translateUpload.disabled = false;
});

els.translateUpload.addEventListener("click", () => {
  const file = els.fileInput.files[0];
  if (file) processBlob(file, file.name, "file");
});

[els.makeTts, els.makeSubtitles, els.burnCaptions, els.mergeTranslatedAudio].forEach((control) => {
  control.addEventListener("change", () => refreshOutputOptions(els.fileInput.files[0] || null));
});

els.swapLanguages.addEventListener("click", () => {
  const source = els.sourceLanguage.value;
  if (source === "Auto detect") {
    els.sourceLanguage.value = els.targetLanguage.value;
    els.targetLanguage.value = "English";
    clearError();
    return;
  }
  els.sourceLanguage.value = els.targetLanguage.value;
  els.targetLanguage.value = source;
  clearError();
});

els.sourceLanguage.addEventListener("change", () => {
  clearError();
  const file = els.fileInput.files[0];
  if (file && els.sourceLanguage.value === "Auto detect" && isMediaFile(file)) {
    showError("For audio/video, choose the spoken source language for best transcription accuracy.");
    els.translateUpload.disabled = true;
    return;
  }
  if (file && !validateSelectedFile(file)) {
    els.translateUpload.disabled = false;
  }
});

els.speakTranslation.addEventListener("click", () => {
  if (!("speechSynthesis" in window)) {
    showError("Speech playback is not available in this browser.");
    return;
  }
  const text = els.translatedText.textContent.trim();
  if (!text) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = {
    English: "en-IN",
    Hindi: "hi-IN",
    Marathi: "mr-IN",
  }[els.targetLanguage.value] || "en-IN";
  const voice = bestSpeechVoice(els.targetLanguage.value);
  if (voice) {
    utterance.voice = voice;
    utterance.lang = voice.lang || utterance.lang;
  }
  utterance.rate = 0.92;
  window.speechSynthesis.speak(utterance);
});

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

loadServerLimits();
loadHealth();
loadHistory();
drawIdleMeter();
refreshOutputOptions();
