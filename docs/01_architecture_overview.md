# 🏛️ Arquitectura Global del Sistema (Architecture Overview)

Este documento describe la arquitectura técnica, el flujo de datos y la interacción entre componentes de **RolePBP (Project Chronicler)**. El sistema está diseñado como un *Hub de Orquestación Narrativa* acoplable y agnóstico al sistema de juego.

---

## 1. Diagrama de Bloques Conceptual

El sistema se divide en tres capas principales que separan la interfaz de usuario de la lógica cognitiva de la Inteligencia Artificial.

```text
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
|  * Orquestador RAG            * Middleware de Seguridad     |
+------------+---------------------------------+--------------+
             |                                 |
             v (SQL Estructurado)              v (Embeddings Semánticos)
+----------------------------+   +----------------------------+
|   BASE DE DATOS RELACIONAL |   |   BASE DE DATOS VECTORIAL  |
|       [ PostgreSQL ]       |   |    [ ChromaDB / Pinecone ] |
|  - Fichas, Usuarios, Flags |   |  - Historial de Chat (Logs)|
|  - IDs de Entidades, Relac.|   |  - Lore e Inyecciones RAG  |
+------------+---------------+   +--------------+-------------+
             |                                 |
             +----------------+----------------+
                              | (Contexto Inyectado + Prompts)
                              v
+-------------------------------------------------------------+
|                       MOTOR COGNITIVO                       |
|           [ OpenAI API (GPT) / Claude API (Anthropic) ]      |
+-------------------------------------------------------------+
