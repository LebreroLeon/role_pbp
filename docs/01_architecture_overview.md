# 🏛️ Arquitectura Global del Sistema (Architecture Overview)

Este documento describe la arquitectura técnica, el flujo de datos y la interacción entre componentes de RolePBP (Project Chronicler). El sistema está diseñado como un Hub de Orquestación Narrativa enfocado exclusivamente en dar soporte al Director de Juego (Máster) y automatizar el registro de campaña, optimizando el consumo de tokens y garantizando la seguridad del lore.

## 1. Diagrama de Flujo y Componentes

Para evitar desmaquetados en el renderizado, el flujo de datos entre las distintas capas del sistema se estructura de forma estrictamente vertical:

    [ CAPA DE INTERFAZ (UI) ]
    - App Web / Mobile (React Native / PWA)
    - Panel General del Chat para Jugadores
    - Panel Privado del Máster con herramientas de IA
                        │
                        │ (API REST / WebSockets)
                        ▼
    [ CAPA DE NEGOCIO (BACKEND) ]
    - FastAPI (Python)
    - Motor de Turnos, Dados y Validación de Reglas
    - Middleware de Orquestación RAG "On-Demand"
         │                                 │
         │ (SQL Estructurado)              │ (Embeddings Semánticos)
         ▼                                 ▼
    ============================      ============================
    BASE DE DATOS RELACIONAL          BASE DE DATOS VECTORIAL
    [ PostgreSQL ]                    [ ChromaDB / Pinecone ]
    - Estado Real / Presente          - Historial de Chat (Logs)
    - Fichas de Personajes            - Resúmenes de Escena
    - Banderas (Flags) de Estado      - Lore e Intenciones de NPCs
    ============================      ============================
         │                                 │
         └────────────────┬────────────────┘
                          │
                          │ (Contexto Híbrido Inyectado)
                          ▼
    [ MOTOR COGNITIVO (SOLO MÁSTER) ]
    - OpenAI API (GPT) / Claude API (Anthropic)
    - Generación de ideas, secretos y WorldLog ejecutivo

## 2. Consistencia de Estado y Aislamiento de Capas

El sistema implementa una **Arquitectura en Dos Capas** controlada para mitigar las contradicciones temporales de la IA:

1. **El Estado Presente (PostgreSQL):** Funciona como la "Verdad Absoluta". Almacena los datos duros actuales (ej: si un NPC está vivo, muerto o presente en la escena). El backend consulta estos campos mediante IDs únicos de entidad antes de armar cualquier prompt.
2. **La Memoria Narrativa (ChromaDB):** Almacena las transcripciones del chat y los resúmenes de bloques anteriores. Funciona exclusivamente por similitud semántica.

### Seguridad y Aislamiento del Jugador
Los jugadores no tienen vías de comunicación directa con el motor de IA. Sus mensajes se guardan de forma pasiva en PostgreSQL y se indexan en ChromaDB. Al eliminar el acceso de los jugadores a los LLMs, el sistema se vuelve inmune a ataques de inyección de prompts (*prompt injection*) y garantiza al 100% que no existan fugas accidentales de secretos o *spoilers* de la campaña.

## 3. Flujo Operativo del "Shadow Master"

El backend de FastAPI opera bajo un principio de consulta pasiva:
* **Fase de Juego Activa:** Los jugadores y el Máster chatean de forma nativa. El consumo de tokens es cero.
* **Fase de Soporte Creativo:** El Máster solicita asistencia sobre el comportamiento de un NPC o el lore de un objeto. El backend realiza el "Sándwich de Contexto" (Cruzando las reglas de Postgres con los recuerdos del RAG) y le muestra el resultado únicamente al Máster en su panel privado.
* **Fase de Cierre de Escena:** Al concluir un bloque argumental, el sistema automatiza la reescritura del WorldLog y actualiza las mutaciones de estado relacionales correspondientes.
