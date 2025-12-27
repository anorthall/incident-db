import { MessageSquare, Shield } from "lucide-react";

export const SEARCH_COUNT_STORAGE_KEY = "cidb-search-count";
export const HISTORY_STORAGE_KEY = "cidb-search-history";
export const HISTORY_ENABLED_STORAGE_KEY = "cidb-history-enabled";
export const VIEW_MODE_STORAGE_KEY = "cidb-view-mode";
export const TABLE_VIEW_HINT_STORAGE_KEY = "cidb-table-hint-shown";
export const SIDEBAR_COOKIE_KEY = "sidebar_state";

export const MAX_HISTORY = 10;

export const MOBILE_BREAKPOINT = 640;
export const TABLET_BREAKPOINT = 768;
export const SCROLL_THRESHOLD = 400;

export const TABLE_HINT_MIN_SEARCHES = 3;
export const TABLE_HINT_DELAY_MS = 2000;
export const TABLE_HINT_DURATION_MS = 60000;

export const TYPING_SPEED_MS = 120;
export const DELETING_SPEED_MS = 60;
export const TYPING_PAUSE_MS = 4000;

export const CIDBLogoForLightMode = "https://cidb.dev/cdn/assets/img/cidb-light-transparent-md.png";
export const CIDBLogoForDarkMode = "https://cidb.dev/cdn/assets/img/cidb-dark-transparent-md.png";
export const CIDBIconForDarkMode = "https://cidb.dev/cdn/assets/img/cidb-dark-icon.png";
export const CIDBIconForLightMode = "https://cidb.dev/cdn/assets/img/cidb-light-icon.png";

export const DiscordIconForLightMode = "https://cidb.dev/cdn/assets/img/discord-icon-light.png";
export const DiscordIconForDarkMode = "https://cidb.dev/cdn/assets/img/discord-icon-dark.png";

const DISCORD_URL = "https://discord.gg/uMN7ndXQ";

export const navItems: { title: string; url: string; icon: typeof MessageSquare }[] = [];

export const cidbItems = [
  {
    title: "Feedback",
    url: "mailto:feedback@cidb.dev",
    icon: MessageSquare,
  },
  {
    title: "Privacy",
    url: "/privacy",
    icon: Shield,
  },
  {
    title: "Discord",
    url: DISCORD_URL,
    imageLight: DiscordIconForLightMode,
    imageDark: DiscordIconForDarkMode,
  },
];
