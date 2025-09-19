

// Load HPO dictionary from JSON
let HPO_DICT = {};

fetch("/assets/ontologies/hpo_terms.json")
  .then(res => res.json())
  .then(data => {
    const nodes = data.graphs?.[0]?.nodes || [];
    for (const node of nodes) {
      if (node.lbl) {
        const term = node.lbl.toLowerCase();
        HPO_DICT[term] = {
          id: node.id,
          definition: node.meta?.definition?.val || "",
          synonyms: node.meta?.synonyms?.map(s => s.val) || []
        };
      }
    }
  })
  .catch(err => console.error("Failed to load HPO terms:", err));

// Attach popup behavior to .hpo-term elements
document.addEventListener("mouseover", (e) => {
  const el = e.target.closest(".hpo-term");
  if (!el) return;

  const key = el.textContent.trim().toLowerCase();
  const data = HPO_DICT[key];
  if (!data) return;

  showTooltip(el, data);
});

function showTooltip(target, data) {
  let tooltip = document.getElementById("hpo-tooltip");
  if (!tooltip) {
    tooltip = document.createElement("div");
    tooltip.id = "hpo-tooltip";
    tooltip.style.position = "absolute";
    tooltip.style.zIndex = "9999";
    tooltip.style.backgroundColor = "#fff";
    tooltip.style.border = "1px solid #ccc";
    tooltip.style.padding = "8px";
    tooltip.style.maxWidth = "300px";
    tooltip.style.fontSize = "0.9em";
    tooltip.style.boxShadow = "0px 2px 6px rgba(0,0,0,0.2)";
    tooltip.style.pointerEvents = "none";
    tooltip.style.transition = "opacity 0.2s ease";
    document.body.appendChild(tooltip);
  }

  tooltip.innerHTML = `
    <strong>${target.textContent}</strong><br>
    <em>${data.definition}</em><br>
    <small>${data.id}</small>
  `;

  const rect = target.getBoundingClientRect();
  tooltip.style.top = `${rect.bottom + window.scrollY + 6}px`;
  tooltip.style.left = `${rect.left + window.scrollX}px`;
  tooltip.style.opacity = "1";

  target.addEventListener("mouseleave", () => {
    tooltip.style.opacity = "0";
  }, { once: true });
}