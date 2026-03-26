# Figma Design System Context

## Authentication Status
**User:** Saahil Tamboli (saahil.tamboli1@gmail.com)
**Plan:** Saahil Tamboli's team (Starter)

## Design System Rules

**Generated on:** January 12, 2026

### 1. Token Definitions
- **Definition Source:** Design tokens are primarily defined in `nexero-dashboard/tailwind.config.ts` and `nexero-dashboard/src/app/globals.css`.
- **Colors:**
    - Custom brand colors are defined in `theme.extend.colors.nexero` (e.g., `bg-nexero-bg-primary`, `text-nexero-text-primary`).
    - Semantic tokens (e.g., `background`, `foreground`, `primary`) are mapped to CSS variables in `globals.css` (e.g., `--background`, `--primary`).
- **Typography & Spacing:** Standard Tailwind defaults are used, with specific border radius extensions in `tailwind.config.ts`.
- **Structure:** Tokens follow the shadcn/ui pattern of mapping utility classes to CSS variables for theming support.

### 2. Component Library
- **Location:** UI primitives are located in `src/components/ui/`. Feature-specific components are in `src/components/dashboard/` or `src/components/pages/`.
- **Architecture:** Components are built using `radix-ui` primitives and `class-variance-authority` (CVA) for variant management (e.g., `button.tsx`).
- **Pattern:** `export function ComponentName` or `const ComponentName = React.forwardRef`.

### 3. Frameworks & Libraries
- **Core:** Next.js 14 (App Router), React, TypeScript.
- **Styling:** Tailwind CSS.
- **UI Libs:** shadcn/ui, Radix UI, Lucide React (icons), Recharts (charts).

### 4. Asset Management
- **Icons:** SVG icons are manually defined in `src/components/ui/icons.tsx` or imported from libraries.
- **Images:** Stored in `public/` or handled via Next.js `<Image>` component.

### 5. Styling Approach
- **Methodology:** Utility-first CSS using Tailwind.
- **Global Styles:** Defined in `src/app/globals.css` (@tailwind directives and base layer overrides).
- **Responsiveness:** Tailwind's responsive prefixes (`md:`, `lg:`, etc.).

### 6. Project Structure
- **App Router:** `src/app/` contains page routes (`page.tsx`) and layouts (`layout.tsx`).
- **Components:** grouped by `ui` (reusable primitives), `dashboard` (business logic/widgets), `layout` (shell), and `pages` (page content).

## Missing Context
**Figma File URL:** [Pending User Input]
To access specific Figma tools like `get_design_context` or `get_variable_defs`, a Figma File URL is required.

**Action Required:** Please provide the Figma File URL (e.g., `https://www.figma.com/design/KEY/Title`) to fetch component specific metadata.
