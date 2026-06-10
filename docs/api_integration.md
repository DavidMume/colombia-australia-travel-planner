# Guía de Integración con APIs Externas

Esta guía documenta cómo conectar el proyecto con APIs reales de vuelos en versiones futuras.

## Amadeus API

**URL:** https://developers.amadeus.com/  
**Plan gratuito:** Sí (sandbox con datos de prueba)

### Setup
```bash
pip install amadeus
```

```python
# Agrega a .env (nunca hagas commit de este archivo)
AMADEUS_API_KEY=tu_api_key
AMADEUS_API_SECRET=tu_api_secret
```

```python
from amadeus import Client, ResponseError
from dotenv import load_dotenv
import os

load_dotenv()

amadeus = Client(
    client_id=os.getenv('AMADEUS_API_KEY'),
    client_secret=os.getenv('AMADEUS_API_SECRET'),
)

# Búsqueda de vuelos
response = amadeus.shopping.flight_offers_search.get(
    originLocationCode='BOG',
    destinationLocationCode='BNE',
    departureDate='2026-10-15',
    adults=1,
)
```

## AviationStack

**URL:** https://aviationstack.com/  
**Plan gratuito:** Sí (100 requests/mes)

```python
import requests
import os

API_KEY = os.getenv('AVIATIONSTACK_API_KEY')

response = requests.get(
    'http://api.aviationstack.com/v1/airports',
    params={'access_key': API_KEY, 'search': 'BOG'},
)
```

## OpenFlights Dataset (gratuito, sin API)

Datos estáticos descargables desde https://openflights.org/data.html

```python
import pandas as pd

# Aeropuertos
airports_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
cols = ['id','name','city','country','iata','icao','lat','lon','alt','tz','dst','tz_db','type','source']
df = pd.read_csv(airports_url, header=None, names=cols)

# Rutas
routes_url = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"
```

## Variables de entorno requeridas

Crea un archivo `.env` en la raíz del proyecto (ya está en `.gitignore`):

```env
AMADEUS_API_KEY=
AMADEUS_API_SECRET=
AVIATIONSTACK_API_KEY=
```
