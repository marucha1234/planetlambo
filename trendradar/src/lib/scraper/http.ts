/**
 * Capa HTTP del scraper: retries con backoff exponencial + jitter,
 * timeout por request, y errores con contexto suficiente para diagnosticar
 * (status, URL, primeros bytes del body).
 */

export class ScrapeError extends Error {
  constructor(
    message: string,
    public readonly context: {
      url: string;
      status?: number;
      bodySnippet?: string;
      attempt?: number;
      cause?: string;
    }
  ) {
    super(message);
    this.name = "ScrapeError";
  }
}

const DEFAULT_TIMEOUT_MS = 15_000;
const MAX_RETRIES = 3;
const BASE_BACKOFF_MS = 2_000;

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Backoff exponencial con jitter: 2s, 4s, 8s (±25%). */
function backoffDelay(attempt: number): number {
  const base = BASE_BACKOFF_MS * 2 ** attempt;
  const jitter = base * 0.25 * (Math.random() * 2 - 1);
  return Math.round(base + jitter);
}

function isRetryableStatus(status: number): boolean {
  return status === 429 || status >= 500;
}

/**
 * GET con retries. Devuelve el body parseado como JSON.
 * Lanza ScrapeError (nunca falla en silencio) si:
 *  - se agotan los retries por red / 429 / 5xx
 *  - el status es 4xx no retryable (probable cambio de contrato o bloqueo)
 *  - el body no es JSON válido
 */
export async function fetchJson(
  url: string,
  headers: Record<string, string>
): Promise<unknown> {
  let lastError: ScrapeError | null = null;

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    if (attempt > 0) {
      const delay = backoffDelay(attempt - 1);
      console.warn(`[scraper] retry ${attempt}/${MAX_RETRIES} en ${delay}ms → ${url}`);
      await sleep(delay);
    }

    let response: Response;
    try {
      response = await fetch(url, {
        headers,
        signal: AbortSignal.timeout(DEFAULT_TIMEOUT_MS),
        cache: "no-store",
      });
    } catch (err) {
      lastError = new ScrapeError(`Fallo de red pidiendo ${url}`, {
        url,
        attempt,
        cause: err instanceof Error ? err.message : String(err),
      });
      continue; // red: retryable
    }

    const bodyText = await response.text();
    const bodySnippet = bodyText.slice(0, 500);

    if (!response.ok) {
      const error = new ScrapeError(
        `HTTP ${response.status} pidiendo ${url}`,
        { url, status: response.status, bodySnippet, attempt }
      );
      if (isRetryableStatus(response.status)) {
        lastError = error;
        continue;
      }
      // 4xx no retryable: bloqueo o cambio de contrato → falla ruidosa inmediata
      throw error;
    }

    try {
      return JSON.parse(bodyText);
    } catch {
      throw new ScrapeError(
        `Respuesta no-JSON de ${url} (¿cambió el endpoint o nos sirven un captcha?)`,
        { url, status: response.status, bodySnippet, attempt }
      );
    }
  }

  throw lastError ?? new ScrapeError(`Retries agotados pidiendo ${url}`, { url });
}
