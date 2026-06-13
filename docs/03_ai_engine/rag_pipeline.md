# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). El objetivo es que la IA responda con precisión técnica e histórica sin sufrir alucinaciones y protegiendo los secretos del Máster.

## 1. El Flujo de Inyección de Contexto Híbrido (Paso a Paso)

Cuando un jugador interactúa en el canal de juego o hace una consulta de Lore, el sistema no envía un prompt vacío. Sigue estrictamente este pipeline asíncrono en FastAPI:

    [ Acción del Jugador / Comando / Consulta ]
                        │
                        ▼
    =============================================
    1. Generación de Embeddings Semánticos
       - Se vectoriza el mensaje del usuario
    =============================================
                        │
                        ▼
    =============================================
    2. Consulta en Base de Datos Vectorial
       - ChromaDB busca los "top K matches"
    =============================================
                        │
                        ▼
    =============================================
    3. Extracción de Estado Presente (Postgres)
       - Se extrae el JSON actual de entidades
    =============================================
                        │
                        ▼
    =============================================
    4. Filtrado de Seguridad y Roles
       - Si es JUGADOR ──> Destruye 'secret_lore'
       - Si es MÁSTER  ──> Mantiene completo
    =============================================
                        │
                        ▼
    =============================================
    5. Construcción del Prompt (El Sándwich)
       - [Reglas] + [RAG] + [Buffer] + [Input]
    =============================================
                        │
                        ▼
            [ Envío a la API del LLM ]

## 2. Gestión de Memoria Operativa y Configuración

El equilibrio entre la inmediatez del chat y el trasfondo histórico se controla mediante los parámetros de configuración de la escena (`memory_settings`):

* **`max_chat_buffer_size` (Ventana de Contexto Deslizable):** Limita la cantidad de mensajes recientes que se envían en texto plano al LLM. Los mensajes antiguos se purgan de la memoria inmediata para ahorrar tokens y evitar saturación, quedando almacenados en PostgreSQL y vectorizados en ChromaDB.
* **`rag_top_k_matches` (Recuperación Histórica):** Define el número exacto de fragmentos del pasado (chunks) que el buscador vectorial recuperará. Un valor de `3` garantiza el balance óptimo: proporciona suficiente contexto (ej: perfil del NPC, estado de la misión y último hito) sin introducir ruido ni elevar el coste de computación.

### Estructura de Prioridades del Prompt (El Sándwich)
Para mitigar alucinaciones de la IA ante contradicciones temporales, el prompt final se construye con la siguiente jerarquía de autoridad:

1.  **REGLAS DEL PRESENTE (PostgreSQL):** Máxima prioridad. Define qué NPCs están vivos, muertos, presentes u hostiles en el instante actual.
2.  **CONTEXTO DEL PASADO (RAG):** Detalla los matices históricos recuperados por similitud según el límite establecido por `rag_top_k_matches`. Si contradice a la regla del presente, el prompt instruye explícitamente a la IA a ignorar el estado pasado y priorizar el presente.
3.  **BUFFER ACTIVO:** El flujo inmediato de la conversación acotado por `max_chat_buffer_size`.

## 3. Cierre de Escena y Mutación de Estado

Al ejecutar la acción de "Cierre de Escena", el pipeline realiza dos acciones atómicas:
1.  Genera un resumen narrativo de la escena y lo indexa en la BD Vectorial para futuras consultas del RAG.
2.  Un parser del backend extrae las mutaciones de estado clave ocurridas (ej: la muerte de un NPC o la resolución de una misión) e impacta un `UPDATE` directo en las tablas relacionales de PostgreSQL, manteniendo la "Verdad Absoluta" actualizada para el inicio de la siguiente escena.
