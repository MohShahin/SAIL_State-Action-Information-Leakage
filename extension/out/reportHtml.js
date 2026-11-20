"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.escapeHtml = escapeHtml;
exports.buildReportHtml = buildReportHtml;
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
const VERDICT_LABEL = {
    pending: 'Pending',
    running: 'Running',
    flagged: 'Flagged',
    passed: 'Passed',
    'not-run': 'Not run',
    off: 'Off',
};
function buildReportHtml(input) {
    const flaggedCount = input.cards.filter((c) => c.status === 'flagged').length;
    const generatedAt = (input.generatedAt ?? new Date()).toISOString();
    const dataset = input.datasetLabel ? escapeHtml(input.datasetLabel) : 'Unknown dataset';
    const cardsHtml = input.cards
        .map((c) => `
    <section class="card card-${c.status}">
      <div class="card-head">
        <h2>${escapeHtml(c.name)}</h2>
        <span class="badge badge-${c.status}">${VERDICT_LABEL[c.status]}</span>
      </div>
      <p class="question"><strong>What this checks:</strong> ${escapeHtml(c.question)}</p>
      <p class="explanation"><strong>What SAIL found:</strong> ${escapeHtml(c.explanation || '(no detail available)')}</p>
      <p class="fix"><strong>What to do:</strong> ${escapeHtml(c.fix)}</p>
    </section>`)
        .join('\n');
    return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>SAIL leakage report</title>
<style>
  body { font-family: -apple-system, "Segoe UI", sans-serif; max-width: 760px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; background: #fff; }
  h1 { font-size: 1.6em; }
  .meta { color: #555; font-size: 0.9em; margin-bottom: 28px; }
  .headline { font-size: 1.2em; font-weight: 600; margin-bottom: 24px; }
  .card { border: 1px solid #ddd; border-radius: 8px; padding: 16px 20px; margin-bottom: 16px; }
  .card-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  .card-head h2 { font-size: 1.1em; margin: 0; }
  .badge { font-size: 0.8em; font-weight: 600; padding: 2px 10px; border-radius: 10px; white-space: nowrap; }
  .badge-flagged { background: #f5a15a; color: #1a1206; }
  .badge-passed { background: #8fbde8; color: #10243a; }
  .badge-not-run, .badge-off, .badge-pending, .badge-running { background: #ddd; color: #333; }
  p { line-height: 1.5; }
  .footer { margin-top: 32px; color: #777; font-size: 0.85em; border-top: 1px solid #eee; padding-top: 16px; }
</style>
</head>
<body>
<h1>SAIL leakage report</h1>
<div class="meta">
  Dataset: ${dataset}${input.isExample ? ' (example data, synthetic)' : ''}<br>
  Generated: ${escapeHtml(generatedAt)}
</div>
<div class="headline">${flaggedCount} of ${input.cards.length} checks found leakage</div>
${cardsHtml}
<div class="footer">
  Generated locally by the SAIL VS Code extension. Nothing in this file was uploaded anywhere.
  ${input.isExample ? 'All names and findings shown are example data, not real results.' : ''}
</div>
</body>
</html>
`;
}
//# sourceMappingURL=reportHtml.js.map