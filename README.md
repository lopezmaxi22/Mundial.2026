# Dashboard Mundial 2026 ⚽

Dashboard deportivo del Mundial 2026 (USA · México · Canadá) con las 48 selecciones,
posiciones por grupo, pronósticos por partido, ranking FIFA y estadísticas.
**Se actualiza solo** vía GitHub Action que consulta una API de fútbol.

🔗 Online: https://lopezmaxi22.github.io/Mundial.2026/

## Estructura
- `index.html` — el dashboard (lee `data.json` en vivo)
- `data.json` — datos: fichas de selecciones + partidos/resultados
- `scripts/update_data.py` — actualiza los marcadores desde football-data.org
- `.github/workflows/update.yml` — corre el script cada 2 hs y commitea solo

---

## Puesta en marcha (3 pasos)

### 1. Subir al repo
Desde esta carpeta (`C:\Claude\Mundial.2026`):
```bash
git init
git add .
git commit -m "Dashboard Mundial 2026"
git branch -M main
git remote add origin https://github.com/lopezmaxi22/Mundial.2026.git
git push -u origin main
```

### 2. API key (para el auto-update)
1. Crear cuenta gratis en https://www.football-data.org/client/register
2. Copiar el token que te dan.
3. En el repo: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `FOOTBALL_API_KEY`
   - Secret: *(el token)*

> El plan free incluye la competición World Cup (código `WC`). Si tu plan no la mostrara,
> avisame y cambiamos a otra fuente (API-Football). Sin la key, el dashboard igual
> funciona mostrando lo que haya en `data.json`.

### 3. Activar GitHub Pages
**Settings → Pages → Source: Deploy from a branch → `main` / root → Save.**

Listo. El Action corre cada 2 hs (o a mano desde la pestaña **Actions → Run workflow**),
actualiza `data.json` y la página refleja los nuevos resultados.

---

## Probar local
```bash
python -m http.server
# abrir http://localhost:8000
```

## Actualizar a mano
```bash
set FOOTBALL_API_KEY=tu_token
python scripts/update_data.py
git add data.json && git commit -m "update" && git push
```

## Notas
- El cron de Actions se pausa si el repo queda 60 días inactivo (se reactiva a mano).
- Las fichas editoriales (participaciones, títulos, "cómo llega") son curadas y no las toca el script.
- Para sumar Fecha 2 y 3: se agregan los partidos al array `matches` de `data.json`.
