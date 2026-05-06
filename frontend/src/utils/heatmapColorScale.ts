/**
 * Heatmap color scale utilities for visualizing expense intensity.
 * Uses logarithmic scaling and a green -> yellow -> red gradient.
 */

/**
 * Calculate logarithmic intensity from weight and max weight.
 * Maps to range [0, 1] for color gradient application.
 * Uses quadratic distribution for better color differentiation at lower ranges.
 */
export function calculateIntensity(weight: number, maxWeight: number): number {
  if (maxWeight <= 0 || weight < 0) {
    return 0;
  }

  // Normalize to [0, 1]
  const normalized = Math.min(weight / maxWeight, 1);

  // Apply quadratic function for better differentiation
  // This makes lower values more distinct while keeping peak at 1
  const squared = normalized * normalized;

  return squared;
}

/**
 * Convert intensity [0, 1] to RGB color.
 * Gradient: Green (#00AA00) -> Yellow (#FFFF00) -> Red (#FF0000)
 */
export function intensityToColor(intensity: number): string {
  // Ensure intensity is in [0, 1]
  const t = Math.min(Math.max(intensity, 0), 1);

  // Three-part gradient: Green -> Yellow -> Red
  let r: number, g: number, b: number;

  if (t < 0.5) {
    // Green to Yellow (0 to 0.5)
    // t_local: 0 = green, 1 = yellow
    const t_local = t * 2;
    r = Math.round(0 + (255 - 0) * t_local); // 0 -> 255
    g = Math.round(170 + 85 * t_local); // 170 -> 255
    b = 0;
  } else {
    // Yellow to Red (0.5 to 1)
    // t_local: 0 = yellow, 1 = red
    const t_local = (t - 0.5) * 2;
    r = 255;
    g = Math.round(255 - 255 * t_local); // 255 -> 0
    b = 0;
  }

  return `rgb(${r}, ${g}, ${b})`;
}

/**
 * Convert intensity [0, 1] to HEX color.
 */
export function intensityToHex(intensity: number): string {
  const rgb = intensityToColor(intensity);

  // Parse rgb(r, g, b) to extract values
  const match = rgb.match(/\d+/g);
  if (!match || match.length < 3) {
    return "#00AA00"; // Default green
  }

  const [r, g, b] = match.map(Number);

  // Convert to hex
  const toHex = (n: number) => {
    const hex = n.toString(16);
    return hex.length === 1 ? "0" + hex : hex;
  };

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`.toUpperCase();
}

/**
 * Calculate opacity based on intensity.
 * Darker colors have higher opacity for better visibility.
 */
export function intensityToOpacity(intensity: number): number {
  // Map [0, 1] to [0.3, 0.8]
  return 0.3 + intensity * 0.5;
}

/**
 * Determine if text on the given intensity background should be light or dark.
 * Returns true if text should be light (white), false if dark (black).
 */
export function shouldUseLightText(intensity: number): boolean {
  // Use dark text for low intensity (light colors), light text for high intensity (dark colors)
  return intensity > 0.5;
}

/**
 * Format weight value for display (with currency and decimals).
 */
export function formatWeightForDisplay(
  weight: number,
  currency: string = "zł",
): string {
  return `${weight.toFixed(2)} ${currency}`;
}

/**
 * Create a color scale legend for heatmap visualization.
 * Returns array of { intensity, color, label } for rendering.
 */
export function generateColorScaleLegend(
  maxWeight: number,
  steps: number = 5,
  currency: string = "zł",
): Array<{ intensity: number; color: string; label: string }> {
  const legend = [];

  for (let i = 0; i < steps; i++) {
    const intensity = i / (steps - 1);
    const weight = intensity ** 2 * maxWeight; // Quadratic distribution for better spacing

    legend.push({
      intensity,
      color: intensityToHex(intensity),
      label: formatWeightForDisplay(weight, currency),
    });
  }

  return legend;
}
