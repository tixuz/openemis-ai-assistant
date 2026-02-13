# Registro de Desarrollo: Agente de IA para OpenEMIS (Asistente Full-stack)

Este documento detalla la metodología de prompts utilizada para construir un puente entre la interfaz de OpenEMIS y un motor de IA local.

### Fase 1: Arquitectura de Referencia (Boilerplate)
**Objetivo:** Crear una comunicación fluida entre una extensión de Chrome (V3) y un backend en FastAPI (Python 3.13).

**Prompt utilizado:**
> "Tengo un proyecto de Python 3.13 en PyCharm. Genera un boilerplate para una extensión de Chrome y un backend en FastAPI. La extensión debe inyectar un botón de 'AI' en el DOM y enviar peticiones fetch a localhost:8000/chat."

### Fase 2: Depuración de Red y Seguridad (CORS & PNA)
**Desafío:** Error 400 Bad Request en las peticiones OPTIONS debido a las políticas de seguridad de Chrome al llamar a la red privada (localhost) desde un dominio público (demo.openemis.org).

**Prompt de depuración:**
> "El backend recibe POST pero falla en el preflight OPTIONS con error 400. Implementa un middleware de registro profundo para visualizar los headers. Asegúrate de manejar el encabezado 'Access-Control-Allow-Private-Network: true' para permitir el acceso desde dominios externos a la red local."

### Fase 3: Interfaz de Usuario e Aislamiento Visual
**Objetivo:** Garantizar la legibilidad del asistente independientemente del tema (claro/oscuro) del sitio web anfitrión.

**Prompt de diseño:**
> "Actualiza styles.css. El cuadro de chat debe tener `background-color: white !important` y `color: black !important` para evitar conflictos con el modo oscuro de OpenEMIS. Usa aislamiento de estilos para que el texto sea siempre visible."

### Estado Actual del Proyecto
- [x] Conexión establecida y verificada (200 OK) para OPTIONS y POST.
- [x] Bypass exitoso de las restricciones de "Private Network Access" de Chrome.
- [x] Interfaz de usuario estable y legible en cualquier entorno.