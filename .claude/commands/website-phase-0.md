---
description: Phase 0 — wire in the three GitHub Issue Form templates that every "suggest/submit" feature across the new site will link to
---

# Website rebuild, Phase 0 — submission infrastructure

**Standing rule for this entire website rebuild:** this plan supersedes
`docs/WEBSITE_RESTRUCTURE_PLAN.md`'s two-track `/package/`+`/research/` IA — do not try to preserve
both structures. Reuse existing, already-verified content wherever it exists (`FORMAL_ANALYSIS.md`,
`proof.html`, `mechanisms.html`, `papers.html`'s five citations) rather than rewriting it. Every
"comment," "suggest," or "submit" feature across every phase links to one of the three templates
built here — do not build a fourth mechanism, a custom form, or any server-side submission handling
anywhere in this project.

## Step 1 — Add the three issue form templates

Place the three provided YAML files at:
```
.github/ISSUE_TEMPLATE/suggest-a-detector.yml
.github/ISSUE_TEMPLATE/submit-a-paper.yml
.github/ISSUE_TEMPLATE/submit-a-dataset-or-model.yml
```

## Step 2 — Add `.github/ISSUE_TEMPLATE/config.yml`

```yaml
blank_issues_enabled: false
contact_links: []
```

This forces every new issue through one of the three structured forms rather than a free-text
issue — keeps submissions consistently shaped for review.

## Step 3 — Verify the forms actually render correctly

GitHub renders issue forms specially — confirm this by checking the repo's **Issues → New issue**
page (a live check against the real GitHub UI, not just YAML syntax validation) shows all three
templates listed with their correct titles and descriptions, and that the blank/free-text option no
longer appears.

## Step 4 — Prepare (but do not yet embed) the Giscus snippet

If the Giscus `<script>` snippet has been provided, save it to
`docs/giscus_snippet.html` for the pages that will need it in Phase 4 — do not embed it into any
page yet, since no comment-bearing pages exist until then. If the snippet hasn't been provided yet,
skip this step and note it as pending.

## Reporting

Confirm all three templates render on the real GitHub Issues page, confirm blank issues are
disabled, and report whether the Giscus snippet was available to save for Phase 4.
