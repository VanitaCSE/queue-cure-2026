/**
 * Queue Cure 2026 - Client-side WebSocket logic
 * All live updates via Socket.IO - no polling, no page refresh.
 */

(function () {
  "use strict";

  const page = document.body.dataset.page;
  let socket = null;
  let state = null;
  let pendingRemoveId = null;
  let searchQuery = "";
  let patientFlowChart = null;
  let queueStatusChart = null;
  let lastUpdatedInterval = null;

  function formatTime(isoString) {
    if (!isoString) return "—";
    try {
      return new Date(isoString).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch {
      return isoString;
    }
  }

  function formatToken(num) {
    return num != null ? `QC-${String(num).padStart(3, "0")}` : "—";
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const id = "toast-" + Date.now();
    const bgClass =
      type === "success" ? "text-bg-success" :
      type === "error" ? "text-bg-danger" :
      type === "warning" ? "text-bg-warning" : "text-bg-primary";

    container.insertAdjacentHTML(
      "beforeend",
      `<div id="${id}" class="toast align-items-center ${bgClass} border-0" role="alert">
        <div class="d-flex">
          <div class="toast-body">${message}</div>
          <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
      </div>`
    );

    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
  }

  function setLoading(btn, loading) {
    if (!btn) return;
    const spinner = btn.querySelector(".spinner-border");
    const text = btn.querySelector(".btn-text");
    btn.disabled = loading;
    if (spinner) spinner.classList.toggle("d-none", !loading);
    if (text) text.classList.toggle("d-none", loading);
  }

  async function apiRequest(url, options = {}) {
    const res = await fetch(url, {
      headers: { "Content-Type": "application/json", ...options.headers },
      ...options,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || "Request failed");
    return data;
  }

  function updateConnectionStatus(connected) {
    const badge = document.getElementById("connectionStatus");
    if (!badge) return;
    badge.classList.toggle("disconnected", !connected);
    badge.innerHTML = connected
      ? `<span class="pulse-dot-sm"></span> <span class="ms-1">🟢 Connected via WebSocket</span>`
      : `<span class="pulse-dot-sm"></span> <span class="ms-1">🔴 Reconnecting...</span>`;

    const wsStatus = document.getElementById("wsStatus");
    if (wsStatus) {
      wsStatus.textContent = connected ? "🟢 Connected" : "🔴 Reconnecting...";
      wsStatus.className = "badge " + (connected ? "bg-success" : "bg-danger");
    }
  }

  function initDarkMode() {
    const toggle = document.getElementById("darkModeToggle");
    const saved = localStorage.getItem("qc-theme") || "light";
    document.documentElement.setAttribute("data-bs-theme", saved);

    if (toggle) {
      toggle.innerHTML = saved === "dark"
        ? '<i class="bi bi-sun"></i> Light Mode'
        : '<i class="bi bi-moon-stars"></i> Dark Mode';
      toggle.addEventListener("click", () => {
        const next = document.documentElement.getAttribute("data-bs-theme") === "dark" ? "light" : "dark";
        document.documentElement.setAttribute("data-bs-theme", next);
        localStorage.setItem("qc-theme", next);
        toggle.innerHTML = next === "dark"
          ? '<i class="bi bi-sun"></i> Light Mode'
          : '<i class="bi bi-moon-stars"></i> Dark Mode';
      });
    }
  }

  function startClock() {
    const update = () => {
      const now = new Date().toLocaleString([], {
        weekday: "short",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      setText("currentTimeDisplay", now);
      
      const clinicInfoDate = document.getElementById("clinicInfoDate");
      if (clinicInfoDate) {
        clinicInfoDate.textContent = new Date().toLocaleDateString([], { year: "numeric", month: "long", day: "numeric" });
      }
    };
    update();
    setInterval(update, 1000);
  }

  function startLastUpdatedTimer() {
    const update = () => {
      const el = document.getElementById("lastUpdated");
      if (el) {
        el.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
      }
    };
    update();
    lastUpdatedInterval = setInterval(update, 1000);
  }

  function initSocket() {
    socket = io({
      transports: ["websocket", "polling"],
      reconnection: true,
      reconnectionAttempts: Infinity,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    socket.on("connect", () => {
      updateConnectionStatus(true);
      socket.emit("request_state");
    });

    socket.on("disconnect", () => updateConnectionStatus(false));

    socket.on("connect_error", () => updateConnectionStatus(false));

    socket.on("queue_updated", (data) => {
      state = data;
      renderState(data);
    });

    socket.on("analytics_updated", (analytics) => {
      if (state) state.analytics = analytics;
      renderAnalytics(analytics);
    });

    socket.on("patient_added", (patient) => {
      showToast(`Added ${patient.patient_name} (${formatToken(patient.token_number)})`, "success");
    });

    socket.on("patient_called", (patient) => {
      showToast(`Now calling ${patient.patient_name} (${formatToken(patient.token_number)})`, "info");
      flashToken();
    });

    socket.on("patient_removed", (patient) => {
      showToast(`Removed ${patient.patient_name}`, "warning");
    });

    socket.on("settings_updated", (settings) => {
      if (state) state.settings = settings;
      applySettings(settings);
    });

    socket.on("queue_reset", () => {
      showToast("Queue has been reset", "warning");
    });
  }

  function flashToken() {
    const el = document.getElementById("currentTokenDisplay");
    if (el) {
      el.classList.remove("token-updated");
      void el.offsetWidth;
      el.classList.add("token-updated");
    }
  }

  function renderState(data) {
    if (!data) return;

    applySettings(data.settings);
    renderAnalytics(data.analytics);

    const current = data.current;
    const currentTokenEl = document.getElementById("currentTokenDisplay");
    if (currentTokenEl) {
      if (current) {
        currentTokenEl.textContent = formatToken(current.token_number);
        currentTokenEl.classList.remove("no-active-token");
      } else {
        currentTokenEl.textContent = "NO ACTIVE TOKEN";
        currentTokenEl.classList.add("no-active-token");
      }
    }
    setText("currentPatientName", current ? current.patient_name : "No patient called");
    setText("waitingCountDisplay", String(data.waiting_count ?? 0));
    setText("estWaitDisplay", String(data.estimated_wait_minutes ?? 0));
    
    const yourPositionDisplay = document.getElementById("yourPositionDisplay");
    if (yourPositionDisplay) {
      yourPositionDisplay.textContent = data.waiting_count > 0 ? String(data.waiting_count) : "—";
    }
    
    updateLastUpdated();

    updateDoctorStatus(data.settings?.doctor_status);

    if (page === "dashboard") renderDashboard(data);
    if (page === "patient") renderPatient(data);
    if (page === "analytics") renderAnalyticsPage(data);
  }
  
  function updateLastUpdated() {
    const now = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    setText("lastUpdated", now);
    setText("lastUpdatedDisplay", now);
  }

  function applySettings(settings) {
    if (!settings) return;

    setText("clinicBrandName", settings.clinic_name);
    setText("patientClinicName", settings.clinic_name);
    setText("clinicInfoName", settings.clinic_name);
    setText("avgConsultDisplay", String(settings.average_consultation_time));
    setText("clinicInfoAvgTime", String(settings.average_consultation_time));
    setText("avgTimeDisplay", `Avg. consultation: ${settings.average_consultation_time} min`);

    const avgInput = document.getElementById("avgConsultTime");
    if (avgInput && document.activeElement !== avgInput) {
      avgInput.value = settings.average_consultation_time;
    }

    const clinicInput = document.getElementById("clinicNameInput");
    if (clinicInput && document.activeElement !== clinicInput) {
      clinicInput.value = settings.clinic_name;
    }

    const doctorSelect = document.getElementById("doctorStatusSelect");
    if (doctorSelect) doctorSelect.value = settings.doctor_status;
  }

  function updateDoctorStatus(status) {
    const badge = document.getElementById("doctorStatusBadge");
    if (badge) {
      badge.classList.toggle("busy", status === "busy");
      const statusIcon = status === "available" ? "🟢" : status === "busy" ? "🟠" : "🔴";
      const statusText = status.charAt(0).toUpperCase() + status.slice(1);
      badge.innerHTML = `${statusIcon} Doctor ${statusText}`;
    }

    const pill = document.getElementById("doctorStatusPill");
    if (pill) {
      pill.classList.toggle("busy", status === "busy");
      const statusIcon = status === "available" ? "🟢" : status === "busy" ? "🟠" : "🔴";
      const statusText = status.charAt(0).toUpperCase() + status.slice(1);
      let bgColor = status === "available" ? "rgba(16,185,129,0.2)" : status === "busy" ? "rgba(217,119,6,0.2)" : "rgba(220,38,38,0.2)";
      let textColor = status === "available" ? "#6ee7b7" : status === "busy" ? "#fcd34d" : "#fca5a5";
      pill.style.background = bgColor;
      pill.style.color = textColor;
      pill.innerHTML = `${statusIcon} Doctor ${statusText}`;
    }

    setText("doctorStatusDisplay", status.charAt(0).toUpperCase() + status.slice(1));
    
    const doctorStatusBadgeSmall = document.getElementById("doctorStatusBadgeSmall");
    if (doctorStatusBadgeSmall) {
      const statusIcon = status === "available" ? "🟢" : status === "busy" ? "🟠" : "🔴";
      const statusText = status.charAt(0).toUpperCase() + status.slice(1);
      doctorStatusBadgeSmall.textContent = `${statusIcon} ${statusText}`;
      let badgeClass = "bg-success";
      if (status === "busy") badgeClass = "bg-warning text-dark";
      if (status === "offline") badgeClass = "bg-danger";
      doctorStatusBadgeSmall.className = "badge " + badgeClass;
    }

    const clinicInfoDoctorStatus = document.getElementById("clinicInfoDoctorStatus");
    if (clinicInfoDoctorStatus) {
      const statusIcon = status === "available" ? "🟢" : status === "busy" ? "🟠" : "🔴";
      const statusText = status.charAt(0).toUpperCase() + status.slice(1);
      clinicInfoDoctorStatus.textContent = `${statusIcon} ${statusText}`;
      let badgeClass = "bg-success";
      if (status === "busy") badgeClass = "bg-warning text-dark";
      if (status === "offline") badgeClass = "bg-danger";
      clinicInfoDoctorStatus.className = "badge " + badgeClass;
    }
  }

  function renderAnalytics(analytics) {
    if (!analytics) return;
    setText("servedTodayDisplay", String(analytics.patients_served_today ?? 0));
    setText("totalTodayDisplay", String(analytics.total_today ?? 0));
    setText("avgWaitDisplay", String(analytics.estimated_wait_minutes ?? 0));
    setText("completionRateDisplay", String(analytics.completion_rate ?? 0));
    setText("removedTodayDisplay", String(analytics.removed_today ?? 0));

    setText("totalPatientsToday", String(analytics.total_today ?? 0));
    setText("patientsServedToday", String(analytics.patients_served_today ?? 0));
    setText("avgWaitTime", String(analytics.estimated_wait_minutes ?? 0));
    setText("completionRate", String(analytics.completion_rate ?? 0));
    setText("currentWaitingPatients", String(analytics.waiting_count ?? 0));
    setText("avgConsultationTime", String(analytics.average_consultation_time ?? 10));
    setText("peakQueueLength", String(analytics.peak_queue_length ?? 0));
    setText("queueLength", String(analytics.waiting_count ?? 0));

    // Update performance summary card
    setText("perfPatientsAdded", String(analytics.total_today ?? 0));
    setText("perfPatientsServed", String(analytics.patients_served_today ?? 0));
    setText("perfPatientsWaiting", String(analytics.waiting_count ?? 0));
    setText("perfCompletionRate", `${String(analytics.completion_rate ?? 0)}%`);

    if (analytics.current_token != null) {
      setText("currentTokenDisplay", formatToken(analytics.current_token));
      setText("currentTokenBadge", formatToken(analytics.current_token));
    } else {
      setText("currentTokenBadge", "—");
    }
    if (analytics.current_patient) {
      setText("currentPatientName", analytics.current_patient);
    }
  }

  function renderAnalyticsPage(data) {
    if (!data) return;
    
    const activityList = document.getElementById("recentActivityList");
    if (activityList) {
      if (data.activity && data.activity.length > 0) {
        activityList.innerHTML = data.activity.map(a => `
          <li class="list-group-item">
            <div class="small text-muted">${formatTime(a.timestamp)}</div>
            <div>${getActivityIcon(a.action)} ${escapeHtml(a.action)}</div>
          </li>
        `).join("");
      } else {
        activityList.innerHTML = `
          <li class="list-group-item text-muted text-center py-4">
            No activity recorded yet.<br>
            Actions such as patient additions,<br>
            token calls and queue resets<br>
            will appear here.
          </li>
        `;
      }
    }

    if (queueStatusChart && data.waiting) {
      const waitingCount = data.waiting.length;
      const calledCount = data.current ? 1 : 0;
      queueStatusChart.data.datasets[0].data = [waitingCount, calledCount, 5, 1];
      queueStatusChart.update();
    }
  }

  function renderDashboard(data) {
    const completeBtn = document.getElementById("completeBtn");
    if (completeBtn) {
      completeBtn.disabled = !data.current;
      completeBtn.dataset.patientId = data.current?.id || "";
    }

    // Update welcome card
    const welcomeWaiting = document.getElementById("welcomeWaitingPatients");
    if (welcomeWaiting) {
      welcomeWaiting.textContent = `Waiting Patients: ${data.waiting_count ?? 0}`;
    }
    const welcomeServed = document.getElementById("welcomeServedPatients");
    if (welcomeServed) {
      welcomeServed.textContent = `Patients Served: ${data.analytics?.patients_served_today ?? 0}`;
    }
    const welcomeDoctor = document.getElementById("welcomeDoctorStatus");
    if (welcomeDoctor) {
      const status = data.settings?.doctor_status ?? "available";
      const statusText = status.charAt(0).toUpperCase() + status.slice(1);
      welcomeDoctor.textContent = `Doctor Status: ${statusText}`;
    }

    renderWaitingTable(data.waiting || []);
    renderHistory(data.history || []);
    renderActivity(data.activity || []);
  }

  function renderWaitingTable(waiting) {
    const tbody = document.getElementById("waitingTableBody");
    if (!tbody) return;

    const filtered = searchQuery
      ? waiting.filter((p) => p.patient_name.toLowerCase().includes(searchQuery.toLowerCase()))
      : waiting;

    if (!filtered.length) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center py-5">
        <div class="empty-state">
          <i class="bi bi-inbox text-muted" style="font-size: 3rem;"></i>
          <h5 class="mt-3 text-muted">No Patients Waiting</h5>
          <p class="text-muted">Receptionist can add a patient to begin the queue.</p>
        </div>
      </td></tr>`;
      return;
    }

    tbody.innerHTML = filtered
      .map(
        (p) => `
      <tr>
        <td><strong>${formatToken(p.token_number)}</strong></td>
        <td>${escapeHtml(p.patient_name)}</td>
        <td class="text-muted small">${formatTime(p.created_at)}</td>
        <td class="text-end">
          <button class="btn btn-sm btn-outline-success me-1 call-btn" data-id="${p.id}" title="Call">
            <i class="bi bi-megaphone"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger remove-btn" data-id="${p.id}" data-name="${escapeHtml(p.patient_name)}" title="Remove">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>`
      )
      .join("");

    tbody.querySelectorAll(".call-btn").forEach((btn) => {
      btn.addEventListener("click", () => callPatient(parseInt(btn.dataset.id, 10)));
    });

    tbody.querySelectorAll(".remove-btn").forEach((btn) => {
      btn.addEventListener("click", () => openRemoveModal(parseInt(btn.dataset.id, 10), btn.dataset.name));
    });
  }

  function renderHistory(history) {
    const list = document.getElementById("historyList");
    if (!list) return;

    if (!history.length) {
      list.innerHTML = '<li class="list-group-item text-muted text-center">No history yet</li>';
      return;
    }

    list.innerHTML = history
      .map(
        (p) => `
      <li class="list-group-item d-flex justify-content-between align-items-center">
        <div>
          <strong>${formatToken(p.token_number)}</strong>
          <span class="ms-2">${escapeHtml(p.patient_name)}</span>
        </div>
        <div class="d-flex align-items-center gap-2">
          <span class="status-badge status-${p.status}">${p.status}</span>
          <span class="small text-muted">${formatTime(p.served_at)}</span>
        </div>
      </li>`
      )
      .join("");
  }

  function getActivityIcon(action) {
    if (action.toLowerCase().includes("patient added")) return "🟢";
    if (action.toLowerCase().includes("patient called")) return "📢";
    if (action.toLowerCase().includes("consultation completed")) return "✅";
    if (action.toLowerCase().includes("settings")) return "⚙️";
    if (action.toLowerCase().includes("queue reset")) return "🔄";
    if (action.toLowerCase().includes("patient removed")) return "❌";
    return "ℹ️";
  }

  function renderActivity(activity) {
    const list = document.getElementById("activityList");
    if (!list) return;

    if (!activity.length) {
      list.innerHTML = '<li class="list-group-item text-muted text-center">No activity yet</li>';
      return;
    }

    list.innerHTML = activity
      .map(
        (a) => `
      <li class="list-group-item">
        <div class="small text-muted">${formatTime(a.timestamp)}</div>
        <div>${getActivityIcon(a.action)} ${escapeHtml(a.action)}</div>
      </li>`
      )
      .join("");
  }

  function renderPatient(data) {
    const upcomingSection = document.getElementById("upcomingSection");
    const emptyStateSection = document.getElementById("emptyStateSection");
    const list = document.getElementById("upcomingList");

    if (!upcomingSection || !emptyStateSection || !list) return;

    const waiting = data.waiting || [];
    if (!waiting.length) {
      // Show empty state, hide upcoming section
      upcomingSection.style.display = "none";
      emptyStateSection.style.display = "block";
      return;
    }

    // Show upcoming section, hide empty state
    upcomingSection.style.display = "block";
    emptyStateSection.style.display = "none";

    list.innerHTML = waiting
      .slice(0, 8)
      .map(
        (p) => `
      <div class="col-md-3 col-6 mb-3">
        <div class="card text-center p-3">
          <div class="h3 fw-bold">${formatToken(p.token_number)}</div>
          <div class="text-secondary small">${escapeHtml(p.patient_name)}</div>
        </div>
      </div>`
      )
      .join("");
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  async function addPatient(e) {
    e.preventDefault();
    const input = document.getElementById("patientNameInput");
    const btn = document.getElementById("addPatientBtn");
    const name = input.value.trim();

    input.classList.remove("is-invalid");
    if (!name) {
      input.classList.add("is-invalid");
      document.getElementById("nameError").textContent = "Patient name is required.";
      return;
    }

    setLoading(btn, true);
    try {
      await apiRequest("/api/patients", {
        method: "POST",
        body: JSON.stringify({ patient_name: name }),
      });
      input.value = "";
    } catch (err) {
      input.classList.add("is-invalid");
      document.getElementById("nameError").textContent = err.message;
      showToast(err.message, "error");
    } finally {
      setLoading(btn, false);
    }
  }

  async function callNext() {
    const btn = document.getElementById("callNextBtn");
    setLoading(btn, true);
    try {
      await apiRequest("/api/patients/call-next", { method: "POST" });
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btn, false);
    }
  }

  async function callPatient(id) {
    try {
      await apiRequest(`/api/patients/${id}/call`, { method: "POST" });
    } catch (err) {
      showToast(err.message, "error");
    }
  }

  function openRemoveModal(id, name) {
    pendingRemoveId = id;
    setText("removePatientName", name);
    bootstrap.Modal.getOrCreateInstance(document.getElementById("removeModal")).show();
  }

  async function confirmRemove() {
    if (!pendingRemoveId) return;
    const btn = document.getElementById("confirmRemoveBtn");
    setLoading(btn, true);
    try {
      await apiRequest(`/api/patients/${pendingRemoveId}`, { method: "DELETE" });
      bootstrap.Modal.getInstance(document.getElementById("removeModal")).hide();
      pendingRemoveId = null;
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btn, false);
    }
  }

  async function completeConsultation() {
    const btn = document.getElementById("completeBtn");
    const id = btn?.dataset.patientId;
    if (!id) return;
    setLoading(btn, true);
    try {
      await apiRequest(`/api/patients/${id}/complete`, { method: "POST" });
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btn, false);
    }
  }

  async function saveSettings(e) {
    e.preventDefault();
    const btn = document.getElementById("saveSettingsBtn");
    const avgTime = parseInt(document.getElementById("avgConsultTime").value, 10);
    const clinicName = document.getElementById("clinicNameInput").value.trim();
    const doctorStatus = document.getElementById("doctorStatusSelect").value;

    setLoading(btn, true);
    try {
      await apiRequest("/api/settings", {
        method: "PUT",
        body: JSON.stringify({
          average_consultation_time: avgTime,
          clinic_name: clinicName,
          doctor_status: doctorStatus,
        }),
      });
      showToast("Settings saved", "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btn, false);
    }
  }

  function openResetModal() {
    bootstrap.Modal.getOrCreateInstance(document.getElementById("resetModal")).show();
  }

  async function confirmReset() {
    const btn = document.getElementById("confirmResetBtn");
    setLoading(btn, true);
    try {
      await apiRequest("/api/queue/reset", { method: "POST" });
      bootstrap.Modal.getInstance(document.getElementById("resetModal")).hide();
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoading(btn, false);
    }
  }

  function initCharts() {
    if (page !== "analytics") return;
    
    const isDark = document.documentElement.getAttribute("data-bs-theme") === "dark";
    const textColor = isDark ? "#cbd5e1" : "#1e293b";
    
    const flowCtx = document.getElementById("patientFlowChart");
    if (flowCtx && typeof Chart !== "undefined") {
      patientFlowChart = new Chart(flowCtx, {
        type: "line",
        data: {
          labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
          datasets: [{
            label: "Patients Added",
            data: [0, 0, 5, 12, 8, 3],
            borderColor: "#2563eb",
            backgroundColor: "rgba(37, 99, 235, 0.1)",
            fill: true,
            tension: 0.4
          }, {
            label: "Patients Served",
            data: [0, 0, 4, 10, 7, 3],
            borderColor: "#059669",
            backgroundColor: "rgba(5, 150, 105, 0.1)",
            fill: true,
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              labels: { color: textColor }
            }
          },
          scales: {
            x: {
              ticks: { color: textColor },
              grid: { color: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.05)" }
            },
            y: {
              ticks: { color: textColor },
              grid: { color: isDark ? "rgba(255,255,255,0.1)" : "rgba(0,0,0,0.05)" }
            }
          }
        }
      });
    }
    
    const statusCtx = document.getElementById("queueStatusChart");
    if (statusCtx && typeof Chart !== "undefined") {
      queueStatusChart = new Chart(statusCtx, {
        type: "doughnut",
        data: {
          labels: ["Waiting", "Called", "Served", "Removed"],
          datasets: [{
            data: [0, 0, 5, 1],
            backgroundColor: ["#2563eb", "#d97706", "#059669", "#dc2626"]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "bottom",
              labels: { color: textColor }
            }
          }
        }
      });
    }
  }

  function initAnalyticsPage() {
    if (page !== "analytics") return;
    
    const resetBtn = document.getElementById("resetQueueBtn");
    if (resetBtn) {
      resetBtn.addEventListener("click", openResetModal);
    }
    const confirmResetBtn = document.getElementById("confirmResetBtn");
    if (confirmResetBtn) {
      confirmResetBtn.addEventListener("click", confirmReset);
    }
    
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    initCharts();
    startLastUpdatedTimer();
  }

  function initDashboard() {
    document.getElementById("addPatientForm")?.addEventListener("submit", addPatient);
    document.getElementById("callNextBtn")?.addEventListener("click", callNext);
    document.getElementById("completeBtn")?.addEventListener("click", completeConsultation);
    document.getElementById("settingsForm")?.addEventListener("submit", saveSettings);
    document.getElementById("resetQueueBtn")?.addEventListener("click", openResetModal);
    document.getElementById("confirmRemoveBtn")?.addEventListener("click", confirmRemove);
    document.getElementById("confirmResetBtn")?.addEventListener("click", confirmReset);

    document.getElementById("searchPatientInput")?.addEventListener("input", (e) => {
      searchQuery = e.target.value;
      if (state) renderWaitingTable(state.waiting || []);
    });
  }

  function initFooterYear() {
    const year = new Date().getFullYear();
    // Update all footers
    const footers = document.querySelectorAll('footer');
    footers.forEach(footer => {
      const strongElement = footer.querySelector('strong');
      if (strongElement) {
        strongElement.innerHTML = `Queue Cure 2026 © ${year}`;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    if (page === "dashboard") initDashboard();
    if (page === "analytics") initAnalyticsPage();
    initDarkMode();
    if (document.getElementById("currentTimeDisplay")) startClock();
    initFooterYear();
    initSocket();
  });
})();
