# Responsiveness Strategy

### Mobile-First Approach
Components will be styled for mobile by default, with responsive prefixes (`md:`, `lg:`) used for larger screens.

### Three-Column Layout Adaptation Strategy
*   **Mobile:** Center content is visible by default. Left and Right sidebars are hidden off-canvas and toggled by header icons.
*   **Tablet (`md`):** Left sidebar becomes persistently visible (condensed). Right sidebar remains off-canvas.
*   **Desktop (`lg`):** The full three-column layout is persistently visible.