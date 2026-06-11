# ✈️ Colombia → Australia Travel Planner

> **Herramienta de exploración de rutas de vuelo inteligentes desde Colombia hacia Australia.**  
> Visualiza escalas, compara rutas, consulta requisitos de visa y encuentra el mejor momento para viajar.

---

> ⚠️ **DISCLAIMER MIGRATORIO**  
> Este proyecto es una herramienta de orientación y exploración. La información sobre visas, tránsito y requisitos de entrada es **orientativa y puede estar desactualizada**. Antes de comprar cualquier tiquete de vuelo, **verifica siempre** con fuentes oficiales: embajadas, consulados, portales de inmigración de cada país y las aerolíneas directamente.  
> El autor no se hace responsable por decisiones de viaje tomadas basándose en esta herramienta.

---

## 🌏 ¿Qué hace este proyecto?

Planear un vuelo desde Colombia hasta Australia no es sencillo: no hay vuelos directos, las opciones de escalas son muchas, los requisitos de visa varían por país y las temporadas afectan tanto los precios como la experiencia en cada escala.

Este proyecto resuelve eso con:

- **10+ rutas precargadas** desde Bogotá, Medellín y Cali hacia Brisbane, Sydney, Melbourne y Perth
- **Mapa interactivo** que muestra rutas y aeropuertos de escala en el mundo
- **Puntuación inteligente** que evalúa cada ruta por número de escalas, potencial turístico, complejidad de visa y temporada
- **Web app con Streamlit** para filtrar, comparar y explorar rutas visualmente
- **Notebook exploratorio** para análisis de datos y visualizaciones con Plotly
- **Arquitectura preparada** para integrar APIs reales de vuelos en el futuro

### Ejemplo de ruta
```
Bogotá (BOG) → Estambul (IST) → Seúl (ICN) → Brisbane (BNE)
```
Puntuación: 82/100 · 38 h · Potencial turístico: alto · Visa: complejidad media

---

## 📁 Estructura del proyecto

```
colombia-australia-travel-planner/
├── app/
│   └── streamlit_app.py        # Web app principal con Streamlit
├── data/
│   ├── airports.csv            # Dataset de aeropuertos con info de visa
│   └── sample_routes.json      # 10+ rutas de ejemplo curadas manualmente
├── docs/
│   └── api_integration.md      # Guía para integrar APIs futuras
├── notebooks/
│   └── 01_exploratory_analysis.ipynb  # Análisis exploratorio con Plotly
├── src/
│   ├── __init__.py
│   ├── routes.py               # Carga, filtros y queries de rutas
│   ├── scoring.py              # Motor de scoring (0–100)
│   └── map_builder.py          # Generación de mapas con Folium
├── assets/                     # Imágenes, mapas HTML exportados
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🚀 Instalación y ejecución local

### 1. Clona el repositorio
```bash
git clone https://github.com/TU_USUARIO/colombia-australia-travel-planner.git
cd colombia-australia-travel-planner
```

### 2. Crea un entorno virtual
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python -m venv .venv
source .venv/bin/activate
```

### 3. Instala las dependencias
```bash
pip install -r requirements.txt
```

### 4. Corre la web app con Streamlit
```bash
streamlit run app/streamlit_app.py
```
Luego abre tu navegador en `http://localhost:8501`

---

## ☁️ Publicar gratis en Cloudflare Pages

El proyecto incluye una versión web estática en `public/`, compatible con
Cloudflare Pages. La web usa `data/verified_routes.json`: cada ruta está formada
únicamente por segmentos directos vigentes o programados comprobados en
FlightsFrom. No se generan trayectos invirtiendo rutas.

### Probar la versión estática localmente

```bash
bash scripts/build-pages.sh
python -m http.server 8000 --directory dist
```

Abre `http://localhost:8000`.

### Configuración de Cloudflare Pages

1. Sube los cambios a GitHub.
2. En Cloudflare, abre **Workers & Pages → Create → Pages → Connect to Git**.
3. Selecciona este repositorio.
4. Usa estos valores:

| Campo | Valor |
|-------|-------|
| Framework preset | None |
| Build command | `bash scripts/build-pages.sh` |
| Build output directory | `dist` |

Cada nuevo push a GitHub actualizará automáticamente la página.

---

## 📓 Explorar el notebook

```bash
jupyter notebook notebooks/01_exploratory_analysis.ipynb
```

O con JupyterLab:
```bash
jupyter lab
```

---

## 📊 Aeropuertos incluidos

| Región | Códigos IATA |
|--------|-------------|
| 🇨🇴 Colombia (origen) | BOG, MDE, CLO |
| 🇦🇺 Australia (destino) | BNE, SYD, MEL, PER |
| 🌍 Escalas principales | IST, DOH, DXB, ICN, SIN, KUL, MAD, LAX, SCL, AKL, HKG, NRT, GRU |

---

## ➕ Cómo agregar nuevas rutas

1. Abre `data/sample_routes.json`
2. Copia cualquier objeto existente del array `"routes"` y modifícalo
3. Asegúrate de que todos los códigos IATA de `origin`, `destination` y `stopovers` existan en `data/airports.csv`
4. Actualiza el campo `"last_updated"` en `metadata`

### Ejemplo de nueva ruta:
```json
{
  "id": "COL-AUS-011",
  "name": "Bogotá → Bangkok → Sydney",
  "origin": "BOG",
  "destination": "SYD",
  "stopovers": ["BKK"],
  "total_stops": 1,
  "approximate_duration_hours": 35,
  "tourist_potential": "high",
  "season_recommendations": {
    "best_months": [11, 12, 1, 2],
    "notes": "Temporada seca en Tailandia (nov-feb). Verano en Sydney."
  },
  "airlines_example": ["Thai Airways", "Qantas"],
  "visa_complexity": "medium",
  "visa_notes": "Tailandia: colombianos pueden necesitar visa (verificar). Australia: ETA requerida.",
  "score": 80,
  "highlights": ["Bangkok: templos, gastronomía, mercados flotantes", "Thai Airways: servicio reconocido en Asia"]
}
```

---

## 🗺️ Cómo actualizar información de visas

La información de visa está en **dos lugares**:

1. **`data/airports.csv`** — columna `visa_notes`: información orientativa sobre cada aeropuerto
2. **`data/sample_routes.json`** — campo `visa_notes` de cada ruta: resumen para esa combinación de países

> Recuerda siempre agregar la advertencia de verificar con fuentes oficiales.

---

## 🔌 Integración futura con APIs

El proyecto está preparado para conectar APIs reales. Ver `docs/api_integration.md` para detalles.

| API | Propósito | Estado |
|-----|-----------|--------|
| [Amadeus](https://developers.amadeus.com/) | Búsqueda de vuelos en tiempo real | ⏳ Pendiente |
| [AviationStack](https://aviationstack.com/) | Datos de aeropuertos y rutas | ⏳ Pendiente |
| [OpenFlights](https://openflights.org/data.html) | Dataset gratuito de rutas aéreas | ⏳ Pendiente |
| Google Flights | Scraping — solo si los términos lo permiten | ⏳ Revisar T&C |

---

## 🧮 Cómo funciona el scoring

El score (0–100) considera:

| Factor | Peso | Detalle |
|--------|------|---------|
| Penalización por escalas | -8 por escala | Máx -25 |
| Bonus turístico | +8 por escala turística | Máx +15 total |
| Bonus por visa fácil | +10 si "low", +5 si "medium" | |
| Penalización duración | -0.5 por cada hora extra sobre 30h | Máx -10 |
| Bonus de temporada | +5 si el mes es recomendado | |

---

## 🗺️ Roadmap

### v1.0 (actual)
- [x] Dataset manual de aeropuertos y rutas
- [x] Motor de scoring
- [x] Mapa interactivo con Folium
- [x] Web app con Streamlit
- [x] Notebook exploratorio con Plotly

### v2.0 (próximo)
- [ ] Integración con Amadeus API para precios reales
- [ ] Más aeropuertos de escala (BKK, CGK, FRA, LHR)
- [ ] Filtro por rango de precios
- [ ] Alerta de temporada alta/baja
- [ ] Deploy en Streamlit Cloud

### v3.0 (futuro)
- [ ] Modelo de recomendación personalizado (ML)
- [ ] Autenticación de usuario y rutas favoritas
- [ ] Comparador de precios históricos
- [ ] PWA / versión móvil

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Lenguaje | Python 3.10+ |
| Web App | Streamlit |
| Mapas | Folium + AntPath |
| Visualizaciones | Plotly |
| Datos | Pandas |
| Formato datos | CSV + JSON |

---

## 📤 Cómo subir a GitHub

```bash
# Inicializar repositorio
git init
git add .
git commit -m "feat: initial project structure with routes, scoring and Streamlit app"

# Crear repositorio en GitHub (con GitHub CLI)
gh repo create colombia-australia-travel-planner --public --source=. --remote=origin --push

# O manualmente desde github.com:
git remote add origin https://github.com/TU_USUARIO/colombia-australia-travel-planner.git
git branch -M main
git push -u origin main
```

---

## 👤 Autor

Proyecto de portfolio — Data Science / Travel Tech  
Desarrollado como herramienta de exploración personal de viajes Colombia → Australia.

---

*Última actualización: junio 2026*
