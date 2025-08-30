# Branding & Style Guide

### Visual Identity & Theme Strategy
The aesthetic is "Focused Calm": a modern, minimalist interface that feels clean and professional. A dual-theme (light/dark) system will be implemented using TailwindCSS's dark mode class strategy, controlled by a theme-toggle component.

### Color Palette

**Light Theme**
| Role | Color Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| Background | `bg-primary` | `#F8F9FA` | Main app background |
| Surface | `bg-surface` | `#FFFFFF` | Card backgrounds, modals |
| Primary | `primary` | `#4A90E2` | Buttons, links, active states |
| Text | `text-primary` | `#212529` | Main text color |
| Text Muted | `text-secondary` | `#6C757D` | Secondary text, placeholders |
| Border | `border` | `#DEE2E6` | Card borders, dividers |

**Dark Theme**
| Role | Color Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| Background | `bg-primary` | `#121212` | Main app background |
| Surface | `bg-surface` | `#1E1E1E` | Card backgrounds, modals |
| Primary | `primary` | `#58A6FF` | Buttons, links, active states |
| Text | `text-primary` | `#E0E0E0` | Main text color |
| Text Muted | `text-secondary` | `#8B949E` | Secondary text, placeholders |
| Border | `border` | `#30363D` | Card borders, dividers |

### Typography
*   **Font Family:** "Inter" (from Google Fonts) will be used for all UI text for its excellent readability.
*   **Typographic Scale:**
    | Element | Font Size | Font Weight |
    | :--- | :--- | :--- |
    | H1 | 2.5rem (40px) | 700 (Bold) |
    | H2 | 2rem (32px) | 700 (Bold) |
    | H3 | 1.5rem (24px) | 600 (Semi-bold) |
    | Body | 1rem (16px) | 400 (Regular) |
    | Small | 0.875rem (14px) | 400 (Regular) |

### Spacing & Layout
*   **Grid System:** An 8px grid system will be used. Spacing tokens in Tailwind will be multiples of 8px (e.g., `space-2` = 8px, `space-4` = 16px).
*   **Layout:** The three-column layout will use generous padding and whitespace to feel uncluttered.

### Core Element Styles
*   **Buttons:** `border-radius: 8px`, subtle `box-shadow` on hover, and a soft transition effect.
*   **Cards (`SolidCard`):** `border-radius: 12px`, a soft `box-shadow`, and a 1px solid border.
*   **Glass Morphism (`GlassCard`):** This effect will be retained for key elements like the nav bar and hero sections. It will be implemented with a semi-transparent blurred background (`backdrop-blur`) and a subtle white border to create a sense of depth.
