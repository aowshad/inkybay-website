# Prompt: build the remaining 8 feature pages

Paste this into Claude Code from the repo root.

```
Read CLAUDE.md, especially "Feature pages" and "Writing a feature page (playbook)".

Setup (once): pip install playwright && python3 -m playwright install chromium
Then make a first commit with only the tooling: scripts/audit.py, docs/, the CLAUDE.md
playbook and content/features/. Message: "Add feature playbook, audit script and draft content".

Then build the eight remaining feature pages ONE AT A TIME, in this order:
custom-quote-requests, font-clipart-library, multiple-printing-methods,
smart-add-on-pricing, ready-made-templates, inventory-management,
quantity-discounts, unlimited-product-options.

For each page:
1. Read its draft in content/features/<slug>.json and its entry in
   src/features/_index.json. Improve the copy only if it breaks a playbook rule
   or makes a claim the description does not support. Keep the structure.
2. Move the file to src/features/<slug>.json (git mv).
3. Run: python3 build.py
4. Run: python3 scripts/audit.py <slug>
   If it fails, fix the JSON (never the shared CSS or JS for one page) and repeat.
5. Commit as me: "Add feature page: <Title>". One page per commit.
6. Tell me in one line what you changed in the copy, if anything.

After all eight: run python3 scripts/audit.py --all, show me the result and
git log --oneline -10, then push to main.

Do not change src/template.html, src/feature.css or render_feature.py unless
the audit fails on every page for the same reason; if so, stop and ask me first.
Also flag: the docs link for custom-quote-requests in _index.json points to the
inventory article; ask me for the right link instead of guessing.
```
