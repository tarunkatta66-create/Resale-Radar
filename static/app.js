/**
 * ResaleRadar — Frontend Application Engine
 * Vanilla JavaScript + Chart.js
 */

(function () {
  "use strict";

  // App State
  let currentDeviceType = "smartphone";
  let apiOptions = null;
  let apiMetrics = null;
  let modelCompareChart = null;
  let importanceChart = null;

  // DOM Elements
  const tabSmartphone = document.getElementById("tabSmartphone");
  const tabLaptop = document.getElementById("tabLaptop");
  const formLoadingState = document.getElementById("formLoadingState");
  const formFieldsContainer = document.getElementById("formFieldsContainer");
  const valuationForm = document.getElementById("valuationForm");
  const submitBtn = document.getElementById("submitBtn");
  const formError = document.getElementById("formError");

  const emptyState = document.getElementById("emptyState");
  const loadingState = document.getElementById("loadingState");
  const resultContent = document.getElementById("resultContent");

  const resSerial = document.getElementById("resSerial");
  const resDeprBadge = document.getElementById("resDeprBadge");
  const resEstimatedPrice = document.getElementById("resEstimatedPrice");
  const resPriceRange = document.getElementById("resPriceRange");
  const resTopFactors = document.getElementById("resTopFactors");
  const resDisclaimer = document.getElementById("resDisclaimer");
  const rfDeviceBadge = document.getElementById("rfDeviceBadge");
  const metricsTableBody = document.getElementById("metricsTableBody");
  const engineStatus = document.getElementById("engineStatus");

  // Number Formatter
  const inrFormatter = new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  });

  // Initialization
  async function init() {
    setupTabSwitching();
    valuationForm.addEventListener("submit", handleFormSubmit);

    try {
      await Promise.all([fetchOptions(), fetchMetrics(), checkHealth()]);
      renderForm(currentDeviceType);
      renderMetricsTable();
      renderImportanceChart(currentDeviceType);
      submitBtn.disabled = false;

      // Auto-demo if requested via query param (e.g., for automated verification or screenshots)
      const urlParams = new URLSearchParams(window.location.search);
      const demoParam = urlParams.get("demo");
      if (demoParam === "laptop") {
        switchDeviceType("laptop");
        setTimeout(() => valuationForm.dispatchEvent(new Event("submit")), 400);
      } else if (demoParam === "smartphone" || demoParam === "1") {
        setTimeout(() => valuationForm.dispatchEvent(new Event("submit")), 400);
      }
    } catch (err) {
      showError("Failed to initialize pricing engine: " + err.message);
    }
  }

  // API Calls
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      const data = await res.json();
      if (data.status === "ok") {
        engineStatus.textContent = "ENGINE ONLINE";
      }
    } catch (e) {
      engineStatus.textContent = "OFFLINE";
      engineStatus.style.color = "var(--danger-red)";
    }
  }

  async function fetchOptions() {
    const res = await fetch("/api/options");
    if (!res.ok) throw new Error("Could not load form options");
    apiOptions = await res.json();
  }

  async function fetchMetrics() {
    const res = await fetch("/api/metrics");
    if (!res.ok) throw new Error("Could not load model benchmarks");
    apiMetrics = await res.json();
  }

  // Tab Switching
  function setupTabSwitching() {
    tabSmartphone.addEventListener("click", () => switchDeviceType("smartphone"));
    tabLaptop.addEventListener("click", () => switchDeviceType("laptop"));
  }

  function switchDeviceType(type) {
    if (currentDeviceType === type) return;
    currentDeviceType = type;

    if (type === "smartphone") {
      tabSmartphone.classList.add("active");
      tabSmartphone.setAttribute("aria-selected", "true");
      tabLaptop.classList.remove("active");
      tabLaptop.setAttribute("aria-selected", "false");
    } else {
      tabLaptop.classList.add("active");
      tabLaptop.setAttribute("aria-selected", "true");
      tabSmartphone.classList.remove("active");
      tabSmartphone.setAttribute("aria-selected", "false");
    }

    renderForm(type);
    renderImportanceChart(type);
    hideError();
  }

  // Dynamic Form Rendering
  function renderForm(deviceType) {
    if (!apiOptions || !apiOptions[deviceType]) return;
    const opt = apiOptions[deviceType];

    formLoadingState.style.display = "none";
    formFieldsContainer.style.display = "block";
    formFieldsContainer.innerHTML = "";

    // Group 1: Basics
    const group1 = document.createElement("div");
    group1.className = "form-group-block";
    group1.innerHTML = `
      <div class="group-title">1. Device Identification</div>
      <div class="grid-2">
        <div class="form-field">
          <label class="field-label" for="fieldBrand">Brand / Manufacturer</label>
          <select id="fieldBrand" name="brand" class="select-control" required>
            ${opt.brands.map((b) => `<option value="${b}">${b}</option>`).join("")}
          </select>
        </div>
        <div class="form-field">
          <label class="field-label" for="fieldOriginalPrice">Original Retail Price</label>
          <div class="currency-input-wrapper">
            <span class="input-prefix">₹</span>
            <input type="number" id="fieldOriginalPrice" name="original_price" class="input-control"
              min="${opt.ranges.original_price.min}" max="${opt.ranges.original_price.max}"
              step="${opt.ranges.original_price.step}" value="${opt.ranges.original_price.default}" required>
          </div>
          <div class="range-markers">
            <span>Min ₹${inrFormatter.format(opt.ranges.original_price.min)}</span>
            <span>Max ₹${inrFormatter.format(opt.ranges.original_price.max)}</span>
          </div>
        </div>
      </div>
    `;
    formFieldsContainer.appendChild(group1);

    // Group 2: Hardware Specs
    const group2 = document.createElement("div");
    group2.className = "form-group-block";

    if (deviceType === "smartphone") {
      group2.innerHTML = `
        <div class="group-title">2. Hardware Specifications</div>
        <div class="grid-2">
          <div class="form-field">
            <label class="field-label" for="fieldStorage">Storage Capacity</label>
            <select id="fieldStorage" name="storage_gb" class="select-control" required>
              ${opt.storage_gb.map((s) => `<option value="${s}" ${s === 128 ? "selected" : ""}>${s} GB</option>`).join("")}
            </select>
          </div>
          <div class="form-field">
            <label class="field-label" for="fieldRam">RAM Capacity</label>
            <select id="fieldRam" name="ram_gb" class="select-control" required>
              ${opt.ram_gb.map((r) => `<option value="${r}" ${r === 6 ? "selected" : ""}>${r} GB RAM</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-field">
            <label class="field-label" for="fieldProcTier">Processor Class</label>
            <select id="fieldProcTier" name="processor_tier" class="select-control" required>
              ${opt.processor_tiers.map((t) => `<option value="${t}" ${t === "Mid" ? "selected" : ""}>${t} Tier</option>`).join("")}
            </select>
          </div>
          <div class="form-field">
            <label class="field-label" for="fieldBoxBill">Documentation &amp; Packaging</label>
            <select id="fieldBoxBill" name="has_box_and_bill" class="select-control" required>
              ${opt.has_box_and_bill.map((bb) => `<option value="${bb.value}">${bb.label}</option>`).join("")}
            </select>
          </div>
        </div>
      `;
    } else {
      group2.innerHTML = `
        <div class="group-title">2. Hardware Specifications</div>
        <div class="grid-2">
          <div class="form-field">
            <label class="field-label" for="fieldCpuTier">Processor Tier</label>
            <select id="fieldCpuTier" name="cpu_tier" class="select-control" required>
              ${opt.cpu_tiers.map((c) => `<option value="${c}" ${c.includes("i5") ? "selected" : ""}>${c}</option>`).join("")}
            </select>
          </div>
          <div class="form-field">
            <label class="field-label" for="fieldRam">RAM Capacity</label>
            <select id="fieldRam" name="ram_gb" class="select-control" required>
              ${opt.ram_gb.map((r) => `<option value="${r}" ${r === 16 ? "selected" : ""}>${r} GB RAM</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-field">
            <label class="field-label" for="fieldStorage">Storage Size</label>
            <select id="fieldStorage" name="storage_gb" class="select-control" required>
              ${opt.storage_gb.map((s) => `<option value="${s}" ${s === 512 ? "selected" : ""}>${s >= 1024 ? s / 1024 + " TB" : s + " GB"}</option>`).join("")}
            </select>
          </div>
          <div class="form-field">
            <label class="field-label" for="fieldStorageType">Storage Drive Type</label>
            <select id="fieldStorageType" name="storage_type" class="select-control" required>
              ${opt.storage_types.map((st) => `<option value="${st}" ${st === "SSD" ? "selected" : ""}>${st} (Fast Drive)</option>`).join("")}
            </select>
          </div>
        </div>
        <div class="grid-2">
          <div class="form-field">
            <label class="field-label" for="fieldGpu">GPU Type</label>
            <select id="fieldGpu" name="gpu_type" class="select-control" required>
              ${opt.gpu_types.map((g) => `<option value="${g}">${g} Graphics</option>`).join("")}
            </select>
          </div>
          <div class="form-field">
            <label class="field-label" for="fieldScreen">Screen Size</label>
            <select id="fieldScreen" name="screen_size_in" class="select-control" required>
              ${opt.screen_sizes.map((sc) => `<option value="${sc}" ${sc === 15.6 ? "selected" : ""}>${sc}" Display</option>`).join("")}
            </select>
          </div>
        </div>
      `;
    }
    formFieldsContainer.appendChild(group2);

    // Group 3: Condition & Age
    const group3 = document.createElement("div");
    group3.className = "form-group-block";
    const ageDefault = opt.ranges.age_months.default;
    const battDefault = opt.ranges.battery_health_pct.default;

    group3.innerHTML = `
      <div class="group-title">3. Wear &amp; Tear Assessment</div>
      <div class="form-field">
        <label class="field-label" for="fieldCondition">Physical Cosmetic State</label>
        <select id="fieldCondition" name="condition" class="select-control" required>
          ${opt.conditions.map((c) => `<option value="${c}" ${c === "Good" ? "selected" : ""}>${c} (${c === "Like New" ? "Mint / Flawless" : c === "Good" ? "Minor Micro-scratches" : c === "Fair" ? "Visible Scuffs & Dents" : "Heavy Wear / Scratches"})</option>`).join("")}
        </select>
      </div>

      <div class="grid-2">
        <div class="form-field">
          <label class="field-label" for="sliderAge">
            <span>Device Age</span>
            <span class="field-value-live" id="labelAgeVal">${ageDefault} months</span>
          </label>
          <input type="range" id="sliderAge" name="age_months" class="range-slider"
            min="${opt.ranges.age_months.min}" max="${opt.ranges.age_months.max}"
            value="${ageDefault}" step="1">
          <div class="range-markers">
            <span>1 mo</span>
            <span>${opt.ranges.age_months.max} mos</span>
          </div>
        </div>

        <div class="form-field">
          <label class="field-label" for="sliderBattery">
            <span>Battery Health</span>
            <span class="field-value-live" id="labelBatteryVal">${battDefault}%</span>
          </label>
          <input type="range" id="sliderBattery" name="battery_health_pct" class="range-slider"
            min="${opt.ranges.battery_health_pct.min}" max="${opt.ranges.battery_health_pct.max}"
            value="${battDefault}" step="1">
          <div class="range-markers">
            <span>${opt.ranges.battery_health_pct.min}%</span>
            <span>100%</span>
          </div>
        </div>
      </div>
    `;
    formFieldsContainer.appendChild(group3);

    // Wire live slider labels
    const sliderAge = document.getElementById("sliderAge");
    const labelAgeVal = document.getElementById("labelAgeVal");
    sliderAge.addEventListener("input", (e) => {
      labelAgeVal.textContent = `${e.target.value} month${e.target.value > 1 ? "s" : ""}`;
    });

    const sliderBattery = document.getElementById("sliderBattery");
    const labelBatteryVal = document.getElementById("labelBatteryVal");
    sliderBattery.addEventListener("input", (e) => {
      labelBatteryVal.textContent = `${e.target.value}%`;
    });
  }

  // Form Submission
  async function handleFormSubmit(e) {
    e.preventDefault();
    hideError();

    const formData = new FormData(valuationForm);
    const payload = {
      device_type: currentDeviceType,
      brand: formData.get("brand"),
      original_price: parseFloat(formData.get("original_price")),
      age_months: parseInt(formData.get("age_months"), 10),
      condition: formData.get("condition"),
      storage_gb: parseInt(formData.get("storage_gb"), 10),
      ram_gb: parseInt(formData.get("ram_gb"), 10),
      battery_health_pct: parseInt(formData.get("battery_health_pct"), 10),
    };

    if (currentDeviceType === "smartphone") {
      payload.processor_tier = formData.get("processor_tier");
      payload.has_box_and_bill = parseInt(formData.get("has_box_and_bill"), 10);
    } else {
      payload.cpu_tier = formData.get("cpu_tier");
      payload.storage_type = formData.get("storage_type");
      payload.gpu_type = formData.get("gpu_type");
      payload.screen_size_in = parseFloat(formData.get("screen_size_in"));
    }

    // Set UI to loading
    setLoading(true);

    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        const detail = errJson.detail
          ? Array.isArray(errJson.detail)
            ? errJson.detail.join(", ")
            : errJson.detail
          : "Server rejected prediction payload";
        throw new Error(detail);
      }

      const result = await response.json();
      displayResult(result);
    } catch (err) {
      showError(err.message || "Failed to calculate valuation.");
    } finally {
      setLoading(false);
    }
  }

  function setLoading(isLoading) {
    if (isLoading) {
      submitBtn.disabled = true;
      submitBtn.classList.add("loading");
      emptyState.style.display = "none";
      resultContent.style.display = "none";
      loadingState.style.display = "flex";
    } else {
      submitBtn.disabled = false;
      submitBtn.classList.remove("loading");
      loadingState.style.display = "none";
    }
  }

  function displayResult(result) {
    emptyState.style.display = "none";
    loadingState.style.display = "none";
    resultContent.style.display = "block";

    // Random serial tag for classified counter feel
    const randomSerial = "RR-" + Math.floor(1000 + Math.random() * 9000);
    resSerial.textContent = `TAG #${randomSerial}`;

    // Depreciation badge
    resDeprBadge.textContent = `− ${result.depreciation_pct}% VALUE LOST`;

    // Count-up animation for estimated price
    animateNumber(resEstimatedPrice, 0, result.estimated_price, 900);

    // Fair trade range
    resPriceRange.textContent = `₹ ${inrFormatter.format(result.price_low)} — ₹ ${inrFormatter.format(result.price_high)}`;

    // Top drivers
    resTopFactors.innerHTML = "";
    result.top_factors.forEach((factor) => {
      const li = document.createElement("li");
      li.textContent = factor;
      resTopFactors.appendChild(li);
    });

    // Disclaimer
    resDisclaimer.textContent = result.disclaimer;

    // Render Model Comparison Chart
    renderModelComparisonChart(result.per_model_predictions);
  }

  // Count up animation
  function animateNumber(element, start, end, duration) {
    const startTime = performance.now();
    function update(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1.0);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.floor(start + (end - start) * eased);
      element.textContent = inrFormatter.format(current);

      if (progress < 1.0) {
        requestAnimationFrame(update);
      } else {
        element.textContent = inrFormatter.format(end);
      }
    }
    requestAnimationFrame(update);
  }

  // Model Comparison Chart
  function renderModelComparisonChart(perModel) {
    const ctx = document.getElementById("modelCompareChart").getContext("2d");
    if (modelCompareChart) {
      modelCompareChart.destroy();
    }

    const labels = ["Linear Regression", "Decision Tree", "Random Forest (Selected)"];
    const values = [perModel.linear, perModel.tree, perModel.forest];
    const backgroundColors = ["#8C8479", "#1F5E4B", "#FF5A1F"];

    modelCompareChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Estimated Resale Price (₹)",
            data: values,
            backgroundColor: backgroundColors,
            borderColor: "#1B1B1B",
            borderWidth: 1.5,
            borderRadius: 2,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => ` ₹ ${inrFormatter.format(context.raw)}`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: "#E5DEC9" },
            ticks: {
              font: { family: "IBM Plex Mono", size: 10 },
              callback: (val) => "₹" + inrFormatter.format(val),
            },
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { family: "Inter", size: 11, weight: 600 },
              color: "#1B1B1B",
            },
          },
        },
      },
    });
  }

  // Feature Importance Chart
  function renderImportanceChart(deviceType) {
    if (!apiMetrics || !apiMetrics[deviceType]) return;
    const deviceData = apiMetrics[deviceType];
    const features = deviceData.feature_importances;

    rfDeviceBadge.textContent = `${deviceType.toUpperCase()} ENGINE`;

    const ctx = document.getElementById("importanceChart").getContext("2d");
    if (importanceChart) {
      importanceChart.destroy();
    }

    const labels = features.map((f) => f.feature);
    const dataVals = features.map((f) => (f.importance * 100).toFixed(1));

    importanceChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Relative Importance (%)",
            data: dataVals,
            backgroundColor: "#1F5E4B",
            hoverBackgroundColor: "#FF5A1F",
            borderColor: "#1B1B1B",
            borderWidth: 1.5,
            borderRadius: 2,
          },
        ],
      },
      options: {
        indexAxis: "y",
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => ` ${ctx.raw}% relative weight`,
            },
          },
        },
        scales: {
          x: {
            grid: { color: "#E5DEC9" },
            ticks: {
              font: { family: "IBM Plex Mono", size: 10 },
              callback: (val) => val + "%",
            },
          },
          y: {
            grid: { display: false },
            ticks: {
              font: { family: "Inter", size: 11, weight: 500 },
              color: "#1B1B1B",
            },
          },
        },
      },
    });
  }

  // Model Performance Table
  function renderMetricsTable() {
    if (!apiMetrics) return;
    metricsTableBody.innerHTML = "";

    const devices = ["smartphone", "laptop"];
    devices.forEach((dev) => {
      const devMetrics = apiMetrics[dev];
      const models = devMetrics.models;
      const bestModel = devMetrics.best_model;

      for (const [modelName, m] of Object.entries(models)) {
        const tr = document.createElement("tr");
        const isBest = modelName === bestModel;
        if (isBest) tr.className = "best-row";

        const devLabel = dev === "smartphone" ? "Smartphone" : "Laptop";
        const modelLabel =
          modelName === "linear"
            ? "Linear Reg."
            : modelName === "tree"
            ? "Decision Tree"
            : "Random Forest";

        tr.innerHTML = `
          <td>${devLabel}</td>
          <td>${modelLabel}${isBest ? ' <span class="best-badge">BEST</span>' : ""}</td>
          <td>₹${inrFormatter.format(m.mae)}</td>
          <td>₹${inrFormatter.format(m.rmse)}</td>
          <td>${m.r2.toFixed(4)}</td>
        `;
        metricsTableBody.appendChild(tr);
      }
    });
  }

  function showError(msg) {
    formError.textContent = msg;
    formError.style.display = "block";
  }

  function hideError() {
    formError.textContent = "";
    formError.style.display = "none";
  }

  // Start on DOMContentLoaded
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
