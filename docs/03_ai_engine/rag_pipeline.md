# 🧠 Arquitectura del Motor de IA: Canalización RAG (Rag Pipeline)

Este documento describe el flujo lógico que sigue el backend para enriquecer el contexto de los Modelos de Lenguaje (LLMs) mediante Generación Aumentada por Recuperación (RAG). El objetivo es que la IA responda con precisión técnica e histórica sin sufrir alucinaciones y protegiendo los secretos del Máster.

---

## 1. El Flujo de Inyección de Contexto (Paso a Paso)

Cuando un jugador interactúa en el canal de juego o hace una consulta de Lore, el sistema no envía un prompt vacío. Sigue estrictamente este pipeline asíncrono en FastAPI:

```text
[ Acción del Jugador / Comando / Consulta ]
                 │
                 ▼
 ┌───────────────────────────────────────────────┐
 │ 1. Generación de Embeddings Semánticos        │
 │    (Se vectoriza el mensaje del usuario)     │
 └───────────────┬───────────────────────────────┘
                 │
                 ▼
 ┌───────────────────────────────────────────────┐
 │ 2. Consulta en la Base de Datos Vectorial     │
 │    (ChromaDB / Pinecone busca top K matches)  │
 └───────────────┬───────────────────────────────┘
                 │
                 ▼
 ┌───────────────────────────────────────────────┐
 │ 3. Filtrado de Seguridad y Roles (Middleware) │
 │    ¿El emisor es un JUGADOR?                  │
 │    ──> SI: Se destruye el campo 'secret_lore' │
 │    ──> NO (Máster): Se mantiene completo.    │
 └───────────────┬───────────────────────────────┘
                 │
                 ▼
 ┌───────────────────────────────────────────────┐
 │ 4. Construcción del Prompt Compuesto          │
 │    [System Prompt] + [Contexto RAG Filtrado]  │
 │    + [Buffer de Escena Activa] + [User Input] │
 └───────────────┬───────────────────────────────┘
                 │
                 ▼
      [ Envío a la API del LLM ]
