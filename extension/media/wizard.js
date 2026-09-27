// SAIL setup wizard page. Same rule as sidebar.js: this file holds no logic and no data of its own. It
// draws exactly the view model the extension sends, and turns every user action straight into a
// postMessage -- never computing next/back/enabled-state itself. Text is set with textContent, never
// innerHTML, except the two constant, argument-free SVG icons below.
(function () {
  'use strict';
  const vscode = acquireVsCodeApi();
  const root = document.getElementById('root');

  const STEP_ORDER = ['data', 'map', 'checks'];
  const STEP_LABELS = { data: 'Dataset', map: 'Columns', checks: 'Checks' };

  function send(name, payload) {
    vscode.postMessage({ type: 'action', name: name, payload: payload });
  }

  function el(tag, className, text) {
    const e = document.createElement(tag);
    if (className) e.className = className;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function button(label, className, onClick, disabled) {
    const b = el('button', className, label);
    b.type = 'button';
    if (disabled) b.disabled = true;
    b.addEventListener('click', onClick);
    return b;
  }

  function errorBanner(message) {
    if (!message) return null;
    return el('div', 'error', message);
  }

  function renderWelcome(vm) {
    const wrap = el('div', 'welcome');
    wrap.append(
      el('div', 'eyebrow', 'STATE-ACTION INFORMATION LEAKAGE'),
      el('h1', null, 'Is your model learning medicine, or just reading the answer?')
    );
    wrap.append(el('p', 'lede', 'SAIL checks your treatment dataset for five kinds of hidden leakage between patient state and treatment. Three short steps, no code.'));
    const banner = errorBanner(vm.error);
    if (banner) wrap.append(banner);
    const actions = el('div', 'welcome-actions');
    actions.append(
      button('Start a check', 'btn btn-primary', () => send('goData')),
      button('Try with example data', 'btn btn-secondary', () => send('useDemo'))
    );
    wrap.append(actions);
    const steps = el('div', 'welcome-steps');
    [
      ['01', 'Choose your data', 'CSV or Parquet, from this project'],
      ['02', 'Confirm the columns', 'SAIL guesses them for you'],
      ['03', 'Read the report', 'Plain-language results and fixes'],
    ].forEach(([num, title, desc]) => {
      const card = el('div', 'welcome-step');
      card.append(el('div', 'num', num), el('div', 'title', title), el('div', 'desc', desc));
      steps.append(card);
    });
    wrap.append(steps);
    return wrap;
  }

  function renderStepDots(vm) {
    const nav = el('div', 'steps-nav');
    const currentIndex = STEP_ORDER.indexOf(vm.step);
    STEP_ORDER.forEach((step, i) => {
      const wrap = el('div', 'step-dot-wrap');
      const isCurrent = step === vm.step;
      const isDone = i < currentIndex;
      const dot = el('div', 'step-dot' + (isCurrent ? ' current' : isDone ? ' done' : ''), String(i + 1));
      const label = el('div', 'step-label' + (isCurrent ? ' current' : ''), STEP_LABELS[step]);
      wrap.append(dot, label, el('div', 'step-rule'));
      nav.append(wrap);
    });
    return nav;
  }

  function renderData(vm) {
    const wrap = el('div', 'step-body');
    wrap.append(el('h2', null, 'Which dataset should SAIL check?'));
    wrap.append(el('p', 'lede', 'Pick the table your model trains on: one row per patient per time step.'));
    const banner = errorBanner(vm.error);
    if (banner) wrap.append(banner);
    if (vm.files.length === 0) {
      wrap.append(el('p', 'empty-note', 'No CSV or Parquet files were found in this workspace.'));
    }
    const list = el('div', 'file-list');
    vm.files.forEach((f) => {
      const row = button('', 'file-row' + (f.selected ? ' selected' : ''), () => send('pickFile', { id: f.id }));
      row.textContent = '';
      const info = el('div', 'file-info');
      info.append(el('div', 'file-name', f.name), el('div', 'file-detail', f.detail));
      row.append(info);
      if (f.selected) row.append(el('span', 'file-selected-tag', 'Selected'));
      list.append(row);
    });
    wrap.append(list);
    wrap.append(button('Browse for another file…', 'browse', () => send('browse')));
    return wrap;
  }

  function renderMap(vm) {
    const wrap = el('div', 'step-body');
    wrap.append(el('h2', null, 'Does this look right?'));
    wrap.append(el('p', 'lede', "SAIL read the column names and made its best guess. Change anything that's wrong."));
    const banner = errorBanner(vm.error);
    if (banner) wrap.append(banner);
    const rows = el('div', 'field-rows');
    vm.fields.forEach((f) => {
      const row = el('div', 'field-row');
      const label = el('div', 'field-label');
      label.append(el('span', 'name', f.label), el('span', 'help', f.help));
      const select = el('select', 'field-select');
      select.append(new Option('— none —', ''));
      f.options.forEach((opt) => select.append(new Option(opt, opt)));
      select.value = f.value || '';
      select.addEventListener('change', () => send('changeField', { field: f.key, value: select.value || null }));
      row.append(label, select, el('span', 'field-auto', f.value ? 'Auto-detected' : ''));
      rows.append(row);
    });
    wrap.append(rows);
    return wrap;
  }

  function renderChecks(vm) {
    const wrap = el('div', 'step-body');
    wrap.append(el('h2', null, 'What should SAIL look for?'));
    wrap.append(el('p', 'lede', 'All five checks are on. Most people should keep them that way.'));
    const banner = errorBanner(vm.error);
    if (banner) wrap.append(banner);
    const list = el('div', 'check-toggles');
    vm.checks.forEach((c) => {
      const label = el('label', 'check-toggle');
      const input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = c.on;
      input.addEventListener('change', () => send('toggleCheck', { id: c.id }));
      const text = el('span', null);
      text.append(el('span', 'name', c.name), document.createElement('br'), el('span', 'question', c.question));
      label.append(input, text);
      list.append(label);
    });
    wrap.append(list);
    return wrap;
  }

  function renderRunning(vm) {
    const wrap = el('div', 'step-body');
    wrap.append(el('h2', null, 'Checking your data…'));
    const row = el('div', 'step-body');
    row.style.flexDirection = 'row';
    row.style.alignItems = 'center';
    row.style.gap = '12px';
    row.append(el('div', 'spinner'), el('p', 'running-note', 'Everything runs here on your computer.'));
    wrap.append(row);
    return wrap;
  }

  function renderDone(vm) {
    const wrap = el('div', 'results');
    const banner = errorBanner(vm.error);
    if (banner) {
      wrap.append(el('h2', null, 'The check could not finish'), banner);
      const actions = el('div', 'welcome-actions');
      actions.append(button('New check', 'btn btn-secondary', () => send('restart')));
      wrap.append(actions);
      return wrap;
    }

    const header = el('div', 'results-header');
    const heading = el('div', 'results-heading');
    heading.append(
      el('div', 'eyebrow', 'LEAKAGE REPORT' + (vm.isExample ? ' · EXAMPLE DATA' : '')),
      el('h2', null, vm.headline)
    );
    const actions = el('div', 'welcome-actions');
    actions.append(
      button('New check', 'btn btn-secondary', () => send('restart')),
      button('Export report', 'btn btn-primary', () => send('exportReport'))
    );
    header.append(heading, actions);
    wrap.append(header);

    const body = el('div', 'results-body');
    const list = el('div', 'results-list');
    vm.results.forEach((r) => {
      const card = button('', 'result-card' + (r.selected ? ' selected' : ''), () => send('selectResult', { id: r.id }));
      const top = el('div', 'result-card-top');
      top.append(el('span', 'result-card-name', r.name), el('span', 'badge badge-' + r.status, r.verdictLabel));
      const snippet = el('div', 'result-card-snippet', r.explanation);
      card.append(top, snippet);
      list.append(card);
    });
    body.append(list);

    const detail = el('div', 'result-detail');
    const sel = vm.selectedResult;
    if (sel) {
      const badgeRow = el('div', 'result-detail-badges');
      badgeRow.append(el('span', 'badge badge-' + sel.status, sel.verdictLabel));
      detail.append(badgeRow, el('h3', null, sel.name));
      detail.append(sectionBlock('WHAT THIS CHECKS', sel.question));
      detail.append(sectionBlock('WHAT SAIL FOUND', sel.explanation || '(no detail available)'));
      detail.append(sectionBlock('WHAT TO DO', sel.fix));
    }
    body.append(detail);
    wrap.append(body);

    if (vm.isExample) {
      wrap.append(el('p', 'phase-note', 'All names and findings shown are example data, not real results.'));
    }
    return wrap;
  }

  function sectionBlock(label, text) {
    const block = el('div', 'result-section');
    block.append(el('div', 'result-section-label', label), el('div', 'result-section-body', text));
    return block;
  }

  function renderNav(vm) {
    const nav = el('div', 'nav');
    nav.append(button('Back', 'btn btn-secondary', () => send('back')));
    nav.append(button(vm.nextLabel, 'btn btn-primary', () => send('next'), vm.nextDisabled));
    return nav;
  }

  function render(vm) {
    root.textContent = '';
    // The results step needs a wider two-column layout than the rest of the wizard's narrow form.
    const wrap = el('div', vm.isDone && !vm.error ? 'wizard wizard-wide' : 'wizard');
    if (vm.isWelcome) {
      wrap.append(renderWelcome(vm));
    } else {
      if (vm.showNav) wrap.append(renderStepDots(vm));
      if (vm.isData) wrap.append(renderData(vm));
      else if (vm.isMap) wrap.append(renderMap(vm));
      else if (vm.isChecks) wrap.append(renderChecks(vm));
      else if (vm.isRunning) wrap.append(renderRunning(vm));
      else if (vm.isDone) wrap.append(renderDone(vm));
      if (vm.showNav) wrap.append(renderNav(vm));
    }
    root.append(wrap);
  }

  window.addEventListener('message', (event) => {
    const message = event.data;
    if (message && message.type === 'wizardState') {
      render(message.viewModel);
    }
  });

  send('ready');
})();
