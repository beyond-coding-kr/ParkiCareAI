const DAYS = ['월','화','수','목','금','토','일'];
const SLOTS_PER_HOUR = 2;
const TOTAL_HOURS = 24;
const TOTAL_SLOTS = TOTAL_HOURS * SLOTS_PER_HOUR;
const COLORS = [
  '#6c63ff','#f472b6','#34d399','#fbbf24','#60a5fa',
  '#fb7185','#a78bfa','#2dd4bf','#f97316','#e879f9',
];
let state = {
  persons: [],
  activePersonId: null,
  use24h: true,
  useKorean: false,   
  editingPersonId: null,
  isDragging: false,
  dragMode: null,
  selectedColor: COLORS[0],
  compareMode: false,
  compareResult: null,
  theme: 'dark',
};
function save() { try { localStorage.setItem('ts_v5', JSON.stringify(state.persons)); } catch(e){} }
function load() {
  try { const r = localStorage.getItem('ts_v5'); if (r) state.persons = JSON.parse(r); } catch(e){}
  if (!state.persons.length) addPerson('나', COLORS[0], false);
  state.activePersonId = state.persons[0].id;
  setTheme(localStorage.getItem('ts_theme') || 'dark');
}
function makeSchedule() {
  const s = {};
  for (let d = 0; d < 7; d++) s[d] = new Array(TOTAL_SLOTS).fill(false);
  return s;
}
let _nid = Date.now();
function uid() { return ++_nid; }
function addPerson(name, color, doSave=true) {
  const p = { id: uid(), name, color, schedule: makeSchedule() };
  state.persons.push(p);
  if (doSave) { save(); renderAll(); }
  return p;
}
function getActive() { return state.persons.find(p => p.id === state.activePersonId) || null; }
function slotToTime(slot) {
  const h = Math.floor((slot * 30) / 60);
  const m = (slot * 30) % 60;
  if (state.use24h) return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}`;
  const h12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
  const ms = String(m).padStart(2,'0');
  if (state.useKorean) {
    return `${h < 12 ? '오전' : '오후'} ${h12}:${ms}`;
  }
  return `${h12}:${ms} ${h < 12 ? 'AM' : 'PM'}`;
}
const $ = id => document.getElementById(id);
const personList=$('personList'), addPersonBtn=$('addPersonBtn');
const toggleFormatBtn=$('toggleFormatBtn'), formatLabel=$('formatLabel');
const toggleAmpmBtn=$('toggleAmpmBtn'), ampmLabel=$('ampmLabel');
const activePersonTag=$('activePersonTag'), timeAxis=$('timeAxis');
const dayHeaders=$('dayHeaders'), gridBody=$('gridBody');
const compareA=$('compareA'), compareB=$('compareB'), compareBtn=$('compareBtn');
const resultPanel=$('resultPanel'), resultBody=$('resultBody');
const modalOverlay=$('modalOverlay'), modalTitle=$('modalTitle');
const personNameInput=$('personNameInput'), colorPicker=$('colorPicker');
const savePersonBtn=$('savePersonBtn'), cancelModalBtn=$('cancelModalBtn');
const closeModalBtn=$('closeModalBtn'), toast=$('toast');
const editHeader=$('editHeader'), compareHeader=$('compareHeader');
const backBtn=$('backBtn'), comparePersonsBadge=$('comparePersonsBadge');
const gridLegend=$('gridLegend'), themeSwitcher=$('themeSwitcher');
const btnSleep=$('btnSleep'), btnSchool=$('btnSchool');
function setTheme(t) {
  state.theme = t;
  document.documentElement.setAttribute('data-theme', t);
  localStorage.setItem('ts_theme', t);
  themeSwitcher.querySelectorAll('.theme-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.theme === t));
}
themeSwitcher.addEventListener('click', e => {
  const btn = e.target.closest('.theme-btn');
  if (btn) setTheme(btn.dataset.theme);
});
function renderAll() {
  renderPersonList();
  renderCompareSelects();
  if (state.compareMode && state.compareResult) showCompareGrid();
  else showEditGrid();
}
function renderPersonList() {
  personList.innerHTML = '';
  state.persons.forEach(p => {
    const li = document.createElement('li');
    li.className = 'person-item' + (p.id === state.activePersonId && !state.compareMode ? ' active' : '');
    li.style.setProperty('--person-color', p.color);
    li.innerHTML = `
      <div class="person-dot" style="background:${p.color}"></div>
      <span class="person-name">${esc(p.name)}</span>
      <div class="person-actions">
        <button class="person-action-btn edit" data-id="${p.id}">✏️</button>
        <button class="person-action-btn delete" data-id="${p.id}">🗑</button>
      </div>`;
    li.addEventListener('click', e => {
      if (e.target.closest('.person-action-btn')) return;
      exitCompare(); state.activePersonId = p.id; renderAll();
    });
    personList.appendChild(li);
  });
  personList.querySelectorAll('.edit').forEach(b =>
    b.addEventListener('click', e => { e.stopPropagation(); openModal('edit', b.dataset.id); }));
  personList.querySelectorAll('.delete').forEach(b =>
    b.addEventListener('click', e => { e.stopPropagation(); deletePerson(+b.dataset.id); }));
}
function renderCompareSelects() {
  const pA = compareA.value, pB = compareB.value;
  compareA.innerHTML = ''; compareB.innerHTML = '';
  state.persons.forEach(p => {
    const o = `<option value="${p.id}">${esc(p.name)}</option>`;
    compareA.innerHTML += o; compareB.innerHTML += o;
  });
  if ([...compareA.options].some(o => o.value == pA)) compareA.value = pA;
  if ([...compareB.options].some(o => o.value == pB)) compareB.value = pB;
  if (state.persons.length >= 2 && !pA) { compareA.value = state.persons[0].id; compareB.value = state.persons[1].id; }
}
function showEditGrid() {
  state.compareMode = false;
  editHeader.style.display = '';
  compareHeader.style.display = 'none';
  gridBody.classList.remove('compare-mode');
  updateActiveTag();
  renderTimeAxis();
  renderDayHeaders();
  renderEditBody();
  renderEditLegend();
  syncTimeAxisPadding();
}
function syncTimeAxisPadding() {
  requestAnimationFrame(() => {
    const hh = dayHeaders.offsetHeight;
    timeAxis.style.paddingTop = hh + 'px';
  });
}
function updateActiveTag() {
  const p = getActive();
  if (!p) return;
  activePersonTag.innerHTML = `<div style="width:8px;height:8px;border-radius:50%;background:${p.color};flex-shrink:0"></div> ${esc(p.name)}의 스케줄`;
  activePersonTag.style.borderColor = p.color + '55';
  activePersonTag.style.color = p.color;
}
function renderTimeAxis() {
  timeAxis.innerHTML = '';
  for (let s = 0; s < TOTAL_SLOTS; s++) {
    const lbl = document.createElement('div');
    const isHour = s % SLOTS_PER_HOUR === 0;
    lbl.className = 'time-label' + (isHour ? '' : ' half');
    lbl.textContent = isHour ? slotToTime(s) : '';
    lbl.style.height = isHour ? '24px' : '22px';
    timeAxis.appendChild(lbl);
  }
}
function renderDayHeaders() {
  dayHeaders.innerHTML = '';
  DAYS.forEach((d, i) => {
    const div = document.createElement('div');
    div.className = 'day-header' + (i >= 5 ? ' weekend' : '');
    div.textContent = d;
    dayHeaders.appendChild(div);
  });
}
function renderEditBody() {
  const p = getActive();
  gridBody.innerHTML = '';
  for (let day = 0; day < 7; day++) {
    const col = document.createElement('div'); col.className = 'day-col';
    for (let s = 0; s < TOTAL_SLOTS; s++) {
      const c = document.createElement('div');
      const busy = p && p.schedule[day][s];
      c.className = 'time-slot' + (busy ? ' busy' : ' empty') + (s % SLOTS_PER_HOUR === 0 ? ' hour-start' : '');
      if (p) c.style.setProperty('--person-color', p.color);
      c.dataset.day = day; c.dataset.slot = s;
      col.appendChild(c);
    }
    gridBody.appendChild(col);
  }
  attachDrag();
}
function renderEditLegend() {
  const p = getActive();
  const col = p ? p.color : 'var(--accent)';
  gridLegend.innerHTML = `
    <div class="legend-item"><div class="legend-dot busy" style="background:${col}"></div><span>바쁜 시간</span></div>
    <div class="legend-item"><div class="legend-dot free"></div><span>빈 시간</span></div>`;
}
function attachDrag() {
  gridBody.onmousedown = onMD; gridBody.onmouseover = onMO;
  gridBody.ontouchstart = onTS; gridBody.ontouchmove = onTM; gridBody.ontouchend = onTE;
}
function cell(e) { return e.target.closest('.time-slot'); }
function onMD(e) {
  if (state.compareMode) return;
  const c = cell(e); if (!c || !getActive()) return;
  e.preventDefault();
  const p = getActive(), d = +c.dataset.day, s = +c.dataset.slot;
  state.isDragging = true;
  state.dragMode = p.schedule[d][s] ? 'clear' : 'fill';
  applySlot(p, d, s);
}
function onMO(e) { if (!state.isDragging) return; const c = cell(e); if (c) applySlot(getActive(), +c.dataset.day, +c.dataset.slot); }
document.addEventListener('mouseup', () => { if (state.isDragging) { state.isDragging = false; save(); } });
function tCell(e) { const t = e.touches[0]; const el = document.elementFromPoint(t.clientX, t.clientY); return el ? el.closest('.time-slot') : null; }
function onTS(e) { if (state.compareMode) return; const c = tCell(e); if (!c || !getActive()) return; e.preventDefault(); const p = getActive(); state.isDragging = true; state.dragMode = p.schedule[+c.dataset.day][+c.dataset.slot] ? 'clear' : 'fill'; applySlot(p, +c.dataset.day, +c.dataset.slot); }
function onTM(e) { if (!state.isDragging) return; e.preventDefault(); const c = tCell(e); if (c) applySlot(getActive(), +c.dataset.day, +c.dataset.slot); }
function onTE() { state.isDragging = false; save(); }
function applySlot(p, d, s) {
  if (!p) return;
  const v = state.dragMode === 'fill';
  if (p.schedule[d][s] === v) return;
  p.schedule[d][s] = v;
  const el = gridBody.querySelector(`[data-day="${d}"][data-slot="${s}"]`);
  if (el) {
    el.className = 'time-slot' + (v ? ' busy' : ' empty') + (s % SLOTS_PER_HOUR === 0 ? ' hour-start' : '');
    el.style.setProperty('--person-color', p.color);
  }
}
document.addEventListener('selectstart', e => { if (state.isDragging) e.preventDefault(); });
function fillSlotRange(startSlot, endSlot) {
  const p = getActive();
  if (!p) { showToast('⚠️ 사람을 먼저 선택하세요'); return; }
  for (let d = 0; d < 7; d++) {
    for (let s = startSlot; s < endSlot; s++) {
      p.schedule[d][s] = true;
    }
  }
  save(); renderAll();
}
btnSleep.addEventListener('click', () => {
  fillSlotRange(0, 14);
  showToast('😴 수면 시간 (0:00~7:00) 체크 완료');
});
btnSchool.addEventListener('click', () => {
  const p = getActive();
  if (!p) { showToast('⚠️ 사람을 먼저 선택하세요'); return; }
  for (let d = 0; d < 5; d++) { 
    for (let s = 18; s < 29; s++) p.schedule[d][s] = true;
  }
  save(); renderAll();
  showToast('🏫 학교 시간 (9:00~14:30, 월~금) 체크 완료');
});
function runCompare() {
  const idA = +compareA.value, idB = +compareB.value;
  if (idA === idB) { showToast('⚠️ 서로 다른 사람을 선택해주세요'); return; }
  const pA = state.persons.find(p => p.id === idA);
  const pB = state.persons.find(p => p.id === idB);
  if (!pA || !pB) return;
  const freeSlots = {};
  for (let d = 0; d < 7; d++) {
    const ranges = []; let start = null;
    for (let s = 0; s < TOTAL_SLOTS; s++) {
      const free = !pA.schedule[d][s] && !pB.schedule[d][s];
      if (free && start === null) start = s;
      else if (!free && start !== null) { ranges.push([start, s - 1]); start = null; }
    }
    if (start !== null) ranges.push([start, TOTAL_SLOTS - 1]);
    freeSlots[d] = ranges;
  }
  state.compareResult = { pA, pB, freeSlots };
  state.compareMode = true;
  renderAll();
}
function showCompareGrid() {
  const { pA, pB, freeSlots } = state.compareResult;
  editHeader.style.display = 'none';
  compareHeader.style.display = '';
  comparePersonsBadge.innerHTML = `
    <span class="cpb-dot" style="background:${pA.color}"></span>${esc(pA.name)}
    <span style="color:var(--text3);margin:0 .2rem">×</span>
    <span class="cpb-dot" style="background:${pB.color}"></span>${esc(pB.name)}`;
  renderTimeAxis(); renderDayHeaders();
  const freeMap = {};
  for (let d = 0; d < 7; d++) {
    freeMap[d] = new Array(TOTAL_SLOTS).fill(false);
    freeSlots[d].forEach(([s, e]) => { for (let i = s; i <= e; i++) freeMap[d][i] = true; });
  }
  gridBody.innerHTML = '';
  gridBody.classList.add('compare-mode');
  for (let day = 0; day < 7; day++) {
    const col = document.createElement('div'); col.className = 'day-col';
    for (let s = 0; s < TOTAL_SLOTS; s++) {
      const c = document.createElement('div');
      c.className = 'time-slot' + (freeMap[day][s] ? ' compare-free' : ' compare-busy') + (s % SLOTS_PER_HOUR === 0 ? ' hour-start' : '');
      col.appendChild(c);
    }
    gridBody.appendChild(col);
  }
  gridLegend.innerHTML = `
    <div class="legend-item"><div class="legend-dot common"></div><span>둘 다 비는 시간</span></div>
    <div class="legend-item"><div class="legend-dot free"></div><span>한쪽 이상 바쁨</span></div>`;
  renderResultText(pA, pB, freeSlots);
  resultPanel.classList.add('open');
  syncTimeAxisPadding();
}
function renderResultText(pA, pB, freeSlots) {
  let hasAny = false;
  for (let d = 0; d < 7; d++) if (freeSlots[d].length) { hasAny = true; break; }
  let html = `<div class="result-compare-info">
    <div class="result-compare-dot" style="background:${pA.color}"></div><span>${esc(pA.name)}</span>
    <span style="color:var(--text3)">+</span>
    <div class="result-compare-dot" style="background:${pB.color}"></div><span>${esc(pB.name)}</span></div>`;
  if (!hasAny) {
    html += `<div class="result-no-match">😔 공통으로 비는 시간이 없어요.<br/>스케줄을 조정해보세요!</div>`;
  } else {
    for (let d = 0; d < 7; d++) {
      if (!freeSlots[d].length) continue;
      html += `<div class="result-day-group"><div class="result-day-label">${DAYS[d]}요일</div>`;
      freeSlots[d].forEach(([s, e]) => { html += `<div class="result-slot">${slotToTime(s)} ~ ${slotToTime(e + 1)}</div>`; });
      html += `</div>`;
    }
  }
  resultBody.innerHTML = html;
}
function exitCompare() {
  state.compareMode = false; state.compareResult = null;
  gridBody.classList.remove('compare-mode');
  resultBody.innerHTML = `<div class="result-placeholder"><div class="result-placeholder-icon">🕐</div><p>왼쪽에서 두 사람을 선택하고<br/>공통 시간 찾기를 눌러보세요</p></div>`;
  resultPanel.classList.remove('open');
}
function openModal(mode, pid=null) {
  state.editingPersonId = pid ? +pid : null;
  if (mode === 'edit' && state.editingPersonId) {
    const p = state.persons.find(x => x.id === state.editingPersonId);
    modalTitle.textContent = '참여자 편집'; personNameInput.value = p.name; state.selectedColor = p.color;
  } else { modalTitle.textContent = '새 참여자 추가'; personNameInput.value = ''; state.selectedColor = COLORS[state.persons.length % COLORS.length]; }
  renderColorPicker(); modalOverlay.classList.add('open');
  setTimeout(() => personNameInput.focus(), 200);
}
function closeModal() { modalOverlay.classList.remove('open'); state.editingPersonId = null; }
function renderColorPicker() {
  colorPicker.innerHTML = '';
  COLORS.forEach(c => {
    const sw = document.createElement('div');
    sw.className = 'color-swatch' + (c === state.selectedColor ? ' selected' : '');
    sw.style.background = c; sw.style.boxShadow = `0 2px 12px ${c}66`;
    sw.addEventListener('click', () => { state.selectedColor = c; colorPicker.querySelectorAll('.color-swatch').forEach(s => s.classList.remove('selected')); sw.classList.add('selected'); });
    colorPicker.appendChild(sw);
  });
}
function savePerson() {
  const name = personNameInput.value.trim();
  if (!name) { showToast('⚠️ 이름을 입력해주세요'); return; }
  if (state.editingPersonId) {
    const p = state.persons.find(x => x.id === state.editingPersonId);
    if (p) { p.name = name; p.color = state.selectedColor; }
    showToast('✅ 수정되었습니다');
  } else { addPerson(name, state.selectedColor); showToast(`✅ "${name}" 추가`); }
  save(); closeModal(); renderAll();
}
function deletePerson(id) {
  if (state.persons.length <= 1) { showToast('⚠️ 최소 1명은 필요합니다'); return; }
  state.persons = state.persons.filter(p => p.id !== id);
  if (state.activePersonId === id) state.activePersonId = state.persons[0].id;
  save(); renderAll(); showToast('🗑 삭제');
}
let tt;
function showToast(msg) { toast.textContent = msg; toast.classList.add('show'); clearTimeout(tt); tt = setTimeout(() => toast.classList.remove('show'), 2500); }
toggleFormatBtn.addEventListener('click', () => {
  state.use24h = !state.use24h;
  formatLabel.textContent = state.use24h ? '24h' : '12h';
  toggleAmpmBtn.style.display = state.use24h ? 'none' : '';
  renderTimeAxis();
  if (state.compareMode && state.compareResult) renderResultText(state.compareResult.pA, state.compareResult.pB, state.compareResult.freeSlots);
});
toggleAmpmBtn.addEventListener('click', () => {
  state.useKorean = !state.useKorean;
  ampmLabel.textContent = state.useKorean ? '오전/오후' : 'AM/PM';
  renderTimeAxis();
  if (state.compareMode && state.compareResult) renderResultText(state.compareResult.pA, state.compareResult.pB, state.compareResult.freeSlots);
});
toggleAmpmBtn.style.display = state.use24h ? 'none' : '';
function esc(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
addPersonBtn.addEventListener('click', () => openModal('add'));
compareBtn.addEventListener('click', runCompare);
backBtn.addEventListener('click', () => { exitCompare(); renderAll(); });
savePersonBtn.addEventListener('click', savePerson);
cancelModalBtn.addEventListener('click', closeModal);
closeModalBtn.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', e => { if (e.target === modalOverlay) closeModal(); });
personNameInput.addEventListener('keydown', e => { if (e.key === 'Enter') savePerson(); });
load();
renderAll();