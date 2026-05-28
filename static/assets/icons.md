# Iconography

The POSHub codebase ships **no icon system** — it uses Unicode emoji inline in Jinja templates. Emoji are deliberately replaced with **Lucide** SVG strokes for the Terminal system.

## Why Lucide

- Single 1.75 stroke width — matches Linear / Vercel / GitHub UI vocabulary
- Round caps / round joins — softens the technical feel without being playful
- 1,500+ icons, MIT licensed
- `currentColor` strokes — inherit text colour
- One CDN line, no build step

This is a **substitution** — the original codebase had no icon set to copy. If you'd prefer Heroicons (Tailwind team, similar stroke weight) or Phosphor (slightly heavier, multiple weights), swap the CDN URL. Tokens are stroke-agnostic.

## Loading Lucide

### Option A — CDN (drop into your Jinja base templates)

In `templates/customer/base.html` and `templates/customer/auth_base.html`, before the closing `</body>`:

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script>lucide.createIcons();</script>
```

Then use icons as:

```html
<i data-lucide="shopping-cart" class="ico"></i>
```

The `<i>` is replaced by an `<svg>` at page load. Re-run `lucide.createIcons()` after dynamic insertions.

Add to `colors_and_type.css` (or the relevant page CSS):

```css
.ico { width: 16px; height: 16px; stroke-width: 1.75; vertical-align: -3px; }
.ico-lg { width: 20px; height: 20px; }
.ico-xl { width: 28px; height: 28px; }
```

### Option B — Inline SVG (no JS)

Copy the SVG markup straight from https://lucide.dev/icons/ and paste it inline. The drop-in `css/base.css` includes an `.ico` rule that styles any `<svg class="ico">` correctly. Recommended for the sidebar (3 icons) and flash messages (3 icons) so the page works with JS disabled.

The `ui_kits/poshub/index.html` recreation uses inline SVGs throughout — copy from there if you need ready-to-paste icon markup.

## Emoji → Lucide mapping

| Where | Emoji | Lucide name | Size |
|---|---|---|---|
| `base.html` sidebar Dashboard | 🏠 | `home` | 16px |
| `base.html` sidebar Cart | 🛒 | `shopping-cart` | 16px |
| `base.html` sidebar Orders | 📦 | `package` | 16px |
| `base.html` flash-info prefix | ℹ️ | `info` | 16px |
| `base.html` flash-error prefix | ❌ | `circle-alert` | 16px |
| `base.html` flash-success prefix | ✅ | `circle-check` | 16px |
| `customer_view.html` toast | 🛒 | `shopping-cart` | 16px |
| `main.html` POS terminal product | 🖥️ | `monitor` | 28px |
| `main.html` barcode scanner | 📷 | `scan-line` | 28px |
| `main.html` receipt printer | 🧾 | `printer` | 28px |
| `main.html` payment terminal | 💳 | `credit-card` | 28px |
| `cart.html` item icon | 🛒 | `shopping-cart` | 16px |
| `cart.html` checkout button | 🔒 | `lock` | 16px (precedes label) |
| `cart.html` stripe note | 🔒 | `lock` | 12px |
| `product_detail.html` add-to-cart | 🛒 | `shopping-cart` | 14px |

## Rules

- **Stroke width:** `1.75` (Lucide default)
- **Default size:** `16px` (inline with body text), `20px` (icon-only buttons + sidebar), `28px` (product thumbnails)
- **Colour:** `currentColor` always — never set `stroke` to a hex value
- **No fills:** all icons are stroke-only. If you need a "selected" state, change the parent's colour, not the icon
- **No coloured tile background** under icons — the icon sits on the surface bare, or inside a `--line-2` thumbnail box for product cards only

## Star rating glyphs

Keep `★ / ☆` (Unicode) for star ratings — they typeset cleanly in Geist and don't read as emoji on any platform. The `product_detail.css` colour rule paints them lime-ish-amber (`#B45309`) instead of the old `#f59e0b` "marigold gold" which clashes with the lime accent.

## The wordmark

The brand mark is **"Receipt slot" (direction A)** — a lime rounded square with a wide ink slot and a shorter line beneath it, reading as a card-reader / receipt-printer slot. It says "POS hardware" at a glance. The wordmark is Geist Bold with **POS** in ink (or white on dark) and **Hub** in lime `#84CC16`.

Files in this folder:
- `mark.svg` — mark only, transparent background (lime screen + ink detail; works on light *and* dark)
- `logo.svg` — full lockup, ink wordmark (use on light surfaces)
- `logo-light.svg` — full lockup, white wordmark (use on `--sidebar` / dark)
- `favicon.svg` — mark on a dark rounded tile (browser tab / app icon)

In CSS the mark is no longer a pseudo-element — put the mark **inline** in the brand markup (more robust, no data-URI quirks). The brand anchor holds the SVG + text:

```html
<!-- templates/customer/base.html — .sidebar-brand -->
<a href="{{ url_for('dashboard') }}" class="sidebar-brand">
  <svg class="brand-mark" viewBox="0 0 64 64"><rect x="6" y="10" width="52" height="44" rx="11" fill="#84CC16"/><rect x="16" y="26" width="32" height="7" rx="3.5" fill="#0A0A0A"/><rect x="16" y="38" width="20" height="5" rx="2.5" fill="#0A0A0A" opacity="0.55"/></svg>
  POS<span class="brand-hub">Hub</span>
</a>
```

Same `<svg class="brand-mark">…</svg>` goes inside the public `.logo` anchor in `auth_base.html` and `main.html`. The `.brand-mark` rule (22×22) and `.brand-hub` (lime) are defined in `base.css`, `auth.css`, and `homepage.css`. Or load the SVG file directly:

```html
<a href="/" class="logo"><img class="brand-mark" src="{{ url_for('static', filename='img/mark.svg') }}" alt="">POS<span class="brand-hub">Hub</span></a>
<!-- favicon -->
<link rel="icon" href="{{ url_for('static', filename='img/favicon.svg') }}" type="image/svg+xml">
```
