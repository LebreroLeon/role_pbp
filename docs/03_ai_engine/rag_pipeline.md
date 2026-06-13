# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). En este modelo, el motor de IA actúa exclusivamente como soporte privado para el Máster ("Shadow Master") y gestor del historial automatizado, eliminando interacciones directas con jugadores para optimizar costes y garantizar la seguridad del lore.

## 1. El Flujo de Inyección de Contexto del Máster (Paso a Paso)

Cuando el Máster solicita asistencia en su panel privado (ej: consulta de intenciones de un NPC, ganchos de escena o verificación de datos del diario), el sistema ejecuta este pipeline asíncrono en FastAPI:

    [ Solicitud Explícita del Máster / Botón de Panel ]
                        │
                        ▼
    =============================================
    1. Generación de Embeddings Semánticos
       - Se vectoriza la consulta del Máster
    =============================================
                        │
                        ▼
    =============================================
    2. Consulta en Base de Datos Vectorial
       - ChromaDB busca los "top K matches" del
         historial y resúmenes de escenas
    =============================================
                        │
                        ▼
    =============================================
    3. Extracción de Estado Completo (Postgres)
       - Se inyecta el JSON actual de NPCs,
         facciones, misiones y secretos (Completo)
    =============================================
                        │
                        ▼
    =============================================
    4. Construcción del Prompt (El Sándwich)
       - [Flags/Secretos] + [RAG] + [Buffer] + [Input]
    =============================================
                        │
                        ▼
            [ Envío a la API del LLM ]

## 2. Gestión de Memoria Operativa y Configuración

El volumen de datos inyectados se parametriza de forma estricta en la configuración global de la campaña (`memory_settings`) para mitigar el ruido en el modelo:

* **`max_chat_buffer_size` (Ventana de Contexto Deslizable):** El backend acota el buffer inmediato de la escena (últimos 15-20 mensajes de los jugadores). El LLM solo lee esto para entender el "aquí y ahora" del roleo antes de sugerirle una respuesta al Máster.
* **`rag_top_k_matches` (Recuperación Histórica):** Fijado por defecto en `3`. Extrae únicamente los chunks más relevantes del pasado. Al estar limitado al Máster, estos chunks incluyen eventos globales que los jugadores pueden desconocer.

### Estructura de Prioridades del Prompt (El Sándwich del Máster)
La jerarquía de autoridad en la construcción del prompt asegura sugerencias coherentes con el estado actual de la base de datos:

1.  **ESTADO ABSOLUTO (PostgreSQL):** Datos duros del presente. Si un NPC tiene el flag `is_dead: true` o `is_present_in_scene: false`, el prompt instruye a la IA a vetar cualquier acción física de dicho personaje, utilizándolo únicamente como referencia histórica.
2.  **SECRETOS Y LORE COMPLETO:** Información oculta del panel del Máster (`secret_lore_master`). La IA cruza estos datos con el estado del mundo para diseñar giros dramáticos o revelar pistas de forma controlada.
3.  **HISTORIAL SEMÁNTICO (RAG):** Contexto narrativo indexado de las escenas pasadas.
4.  **BUFFER ACTIVO:** El flujo conversacional reciente de los jugadores.

## 3. Cierre de Escena y Mutación Automática de Estado

El mayor consumo automatizado de tokens ocurre de forma controlada únicamente al finalizar un bloque de juego:

1.  **Consolidación del WorldLog:** Al activar el "Cierre de Escena", la IA procesa el buffer completo del chat, genera un resumen ejecutivo de los acontecimientos y lo indexa vectorizado en ChromaDB.
2.  **Sincronización Relacional:** El backend analiza el desenlace para actualizar los esquemas de PostgreSQL (`UPDATE`). Si el transcurso de la escena alteró flags de salud, estados de misiones o la actitud de una facción, el cambio queda consolidado de inmediato para la siguiente sesión.
