# Responsive Best Practices

This note adapts the Conde Nast responsive-design guide to the WSIS mobile rewrite.

Reference:
- [Conde Nast Responsive Design Best Practices](https://github.com/CondeNast/Responsive-Design-Best-Practices)

## Core principles we should adopt

### 1. Start mobile-first

The Conde Nast guide recommends a mobile-first approach so the design grows from the smallest screen instead of shrinking a desktop layout later. For WSIS, that means:

- design for `390x844` first
- treat desktop as the expanded layout
- avoid making the map or data tables the first thing the user must parse on phone screens

### 2. Keep structure lean

The guide emphasizes lean HTML and clear structure. In WSIS terms:

- keep sections simple and self-describing
- reduce nested layout containers
- use fewer side-by-side blocks on mobile
- avoid repeating the same metric blocks in multiple dense formats

### 3. Separate structure, styling, and behavior

The guide recommends moving styles out of inline markup and keeping JS logic organized. For WSIS:

- centralize layout rules instead of spreading visual overrides across page sections
- keep visual tokens and responsive rules explicit
- avoid page-specific one-off mobile hacks unless they are temporary

### 4. Stack content as screens shrink

The source calls out stacking content on smaller screens as a common responsive pattern. WSIS should apply that directly:

- replace multi-column sections with stacked cards below mobile breakpoint
- render metric grids as labeled rows or two-up cells max
- collapse large tables into summaries or expanders on phone

### 5. Use media-query style breakpoint logic based on design, not device names

The Conde Nast guide prefers breakpoints that follow the design rather than hard-coding exact device lists. For WSIS:

- define responsive modes such as `mobile`, `tablet`, and `desktop`
- tune them around layout breakage, not just named devices
- still validate against iPhone 12 because that is the current target

### 6. Make images and visuals fluid

The guide highlights `max-width: 100%` and responsive image handling. For WSIS:

- all screenshots, charts, and visuals should fit their containers
- chart height should shrink on mobile
- the map should become a preview or secondary panel rather than dominate the first fold

### 7. Plan for touch behavior, not mouse behavior

The guide notes that touch interaction behaves differently from desktop click behavior. In WSIS:

- city selection should not depend only on precise taps on dense map points
- buttons should be full-width and thumb-friendly on phone
- filters should be operable without tiny sliders packed into grids

## WSIS-specific implementation rules

### Home page

- show decision summary before the map
- put filters above or before the map on mobile
- provide a non-map city picker on mobile
- keep shortlist cards one per row

### City Profile

- turn four-up metric rows into stacked or two-up blocks
- move trust tables into compact cards or expanders
- keep the first screen focused on verdict, rent, salary fit, and trust

### Comparison

- compare only Chicago plus one candidate in David mode
- use stacked comparison cards instead of desktop-style charts as the lead element
- demote large radar/table sections below the first decision summary

## Anti-patterns to avoid

- desktop-first `st.columns(...)` everywhere
- wide `st.dataframe(...)` blocks as primary mobile content
- map-first interaction without a list fallback
- chart-heavy first screens
- small touch targets inside dense filter trays

## Practical acceptance criteria

- no horizontal scroll at `390x844`
- primary CTA visible in the first viewport
- Chicago baseline visible in David mode before major scrolling
- core decision content readable before the full map
- mobile users can inspect and compare cities without needing pinpoint map taps
