/** Países objetivo. Códigos ISO 3166-1 alfa-2, los mismos que usa el Creative Center. */
export const COUNTRIES = ["AR", "MX", "BR", "ES", "US"] as const;
export type CountryCode = (typeof COUNTRIES)[number];

export const COUNTRY_NAMES: Record<CountryCode, string> = {
  AR: "Argentina",
  MX: "México",
  BR: "Brasil",
  ES: "España",
  US: "Estados Unidos",
};

export const SCRAPE_TARGETS = ["hashtags", "sounds", "videos"] as const;
export type ScrapeTarget = (typeof SCRAPE_TARGETS)[number];

/** Ventana que le pedimos al Creative Center (días). 7 = señal temprana. */
export const TREND_PERIOD_DAYS = 7;

/** Ítems por página y páginas por target×país (2×50 = top 100). */
export const PAGE_SIZE = 50;
export const PAGES_PER_TARGET = 2;
