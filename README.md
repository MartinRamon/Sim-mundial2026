# ⚽ Porra Mundial 2026

Aplicación web para que la gente de AMFRESH haga sus **predicciones del Mundial de Fútbol 2026** (Canadá · México · EE. UU.) desde la fase de grupos hasta la final, y compita en un **ranking en directo**.

> **100 % Python, sin dependencias externas.** No usa Node.js, ni frameworks, ni `pip install`, ni CDNs. Funciona únicamente con la **biblioteca estándar de Python** (`http.server`, `sqlite3`, `hashlib`, `hmac`, `json`…). Pensada para entornos con restricciones de seguridad.

- **Fase de grupos real**: los 12 grupos (A–L) con los 48 equipos según el sorteo final de la FIFA.
- **Eliminatorias generadas automáticamente** a partir de los resultados que predice cada usuario, incluyendo la asignación oficial de los **8 mejores terceros** (tabla del *Anexo C* de la FIFA, las 495 combinaciones).
- **Penaltis**: a partir de dieciseisavos, si un usuario predice un empate, puede elegir quién pasa en la tanda de penaltis.
- **Ranking interactivo**: un usuario **ADMIN** introduce los resultados reales y los puntos de todos se recalculan al instante.

## 🧮 Normas de puntuación

| Concepto | Puntos |
| --- | --- |
| Acertar el ganador del partido (o el empate en grupos) | **+1** |
| Acertar el resultado exacto (además del punto por ganador) | **+2 extra** |
| Cláusula antipatriótica (España) | **−3 por ronda** |

**Cláusula antipatriótica**: si predices que España queda eliminada **antes** de lo que ocurre en la realidad, pierdes 3 puntos por cada ronda de diferencia.
Ejemplo: predices que España cae en **octavos** pero llega a **semifinales** → 2 rondas → **−6 puntos**.

## 🚀 Puesta en marcha

Requisito único: **Python 3.8 o superior** (probado con Python 3.12). Nada más.

```bash
# 1. (Opcional) Configurar variables de entorno
cp .env.example .env
#    Edita .env y cambia AUTH_SECRET y ADMIN_PASSWORD

# 2. Crear la base de datos y el usuario admin
python run.py setup

# 3. Arrancar el servidor
python run.py
```

> En Windows usa `py` en lugar de `python` si hace falta: `py run.py setup` y `py run.py`.
> Para copiar el `.env` en PowerShell: `copy .env.example .env`.

La web queda disponible en `http://localhost:8000`.

**En local no hace falta `pip install`**: la app funciona solo con la biblioteca estándar. La única dependencia de `requirements.txt` (`libsql-client`) se usa **exclusivamente para el despliegue en la nube** con base de datos Turso (ver más abajo); con SQLite local ni se importa.

### Variables de entorno (`.env`, todas opcionales)

| Variable | Descripción | Por defecto |
| --- | --- | --- |
| `DB_PATH` | Ruta del fichero SQLite | `porra.db` |
| `AUTH_SECRET` | Secreto para firmar las sesiones. Usa una cadena larga y aleatoria. | *(inseguro por defecto)* |
| `ADMIN_NAME` / `ADMIN_PASSWORD` | Credenciales del admin que crea `python run.py setup`. | `admin` / `admin1234` |
| `HOST` / `PORT` | Dirección y puerto del servidor | `0.0.0.0` / `8000` |
| `TURSO_DATABASE_URL` / `TURSO_AUTH_TOKEN` | Solo para el despliegue en la nube: si se definen, la app usa la base de datos **Turso** (libSQL) en lugar del SQLite local. | *(vacías)* |

> Al arrancar, si no existe el usuario admin se crea automáticamente con `ADMIN_NAME` / `ADMIN_PASSWORD` (ya no es obligatorio ejecutar `python run.py setup`).

## ☁️ Despliegue en la nube (gratis)

Para publicar la web en internet (que cada participante haga su quiniela desde su
propio dispositivo y el admin meta los resultados en directo), consulta la guía
paso a paso en **[DEPLOY.md](DEPLOY.md)**: usa **Render** (servidor) + **Turso**
(base de datos), ambos gratis y sin tarjeta. El repo ya incluye `render.yaml`,
`Procfile` y `Dockerfile` listos.

## 👥 Cómo se usa

1. **Cada participante** entra en `/login`, crea una cuenta con su nombre y una contraseña, y rellena sus predicciones en **Mis predicciones**.
   - Primero la fase de grupos (72 partidos). Al completarla se **desbloquean las eliminatorias**, que se generan con sus resultados.
   - En eliminatorias, si pone un empate aparece el botón para elegir el ganador en **penaltis**.
   - Los cambios se **autoguardan**; además puede pulsar *Confirmar predicciones*.
2. **El admin** (entra con `ADMIN_NAME` / `ADMIN_PASSWORD`) va al **Panel de administración** e introduce los **resultados reales** a medida que se juegan los partidos.
3. **El ranking** (`/ranking`) muestra la clasificación y se actualiza automáticamente cada 30 s.

## 🗂️ Estructura del proyecto

```
run.py                 # Punto de entrada: "python run.py setup" / "python run.py"
porra/
  server.py            # Servidor http.server: rutas, API y sesiones
  views.py             # Generación de HTML (sin motores de plantillas)
  wc_data.py           # Grupos, partidos y plantilla del cuadro de eliminatorias
  bracket.py           # Motor del cuadro: clasificaciones, terceros, propagación
  scoring.py           # Motor de puntuación (ganador/exacto/penalización España)
  validate.py          # Saneamiento de los datos de predicción
  db.py                # Acceso a SQLite (sqlite3)
  auth.py              # Contraseñas (PBKDF2) y sesiones (cookie firmada con HMAC)
  config.py            # Lectura de .env / variables de entorno
data/
  annexC.json          # Tabla oficial del Anexo C (495 combinaciones de terceros)
static/
  styles.css           # Estilos (CSS propio, sin frameworks)
  predict.js           # Editor de predicciones + motor del cuadro en el navegador
  ranking.js           # Ranking interactivo
scripts/
  test_engine.py       # Comprobaciones del motor (cuadro + puntuación)
DEPLOY.md              # Guía de despliegue gratis (Render + Turso)
render.yaml            # Blueprint de Render (servicio web gratuito)
Procfile               # Comando de arranque (Render / Railway)
Dockerfile             # Imagen opcional (Fly.io / contenedores)
```

## ✅ Pruebas del motor

```bash
python scripts/test_engine.py
```

Verifica la generación del cuadro, la asignación de los 8 mejores terceros (Anexo C), la propagación hasta la final y la cláusula de España.

## 📊 Datos

Grupos y cuadro de eliminatorias según el sorteo final de la FIFA para el
[Mundial 2026](https://www.fifa.com/es/tournaments/mens/worldcup/canadamexicousa2026/standings).
La tabla del Anexo C (asignación de los mejores terceros en dieciseisavos) procede de las 495 combinaciones publicadas por la FIFA.
