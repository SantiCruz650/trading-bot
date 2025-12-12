# Guía de Despliegue en Render (Gratis)

Sigue estos pasos para poner tu Trading Bot en internet totalmente gratis.

## Paso 1: Crear cuenta en Render
1. Ve a [render.com](https://render.com).
2. Haz clic en **"Get Started for Free"**.
3. Regístrate usando tu cuenta de **GitHub** (esto es importante para conectar tu código).

## Paso 2: Conectar tu Repositorio
1. En el panel de control de Render (Dashboard), haz clic en el botón **"New +"** y selecciona **"Blueprint"**.
2. Conecta tu cuenta de GitHub si aún no lo has hecho.
3. Busca el repositorio de tu proyecto (`trading-bot`) y haz clic en **"Connect"**.

## Paso 3: Desplegar
1. Render detectará automáticamente el archivo `render.yaml` que he creado.
2. Verás una lista de servicios que se van a crear:
   - `mcrypto-backend`: El cerebro de tu bot.
   - `mcrypto-db`: La base de datos.
   - `mcrypto-redis`: El sistema de memoria rápida.
3. Haz clic en **"Apply"** o **"Create Resources"**.

## Paso 4: ¡Listo!
Render empezará a construir y desplegar tu aplicación. Esto puede tardar unos minutos.
Cuando termine, verás una URL (algo como `https://mcrypto-backend.onrender.com`) en el servicio `mcrypto-backend`.
¡Ese es tu enlace! Compártelo y entra desde cualquier lugar.

> [!NOTE]
> Como es un servicio gratuito, si nadie entra en 15 minutos, el servidor se "duerme". Cuando vuelvas a entrar, tardará unos 30-50 segundos en despertar. ¡Es normal en el plan gratis!
