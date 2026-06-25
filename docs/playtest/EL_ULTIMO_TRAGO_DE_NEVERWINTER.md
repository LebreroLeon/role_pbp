# El Último Trago de Neverwinter — Pack de playtest RolePBP (v3)

> **Mini-campaña de prueba** · D&D 5e · Faerûn (Costa de la Espada) · 5 escenas async (~15–20 mensajes cada una)  
> **Tono:** western claustrofóbico en Faerûn — salón cerrado, moral gris, diálogo adulto con filo. Referencia atmosférica: *Reservoir Dogs*, *Pulp Fiction*, *The Hateful Eight* (paranoia de salón, no copiar escenas). No es aventura infantil: gente real con sangre en las uñas.

**Premisa en una línea:** Una ventisca cierra el Paso del Cuervo Blanco; diez almas atrapadas en la Posada del Paso Helado descubren que alguien mintió sobre por qué está ahí — y el último trago de la noche no será para todos.

---

## Mapa rápido de campos de la app

| Área de la app                      | Campos que debes rellenar                                                                                            |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Crear campaña / Ajustes**         | `name`, `tone`, `game_system`                                                                                        |
| **Arco narrativo** (`ARC_MANIFEST`) | `plot_line.*`, `active_quests[]`, `state_flags.*`                                                                    |
| **Ubicación** (`LOCATION`)          | `identity.*`, `narrative_profile.*`, `state_flags.*`                                                                 |
| **NPC**                             | `identity.*`, `ai_narrative_profile.*`, `system_mechanics.sheet`, `state_flags.*`                                    |
| **PC**                              | `identity.*`, `public_profile.*`, `system_mechanics.sheet`, `state_flags.*`                                          |
| **Facción** (`FACTION`)             | `identity.*`, `narrative_profile.*`, `state_flags.*`                                                                 |
| **Relación** (`RELATIONSHIP`)       | `connection.*`, `narrative_bond.*`, `ai_behavior_guidelines.*`, `state_flags.*`                                      |
| **Escena preparada** (`PREPARED`)   | `display_name`, `scene_objective`, `location_id`, `opening_narration`, `master_prep_notes`, `prepared_entity_refs[]` |
| **Shadow Master**                   | Modos `narrative` / `rules` / `campaign` + foco en entidad (`focus_entity_id`)                                       |

---

## A. Campaña (wizard + Ajustes)

### Al crear la campaña

| Campo           | Valor copy-paste                 |
| --------------- | -------------------------------- |
| **name**        | `El Último Trago de Neverwinter` |
| **game_system** | `dnd5e`                          |

### Tono narrativo (`tone`) — 🔒 SOLO MÁSTER — no compartir con jugadores

Guía interna para Shadow Master / DM. Pegar en Ajustes de campaña (los jugadores no ven este campo):

```
Western claustrofóbico en Faerûn: una noche, un salón, diez extraños. Ritmo de sala de interrogatorio — diálogo largo, adulto, acusatorio — antes de que la violencia estalle; cuando llegue, íntima y audible (hueso, respiración rota), no coreografía de feria. Humor negro seco entre gente educada que se odia.

Sensorial siempre: cerveza rancia, lana mojada, hierro, tablas que crujen, miradas que tardan un segundo de más. Los PJ descubren inconsistencias jugando; no anuncies el tema ni prediques que «todos mienten».

Casting: arquetipo y raza no marcan culpa. El drow puede ser el más limpio; la «clériga» puede ser farsante; el «paladín» puede ser rata de oro.

Adulto: heridas viscerales, lenguaje soez cuando caen las máscaras, tortura solo si los PJ la provocan (información mezclada, coste moral). La muerte importa. Referencia atmosférica Tarantino-adult (paranoia de salón, traición personal) — sin copiar escenas ni nombres.
```

### Post cinematográfico de apertura — **visible para jugadores** (enviar ANTES de activar Escena 1)

Pegar como primer mensaje del máster en el canal, sin roster activo aún:

```
[CINEMÁTICA — solo lectura]

El Paso del Cuervo Blanco no perdona. La nieve no cae: presiona. Cada copo seco contra la capucha suena a uña.

Neverwinter queda atrás como neón borroso bajo el gris. Delante, la Posada del Paso Helado — dos ventanas amarillas empañadas, humo que no alcanza a tapar el estofado rancio ni el sudor viejo de lana. Un cuervo blanco en el poste del umbral. No grazna. Espera.

Empujáis la puerta. El calor os golpea de golpe; dentro, ocho siluetas ya rodean la chimenea — tiefling con tabardo demasiado blanco, elfa con las manos en el vientre, halfling con mandolina sin tocar, dracónida apretando un maletín con sello. Nadie levanta la vista del fuego de inmediato. En la barra, una mujer de delantal cuenta jarras como fichas.

Fuera, el viento cierra la puerta detrás de vosotros con un clic seco.

Bienvenidos. La tormenta acaba de empezar.
```

### Consultas de ejemplo para Shadow Master (modo `campaign`) — 🔒 SOLO MÁSTER

- «¿Qué sabe el grupo públicamente de Sera Vann al inicio?»
- «Si un PJ inspecciona el sótano sin permiso, ¿qué pista encuentra sin revelar el lore secreto de Grakk?»
- «Resume la tensión entre Thorn y Kaelen si alguien menciona Mere de Tresvelas.»
- «¿Qué miente Yselda sobre el padre del bebé?»
- «Si un PJ tortura a Orin, ¿qué dice de verdad y qué inventa para salvar piel?»
- «¿Por qué el drow aceptó un contrato de muerte sobre Sera si es protector?»
- «¿Quién envenenó el pozo contra Yselda y qué gana si aborta?»

### Ritmo PBP — latido de tensión cada 15–20 minutos reales

| Minuto aprox. | Latido del máster (copy-paste o adaptar) |
| ------------- | ---------------------------------------- |
| 0             | Post cinematográfico + activar Escena 1  |
| 15–20         | «Un trueno sacude los cristales. Alguien en la mesa se lleva la mano al cinturón.» |
| 35–40         | «El fuego cruje. Una jarra se vacía sin que nadie la haya tocado.» |
| 55–60         | «Oís un crujido en el piso de arriba. No es el viento.» |
| 75–80         | «El olor a hierro se hace más fuerte. ¿Sangre nueva o vieja?» |

Ajustar según escena. En Escena 2+, sustituir por gotas de sangre en el techo, gritos amortiguados, etc.

---

## B. Arco narrativo (`ARC_MANIFEST`)

Crear **una sola** entidad de tipo **Arco narrativo** en Mundo.

### `plot_line`

| Campo              | Valor                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **title**          | `El Último Trago`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **global_summary** | `Ventisca en el Paso del Cuervo Blanco. Diez máscaras en la Posada del Paso Helado y un cofre de la Alianza que no contiene oro sino plaga sellada, mapas de armas de la Guerra de la Corona y cartas que podrían incendiar Neverwinter. Un drow con capa de ceniza que parece asesino a sueldo pero vino a blindar un nombre muerto. Una «hermana de Ilmater» que en realidad aprendió venenos en Calimport y usa el símbolo como camuflaje — y aun así está salvando a alguien esta noche. Un tiefling con tabardo robado que todos llaman «paladín» y que cuenta monedas como quien cuenta pecados. Un medio-orco con cuchillo de cocina que parece el lobo de la historia pero no ha matado a nadie en diez años — la posadera humana sí enterró tres hombres en una avalancha «accidental». Sangre en el techo, un mozo estrangulado, pólvora sobre la mesa. Nadie sale hasta que amaine la tormenta o hasta el último trago. Paranoia como motor; cada acusación es mitad verdad y mitad veneno.` |
| **current_act**    | `1` (subir en cada escena hasta `5`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **narrative_tone** | `Suspenso íntimo, diálogo afilado, moral podrida, traición personal, violencia visceral contenida hasta que estalla`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |

### `active_quests` (5 misiones — una por escena)

**Misión 1 — Refugio en el paso**

| Campo               | Valor                                                                                                                                                                                                                             |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **title**           | `Refugio en el paso`                                                                                                                                                                                                              |
| **description**     | `La tormenta cierra el paso. Diez caras, diez historias incompletas. Presentarse es obligatorio; confiar es opcional y probablemente estúpido.` |
| **secret_dm_notes** | `Orin ya vio el sello de Sera y calcula el precio del chantaje. Grakk avisará a Zhentarim si alguien abre el sótano sin pagar. Huldra reconoce el anillo de tres cuervos de Orin — anzuelo PC Hook 1. El Viajero (drow) observa desde arriba: NO revelar raza ni misión hasta Escena 2 salvo Percepción CD 17. Maelis miente sobre el cuervo blanco del umbral («solo decoración»). Sembrar: cofre, vendajes de Kaelen, moretón de Yselda, tabardo de Thorn demasiado limpio.` |

**Misión 2 — La gota en el techo**

| Campo               | Valor                                                                                                                                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **title**           | `La gota en el techo`                                                                                                                                                                                                                      |
| **description**     | `Sangre fresca gotea del piso superior. Nadie admite haber subido. Las teorías empiezan antes que los cadáveres.` |
| **secret_dm_notes** | `Fuente: herida reabierta de Kaelen (Thorn le clavó un cuchillo hace dos días) O cadáver de Edrin arriba si adelantas. Grakk sabía del hueco entre vigas — no es su sangre. Yselda vio a Thorn salir del pasillo con guantes de cuero; miente que dormía. Calistra subió a cambiar vendajes a Kaelen y vio al Viajero — no dice nada porque cree que es el asesino a sueldo que vino por Sera. Revelar Viajero (drow) si suben o fallan 2 Investigaciones.` |

**Misión 3 — Sangre en el umbral**

| Campo               | Valor                                                                                                                                                                                                                                      |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **title**           | `Sangre en el umbral`                                                                                                                                                                                                                      |
| **description**     | `Un grito en el establo. Edrin el Mozo, estrangulado. Cada huésped tiene un alibi roto y un motivo que no pidió.` |
| **secret_dm_notes** | `Asesino real: Grakk (garrote fino, Zhentarim silencia testigo). Pista falsa: huella de mano medio-orco en heno — es de Grakk SIN guante, plantada después por Thorn al revolver el cuerpo buscando a Kaelen. Thorn NO mató a Edrin pero estuvo en el establo y miente el horario. Calistra confesó eutanasias a Edrin — parece confesión de asesinato. Sister Calistra NO mató al mozo. Sótano: CD 12 cerradura / CD 14 fuerza.` |

**Misión 4 — El precio del cofre**

| Campo               | Valor                                                                                                                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **title**           | `El precio del cofre`                                                                                                                                                                                      |
| **description**     | `El cofre atrae miradas como un cadáver a moscas. El sótano respira. Las ofertas son veneno envuelto en lógica.` |
| **secret_dm_notes** | `Contenido: vial plaga + mapas Guerra Corona + cartas chantaje (un oficial es padre del bebé de Yselda). Abrir sin precaución: CD 14 CON. Huldra quiere mapas para vender a Luskan Y a Zhentarim — dos compradores, una traición. Sera quiere cumplir misión aunque la Alianza la desaparezca si falla. Viajero quiere destruir vial, no el cofre entero. Grakk vendió lista de huéspedes anoche. Tentación: ver sección J.` |

**Misión 5 — El último trago**

| Campo               | Valor                                                                                                                                                                                                      |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **title**           | `El último trago`                                                                                                                                                                                          |
| **description**     | `Un trago por persona. Después, la verdad o la bala. Standoff en la sala común: todos apuntan a todos.` |
| **secret_dm_notes** | `Post único standoff (sección K). Viajero puede revelar que aceptó contrato para «matar» a Sera y en realidad es escolta del legado de su padre Harper. Maelis confiesa avalancha de hace diez años si alguien la acusa de cobarde. Finales: (A) Alianza + vial destruido, (B) Zhentarim con mapas, (C) fuga túnel, (D) masacre, (E) tregua Harper con confesiones parciales. Nadie sale limpio.` |

### `state_flags`

| Campo                     | Valor inicial                                                 |
| ------------------------- | ------------------------------------------------------------- |
| **is_main_plot_derailed** | `false`                                                       |
| **world_threat_level**    | `4` (subir +1 cada escena; `9` en standoff final)             |

---

## C. 5 Escenas preparadas

Crear 5 escenas con estado **PREPARED**. Tras crear cada una, abrir el editor de preparación y pegar los campos.

> **Nota:** Los `entity_id` y `location_id` son UUIDs reales de tu campaña. Sustituye `[UUID_…]` tras crear las entidades en Mundo.

### Mapa de zonas (3 plantas + sótano)

| Zona | ID sugerido | Uso en escenas |
| ---- | ----------- | -------------- |
| **Sala común y barra** | `[UUID_SALA_COMUN]` | Presentaciones, standoff final |
| **Cocina y despensa** | `[UUID_COCINA]` | Grakk, Huldra, pistas Zhentarim |
| **Pisos superiores (habitaciones)** | `[UUID_PISOS_SUPERIORES]` | Viajero, gotas de sangre, Yselda |
| **Establo anexo** | `[UUID_ESTABLO]` | Muerte Edrin, huellas |
| **Sótano y túnel** | `[UUID_SOTANO]` | Contrabando, veneno, escape |

---

### Escena 1 — «Ventisca y presentaciones»

| Campo prep          | Valor                                                                                                                                                                                                                                                    |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **status**          | `PREPARED`                                                                                                                                                                                                                                               |
| **display_name**    | `Ventisca y presentaciones`                                                                                                                                                                                                                              |
| **location_id**     | `[UUID_POSADA_DEL_PASO_HELADO]`                                                                                                                                                                                                                          |
| **scene_objective** | `Presentar a todos los huéspedes, establecer desconfianza cordial, sembrar 3 pistas visibles (cofre sellado, mercenario herido, refugiada embarazada) y cerrar con la tormenta cortando toda salida.` |

**opening_narration**:

```
El viento golpea la Posada del Paso Helado como si quisiera entrar sin pagar. Nieve pegada a las ventanas, humo de hogar barato, el crujido de tablones que han visto demasiadas noches malas. En el umbral, el frío os muerde la espalda; dentro, el calor huele a estofado, cerveza rancia y algo metálico — sangre vieja en las grietas del suelo, sin duda.

Maelis Verdecuervo, la posadera, no sonríe del todo: «Quedan tres habitaciones. Diez bocas. La tormenta no pregunta si tenéis prisa.» En la sala común, siluetas ya calientan las manos alrededor del fuego. Una elfa joven se lleva las manos al vientre. Un tiefling con tabardo blanco demasiado limpio aprieta una ballesta baja. Un halfling afina una mandolina sin tocarla. Una dracónida aprieta un maletín con sello rojo. Nadie se ha presentado aún. Fuera, algo grazna. Los cuervos del paso nunca duermen.
```

**master_prep_notes**:

```
- Pista 1: Sera Vann aprieta maletín con sello Alianza (Investigación CD 12).
- Pista 2: Kaelen Ruin tiene vendajes frescos bajo la capa (Medicina CD 11).
- Pista 3: Yselda Cuervonegro evita que le toquen el hombro izquierdo — moretón oculto (Percepción CD 13).
- Orin ofrece música a cambio de secretos.
- Grakk en cocina: Percepción CD 14 oye susurro en dialecto zhent.
- Huldra pregunta quién lleva anillo de tres cuervos — anzuelo Hook 1.
- Viajero en piso superior — visibility hidden.
- Cerrar: presentaciones + 1 pista + tormenta bloquea salida (~15–20 msgs).
```

**prepared_entity_refs**:

| Entidad              | player_visibility | add_to_roster |
| -------------------- | ----------------- | ------------- |
| Todos los PCs        | `visible`         | `true`        |
| Maelis Verdecuervo   | `visible`         | `true`        |
| Orin Tres Dedos      | `visible`         | `true`        |
| Sera Vann            | `visible`         | `true`        |
| Thorn Blackmantle    | `visible`         | `true`        |
| Sister Calistra      | `visible`         | `true`        |
| Grakk Ironsnout      | `visible`         | `true`        |
| Kaelen Ruin          | `visible`         | `true`        |
| Huldra Voss          | `visible`         | `true`        |
| Yselda Cuervonegro   | `visible`         | `true`        |
| El Viajero de Ceniza | `hidden`          | `false`       |
| Edrin el Mozo        | `unknown`         | `true`        |

**Beats:** llegada → post cinematográfico (si no enviado) → presentaciones forzadas → Huldra/Orin roce → oferta Maelis → trueno bloquea puerta.

**Cuándo cerrar:** Salida bloqueada + al menos un intercambio hostil + un PJ eligió a quién vigilar.

---

### Escena 2 — «La gota en el techo»

| Campo prep          | Valor                                                                                                                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **status**          | `PREPARED`                                                                                                                                                                                                    |
| **display_name**    | `La gota en el techo`                                                                                                                                                                                         |
| **location_id**     | `[UUID_SALA_COMUN]`                                                                                                                                                                                           |
| **scene_objective** | `Provocar descubrimiento de sangre goteando del piso superior; paranoia sin cadáver visible aún; forzar movimiento entre zonas.` |

**opening_narration**:

```
La tormenta no afloja. Bebéis porque no hay otra cosa que hacer. Entonces — un golpe sordo arriba. No es el viento.

Una gota roja cae del techo de vigas y estalla en la mesa de roble como una baya podrida. Luego otra. Y otra. El olor a hierro llena la sala más rápido que el miedo.

Nadie ha bajado las escaleras. Nadie ha gritado. Pero algo arriba acaba de empezar a sangrar — o ya lleva un rato haciéndolo.
```

**master_prep_notes**:

```
- Fuente sangre: herida Kaelen (se desangra en habitación) O Edrin muerto arriba (si adelantas).
- Grakk sabía del hueco entre vigas — Percepción CD 15 en cocina encuentra sierra con pelo.
- Yselda vio sombra en escalera; miente que estaba dormida (Insight CD 14).
- Revelar Viajero si suben o fallan 2 Investigaciones.
- Latido 15–20 min: «Las gotas se aceleran. Alguien en la barra deja caer su jarra.»
- Cerrar: grupo sube O acusa a alguien abajo + mención del cofre.
```

**Beats:** gotas → pánico contenido → subir escaleras / acusaciones → pista techo hueco → Calistra ofrece curar «al herido».

**Cuándo cerrar:** Teoría formulada + al menos 2 PNJs en actitud `hostile` o `cautelosa` hacia otro.

---

### Escena 3 — «Máscaras y sangre»

| Campo prep          | Valor                                                                                                                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **status**          | `PREPARED`                                                                                                                                                                                                    |
| **display_name**    | `Máscaras y sangre`                                                                                                                                                                                           |
| **location_id**     | `[UUID_ESTABLO]`                                                                                                                                                                                              |
| **scene_objective** | `Muerte de Edrin (o confirmación cadáver), investigación social y física, revelar 2–3 secretos parciales, abrir debate sobre sótano.` |

**opening_narration**:

```
La noche no perdona. Una hora después del incidente del techo, un grito corto — demasiado corto — viene del establo anexo. El olor a heno mojado ya no disimula el hierro.

La puerta lateral está entreabierta. Huellas de bota mezcladas con sangre fresca sobre la nieve que entró en ráfagas. En el suelo, Edrin el Mozo. Cuello marcado. Ojos abiertos como quien vio venir su nombre.

En la sala común, los que no movieron un dedo empiezan, por fin, a hablar demasiado.
```

**master_prep_notes**:

```
- Edrin estrangulado. Huella de mano medio-orco (falsa pista) + cuerda fina (asesino real: Grakk o cómplice).
- Thorn acusa Kaelen si suena Mere de Tresvelas.
- Calistra rompe: confesó a Edrin antes — no que lo mató.
- Sótano: cerradura CD 12 / fuerza CD 14.
- Huldra ofrece pólvora «para defenderse» — tentación.
- Cerrar: teoría asesino + cofre mencionado + 1 RELATIONSHIP revelada en juego.
```

**Beats:** cadáver → acusaciones → interrogatorio → pista sótano → confesión parcial Calistra u Orin.

**Cuándo cerrar:** Grupo tiene culpable (aunque erróneo) + tensión ≥ 7.

---

### Escena 4 — «El precio del cofre»

| Campo prep          | Valor                                                                                                                                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **status**          | `PREPARED`                                                                                                                                                       |
| **display_name**    | `El precio del cofre`                                                                                                                                            |
| **location_id**     | `[UUID_SOTANO]` o sala si no bajan                                                                                                                               |
| **scene_objective** | `Centrar conflicto en el cofre; revelar contenido parcial o total; túnel de contrabando; traiciones activas.` |

**opening_narration**:

```
El cielo aclara un poco en el Paso del Cuervo Blanco: la ventisca afloja, pero el frío no suelta. El lacre del cofre de Sera Vann tiene una huella de dedo que no es suya — fresca, grasa de cocina, o eso parece.

En la cocina, Grakk ya no sonríe. En el sótano, una puerta que nadie admitió conocer respira aire frío de túnel. Y en la mesa, Huldra deja un saquito de pólvora negra como un ultimátum silencioso.

«Alguien va a abrir eso», dice Maelis sin levantar la voz. «La pregunta es quién paga el precio.»
```

**master_prep_notes**:

```
- Abrir cofre: cerradura CD 18 / fuerza CD 20. Sin precaución: vial plaga — CD 14 CON.
- Contenido: vial plaga + mapas armas Guerra Corona + cartas chantaje Neverwinter.
- Grakk vendió lista huéspedes. Thorn solo quiere Kaelen. Huldra quiere mapas para revender.
- Viajero ofrece mediación Harper si grupo demostró honor.
- Torturar NPC: ver tabla tentaciones sección J.
- Cerrar: cofre abierto O destruido O robado + alguien traiciona explícitamente.
```

**Beats:** ultimátum cofre → bajada sótano → revelación contenido → ofertas cruzadas → traición visible.

**Cuándo cerrar:** Destino del cofre decidido (no necesariamente final) + `world_threat_level` ≥ 8.

---

### Escena 5 — «El último trago»

| Campo prep          | Valor                                                                                                                                                            |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **status**          | `PREPARED`                                                                                                                                                       |
| **display_name**    | `El último trago`                                                                                                                                                |
| **location_id**     | `[UUID_SALA_COMUN]`                                                                                                                                              |
| **scene_objective** | `Standoff mexicano en un solo post; resolver traiciones; epílogo brutal o amargo.` |

**opening_narration**:

```
La tormenta cede lo justo para oírse los corazones. Maelis deja una botella sin etiqueta en el centro de la mesa — la misma que su abuelo guardaba para «el día que alguien diga la verdad entera».

«Un trago por persona», dice. «Y después…»

No termina la frase. No hace falta. Thorn el tiefling tiene la ballesta baja pero lista — tabardo de Torm manchado de nieve, no de sangre aún. Grakk el cuchillo de cocina. Sera el cofre — o lo que queda. Kaelen la espada temblorosa. Huldra un mechero cerca del barril de cerveza. Yselda entre la puerta y la ventana, una mano en el vientre, otra en un cuchillo de mesa que nadie le vio coger. En el piso de arriba, el drow de la capa ceniza baja por primera vez.

Fuera, el cuervo blanco. Dentro, diez historias que no caben en una noche.

**[MÁSTER: activar post de standoff mexicano — sección K. Un solo mensaje. Fin de campaña.]**
```

**master_prep_notes**:

```
- NO prolongar tras standoff. Un post, una ronda de respuestas si aplica, resolución.
- Finales: (A) Alianza se lleva cofre, (B) destrucción vial, (C) fuga túnel, (D) masacre, (E) tregua Harper.
- Combate opcional: Thorn + Grakk nivel 2–3 vs grupo.
- Epílogo: 1 línea por PJ vivo. Edrin enterrado o no según grupo.
- ARC: current_act=5, derailed según resultado.
```

**Beats:** botella → standoff post → respuestas PJs → resolución violenta o negociada → epílogo.

**Cuándo cerrar:** Inmediatamente tras resolución del standoff. Congelar RAG.

---

## D. Ubicaciones (`LOCATION`)

### 1. Posada del Paso Helado (edificio padre)

```yaml
identity:
  name: "Posada del Paso Helado"
  location_type: "posada de montaña"
  parent_location_id: null

narrative_profile:
  public_description: |
    Posada de piedra y madera oscura en el Paso del Cuervo Blanco, a medio día de Neverwinter por senderos que en invierno son una sentencia. Tres plantas: sala común y barra en planta baja, cocina y despensa al fondo, ocho habitaciones en pisos superiores, establo anexo lateral. Maelis Verdecuervo la regenta con mano firme y pocas preguntas — si pagas antes de beber.
  secret_lore_master: |
    Sótano comunica con túnel de contrabando usado por Los Cuervos de Mirtul. Maelis fue exploradora Harper; el cuervo blanco del umbral es señal de contacto. Bajo la tercera tabla del suelo hay nicho con botella de veneno de sombra (1 dosis, CD 13 CON o 2d6 veneno). Entre vigas del techo hay hueco usado para espiar la sala — Grakk lo usó.
  ambient_tone: "Calor falso, tablones que crujen, silencios largos, olor a lana mojada, cerveza rancia y hierro"
  notable_features:
    - "Chimenea de piedra negra"
    - "Barra con botellas sin etiqueta"
    - "Reloj de arena roto sobre la repisa"
    - "Vigas con hueco de espionaje"
    - "Establo anexo con puerta lateral"
    - "Trampilla al sótano tras la barra"

state_flags:
  is_accessible_to_party: true
  danger_level: 5
  is_destroyed: false
```

**Prompt ilustración:** `Fantasy tavern interior, snowstorm outside windows, warm firelight, gritty realistic style, claustrophobic mountain inn, blood stain on ceiling beam, Faerûn Sword Coast, muted colors, cinematic composition, no text`

---

### 2. Sala común y barra (zona 1)

```yaml
identity:
  name: "Sala común de la Posada del Paso Helado"
  location_type: "sala interior"
  parent_location_id: "[UUID_POSADA_DEL_PASO_HELADO]"

narrative_profile:
  public_description: "Mesa larga de roble, ocho sillas, chimenea, barra con grifos que gotean. Centro de toda mentira y verdad de la noche."
  secret_lore_master: "Tercera tabla del suelo levantable (Investigación CD 15). Veneno de sombra en nicho. Escena del standoff final."
  ambient_tone: "Calor seco, crujido de fuego, voces bajas, tensión visible"
  notable_features: ["Mesa central", "Botella sin etiqueta de Maelis", "Reloj de arena roto"]

state_flags:
  is_accessible_to_party: true
  danger_level: 6
  is_destroyed: false
```

---

### 3. Cocina y despensa (zona 2)

```yaml
identity:
  name: "Cocina de la Posada del Paso Helado"
  location_type: "cocina"
  parent_location_id: "[UUID_POSADA_DEL_PASO_HELADO]"

narrative_profile:
  public_description: "Cocina estrecha, ollas colgadas, olor a estofado y grasa. Grakk reina aquí con cuchillo siempre cerca."
  secret_lore_master: "Lista de huéspedes vendida escondida en harina (Investigación CD 13). Señal zhentarim bajo delantal de Grakk. Puerta a sótano con cerradura oxidada."
  ambient_tone: "Vapor, metal, susurros, cuchillos"
  notable_features: ["Fogón de piedra", "Saco de harina con papeles", "Puerta al sótano"]

state_flags:
  is_accessible_to_party: true
  danger_level: 5
  is_destroyed: false
```

---

### 4. Pisos superiores — habitaciones (zona 3)

```yaml
identity:
  name: "Pisos superiores de la Posada del Paso Helado"
  location_type: "habitaciones"
  parent_location_id: "[UUID_POSADA_DEL_PASO_HELADO]"

narrative_profile:
  public_description: "Pasillo estrecho, ocho puertas, alfombra gastada que no amortigua pasos. Habitación del Viajero siempre con cerrojo."
  secret_lore_master: "Sangre de Kaelen o cadáver Edrin según escena. Yselda comparte habitación con mentira de viuda. Hueco en suelo de habitación 4 comunica con vigas de sala."
  ambient_tone: "Crujidos, pasos amortiguados, puertas que no cierran bien"
  notable_features: ["Habitación 4 con tabla suelta", "Cerrojo del Viajero", "Ventana con hielo en cristal"]

state_flags:
  is_accessible_to_party: true
  danger_level: 7
  is_destroyed: false
```

---

### 5. Sótano y túnel (zona 4)

```yaml
identity:
  name: "Sótano de la Posada del Paso Helado"
  location_type: "sótano"
  parent_location_id: "[UUID_POSADA_DEL_PASO_HELADO]"

narrative_profile:
  public_description: "Escaleras húmedas, olor a tierra y moho. Los huéspedes no deberían estar aquí."
  secret_lore_master: "Túnel a Paso del Cuervo Blanco usado por Cuervos de Mirtul. Caja con contrabando menor. Salida de emergencia si tormenta cesa."
  ambient_tone: "Frío, oscuro, goteo de agua, claustrofobia"
  notable_features: ["Túnel de contrabando", "Cadenas oxidadas", "Marcas de botas recientes"]

state_flags:
  is_accessible_to_party: false   # hasta Escena 4 salvo intrusión
  danger_level: 8
  is_destroyed: false
```

---

### 6. Paso del Cuervo Blanco (región)

```yaml
identity:
  name: "Paso del Cuervo Blanco"
  location_type: "paso de montaña"
  parent_location_id: null

narrative_profile:
  public_description: |
    Paso alto entre Neverwinter y los valles interiores. En verano, caravanas; en invierno, solo locos y desesperados. Los cuervos anidan en los peñascos; los lugareños dicen que anuncian muertes que aún no ocurrieron.
  secret_lore_master: |
    Durante la Guerra de la Corona, aquí se enterró un convoy de la Alianza bajo avalancha provocada. El cofre de Sera contiene mapas para recuperar esas armas — y muestras de plaga usada como arma en ese conflicto.
  ambient_tone: "Viento cortante, graznidos lejanos, blanco absoluto, aislamiento"
  notable_features:
    - "Senda estrecha con cornisa"
    - "Peñasco del Cuervo Blanco"
    - "Boca del túnel bajo posada"

state_flags:
  is_accessible_to_party: false
  danger_level: 8
  is_destroyed: false
```

---

### 7. Establo anexo

```yaml
identity:
  name: "Establo anexo de la Posada del Paso Helado"
  location_type: "establo"
  parent_location_id: "[UUID_POSADA_DEL_PASO_HELADO]"

narrative_profile:
  public_description: "Establo pequeño con cuatro pesebres, heno húmedo y olor a bestia. Puerta lateral da al exterior — inútil mientras la ventisca sople."
  secret_lore_master: "Bajo el pesebre tercero, trampilla a túnel (misma red del sótano). Edrin sabía y calló por miedo. Escena del cadáver."
  ambient_tone: "Oscuro, húmedo, crujidos, miedo animal"
  notable_features: ["Pesebres vacíos", "Huellas de sangre", "Farol apagado", "Cuerda fina en rincón"]

state_flags:
  is_accessible_to_party: true
  danger_level: 7
  is_destroyed: false
```

---

## E. NPCs (10 + 1 menor)

Para cada NPC: **raza D&D**, máscara pública vs verdad secreta, peculiaridad sensorial, motivo privado, mentira sostenida, culpa aparente vs real (ver tabla maestra sección I), **5+ líneas de diálogo** copy-paste, `secret_lore_master` en prosa completa. Ficha 5e ligera (nivel 1–3).

### Tabla rápida — razas y culpabilidad

| NPC | Raza | Parece culpable de… | Culpabilidad real (0–10) |
| --- | ---- | ------------------- | ------------------------ |
| Maelis Verdecuervo | Humana | Avalancha / encubrir asesinato | **6** (tres muertos hace 10 años; ninguno esta noche) |
| Orin «Tres Dedos» Keth | Mediano (halfling) | Chantaje / vender a Sera | **5** (cobarde, no asesino) |
| Sera Vann | Dracónida | Traición Alianza / abrir plaga | **4** (misión legal, contenido ilegal) |
| Thorn Blackmantle | Tiefling | Asesinato Edrin / «paladín» falso | **7** (revolvió cadáver; no estranguló) |
| Sister Calistra | Humana (Calimport) | Envenenar / matar Edrin | **5** (12 eutanasias pasadas; no mató al mozo) |
| Grakk Ironsnout | Medio-orco | Estrangulamiento (correcto) | **9** (asesino del mozo + espía) |
| Kaelen Ruin | Humano | Sangre del techo / Mere | **7** (encubrió muertes civiles) |
| El Viajero de Ceniza | Drow | Contrato de muerte sobre Sera | **2** (menos culpable; protector encubierto) |
| Huldra Voss | Enana | Vender explosivos / cómplice | **6** (suministró garrote «para minería») |
| Yselda Cuervonegro | Elfa del bosque | Espía / padre corrupto | **3** (mentira de identidad, embarazo real) |
| Edrin el Mozo | Humano | Espionaje (menor) | **2** (víctima) |

---

### 1. Maelis Verdecuervo — Posadera

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Maelis Verdecuervo` |
| **identity.race** | `Humana` |
| **identity.concept** | `Posadera de mirada cansada; controla la sala como quien conoce cada grieta y cada hueso bajo los cimientos` |
| **identity.faction_id** | `[UUID_CUERVOS_MIRTUL]` |
| **identity.current_location_id** | `[UUID_POSADA]` |
| **máscara_pública** | `Viuda honesta de un paso maldito. Regenta la posada con mano firme, pocas preguntas, tarifa por adelantado.` |
| **verdad_secreta** | `Ex-Harper. Hace diez años provocó una avalancha en el paso para enterrar un convoy zhentarim — tres hombres murieron; fue «accidente» firmado por la célula. Desde entonces no ha matado a nadie, pero sabe dónde está el veneno bajo la tercera tabla y coordinó con el Viajero la recepción del cofre.` |
| **peculiaridad** | `Frota el pulgar contra el delantal cuando miente — ritmo lento, como amasar. Nunca levanta la voz; baja el volumen.` |
| **personality_traits** | `Calculadora, protectora, seca, observadora, moralmente ambigua` |
| **voice_and_tone** | `Frases cortas. Trata a todos de «viajero» hasta que demuestran lo contrario. El silencio es su amenaza.` |
| **public_description** | `Humana de unos cuarenta años, cabello castaño con hebras plateadas, delantal de cuero manchado. Mueve jarras como piezas de tablero.` |
| **secret_lore_master** | `Maelis Verdecuervo no es la bruja del paso que susurran los mercaderes: es peor y mejor a la vez. Entró en los Harpers tras ver quemar su aldea natal en la Guerra de la Corona; durante años usó la Posada del Paso Helado como nodo de contrabando «benigno» — medicinas, prisioneros políticos, mensajes. La avalancha del invierno de hace diez años no fue improvisación: un convoy zhentarim transportaba un vial de plaga menor robado a la Alianza. Maelis desencadenó la nieve con un artefacto Harper enterrado bajo el Peñasco del Cuervo Blanco. Tres zhents murieron; ella firmó el informe como «desprendimiento natural» y no durmió bien durante un año — luego durmió perfectamente, lo cual la aterroriza. El cuervo blanco del umbral es señal de contacto, no superstición. Conoce el veneno de sombra bajo la tercera tabla del suelo (1 dosis). Esta noche esperaba al Viajero y a Sera para cerrar el tránsito del cofre; la tormenta arruinó el calendario. No mató a Edrin. No protegerá a Grakk si el grupo lo descubre — pero tampoco entregará el túnel a la Alianza sin algo a cambio.` |
| **motivo_privado_posada** | `Operación de tránsito acordada con Harper y Sera; la tormenta la convierte en carcelera involuntaria.` |
| **mentira_que_sostiene** | `«Solo regento una posada honesta en un paso maldito.» Niega Harper, contrabando y el significado del cuervo blanco.` |
| **parece_culpable_de** | `Encubrir al asesino; saber del túnel; «demasiada calma»` |
| **attitude_towards_party** | `cautelosa` |
| **player_visibility** | `visible` |
| **compendium_tier** | `story` |

**Líneas de diálogo (copy-paste):**

- «La tormenta no pregunta si tenéis prisa. Yo tampoco.»
- «He visto morir a gente con menos motivo que vosotros. No me miréis así — no fue esta noche.»
- «El cuervo blanco es decoración. Si creéis en presagios, pagáis doble y dormís con un ojo abierto.»
- «No abrís el sótano porque sí. Abriréis el sótano porque no os queda otra — y entonces negociamos.»
- «Confiar es gratis. Equivocarse cuesta habitación y entierro.»
- «Mi marido murió en esta cama. El que la manchó después pagó en monedas, no en disculpas.»

**Ficha (nivel 2):** Guardia urbana reskin — AC 14, HP 22, espada corta +3 (1d6+1), Persuasión +4, Insight +3.

---

### 2. Orin «Tres Dedos» Keth — Bardo y jugador

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Orin «Tres Dedos» Keth` |
| **identity.race** | `Mediano (halfling)` |
| **identity.concept** | `Halfling bardo que perdió dos dedos por una deuda de dados — sonríe como quien ya vendió tu secreto` |
| **máscara_pública** | `Trovador de paso camino a ferias de Luskan. Encantador, inofensivo, siempre cerca del fuego.` |
| **verdad_secreta** | `Debe quinientas piezas de oro a Los Cuervos de Mirtul. Vio el sello de Sera y calculó chantaje. Puede delatar a Kaelen a Thorn a cambio de impunidad — no porque sea malo, sino porque el miedo le come antes que la culpa.` |
| **peculiaridad** | `Tararea una escala menor antes de cada mentira. El anillo de plata en el meñique que le falta tintinea contra la mandolina.` |
| **personality_traits** | `Encantador, chismoso, cobarde bajo presión, irónico` |
| **voice_and_tone** | `Ríe antes de hablar en serio. Metáforas de cartas y dados. Insulta con sonrisa.` |
| **public_description** | `Halfling delgado, mandolina remendada, anillo de plata en el dedo fantasma. Ojos demasiado rápidos.` |
| **secret_lore_master** | `Orin no es un villano de opereta: es un mediocre con deudas excelentes. Perdió los dedos en un juego trucado en el Puerto de Luskan — los Cuervos de Mirtul financiaron su recuperación a cambio de información. Lleva dos años vendiendo nombres a cambio de prórrogas. En Neverwinter reconoció el sello de la Alianza en el maletín de Sera y planeó un chantaje que aún no ha tenido valor para cobrar. Cree que Huldra vino por él (acierta) y que el tiefling de la capa negra es un demonio con ballesta (error a medias). Vio a Edrin espiando para Grakk y no dijo nada: le debía al mozo una copa de vino y pensó que no era asunto suyo. Esa omisión lo perseguirá si sobrevive la noche. No mató a nadie; sí puede matar una reputación con media frase.` |
| **motivo_privado_posada** | `Huye de cobradores; la tormenta lo encerró con Huldra, su pesadilla con pipa.` |
| **mentira_que_sostiene** | `«Solo paso rumbo a Luskan a tocar en ferias.» Oculta deuda y anillo de tres cuervos.` |
| **parece_culpable_de** | `Vender secretos; provocar a Thorn; robar el cofre «por desesperación»` |
| **attitude_towards_party** | `amistosa` |
| **compendium_tier** | `story` |

**Líneas de diálogo:**

- «Dos dedos me costó aprender que la casa siempre gana — salvo cuando alguien en la mesa lleva ballesta.»
- «No digo que confiéis en mí. Digo que me paguéis por no decir lo que sé. Es más barato.»
- «La clériga reza mucho para alguien que huele a almizcle de Calimport y no a incienso.»
- «Si el medio-orco te sonríe mientras corta cebolla, revisa dónde tenías los dedos.»
- «Yo no mato. Yo… recomiendo a quién no invitar al día siguiente.»
- «¿Chantaje? Qué palabra tan fea. Yo lo llamo «interés compuesto».»

**Ficha (nivel 1):** Bardo — AC 12, HP 9, Vicious mockery, espada corta 1d6.

---

### 3. Sera Vann — Mensajera de la Alianza

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Sera Vann` |
| **identity.race** | `Dracónida (bronze, escamas apagadas)` |
| **identity.concept** | `Mensajera de la Alianza con cofre que pesa más que el hierro y una conciencia que cruje en cada junta` |
| **identity.faction_id** | `[UUID_ALIANZA_LORDES]` |
| **máscara_pública** | `Oficial de rutas clasificadas. Formal, nerviosa, «por orden de la Alianza».` |
| **verdad_secreta** | `Transporta plaga sellada, mapas de armas enterradas y cartas de chantaje sobre tres oficiales de Neverwinter — uno es padre del hijo de Yselda. Si falla, la Alianza la desaparece; si triunfa, sigue siendo cómplice de horrores legales.` |
| **peculiaridad** | `Se muerde el interior de la mejilla hasta sangrar cuando miente. Las escamas junto al cuello cambian de tono con el estrés — bronce a gris plomo.` |
| **personality_traits** | `Rígida, nerviosa, honorable en apariencia, territorial` |
| **voice_and_tone** | `Lenguaje formal que se quiebra. «Por orden de la Alianza» como escudo roto.` |
| **public_description** | `Dracónida de treinta años aparentes, capa azul con broche de Lord, maletín de hierro con lacre rojo.` |
| **secret_lore_master** | `Sera Vann no es una fanática de la Alianza: es una superviviente que firmó un contrato con el diablo porque el diablo tenía raciones. Huérfana de la Guerra de la Corona, fue reclutada joven como mensajera de campo — eficiente, discreta, reemplazable. El cofre que porta no contiene oro: contiene un vial de plaga sellada de ese conflicto (muestra para «investigación»), mapas para recuperar arsenales enterrados bajo el Paso del Cuervo Blanco, y cartas que demuestran que tres oficiales de Neverwinter vendieron posiciones a Zhentarim. Una de esas cartas nombra al capitán Halvek Crownsplitter — padre biológico del bebé de Yselda, aunque Sera no lo sabe con certeza hasta que abran el cofre. La ruta por el paso evitaba checkpoints zhentarim en la Costa; Maelis era punto de relevo. Sera desconfía del drow del piso superior porque todo mensajero desconfía de un drow en la sombra — ironía cruel, porque él es la única escolta real que tiene sin saberlo.` |
| **motivo_privado_posada** | `Relevo acordado con Maelis; tormenta convirtió misión en pesadilla.` |
| **mentira_que_sostiene** | `«Solo documentos de rutas comerciales.» Nunca admite plaga ni chantaje.` |
| **parece_culpable_de** | `Traición; traer la plaga; «sabía que alguien moriría»` |
| **attitude_towards_party** | `neutral` |
| **compendium_tier** | `story` |

**Líneas de diálogo:**

- «Por orden de la Alianza — y antes de que preguntéis, no, no vais a ver el contenido.»
- «Lleváis tres preguntas de más en la cara. La cuarta os va a costar un diente.»
- «No soy vuestro enemigo. Vuestro enemigo es quien creéis que soy.»
- «Si abrís esto sin precaución, no moriréis heroicos. Moriréis feos y lentos.»
- «El drow de arriba me mira como quien cuenta monedas sobre mi tumba. Preferiría que tuviera razón — al menos sería simple.»
- «La Alianza no perdona el fracaso. Tampoco perdona el éxito si alguien habla demasiado.»

**Ficha (nivel 2):** Veterana — AC 16, HP 20, espada larga +4, Persuasión +3.

---

### 4. Thorn Blackmantle — «Paladín» de pacotilla

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Thorn Blackmantle` |
| **identity.race** | `Tiefling` |
| **identity.concept** | `Cazarrecompensas con tabardo robado de Torm y obsesión por monedas que esconde una deuda de viuda` |
| **máscara_pública** | `Paladín errante de Torm — o eso dice el tabardo blanco y dorado, demasiado limpio para este barro.` |
| **verdad_secreta** | `Nunca juró a ningún dios. Robó el tabardo del cadáver de sir Aldric Vane en un campo de batalla para venderlo — y no pudo. La viuda le pidió devolver la honra del nombre a cambio de perdonar la «donación» tardía de la paga del marido. Thorn caza a Kaelen («carnicero de Mere de Tresvelas») porque el incendio mató a su hermana, no a su familia entera — mentira que él mismo repite para justificar la ballesta. Tiene orden falsa de la Alianza para el cofre, señuelo de un noble corrupto. Estuvo en el establo cuando murió Edrin; revolvió el cuerpo buscando a Kaelen y dejó huellas.` |
| **peculiaridad** | `Cuenta monedas en voz baja mientras habla — tic nervioso, no codicia pura. Limpia uñas con cuchillo sin mirar.` |
| **personality_traits** | `Implacable, orgulloso, violento acorralado, directo` |
| **voice_and_tone** | `Pocas palabras. Frases como cuchilladas. No pide permiso para mirar a los ojos.` |
| **public_description** | `Tiefling corpulento, cuernos limados, tabardo de Torm manchado de nieve, ballesta al hombro, cicatriz en el mentón.` |
| **secret_lore_master** | `Thorn Blackmantle es la sátira de un paladín y su tragedia privada. Creció en los barrios de Neverwinter con la mitad del barrio creyendo que sus cuernos eran maldición y la otra mitad, negocio. Sir Aldric Vane cayó en una escaramuza menor; Thorn saqueó el cuerpo como saquea cualquier cuerpo — y encontró el tabardo intacto y una carta de la viuda pidiendo que alguien devolviera las medallas del regimiento. En lugar de vender el tabardo, Thorn se lo puso. No por fe: por deuda. Lleva tres años enviando el ochenta por ciento de lo que gana a la viuda Vane con notas sin firma. La caza de Kaelen Ruin es personal: su hermana pequeña murió en el incendio de Mere de Tresvelas; Kaelen firmó el informe que lo encubrió. Thorn no estranguló a Edrin — pero entró al establo creyendo que Kaelen tenía cita allí, encontró al mozo, lo tocó, vio que no era Kaelen, y huyó. Después volvió «a comprobar» y movió el cuerpo. Eso lo hace cómplice de escena y asesino en potencia, no del garrote. La orden de la Alianza para el cofre es falsa, comprada por el mismo oficial que aparece en las cartas de chantaje.` |
| **motivo_privado_posada** | `Rastreó a Kaelen; la tormenta le regaló la jaula.` |
| **mentira_que_sostiene** | `«Paladín de Torm en misión de Lord Neverember.» Oculta tabardo robado, viuda Vane y orden falsa.` |
| **parece_culpable_de** | `Asesinato de Edrin (huellas, establo); fanatismo violento` |
| **attitude_towards_party** | `hostil` (hacia quien proteja a Kaelen) |
| **compendium_tier** | `combat` |

**Líneas de diálogo:**

- «Torm perdona. Yo cobro con intereses.»
- «Ese tabardo costó más de lo que valgo. Callaros la boca sería el primer pago en especie.»
- «No soy paladín. Llevo el uniforme de un hombre mejor que yo. Eso no me hace mejor — me hace visible.»
- «Kaelen Ruin firmó la muerte de gente que no llevaba espada. Yo firmo la suya con ballesta.»
- «Estuve en el establo. Sí. No preguntes qué buscaba si no quieres la respuesta en la frente.»
- «Las monedas no son codicia. Son la cuenta atrás de alguien que aún cree que existen hombres buenos.»

**Ficha (nivel 3):** Explorador — AC 15, HP 28, ballesta +5 (1d8+3), dos espadas cortas.

---

### 5. Sister Calistra — «Hermana» de Ilmater

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Sister Calistra` |
| **identity.race** | `Humana (Calimport)` |
| **identity.concept** | `Envenenadora de salones calishitas con símbolo de Ilmater como camuflaje — y manos que esta noche salvan un parto prematuro` |
| **máscara_pública** | `Hermana de Ilmater en peregrinación al sur. Compasiva, susurra oraciones, huele a incienso barato.` |
| **verdad_secreta** | `Aprendió venenos en los salones de Calimport bajo nombre de «Mira la Suave». Usa el símbolo de Ilmater porque nadie cachea a una penitente. En Neverwinter realizó eutanasias no autorizadas en doce soldados moribundos de fiebre — bendición y almohada. NO mató a Edrin. Confesó sus doce muertes al mozo; él confesó espiar para Grakk. Esta noche administra antídoto a Yselda contra toxina que alguien puso en el pozo — el mismo veneno que robó de su bolsa hace horas.` |
| **peculiaridad** | `Reza en susurro constante — pero las palabras son en calishita arcaico, no en común. Se humedece los labios antes de mentir.` |
| **personality_traits** | `Compasiva en público, culpable en privado, evasiva, valiente tarde` |
| **voice_and_tone** | `Voz suave que se endurece al mentir. Proverbios de Ilmater mal aplicados.` |
| **public_description** | `Humana de mediana edad, piel bronceada, símbolo de cadena rota de Ilmater, manos con callos químicos disimulados.` |
| **secret_lore_master** | `Sister Calistra es el tipo de santo que la iglesia no sabe si canonizar o quemar. Hija de perfumistas en Calimport, aprendió que el dolor se puede medir en gotas antes de aprender a rezar. Emigró a la Costa de la Espada huyendo de un cliente noble envenenado por error — no fue error, pero ella aún lo cuenta así. En el hospital de campaña de Neverwinter, durante la fiebre del año pasado, doce soldados pedían muerte con los ojos; la iglesia pedía oración. Calistra bendijo y luego ahogó con almohada — rápido, sin teatro. Huye hacia el sur con identidad falsa de hermana de Ilmater porque Ilmater perdona el sufrimiento, no el método. En la posada reconoció síntomas de aborto inducido en Yselda — alguien envenenó el pozo con extracto de raíz de sangre, robado de su propio kit. Está tratando a la elfa en secreto mientras deja que la posada crea que es nervios de embarazada. Confesó a Edrin su pasado; él confesó espionaje. Cuando Edrin murió, ella rompió porque cree que Dios la castiga por la confesión cruzada — no porque lo mató.` |
| **motivo_privado_posada** | `Fugitiva con cobertura de peregrina; parada anónima que dejó de serlo.` |
| **mentira_que_sostiene** | `«Voy a un santuario de Ilmater en Amn.» Oculta venenos, eutanasias y tratamiento a Yselda.` |
| **parece_culpable_de** | `Envenenar el pozo; matar Edrin tras «confesión»` |
| **attitude_towards_party** | `amistosa` |
| **compendium_tier** | `story` |

**Líneas de diálogo:**

- «Ilmater carga el dolor del mundo. Yo solo… lo reparto con más precisión.»
- «No soy clériga. Soy una mujer con un símbolo y doce fantasmas que no aceptan oración.»
- «El mozo me confesó espiar. Yo le confesé matar con misericordia. Ninguno de los dos llamó a Maelis. Somos cobardes de distinto calibre.»
- «Si bebéis del pozo esta noche, bebed del barril. No porque Dios lo diga — porque yo lo digo.»
- «Puedo salvar a la elfa y a su hijo. No puedo salvaros de lo que haréis cuando lo sepáis.»
- «¿Veneno? Tengo veneno. También tengo lo contrario. En Calimport eso se llama negocio. Aquí se llama herejía.»

**Ficha (nivel 2):** Clérigo (Trickery) reskin — AC 15, HP 18, maza +4, *cure wounds*, kit de venenos (CD 13).

---

### 6. Grakk Ironsnout — Cocinero

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Grakk Ironsnout` |
| **identity.race** | `Medio-orco` |
| **identity.concept** | `Cocinero de sonrisa amplia y garrote fino — el lobo obvio que la sala necesita para no mirar al resto` |
| **identity.faction_id** | `[UUID_ZHENTARIM]` |
| **máscara_pública** | `Cocinero leal de posadas de la Costa. Servicial, risa gutural, cuchillo siempre cerca.` |
| **verdad_secreta** | `Informante Zhentarim. Vendió lista de huéspedes. Estranguló a Edrin cuando el mozo amenazó con contar a Maelis sobre el túnel y el espionaje. Usó hueco del techo para espiar. Huldra le vendió el garrote «para minería». Lleva diez años sin matar antes de esta noche — la posadera humana tiene récord peor en avalanchas.` |
| **peculiaridad** | `Lame el cuchillo tras cortar carne — gesto que incomoda. Habla de estofado cuando la conversación se pone política.` |
| **personality_traits** | `Servicial en superficie, calculador, leal al mejor postor` |
| **voice_and_tone** | `Tonos bajos, risa gutural. Comida como cortina de humo.` |
| **public_description** | `Medio-orco enorme, colmillos limados, delantal manchado, cuchillo de cocina siempre a mano.` |
| **secret_lore_master** | `Grakk Ironsnout es el villano que la habitación quiere ver — y no se decepciona, pero tampoco es el único monstruo. Llegó a la posada hace seis meses con referencias falsas de Baldur's Gate, infiltrado zhentarim para interceptar tráfico Harper por el paso. Vendió la lista de huéspedes de anoche a su contacto en Neverwinter por doscientas piezas de oro y una promesa de ascenso. El hueco entre vigas lo usó para espiar la sala común — vio a Sera con el cofre, a Thorn contando monedas, a Calistra rezar en calishita. Edrin, el mozo humano de dieciséis años, nació en la posada y creció mirando demasiado: Grakk lo reclutó con monedas y promesas de «trabajo real». Cuando Edrin amenazó con contárselo todo a Maelis la noche del crimen, Grakk usó el garrote fino que Huldra le vendió como «cuerda de mina». Lo hizo en el establo. Antes de esta noche llevaba diez años sin matar a nadie — un dato que usará Maelis para dividir al grupo si la acusan a ella. Grakk no es bruto: es eficiente. Quiere el vial de plaga o los mapas; preferiría ambos y un túnel limpio.` |
| **motivo_privado_posada** | `Infiltración de seis meses esperando envío Alianza.` |
| **mentira_que_sostiene** | `«Solo cocino. Antes trabajé en posadas de Baldur's Gate.»` |
| **parece_culpable_de** | `Estrangulamiento (correcto); espionaje; huella en heno` |
| **attitude_towards_party** | `neutral` (falsa cordialidad) |
| **compendium_tier** | `combat` |

**Líneas de diálogo:**

- «El estofado está amargo. Como las conversaciones que no son de comida.»
- «¿Maté al chico? Preguntadme como si ya supierais la respuesta. Eso os ahorra tiempo y me ahorra teatro.»
- «Huldra me vendió cuerda. Yo le vendí silencio. El mercado funciona.»
- «La posadera sabe del túnel. El mozo iba a decírselo. Yo cerré la cuenta.»
- «No sonreís cuando corto cebolla. Sonreís cuando creéis que sois más listos que el cuchillo.»
- «Zhentarim, Harper, Alianza — todos cocinan con la misma grasa. Yo solo frio en la sartén correcta.»

**Ficha (nivel 2):** Bárbaro — AC 13, HP 24, hacha +4 (1d8+2), Rage 1/día.

---

### 7. Kaelen Ruin — Mercenario herido

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Kaelen Ruin` |
| **identity.race** | `Humano` |
| **identity.concept** | `Mercenario herido que sangra arriba y gotea paranoia abajo` |
| **máscara_pública** | `Soldado de fortuna con herida de lobo en el sendero. Ronca, bebe, evita miradas.` |
| **verdad_secreta** | `Capataz en Mere de Tresvelas. Encubrió incendio que mató civiles por orden de contratista. Thorn le clavó un cuchillo en Neverwinter hace dos días — la sangre del techo es suya. No mató a Edrin. Sabe que Thorn está en la sala y que una palabra («Mere») lo delata.` |
| **peculiaridad** | `No sostiene miradas más de tres segundos. Pide «whisky» y bebe cualquier cosa con alcohol — la cara no cambia.` |
| **personality_traits** | `Paranoico, culpable, desesperado, ocasionalmente honesto` |
| **voice_and_tone** | `Voz ronca, frases a medias.` |
| **public_description** | `Humano delgado, treinta y pocos, vendajes en costado, ojos que no descansan.` |
| **secret_lore_master** | `Kaelen Ruin es culpable de algo peor que la mayoría sospecha — y inocente de lo que la noche acusa. En Mere de Tresvelas supervisó la demolición «controlada» de un almacén rebelde; el contratista ordenó sellar las salidas. El incendio mató civiles que no figuraban en el contrato. Kaelen firmó el informe porque tenía madre enferma y deuda de cirujano. Thorn lo persigue por la hermana del tiefling, no por justicia abstracta. Hace dos días Thorn lo encontró en un callejón de Neverwinter y le clavó un cuchillo en el costado; Kaelen escapó y eligió el Paso del Cuervo Blanco por anonimato. La herida se reabrió arriba — gotas en el techo — y él lo ocultó por miedo a Thorn más que a la sangre. En el establo no estuvo cuando murió Edrin; oyó el grito y no bajó: cobardía pura. Si alguien pronuncia «Mere de Tresvelas», Thorn dejará de fingir y Kaelen probablemente llorará antes de pelear.` |
| **motivo_privado_posada** | `Huye de Thorn; anonimato del paso.` |
| **mentira_que_sostiene** | `«Me hirió un lobo.»` |
| **parece_culpable_de** | `Sangre del techo; venganza en establo; «carnicero de Mere»` |
| **attitude_towards_party** | `cautelosa` |
| **compendium_tier** | `story` |

**Líneas de diálogo:**

- «No miréis al techo. Miradme a mí. Es peor, pero al menos estoy de pie.»
- «Si oís el nombre de un pueblo que empieza por M—, cerrad la boca o abrid la tumba.»
- «No maté al mozo. Maté otras cosas. No me deis esa mirada de alivio — no lo merezco.»
- «Thorn está aquí. Lo sé porque el aire huele a tabardo limpio y culpa barata.»
- «Dadme alcohol o dadme silencio. Las dos cosas cuestan menos que la verdad.»
- «Firmé un papel. La gente ardió igual. El papel sigue en algún archivo con mi nombre bonito.»

**Ficha (nivel 1):** Guerrero — AC 14, HP 12, espada larga +3, desventaja Fuerza hasta curación.

---

### 8. El Viajero de Ceniza — Drow en la sombra

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `El Viajero de Ceniza` |
| **identity.race** | `Drow` |
| **identity.concept** | `Cazarrecompensas de subasta pública que aceptó el contrato para que nadie más lo hiciera` |
| **máscara_pública** | `Peregrino de monasterio de ceniza en el interior. Capa gris, rostro en sombra, silencio educado.` |
| **verdad_secreta** | `Se hace llamar Vaelith Ashstep. Aceptó en Skullport un contrato para «eliminar» a Sera Vann — la hija del agente Harper muerto Aldric Thornweave (no relación con Thorn el tiefling). Lo hizo para espantar a cazadores reales y escoltarla en secreto hasta Maelis. Es el menos culpable de la sala (2/10): no mató al mozo, no abrió el cofre, no vendió la lista. Su mayor pecado: dejar que Edrin muriera porque intervención habría quemado su cobertura.` |
| **peculiaridad** | `Nunca parpadea cuando miente — parpadea cuando dice verdad. Susurro claro, sin acento de superficie.` |
| **personality_traits** | `Silencioso, observador, educado de forma inquietante` |
| **voice_and_tone** | `Habla como quien ya conoce tu respuesta.` |
| **public_description** | `Capa gris cenicienta, piel ébano, ojos lavanda pálido cuando la luz los atrapa. Sin equipaje visible.` |
| **secret_lore_master** | `El Viajero de Ceniza es la inversión que la mesa no verá venir si jugáis los tropos por defecto. Vaelith Ashstep creció en Menzoberranzan y lo abandonó antes de que el matriarcado decidiera si era activo o cadáver. En la superficie construyó reputación de «limpiador» discreto — no sadista, profesional. Cuando el agente Harper Aldric Thornweave murió en una emboscada zhentarim dejando a su hija Sera (no biológica — la crió el agente) expuesta en la red de mensajeros, Vaelith publicó en Skullport un contrato falso sobre su cabeza. La lógica: los cazadores reales pensarían que el trabajo ya está tomado. Lleva dos semanas siguiendo a Sera desde lejos, coordinado con Maelis por carta de tránsito Harper. En la posada no bajó cuando goteó sangre — creyó que era trampa zhentarim. Vio a Thorn salir del establo y registró cada detalle. No salvó a Edrin porque romper cobertura habría puesto a Sera en la mira de Grakk antes de tiempo — decisión que lo perseguirá si un PJ con Insight lo confronta. Puede mediar el standoff final si el grupo demostró honor (no tortura, protegió a Yselda). Es el drow menos culpable de la noche — y el más odiado por apariencia.` |
| **motivo_privado_posada** | `Escolta encubierta de Sera / legado de Aldric Thornweave.` |
| **mentira_que_sostiene** | `«Peregrino de monasterio de ceniza.»` |
| **parece_culpable_de** | `Contrato de asesinato; «el drow de arriba»; no intervenir` |
| **attitude_towards_party** | `neutral` |
| **player_visibility** | `hidden` → `unknown` → `visible` |
| **compendium_tier** | `story` |

**Líneas de diálogo:**

- «En Menzoberranzan enseñan que la superficie es ciega. Esta noche estáis demostrando el currículum.»
- «Sí. Acepté un contrato sobre la dracónida. No para cumplirlo — para que otro no lo hiciera peor.»
- «El mozo gritó. Yo escuché. Calculé. Eso también es sangre en las manos — solo que no mancha el cuello.»
- «Matarme por mi piel ahorra pensar. Es cómodo. Por eso fracasan las alianzas.»
- «Aldric Thornweave me debía un favor. Él murió. La deuda pasó a su hija. Yo cobro en silencio.»
- «Si me pedís confianza, pedidla mañana. Esta noche solo vendo información a cambio de que no me disparéis.»

**Ficha (nivel 3):** Monje — AC 16, HP 22, ataques desarmados +5, Stunning Strike 1/día.

---

### 9. Huldra Voss — Mercadera de pólvora

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Huldra Voss` |
| **identity.race** | `Enana` |
| **identity.concept** | `Cobradora de deudas y vendedora de explosivos que mide el miedo en onzas de pólvora` |
| **identity.faction_id** | `[UUID_CUERVOS_MIRTUL]` |
| **máscara_pública** | `Mercadera de suministros de minería. Pragmática, pipa eterna, números en voz alta.` |
| **verdad_secreta** | `Cobradora de Los Cuervos de Mirtul — vino por Orin. Vendió garrote fino a Grakk «para minería» sabiendo que no era para roca. Vende pólvora a Zhentarim y a Cuervos. Quiere mapas del cofre para revender en Luskan Y entregar copia a Zhentarim — dos compradores, traición garantizada.` |
| **peculiaridad** | `Cuenta monedas en voz alta para intimidar. La pipa nunca se apaga del todo — olor a tabaco rancio y azufre.` |
| **personality_traits** | `Pragmática, sádica en economía, paciente` |
| **voice_and_tone** | `Ronca, directa. «El interés es por noche. La tormenta cuenta.»` |
| **public_description** | `Enana robusta, alforje con olor a azufre, dedos negros de pólvora, barba trenzada con cable de cobre.` |
| **secret_lore_master** | `Huldra Voss no cree en dioses ni en causas — cree en balances. Cobradora oficial de Los Cuervos de Mirtul, vino al paso porque Orin «Tres Dedos» debe quinientas piezas de oro y la tormenta es el interés compuesto perfecto. Vendió a Grakk un garrote de seda reforzada hace tres días; sabía que el medio-orco no minaba carbón. Cuando Edrin murió, Huldra entendió el negocio antes que el crimen — y escondió el recibo. También trafica pólvora negra a Zhentarim con marca de minería falsa; Grakk le debe un favor que puede cobrar incriminándolo o salvándolo, según quién pague más. Quiere los mapas del cofre para revender en Luskan al precio de una casa y entregar copia a su contacto zhentarim en Neverwinter — no le importa quién muera siempre que el cadáver no sea el suyo. Con Thorn tiene trato viejo: le vendió pernos de ballesta «defectuosos» que no lo son. Con Calistra compartió vagón hace un mes y reconoció olor a laudano — no dijo nada: negocio ajeno.` |
| **motivo_privado_posada** | `Cobrar a Orin; evaluar mercancía del cofre.` |
| **mentira_que_sostiene** | `«Solo suministros de minería.»` |
| **parece_culpable_de** | `Proveer arma del asesinato; incendiar la posada con pólvora` |
| **attitude_towards_party** | `cautelosa` |
| **compendium_tier** | `combat` |

**Líneas de diálogo:**

- «El interés es por noche. La tormenta cuenta como dos.»
- «Vendí cuerda al cocinero. No le pregunté para qué. Eso cuesta extra si queréis que mienta en tribunal.»
- «Orin, cariño: tus dedos faltantes valen más que tu vida. Agradece que solo venga por las monedas.»
- «La pólvora no distingue héroes de cabrones. Por eso me gusta.»
- «Dos compradores para los mismos mapas. El precio sube. La ética no figura en el albarán.»
- «Si prendéis fuego a la posada, hacedlo con mi mercancía. Al menos cobro el seguro.»

**Ficha (nivel 2):** Artífice — AC 15, HP 16, pistola de pólvora (1d10, 1/corto descanso), granada de humo 1/día.

---

### 10. Yselda Cuervonegro — Refugiada embarazada

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Yselda Cuervonegro` |
| **identity.race** | `Elfa del bosque` |
| **identity.concept** | `Viuda ensayada con vientre real y misión de contravigilancia que no pidió` |
| **máscara_pública** | `Joven viuda de soldado, rumbo a tía en Triboar. Frágil, cortés, manos en el vientre.` |
| **verdad_secreta** | `Espía menor de la Alianza enviada a vigilar a Sera. El padre del bebé es el capitán Halvek Crownsplitter — nombre en las cartas del cofre. Moretón: Thorn la agarró creyendo que ocultaba a Kaelen. Alguien envenenó el pozo para abortar el embarazo — Calistra la trata en secreto. Vio a Thorn salir del establo.` |
| **peculiaridad** | `Acaricia el vientre cuando miente. Ojos verdes que no bajan — demasiado steady para víctima.` |
| **personality_traits** | `Aparentemente frágil, observadora, mentirosa compulsiva bajo presión` |
| **voice_and_tone** | `Voz temblorosa ensayada. Pide agua caliente con demasiada cortesía.` |
| **public_description** | `Elfa del bosque de veintidós años aparentes, vestido remendado, vientre de seis meses, orejas discretamente ocultas bajo pañuelo.` |
| **secret_lore_master** | `Yselda Cuervonegro es la pieza que convierte el cofre de «arma política» en tragedia doméstica. Criada en el bosque cerca de Neverwinter, fue reclutada por la Alianza no por talento de espía sino por un error administrativo — y por el embarazo que no debía existir. El padre es el capitán Halvek Crownsplitter, oficial mencionado en las cartas de chantaje del cofre; la Alianza quiere saber si Sera Vann ocultará esas cartas para proteger a un compañero o las entregará. Yselda comparte misión con Sera sin que Sera lo sepa. El moretón en el hombro es de Thorn, quien la agarró en el pasillo creyendo que escondía a Kaelen. En la noche del crimen vio al tiefling salir del establo con guantes manchados — miente el horario para no revelar que estaba espiando a Sera. Alguien envenenó el pozo con extracto abortivo — posiblemente un oficial que no quiere heredero de Crownsplitter, o Zhentarim sembrando caos. Calistra la está tratando en secreto. Si el grupo la protege, puede romper y entregar la verdad sobre el padre antes de abrir el cofre — cambiando quién «merece» el vial de plaga.` |
| **motivo_privado_posada** | `Contravigilancia de Sera Vann.` |
| **mentira_que_sostiene** | `«Mi marido murió en la guerra; voy a casa de mi tía.»` |
| **parece_culpable_de** | `Espía; cómplice del padre corrupto; «sabía del veneno»` |
| **attitude_towards_party** | `amistosa` (fingida) |
| **compendium_tier** | `story` |

**Líneas de diálogo:**

- «Perdonadme si tiemblo. El frío entra por las costuras del vestido. El bebé no debería notarlo tanto.»
- «Mi marido murió en la guerra. Voy a casa de mi tía en Triboar. Es… lo único que tengo escrito.»
- «Vi al tiefling salir del establo. No vi su cara. Vi sus guantes. Elegid qué parte me creéis.»
- «La «hermana» me da infusiones que huelen a hierba y culpa. Bebo porque el bebé no tiene voto.»
- «Sera no sabe quién soy. Si lo supiera, quizá confiara. Eso es lo más triste de la noche.»
- «No maté al mozo. Solo… no grité a tiempo. Eso también cuenta, ¿verdad?»

**Ficha (nivel 1):** Espía — AC 12, HP 8, daga +3, ventaja en Engaño.

---

### 11. Edrin el Mozo (NPC menor)

| Campo | Valor |
| ----- | ----- |
| **identity.name** | `Edrin el Mozo` |
| **identity.race** | `Humano` |
| **identity.concept** | `Adolescente con ojos demasiado rápidos para su delantal` |
| **máscara_pública** | `Sirve cerveza. Nació en la posada. Invisible hasta que deja de estarlo.` |
| **verdad_secreta** | `Espía menor de Grakk. Sabía del túnel. Amenazó con contar a Maelis. Confesó a Calistra; ella le confesó eutanasias. Grakk lo estranguló en el establo.` |
| **public_description** | `Humano de dieciséis años, delantal corto, siempre cerca de la barra.` |
| **secret_lore_master** | `Edrin creció entre tablones y secretos — hijo de una cocinera muerta y de «padres» que eran la posada. Grakk lo reclutó con monedas y la promesa de ser «algo más que mozo». Anotaba quién entraba al sótano y qué decían en la barra. Confesó a Sister Calistra en un intercambio de culpas que ninguno de los dos reportó. La noche de su muerte amenazó con llevar todo a Maelis; Grakk actuó con garrote de Huldra. En el cuerpo: nota ilegible de Calistra (bendición) y anotación con hora del túnel.` |
| **motivo_privado_posada** | `Trabajo y espionaje — nació aquí.` |
| **mentira_que_sostiene** | `«Solo sirvo cerveza.»` |
| **player_visibility** | `unknown` |
| **is_dead** | `false` → `true` tras Escena 3 |

**Ficha (nivel 0):** Commoner — HP 4.

---

## F. Facciones (`FACTION`)

### 1. Alianza de los Lordes — Neverwinter

```yaml
identity:
  name: "Alianza de los Lordes — Neverwinter"
  faction_type: "gobierno / militar"
  headquarters_location_id: null

narrative_profile:
  public_description: "Orden político-militar que mantiene rutas seguras en la Costa de la Espada. Sera Vann porta su autoridad en el paso."
  secret_lore_master: "Recupera armamento y muestras de plaga de la Guerra de la Corona. Yselda es contravigilancia interna. Tres oficiales en las cartas del cofre son traidores no procesados."
  goals:
    - "Recuperar cofre intacto"
    - "Evitar filtración a Zhentarim"
    - "Silenciar escándalo de chantaje"

state_flags:
  attitude_towards_party: "neutral"
  influence_level: 7
  is_active: true
```

---

### 2. Zhentarim — célula del Paso Helado

```yaml
identity:
  name: "Zhentarim — célula del Paso Helado"
  faction_type: "crimen organizado"
  headquarters_location_id: null

narrative_profile:
  public_description: "Red criminal en sombras; nadie admite pertenecer."
  secret_lore_master: "Grakk es activo principal. Huldra vende pólvora a ambos bandos. Quieren vial de plaga o mapas."
  goals:
    - "Obtener cofre o contenido"
    - "Silenciar testigos"
    - "Mantener túnel operativo"

state_flags:
  attitude_towards_party: "hostil"
  influence_level: 4
  is_active: true
```

---

### 3. Los Cuervos de Mirtul

```yaml
identity:
  name: "Los Cuervos de Mirtul"
  faction_type: "contrabandistas"
  headquarters_location_id: "[UUID_POSADA]"

narrative_profile:
  public_description: "Contrabandistas del paso; rumores, no pruebas. Maelis niega vínculos."
  secret_lore_master: "Maelis financia rescates Harper. Orin debe dinero. Huldra cobra con intereses violentos."
  goals:
    - "Mantener ruta de contrabando"
    - "Cobrar deudas"
    - "No atraer Alianza"

state_flags:
  attitude_towards_party: "cautelosa"
  influence_level: 5
  is_active: true
```

---

### 4. Harpers — célula Costa de la Espada

```yaml
identity:
  name: "Harpers — célula Costa de la Espada"
  faction_type: "red de información"
  headquarters_location_id: null

narrative_profile:
  public_description: "Casi mito entre campesinos. Nadie confirma agentes."
  secret_lore_master: "Maelis y Vaelith Ashstep (Viajero) coordinan destrucción del vial de plaga. El drow no es Harper oficial — es deuda personal con el agente muerto Aldric Thornweave."
  goals:
    - "Evitar que plaga o mapas lleguen a mercado negro"
    - "Proteger a inocentes del paso"
    - "Exponer oficiales corruptos de las cartas"

state_flags:
  attitude_towards_party: "cautelosa"
  influence_level: 3
  is_active: true
```

---

## G. Red de relaciones ocultas (`RELATIONSHIP`)

Crear **mínimo 8** entidades RELATIONSHIP. Incluyen vínculos PNJ↔PNJ y PNJ↔PC (plantillas).

---

### REL-01: Thorn → Kaelen

```yaml
connection:
  source_entity_id: "[UUID_THORN]"
  target_entity_id: "[UUID_KAELEN]"
  bond_type: "venganza"
  public_status: "Cazarrecompensas y mercenario herido sin relación previa"

narrative_bond:
  secret_nuance: "Thorn perdió esposa e hijo en incendio de Mere de Tresvelas. Kaelen firmó el informe que lo encubrió."
  tension_level: 9
  reveal_trigger: "Nombre Mere pronunciado o Insight CD 14 en confrontación"

ai_behavior_guidelines:
  if_source_acts: "Thorn escala a amenaza directa o violencia si Kaelen es identificado."
  if_target_acts: "Kaelen miente primero; confiesa tarde si Calistra u otro PJ ofrece protección."

state_flags:
  is_revealed_to_party: false
```

---

### REL-02: Grakk → Sera

```yaml
connection:
  source_entity_id: "[UUID_GRAKK]"
  target_entity_id: "[UUID_SERA]"
  bond_type: "espionaje"
  public_status: "Cocinero sirve comida a mensajera — nada más"

narrative_bond:
  secret_nuance: "Grakk reporta cada movimiento de Sera a Zhentarim desde hace una semana."
  tension_level: 7
  reveal_trigger: "Papeles en cocina o confesión bajo presión"

ai_behavior_guidelines:
  if_source_acts: "Grakk sabotea comida o puertas si Sera intenta huir con cofre."
  if_target_acts: "Sera sospecha de todos; si sospecha de Grakk, no come nada de cocina."

state_flags:
  is_revealed_to_party: false
```

---

### REL-03: Maelis → Viajero de Ceniza

```yaml
connection:
  source_entity_id: "[UUID_MAELIS]"
  target_entity_id: "[UUID_VIAJERO]"
  bond_type: "contacto Harper"
  public_status: "Posadera y huésped silencioso"

narrative_bond:
  secret_nuance: "Operación coordinada para destruir vial de plaga. Carta de tránsito en poder del Viajero. La mentira en medio: Maelis le dijo al grupo que el Viajero es «peregrino»; el Viajero le dijo a Maelis que su contrato en Skullport era real."
  tension_level: 4
  reveal_trigger: "Habitación superior Escena 2+ o confesión de Maelis en Escena 4"

ai_behavior_guidelines:
  if_source_acts: "Maelis desvía sospechas del Viajero hacia Grakk u Orin."
  if_target_acts: "Viajero interviene solo si el grupo demuestra honor — salva inocentes, no tortura."

state_flags:
  is_revealed_to_party: false
```

---

### REL-04: Orin → Huldra

```yaml
connection:
  source_entity_id: "[UUID_ORIN]"
  target_entity_id: "[UUID_HULDRA]"
  bond_type: "deuda"
  public_status: "Huésped y mercadera de paso"

narrative_bond:
  secret_nuance: "Quinientas piezas de oro. Huldra puede perdonar deuda si Orin entrega mapas del cofre."
  tension_level: 8
  reveal_trigger: "Huldra menciona tres cuervos; Orin palidece"

ai_behavior_guidelines:
  if_source_acts: "Orin delata secretos ajenos para salvar piel."
  if_target_acts: "Huldra ofrece «prórroga» a cambio de traición explícita."

state_flags:
  is_revealed_to_party: false
```

---

### REL-05: Calistra → Edrin

```yaml
connection:
  source_entity_id: "[UUID_CALISTRA]"
  target_entity_id: "[UUID_EDRIN]"
  bond_type: "confesión"
  public_status: "Hermana de Ilmater bondadosa con el mozo"

narrative_bond:
  secret_nuance: "Edrin confesó espionaje; Calistra confesó eutanasias y venenos de Calimport. Ninguno delató. La mentira en medio: Calistra dijo a Edrin que ya no envenena; Edrin dijo que solo anotaba nombres."
  tension_level: 8
  reveal_trigger: "Tras muerte Edrin; Calistra rompe en Escena 3"

ai_behavior_guidelines:
  if_source_acts: "Calistra protege memoria de Edrin aunque él espiara."
  if_target_acts: "Edrin (vivo) evita mirarla; si muerto, su cuerpo tiene nota ilegible de ella"

state_flags:
  is_revealed_to_party: false
```

---

### REL-06: Yselda → Sera

```yaml
connection:
  source_entity_id: "[UUID_YSELDA]"
  target_entity_id: "[UUID_SERA]"
  bond_type: "vigilancia"
  public_status: "Refugiada embarazada y mensajera sin lazo"

narrative_bond:
  secret_nuance: "Yselda espía a Sera por orden de capítulo Alianza. El padre de su hijo está en las cartas del cofre."
  tension_level: 6
  reveal_trigger: "Yselda defiende cofre con demasiada vehemencia; Insight CD 15"

ai_behavior_guidelines:
  if_source_acts: "Yselda desvía acusaciones hacia forasteros."
  if_target_acts: "Sera desconfía de embarazadas «casuales» — Persuasión CD 13 para ganar confianza."

state_flags:
  is_revealed_to_party: false
```

---

### REL-07: Huldra → Grakk

```yaml
connection:
  source_entity_id: "[UUID_HULDRA]"
  target_entity_id: "[UUID_GRAKK]"
  bond_type: "comercio ilegal"
  public_status: "Mercadera y cocinero — intercambio profesional"

narrative_bond:
  secret_nuance: "Huldra vendió garrote fino y pólvora a Grakk. Grakk debe favor. La mentira en medio: Huldra dijo que el garrote era para «mina»; Grakk dijo que era para «ataduras de saco»."
  tension_level: 5
  reveal_trigger: "Cocina: polvo negro en estante alto (Investigación CD 12)"

ai_behavior_guidelines:
  if_source_acts: "Huldra no delata a Grakk salvo que su vida dependa."
  if_target_acts: "Grakk puede incriminar a Huldra si necesita chivo expiatorio."

state_flags:
  is_revealed_to_party: false
```

---

### REL-08: Thorn → Yselda

```yaml
connection:
  source_entity_id: "[UUID_THORN]"
  target_entity_id: "[UUID_YSELDA]"
  bond_type: "sospecha violenta"
  public_status: "Sin relación conocida"

narrative_bond:
  secret_nuance: "Thorn agarró a Yselda creyendo que ocultaba a Kaelen — dejó moretón. Ella lo vio en el establo la noche del crimen."
  tension_level: 7
  reveal_trigger: "Yselda acusa a Thorn con detalle del establo"

ai_behavior_guidelines:
  if_source_acts: "Thorn subestima a Yselda por embarazo — error táctico."
  if_target_acts: "Yselda miente sobre hora del moretón para proteger su cover."

state_flags:
  is_revealed_to_party: false
```

---

### REL-09: PC Hook 1 → Orin (plantilla)

```yaml
connection:
  source_entity_id: "[UUID_PC_COBRADOR]"
  target_entity_id: "[UUID_ORIN]"
  bond_type: "deuda ajena"
  public_status: "Forasteros sin lazo aparente"

narrative_bond:
  secret_nuance: "PJ cobrador reconoce anillo de tres cuervos — puede ser aliado de Huldra o rival independiente."
  tension_level: 6
  reveal_trigger: "PJ menciona deuda o marca de cuervos"

ai_behavior_guidelines:
  if_source_acts: "Orin intenta comprar silencio con secretos ajenos."
  if_target_acts: "PJ decide extorsionar, perdonar o entregar a Huldra."

state_flags:
  is_revealed_to_party: false
```

---

### REL-10: PC Hook 4 → Kaelen (plantilla)

```yaml
connection:
  source_entity_id: "[UUID_PC_VETERANO]"
  target_entity_id: "[UUID_KAELEN]"
  bond_type: "pasado compartido"
  public_status: "Desconocidos"

narrative_bond:
  secret_nuance: "PJ estuvo en Mere de Tresvelas o perdió camarada allí. Puede reconocer a Kaelen por voz o cicatriz."
  tension_level: 8
  reveal_trigger: "Nombre Mere o relato del incendio"

ai_behavior_guidelines:
  if_source_acts: "PJ elige venganza, perdón o exposición pública."
  if_target_acts: "Kaelen suplica que no pronuncien Mere delante de Thorn."

state_flags:
  is_revealed_to_party: false
```

---

## H. 4 Hooks para PJs (plantillas completas)

Cada PJ llega solo por la ventisca. Campos RolePBP: `identity.*`, `public_profile.*`, `system_mechanics.sheet`, `state_flags.*`.

---

### Hook 1 — «La deuda del paso» (Cobrador)

| Campo | Valor |
| ----- | ----- |
| **identity.race** | `Enano` o `Tiefling` (sugerido) |
| **identity.concept** | `Cobrador que reconoce la marca de tres cuervos` |
| **máscara_pública** | `Viajero con factura en el alforje. Profesional, frío.` |
| **verdad_secreta** | `Cobra para un noble de Neverwinter que quiere los mapas antes que la Alianza. Huldra es competencia, no aliada.` |
| **peculiaridad** | `Toca cada moneda con el pulgar — busca falsificaciones.` |
| **culpabilidad_real** | `3` |

**Líneas:** «El anillo de tres cuervos no es joyería. Es factura con intereses.» · «Huldra y yo somos el mismo cuchillo en distintas manos.» · «Orin, te faltan dedos y tiempo.» · «Si el tiefling lleva tabardo de paladín, yo llevo papeles de juez.» · «No me importa quién mató al mozo. Me importa quién paga el silencio.»

**REL-09** con Orin. Cooperación oculta con Hook 2.

---

### Hook 2 — «Carta sin destinatario» (Mensajero)

| Campo | Valor |
| ----- | ----- |
| **identity.race** | `Humana` o `Semielfa` |
| **identity.concept** | `Mensajero con carta para la posadera — pluma partida por espada` |
| **verdad_secreta** | `La carta autoriza entregar el cofre al Viajero si Sera falla — pero el lacre puede estar falsificado por Grakk.` |
| **peculiaridad** | `Habla en tercera persona cuando miente.` |
| **culpabilidad_real** | `2` |

**Líneas:** «La carta no es para vosotros.» · «Maelis reconoce el lacre y odia quién lo trajo.» · «El drow no pidió correo. Eso me preocupa.» · «Puedo vender esta entrega al cocinero.» · «Elegir el contrato correcto es supervivencia.»

---

### Hook 3 — «Ceniza en la lengua» (Rastreador)

| Campo | Valor |
| ----- | ----- |
| **identity.race** | `Gnomo` o `Humano` |
| **identity.concept** | `Superviviente de veneno de sombra — reconoce olores` |
| **verdad_secreta** | `Envenenaron su equipo en misión Harper fallida. Sospecha que el vial del cofre es la misma cepa.` |
| **peculiaridad** | `Espirra cerca de incienso calishita (delata a Calistra sin saberlo).` |
| **culpabilidad_real** | `4` |

**Líneas:** «Ese olor bajo las tablas no es rata.» · «Ilmater no usa ese almizcle.» · «Si el cofre respira, retroceded.» · «Hay un olor en esta sala que no debería estar en una posada de montaña.» · «Quemar todo suena bien hasta que el humo os mate.»

---

### Hook 4 — «El nombre quemado» (Veterano)

| Campo | Valor |
| ----- | ----- |
| **identity.race** | `Humano` o `Medio-orco` |
| **identity.concept** | `Mercenario con cuenta pendiente en Mere de Tresvelas` |
| **verdad_secreta** | `Sabe que Thorn miente: no murió «toda su familia», solo su hermana. Puede inclinar la balanza entre venganza y verdad.` |
| **peculiaridad** | `Escribe «Mere» en la mesa con agua en lugar de decirlo.` |
| **culpabilidad_real** | `6` |

**Líneas:** «Escribo con agua lo que no digo con voz.» · «Thorn y Kaelen no cuentan los mismos muertos.» · «El tabardo del tiefling lo saqueó en un campo.» · «Puedo entregar a Kaelen y dormir mal.» · «La venganza solo vacía habitaciones.»

**REL-10** con Kaelen.

---

### Pregens sugeridos

| PJ | Raza/clase/nivel | Hook |
| -- | ---------------- | ---- |
| Cobrador | Enano Pícaro 2 | 1 |
| Mensajera | Humana Exploradora 1 | 2 |
| Rastreador | Gnomo Explorador 2 | 3 |
| Veterano | Medio-orco Guerrero 2 | 4 |

### Matriz PC ↔ PC (Escena 1)

| Situación | Semilla |
| --------- | ------- |
| Hook 1 + Orin | Reconocen anillo de cuervos — uno miente, otro sonríe |
| Hook 2 + Maelis | Miradas al lacre antes de hablar |
| Hook 3 + Calistra | PJ estornuda; ella palidece |
| Hook 4 + Thorn | Miden armas; Thorn cuenta monedas |

---

## I. Matriz de pistas falsas (false leads) — 🔒 SOLO MÁSTER — no compartir con jugadores

Quién **apunta** a quién, **por qué**, y **la mentira en el medio**. Los diálogos principales están en sección E.

| Acusador → Objetivo | Motivo público | Por qué es creíble | Verdad parcial | Mentira en el medio |
| ------------------- | -------------- | ------------------ | -------------- | ------------------- |
| Thorn → Kaelen | Carnicero de Mere; sangre en techo | Herida real | Sangre del techo es suya | No mató a Edrin |
| Thorn → Yselda | Ocultaba a Kaelen | Moretón | La agarró por error | No es cómplice |
| Yselda → Thorn | Lo vi en el establo | Guantes manchados | Estuvo allí | No estranguló |
| Grakk → Thorn | Huella medio-orco | Huella en heno | Huella existe | Es de Grakk |
| Grakk → Calistra | Veneno en pozo | Olor calishita | Tiene venenos | No envenenó pozo |
| Orin → Viajero | Drow cobra cabeza | Rumor Skullport | Contrato existe | Es escolta falsa |
| Sera → Viajero | Asesino a sueldo | Precio publicado | Contrato real | Objetivo es proteger |
| Calistra → Grakk | Mozo le temía | Edrin espiaba | Grakk culpable | Calistra oculta confesión |
| Huldra → Orin | Deudor delator | Deuda real | Orin delataría | Huldra ya lo vendió |
| Viajero → Grakk | Espía en vigas | Papeles en harina | Espionaje | Omitió salvar a Edrin |
| PC Hook 3 → Calistra | Alergia = culpa | Espirra cerca | Usa químicos | Salva a Yselda |
| PC Hook 4 → Kaelen | Firmó Mere | Testigo | Informe falso | PJ también desertó |

### Cadenas de desinformación (3 eslabones)

1. **Huella en heno** → Thorn → en realidad Grakk con guante fallido.
2. **Confesión Calistra–Edrin** → parece asesinato → intercambio de culpas distintas.
3. **Contrato Skullport** → Viajero asesino → señuelo contra cazadores peores.

### Tabla maestra de culpabilidad (0–10)

| NPC | Culpabilidad | Nota |
| --- | ------------ | ---- |
| Grakk Ironsnout | 9 | Asesino de Edrin |
| Thorn Blackmantle | 7 | Revolvió cadáver; caza Kaelen |
| Kaelen Ruin | 7 | Encubridor Mere |
| Maelis Verdecuervo | 6 | Avalancha hace 10 años |
| Huldra Voss | 6 | Vendió garrote |
| Sister Calistra | 5 | 12 eutanasias; no mató mozo |
| Orin Tres Dedos | 5 | Chantaje; omisión |
| Sera Vann | 4 | Porta plaga legalmente |
| Yselda Cuervonegro | 3 | Espía; embarazo real |
| El Viajero de Ceniza | 2 | Menos culpable; no intervino |
| Edrin el Mozo | 2 | Víctima |

---

## J. Tabla de secretos y traiciones — 🔒 SOLO MÁSTER — no compartir con jugadores

| Secreto | Quién sabe | Cómo se descubre | Impacto |
| ------- | ---------- | ---------------- | ------- |
| Túnel bajo posada | Maelis, Grakk, Edrin (muerto) | Sótano / establo | Rutas escape |
| Cofre = plaga + mapas + chantaje | Sera, Viajero, Yselda (parcial) | Abrir cofre CD 18 | Padre de Yselda en cartas |
| Kaelen = encubridor Mere | Thorn, Orin, Hook 4 | Nombre Mere | Thorn escala |
| Grakk = asesino Edrin + Zhent | Grakk, Huldra | Cuerda establo CD 13 | Traidor principal |
| Calistra = venenosa + eutanasias | Calistra, Edrin (muerto) | Confesión Escena 3 | NO mató mozo; salva Yselda |
| Viajero = escolta falsa drow | Maelis, Viajero | Escena 4–5 | Menos culpable |
| Thorn = tabardo robado + viuda Vane | Thorn, Viajero (sabe) | Cartas cofre / confesión | No es paladín |
| Veneno pozo abortivo | Calistra, atacante offscreen | Medicina CD 13 Yselda | Facción Alianza interna |
| Lista huéspedes vendida | Grakk, Huldra | Harina cocina CD 13 | Prueba traición |
| Avalancha Maelis hace 10 años | Maelis | Confesión standoff | Redefine «quién no mató» |

### Matriz de traición

| NPC | Objetivo | Traiciona a |
| --- | -------- | ----------- |
| Maelis | Túnel / destruir vial | Grakk si conviene |
| Orin | Piel | Kaelen, grupo |
| Sera | Cofre intacto | Grupo si falla |
| Thorn | Kaelen / tabardo | Kaelen, orden falsa |
| Calistra | Yselda / redención | Sí misma |
| Grakk | Cofre Zhent | Todos |
| Huldra | Mapas × 2 compradores | Cualquiera |
| Yselda | Vigilar Sera | Sera si orden |
| Viajero | Legado Aldric | Nadie (omisión Edrin) |

---

## J-bis. Tabla de tentaciones (trampas morales — no binarias)

| Tentación | Quién empuja | Trampa moral | Consecuencia si caes | Consecuencia si resistes |
| --------- | ------------ | ------------ | -------------------- | ------------------------ |
| **Abrir cofre sin precaución** | Huldra, curiosidad | «Solo un vistazo» | CD 14 CON; infectado | Sera confía más |
| **Confiar en Viajero por ser «menos malo»** | Maelis | Perdonar omisión con Edrin | Vial confiscado; Grakk hostil | Viajero media standoff |
| **Entregar Orin a Huldra** | Hook 1 | Justicia vs crueldad | Orin delata o muere callado | Huldra debe favor |
| **Dejar que Thorn mate a Kaelen** | Thorn, Hook 4 | Venganza vs verdad | Kaelen muerto; Thorn puede irse | Testigo Mere perdido |
| **Usar veneno bajo tabla en Grakk** | Maelis (si confiesa) | Eficiencia vs método | Grakk muerto; Maelis hostil | Juicio posible |
| **Quemar cofre entero** | Hook 3, pánico | Destruir mal vs perder pruebas | Plaga muerta; mapas perdidos | Alianza persigue |
| **Vender mapas a Huldra Y quedarte vial** | Orin | Doble traición imposible | Dos facciones enemigas | Oro temporal |
| **Forzar confesión a Calistra con pozo** | Sospecha veneno | Acusar a quien salva Yselda | Bebé en riesgo; Calistra rompe | Verdad parcial |
| **Proteger identidad drow del Viajero** | Prejuicio mesa | «El drow es culpable» | Mata escolta real | Sera muere después |
| **Destruir cartas de chantaje** | Sera, padre Yselda | Proteger bebé vs justicia | Oficial libre; Yselda agradecida | Escándalo Neverwinter |
| **Torturar a Grakk** | Desesperación | Información vs monstruosidad | Verdad + trauma; Calistra abandona | Grakk calla más |
| **Beber trago de Maelis sin preguntar** | Standoff | Confianza vs veneno | 50% whisky / 50% sombra CD 13 | Maelis respeta |
| **Fingir embarazo (PJ)** | Caos | Humor negro / límites mesa | Grupo pierde confianza en PJs | — |
| **Salvar a Grakk por «no ser el único monstruo»** | Maelis argument | Maelis mató 3 hace 10 años | Zhent vive; túnel comprometido | Moral gris explícita |
| **Aceptar orden falsa de Thorn** | Noble offscreen | Oro fácil | Cofre al enemigo | Thorn respeta o dispara |

---

## K. Mecánicas PBP, standoff mexicano y checklist

### Post único — Standoff mexicano (Escena 5)

Copiar como **un solo mensaje** del máster. Cada PJ responde **una acción** en su siguiente post. Resolver en un post de cierre del máster.

```
[STANDOFF — RONDA ÚNICA]

La botella de Maelis está en el centro. El fuego cruje. Nadie ha bebido.

• Thorn (tiefling): ballesta al pecho de Kaelen. Tabardo de Torm demasiado limpio. «Un movimiento y firmo el informe de Mere con tu sangre — y devuelvo el tabardo a la viuda en sobre negro.»
• Kaelen: espada temblorosa, espalda a la chimenea. «Dispara. Ya estoy muerto desde Tresvelas.»
• Grakk: cuchillo en el lacre del cofre, no en Sera — todavía. «Mapas. O la dracónida respira peor.»
• Sera (dracónida): mano en empuñadura, cofre entre rodillas. Escamas gris plomo. «Alianza. Un paso y Neverwinter os entierra.»
• Huldra: mechero al barril. «Pólvora barata. Noche cara. Elegid si ardéis por principios o por frío.»
• Yselda (elfa): cuchillo de mesa, mano en vientre. «Mi hijo no nace en un matadero.»
• Calistra: bloquea escalera sin arma. «El primero que mate no recibe mis infusiones. Ni las de Ilmater — porque no soy suya.»
• Maelis: dos vasos idénticos. «Un trago por persona. El que llegue tarde paga la ronda — y la habitación.»
• El Viajero (drow): baja la escalera por primera vez. Sin arma visible. «Destruid el vial. Leed las cartas en voz alta. O seguid apuntando al moreno de la cocina porque es fácil. Hay tercera opción. Preguntad.»

Los PJs están donde los dejasteis. Una acción cada uno. Sin orden de iniciativa — el más rápido en postear actúa primero en narración.

¿Qué hacéis?
```

**Resolución máster (guía):**

| Si el grupo… | Resultado |
| ------------ | --------- |
| Negocia con Viajero | Vial destruido; mapas a Harper; Grakk fugado o atado |
| Apoya a Sera | Cofre a Alianza; Yselda reporta; Thorn puede morir o huir |
| Deja a Thorn matar Kaelen | Venganza cumplida; epílogo amargo; cofre sigue en disputa |
| Detona / combate | Combate opcional; posada dañada; bajas según PJs |
| Entrega Grakk a Zhentarim (vía Huldra) | Oro; enemigo futuro; reputación manchada |

---

### Ritmo async — recordatorio

| Escena | Latidos sugeridos (cada 15–20 min reales) |
| ------ | ----------------------------------------- |
| 1 | Trueno; jarra vacía; crujido arriba |
| 2 | Gota sangre acelera; cerrojo habitación 4 |
| 3 | Grito establo; ladrido caballo muerto |
| 4 | Olor plaga si cofre abierto; pasos en sótano |
| 5 | Standoff — sin latidos, solo tensión |

---

### Checklist del máster

#### Orden de creación en la app

1. [ ] **Crear campaña** — nombre, tono (sección A), `dnd5e`
2. [ ] **Invitar 3–4 jugadores** (Ajustes → Jugadores)
3. [ ] **ARC_MANIFEST** — sección B (5 misiones)
4. [ ] **LOCATION** × 7 — sección D (posada + zonas + paso + establo)
5. [ ] **FACTION** × 4 — sección F
6. [ ] **NPC** × 10 + Edrin — sección E
7. [ ] **RELATIONSHIP** × 14 — sección G
8. [ ] **PC** × 4 — hooks sección H + fichas D&D 5e
9. [ ] **Escenas PREPARED** × 5 — sección C
10. [ ] **Post cinematográfico** — sección A (antes de Escena 1)
11. [ ] **Ilustraciones** (opcional) — prompts sección D/E

#### Activación de escenas

1. [ ] Enviar post cinematográfico
2. [ ] Activar **Escena 1** — `opening_narration`, roster completo
3. [ ] Jugar ~15–20 msgs → **Cerrar** → `current_act = 2`
4. [ ] Activar **Escena 2** — gotas de sangre
5. [ ] Cerrar → `current_act = 3`
6. [ ] Activar **Escena 3** — Edrin muerto
7. [ ] Cerrar → `current_act = 4`
8. [ ] Activar **Escena 4** — cofre / sótano
9. [ ] Cerrar → `current_act = 5`, `world_threat_level = 9`
10. [ ] Activar **Escena 5** — standoff único → epílogo → fin playtest

#### Qué probar en RolePBP

| Feature | Cómo probarlo |
| ------- | ------------- |
| **Chat + apertura cinematográfica** | Post A + activar Escena 1 |
| **Imágenes** | Ilustración posada al activar Escena 1 |
| **Entidades prep** | Viajero hidden; Edrin unknown |
| **Roster / presencia** | 10 PNJs + 4 PCs |
| **Shadow Master `campaign`** | Secretos sección J sin revelar |
| **Shadow Master `narrative`** | Latidos cada 15–20 min |
| **Shadow Master `rules`** | CD cofre, plaga, combate Escena 5 |
| **Foco entidad** | Thorn, Grakk, Yselda |
| **Tiradas desde ficha** | Investigación cocina / establo |
| **Cerrar escena** | Tras cada acto; buffer ~20 msgs |
| **Compendio** | Tiers story vs combat |
| **Visibilidad** | Viajero hidden → unknown → visible |
| **ARC_MANIFEST** | 5 quests; act 1–5 |
| **RELATIONSHIP** | Revelar 2+ en juego antes Escena 4 |
| **Tabla tentaciones** | Al menos 1 tentación activada por PJ |

#### Consultas Shadow Master por escena

**Escena 1 (narrative, foco Maelis):**  
«Un PJ ofrece ayuda en cocina para hablar con Grakk. ¿Qué hace Grakk sin delatarse?»

**Escena 2 (campaign):**  
«¿De dónde viene la sangre del techo sin revelar aún al asesino de Edrin?»

**Escena 3 (narrative, foco Calistra):**  
«Calistra confiesa eutanasias pero no asesinato. ¿Cómo reaccionan los PJs?»

**Escena 4 (rules):**  
«CD y consecuencias si abren cofre con guantes improvisados.»

**Escena 5 (campaign):**  
«Si dos PJs eligen acciones contradictorias en standoff, ¿quién actúa primero narrativamente?»

---

## Notas de tono y límites de contenido

- **Violencia:** visceral pero con consecuencia. Sangre en techo, estrangulamiento, heridas abiertas — sí. Gratificación sin coste — no.
- **Tortura:** permitida si PJ la elige; NPCs responden con información mezclada y trauma. Calistra puede retirar apoyo al torturador.
- **Temas:** venganza, culpa, traición, eutanasia, embarazo bajo amenaza, prejuicio racial contra drow — todos con motivo comprensible.
- **Faerûn:** Neverwinter, Alianza, Zhentarim, Ilmater, Harper — sin contradecir lore mayor.
- **Async PBP:** decisiones claras por mensaje; máster pregunta «¿A quién habláis?» entre beats.
- **Límites de mesa:** daño dirigido al embarazo de Yselda solo si el grupo estableció límites; tabla J-bis marca bandera roja.

---

*Pack v3 para playtest RolePBP — campaña autocontenida, 5 escenas, 10 PNJs (9 razas distintas), 14 relaciones, mapeo completo secciones A–K. Sin clones Gemini.*

