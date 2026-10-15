// Small browser enhancements. The analysis itself runs in Python.
const form = document.getElementById("resume-form");
if (form) {
  const resume = document.getElementById("resume-text");
  const file = document.getElementById("resume-file");
  const status = document.getElementById("form-status");
  const button = document.getElementById("analyze-button");
  resume.addEventListener("input", () => {
    document.getElementById("resume-count").textContent = `${resume.value.length} / 30,000`;
  });
  form.addEventListener("submit", (event) => {
    const hasText = resume.value.trim().length > 0;
    const hasFile = file.files.length > 0;
    if (hasText === hasFile) {
      event.preventDefault();
      status.textContent = hasText ? "Choose one input: clear the file or the pasted text." : "Upload a file or paste your resume first.";
      return;
    }
    if (hasFile && file.files[0].size > 5 * 1024 * 1024) {
      event.preventDefault();
      status.textContent = "Please use a file smaller than 5 MB.";
      return;
    }
    button.disabled = true;
    button.textContent = "Reading your resume…";
    status.textContent = document.getElementById("use-ai").checked
      ? "Analyzing locally, then requesting AI feedback. This can take about a minute."
      : "Checking structure, wording and skills…";
  });
  // Browsers can restore a disabled button when navigating Back.
  window.addEventListener("pageshow", () => {
    button.disabled = false;
    button.textContent = "Analyze my resume →";
  });
}

function downloadFile(text, filename, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const reportData = document.getElementById("report-data");
if (reportData) {
  const report = JSON.parse(reportData.textContent);
  const text = JSON.parse(document.getElementById("report-text").textContent);
  document.getElementById("download-text").addEventListener("click", () => {
    downloadFile(text, "resume-report.txt", "text/plain;charset=utf-8");
  });
  document.getElementById("download-json").addEventListener("click", () => {
    downloadFile(JSON.stringify(report, null, 2), "resume-report.json", "application/json");
  });
  document.getElementById("print-report").addEventListener("click", () => window.print());
  // Include every diagnostic in a printed report, even if collapsed on screen.
  let openDetails = [];
  window.addEventListener("beforeprint", () => {
    openDetails = Array.from(document.querySelectorAll("details")).filter(item => item.open);
    document.querySelectorAll("details").forEach(item => { item.open = true; });
  });
  window.addEventListener("afterprint", () => {
    document.querySelectorAll("details").forEach(item => { item.open = openDetails.includes(item); });
  });
}
