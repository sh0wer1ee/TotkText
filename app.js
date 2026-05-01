const state = {
  manifest: null,
  folder: null,
  file: null,
  chunk: 0,
  currentData: null,
  targetRow: null,
  searchWorker: null,
};

const els = {
  versionLabel: document.querySelector("#versionLabel"),
  folderSelect: document.querySelector("#folderSelect"),
  fileSelect: document.querySelector("#fileSelect"),
  fileMeta: document.querySelector("#fileMeta"),
  searchForm: document.querySelector("#searchForm"),
  searchInput: document.querySelector("#searchInput"),
  clearSearch: document.querySelector("#clearSearch"),
  mobileFab: document.querySelector("#mobileFab"),
  mobileScrim: document.querySelector("#mobileScrim"),
  sidebar: document.querySelector(".sidebar"),
  browseToggle: document.querySelector("#browseToggle"),
  browsePanel: document.querySelector("#browsePanel"),
  searchPanel: document.querySelector("#searchPanel"),
  statusText: document.querySelector("#statusText"),
  resultsPanel: document.querySelector("#resultsPanel"),
  resultsMeta: document.querySelector("#resultsMeta"),
  resultsList: document.querySelector("#resultsList"),
  browserTitle: document.querySelector("#browserTitle"),
  prevChunk: document.querySelector("#prevChunk"),
  nextChunk: document.querySelector("#nextChunk"),
  pageInfo: document.querySelector("#pageInfo"),
  rows: document.querySelector("#rows"),
};

function chunkName(index) {
  return String(index).padStart(4, "0");
}

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) {
    throw new Error(`${res.status} ${path}`);
  }
  return res.json();
}

function fileInfo(folder, file) {
  return state.manifest.folders[folder][file];
}

async function init() {
  state.manifest = await fetchJson("./data/manifest.json");
  els.versionLabel.textContent = `ver. ${state.manifest.version}`;

  for (const folder of Object.keys(state.manifest.folders)) {
    els.folderSelect.append(new Option(folder, folder));
  }

  const def = state.manifest.default;
  state.folder = def.folder;
  state.file = def.file;
  state.chunk = def.chunk;
  els.folderSelect.value = state.folder;
  populateFiles();
  els.fileSelect.value = state.file;
  await loadChunk(state.folder, state.file, state.chunk);
}

function populateFiles() {
  els.fileSelect.replaceChildren();
  for (const file of Object.keys(state.manifest.folders[state.folder])) {
    els.fileSelect.append(new Option(file, file));
  }
}

async function loadChunk(folder, file, chunk, targetRow = null) {
  const info = fileInfo(folder, file);
  const safeChunk = Math.max(0, Math.min(chunk, info.chunks - 1));
  const path = `./data/chunks/${folder}/${file}/${chunkName(safeChunk)}.json`;
  state.folder = folder;
  state.file = file;
  state.chunk = safeChunk;
  state.targetRow = targetRow;
  state.currentData = await fetchJson(path);

  els.folderSelect.value = folder;
  populateFiles();
  els.fileSelect.value = file;
  renderBrowser();
}

function renderBrowser() {
  const data = state.currentData;
  const meta = data.meta;
  const end = meta.start + meta.count;
  const total = meta.total;

  els.browserTitle.textContent = `${meta.folder} / ${meta.file}`;
  els.fileMeta.textContent = `${total.toLocaleString()} rows, ${fileInfo(meta.folder, meta.file).chunks} chunks`;
  els.pageInfo.textContent = `${meta.start + 1}-${end} / ${total}`;
  els.prevChunk.disabled = state.chunk <= 0;
  els.nextChunk.disabled = state.chunk >= fileInfo(meta.folder, meta.file).chunks - 1;

  els.rows.replaceChildren();
  for (const row of data.rows) {
    els.rows.append(renderRow(row, row.index === state.targetRow));
  }

  const target = document.querySelector(".row.target");
  if (target) {
    target.scrollIntoView({ block: "center" });
  }
}

function renderRow(row, isTarget) {
  const wrap = document.createElement("article");
  wrap.className = `row${isTarget ? " target" : ""}`;

  const head = document.createElement("div");
  head.className = "rowHead";
  const index = document.createElement("span");
  index.className = "index";
  index.textContent = `#${row.index}`;
  const key = document.createElement("span");
  key.className = "key";
  key.textContent = row.key;
  head.append(index, key);

  const cells = document.createElement("div");
  cells.className = "cells";
  for (const lang of ["CNzh", "TWzh", "JPja", "USen"]) {
    const cell = document.createElement("div");
    cell.className = "cell";
    const label = document.createElement("span");
    label.className = "lang";
    label.textContent = lang;
    cell.append(label);
    cell.append(renderGameText(row[lang] || "", lang === "JPja"));
    cells.append(cell);
  }

  wrap.append(head, cells);
  return wrap;
}

function renderGameText(raw, enableRuby) {
  const frag = document.createDocumentFragment();
  const rubyRe = /<Ruby=\{([0-9]+):([0-9]+)\}([^>]*)>/y;
  const stack = [{ node: frag, tag: "root" }];
  let i = 0;

  const parent = () => stack[stack.length - 1].node;

  while (i < raw.length) {
    rubyRe.lastIndex = i;
    const rubyMatch = enableRuby ? rubyRe.exec(raw) : null;
    if (rubyMatch) {
      const baseLen = Number(rubyMatch[1]) / 2;
      const rubyText = rubyMatch[3];
      const baseStart = rubyRe.lastIndex;
      const base = raw.slice(baseStart, baseStart + baseLen);
      const ruby = document.createElement("ruby");
      ruby.append(document.createTextNode(base));
      const rt = document.createElement("rt");
      rt.textContent = rubyText;
      ruby.append(rt);
      parent().append(ruby);
      i = baseStart + baseLen;
      continue;
    }

    if (raw.startsWith("<PageBreak>", i)) {
      parent().append(document.createElement("br"));
      i += "<PageBreak>".length;
      continue;
    }

    if (raw[i] === "<") {
      const end = raw.indexOf(">", i + 1);
      if (end !== -1) {
        handleGameTag(raw.slice(i, end + 1), stack);
        i = end + 1;
        continue;
      }
    }

    parent().append(document.createTextNode(raw[i]));
    i += 1;
  }

  return frag;
}

function handleGameTag(tag, stack) {
  if (/^<\/?unk\[[0-9: ]*\]>$/.test(tag)) return;

  const colorMatch = tag.match(/^<Color=([^>]+)>$/);
  if (colorMatch) {
    const color = colorMatch[1];
    if (color === "white") {
      closeStyleTag(stack, "color");
      return;
    }
    const span = document.createElement("span");
    span.className = `gameColor gameColor-${safeClassName(color)}`;
    span.style.color = gameColorValue(color);
    stack[stack.length - 1].node.append(span);
    stack.push({ node: span, tag: "color" });
    return;
  }

  if (tag === "</Color>") {
    closeStyleTag(stack, "color");
    return;
  }

  const sizeMatch = tag.match(/^<Size=([0-9]+)>$/);
  if (sizeMatch) {
    const size = sizeMatch[1];
    if (size === "100") {
      closeStyleTag(stack, "size");
      return;
    }
    const span = document.createElement("span");
    span.className = `gameSize gameSize-${size}`;
    stack[stack.length - 1].node.append(span);
    stack.push({ node: span, tag: "size" });
    return;
  }

  if (tag === "</Size>") {
    closeStyleTag(stack, "size");
  }
}

function closeStyleTag(stack, tagName) {
  for (let i = stack.length - 1; i > 0; i -= 1) {
    const entry = stack.pop();
    if (entry.tag === tagName) return;
  }
}

function safeClassName(value) {
  return value.toLowerCase().replace(/[^a-z0-9_-]/g, "");
}

function gameColorValue(color) {
  const colors = {
    aqua: "#00a6c8",
    blue: "#2f6fd0",
    green: "#2f8f4e",
    grey: "#808080",
    gray: "#808080",
    lightgreen: "#48a868",
    orange: "#d46d1f",
    red: "#d13b32",
    yellow: "#b88700",
  };
  return colors[color.toLowerCase()] || color;
}

function startSearch(query) {
  const trimmed = query.trim();
  if (!trimmed) return;

  if (state.searchWorker) {
    state.searchWorker.terminate();
  }

  els.resultsPanel.classList.remove("hidden");
  els.resultsList.replaceChildren();
  els.resultsMeta.textContent = "Scanning";
  els.statusText.textContent = `Searching "${trimmed}"`;
  if (window.matchMedia("(max-width: 900px)").matches) {
    openMobilePanel();
  }

  state.searchWorker = new Worker("./search-worker.js");
  state.searchWorker.onmessage = (event) => {
    const msg = event.data;
    if (msg.type === "progress") {
      els.resultsMeta.textContent = `${msg.done}/${msg.total} shards, ${msg.count} hits`;
      appendResults(msg.results);
    }
    if (msg.type === "done") {
      els.resultsMeta.textContent = `${msg.count} hits`;
      els.statusText.textContent = msg.count ? "Search complete" : "No matches";
      state.searchWorker.terminate();
      state.searchWorker = null;
    }
    if (msg.type === "error") {
      els.statusText.textContent = msg.message;
    }
  };
  state.searchWorker.postMessage({
    query: trimmed,
    shards: state.manifest.search.shards,
    limit: 300,
  });
}

function appendResults(results) {
  for (const item of results) {
    const button = document.createElement("button");
    button.className = "result";
    const loc = document.createElement("span");
    loc.className = "resultLoc";
    loc.textContent = `${item.loc[0]} / ${item.loc[1]} / ${item.key}`;
    const text = document.createElement("span");
    text.className = "resultText";
    text.textContent = item.text;
    button.append(loc, text);
    button.addEventListener("click", async () => {
      const [folder, file, chunk, rowIndex] = item.loc;
      await loadChunk(folder, file, chunk, chunk * state.manifest.chunkSize + rowIndex);
      closeMobileDrawer();
    });
    els.resultsList.append(button);
  }
}

function closeMobileDrawer() {
  if (!window.matchMedia("(max-width: 900px)").matches) return;
  closeMobilePanel();
}

function openMobilePanel() {
  els.searchPanel.classList.add("open");
  els.mobileScrim.hidden = false;
  els.mobileFab.setAttribute("aria-expanded", "true");
  document.body.classList.add("panelOpen");
}

function closeMobilePanel() {
  els.searchPanel.classList.remove("open");
  els.mobileScrim.hidden = true;
  els.mobileFab.setAttribute("aria-expanded", "false");
  document.body.classList.remove("panelOpen");
}

els.folderSelect.addEventListener("change", async () => {
  state.folder = els.folderSelect.value;
  populateFiles();
  state.file = els.fileSelect.value;
  await loadChunk(state.folder, state.file, 0);
  closeMobileBrowse();
});

els.fileSelect.addEventListener("change", async () => {
  state.file = els.fileSelect.value;
  await loadChunk(state.folder, state.file, 0);
  closeMobileBrowse();
});

els.prevChunk.addEventListener("click", () => loadChunk(state.folder, state.file, state.chunk - 1));
els.nextChunk.addEventListener("click", () => loadChunk(state.folder, state.file, state.chunk + 1));

els.searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  startSearch(els.searchInput.value);
});

els.clearSearch.addEventListener("click", () => {
  els.searchInput.value = "";
  els.resultsPanel.classList.add("hidden");
  els.resultsList.replaceChildren();
  els.resultsMeta.textContent = "";
  els.statusText.textContent = "";
  if (state.searchWorker) {
    state.searchWorker.terminate();
    state.searchWorker = null;
  }
});

els.mobileFab.addEventListener("click", openMobilePanel);
els.mobileScrim.addEventListener("click", closeMobilePanel);
els.browseToggle.addEventListener("click", () => {
  const willOpen = !els.browsePanel.classList.contains("open");
  els.browsePanel.classList.toggle("open", willOpen);
  const isOpen = els.browsePanel.classList.contains("open");
  els.browseToggle.setAttribute("aria-expanded", String(isOpen));
});
els.sidebar.addEventListener("click", () => {
  if (!window.matchMedia("(max-width: 900px)").matches) return;
  closeMobilePanel();
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeMobilePanel();
  }
});

function closeMobileBrowse() {
  if (!window.matchMedia("(max-width: 900px)").matches) return;
  els.browsePanel.classList.remove("open");
  els.browseToggle.setAttribute("aria-expanded", "false");
}

init().catch((error) => {
  els.statusText.textContent = error.message;
});
