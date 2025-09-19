const pageRank = {
  glossary: 1,
  triads: 2,
  associations: 3,
  labs: 4,
  pharm: 5
};
let searchIndex = [];

async function loadSearchIndex() {
  const res = await fetch("/study_tables/assets/search_index.json");
  searchIndex = await res.json();
}

function filterSuggestions(query) {
  const q = query.trim().toLowerCase();
  if (!q) return [];

  const seen = new Set();
  return searchIndex
    .filter(entry => entry.term.includes(q))
    .filter(entry => {
      const key = `${entry.term}-${entry.page}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .sort((a, b) => {
      const rankA = pageRank[a.page.replace(".html", "")] || 999;
      const rankB = pageRank[b.page.replace(".html", "")] || 999;
      return rankA - rankB;
    })
    .slice(0, 15);
}

function setupSearch() {
  const input = document.getElementById("searchInput");
  const datalist = document.getElementById("tableSuggestions");
  if (!input || !datalist) return;

  input.addEventListener("input", () => {
    const results = filterSuggestions(input.value);
    const container = document.getElementById("searchResults");
    container.innerHTML = "";
    if (!results.length) {
      container.style.display = "none";
      return;
    }

    let lastSection = null;
    results.forEach(entry => {
      const section = entry.section || entry.page.replace(".html", "").replace(/-/g, " ");
      if (section !== lastSection) {
        const header = document.createElement("div");
        header.textContent = section;
        header.className = "search-group-header";
        container.appendChild(header);
        lastSection = section;
      }

      const div = document.createElement("div");
      div.className = "search-result";
      div.innerHTML = `<strong>${entry.term}</strong>`;
      div.onclick = () => {
        const url = `pages/${entry.page}#highlight-${encodeURIComponent(entry.term)}`;
        window.location.href = url;
      };
      container.appendChild(div);
    });

    container.style.display = "block";
  });

  document.addEventListener("click", (e) => {
    if (!document.getElementById("searchResults").contains(e.target) &&
        e.target !== document.getElementById("searchInput")) {
      document.getElementById("searchResults").style.display = "none";
    }
  });

  input.addEventListener("change", () => {
    const val = input.value;
    const match = searchIndex.find(entry => {
      const pageName = entry.page.replace(".html", "").replace(/-/g, " ");
      return val === `${entry.term}  —  ${pageName}`;
    });
    if (match) {
      const url = `pages/${match.page}#highlight-${encodeURIComponent(match.term)}`;
      window.location.href = url;
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadSearchIndex();
  setupSearch();
  const hash = decodeURIComponent(location.hash);
  if (hash.startsWith("#highlight-")) {
    const term = hash.replace("#highlight-", "").toLowerCase();
    const cells = Array.from(document.querySelectorAll("td"));

    for (const cell of cells) {
      if (cell.textContent.toLowerCase().includes(term)) {
        cell.scrollIntoView({ behavior: "smooth", block: "center" });
        cell.classList.add("highlight-temp");
        break;
      }
    }

    // Clear highlight on next click
    document.addEventListener("click", () => {
      document.querySelectorAll(".highlight-temp").forEach(el => el.classList.remove("highlight-temp"));
    }, { once: true });
  }
});