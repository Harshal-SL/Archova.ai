/**
 * AI Architecture Engine Test Harness
 * Vanilla JavaScript orchestration layer for manual verification.
 */

// ── Configuration & State ───────────────────────────────────────────────────

const API_BASE_URL = "http://localhost:8000/api/v1/generations";
const HEALTH_URL = "http://localhost:8000/";

let generationId = null;
let currentQuestionId = null;
let currentLldType = "backend";
let logEventSource = null;
let autoScroll = true;
let totalLogCount = 0;
let seenLogKeys = new Set();

let currentLLDStates = {
  backend: "NOT_STARTED",
  frontend: "NOT_STARTED",
  database: "NOT_STARTED",
  security: "NOT_STARTED",
  cloud: "NOT_STARTED",
};

// ── Sample Prompts for Quick Testing ────────────────────────────────────────

const SAMPLE_PROMPTS = {
  1: `Build a modern, cloud-native Online Event Management System for university hackathons.
The platform allows students to browse events, register, form teams, submit project artifacts, and receive real-time notifications.
Organizers must be able to manage event schedules, check in participants via QR code, coordinate judge scoring, and export analytics.
Requires sub-200ms API response time, 99.9% uptime under 5,000 concurrent participants, and OAuth2 authentication.`,
  2: `Build a modern College Library Management System.
Students must authenticate securely, search the catalog, and borrow or reserve books.
Librarians must manage inventory, record book circulation, track overdue fines, and generate administrative reports.
Requires sub-250ms catalog search response time under 500 concurrent users with PostgreSQL and Redis.`,
  3: `Build an IoT-Enabled Smart Parking Management System.
Drivers can view parking spot availability in real time, reserve slots, and pay digital parking fees.
Attendants verify vehicle check-in and check-out with automated license plate recognition and overstay alerts.
Platform requires high availability, WebSocket push notifications, and multi-zone rate analytics.`,
};

// ── Initialization ──────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  checkApiHealth();
});

// ── API Health Check ────────────────────────────────────────────────────────

async function checkApiHealth() {
  const badge = document.getElementById("api-status-badge");
  try {
    const res = await fetch(HEALTH_URL);
    if (res.ok) {
      const data = await res.json();
      badge.textContent = "API: Connected (v2.0.0)";
      badge.className = "badge badge-success";
    } else {
      badge.textContent = `API: Error ${res.status}`;
      badge.className = "badge alert-error";
    }
  } catch (err) {
    badge.textContent = "API: Offline (Start Backend)";
    badge.className = "badge alert-error";
    showError("Unable to connect to AI Engine at http://localhost:8000. Please ensure the FastAPI backend is running.");
  }
}

// ── Step 1: Start Generation ────────────────────────────────────────────────

async function startGeneration() {
  const promptInput = document.getElementById("prompt-input");
  const prompt = promptInput.value.trim();

  if (!prompt) {
    showError("Please enter a problem statement or select a sample prompt.");
    promptInput.focus();
    return;
  }

  dismissError();
  setButtonLoading("btn-start", true, "Analyzing Requirements...");

  appendTerminalLog(getTimestamp(), "CLIENT", "🚀 Sending problem statement to AI Architecture Engine...", "INFO");
  appendTerminalLog(getTimestamp(), "CLIENT", "⏳ Waiting for REE Input Understanding & Multi-Agent analysis...", "INFO");

  try {
    const response = await fetch(API_BASE_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Server error (${response.status})`);
    }

    // Save generation ID
    generationId = data.generation_id;
    document.getElementById("session-badge").textContent = `ID: ${generationId}`;
    document.getElementById("session-badge").className = "badge badge-primary";

    showInfo(`Generation session started (${generationId}).`);

    // Connect real-time log stream
    connectLogStream(generationId);

    // Reveal Step 2 Card
    document.getElementById("step2-card").classList.remove("hidden");
    document.getElementById("step2-card").scrollIntoView({ behavior: "smooth" });

    // Handle initial questions or completed state
    if (data.status === "INTERVIEW_IN_PROGRESS" && data.current_question) {
      renderQuestion(data.current_question);
    } else {
      showInterviewCompleted();
    }
  } catch (err) {
    appendTerminalLog(getTimestamp(), "CLIENT", `❌ Error starting generation: ${err.message}`, "ERROR");
    showError(`Failed to start generation: ${err.message}`);
  } finally {
    setButtonLoading("btn-start", false, "Start Generation");
  }
}

// ── Step 2: Render & Submit Interview Questions ─────────────────────────────

function renderQuestion(q) {
  currentQuestionId = q.question_id;

  // Show question container, hide completed container
  document.getElementById("question-container").classList.remove("hidden");
  document.getElementById("interview-completed-container").classList.add("hidden");

  // Populate Question text and metadata
  document.getElementById("question-id-badge").textContent = q.question_id || "Question";
  document.getElementById("question-text").textContent = q.question || "Clarification needed:";
  
  const rationaleEl = document.getElementById("question-rationale");
  if (q.rationale) {
    rationaleEl.textContent = `Context: ${q.rationale}`;
    rationaleEl.classList.remove("hidden");
  } else {
    rationaleEl.classList.add("hidden");
  }

  const priorityBadge = document.getElementById("question-priority-badge");
  priorityBadge.textContent = `${(q.priority || "medium").toUpperCase()} PRIORITY`;

  // Render clickable options list
  const optionsGroup = document.getElementById("options-group");
  const optionsList = document.getElementById("options-list");
  optionsList.innerHTML = "";

  // Filter out any empty or meaningless placeholder strings
  const validOptions = (q.options || []).filter((opt) => {
    const s = String(opt).trim().toLowerCase();
    return s && !["option a", "option b", "option c", "option 1", "option 2", "placeholder", "none"].includes(s);
  });

  if (validOptions.length > 0) {
    optionsGroup.classList.remove("hidden");
    let defaultBtn = null;
    let defaultVal = q.default_option || "";

    validOptions.forEach((optText, idx) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-option";
      btn.id = `btn-option-${idx + 1}`;
      btn.innerHTML = `<span class="opt-kbd">[${idx + 1}]</span> ${optText}`;
      btn.onclick = () => selectOption(optText, btn);
      optionsList.appendChild(btn);

      // Identify recommended default option
      if (defaultVal && optText === defaultVal) {
        defaultBtn = btn;
      } else if (!defaultBtn && (optText.toLowerCase().includes("recommended default") || optText.toLowerCase().includes("default"))) {
        defaultBtn = btn;
        defaultVal = optText;
      }
    });

    // Auto-select recommended default if found or fallback to first option
    if (!defaultBtn && optionsList.firstChild) {
      defaultBtn = optionsList.firstChild;
      defaultVal = validOptions[0];
    }
    if (defaultBtn) {
      selectOption(defaultVal, defaultBtn);
    }
  } else {
    optionsGroup.classList.add("hidden");
  }

  // Answer input field
  const answerInput = document.getElementById("answer-input");
  answerInput.placeholder = validOptions.length > 0 
    ? "Option selected above. Press Enter ↵ to submit or customize here..." 
    : "Type your answer to this question here...";
  answerInput.focus();
}

function selectOption(value, btnElement) {
  document.getElementById("answer-input").value = value;
  // Visual active highlight
  document.querySelectorAll(".btn-option").forEach((b) => b.classList.remove("selected"));
  if (btnElement) {
    btnElement.classList.add("selected");
  }
}

async function submitAnswer() {
  const answerInput = document.getElementById("answer-input");
  const answer = answerInput.value.trim();

  if (!answer) {
    showError("Please enter or select an answer before submitting.");
    answerInput.focus();
    return;
  }

  if (!generationId || !currentQuestionId) {
    showError("Invalid session state. Please restart generation.");
    return;
  }

  dismissError();
  setButtonLoading("btn-submit-answer", true, "Submitting Answer...");

  appendTerminalLog(getTimestamp(), "INTERVIEW", `Submitting answer for question '${currentQuestionId}': "${answer.slice(0, 80)}"`, "INFO");

  try {
    const url = `${API_BASE_URL}/${generationId}/answers`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: currentQuestionId,
        answer: answer,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Server error (${response.status})`);
    }

    if (data.status === "INTERVIEW_IN_PROGRESS" && data.next_question) {
      renderQuestion(data.next_question);
      showInfo("Answer recorded. Next question loaded.");
    } else {
      showInterviewCompleted();
      showInfo("All interview questions answered! Ready to generate architecture.");
    }
  } catch (err) {
    appendTerminalLog(getTimestamp(), "CLIENT", `❌ Submit error: ${err.message}`, "ERROR");
    showError(`Failed to submit answer: ${err.message}`);
  } finally {
    setButtonLoading("btn-submit-answer", false, "Submit Answer [Enter ↵]");
  }
}

// ── Global Keyboard Shortcuts ──────────────────────────────────────────────
window.addEventListener("keydown", (e) => {
  const step2Card = document.getElementById("step2-card");
  const questionContainer = document.getElementById("question-container");
  const completedContainer = document.getElementById("interview-completed-container");
  const promptInput = document.getElementById("prompt-input");

  // If on initial prompt input and Enter is pressed (without Shift)
  if (document.activeElement === promptInput && e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    startGeneration();
    return;
  }

  // Interview Question Active Shortcuts
  if (step2Card && !step2Card.classList.contains("hidden")) {
    if (questionContainer && !questionContainer.classList.contains("hidden")) {
      // Numbers 1-5 select options
      if (["1", "2", "3", "4", "5"].includes(e.key) && document.activeElement.tagName !== "INPUT") {
        const btn = document.getElementById(`btn-option-${e.key}`);
        if (btn) {
          e.preventDefault();
          btn.click();
        }
      }
      // Enter key submits current answer
      else if (e.key === "Enter") {
        e.preventDefault();
        submitAnswer();
      }
    } else if (completedContainer && !completedContainer.classList.contains("hidden")) {
      // Enter key triggers Generate Architecture
      if (e.key === "Enter") {
        e.preventDefault();
        generateArchitecture();
      }
    }
  }
});

function showInterviewCompleted() {
  document.getElementById("question-container").classList.add("hidden");
  document.getElementById("interview-completed-container").classList.remove("hidden");
}

// ── Step 3: Generate ARSRS + HLD ────────────────────────────────────────────

async function generateArchitecture() {
  if (!generationId) {
    showError("No active generation session found.");
    return;
  }

  dismissError();
  setButtonLoading("btn-generate-arch", true, "Generating ARSRS and HLD...");
  showInfo("AI Engine is executing REE Finalizer & SAE Planning / HLD phases. Please wait...");
  appendTerminalLog(getTimestamp(), "CLIENT", "⚙️ Triggering Architecture Generation (ARSRS + HLD)...", "INFO");

  try {
    const url = `${API_BASE_URL}/${generationId}/generate`;
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Server error (${response.status})`);
    }

    // Render ARSRS & HLD JSON immediately
    document.getElementById("arsrs-json").textContent = JSON.stringify(data.arsrs || {}, null, 2);
    document.getElementById("hld-json").textContent = JSON.stringify(data.hld || {}, null, 2);

    // Reveal Step 3 (ARSRS & HLD)
    document.getElementById("step3-card").classList.remove("hidden");

    // Reveal Step 4 (LLD Dashboard)
    document.getElementById("step4-card").classList.remove("hidden");
    document.getElementById("step3-card").scrollIntoView({ behavior: "smooth" });

    showInfo("ARSRS & HLD generated successfully! Server is streaming background parallel LLD events in real-time.");

    // Initial LLD check (select backend)
    selectLLD("backend");

  } catch (err) {
    appendTerminalLog(getTimestamp(), "CLIENT", `❌ Generation failed: ${err.message}`, "ERROR");
    showError(`Architecture generation failed: ${err.message}`);
  } finally {
    setButtonLoading("btn-generate-arch", false, "Generate Architecture (ARSRS + HLD)");
  }
}

// ── Step 4: Real-Time Event Driven LLD Status & Process Tracking ───────────

function updateActiveProcess(entry) {
  const banner = document.getElementById("active-process-banner");
  const titleEl = document.getElementById("active-process-title");
  const descEl = document.getElementById("active-process-desc");
  const pillEl = document.getElementById("active-process-pill");

  if (!banner || !entry) return;

  banner.classList.remove("hidden");
  titleEl.textContent = `${entry.process || entry.stage}:`;
  descEl.textContent = entry.message || "Working...";

  const pStatus = (entry.process_status || (entry.level === "ERROR" ? "FAILED" : "IN_PROGRESS")).toUpperCase();
  pillEl.textContent = pStatus.replace("_", " ");
  pillEl.className = `status-pill pill-${pStatus.toLowerCase().replace("_", "-")}`;

  if (pStatus === "COMPLETED") {
    pillEl.className = "status-pill pill-ready";
  } else if (pStatus === "FAILED") {
    pillEl.className = "status-pill pill-failed";
  } else {
    pillEl.className = "status-pill pill-generating";
  }
}

function updateStatusPills(llds) {
  if (!llds) return;
  const types = ["backend", "frontend", "database", "security", "cloud"];
  types.forEach((type) => {
    const status = (llds[type] || "NOT_STARTED").toUpperCase();
    const pill = document.getElementById(`pill-${type}`);
    if (pill) {
      pill.textContent = status;
      pill.className = `status-pill pill-${status.toLowerCase().replace("_", "-")}`;
    }
  });

  // Update pill for active selected LLD header
  const activeStatus = (llds[currentLldType] || "NOT_STARTED").toUpperCase();
  const selectedPill = document.getElementById("selected-lld-status-pill");
  if (selectedPill) {
    selectedPill.textContent = activeStatus;
    selectedPill.className = `status-pill pill-${activeStatus.toLowerCase().replace("_", "-")}`;
  }

  // Check if all 5 LLDs are completed
  const allTerminal = types.every((t) => llds[t] === "READY" || llds[t] === "FAILED");
  if (allTerminal) {
    const indicator = document.getElementById("polling-indicator");
    if (indicator) {
      indicator.innerHTML = "✓ All background LLDs completed (Stream closed)";
      indicator.style.color = "var(--color-success)";
    }
    // Cleanly close SSE stream connection to stop all background server load
    if (logEventSource) {
      logEventSource.close();
      logEventSource = null;
    }
  }
}

// ── Step 5: View Specific LLD ───────────────────────────────────────────────

async function selectLLD(lldType, smoothScroll = false) {
  currentLldType = lldType;

  // Update active tab buttons
  document.querySelectorAll(".lld-buttons .btn-tab").forEach((btn) => {
    btn.classList.remove("active");
  });
  const activeBtn = document.getElementById(`btn-lld-${lldType}`);
  if (activeBtn) {
    activeBtn.classList.add("active");
  }

  // Update viewer title
  const titles = {
    backend: "Backend Low Level Design",
    frontend: "Frontend Low Level Design",
    database: "Database Low Level Design",
    security: "Security Architecture LLD",
    cloud: "Cloud & Infrastructure LLD",
  };
  document.getElementById("selected-lld-title").textContent = titles[lldType] || `${lldType.toUpperCase()} LLD`;

  const jsonViewer = document.getElementById("selected-lld-json");
  const msgBox = document.getElementById("lld-message-box");
  const msgIcon = document.getElementById("lld-message-icon");
  const msgText = document.getElementById("lld-message-text");

  if (!generationId) {
    jsonViewer.textContent = "No active generation session.";
    return;
  }

  try {
    const url = `${API_BASE_URL}/${generationId}/lld/${lldType}`;
    const response = await fetch(url);
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Failed to fetch LLD (${response.status})`);
    }

    // Update status pill
    const statusPill = document.getElementById("selected-lld-status-pill");
    const status = (data.status || "NOT_STARTED").toUpperCase();
    statusPill.textContent = status;
    statusPill.className = `status-pill pill-${status.toLowerCase().replace("_", "-")}`;

    if (data.status === "READY") {
      msgBox.classList.add("hidden");
      jsonViewer.textContent = JSON.stringify(data.data || {}, null, 2);
    } else if (data.status === "GENERATING") {
      msgBox.classList.remove("hidden");
      msgBox.style.backgroundColor = "rgba(245, 158, 11, 0.1)";
      msgBox.style.borderColor = "rgba(245, 158, 11, 0.4)";
      msgBox.style.color = "#fcd34d";
      msgIcon.textContent = "⏳";
      msgText.textContent = data.message || `${lldType.toUpperCase()} LLD is still being generated in the background...`;
      jsonViewer.textContent = JSON.stringify({ status: "GENERATING", message: data.message }, null, 2);
    } else if (data.status === "FAILED") {
      msgBox.classList.remove("hidden");
      msgBox.style.backgroundColor = "rgba(239, 68, 68, 0.15)";
      msgBox.style.borderColor = "rgba(239, 68, 68, 0.4)";
      msgBox.style.color = "#fca5a5";
      msgIcon.textContent = "❌";
      msgText.textContent = `Error: ${data.error || "LLD generation failed."}`;
      jsonViewer.textContent = JSON.stringify({ status: "FAILED", error: data.error }, null, 2);
    } else {
      msgBox.classList.add("hidden");
      jsonViewer.textContent = JSON.stringify({ status: "NOT_STARTED", message: data.message }, null, 2);
    }

    if (smoothScroll) {
      jsonViewer.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  } catch (err) {
    showError(`Error fetching ${lldType} LLD: ${err.message}`);
  }
}

// ── Live Terminal Console & SSE Streaming ────────────────────────────────────

function getTimestamp() {
  const d = new Date();
  return d.toTimeString().split(" ")[0];
}

function appendTerminalLog(timestamp, stage, message, level = "INFO") {
  const body = document.getElementById("terminal-body");
  if (!body) return;

  const key = `${timestamp}|${stage}|${message}`;
  if (seenLogKeys.has(key)) return;
  seenLogKeys.add(key);

  const line = document.createElement("div");
  line.className = "terminal-line";

  const tsSpan = document.createElement("span");
  tsSpan.className = "terminal-ts";
  tsSpan.textContent = `[${timestamp || getTimestamp()}]`;

  const tagSpan = document.createElement("span");
  const stageLower = String(stage || "INFO").toLowerCase().replace("_", "-");
  tagSpan.className = `terminal-tag ${stageLower}`;
  tagSpan.textContent = `[${stage || "INFO"}]`;

  const msgSpan = document.createElement("span");
  msgSpan.className = `terminal-msg ${level === "ERROR" ? "error" : ""}`;
  msgSpan.textContent = message;

  line.appendChild(tsSpan);
  line.appendChild(tagSpan);
  line.appendChild(msgSpan);
  body.appendChild(line);

  totalLogCount++;
  const badge = document.getElementById("log-count-badge");
  if (badge) badge.textContent = `${totalLogCount} Logs`;

  if (autoScroll) {
    body.scrollTop = body.scrollHeight;
  }
}

let loadedLLDTypes = new Set();

function connectLogStream(genId) {
  if (logEventSource) {
    logEventSource.close();
    logEventSource = null;
  }
  loadedLLDTypes.clear();

  // 1. Initial historical logs fetch (one-time only)
  fetchLogsHistory(genId);

  // 2. Connect EventSource (SSE) for pure real-time event streaming
  try {
    const sseUrl = `${API_BASE_URL}/${genId}/logs/stream`;
    logEventSource = new EventSource(sseUrl);

    logEventSource.onmessage = (event) => {
      try {
        if (!event.data || event.data.trim() === "" || event.data.startsWith(":")) return;
        const entry = JSON.parse(event.data);
        appendTerminalLog(entry.timestamp, entry.stage, entry.message, entry.level);
        
        // Update active process banner
        updateActiveProcess(entry);

        // Update LLD status pills if server pushed LLD snapshot
        if (entry.lld_status) {
          updateStatusPills(entry.lld_status);
        }

        // If the currently selected LLD just finished and has not been rendered yet, refresh once
        if (entry.lld_completed) {
          if (!loadedLLDTypes.has(entry.lld_completed) && entry.lld_completed === currentLldType) {
            loadedLLDTypes.add(entry.lld_completed);
            selectLLD(currentLldType, false);
          }
        }

        // Cleanly terminate SSE connection if session completed
        if (entry.message && (entry.message.includes("Generation lifecycle COMPLETED") || entry.message.includes("All background parallel LLD tasks completed"))) {
          if (logEventSource) {
            logEventSource.close();
            logEventSource = null;
          }
        }
      } catch (e) {}
    };

    logEventSource.onerror = (err) => {
      // Cleanly terminate on any connection drop or server close to prevent infinite reconnect loops
      if (logEventSource) {
        logEventSource.close();
        logEventSource = null;
      }
    };
  } catch (err) {
    console.warn("EventSource setup skipped:", err);
  }
}

async function fetchLogsHistory(genId) {
  if (!genId) return;
  try {
    const res = await fetch(`${API_BASE_URL}/${genId}/logs`);
    if (res.ok) {
      const data = await res.json();
      (data.logs || []).forEach((entry) => {
        appendTerminalLog(entry.timestamp, entry.stage, entry.message, entry.level);
        if (entry.lld_status) updateStatusPills(entry.lld_status);
      });
    }
  } catch (e) {}
}

function clearTerminalLogs() {
  const body = document.getElementById("terminal-body");
  if (body) {
    body.innerHTML = '<div class="terminal-welcome"><span class="terminal-prompt">$</span> Terminal cleared.</div>';
  }
  seenLogKeys.clear();
  totalLogCount = 0;
  const badge = document.getElementById("log-count-badge");
  if (badge) badge.textContent = "0 Logs";
}

function toggleAutoScroll() {
  autoScroll = !autoScroll;
  const btn = document.getElementById("toggle-autoscroll");
  if (btn) {
    btn.textContent = `Auto-Scroll: ${autoScroll ? "ON" : "OFF"}`;
  }
}

// ── UI Helpers ──────────────────────────────────────────────────────────────

function switchSpecTab(tabName) {
  const arsrsBtn = document.getElementById("tab-arsrs-btn");
  const hldBtn = document.getElementById("tab-hld-btn");
  const arsrsPane = document.getElementById("tab-arsrs-pane");
  const hldPane = document.getElementById("tab-hld-pane");

  if (tabName === "arsrs") {
    arsrsBtn.classList.add("active");
    hldBtn.classList.remove("active");
    arsrsPane.classList.remove("hidden");
    hldPane.classList.add("hidden");
  } else {
    hldBtn.classList.add("active");
    arsrsBtn.classList.remove("active");
    hldPane.classList.remove("hidden");
    arsrsPane.classList.add("hidden");
  }
}

function fillSample(sampleId) {
  const prompt = SAMPLE_PROMPTS[sampleId] || "";
  document.getElementById("prompt-input").value = prompt;
  dismissError();
}

function copyJson(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.textContent;
  navigator.clipboard.writeText(text).then(() => {
    showInfo("JSON copied to clipboard!");
  }).catch(() => {
    showError("Could not copy JSON to clipboard.");
  });
}

function setButtonLoading(buttonId, isLoading, defaultText) {
  const btn = document.getElementById(buttonId);
  if (!btn) return;
  const spinner = btn.querySelector(".spinner");

  btn.disabled = isLoading;
  if (spinner) {
    if (isLoading) {
      spinner.classList.remove("hidden");
    } else {
      spinner.classList.add("hidden");
    }
  }
  if (defaultText) {
    btn.lastChild.textContent = ` ${defaultText}`;
  }
}

function showError(message) {
  const banner = document.getElementById("error-banner");
  document.getElementById("error-message").textContent = message;
  banner.classList.remove("hidden");
}

function dismissError() {
  document.getElementById("error-banner").classList.add("hidden");
}

function showInfo(message) {
  const banner = document.getElementById("info-banner");
  document.getElementById("info-message").textContent = message;
  banner.classList.remove("hidden");
  setTimeout(() => {
    banner.classList.add("hidden");
  }, 4000);
}

function dismissInfo() {
  document.getElementById("info-banner").classList.add("hidden");
}

async function manualStatusCheck() {
  if (!generationId) {
    showError("No active generation session to check.");
    return;
  }
  try {
    const url = `${API_BASE_URL}/${generationId}/status`;
    const response = await fetch(url);
    if (response.ok) {
      const data = await response.json();
      if (data.llds) updateStatusPills(data.llds);
    }
  } catch (e) {}
  fetchLogsHistory(generationId);
  selectLLD(currentLldType);
  showInfo("Status and logs refreshed.");
}

function resetSession() {
  if (logEventSource) {
    logEventSource.close();
    logEventSource = null;
  }
  generationId = null;
  currentQuestionId = null;
  currentLldType = "backend";
  currentLLDStates = {
    backend: "NOT_STARTED",
    frontend: "NOT_STARTED",
    database: "NOT_STARTED",
    security: "NOT_STARTED",
    cloud: "NOT_STARTED",
  };

  const processBanner = document.getElementById("active-process-banner");
  if (processBanner) processBanner.classList.add("hidden");

  const indicator = document.getElementById("polling-indicator");
  if (indicator) {
    indicator.innerHTML = '<span class="pulse-dot"></span> Live Server Stream';
    indicator.style.color = "var(--color-primary)";
  }

  document.getElementById("prompt-input").value = "";
  document.getElementById("session-badge").textContent = "No Active Session";
  document.getElementById("session-badge").className = "badge badge-secondary";

  document.getElementById("step2-card").classList.add("hidden");
  document.getElementById("step3-card").classList.add("hidden");
  document.getElementById("step4-card").classList.add("hidden");

  updateStatusPills(currentLLDStates);
  clearTerminalLogs();
  dismissError();
  dismissInfo();
  showInfo("Session reset. Ready for a new problem statement.");
  window.scrollTo({ top: 0, behavior: "smooth" });
}
