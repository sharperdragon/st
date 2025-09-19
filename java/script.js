/*** ─── BUZZWORDS ───────────────────────────────────────────── **/
function injectBuzzScrollCSS(duration) {
  const style = document.createElement("style");
  style.innerHTML = `
    .buzz-track {
      --scroll-duration: ${duration}s;
      animation: scroll-buzz var(--scroll-duration) linear infinite;
      will-change: transform;
    }
    .buzz-track.paused {
      animation-play-state: paused;
      transform: translateY(1px);
    }
    @keyframes scroll-buzz {
      0% { transform: translateX(0); }
      100% { transform: translateX(-100%); }
    }
  `;
  document.head.appendChild(style);
}

function loadBuzzwords() {
  const track = document.querySelector(".buzz-track");
  if (!track) return;

  fetch("/STEVEL-1-Summaries/static/data/buzzwords.json")
    .then(response => response.json())
    .then(data => {
      const items = Array.isArray(data)
        ? data.map(item => `<span class="buzzword"><strong>${item.term}</strong><span class="assoc"> — ${item.assoc}</span></span>`)
        : Object.entries(data).map(([term, assoc]) => `<span class="buzzword"><strong>${term}</strong><span class="assoc"> — ${assoc}</span></span>`);

      const itemCount = items.length;
      const randomOffset = Math.floor(Math.random() * itemCount);
      const previewItems = items.slice(randomOffset).concat(items.slice(0, randomOffset));
      track.innerHTML = previewItems.join("    ");
      // Ensure the buzz-track is wide enough to trigger scrolling
      track.style.minWidth = `${previewItems.length * 240}px`;
      // remove inline transform so CSS animation works
      track.style.removeProperty("transform");

      // Add hover event listeners to toggle .paused class for smooth transition
      track.addEventListener("mouseenter", () => {
        track.classList.add("paused");
      });
      track.addEventListener("mouseleave", () => {
        track.classList.remove("paused");
      });

      requestAnimationFrame(() => {
        const fullWidth = track.scrollWidth;
        const speedPxPerSec = 60;
        const duration = Math.max(20, Math.round(fullWidth / speedPxPerSec));
        injectBuzzScrollCSS(duration);
      });
    })
    .catch(err => {
      console.error("❌ Failed to load buzzwords:", err);
      track.textContent = "Buzzwords unavailable.";
    });
}

/*** ─── RAPID REVIEW CARDS ─────────────────────────────────── **/
function loadRapidReviewCards() {
  const container = document.getElementById("RapidCarousel");
  if (!container) return;

  fetch("/STEVEL-1-Summaries/static/data/rapid_cards.json")
    .then(res => res.json())
    .then(data => {
      const items = data.map(entry => `
        <div class="carousel-item">
          <div class="question">${entry.question}</div>
          <div class="answer">${entry.answer}</div>
        </div>
      `).join("");
      container.innerHTML = items;
      container.querySelectorAll(".answer").forEach(a => a.style.opacity = "0");
      setupRapidCarousel(); // initialize carousel only after loading
    })
    .catch(err => {
      console.error("❌ Failed to load rapid review cards:", err);
      container.innerHTML = "<p style='color:#777;'>Rapid Review unavailable.</p>";
    });
}

function setupRapidCarousel() {
  const container = document.getElementById("RapidCarousel");
  if (!container) return;

  const items = container.querySelectorAll(".carousel-item");
  if (items.length === 0) {
    container.innerHTML = "<p style='color:#777;'>Rapid Review Carousel coming soon.</p>";
    return;
  }

  let index = 0;

  const rotate = () => {
    items.forEach((item, i) => {
      item.style.display = i === index ? "block" : "none";
    });

    const currentItem = items[index];
    const answer = currentItem.querySelector(".answer");
    if (answer) {
      answer.style.opacity = "0";
      answer.classList.remove("revealed");

      let hovered = false;

      currentItem.addEventListener("mouseenter", () => {
        hovered = true;
        answer.style.opacity = "1";
      });

      currentItem.addEventListener("mouseleave", () => {
        hovered = false;
      });

      setTimeout(() => {
        if (!hovered) {
          answer.style.opacity = "1";
          answer.classList.add("revealed");
        }
      }, 8000);
    }

    index = (index + 1) % items.length;
  };

  rotate();
  setInterval(rotate, 9600); // Rotate every 9 seconds
}

function resizeCarouselFont() {
  const container = document.getElementById("RapidCarousel");
  if (!container) return;

  const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
  const baseSize = Math.max(12, Math.min(22, vw * 0.018)); // clamp between 14px–18px
  container.style.fontSize = `${baseSize}px`;
}

/*** ─── SEARCH FUNCTIONALITY ───────────────────────────────── **/
function filterCards() {
  const input = document.getElementById("searchInput").value.toLowerCase();
  const cards = document.querySelectorAll(".data-co");
  cards.forEach(card => {
    const text = card.textContent.toLowerCase();
    card.style.display = text.includes(input) ? "block" : "none";
  });
}

function enableTableSearch() {
  const input = document.getElementById("searchInput");
  const datalist = document.getElementById("tableSuggestions");
  if (!input || !datalist) return;

  const suggestions = new Set();
  document.querySelectorAll("td").forEach(cell => {
    const words = cell.textContent.match(/\b\w+\b/g); // Only full words
    if (words) {
      words.forEach(word => {
        if (word.length > 2) suggestions.add(word.toLowerCase());
      });
    }
  });

  datalist.innerHTML = [...suggestions].sort().map(word =>
    `<option value="${word}">`
  ).join("");

  input.addEventListener("input", () => {
    const query = input.value.toLowerCase();
    document.querySelectorAll("td").forEach(cell => {
      const originalText = cell.textContent;
      const text = originalText.toLowerCase();
      if (query && text.includes(query)) {
        const regex = new RegExp(`(${query})`, "gi");
        cell.innerHTML = originalText.replace(regex, `<mark>$1</mark>`);
        cell.style.opacity = "";
      } else {
        cell.innerHTML = originalText;
        cell.style.opacity = query ? "0.2" : "";
      }
    });
  });
}

function initSearchBinding() {
  const searchInput = document.getElementById("searchInput");
  if (!searchInput || document.getElementById("searchResults")) return;

  if (document.querySelector("td")) {
    enableTableSearch();
  }
}

/*** ─── SUGGESTIONS BOX ────────────────────────────────────── **/
function setupSuggestionBox() {
  const form = document.getElementById("suggestionForm");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = document.getElementById("suggestionInput");
    const status = document.getElementById("suggestionStatus");
    const suggestion = input.value.trim();
    if (!suggestion) return;

    try {
      const res = await fetch("http://127.0.0.1:8000/api/suggest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ suggestion })
      });
      if (res.ok) {
        status.textContent = "✅ Sent!";
        input.value = "";
      } else {
        status.textContent = "❌ Error sending";
      }
    } catch {
      status.textContent = "❌ Connection failed";
    }
  });
}
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
      const answer = entry.target.querySelector('.answer');
      if (answer && !answer.classList.contains("revealed")) {
        answer.classList.add("revealed");
      }
    }
  });
}, {
  root: null,
  rootMargin: '0px',
  threshold: 0.5
});

document.querySelectorAll('.carousel-item').forEach(item => {
  observer.observe(item);
});

/*** ─── UTILS / INIT ───────────────────────────────────────── **/
document.addEventListener("DOMContentLoaded", () => {
  loadBuzzwords();
  loadRapidReviewCards();
  initSearchBinding();
  resizeCarouselFont();
  window.addEventListener("resize", resizeCarouselFont);

  // Suggestions box support
  setupSuggestionBox();

  const transitionStyle = document.createElement("style");
  transitionStyle.innerHTML = `
    .carousel-item .answer {
      display: inline-block;
      opacity: 0;
      transform: translateX(1px);
      transition: opacity 0.5s ease, transform 0.5s ease;
    }
    .carousel-item .answer.revealed {
      opacity: 1;
      transform: translateX(0);
    }
  `;
  document.head.appendChild(transitionStyle);

  const colWidthStyle = document.createElement("style");
  colWidthStyle.textContent = `
    thead th {
      width: max-content !important;
      white-space: nowrap;
    }
    table {
      table-layout: auto !important;
      border-collapse: separate !important;
    }
  `;
  document.head.appendChild(colWidthStyle);

  document.querySelectorAll("th").forEach(th => th.removeAttribute("style"));
});


(function () {
  const isReallyMobile = () => {
    const ua = navigator.userAgent;
    const isMobileUA = /iPhone|iPad|iPod|Android|webOS|BlackBerry|IEMobile|Opera Mini/i.test(ua);
    const isSmallScreen = window.innerWidth <= 768;
    const isTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 1;
    return isMobileUA && isSmallScreen && isTouch;
  };

  if (isReallyMobile()) {
    document.body.classList.add("mobile-compact");
  }
})();




