# 🏛️ Arquitectura Global del Sistema (Architecture Overview)

Este documento describe la arquitectura técnica, el flujo de datos y la interacción entre componentes de RolePBP (Project Chronicler). El sistema está diseñado como un Hub de Orquestación Narrativa acoplable y agnóstico al sistema de juego, con un enfoque de consistencia de estado en dos capas.

## 1. Diagrama de Bloques Conceptual

El sistema separa la interfaz de usuario de la lógica cognitiva y las reglas de negocio, utilizando un flujo híbrido para garantizar que la IA no sufra de contradicciones temporales.

+-------------------------------------------------------------+
|                     CAPA DE INTERFAZ (UI)                   |
|      [ Aplicación Web / Mobile (React Native / PWA) ]       |
+------------------------------+------------------------------+
                               | (API REST / WebSockets)
                               v
+-------------------------------------------------------------+
|                    CAPA DE NEGOCIO (BACKEND)                |
|                     [ FastAPI (Python) ]                    |
|                                                             |
|  * Motor de Turnos y Dados    * Gestor de Lore (Admin DM)   |
|  * Orquestador RAG híbrido    * Middleware de Consistencia  |
+------------+---------------------------------+--------------+
             |                                 |
             | (SQL Estructurado)              | (Embeddings Semánticos)
             v                                 v
+----------------------------+   +----------------------------+
|   BASE DE DATOS RELACIONAL |   |   BASE DE DATOS VECTORIAL  |
|       [ PostgreSQL ]       |   |    [ ChromaDB / Pinecone ] |
|  - Estado Real / Presente  |   |  - Historial de Chat (Logs)|
|  - Fichas, Flags de Estado |   |  - Resúmenes de Escena     |
|  - IDs de Entidades, Relac.|   |  - Lore Inyectado          |
+------------+---------------+   +--------------+-------------+
             |                                 |
             +----------------+----------------+
                              | (Contexto Híbrido Inyectado + Prompts)
                              v
+-------------------------------------------------------------+
|                       MOTOR COGNITIVO                       |
|           [ OpenAI API (GPT) / Claude API (Anthropic) ]      |
+-------------------------------------------------------------+

## 2. Capas de Datos y Consistencia de Estado

Para evitar que la IA sufra alucinaciones cronológicas (ej: interactuar con un NPC que murió en escenas anteriores porque el RAG recuperó un fragmento antiguo), el sistema implementa una **Arquitectura en Dos Capas**:

1. **El Estado Presente (PostgreSQL):** Funciona como la "Verdad Absoluta". Almacena flags booleanos y enums (`is_dead`, `is_active`) que dictan las reglas del presente. Se consulta directamente por ID de entidad.
2. **El Lore Histórico (ChromaDB / Pinecone):** Funciona como la "Memoria Narrativa". Almacena los matices, resúmenes y descripciones literales de lo acontecido mediante embeddings vectoriales de similitud semántica.

El backend fusiona ambos flujos en un "Sándwich de Contexto" antes de enviar la petición al LLM.
