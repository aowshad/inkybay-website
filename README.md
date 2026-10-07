# InkyBay website

Marketing site for InkyBay (product customizer for Shopify): the locked homepage plus nine feature pages, built
from one template.

- Live: https://aowshad.github.io/inkybay-website/ (feature pages at `features/<slug>/`).
- Build: `python3 build.py` writes the site to `site/` (not in git). Preview it with
  `python3 -m http.server -d site` and open http://localhost:8000/.
- Edit `src/template.html` (homepage and shared look), `src/feature.css` (feature template) and
  `src/features/*.json` (feature page content).
- Check: `python3 scripts/audit.py --all` must print PASS before you commit.
- Deploy: every push to `main` builds and publishes `site/` with GitHub Actions (`.github/workflows/pages.yml`).
- Read `CLAUDE.md` first: working rules, tokens, components, section behaviour and the feature-page playbook.
