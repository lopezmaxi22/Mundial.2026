/**
 * Cloudflare Worker - Proxy para balldontlie FIFA World Cup API
 * --------------------------------------------------------------
 * - La API key NUNCA va en este archivo. Se carga en Cloudflare como
 *   variable SECRETA llamada:  BDL_API_KEY
 *   (Worker > Settings > Variables and Secrets > Add > tipo Secret)
 * - Cachea cada endpoint para no quemar el rate limit (GOAT = 600 req/min).
 * - CORS RESTRINGIDO: solo tus dominios pueden usar el Worker desde el
 *   navegador. Esto evita que otros sitios te roben la cuota de la API.
 */

const BDL_BASE = "https://api.balldontlie.io/fifa/worldcup/v1";

// === SEGURIDAD: solo estos orígenes pueden llamar al Worker desde el browser ===
// Cuando compres tu dominio propio, sumalo acá (descomentá y editá la última línea).
const ALLOWED_ORIGINS = [
  "https://lopezmaxi22.github.io",
  "https://mundial-2026-45s.pages.dev",
  "https://mundial.canillerasmalasia.com.ar",
];

// Endpoints permitidos y su cache (en segundos).
const ROUTES = {
  matches:            25,
  group_standings:    60,
  match_events:       25,
  match_lineups:      120,
  team_match_stats:   25,
  player_match_stats: 40,
  match_shots:        30,
  match_momentum:     30,
  match_best_players: 60,
  match_avg_positions:120,
  match_team_form:    300,
  teams:              86400,
  stadiums:           86400,
  players:            86400,
  rosters:            3600,
  odds:               60,
};

// Devuelve los headers CORS segun el Origin del request.
// Si el Origin no esta en la lista blanca, usa el primero (tu github.io) como
// default, de modo que un sitio de terceros NO recibe permiso para usar la API.
function cors(request) {
  const origin = request.headers.get("Origin") || "";
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    "Access-Control-Allow-Origin": allowed,
    "Access-Control-Allow-Methods": "GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Vary": "Origin",
  };
}

function json(obj, request, status = 200) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...cors(request) },
  });
}

export default {
  async fetch(request, env, ctx) {
    // Preflight CORS
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: cors(request) });
    }

    const url = new URL(request.url);
    const parts = url.pathname.replace(/^\/+/, "").split("/");
    const endpoint = parts[0] === "api" ? parts[1] : parts[0];

    // Health check: /  o  /health
    if (!endpoint || endpoint === "health") {
      return json({ ok: true, service: "mundial-2026 proxy", endpoints: Object.keys(ROUTES) }, request);
    }

    if (!(endpoint in ROUTES)) {
      return json({ error: "endpoint no permitido", allowed: Object.keys(ROUTES) }, request, 400);
    }

    if (!env.BDL_API_KEY) {
      return json({ error: "Falta el secret BDL_API_KEY en el Worker" }, request, 500);
    }

    const ttl = ROUTES[endpoint];

    // Reconstruye la URL upstream conservando TODOS los query params
    const upstream = new URL(`${BDL_BASE}/${endpoint}`);
    url.searchParams.forEach((v, k) => upstream.searchParams.append(k, v));

    // Cache (clave = URL upstream sin la key)
    const cacheKey = new Request(upstream.toString(), { method: "GET" });
    const cache = caches.default;

    const cached = await cache.match(cacheKey);
    if (cached) {
      const r = new Response(cached.body, cached);
      Object.entries(cors(request)).forEach(([k, v]) => r.headers.set(k, v));
      r.headers.set("X-Cache", "HIT");
      return r;
    }

    // Llama a balldontlie con la key (lado servidor, nunca expuesta)
    let apiResp;
    try {
      apiResp = await fetch(upstream.toString(), {
        headers: { Authorization: env.BDL_API_KEY },
      });
    } catch (e) {
      return json({ error: "fallo al contactar balldontlie", detail: String(e) }, request, 502);
    }

    const body = await apiResp.text();
    const r = new Response(body, {
      status: apiResp.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": `public, max-age=${ttl}`,
        "X-Cache": "MISS",
        ...cors(request),
      },
    });

    if (apiResp.status === 200 && ttl > 0) {
      ctx.waitUntil(cache.put(cacheKey, r.clone()));
    }
    return r;
  },
};
