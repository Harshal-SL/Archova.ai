/**
 * Dynamic Architecture Topology Color System
 * Provides curated, harmonized, vibrant color palettes for HLD and LLD components
 * and ensures that all connection edges use the exact same color as their originating component.
 */

export interface ComponentColorTheme {
  name: string;
  primary: string;         // Vibrant core color (e.g. "#10B981")
  darkColor: string;       // High-luminescence contrast for dark canvas (e.g. "#34D399")
  lightColor: string;      // Heavy deep saturated contrast for light canvas (e.g. "#047857")
  bgDark: string;          // Subtle gradient wash (dark)
  bgLight: string;         // Rich heavy gradient wash (light)
  borderDark: string;      // Card border (dark)
  borderLight: string;     // Heavy solid card border (light)
  glow: string;            // Shadow glow color
  badgeBgDark: string;     // Badge/icon container bg (dark)
  badgeBgLight: string;    // Solid heavy badge container bg (light)
  badgeBorderDark: string; // Badge/icon container border (dark)
  badgeBorderLight: string;// Heavy badge container border (light)
  badgeTextDark: string;   // High-contrast text (dark)
  badgeTextLight: string;  // Pure white text against heavy badge (light)
  headerBarLight: string;  // Solid heavy accent color for top/left bar (light)
  headerBarDark: string;   // Solid accent color for top/left bar (dark)
}

function hexToRgb(hex: string): [number, number, number] {
  const clean = hex.replace("#", "");
  const bigint = parseInt(clean, 16);
  if (isNaN(bigint) || clean.length !== 6) {
    return [59, 130, 246]; // fallback blue
  }
  return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
}

export function createColorTheme(
  name: string,
  primary: string,
  darkColor: string,
  lightColor: string
): ComponentColorTheme {
  const [pr, pg, pb] = hexToRgb(primary);
  const [dr, dg, db] = hexToRgb(darkColor);
  const [lr, lg, lb] = hexToRgb(lightColor);

  return {
    name,
    primary,
    darkColor,
    lightColor,
    bgDark: `rgba(${pr}, ${pg}, ${pb}, 0.14)`,
    bgLight: `rgba(${lr}, ${lg}, ${lb}, 0.12)`,
    borderDark: `rgba(${dr}, ${dg}, ${db}, 0.50)`,
    borderLight: lightColor, // Solid, heavy color border in light mode!
    glow: `rgba(${pr}, ${pg}, ${pb}, 0.40)`,
    badgeBgDark: `rgba(${pr}, ${pg}, ${pb}, 0.22)`,
    badgeBgLight: lightColor, // Solid heavy colored badge in light mode!
    badgeBorderDark: `rgba(${dr}, ${dg}, ${db}, 0.60)`,
    badgeBorderLight: lightColor,
    badgeTextDark: darkColor,
    badgeTextLight: "#ffffff", // Pure crisp white icon/text against the heavy solid color badge!
    headerBarLight: lightColor,
    headerBarDark: darkColor,
  };
}

// ── 16 Curated Heavy Vibrant Modern Tech Colors ──
export const COLOR_PALETTE: ComponentColorTheme[] = [
  createColorTheme("emerald", "#10B981", "#34D399", "#047857"),   // 0: Heavy Emerald / Auth / Security
  createColorTheme("blue", "#3B82F6", "#60A5FA", "#1D4ED8"),      // 1: Heavy Royal Blue / Catalog
  createColorTheme("fuchsia", "#D946EF", "#E879F9", "#A21CAF"),   // 2: Heavy Fuchsia / Circulation / Loans
  createColorTheme("amber", "#F59E0B", "#FBBF24", "#B45309"),     // 3: Heavy Warm Amber / User Actor / State
  createColorTheme("teal", "#14B8A6", "#2DD4BF", "#0F766E"),      // 4: Heavy Mint Teal / Inventory / Returns
  createColorTheme("purple", "#8B5CF6", "#A78BFA", "#6D28D9"),    // 5: Heavy Electric Violet / Gateway / Ingress
  createColorTheme("crimson", "#EF4444", "#F87171", "#B91C1C"),   // 6: Heavy Crimson Red / Cache / WAF
  createColorTheme("orange", "#F97316", "#FB923C", "#C2410C"),    // 7: Heavy Vivid Orange / Admin / Router
  createColorTheme("sky", "#0EA5E9", "#38BDF8", "#0369A1"),       // 8: Heavy Sky Blue / Web App / ALB
  createColorTheme("rose", "#F43F5E", "#FB7185", "#BE123C"),      // 9: Heavy Ruby Rose / Prometheus / Blacklist
  createColorTheme("indigo", "#6366F1", "#818CF8", "#4338CA"),    // 10: Heavy Deep Indigo / Database / CI/CD
  createColorTheme("yellow", "#EAB308", "#FACC15", "#A16207"),    // 11: Heavy Golden Bronze / Notification
  createColorTheme("cyan", "#06B6D4", "#22D3EE", "#0E7490"),      // 12: Heavy Deep Cyan / Kubernetes / Alembic
  createColorTheme("violet", "#A855F7", "#C084FC", "#7E22CE"),    // 13: Heavy Orchid Violet / Reporting / BI
  createColorTheme("lime", "#84CC16", "#A3E635", "#4D7C0F"),      // 14: Heavy Forest Lime / Audit Trail
  createColorTheme("vermilion", "#FF5722", "#FF7043", "#D84315"), // 15: Heavy Flame Vermilion / RabbitMQ
];

// Helper lookup by name
const PALETTE_MAP = new Map<string, ComponentColorTheme>(
  COLOR_PALETTE.map((t) => [t.name, t])
);

// Explicit Mapping for High-Level Design (HLD) & All 5 Low-Level Designs (LLDs)
const KNOWN_COMPONENT_THEMES: Record<string, string> = {
  // ── HLD Components ──
  "actor-student": "amber",
  "actor-admin": "orange",
  "node-frontend": "sky",
  "node-gateway": "purple",
  "svc-1": "emerald",
  "svc-2": "blue",
  "svc-3": "fuchsia",
  "svc-4": "yellow",
  "svc-5": "teal",
  "svc-6": "violet",
  "node-rabbitmq": "vermilion",
  "node-database": "indigo",
  "node-redis": "crimson",
  "node-github-actions": "indigo",
  "node-k8s": "cyan",
  "node-prometheus": "rose",

  // ── Backend LLD Components ──
  "bep-1": "emerald",
  "bep-2": "blue",
  "bep-3": "fuchsia",
  "bep-4": "teal",
  "bep-5": "orange",
  "bsvc-1": "emerald",
  "bsvc-2": "blue",
  "bsvc-3": "fuchsia",
  "bsvc-4": "yellow",
  "bsvc-5": "teal",
  "bsvc-6": "violet",
  "brepo-1": "emerald",
  "brepo-2": "blue",
  "brepo-3": "fuchsia",
  "brepo-4": "teal",
  "brepo-5": "violet",
  "bmodel-1": "emerald",
  "bmodel-2": "blue",
  "bmodel-3": "fuchsia",
  "bmodel-4": "teal",
  "bmodel-5": "violet",

  // ── Database LLD Components ──
  "dtbl-users": "emerald",
  "dtbl-books": "blue",
  "dtbl-loans": "fuchsia",
  "dtbl-borrows": "amber",
  "dtbl-returns": "teal",
  "dnode-redis": "crimson",
  "dnode-pgbouncer": "purple",
  "dnode-alembic": "cyan",

  // ── Frontend LLD Components ──
  "fpg-1": "emerald",
  "fpg-2": "blue",
  "fpg-3": "fuchsia",
  "fpg-4": "teal",
  "fpg-5": "orange",
  "fcmp-1": "emerald",
  "fcmp-2": "blue",
  "fcmp-3": "fuchsia",
  "fcmp-4": "teal",
  "fcmp-5": "violet",
  "fnode-zustand": "amber",
  "fnode-tanstack": "crimson",
  "fnode-axios": "sky",
  "fnode-zod": "purple",

  // ── Cloud LLD Components (AWS ECS Fargate) ──
  "cnode-route53": "amber",
  "cnode-cloudfront": "purple",
  "cnode-alb": "sky",
  "cecs-1": "emerald",
  "cecs-2": "blue",
  "cecs-3": "fuchsia",
  "cecs-4": "yellow",
  "cecs-5": "teal",
  "cecs-6": "violet",
  "cnode-rds": "indigo",
  "cnode-elasticache": "crimson",
  "cnode-github": "indigo",
  "cnode-cloudwatch": "vermilion",

  // ── Security LLD Components ──
  "secnode-waf": "crimson",
  "secnode-tls": "sky",
  "secnode-oauth": "orange",
  "secnode-jwt": "purple",
  "secnode-rbac": "emerald",
  "secnode-blacklist": "rose",
  "secnode-kms": "amber",
  "secnode-audit": "teal",
};

/**
 * Deterministically hash any string into a valid palette index
 */
function hashStringToPaletteIndex(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (hash << 5) - hash + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash) % COLOR_PALETTE.length;
}

/**
 * Resolves the ComponentColorTheme for any component/node.
 * Checks explicit ID registry first, then semantic keywords, then deterministic hash fallback.
 */
export function getComponentTheme(
  nodeId?: string,
  label?: string,
  category?: string,
  explicitColor?: string
): ComponentColorTheme {
  // 1. Explicit hex override
  if (explicitColor && explicitColor.startsWith("#")) {
    return createColorTheme("custom", explicitColor, explicitColor, explicitColor);
  }

  const cleanId = (nodeId || "").toLowerCase().trim();

  // 2. Direct match in registry
  if (KNOWN_COMPONENT_THEMES[cleanId]) {
    const themeName = KNOWN_COMPONENT_THEMES[cleanId];
    const theme = PALETTE_MAP.get(themeName);
    if (theme) return theme;
  }

  // 3. Match by service numbering pattern (e.g. svc-1 -> emerald, svc-2 -> blue, etc.)
  const svcMatch = cleanId.match(/(?:svc|service)[-_]?0?([1-9])/i);
  if (svcMatch && svcMatch[1]) {
    const idx = (parseInt(svcMatch[1], 10) - 1) % COLOR_PALETTE.length;
    return COLOR_PALETTE[idx];
  }

  // 4. Semantic keyword heuristic
  const textToScan = `${cleanId} ${label || ""} ${category || ""}`.toLowerCase();
  if (textToScan.includes("auth") || textToScan.includes("login") || textToScan.includes("role") || textToScan.includes("user")) {
    return PALETTE_MAP.get("emerald")!;
  }
  if (textToScan.includes("search") || textToScan.includes("catalog") || textToScan.includes("book")) {
    return PALETTE_MAP.get("blue")!;
  }
  if (textToScan.includes("borrow") || textToScan.includes("loan") || textToScan.includes("circulation")) {
    return PALETTE_MAP.get("fuchsia")!;
  }
  if (textToScan.includes("notification") || textToScan.includes("reminder") || textToScan.includes("alert")) {
    return PALETTE_MAP.get("yellow")!;
  }
  if (textToScan.includes("inventory") || textToScan.includes("asset") || textToScan.includes("rfid") || textToScan.includes("return")) {
    return PALETTE_MAP.get("teal")!;
  }
  if (textToScan.includes("report") || textToScan.includes("analytics") || textToScan.includes("metrics") || textToScan.includes("bi")) {
    return PALETTE_MAP.get("violet")!;
  }
  if (textToScan.includes("queue") || textToScan.includes("rabbit") || textToScan.includes("kafka") || textToScan.includes("event")) {
    return PALETTE_MAP.get("vermilion")!;
  }
  if (textToScan.includes("gateway") || textToScan.includes("ingress") || textToScan.includes("nginx")) {
    return PALETTE_MAP.get("purple")!;
  }
  if (textToScan.includes("redis") || textToScan.includes("cache") || textToScan.includes("waf")) {
    return PALETTE_MAP.get("crimson")!;
  }
  if (textToScan.includes("postgres") || textToScan.includes("database") || textToScan.includes("sql") || textToScan.includes("rds")) {
    return PALETTE_MAP.get("indigo")!;
  }
  if (textToScan.includes("frontend") || textToScan.includes("react") || textToScan.includes("web") || textToScan.includes("alb")) {
    return PALETTE_MAP.get("sky")!;
  }
  if (textToScan.includes("admin") || textToScan.includes("librarian") || textToScan.includes("oauth")) {
    return PALETTE_MAP.get("orange")!;
  }
  if (textToScan.includes("student") || textToScan.includes("actor") || textToScan.includes("kms")) {
    return PALETTE_MAP.get("amber")!;
  }

  // 5. Deterministic hash fallback
  const index = hashStringToPaletteIndex(cleanId || label || "component");
  return COLOR_PALETTE[index];
}

/**
 * Resolves the connection/edge color.
 * Guaranteed to match the originating/source component's color!
 */
export function getEdgeTheme(
  sourceId?: string,
  targetId?: string,
  explicitStroke?: string
): ComponentColorTheme {
  if (explicitStroke && explicitStroke.startsWith("#")) {
    return createColorTheme("custom-edge", explicitStroke, explicitStroke, explicitStroke);
  }
  return getComponentTheme(sourceId);
}

/**
 * Layer group container accent theme
 */
export function getLayerGroupTheme(label?: string, id?: string): ComponentColorTheme {
  const text = `${id || ""} ${label || ""}`.toLowerCase();
  if (text.includes("frontend") || text.includes("page")) return PALETTE_MAP.get("sky")!;
  if (text.includes("backend") || text.includes("service") || text.includes("microservice") || text.includes("domain")) return PALETTE_MAP.get("emerald")!;
  if (text.includes("database") || text.includes("data") || text.includes("persistence") || text.includes("schema") || text.includes("model")) return PALETTE_MAP.get("indigo")!;
  if (text.includes("deployment") || text.includes("deploy") || text.includes("devops") || text.includes("observability") || text.includes("cloud")) return PALETTE_MAP.get("cyan")!;
  if (text.includes("gateway") || text.includes("ingress") || text.includes("security")) return PALETTE_MAP.get("purple")!;
  if (text.includes("async") || text.includes("queue") || text.includes("event")) return PALETTE_MAP.get("vermilion")!;
  return PALETTE_MAP.get("blue")!;
}
