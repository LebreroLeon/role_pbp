# 🏛️ Arquitectura Global del Sistema (Architecture Overview)

Este documento describe la arquitectura técnica, el flujo de datos y la interacción entre componentes de RolePBP (Project Chronicler). El sistema está diseñado como un Hub de Orquestación Narrativa enfocado exclusivamente en dar soporte al Director de Juego (Máster) y automatizar el registro de campaña, optimizando el consumo de tokens y garantizando la seguridad del lore.

## 1. Diagrama de Flujo y Componentes

El flujo de datos entre las distintas capas del sistema se estructura de forma estrictamente vertical:

```
[ CAPA DE INTERFAZ (UI) ]
- React + Vite (mobile-first, PWA)
- Capacitor → APK Android (prioridad) / iOS / escritorio
- Panel General del Chat para Jugadores
- Panel Privado del Máster con herramientas de IA
                    │
                    │ (API REST / WebSockets)
                    ▼
[ CAPA DE NEGOCIO (BACKEND) ]
- FastAPI (Python async)
- Motor de Turnos, Dados y Validación de Reglas
- Middleware de Orquestación RAG "On-Demand"
- Rate Limiting + Semantic Cache (rutas IA)
                    │
                    │ (SQL + JSONB + pgvector)
                    ▼
===========================================
[ PostgreSQL 16 + pgvector ]
- Estado relacional y flags (verdad absoluta)
- Documentos JSONB de entidades (NPC, PC, Facción…)
- Embeddings vectoriales (memoria narrativa RAG)
- Caché semántica de respuestas del Máster
===========================================
                    │
                    │ (Contexto Híbrido Inyectado)
                    ▼
[ MOTOR COGNITIVO (SOLO MÁSTER) ]
- OpenAI API (GPT) / Claude API (Anthropic)
- Generación de ideas, secretos y WorldLog ejecutivo
```

### Decisión de base de datos vectorial: pgvector

RolePBP usa **pgvector** como extensión de PostgreSQL. Motivos:

| Criterio | pgvector | ChromaDB / Pinecone |
|---|---|---|
| Coste | Gratuito y open source | ChromaDB gratis pero servicio aparte; Pinecone de pago en producción |
| Operaciones | Una sola base de datos (JSONB + vectores) | Dos sistemas que sincronizar |
| Escala del proyecto | Suficiente para miles de chunks por campaña | Overkill para el volumen PBP |
| Docker | Imagen `pgvector/pgvector:pg16` | Contenedor o servicio adicional |

> **Nota de migración:** el código actual en `backend/app/services/rag.py` usa ChromaDB como prototipo. La implementación objetivo es pgvector. Ver `docs/04_data_persistence.md`.

## 2. Consistencia de Estado y Aislamiento de Capas

El sistema implementa una **Arquitectura en Dos Capas** controlada para mitigar las contradicciones temporales de la IA:

1. **El Estado Presente (PostgreSQL / JSONB):** Funciona como la "Verdad Absoluta". Almacena los datos duros actuales (ej: si un NPC está vivo, muerto o presente en la escena). El backend consulta estos campos mediante IDs únicos de entidad antes de armar cualquier prompt.
2. **La Memoria Narrativa (pgvector):** Almacena embeddings de transcripciones del chat y resúmenes de bloques anteriores. Funciona exclusivamente por similitud semántica. **Nunca** es fuente de verdad para flags de estado.

### Seguridad y Aislamiento del Jugador

Los jugadores no tienen vías de comunicación directa con el motor de IA. Sus mensajes se guardan de forma pasiva en PostgreSQL y se indexan en pgvector. Al eliminar el acceso de los jugadores a los LLMs, el sistema se vuelve inmune a ataques de inyección de prompts (*prompt injection*) y garantiza al 100% que no existan fugas accidentales de secretos o *spoilers* de la campaña.

### Modelo de permisos (resumen)

| Rol | Chat de escena | Panel Máster | LLM / RAG | `secret_lore_master` | Cierre de escena |
|---|---|---|---|---|---|
| Jugador | Lectura/escritura propia | Sin acceso | Sin acceso | Sin acceso | Sin acceso |
| Máster | Lectura/escritura total | Acceso completo | On-demand | Acceso completo | Acceso completo |

La autenticación (JWT o sesión) y el aislamiento por `campaign_id` se implementarán en el MVP. Ver `docs/04_data_persistence.md`.

## 3. Flujo Operativo del "Shadow Master"

El backend de FastAPI opera bajo un principio de consulta pasiva:

- **Fase de Juego Activa:** Los jugadores y el Máster chatean de forma nativa. El consumo de tokens es cero.
- **Fase de Soporte Creativo:** El Máster solicita asistencia sobre el comportamiento de un NPC o el lore de un objeto. El backend realiza el "Sándwich de Contexto" (cruzando las reglas de Postgres con los recuerdos del RAG) y le muestra el resultado únicamente al Máster en su panel privado.
- **Fase de Cierre de Escena:** Al concluir un bloque argumental, el sistema automatiza la reescritura del WorldLog y actualiza las mutaciones de estado relacionales correspondientes.

## 4. Estrategia Multiplataforma (Android-first)

El objetivo principal es ejecutar la app en **teléfonos Android**. Debe ser posible desplegarla después en **iOS, Windows, Linux y navegador** sin reescribir la lógica de negocio.

### Enfoque por fases

| Fase | Plataforma | Tecnología | Entregable |
|---|---|---|---|
| **1 — MVP** | Android (navegador) + cualquier navegador | React + Vite, UI **mobile-first**, PWA | App usable en Chrome Android; instalable como PWA |
| **2 — Distribución nativa** | Android APK, iOS | **Capacitor** envolviendo el build de Vite | APK en Play Store; IPA en App Store |
| **3 — Escritorio** | Windows, Linux, macOS | PWA instalada o Capacitor Desktop / Electron (evaluar según demanda) | App de escritorio opcional |

### Por qué React + Capacitor (y no React Native desde el día 1)

- El frontend ya está en **React + Vite**; Capacitor reutiliza el mismo código para Android/iOS.
- **PWA mobile-first** cubre Android inmediatamente sin pasar por la tienda.
- Un solo codebase para web, Android e iOS reduce el coste de mantenimiento del MVP.
- React Native queda descartado para la fase inicial; solo tendría sentido si la UI nativa fuera un requisito crítico desde el día 1.

### Requisitos de UI mobile-first

- Diseño responsive con breakpoints pensados para pantallas de 360–430 px de ancho.
- Áreas táctiles mínimas de 44×44 px.
- Panel Máster y panel Jugador como rutas separadas; en móvil, navegación simplificada (tabs o drawer).
- El backend es agnóstico de plataforma: misma API REST + WebSockets para todos los clientes.
