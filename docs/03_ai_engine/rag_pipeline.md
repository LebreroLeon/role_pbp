# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). El sistema equilibra el soporte creativo para el Máster ("Shadow Master") y la interacción controlada de los jugadores, optimizando el consumo de tokens mediante restricciones mecánicas y caché semántica.

## 1. El Flujo de Inyección de Contexto Híbrido (Paso a Paso)

Cuando se solicita explícitamente la interacción o consulta de la IA (y supera las reglas de validación de créditos), el sistema ejecuta este pipeline asíncrono en FastAPI:

    [ Solicitud de Interacción / Comando / Consulta ]
                        │
                        ▼
    =============================================
    1. Intercepción y Verificación de Caché
       - Si la consulta ya existe en 'lore_cache',
         devuelve el resultado (Coste: 0 tokens).
    =============================================
                        │ (Miss en Caché)
                        ▼
    =============================================
    2. Generación de Embeddings Semánticos
       - Se vectoriza el mensaje del usuario
    =============================================
                        │
                        ▼
    =============================================
    3. Consulta en Base de Datos Vectorial
       - ChromaDB busca los "top K matches" del
         historial y resúmenes de escenas
    =============================================
                        │
                        ▼
    =============================================
    4. Extracción de Estado Presente (Postgres)
       - Se inyecta el JSON actual de entidades.
       - Si el emisor es JUGADOR: Se purgan
         los campos 'secret_lore_master'.
    =============================================
                        │
                        ▼
    =============================================
    5. Construcción del Prompt (El Sándwich)
       - [Flags] + [RAG] + [Buffer] + [Input]
    =============================================
                        │
                        ▼
            [ Envío a la API del LLM ]

## 2. Gestión de Memoria Operativa y Configuración

El volumen de datos inyectados se parametriza de forma estricta en la configuración de la escena (`memory_settings`):

* **`max_chat_buffer_size` (Ventana de Contexto Deslizable):** El backend acota el buffer inmediato de la escena (últimos 15-20 mensajes de los jugadores) para entender el flujo conversacional reciente.
* **`rag_top_k_matches` (Recuperación Histórica):** Fijado por defecto en `3`. Extrae únicamente los chunks más relevantes del pasado para evitar ruido y ahorrar costes.

### Estructura de Prioridades del Prompt (El Sándwich)
La jerarquía de autoridad en la construcción del prompt asegura respuestas coherentes con el estado actual de la base de datos:
1. **ESTADO ABSOLUTO (PostgreSQL):** Si un NPC tiene el flag `is_dead: true`, la IA tiene prohibido interactuar con él en el presente.
2. **SECRETOS FILTRADOS:** Información de trasfondo (limpia de secretos del Máster si el emisor es un jugador).
3. **HISTORIAL SEMÁNTICO (RAG):** Contexto narrativo de escenas pasadas.
4. **BUFFER ACTIVO:** El hilo del chat reciente.

## 3. Cierre de Escena y Mutación Automática de Estado

Al finalizar formalmente un bloque de juego:
1. **Consolidación del WorldLog:** La IA procesa el buffer del chat, genera un resumen ejecutivo y lo indexa vectorizado en ChromaDB.
2. **Sincronización Relacional:** El backend analiza el desenlace para actualizar los esquemas de PostgreSQL (`UPDATE`), restableciendo además el contador de créditos de los jugadores para la siguiente escena.

## 4. Políticas de Optimización de Tokens y Control de Abuso

Para mitigar picos de costes por parte de los usuarios, el backend implementa un sistema triple de contención:

### Sistema de Créditos Gamificado (Rate Limiting)
* **Límite de Escena:** Los jugadores comparten un pool cerrado de consultas por escena (`max_player_lore_queries_per_scene`, por defecto `3`), almacenado en `remaining_player_lore_tokens`.
* **Validación:** Cada consulta al `@asistente` resta 1 token del pool. Al llegar a 0, FastAPI rechaza las peticiones de los jugadores hasta que el Máster ejecute el "Cierre de Escena".
* **Excepción:** El Máster tiene consultas ilimitadas a su panel privado ("Shadow Master").

### Semantic Caching (Caché de Lore)
Antes de procesar el pipeline del LLM, el backend busca la consulta en la tabla `lore_cache` de PostgreSQL mediante una métrica de similitud. Las dudas repetidas sobre el entorno se resuelven de forma local e instantánea, reduciendo las llamadas redundantes a la API externa a cero.
