// SAIL sidebar page. It holds no data of its own: it draws whatever state the extension sends and
// tells the extension when it is ready. Text is always set with textContent, never as HTML.
(function () {
  'use strict';
  const vscode = acquireVsCodeApi();

  const skeleton = document.getElementById('skeleton');
  const app = document.getElementById('app');
  const datasetLabel = document.getElementById('dataset-label');
  const list = document.getElementById('checks');

  const NO_DATASET = 'No dataset chosen';
  const TAGS = { flagged: 'Flagged', passed: 'Passed', off: 'Off', 'not-run': 'Not run' };
  const TICK =
    '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" aria-hidden="true"><path d="M5 12l5 5 9-10"></path></svg>';

  function glyph(status) {
    // 'not-run' draws like 'pending' (an open circle: no verdict either way) but keeps its own tag text.
    const glyphStatus = status === 'not-run' ? 'pending' : status;
    const el = document.createElement('span');
    el.className = 'glyph glyph-' + glyphStatus;
    el.setAttribute('aria-hidden', 'true');
    if (status === 'flagged') {
      el.textContent = '!';
    } else if (status === 'passed') {
      el.innerHTML = TICK; // constant markup, no user text
    }
    return el;
  }

  function render(state) {
    datasetLabel.textContent = state.dataset || NO_DATASET;
    datasetLabel.classList.toggle('is-empty', !state.dataset);

    list.textContent = '';
    for (const check of state.checks) {
      const row = document.createElement('li');
      row.className = 'check';
      row.title = check.question;

      const name = document.createElement('span');
      name.className = 'check-name';
      name.textContent = check.name;

      const tag = document.createElement('span');
      tag.className = 'check-tag tag-' + check.status;
      tag.textContent = TAGS[check.status] || '';

      row.append(glyph(check.status), name, tag);
      list.append(row);
    }

    // First content: swap the skeleton for the real thing.
    if (skeleton) {
      skeleton.remove();
    }
    app.hidden = false;
  }

  window.addEventListener('message', (event) => {
    const message = event.data;
    if (message && message.type === 'state' && message.state) {
      render(message.state);
    }
  });

  vscode.postMessage({ type: 'ready' });
})();
