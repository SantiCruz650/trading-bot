# MCrypto: Guía de Conexión Segura (API de Trading)

Para que MCrypto pueda operar en su nombre, es necesario establecer un puente de comunicación seguro con su casa de cambio (Exchange). Este puente se llama **API**.

### ¿Qué es una API de Trading?
Imagine la API como una "llave digital" que usted entrega al bot. Esta llave permite que MCrypto vea sus saldos y envíe órdenes de compra o venta sin necesidad de que usted le entregue su contraseña personal o acceso total a su cuenta.

---

## 1. Casas de Cambio (Exchanges) Recomendadas
MCrypto está optimizado para trabajar con las instituciones más líquidas y seguras del mercado:
*   **Binance** (Recomendado por volumen y estabilidad)
*   **Bybit** (Excelente para ejecución rápida)
*   **OKX** (Gran variedad de herramientas institucionales)

---

## 2. Guía de Creación de API Keys (Paso a Paso)

1.  **Seguridad**: Inicie sesión en su Exchange y diríjase a la sección de "Gestión de API" (API Management).
2.  **Crear Nueva Llave**: Seleccione "Crear API creada por el sistema".
3.  **Etiqueta**: Póngale un nombre claro como `MCrypto_Bot_Prod`.
4.  **Autenticación**: Complete los pasos de seguridad (Google Authenticator, Email, SMS).

---

## 3. Permisos Críticos (Configuración de Seguridad)

Para proteger su capital, debe seguir estas reglas de permisos **estrictamente**:

### Permisos que DEBEN activarse (✅)
*   **Habilitar Spot Trading** o **Trade**: Permite al bot ejecutar compras y ventas en el mercado al contado.
*   **Leer Datos / Reading**: Permite al bot ver su balance para calcular el riesgo.

### Permisos que JAMÁS deben activarse (❌)
*   **Habilitar Retiros (Withdrawals)**: ⚠️ **PELIGRO**. Bajo ninguna circunstancia el bot debe tener permiso para retirar fondos de su cuenta.
*   **Transferencias Internas**: No es necesario para el funcionamiento de MCrypto.
*   **Futuros / Margen**: Salvo que su estrategia específica lo requiera, manténgalo desactivado para evitar apalancamiento accidental.

---

## 4. Dónde Conectar sus Claves en MCrypto

Una vez generadas, usted obtendrá dos códigos:
1.  **API Key**: El identificador de su llave.
2.  **Secret Key**: La clave privada (Solo se muestra una vez).

**Instrucción**: Pegue estas claves en el archivo de configuración `.env` de su servidor MCrypto o en el panel de herramientas administrativas según le indique su asesor técnico.

---

## 5. Advertencias y Errores Comunes

> [!CAUTION]
> **Errores que causan pérdidas operativas**:
> 1. **Permisos mal configurados**: Si no activa "Spot Trading", el bot enviará señales pero el Exchange las rechazará, causando incoherencia en la estrategia.
> 2. **Restricción de IP**: Si su servidor tiene una IP fija, actívela en el Exchange para que *solo* esa IP pueda usar las llaves.
> 3. **Vencimiento de Llaves**: Algunos Exchanges desactivan las APIs si no hay actividad en 90 días. Revise su panel mensualmente.

---

## 6. Checklist Final de Verificación
- [ ] ¿La llave tiene habilitado el comercio Spot?
- [ ] ¿La opción "Habilitar Retiros" está **desactivada**?
- [ ] ¿He guardado la "Secret Key" en un lugar seguro?
- [ ] ¿He configurado la restricción de IP (si aplica)?
- [ ] ¿El balance en el Exchange coincide con lo que reporta MCrypto?

---
*Su capital es su herramienta más importante. Protéjala con una configuración de API profesional.*
