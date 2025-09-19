const originalTableState = new Map();

function attachCellClickListeners() {
  document.querySelectorAll("td").forEach(cell => {
    cell.addEventListener("click", () => {
      cell.style.opacity = "";
    });
  });
}

/**
 * Toggle visibility of a given column index across all tables
 */
function toggleColumn(colIndex) {
  const cells = Array.from(document.querySelectorAll('td[data-col="' + colIndex + '"]'))
    .filter(cell => !cell.closest("tr.row-divider"));
  const currentlyHidden = cells.every(cell => cell.dataset.hidden === "true");
  cells.forEach(cell => {
    if (currentlyHidden) {
      cell.style.opacity = "";
      delete cell.dataset.hidden;
    } else {
      cell.style.opacity = "0";
      cell.dataset.hidden = "true";
    }
  });
}

/**
 * Reset visibility styles and restore original row order for all tables.
 */
function resetColumns() {
  document.querySelectorAll('td, th').forEach(cell => {
    cell.style.opacity = '';
  });

  document.querySelectorAll("table").forEach((table, tableIndex) => {
    const tbodies = table.querySelectorAll("tbody");
    const cachedRows = originalTableState.get(tableIndex);

    if (!cachedRows) return;

    tbodies.forEach((tbody, i) => {
      if (!cachedRows[i]) return;
      tbody.innerHTML = "";
      cachedRows[i].forEach(row => tbody.appendChild(row.cloneNode(true)));
    });
  });
  attachCellClickListeners();
}

function filterRowsByInput(inputId, rowSelector) {
  const input = document.getElementById(inputId);
  if (!input) return;
  const query = input.value.toLowerCase();
  document.querySelectorAll(rowSelector).forEach(row => {
    if (row.closest("tfoot") || row.classList.contains("section-divider")) return;
    const text = row.textContent.toLowerCase();
    row.style.opacity = text.includes(query) ? "" : "0";
  });
}

/**
 * Shuffle all rows inside all tbody sections of a table,
 * preserving section-divider rows at the start of each tbody.
 */
function shuffleTableRows(table) {
  const tbodies = table.querySelectorAll("tbody");
  tbodies.forEach(tbody => {
    // ❌ Remove rows that are 'row-divider' or contain 'row-divider' <td>
    tbody.querySelectorAll("tr").forEach(row => {
      if (
        row.classList.contains("row-divider") ||
        row.querySelector("td.row-divider")
      ) {
        row.remove();
      }
    });

    const rows = Array.from(tbody.querySelectorAll("tr"))
      .filter(row =>
        !row.classList.contains("section-divider") &&
        !row.classList.contains("row-divider") &&
        !row.closest("tfoot") &&
        !row.closest("tfoot tr") &&
        !(row.id && row.id.startsWith("section-"))
      );
    const sectionRows = Array.from(tbody.querySelectorAll("tr.section-divider"));

    // Preserve visibility state (row.style.display) before shuffling
    const rowVisibilityMap = new Map();
    rows.forEach(row => {
      rowVisibilityMap.set(row, row.style.display);
    });

    // Fisher-Yates shuffle
    for (let i = rows.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [rows[i], rows[j]] = [rows[j], rows[i]];
    }

    // Hide section headers before appending
    sectionRows.forEach(row => {
      row.style.display = "none";
    });

    // Clear tbody and re-append only shuffled rows
    tbody.innerHTML = "";

    // Remove row-specific borders or table-specific styles
    rows.forEach(row => {
      row.removeAttribute("style");
      row.querySelectorAll("td").forEach(td => td.removeAttribute("style"));
    });

    tbody.innerHTML = "";
    rows.forEach(row => {
      // row.classList.remove("row-divider"); // removed as row-divider rows are already removed above
      row.querySelectorAll("td").forEach(td => td.style.borderBottom = "none");
      tbody.appendChild(row);
      // Restore visibility state after shuffle
      if (rowVisibilityMap.has(row)) {
        row.style.display = rowVisibilityMap.get(row);
      }
    });

    // Reapply hidden column visibility after shuffle
    document.querySelectorAll("td[data-col]").forEach(td => {
      if (td.dataset.hidden === "true") {
        td.style.opacity = "0";
      }
    });
  });
  attachCellClickListeners();
}

// Add shuffle button listener for all tables on the page
document.addEventListener("DOMContentLoaded", () => {
  // 1. Inject sticky header CSS dynamically
  const style = document.createElement('style');
  style.textContent = `
    thead tr.sticky-header {
      position: sticky;
      top: 0;
      background: #fff;
      z-index: 2;
    }
  `;
  document.head.appendChild(style);

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

  const shuffleBtn = document.getElementById("shuffle-button");
  if (shuffleBtn) {
    shuffleBtn.addEventListener("click", () => {
      document.querySelectorAll("table").forEach(table => shuffleTableRows(table));
    });
  }

  // Cache original table row order at load time to support reset
  document.querySelectorAll("table").forEach((table, tableIndex) => {
    const tbodies = table.querySelectorAll("tbody");
    const cachedTbodyRows = [];

    tbodies.forEach(tbody => {
      const rows = Array.from(tbody.querySelectorAll("tr"));
      cachedTbodyRows.push(rows.map(row => row.cloneNode(true)));
    });

    originalTableState.set(tableIndex, cachedTbodyRows);
  });

  const resetBtn = document.getElementById("reset-button");
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      resetColumns();
    });
  }

  const hideAllBtn = document.getElementById("hide-all-button");
  if (hideAllBtn) {
    hideAllBtn.addEventListener("click", () => {
      document.querySelectorAll("tbody tr").forEach(row => {
        if (
          row.closest("tfoot") ||
          row.classList.contains("section-divider") ||
          (row.id && row.id.startsWith("section-"))
        ) return;
        row.querySelectorAll("td").forEach(td => {
          td.style.opacity = "0";
          td.dataset.hidden = "true";
        });
      });
    });
  }

  // Wire up "Toggle Column" dropdown menu logic
  const toggleColBtn = document.getElementById("toggle-col-button");
  const toggleColMenu = document.getElementById("toggle-col-menu");

  if (toggleColBtn && toggleColMenu) {
    // Toggle dropdown visibility with dynamic rebuild
    toggleColBtn.addEventListener("click", () => {
      // Rebuild menu each time to ensure fresh DOM access
      toggleColMenu.innerHTML = "";
      const headerRow = document.querySelector("thead tr:nth-of-type(2)");
      const headerCells = headerRow ? headerRow.querySelectorAll("th:not([colspan])") : [];

      headerCells.forEach((th, index) => {
        const colOption = document.createElement("div");
        colOption.textContent = th.textContent || `Column ${index + 1}`;
        colOption.style.padding = "4px 12px";
        colOption.style.cursor = "pointer";
        colOption.addEventListener("click", () => {
          toggleColumn(index);
          toggleColMenu.style.display = "none";
        });
        toggleColMenu.appendChild(colOption);
      });

      // Show or hide the dropdown
      toggleColMenu.style.display = toggleColMenu.childNodes.length > 0 ? "block" : "none";
    });

    // Hide dropdown when clicking outside
    document.addEventListener("click", (e) => {
      if (!toggleColBtn.contains(e.target) && !toggleColMenu.contains(e.target)) {
        toggleColMenu.style.display = "none";
      }
    });
  }

  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("input", () => {
      filterRowsByInput("searchInput", "tbody tr td");
    });
  }

  attachCellClickListeners();

  // 2. Make the header row containing .th-menu-wrapper sticky
  const menuWrapperRow = document.querySelector("thead tr");
  if (menuWrapperRow && menuWrapperRow.querySelector(".th-menu-wrapper")) {
    menuWrapperRow.classList.add("sticky-header");
  }

  // Enable click-to-toggle submenu for nav categories, and normal link for those without submenu
  document.querySelectorAll('.nav_category').forEach(cat => {
    const submenu = cat.querySelector('.nav_submenu');
    const anchor = cat.querySelector('a');

    cat.addEventListener('click', (e) => {
      e.stopPropagation(); // prevent bubbling
      if (!submenu) {
        if (anchor && anchor.href) {
          window.location.href = anchor.href;
        }
        return;
      }

      const isVisible = submenu.style.display === 'block';
      document.querySelectorAll('.nav_submenu').forEach(sm => sm.style.display = 'none'); // close others
      submenu.style.display = isVisible ? 'none' : 'block'; // toggle this one
    });
  });

  // Close all submenus if clicking outside
  document.addEventListener('click', () => {
    document.querySelectorAll('.nav_submenu').forEach(sm => sm.style.display = 'none');
  });

  // Inject fallback sticky style for 2nd thead row
  const stickyStyle = document.createElement("style");
  stickyStyle.textContent = `
    thead tr.sticky-fallback {
      position: sticky;
      top: 0;
      background: #f7f9fa;
      z-index: 10;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
  `;
  document.head.appendChild(stickyStyle);

  // Inject sticky style for colspan-heading rows
  const stickyHeaderStyle = document.createElement("style");
  stickyHeaderStyle.textContent = `
    thead tr.colspan-heading th {
      position: sticky;
      top: 0;
      z-index: 4;
      background-color: #d0e5f5;
    }
  `;
  document.head.appendChild(stickyHeaderStyle);

  // Ensure table parent wrappers allow sticky headers in scrollable tables
  document.querySelectorAll("table").forEach(table => {
    const wrapper = table.parentElement;
    if (wrapper && !wrapper.classList.contains("table-scroll-wrapper")) {
      wrapper.style.overflowX = "auto";
      wrapper.style.position = "relative";
    }
  });

  // Watch second thead row and apply sticky class on scroll
  document.querySelectorAll("table").forEach(table => {
    const thead = table.querySelector("thead");
    if (!thead) return;
    const rows = thead.querySelectorAll("tr");
    if (rows.length < 2) return;

    const labelRow = rows[1];
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (!entry.isIntersecting) {
          labelRow.classList.add("sticky-fallback");
        } else {
          labelRow.classList.remove("sticky-fallback");
        }
      });
    }, { threshold: 1.0 });

    observer.observe(labelRow);
  });

  document.querySelectorAll("th").forEach(th => th.removeAttribute("style"));

  // Add .colspan-heading class to rows with <th colspan>
  document.querySelectorAll("table").forEach(table => {
    const thead = table.querySelector("thead");
    if (!thead) return;
    const rows = thead.querySelectorAll("tr");
    rows.forEach(row => {
      const th = row.querySelector("th[colspan]");
      if (th) {
        row.classList.add("colspan-heading");
      }
    });
  });
});

document.querySelectorAll(".th-dropdown a").forEach(link => {
  link.addEventListener("click", (event) => {
    const colIndex = link.getAttribute("data-col");
    if (colIndex !== null) toggleColumn(colIndex);
    event.preventDefault();
  });
});

document.querySelectorAll(".th-menu-wrapper").forEach(wrapper => {
  const dropdown = wrapper.querySelector(".th-dropdown");
  if (!dropdown) return;

  let hideTimeout;

  const showDropdown = () => {
    clearTimeout(hideTimeout);
    dropdown.style.display = "block";
  };

  const hideDropdown = () => {
    hideTimeout = setTimeout(() => {
      dropdown.style.display = "none";
    }, 400); //
  };

  wrapper.addEventListener("mouseenter", showDropdown);
  wrapper.addEventListener("mouseleave", hideDropdown);
  dropdown.addEventListener("mouseenter", showDropdown);
  dropdown.addEventListener("mouseleave", hideDropdown);
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


const button = document.getElementById("float-nav-button-container");

if (button) {
  const dropdown = document.querySelector(".nav_dropdown_container");
  if (dropdown) {
    dropdown.style.top = "0";
    dropdown.style.right = "100%";
    dropdown.style.left = "auto";
  }
}


// Toggle main dropdown
document.getElementById("float-nav-button-container")
  .addEventListener("click", function () {
    const dd = document.getElementById("nav-dropdown");
    dd.style.display = dd.style.display === "block" ? "none" : "block";
  });

// Close dropdown on outside click
document.addEventListener("click", function (e) {
  const dd = document.getElementById("nav-dropdown");
  const btn = document.getElementById("float-nav-button-container");
  if (!dd.contains(e.target) && !btn.contains(e.target)) {
    dd.style.display = "none";
  }
});

// Wire up submenu hover handlers once DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('.nav_category.has-children').forEach(cat => {
    const sub = cat.querySelector('.nav_submenu');
    if (!sub) return;
    cat.addEventListener('mouseover',  () => sub.style.display = 'block');
    cat.addEventListener('mouseleave', () => sub.style.display = 'none');
  });
});
  const dropdownElem = document.getElementById("nav-dropdown");
  dropdownElem.addEventListener('mouseleave', () => {
    dropdownElem.style.display = 'none';
  });