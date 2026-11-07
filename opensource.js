(() => {
  "use strict";

  const container = document.getElementById("github-activity");
  if (!container) return;

  const updated = document.getElementById("github-activity-updated");
  const mergedCount = document.getElementById("github-merged-count");
  const openCount = document.getElementById("github-open-count");
  const statusMeta = {
    merged: { label: "Merged", className: "badge-success" },
    open: { label: "Under review", className: "badge-warning" },
  };
  const themeLabels = {
    "formal-proof": "Formal proof",
    "verifiable-software": "Verifiable software",
    control: "Control",
    quantitative: "Quantitative",
    other: "Other",
  };

  const formatDate = (value) => {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const setCount = (node, count) => {
    if (!node || typeof count !== "number") return;
    node.textContent = `${count} PR${count === 1 ? "" : "s"}`;
  };

  const renderFallback = (message) => {
    container.replaceChildren();
    const note = document.createElement("p");
    note.className = "small text-muted mb-0";
    note.append(message);
    const link = document.createElement("a");
    link.href = "https://github.com/Qunsheng-Zhang";
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "View GitHub";
    note.append(" ", link);
    container.append(note);
  };

  fetch("data/github-contributions.json", { cache: "no-store" })
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      const items = (Array.isArray(data.items) ? data.items : []).filter(
        (item) => item.status === "merged" || item.status === "open"
      );

      setCount(mergedCount, data.counts?.merged ?? items.filter((item) => item.status === "merged").length);
      setCount(openCount, data.counts?.open ?? items.filter((item) => item.status === "open").length);

      if (updated) {
        const stamp = new Date(data.generated_at);
        updated.textContent = Number.isNaN(stamp.getTime())
          ? ""
          : `Last synced: ${stamp.toISOString().slice(0, 16).replace("T", " ")} UTC`;
      }

      if (!items.length) {
        renderFallback("No public merged or open pull requests found yet.");
        return;
      }

      container.replaceChildren();
      items.forEach((item) => {
        const row = document.createElement("div");
        row.className = "timeline-item";

        const main = document.createElement("div");
        main.className = "timeline-main";

        const title = document.createElement("div");
        title.className = "timeline-title";
        const link = document.createElement("a");
        link.href = item.url;
        link.target = "_blank";
        link.rel = "noreferrer";
        link.textContent = item.title;
        title.append(link);

        const sub = document.createElement("div");
        sub.className = "timeline-sub";
        sub.textContent = `${item.repo} · #${item.number}`;

        const meta = document.createElement("div");
        meta.className = "timeline-meta";
        const status = statusMeta[item.status] || {
          label: "Closed",
          className: "badge-light",
        };
        const statusBadge = document.createElement("span");
        statusBadge.className = `badge ${status.className}`;
        statusBadge.textContent = status.label;

        const themeBadge = document.createElement("span");
        themeBadge.className = "badge badge-light";
        themeBadge.style.marginLeft = "0.35rem";
        themeBadge.textContent = themeLabels[item.theme] || "Other";

        const date = document.createElement("em");
        date.textContent = formatDate(item.updated_at);

        meta.append(statusBadge, themeBadge, date);
        main.append(title, sub, meta);
        row.append(main);
        container.append(row);
      });
    })
    .catch(() => {
      if (updated) updated.textContent = "";
      renderFallback("Live GitHub activity is temporarily unavailable.");
    });
})();
