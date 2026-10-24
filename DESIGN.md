---
name: Strata Landing & Documentation Design System
version: 1.0.0
colors:
  background: "#000000"
  surface_primary: "#0a0a0c"
  surface_secondary: "#121216"
  surface_tertiary: "#1a1a20"
  border_subtle: "rgba(255, 255, 255, 0.08)"
  border_prominent: "rgba(255, 255, 255, 0.16)"
  text_primary: "#f5f5f7"
  text_secondary: "#86868b"
  text_muted: "#6e6e73"
  accent_blue: "#2997ff"
  accent_blue_hover: "#0071e3"
  accent_green: "#30d158"
  accent_orange: "#ff9f0a"
  accent_red: "#ff453a"
typography:
  font_sans: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
  font_mono: "'SF Mono', SFMono-Regular, ui-monospace, Menlo, Monaco, Consolas, monospace"
  hero_title:
    size: "56px"
    line_height: "1.08"
    weight: "700"
    letter_spacing: "-0.015em"
  section_title:
    size: "40px"
    line_height: "1.15"
    weight: "600"
    letter_spacing: "-0.01em"
  card_title:
    size: "22px"
    line_height: "1.25"
    weight: "600"
    letter_spacing: "-0.005em"
  body:
    size: "17px"
    line_height: "1.5"
    weight: "400"
    letter_spacing: "-0.022em"
  body_small:
    size: "14px"
    line_height: "1.4"
    weight: "400"
    letter_spacing: "-0.01em"
  code:
    size: "13px"
    line_height: "1.6"
    weight: "400"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  xxl: "64px"
  section: "96px"
rounded:
  sm: "6px"
  md: "12px"
  lg: "18px"
  xl: "24px"
  pill: "9999px"
components:
  button_primary:
    background: "#2997ff"
    text: "#ffffff"
    padding: "12px 24px"
    radius: "9999px"
  button_secondary:
    background: "rgba(255, 255, 255, 0.08)"
    text: "#f5f5f7"
    padding: "12px 24px"
    radius: "9999px"
  terminal_box:
    background: "#0d0d11"
    border: "1px solid rgba(255, 255, 255, 0.12)"
    radius: "16px"
---

# Overview
This design system defines the visual contract for the Strata Landing Page and GitHub Pages documentation. It is inspired by Apple's product showcase principles: clarity, product-first hierarchy, restrained global navigation, high contrast typography, deep dark aesthetic, and progressive disclosure without noisy gradients.

# Colors
- **Surfaces**: Pure black `#000000` base with progressive layers (`#0a0a0c`, `#121216`, `#1a1a20`) creating optical depth without drop-shadow clutter.
- **Borders**: Subdued hairlines `rgba(255, 255, 255, 0.08)` and active borders `rgba(255, 255, 255, 0.16)`.
- **Text**: Primary `#f5f5f7` (90%+ contrast), Secondary `#86868b` for descriptions, Muted `#6e6e73` for metadata.
- **Accents**: Apple Blue `#2997ff` for calls to action, Green `#30d158` for verified indicators and fast benchmarks.

# Typography
- Follows Apple's San Francisco Pro display / text rhythm.
- Tight letter-spacing on headlines (`-0.015em`), legible neutral mono font for terminal commands and checksums.

# Layout
- Global max container width: `1120px`.
- Restrained top navigation bar with blur effect (`backdrop-filter: blur(20px)`).
- Clear progressive section cadence:
  1. Hero with immediate terminal installer and primary download
  2. Technical Architecture Pillars
  3. Real Measured Hardware Benchmarks (RTX 5060 Ti + 32GB RAM)
  4. Releases, Downloads & Verification
  5. System Requirements and Architecture Overview

# Elevation & Depth
- Optical hierarchy via surface tonal values (`surface_primary` to `surface_tertiary`) rather than heavy blurred drop shadows.
- Subtle inner glows and crisp 1px borders.

# Shapes
- Consistent rounding: `12px` for inner elements, `18px`-`24px` for structural cards, `9999px` (pill) for interactive CTA buttons and status badges.

# Components
- **Navbar**: Translucent sticky bar with responsive brand pill, anchor links, and instant i18n language switcher (EN / 日本語 / 简体中文).
- **Terminal Snippet**: Dark terminal card with command syntax highlighting, shell selector tabs (PowerShell / Bash), and one-click copy with visual toast.
- **Feature Grid**: 2x3 responsive grid with concise technical titles and verifiable architectural evidence.
- **Benchmark Table**: High-readability metric comparison showing measured speedup, slot prefill throughput, and eliminated CUDA stack allocations.
- **Download Module**: Clean artifact cards with version tags, file sizes, direct download links, and verified SHA-256 sums.

# Do's and Don'ts
- **DO**: Keep text concise, factual, and backed by measured numbers.
- **DO**: Provide clear, accessible keyboard navigation and WCAG AA contrast.
- **DON'T**: Use purple gradients or bubbly generic "AI-wrapper" styling.
- **DON'T**: Hide critical download or command actions behind hover states.
