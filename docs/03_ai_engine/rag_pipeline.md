# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). El objetivo es que la IA responda con precisión técnica e histórica sin sufrir alucinaciones, protegiendo los secretos del Máster y optimizando el consumo de tokens.

## 1. El Flujo de Inyección de Contexto Híbrido (Paso a Paso)

Cuando un usuario solicita explícitamente la interacción o consulta de la IA, el sistema ejecuta de forma asíncrona este pipeline en FastAPI:

    [ Solicitud de Interacción / Comando / Consulta ]
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

## 4. Políticas de Optimización de Tokens y Filosofía "On-Demand"

Para garantizar la soberanía creativa del Director de Juego y la viabilidad económica de la plataforma, el Motor de IA se rige por un principio estricto de **Intervención Bajo Demanda**.

### Soberanía del Máster (Flujo por Defecto)
El Máster tiene control absoluto y nativo sobre el chat de juego. Puede leer las acciones de los jugadores y enviar sus propias respuestas lógicas y descripciones de forma manual sin que intervenga el LLM, resultando en un coste de tokens igual a cero. La IA actúa únicamente como un copiloto pasivo.

### Triggers de Activación del LLM
El backend de FastAPI solo procesará el pipeline de inyección de IA y consumo de créditos en los siguientes casos aislados:
* **Petición del Consultor de Lore:** Un jugador lanza una pregunta explícita en su chat privado etiquetando al bot (`@asistente`).
* **Solicitud de Soporte Creativo (Shadow Master):** El Máster pulsa activamente un botón de la interfaz de su panel privado solicitando ideas de escenas, ganchos o diálogos para un NPC específico.
* **Comandos del Sistema:** Ejecución de comandos estructurales delegados que requieran traducción narrativa (ej: resolución automatizada de una tirada de dados reglamentaria con `/roll`).
* **Hito de Cierre:** Al finalizar formalmente una escena de juego para consolidar el diario de campaña.
