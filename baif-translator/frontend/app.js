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
  translateUpload: document.querySelector("#translateUpload"),
  progressPanel: document.querySelector("#progressPanel"),
  progressTitle: document.querySelector("#progressTitle"),
  progressPercent: document.querySelector("#progressPercent"),
  progressBar: document.querySelector("#progressBar"),
  progressCopy: document.querySelector("#progressCopy"),
  resultPanel: document.querySelector("#resultPanel"),
  resultTitle: document.querySelector("#resultTitle"),
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
};

const progressSteps = [
  "Preparing audio",
  "Transcribing speech",
  "Translating meaning",
  "Generating voice",
  "Packaging outputs",
];

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

function resetResult() {
  els.resultPanel.classList.add("hidden");
  els.outputAudio.removeAttribute("src");
  els.speakTranslation.classList.add("hidden");
  els.downloadActions.innerHTML = "";
  els.zipDownload.classList.add("hidden");
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
  els.recordState.textContent = "Ready to record";
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
      els.recordTimer.textContent = formatTime((Date.now() - state.startedAt) / 1000);
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

function beginFakeProgress(inputLabel) {
  els.progressPanel.classList.remove("hidden");
  setProgress(7, `Uploading your ${inputLabel}.`);
  let index = 0;
  return window.setInterval(() => {
    const next = Math.min(88, 18 + index * 17);
    setProgress(next, progressSteps[Math.min(index, progressSteps.length - 1)]);
    index += 1;
  }, 1800);
}

function artifactMap(artifacts) {
  return Object.fromEntries(artifacts.map((artifact) => [artifact.key, artifact]));
}

function artifactUrl(artifact) {
  return artifact.download_url;
}

function renderDownloads(artifacts) {
  const labels = {
    tts_mp3: "MP3",
    tts_wav: "WAV",
    translated_txt: "Text",
    srt: "SRT",
    vtt: "VTT",
  };
  els.downloadActions.innerHTML = "";
  ["tts_mp3", "tts_wav", "translated_txt", "srt", "vtt"].forEach((key) => {
    if (!artifacts[key]) return;
    const link = document.createElement("a");
    link.className = "download-pill";
    link.href = artifactUrl(artifacts[key]);
    link.download = artifacts[key].filename;
    link.textContent = labels[key];
    els.downloadActions.appendChild(link);
  });
}

function renderResult(payload) {
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
  renderDownloads(artifacts);
  els.resultPanel.classList.remove("hidden");
}

async function processBlob(blob, filename, inputLabel = "voice note") {
  clearError();
  resetResult();
  const progressId = beginFakeProgress(inputLabel);
  els.translateRecording.disabled = true;
  els.translateUpload.disabled = true;

  const form = new FormData();
  form.append("file", blob, filename);
  form.append("source_language", els.sourceLanguage.value);
  form.append("target_language", els.targetLanguage.value);
  form.append("make_subtitles", "true");
  form.append("make_tts", "true");
  form.append("burn_captions", "false");
  form.append("merge_translated_audio", "false");
  form.append("allow_model_download", "true");

  try {
    const response = await fetch("/translate/file", { method: "POST", body: form });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Translation failed.");
    }
    window.clearInterval(progressId);
    setProgress(100, "Your translation is ready.");
    renderResult(payload);
  } catch (error) {
    window.clearInterval(progressId);
    showError(error.message || "Translation failed.");
  } finally {
    els.translateRecording.disabled = false;
    els.translateUpload.disabled = !els.fileInput.files.length;
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
  els.uploadPanel.classList.toggle("hidden");
});

els.fileInput.addEventListener("change", () => {
  els.translateUpload.disabled = !els.fileInput.files.length;
});

els.translateUpload.addEventListener("click", () => {
  const file = els.fileInput.files[0];
  if (file) processBlob(file, file.name, "file");
});

els.swapLanguages.addEventListener("click", () => {
  const source = els.sourceLanguage.value;
  els.sourceLanguage.value = els.targetLanguage.value;
  els.targetLanguage.value = source;
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
  window.speechSynthesis.speak(utterance);
});

drawIdleMeter();
