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
  auth: {
    user: null,
    csrfToken: "",
    mode: "login",
  },
  currentJobId: "",
  currentQueueJobId: "",
  currentReviewVersion: null,
  impactData: null,
  batchRunning: false,
  batchCancelRequested: false,
  glossaryTimer: null,
  onboarding: {
    systemReady: false,
    hasCompletedJob: false,
  },
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
  cancelJob: document.querySelector("#cancelJob"),
  resultPanel: document.querySelector("#resultPanel"),
  resultTitle: document.querySelector("#resultTitle"),
  warningList: document.querySelector("#warningList"),
  outputAudio: document.querySelector("#outputAudio"),
  speakTranslation: document.querySelector("#speakTranslation"),
  downloadActions: document.querySelector("#downloadActions"),
  zipDownload: document.querySelector("#zipDownload"),
  originalText: document.querySelector("#originalText"),
  translatedText: document.querySelector("#translatedText"),
  correctedText: document.querySelector("#correctedText"),
  saveCorrection: document.querySelector("#saveCorrection"),
  approveCorrection: document.querySelector("#approveCorrection"),
  reviewStatus: document.querySelector("#reviewStatus"),
  reviewMessage: document.querySelector("#reviewMessage"),
  retryJob: document.querySelector("#retryJob"),
  deleteJob: document.querySelector("#deleteJob"),
  errorPanel: document.querySelector("#errorPanel"),
  errorText: document.querySelector("#errorText"),
  meterCanvas: document.querySelector("#meterCanvas"),
  recordVisual: document.querySelector("#recordVisual"),
  healthChip: document.querySelector("#healthChip"),
  readinessList: document.querySelector("#readinessList"),
  recentCount: document.querySelector("#recentCount"),
  recentList: document.querySelector("#recentList"),
  librarySearch: document.querySelector("#librarySearch"),
  outputSummary: document.querySelector("#outputSummary"),
  makeTts: document.querySelector("#makeTts"),
  makeSubtitles: document.querySelector("#makeSubtitles"),
  burnCaptions: document.querySelector("#burnCaptions"),
  mergeTranslatedAudio: document.querySelector("#mergeTranslatedAudio"),
  authPanel: document.querySelector("#authPanel"),
  authTitle: document.querySelector("#authTitle"),
  authCopy: document.querySelector("#authCopy"),
  authForm: document.querySelector("#authForm"),
  authUsername: document.querySelector("#authUsername"),
  authDisplayName: document.querySelector("#authDisplayName"),
  authPassword: document.querySelector("#authPassword"),
  authPasswordHint: document.querySelector("#authPasswordHint"),
  authSubmit: document.querySelector("#authSubmit"),
  authSwitch: document.querySelector("#authSwitch"),
  authMessage: document.querySelector("#authMessage"),
  userBadge: document.querySelector("#userBadge"),
  logoutButton: document.querySelector("#logoutButton"),
  adminPanel: document.querySelector("#adminPanel"),
  adminUserCount: document.querySelector("#adminUserCount"),
  adminUserList: document.querySelector("#adminUserList"),
  batchSummary: document.querySelector("#batchSummary"),
  batchTitle: document.querySelector("#batchTitle"),
  batchCount: document.querySelector("#batchCount"),
  batchList: document.querySelector("#batchList"),
  trustBackend: document.querySelector("#trustBackend"),
  trustProfile: document.querySelector("#trustProfile"),
  trustTiming: document.querySelector("#trustTiming"),
  trustReview: document.querySelector("#trustReview"),
  impactPanel: document.querySelector("#impactPanel"),
  impactHeadline: document.querySelector("#impactHeadline"),
  impactGrid: document.querySelector("#impactGrid"),
  impactDirections: document.querySelector("#impactDirections"),
  impactPrivacy: document.querySelector("#impactPrivacy"),
  exportImpact: document.querySelector("#exportImpact"),
  journeyTranslate: document.querySelector("#journeyTranslate"),
  journeyReview: document.querySelector("#journeyReview"),
  journeyOffline: document.querySelector("#journeyOffline"),
  glossaryInsight: document.querySelector("#glossaryInsight"),
  diffBox: document.querySelector("#diffBox"),
  diffSummary: document.querySelector("#diffSummary"),
  machineDiff: document.querySelector("#machineDiff"),
  correctedDiff: document.querySelector("#correctedDiff"),
  onboardingPanel: document.querySelector("#onboardingPanel"),
  onboardingProgress: document.querySelector("#onboardingProgress"),
  onboardingSystem: document.querySelector("#onboardingSystem"),
  onboardingSystemCopy: document.querySelector("#onboardingSystemCopy"),
  onboardingAccess: document.querySelector("#onboardingAccess"),
  onboardingAccessCopy: document.querySelector("#onboardingAccessCopy"),
  onboardingFirstJob: document.querySelector("#onboardingFirstJob"),
  onboardingFirstJobCopy: document.querySelector("#onboardingFirstJobCopy"),
  onboardingNext: document.querySelector("#onboardingNext"),
  systemPanel: document.querySelector(".system-panel"),
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

function setAuthMessage(message, isError = false) {
  els.authMessage.textContent = message || "";
  els.authMessage.classList.toggle("error", Boolean(isError));
}

function setAuthMode(mode) {
  state.auth.mode = mode;
  setAuthMessage("");
  els.authPassword.value = "";
  els.authDisplayName.closest("label").classList.toggle("hidden", mode === "login");
  if (mode === "setup") {
    els.authTitle.textContent = "Create the first admin";
    els.authCopy.textContent = "Set up the first local admin before any BAIF content can be processed.";
    els.authSubmit.textContent = "Create admin";
    els.authSwitch.classList.add("hidden");
    els.authPassword.autocomplete = "new-password";
    els.authPasswordHint.textContent = "Use at least 10 characters and keep this administrator password private.";
    return;
  }
  if (mode === "register") {
    els.authTitle.textContent = "Request access";
    els.authCopy.textContent = "An admin must approve the account before it can translate or download content.";
    els.authSubmit.textContent = "Request access";
    els.authSwitch.textContent = "Back to sign in";
    els.authSwitch.classList.remove("hidden");
    els.authPassword.autocomplete = "new-password";
    els.authPasswordHint.textContent = "Use at least 10 characters. You will sign in after an administrator approves the account.";
    return;
  }
  els.authTitle.textContent = "Sign in";
  els.authCopy.textContent = "Use your approved VaaniSetu account to process or download content.";
  els.authSubmit.textContent = "Sign in";
  els.authSwitch.textContent = "Request access";
  els.authSwitch.classList.remove("hidden");
  els.authPassword.autocomplete = "current-password";
  els.authPasswordHint.textContent = "Use your approved VaaniSetu account password.";
}

function setOnboardingItem(element, complete) {
  element.classList.toggle("complete", complete);
  const marker = element.querySelector(".onboarding-check");
  marker.textContent = complete ? "✓" : marker.dataset.step;
}

function renderOnboarding() {
  if (!state.auth.user || !els.onboardingPanel) return;
  const accessReady = state.auth.user.status === "active";
  const completed = [state.onboarding.systemReady, accessReady, state.onboarding.hasCompletedJob];
  const completeCount = completed.filter(Boolean).length;

  setOnboardingItem(els.onboardingSystem, state.onboarding.systemReady);
  setOnboardingItem(els.onboardingAccess, accessReady);
  setOnboardingItem(els.onboardingFirstJob, state.onboarding.hasCompletedJob);
  els.onboardingSystemCopy.textContent = state.onboarding.systemReady
    ? "Local translation is available."
    : "An administrator must complete the named System setup action.";
  els.onboardingAccessCopy.textContent = state.auth.user.role === "admin"
    ? "Administrator account is active. Approve trainers under User approvals."
    : "Your account is approved and ready to translate.";
  els.onboardingFirstJobCopy.textContent = state.onboarding.hasCompletedJob
    ? "A completed translation is available in the reusable library."
    : "Start with a short text, review it, then download the offline package.";
  els.onboardingProgress.textContent = completeCount === 3 ? "Ready" : `${completeCount} of 3 ready`;
  els.onboardingProgress.classList.toggle("ready", completeCount === 3);
  els.onboardingProgress.classList.toggle("attention", completeCount < 3);

  if (!els.onboardingPanel.dataset.initialized) {
    els.onboardingPanel.open = completeCount < 3;
    els.onboardingPanel.dataset.initialized = "true";
  }
  if (!state.onboarding.systemReady) {
    els.onboardingNext.textContent = "View system setup";
    els.onboardingNext.disabled = false;
  } else if (!state.onboarding.hasCompletedJob) {
    els.onboardingNext.textContent = "Start first translation";
    els.onboardingNext.disabled = false;
  } else if (state.auth.user.role === "admin") {
    els.onboardingNext.textContent = "Review user approvals";
    els.onboardingNext.disabled = false;
  } else {
    els.onboardingNext.textContent = "Onboarding complete";
    els.onboardingNext.disabled = true;
  }
}

function showWorkspace(user) {
  document.querySelectorAll("[data-auth-required]").forEach((element) => element.classList.remove("hidden"));
  els.authPanel.classList.add("hidden");
  els.userBadge.textContent = `${user.display_name || user.username} · ${user.role === "admin" ? "Admin" : "Authorised user"}`;
  els.userBadge.classList.remove("hidden");
  els.logoutButton.classList.remove("hidden");
  els.adminPanel.classList.toggle("hidden", user.role !== "admin");
  if (user.role === "admin") loadUsers();
  renderOnboarding();
  loadHistory();
  loadImpact();
}

function showAuthPanel(mode) {
  document.querySelectorAll("[data-auth-required]").forEach((element) => element.classList.add("hidden"));
  els.adminPanel.classList.add("hidden");
  els.userBadge.classList.add("hidden");
  els.logoutButton.classList.add("hidden");
  els.authPanel.classList.remove("hidden");
  setAuthMode(mode);
}

async function apiFetch(url, options = {}) {
  const method = (options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});
  if (!["GET", "HEAD", "OPTIONS"].includes(method) && state.auth.csrfToken) {
    headers.set("X-CSRF-Token", state.auth.csrfToken);
  }
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
  });
  if (response.status === 401 || response.status === 403) {
    if (!url.startsWith("/auth/")) {
      state.auth.user = null;
      state.auth.csrfToken = "";
      showAuthPanel("login");
    }
  }
  return response;
}

async function loadSession() {
  try {
    const response = await apiFetch("/auth/session", { cache: "no-store" });
    const payload = await response.json();
    state.auth.user = payload.user || null;
    state.auth.csrfToken = payload.csrf_token || "";
    if (payload.user) {
      showWorkspace(payload.user);
    } else {
      showAuthPanel(payload.setup_required ? "setup" : "login");
    }
  } catch {
    showAuthPanel("login");
    setAuthMessage("Could not reach the local worker.", true);
  }
}

async function submitAuth(event) {
  event.preventDefault();
  setAuthMessage("");
  const body = {
    username: els.authUsername.value.trim(),
    password: els.authPassword.value,
    display_name: els.authDisplayName.value.trim(),
  };
  const endpoint = {
    setup: "/auth/setup",
    register: "/auth/register",
    login: "/auth/login",
  }[state.auth.mode];

  els.authSubmit.disabled = true;
  try {
    const response = await apiFetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Access request failed.");
    if (state.auth.mode === "register") {
      setAuthMode("login");
      setAuthMessage("Access requested. An admin must approve this account.");
      return;
    }
    state.auth.user = payload.user;
    state.auth.csrfToken = payload.csrf_token || "";
    els.authForm.reset();
    showWorkspace(payload.user);
  } catch (error) {
    setAuthMessage(error.message || "Access request failed.", true);
  } finally {
    els.authSubmit.disabled = false;
  }
}

async function logout() {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } finally {
    state.auth.user = null;
    state.auth.csrfToken = "";
    resetResult();
    showAuthPanel("login");
  }
}

function renderUsers(users) {
  els.adminUserList.innerHTML = "";
  els.adminUserCount.textContent = `${users.length} users`;
  users.forEach((user) => {
    const row = document.createElement("article");
    row.className = "admin-user";

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = user.display_name ? `${user.display_name} (${user.username})` : user.username;
    const meta = document.createElement("span");
    meta.textContent = `${user.role} · ${user.status}`;
    copy.append(title, meta);

    const actions = document.createElement("div");
    actions.className = "admin-user-actions";
    if (user.status === "pending") {
      const approve = document.createElement("button");
      approve.className = "translate-action";
      approve.type = "button";
      approve.textContent = "Approve";
      approve.addEventListener("click", () => updateUser(user.username, "approve"));
      actions.appendChild(approve);
    }
    if (user.status === "active" && user.username !== state.auth.user?.username) {
      const deactivate = document.createElement("button");
      deactivate.className = "secondary-action";
      deactivate.type = "button";
      deactivate.textContent = "Deactivate";
      deactivate.addEventListener("click", () => updateUser(user.username, "deactivate"));
      actions.appendChild(deactivate);
    }
    row.append(copy, actions);
    els.adminUserList.appendChild(row);
  });
}

async function loadUsers() {
  if (state.auth.user?.role !== "admin") return;
  try {
    const response = await apiFetch("/auth/users", { cache: "no-store" });
    if (!response.ok) return;
    renderUsers(await response.json());
  } catch {
    // The admin panel is supplemental; sign-in protection remains server-side.
  }
}

async function updateUser(username, action) {
  try {
    const response = await apiFetch(`/auth/users/${encodeURIComponent(username)}/${action}`, { method: "POST" });
    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.detail || "Could not update user.");
    }
    loadUsers();
  } catch (error) {
    setAuthMessage(error.message || "Could not update user.", true);
  }
}

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
    tab.tabIndex = active ? 0 : -1;
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

function setJourney(stage) {
  const order = [els.journeyTranslate, els.journeyReview, els.journeyOffline];
  const activeIndex = { translate: 0, review: 1, offline: 2 }[stage] ?? 0;
  order.forEach((item, index) => {
    item.classList.toggle("active", index === activeIndex);
    item.classList.toggle("complete", index < activeIndex);
    if (index === activeIndex) item.setAttribute("aria-current", "step");
    else item.removeAttribute("aria-current");
  });
}

function appendDiffWords(container, words, changedIndexes) {
  container.innerHTML = "";
  words.forEach((word, index) => {
    const node = changedIndexes.has(index) ? document.createElement("mark") : document.createElement("span");
    node.textContent = word;
    container.appendChild(node);
    if (index < words.length - 1) container.appendChild(document.createTextNode(" "));
  });
}

function renderCorrectionDiff() {
  const originalWords = (els.translatedText.textContent || "").trim().split(/\s+/).filter(Boolean);
  const correctedWords = (els.correctedText.value || "").trim().split(/\s+/).filter(Boolean);
  const removed = new Set();
  const added = new Set();
  if (!originalWords.length && !correctedWords.length) {
    els.diffSummary.textContent = "No correction changes yet";
    els.machineDiff.textContent = "";
    els.correctedDiff.textContent = "";
    return;
  }
  if (originalWords.length * correctedWords.length <= 90000) {
    const matrix = Array.from({ length: originalWords.length + 1 }, () => new Uint16Array(correctedWords.length + 1));
    for (let i = originalWords.length - 1; i >= 0; i -= 1) {
      for (let j = correctedWords.length - 1; j >= 0; j -= 1) {
        matrix[i][j] = originalWords[i] === correctedWords[j] ? matrix[i + 1][j + 1] + 1 : Math.max(matrix[i + 1][j], matrix[i][j + 1]);
      }
    }
    let i = 0;
    let j = 0;
    while (i < originalWords.length || j < correctedWords.length) {
      if (i < originalWords.length && j < correctedWords.length && originalWords[i] === correctedWords[j]) {
        i += 1;
        j += 1;
      } else if (j < correctedWords.length && (i === originalWords.length || matrix[i][j + 1] >= matrix[i + 1][j])) {
        added.add(j);
        j += 1;
      } else {
        removed.add(i);
        i += 1;
      }
    }
  } else {
    originalWords.forEach((_word, index) => removed.add(index));
    correctedWords.forEach((_word, index) => added.add(index));
  }
  appendDiffWords(els.machineDiff, originalWords, removed);
  appendDiffWords(els.correctedDiff, correctedWords, added);
  const changes = removed.size + added.size;
  els.diffSummary.textContent = changes ? `${changes} word change${changes === 1 ? "" : "s"} highlighted` : "No correction changes yet";
}

async function loadGlossaryInsight() {
  const textValue = els.textInput.value.trim();
  if (textValue.length < 3 || !state.auth.user) {
    els.glossaryInsight.classList.add("hidden");
    els.glossaryInsight.innerHTML = "";
    return;
  }
  try {
    const response = await apiFetch("/glossary/coverage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: textValue, source_language: els.sourceLanguage.value, target_language: els.targetLanguage.value }),
    });
    if (!response.ok) throw new Error("Glossary check unavailable");
    const payload = await response.json();
    els.glossaryInsight.innerHTML = "";
    const heading = document.createElement("strong");
    heading.textContent = payload.matches?.length ? `${payload.matches.length} agriculture term${payload.matches.length === 1 ? "" : "s"} detected` : "No seeded agriculture terms detected";
    els.glossaryInsight.appendChild(heading);
    if (payload.matches?.length) {
      const list = document.createElement("div");
      list.className = "glossary-chips";
      payload.matches.forEach((match) => {
        const chip = document.createElement("span");
        chip.textContent = `${match.source_term} → ${match.target_term}`;
        list.appendChild(chip);
      });
      els.glossaryInsight.appendChild(list);
    }
    const note = document.createElement("small");
    note.textContent = `Glossary v${payload.version} · bilingual review remains required`;
    els.glossaryInsight.appendChild(note);
    els.glossaryInsight.classList.remove("hidden");
  } catch {
    els.glossaryInsight.classList.add("hidden");
  }
}

function scheduleGlossaryInsight() {
  window.clearTimeout(state.glossaryTimer);
  state.glossaryTimer = window.setTimeout(loadGlossaryInsight, 300);
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
  els.correctedText.value = "";
  els.reviewStatus.textContent = "Not approved";
  els.reviewMessage.textContent = "";
  els.trustBackend.textContent = "Checking";
  els.trustProfile.textContent = "Checking";
  els.trustTiming.textContent = "Available in details";
  els.trustReview.textContent = "Human review pending";
  state.currentJobId = "";
  state.currentQueueJobId = "";
  state.currentReviewVersion = null;
  setJourney("translate");
  renderCorrectionDiff();
}

function resetRecording() {
  if (state.recordingUrl) URL.revokeObjectURL(state.recordingUrl);
  state.stream?.getTracks().forEach((track) => track.stop());
  state.audioContext?.close();
  window.clearInterval(state.timerId);
  window.cancelAnimationFrame(state.meterId);
  state.stream = null;
  state.audioContext = null;
  state.analyser = null;
  state.mediaRecorder = null;
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
    state.stream?.getTracks().forEach((track) => track.stop());
    state.audioContext?.close();
    state.stream = null;
    state.audioContext = null;
    state.analyser = null;
    state.mediaRecorder = null;
    els.recordButton.textContent = "Start recording";
    els.recordButton.classList.remove("recording");
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
  if (!state.recordingBlob.size) {
    state.recordingBlob = null;
    state.mediaRecorder = null;
    els.recordButton.textContent = "Start recording";
    els.recordButton.classList.remove("recording");
    els.recordState.textContent = "No audio captured";
    showError("No audio was captured. Check the microphone and record again.");
    drawIdleMeter();
    return;
  }
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
    const response = await apiFetch(statusUrl, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not read translation status.");
    setProgress((payload.progress || 0) * 100, payload.message || "Processing...");
    if (payload.status === "succeeded") {
      payload.result.stage_timings = payload.stage_timings || {};
      return payload.result;
    }
    if (payload.status === "failed") throw new Error(payload.error || "Translation could not be completed.");
    if (payload.status === "cancelled") throw new Error("Translation was cancelled.");
    await new Promise((resolve) => window.setTimeout(resolve, 800));
  }
}

async function submitJob(url, options) {
  const response = await apiFetch(url, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || "Translation could not be queued.");
  state.currentQueueJobId = payload.job_id;
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
    approved_corrected_package: "Approved package",
  };
  els.downloadActions.innerHTML = "";
  Object.keys(artifacts)
    .filter((key) => key.startsWith("corrected_txt_v"))
    .sort()
    .forEach((key) => {
      labels[key] = `Correction ${key.replace("corrected_txt_v", "v")}`;
    });
  ["approved_corrected_package", "tts_mp3", "tts_wav", "captioned_video", "translated_video", "translated_txt", "translated_markdown", "translated_table", "source_txt", "srt", "vtt", "job_report", ...Object.keys(artifacts).filter((key) => key.startsWith("corrected_txt_v")).sort()].forEach((key) => {
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
  state.currentJobId = payload.job_id || "";
  state.currentReviewVersion = null;
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
  els.correctedText.value = payload.translated_text || "";
  setJourney("review");
  renderCorrectionDiff();
  els.reviewStatus.textContent = "Checking";
  els.reviewMessage.textContent = "";
  const metadata = payload.metadata || {};
  const backendLabels = {
    "approved-memory": "Approved human translation memory",
    "indictrans2-local": "Local IndicTrans2",
    "nllb-ct2-local": "Local NLLB · CPU optimised",
    "nllb-local": "Local NLLB",
  };
  els.trustBackend.textContent = backendLabels[metadata.translation_backend] || metadata.translation_backend || "Recorded in job details";
  els.trustProfile.textContent = metadata.model_profile || "Local worker";
  const totalSeconds = Number(payload.stage_timings?.total || 0);
  els.trustTiming.textContent = totalSeconds > 0 ? `${totalSeconds.toFixed(1)} seconds` : "Recorded in job details";
  els.trustReview.textContent = "Human review pending";
  renderWarnings(payload.warnings || []);
  renderDownloads(artifacts);
  els.resultPanel.classList.remove("hidden");
  loadReview(payload.job_id);
  loadHistory();
  loadImpact();
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
  items.slice(0, 10).forEach((item) => {
    const result = item.result || item;
    const row = document.createElement("article");
    row.className = "recent-item";

    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = `${result.source_language} to ${result.target_language}`;
    const meta = document.createElement("span");
    const createdAt = item.created_at || result.created_at || "";
    meta.textContent = `${result.input_type || item.kind} · ${item.status || "saved"}${createdAt ? ` · ${new Date(createdAt).toLocaleString()}` : ""}`;
    copy.append(title, meta);
    row.appendChild(copy);

    const actions = document.createElement("div");
    actions.className = "recent-actions";
    const review = document.createElement("button");
    review.className = "secondary-action compact";
    review.type = "button";
    review.textContent = "Review";
    review.addEventListener("click", () => openLibraryJob(item.job_id || result.job_id));
    actions.appendChild(review);
    if (["succeeded", "failed", "cancelled"].includes(item.status)) {
      const remove = document.createElement("button");
      remove.className = "secondary-action compact";
      remove.type = "button";
      remove.textContent = "Delete";
      remove.addEventListener("click", () => deleteSavedJob(item.job_id || result.job_id));
      actions.appendChild(remove);
    }
    const bundle = (result.artifacts || []).find?.((artifact) => artifact.key === "bundle_zip") || null;
    if (bundle || item.artifacts?.bundle_zip) {
      const link = document.createElement("a");
      link.className = "download-pill";
      link.href = artifactDownloadUrl(item.job_id || result.job_id, "bundle_zip");
      link.download = bundle?.filename || "vaanisetu_outputs.zip";
      link.textContent = "Package";
      actions.appendChild(link);
    }
    row.appendChild(actions);
    els.recentList.appendChild(row);
  });
}

async function retrySavedJob(jobId) {
  clearError();
  try {
    const response = await apiFetch(`/jobs/${encodeURIComponent(jobId)}/retry`, { method: "POST" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not run this job again.");
    state.currentQueueJobId = payload.job_id;
    beginProgress("text");
    renderResult(await waitForJob(payload.status_url));
  } catch (error) {
    showError(error.message || "Could not run this job again.");
  }
}

async function deleteSavedJob(jobId) {
  if (!jobId || !window.confirm("Delete this job and all of its local outputs? This cannot be undone.")) return;
  try {
    const response = await apiFetch(`/jobs/${encodeURIComponent(jobId)}`, { method: "DELETE" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not delete this job.");
    if (state.currentJobId === jobId || state.currentQueueJobId === jobId) resetResult();
    loadHistory();
  } catch (error) {
    showError(error.message || "Could not delete this job.");
  }
}

async function loadHistory() {
  if (!state.auth.user) return;
  try {
    const params = new URLSearchParams({ limit: "50" });
    const query = els.librarySearch?.value.trim();
    if (query) params.set("q", query);
    const response = await apiFetch(`/library?${params.toString()}`);
    if (!response.ok) return;
    const payload = await response.json();
    if (!query) {
      state.onboarding.hasCompletedJob = (payload.items || []).some((item) => item.status === "succeeded" || item.result);
      renderOnboarding();
    }
    renderHistory(payload.items || []);
  } catch {
    if (!els.librarySearch?.value.trim()) {
      state.onboarding.hasCompletedJob = false;
      renderOnboarding();
    }
    renderHistory([]);
  }
}

function formatBytes(bytes) {
  const value = Number(bytes || 0);
  if (value < 1024) return `${value} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let size = value / 1024;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(size >= 10 ? 0 : 1)} ${units[index]}`;
}

function renderImpact(payload) {
  state.impactData = payload;
  const jobs = payload.jobs || {};
  const delivery = payload.delivery || {};
  const review = payload.review || {};
  els.impactHeadline.textContent = `${jobs.succeeded || 0} completed · ${delivery.media_minutes || 0} media min`;
  const cards = [
    ["Completed translations", jobs.succeeded || 0],
    ["Successful jobs", `${jobs.success_rate_percent || 0}%`],
    ["Media translated", `${delivery.media_minutes || 0} min`],
    ["Offline packages", delivery.offline_packages || 0],
    ["Human-approved", review.approved_jobs || 0],
    ["Approved reuse", review.approved_memory_reuses || 0],
    ["Artifacts delivered", delivery.artifacts_created || 0],
    ["Local storage", formatBytes(payload.storage_bytes)],
  ];
  els.impactGrid.innerHTML = "";
  cards.forEach(([label, value]) => {
    const card = document.createElement("div");
    const strong = document.createElement("strong");
    const span = document.createElement("span");
    strong.textContent = String(value);
    span.textContent = label;
    card.append(strong, span);
    els.impactGrid.appendChild(card);
  });
  els.impactDirections.innerHTML = "";
  const heading = document.createElement("strong");
  heading.textContent = "Language directions";
  els.impactDirections.appendChild(heading);
  const directions = Object.entries(payload.language_directions || {});
  if (!directions.length) {
    const empty = document.createElement("span");
    empty.textContent = "Completed language directions will appear here.";
    els.impactDirections.appendChild(empty);
  } else {
    const list = document.createElement("div");
    list.className = "impact-chips";
    directions.forEach(([direction, count]) => {
      const chip = document.createElement("span");
      chip.textContent = `${direction} · ${count}`;
      list.appendChild(chip);
    });
    els.impactDirections.appendChild(list);
  }
  els.impactPrivacy.textContent = payload.privacy || "Aggregated counts only; no content is included.";
}

async function loadImpact() {
  if (!state.auth.user) return;
  try {
    const response = await apiFetch("/impact", { cache: "no-store" });
    if (!response.ok) throw new Error("Impact summary unavailable");
    renderImpact(await response.json());
  } catch {
    els.impactHeadline.textContent = "Unavailable";
  }
}

function exportImpactReport() {
  if (!state.impactData) return;
  const blob = new Blob([JSON.stringify(state.impactData, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `vaanisetu-impact-${new Date().toISOString().slice(0, 10)}.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

async function openLibraryJob(jobId) {
  if (!jobId) return;
  clearError();
  try {
    const response = await apiFetch(`/jobs/${encodeURIComponent(jobId)}`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not open this job.");
    if (!payload.result) throw new Error("This job is not ready for review.");
    state.currentQueueJobId = payload.job_id;
    payload.result.stage_timings = payload.stage_timings || {};
    renderResult(payload.result);
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (error) {
    showError(error.message || "Could not open this job.");
  }
}

async function loadReview(jobId) {
  if (!jobId) return;
  try {
    const response = await apiFetch(`/jobs/${encodeURIComponent(jobId)}/review`, { cache: "no-store" });
    if (!response.ok) throw new Error("Review unavailable");
    const review = await response.json();
    state.currentReviewVersion = review.versions?.at(-1)?.version || null;
    els.reviewStatus.textContent = review.status === "approved" ? `Approved v${review.approved_version}` : `${review.versions?.length || 0} corrections`;
    els.trustReview.textContent = review.status === "approved" ? `Approved · version ${review.approved_version}` : review.versions?.length ? `${review.versions.length} saved correction${review.versions.length === 1 ? "" : "s"}` : "Human review pending";
    if (review.status === "approved") setJourney("offline");
    const latest = review.versions?.at(-1);
    if (latest?.artifact_key) {
      const correction = await apiFetch(`/jobs/${encodeURIComponent(jobId)}/artifacts/${encodeURIComponent(latest.artifact_key)}`, { cache: "no-store" });
      if (correction.ok) {
        els.correctedText.value = await correction.text();
        renderCorrectionDiff();
      }
    }
  } catch {
    els.reviewStatus.textContent = "Not approved";
    els.trustReview.textContent = "Human review pending";
  }
}

async function saveCorrection() {
  if (!state.currentJobId) return;
  els.reviewMessage.textContent = "";
  const savedText = els.correctedText.value;
  try {
    const response = await apiFetch(`/jobs/${encodeURIComponent(state.currentJobId)}/review/corrections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corrected_text: savedText }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not save correction.");
    state.currentReviewVersion = payload.versions?.at(-1)?.version || null;
    els.reviewStatus.textContent = `${payload.versions.length} corrections`;
    els.trustReview.textContent = `${payload.versions.length} saved correction${payload.versions.length === 1 ? "" : "s"}`;
    els.reviewMessage.textContent = "Correction saved. Approve it when reviewed.";
    await openLibraryJob(state.currentJobId);
    els.correctedText.value = savedText;
    els.reviewMessage.textContent = "Correction saved. Approve it when reviewed.";
  } catch (error) {
    els.reviewMessage.textContent = error.message || "Could not save correction.";
  }
}

async function approveCorrection() {
  if (!state.currentJobId) return;
  els.reviewMessage.textContent = "";
  const approvedText = els.correctedText.value;
  try {
    const response = await apiFetch(`/jobs/${encodeURIComponent(state.currentJobId)}/review/finalize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ corrected_text: approvedText }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not approve correction.");
    els.reviewStatus.textContent = `Approved v${payload.approved_version}`;
    els.trustReview.textContent = `Approved · version ${payload.approved_version}`;
    setJourney("offline");
    els.reviewMessage.textContent = "The visible correction was saved and approved. Package and translation memory updated.";
    await openLibraryJob(state.currentJobId);
    els.correctedText.value = approvedText;
    els.reviewMessage.textContent = "The visible correction was saved and approved. Package and translation memory updated.";
    loadImpact();
  } catch (error) {
    els.reviewMessage.textContent = error.message || "Could not approve correction.";
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
    state.onboarding.systemReady = operationalReady;
    els.healthChip.textContent = payload.production_ready
      ? "Production ready"
      : operationalReady
        ? "Ready to translate"
        : "Needs setup";
    els.healthChip.classList.toggle("ready", operationalReady);
    els.healthChip.classList.toggle("attention", !operationalReady);
    renderReadiness(payload.checks || []);
    renderOnboarding();
  } catch {
    state.onboarding.systemReady = false;
    els.healthChip.textContent = "Unavailable";
    els.healthChip.classList.add("attention");
    els.readinessList.innerHTML = "";
    const row = document.createElement("div");
    row.className = "readiness-item";
    row.innerHTML = '<span class="readiness-dot"></span><div><p>Backend health</p><span>Start the API server to see model readiness.</span></div>';
    els.readinessList.appendChild(row);
    renderOnboarding();
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

function fileJobForm(blob, filename) {
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
  return form;
}

async function submitFileJob(blob, filename) {
  return submitJob("/jobs/file", { method: "POST", body: fileJobForm(blob, filename) });
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

  try {
    const payload = await submitFileJob(blob, filename);
    setProgress(100, "Your translation is ready.");
    renderResult(payload);
  } catch (error) {
    showError(error.message || "Translation failed.");
  } finally {
    els.translateRecording.disabled = false;
    els.translateUpload.disabled = !els.fileInput.files.length;
  }
}

function createBatchRow(file, index) {
  const row = document.createElement("article");
  row.className = "batch-item";
  row.dataset.batchIndex = String(index);
  const name = document.createElement("strong");
  name.textContent = file.name;
  const status = document.createElement("span");
  status.textContent = "Waiting";
  row.append(name, status);
  els.batchList.appendChild(row);
  return row;
}

async function processSelectedFiles() {
  const files = Array.from(els.fileInput.files || []);
  if (!files.length || state.batchRunning) return;
  if (files.length === 1) {
    await processBlob(files[0], files[0].name, "file");
    return;
  }
  if (files.length > 10) {
    showError("Choose up to 10 files in one batch so the CPU worker queue stays manageable.");
    return;
  }
  const invalid = files.map((file) => [file, validateSelectedFile(file)]).find(([, error]) => error);
  if (invalid) {
    showError(`${invalid[0].name}: ${invalid[1]}`);
    return;
  }
  if (els.sourceLanguage.value === "Auto detect" && files.some(isMediaFile)) {
    showError("For an audio/video batch, choose the spoken source language for best transcription accuracy.");
    return;
  }
  const languageError = validateLanguagePair();
  if (languageError) {
    showError(languageError);
    return;
  }

  clearError();
  resetResult();
  state.batchRunning = true;
  state.batchCancelRequested = false;
  els.translateUpload.disabled = true;
  els.batchSummary.classList.remove("hidden");
  els.batchList.innerHTML = "";
  els.batchTitle.textContent = "Batch in progress";
  const rows = files.map(createBatchRow);
  let completed = 0;
  let failed = 0;
  let lastResult = null;
  els.batchCount.textContent = `0 of ${files.length}`;

  for (let index = 0; index < files.length; index += 1) {
    if (state.batchCancelRequested) break;
    const file = files[index];
    const row = rows[index];
    const status = row.querySelector("span");
    status.textContent = "Processing";
    row.classList.add("active");
    beginProgress("file");
    els.progressTitle.textContent = `Processing ${index + 1} of ${files.length}`;
    try {
      const payload = await submitFileJob(file, file.name);
      completed += 1;
      lastResult = payload;
      status.textContent = "Complete";
      row.classList.add("complete");
      const open = document.createElement("button");
      open.type = "button";
      open.className = "secondary-action compact";
      open.textContent = "Review";
      open.addEventListener("click", () => openLibraryJob(payload.job_id));
      row.appendChild(open);
    } catch (error) {
      failed += 1;
      status.textContent = error.message || "Failed";
      row.classList.add("failed");
    } finally {
      row.classList.remove("active");
      els.batchCount.textContent = `${index + 1} of ${files.length}`;
    }
  }

  state.batchRunning = false;
  els.translateUpload.disabled = false;
  els.progressPanel.classList.add("hidden");
  els.batchTitle.textContent = `${state.batchCancelRequested ? "Batch stopped" : "Batch complete"} · ${completed} succeeded${failed ? ` · ${failed} failed` : ""}`;
  if (lastResult) renderResult(lastResult);
  else showError("No file in this batch could be completed. Review the messages above and retry.");
  loadHistory();
  loadImpact();
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
  tab.addEventListener("keydown", (event) => {
    if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
    event.preventDefault();
    const tabs = Array.from(els.modeTabs);
    const current = tabs.indexOf(tab);
    const next = event.key === "Home"
      ? 0
      : event.key === "End"
        ? tabs.length - 1
        : (current + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
    setInputMode(tabs[next].dataset.mode);
    tabs[next].focus();
  });
});

els.translateText.addEventListener("click", processTextInput);
els.saveCorrection.addEventListener("click", saveCorrection);
els.approveCorrection.addEventListener("click", approveCorrection);
els.correctedText.addEventListener("input", renderCorrectionDiff);
els.textInput.addEventListener("input", scheduleGlossaryInsight);
els.librarySearch.addEventListener("input", () => {
  window.clearTimeout(state.libraryTimer);
  state.libraryTimer = window.setTimeout(loadHistory, 250);
});

els.fileInput.addEventListener("change", () => {
  clearError();
  const files = Array.from(els.fileInput.files || []);
  const representative = files.find(isVideoFile) || files[0] || null;
  refreshOutputOptions(representative);
  if (!files.length) {
    els.translateUpload.disabled = true;
    els.selectedFileName.textContent = "Choose a file";
    els.batchSummary.classList.add("hidden");
    return;
  }
  els.selectedFileName.textContent = files.length === 1 ? files[0].name : `${files.length} files selected`;
  const invalid = files.map((file) => [file, validateSelectedFile(file)]).find(([, error]) => error);
  if (invalid) {
    showError(`${invalid[0].name}: ${invalid[1]}`);
    els.translateUpload.disabled = true;
    return;
  }
  if (els.sourceLanguage.value === "Auto detect" && files.some(isMediaFile)) {
    showError("For audio/video, choose the spoken source language for best transcription accuracy.");
    els.translateUpload.disabled = true;
    return;
  }
  if (files.length > 10) {
    showError("Choose up to 10 files in one batch so the CPU worker queue stays manageable.");
    els.translateUpload.disabled = true;
    return;
  }
  els.translateUpload.disabled = false;
  els.translateUpload.textContent = files.length === 1 ? "Translate file" : `Translate ${files.length} files`;
});

els.translateUpload.addEventListener("click", processSelectedFiles);
els.exportImpact.addEventListener("click", exportImpactReport);

[els.makeTts, els.makeSubtitles, els.burnCaptions, els.mergeTranslatedAudio].forEach((control) => {
  control.addEventListener("change", () => refreshOutputOptions(els.fileInput.files[0] || null));
});

els.swapLanguages.addEventListener("click", () => {
  const source = els.sourceLanguage.value;
  if (source === "Auto detect") {
    els.sourceLanguage.value = els.targetLanguage.value;
    els.targetLanguage.value = "English";
    clearError();
    scheduleGlossaryInsight();
    return;
  }
  els.sourceLanguage.value = els.targetLanguage.value;
  els.targetLanguage.value = source;
  clearError();
  scheduleGlossaryInsight();
});

els.sourceLanguage.addEventListener("change", () => {
  clearError();
  const files = Array.from(els.fileInput.files || []);
  if (files.length && els.sourceLanguage.value === "Auto detect" && files.some(isMediaFile)) {
    showError("For audio/video, choose the spoken source language for best transcription accuracy.");
    els.translateUpload.disabled = true;
    return;
  }
  if (files.length && files.every((file) => !validateSelectedFile(file))) {
    els.translateUpload.disabled = false;
  }
  scheduleGlossaryInsight();
});

els.targetLanguage.addEventListener("change", scheduleGlossaryInsight);

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

els.authForm.addEventListener("submit", submitAuth);

els.authSwitch.addEventListener("click", () => {
  setAuthMode(state.auth.mode === "register" ? "login" : "register");
});

els.logoutButton.addEventListener("click", logout);

els.cancelJob.addEventListener("click", async () => {
  if (!state.currentQueueJobId) return;
  if (state.batchRunning) state.batchCancelRequested = true;
  const response = await apiFetch(`/jobs/${encodeURIComponent(state.currentQueueJobId)}/cancel`, { method: "POST" });
  if (!response.ok) showError("Could not cancel this job.");
});

els.retryJob.addEventListener("click", () => retrySavedJob(state.currentQueueJobId || state.currentJobId));
els.deleteJob.addEventListener("click", () => deleteSavedJob(state.currentQueueJobId || state.currentJobId));

els.adminPanel.addEventListener("toggle", () => {
  if (els.adminPanel.open) loadUsers();
});

els.onboardingNext.addEventListener("click", () => {
  if (!state.onboarding.systemReady) {
    els.systemPanel.open = true;
    els.systemPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  if (!state.onboarding.hasCompletedJob) {
    setInputMode("text");
    document.querySelector(".translator-surface").scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => els.textInput.focus(), 350);
    return;
  }
  if (state.auth.user?.role === "admin") {
    els.adminPanel.open = true;
    els.adminPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

if ("speechSynthesis" in window) {
  window.speechSynthesis.onvoiceschanged = () => window.speechSynthesis.getVoices();
}

loadServerLimits();
loadHealth();
loadSession();
drawIdleMeter();
refreshOutputOptions();
