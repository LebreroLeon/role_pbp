# 🚀 RolePBP (Project Chronicler)

> **El primer gestor de rol por turnos (Play-by-Post) asistido por Inteligencia Artificial de alta calidad.**

---

## 📋 ¿Qué es RolePBP y cómo funciona?

**RolePBP** es una aplicación móvil y web diseñada para los amantes del rol que **no tienen tiempo** para quedar 3 o 4 horas fijas a la semana en una mesa física o en Discord. Con RolePBP, la partida va contigo en el bolsillo. Juegas en tus tiempos libres (en el autobús, en el descanso del trabajo o desde el sofá) respondiendo al turno cuando tú puedas.

La magia de la app ocurre gracias a un **asistente de Inteligencia Artificial integrado**, que actúa como el copiloto perfecto de la campaña. Funciona a través de un chat inteligente estructurado de la siguiente manera:

* **El Chat de Juego:** Un chat limpio y especializado en rol donde los jugadores escriben las acciones de sus personajes, lanzan dados virtuales con un comando y el Máster describe qué pasa. Todo queda ordenado cronológicamente.
* **La IA "Cerebro" de la Campaña:** Todo lo que se escribe en el chat se guarda de forma inteligente. La IA lee la partida constantemente, por lo que **recuerda absolutamente todo** lo que ha pasado en la historia, desde el primer día hasta el último.
* **El Panel del Máster (Alimentando el mundo):** Como Director de Juego, tienes un panel privado donde subes las fichas de los personajes, creas los NPCs, defines las misiones ocultas y le dices a la IA qué tono quieres (ej: *"una campaña oscura y peligrosa de ciberpunk"*).
* **El Cierre de Escenas:** Cuando los jugadores terminan una misión o un combate, la IA genera automáticamente un **resumen de la escena** y actualiza el "diario de campaña". Las consecuencias de lo que hagan los jugadores cambian el mundo de forma automática.

---

## 🛠️ ¿Cómo se gestiona el juego a través de la App?

La aplicación divide la experiencia en tres herramientas muy sencillas pero ultrapotentes:

### 1. Para los Jugadores (El Consultor de Lore)
Tienen un chat privado secundario con la IA. Pueden preguntarle cosas como:
* *“Oye, ¿cómo se llamaba el tabernero que nos dio la pista hace dos semanas?”*
* *“¿Qué porcentaje de éxito tengo al disparar si estoy a cubierto según las reglas?”*

La IA les responde al instante basándose **únicamente en lo que su personaje ya sabe**, sin hacer *spoilers*.

### 2. Para el Máster (El "Shadow Master")
El Máster tiene un panel con sugerencias en tiempo real. Mientras los jugadores debaten en el chat qué hacer, la IA le susurra ideas al Máster en privado:
> 💡 *“El jugador X acaba de robar el implante. Recuerda que la corporación Arasaka les está buscando; este sería un buen momento para que aparezca una patrulla en la siguiente esquina. Aquí tienes 3 opciones de cómo introducir la escena”.*

### 3. Gestión de Reglas y Dados
Olvídate de buscar en manuales de 400 páginas. Haces una tirada en el chat, la app calcula los modificadores usando la ficha digital del jugador y la IA le traduce al Máster el resultado narrativo exacto según el reglamento oficial cargado.

---

## 🏆 Ventajas competitivas: ¿Por qué es mejor que la competencia?

Si alguien te dice *"para jugar por turnos ya uso WhatsApp o Discord con un bot de dados"*, aquí es donde **RolePBP** los destroza:

| Característica | WhatsApp / Discord convencional | Herramientas como Kanka / Notion | **RolePBP (Tu App)** |
| :--- | :--- | :--- | :--- |
| **Memoria del juego** | Se pierde en el scroll de miles de mensajes. Nadie recuerda los detalles de hace un mes. | Tienes que escribir las notas a mano de forma aburrida tras cada sesión. | **Total y Automática.** La IA extrae los datos del chat y mantiene la base de datos de lore actualizada por ti. |
| **Consultas en vivo** | Tienes que parar la partida para buscar en el PDF de reglas o preguntar en el grupo. | Es solo una base de datos estática, no interactúa contigo. | **Chat con IA en tiempo real.** Preguntas y te responde integrando las reglas del juego y el contexto de la historia. |
| **Apoyo al Máster** | El Máster sufre el "síndrome de la hoja en blanco" y el estrés de improvisar solo. | No te da ideas, solo almacena lo que tú ya has pensado. | **Copiloto creativo.** Te genera ganchos de escenas, diálogos para NPCs y complicaciones lógicas basadas en tu propio lore. |
| **Estructura de Turnos** | Caótico. La gente habla a la vez, se pisan las acciones o el chat se llena de memes. | No tiene chat propio para jugar de forma nativa. | **Diseñado para PBP.** Notificaciones inteligentes de turno, hilos separados para narrativa, pensamientos y dados. |

> 🎯 **Conclusión para la encuesta / Landing Page:**
> Con este enfoque, lo que se vende no es una app de chat, sino **tiempo, comodidad y una experiencia narrativa de máxima calidad sin esfuerzo**. Le estamos diciendo al rolero: *"Vuelve a jugar a rol con la misma calidad que antes, pero dedicándole solo 5 minutos al día desde tu móvil"*.

---
---

# 📑 Documentación Técnica de Arquitectura

## 👁️ Visión del Proyecto: "The Chronicler"
El objetivo es desarrollar una plataforma de rol tipo Play-by-Post diseñada para grupos que juegan en tiempos libres, donde la experiencia se eleva mediante una IA asistente de alta calidad. La app funcionará como un chat estructurado en turnos que almacena cada interacción en una base de datos de persistencia, permitiendo que la IA actúe como una "memoria total" de la campaña. 

El Máster dispondrá de un panel de control para alimentar a la IA con fichas de personajes, NPCs, arcos argumentales, misiones y el tono narrativo deseado. Esta base de conocimiento servirá como "alimento" para que la IA ofrezca dos servicios clave: una IA de consulta para jugadores (basada en reglas y hechos consumados de la campaña) y una IA de apoyo al Máster (que analiza el historial para sugerir escenas, complicaciones o giros argumentales basados en el lore previo). Al cerrar cada escena, la IA generará automáticamente un resumen estructurado para actualizar el registro histórico, garantizando que el sistema sea coherente, no tenga cabos sueltos y siempre tenga a mano el estado actual de la partida, sin que el Máster tenga que recordar manualmente cada pequeño detalle o conexión entre sucesos.

---

## 🗂️ Índice de Especificaciones de Software

### 1. Visión y Objetivos
* **Propósito:** Definir el alcance (asistente narrativo y gestor de estado para campañas de rol por turnos).
* **Usuarios:** Máster (Editor, Narrador, Gestor) y Jugadores (Participantes).
* **Flujo principal:** El ciclo de vida de una escena (`Creación` -> `Posteo` -> `Resolución` -> `Cierre/Resumen`).

### 2. Arquitectura de Datos (El Núcleo)
* **Estructura de la "Base de Conocimiento" (Lore):**
    * `Entity`: Estructura base para NPCs, Facciones, Lugares e Ítems.
    * `Relationship`: Grafo o mapa de conexiones semánticas entre entidades.
    * `ArcManifest`: Registro de arco argumental, misiones activas e hitos completados.
* **Estructura del Estado de Campaña:**
    * `PlayerCharacter`: Ficha digital indexable, inventario y estado de salud.
    * `SceneState`: Historial del chat log, logs de tiradas de dados y contexto activo de la escena.
    * `WorldLog`: Historial cronológico consolidado de eventos y resúmenes pasados.

### 3. Módulos de IA (Orquestación)
* **Capa de RAG (Retrieval-Augmented Generation):** Estrategia de búsqueda semántica e inyección de contexto relevante en la BD vectorial antes de consultar el LLM.
* **System Prompts:** Definición estricta de prompts de sistema para los tres roles de la IA (El *"Consultor de Reglas"*, el *"Shadow Master"* y el *"Secretario"*).
* **Pipeline de Resumen:** Lógica automatizada al cerrar escenas para la consolidación de datos y re-indexación en el `WorldLog`.

### 4. Flujo de Interacción (User Journeys)
* **Flujo del Máster:** Interfaz de creación de ganchos narrativos, inserción de datos de lore y herramientas de moderación.
* **Flujo de los Jugadores:** Sistema de interacción en el chat de juego, consultas privadas de reglas e interactividad con su ficha.

### 5. Especificaciones Técnicas (Stack sugerido)
* **Capa de Datos:** Base de datos relacional (PostgreSQL) para datos estructurados + pgvector (`campaign_memory`) para embeddings de texto.
* **API / Backend:** Desarrollado en Python utilizando FastAPI.
* **Frontend / Cliente:** Interfaz multiplataforma (React Native / PWA).

### Configuración rápida — OpenAI (opcional)

Copia `.env.example` a `.env` en la raíz del repo. Para RAG, Shadow Master y `@asistente` jugador:

```env
OPENAI_API_KEY=sk-...
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
```

Sin clave, el backend funciona en modo degradado (respuestas stub / sin embeddings). **No commitees `.env`**.

Manuales D&D: copia PDFs a `data/manuals/dnd5e/` (ver `data/manuals/dnd5e/README.md`) e indexa con:

```bash
python backend/scripts/index_system_manuals.py --system dnd5e --dry-run
python backend/scripts/index_system_manuals.py --system dnd5e
```
