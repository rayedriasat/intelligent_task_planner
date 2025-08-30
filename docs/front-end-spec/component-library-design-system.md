# Component Library / Design System

### Design System Approach
We will implement a practical, token-based design system. All styling will be driven by a set of **Design Tokens** (colors, fonts, spacing) defined below and configured in the `tailwind.config.js` file.

### 1. Design Tokens (The Foundation)
*   **Colors:** The full light and dark mode color palettes defined in the Style Guide below will be configured in `tailwind.config.js`.
*   **Typography:** Font families, sizes, and weights will be configured as tokens.
*   **Spacing, Border Radius, & Shadows:** A consistent scale based on an 8px grid will be mapped to the TailwindCSS theme.

### 2. Component Hierarchy
*   **Level 1: Atoms:** `Button`, `Badge`, `ProgressBar`, `FormInput`, `FormSelect`, `Icon`.
*   **Level 2: Molecules:** `GlassCard`, `SolidCard`, `TaskCard`, `Modal`.
*   **Level 3: Organisms:** `KanbanColumn`, `KanbanBoard`.
