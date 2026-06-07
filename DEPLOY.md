# Desplegar la Porra del Mundial 2026 (gratis, con Render + Turso)

Esta guia deja la web publicada en internet para que **cualquier participante,
desde cualquier dispositivo**, se cree su cuenta y haga sus predicciones, y para
que **tu (admin)** vayas metiendo los resultados. Todo **gratis y sin tarjeta**.

- **Render** sirve la web (HTTPS y subdominio gratis, despliegue con `git push`).
- **Turso** (libSQL) guarda la base de datos *fuera* de Render, para que las
  predicciones **no se borren** cuando el servidor se reinicie.

> ¿Por que Turso? El plan gratis de Render usa disco "efimero": se borra en cada
> reinicio. Si guardasemos el SQLite ahi, perderiamos los datos. Turso es SQLite
> en la nube, asi que el codigo es casi el mismo y los datos persisten.

---

## Resumen en 4 pasos

1. Subir el proyecto a **GitHub**.
2. Crear una base de datos en **Turso** y copiar su *URL* y su *token*.
3. Desplegar en **Render** con el Blueprint (`render.yaml`) y rellenar 4 variables.
4. Entrar como admin, fijar el cierre y compartir el enlace.

---

## Paso 1 — Subir el proyecto a GitHub

1. Crea una cuenta en https://github.com (gratis) y un repositorio nuevo
   (puede ser **privado**).
2. Desde la carpeta del proyecto:

   ```bash
   git init
   git add .
   git commit -m "Porra Mundial 2026"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/porra-mundial-2026.git
   git push -u origin main
   ```

   > El `.gitignore` ya evita subir `.env`, la base de datos local (`*.db`) y
   > `__pycache__`. No se sube ningun secreto.

---

## Paso 2 — Crear la base de datos en Turso

1. Entra en https://turso.tech y registrate (gratis, **sin tarjeta**).
2. **Crear la base de datos** (lo mas facil, desde la web):
   - Pulsa **Create Database**, ponle un nombre (p. ej. `porra-mundial`),
     elige una region cercana (Europa) y crea.
   - En la pantalla de la base de datos copia la **Database URL**
     (tiene el formato `libsql://porra-mundial-tu-org.turso.io`).
   - Crea un **token de acceso** (boton *Create Token* / *Generate Token*) y
     copialo (es una cadena larga). Guardalo: solo se muestra una vez.

   <details>
   <summary>Alternativa por linea de comandos (opcional)</summary>

   ```bash
   # instala la CLI (Linux/macOS/WSL)
   curl -sSfL https://get.tur.so/install.sh | bash
   turso auth signup
   turso db create porra-mundial
   turso db show porra-mundial --url      # -> la URL libsql://...
   turso db tokens create porra-mundial   # -> el token
   ```
   </details>

   > El plan gratis de Turso es enorme para esto (miles de millones de lecturas
   > al mes y varios GB). Una porra no lo roza ni de lejos.

Apunta estos dos datos, los necesitas en el paso 3:
- `TURSO_DATABASE_URL` = la URL `libsql://...`
- `TURSO_AUTH_TOKEN` = el token

---

## Paso 3 — Desplegar en Render

1. Entra en https://render.com y registrate (gratis, **sin tarjeta** para Web
   Services). Conecta tu cuenta de GitHub.
2. Pulsa **New +** → **Blueprint**.
3. Elige el repositorio que subiste. Render detectara el fichero `render.yaml`
   y propondra crear el servicio `porra-mundial-2026` (plan **Free**).
4. Antes de aplicar, Render te pedira las variables marcadas como "a definir".
   Rellena:

   | Variable               | Valor                                             |
   |------------------------|---------------------------------------------------|
   | `ADMIN_NAME`           | el nombre de tu usuario admin (p. ej. `admin`)    |
   | `ADMIN_PASSWORD`       | **una contrasena fuerte y privada** (cambiala)    |
   | `TURSO_DATABASE_URL`   | la URL `libsql://...` del paso 2                   |
   | `TURSO_AUTH_TOKEN`     | el token del paso 2                               |

   > `AUTH_SECRET` se genera **solo** (Render crea un secreto aleatorio fuerte).
   > No definas `HOST` ni `PORT`: Render asigna el puerto y la app escucha en
   > `0.0.0.0` automaticamente.

5. Pulsa **Apply** / **Create**. Render instalara las dependencias y arrancara.
   En los **Logs** veras algo como:

   ```
   Usuario admin "admin" creado.
   Porra Mundial 2026 escuchando en http://0.0.0.0:10000
   ```

6. Tu web estara en una URL del tipo
   `https://porra-mundial-2026.onrender.com` (la ves arriba en el panel).

---

## Paso 4 — Probar y compartir

1. Abre la URL. Deberias ver la pagina de inicio / login.
2. **Como participante:** cualquiera entra en la URL, pulsa registrarse, elige
   un nombre y una contrasena, y rellena su quiniela. Cada uno desde su movil
   u ordenador.
3. **Como admin:** entra con el `ADMIN_NAME` y `ADMIN_PASSWORD` que pusiste.
   - En **Panel de administracion** (`/admin`) metes los resultados reales segun
     se juegan los partidos: el ranking y las estadisticas se actualizan solos.
   - Ahi mismo fijas la **fecha de cierre**: a partir de esa hora nadie puede
     editar y se pueden ver las quinielas de los demas.
4. Comparte el enlace con tu grupo. ¡Listo!

---

## Cosas que conviene saber

- **Primer acceso lento (arranque en frio):** en el plan gratis, si no hay
  visitas durante ~15 minutos, Render "duerme" el servicio y la siguiente carga
  tarda ~30-60 s. Despues va fluido. Para una porra es asumible.
  - *(Opcional)* Si te molesta, puedes mantenerlo despierto con un ping gratuito
    (p. ej. https://cron-job.org) que visite la URL cada 10-14 min. El plan
    gratis de Render da 750 horas de instancia al mes, suficiente para tenerlo
    casi siempre activo durante el Mundial.

- **Copia de seguridad (recomendable):** Turso ya es duradero, pero por
  tranquilidad puedes exportar la base de datos cuando quieras:

  ```bash
  turso db dump porra-mundial > copia-porra.sql
  ```

- **Seguridad:** usa una `ADMIN_PASSWORD` larga y privada. `AUTH_SECRET` lo
  genera Render. Todo va por HTTPS automaticamente. Si en los logs ves un aviso
  `[SEGURIDAD] ...`, es que alguna variable quedo con el valor por defecto:
  definela en el panel de Render.

- **Actualizar la web:** cada vez que hagas `git push` a `main`, Render
  vuelve a desplegar solo. La base de datos (en Turso) no se toca.

---

## Plan B — Si prefieres no depender de Turso ni del arranque en frio

Si mas adelante quieres SQLite "de toda la vida" sin base de datos externa y sin
que el servicio se duerma, puedes pasarte a **Fly.io** (pide tarjeta solo para
verificar; con esta app no te cobra dentro del plan gratis):

- Despliegas el contenedor con el `Dockerfile` incluido.
- Creas un **volumen persistente** y apuntas `DB_PATH` a el (p. ej.
  `/data/porra.db`): SQLite se queda **sin cambios de codigo** y los datos
  persisten en el volumen.
- No definas `TURSO_DATABASE_URL`: al estar vacia, la app usa SQLite local.
