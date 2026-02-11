# MCrypto: Manual de Operación y Modelo Mental

Este manual define su relación con el sistema MCrypto. Léalo cuidadosamente para pasar de una mentalidad de "operador manual" a una de "supervisor estratégico".

---

## 🧠 1. El Modelo Mental del Trader
Para tener éxito con MCrypto, debe adoptar una filosofía institucional:

*   **¿Qué hace MCrypto?**: Ejecuta una estrategia matemática de acumulación (DCA) validada por Inteligencia Artificial. Su fuerza reside en la disciplina y la ejecución infatigable de reglas complejas.
*   **¿Qué NO hace?**: No predice el futuro con certeza absoluta ni garantiza ganancias diarias fijas. El trading es un juego de probabilidades, no de certezas.
*   **Expectativa Realista**: No se persigue "hacer dinero rápido". Se persigue **crecimiento sostenido y protección del capital**. Habrá días de lateralización y días de gran actividad.
*   **Gobernanza Algorítmica**: El bot no tiene emociones. No siente miedo de comprar en la caída ni euforia al vender en el pico. **El bot decide, el humano supervisa**.

---

## 📅 2. Flujo de Operación Diaria (5 Minutos)

Su rutina diaria en la plataforma debe ser simple y profesional:

1.  **Entrar (Mañana/Noche)**: Una revisión rápida al día es suficiente.
2.  **Verificar Estado**: Confirme que el indicador de conexión está en `Online`.
3.  **Chequeo de Salud (Equity)**: Observe la curva de capital. No se enfoque en los micro-movimientos de una hora, mire la tendencia de los últimos días.
4.  **Revisión de Riesgo**: Observe la barra de "Exposición Global". Si está en niveles bajos, el bot tiene margen de maniobra. Si está alta, el Risk Governor estará actuando para protegerle.

---

## 🚦 3. Los Estados del Sistema: Entendiendo la Inteligencia

El Dashboard mostrará estados que dictan el comportamiento del bot:

*   **🟢 RUNNING (Normal)**: El mercado es saludable. El bot evalúa señales y ejecuta entradas DCA según el plan.
*   **🟡 PROTECTIVE (Protegido)**: Se ha detectado un aumento en la volatilidad o una caída en la precisión del ML. El bot sigue operando pero con **tamaños de orden reducidos** y mayor cautela.
*   **❄️ FREEZE (Congelado)**: El mercado está en condiciones extremas (caída libre o volatilidad irracional). El bot detiene todas las compras preventivamente. **Es una función de seguridad, no un error**.
*   **🚨 KILL (Switch de Emergencia)**: El sistema se detiene por orden humana o por superar un límite de pérdida crítica. Requiere intervención manual para reiniciar.

---

## 🕹️ 4. Sus Herramientas de Control

*   **Start / Stop**: Use esto cuando desee pausar la actividad por decisiones fundamentales (ej. va a retirar fondos o realizar mantenimiento en su cuenta de Exchange).
*   **Emergency Kill**: Solo para eventos "Cisne Negro" (noticias catastróficas globales). Detiene todo en seco.
*   **Modo Normal vs. Conservador**:
    *   *Normal*: Balance óptimo entre acumulación y riesgo.
    *   *Conservador*: Prioriza la preservación a toda costa; el bot será mucho más selectivo y las órdenes más pequeñas.

---

## 🚫 5. Regla de Oro: Lo que NUNCA debe hacer
*   **No "ayudar" al bot**: No abra operaciones manuales en la misma cuenta. Confundirá los cálculos de equidad y riesgo del motor.
*   **No ignorar los bloqueos**: Si el Risk Governor ha congelado el bot, no lo fuerce a iniciar. El sistema ha visto un peligro que el ojo humano suele ignorar por exceso de optimismo.
*   **No sobre-operar**: La tentación de tocar botones es el mayor enemigo del trader. Si el sistema está en `Normal`, déjelo trabajar.

---

## ✅ 6. Checklist: GO LIVE (Hacia Dinero Real)

Antes de activar el capital real, verifique cada punto:

1.  **APIs**: ¿Están conectadas con permisos de "Spot Trade" y sin permisos de "Withdraw"? (Ver `manual_api.md`).
2.  **Capital Inicial**: Asegúrese de tener el balance en USDT listo en su cuenta de Spot. (Recomendado: Mínimo 1,000 USDT para una gestión de riesgo fluida).
3.  **Modo Inicial**: Inicie siempre en modo **Conservative** las primeras 48 horas para validar que la conexión es estable.
4.  **Prueba de Kill Switch**: Ejecute una prueba (con el bot encendido) para confirmar que puede detenerlo al instante.
5.  **Confirmación Visual**: ¿Ve su balance reflejado correctamente en el Dashboard v2?
6.  **Activación Final**: Una vez verificado todo, presione `START BOT`.

---
*MCrypto: Tecnología de grado institucional para su gestión de capital.*
