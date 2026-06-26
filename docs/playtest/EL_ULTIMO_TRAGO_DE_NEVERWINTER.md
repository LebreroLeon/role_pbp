# EL ÚLTIMO TRAGO DE NEVERWINTER
### Documento de Referencia del Máster — v5.0

> **Sistema:** D&D 5e · Faerûn, Costa de la Espada  
> **Formato:** PBP async · 5 escenas · ~15–20 mensajes por escena  
> **Solo el Máster lee esto completo. Los jugadores solo ven lo que el Máster elige revelar.**

---

## APÉNDICE TÉCNICO — Mapa de campos de la app RolePBP

| Área de la app | Campos que rellenar |
|---|---|
| **Crear campaña / Ajustes** | `name`, `tone`, `game_system` |
| **Arco narrativo** (`ARC_MANIFEST`) | `plot_line.*`, `active_quests[]`, `state_flags.*` |
| **Ubicación** (`LOCATION`) | `identity.*`, `narrative_profile.*`, `state_flags.*` |
| **NPC** | `identity.*`, `ai_narrative_profile.*`, `system_mechanics.sheet`, `state_flags.*` |
| **PC** | `identity.*`, `public_profile.*`, `system_mechanics.sheet`, `state_flags.*` |
| **Facción** (`FACTION`) | `identity.*`, `narrative_profile.*`, `state_flags.*` |
| **Relación** (`RELATIONSHIP`) | `connection.*`, `narrative_bond.*`, `ai_behavior_guidelines.*`, `state_flags.*` |
| **Escena preparada** (`PREPARED`) | `display_name`, `scene_objective`, `location_id`, `opening_narration`, `master_prep_notes`, `prepared_entity_refs[]` |
| **Shadow Master** | Modos `narrative` / `rules` / `campaign` + foco en entidad (`focus_entity_id`) |

---

---

# 0. SINOPSIS

**Premisa.** Una ventisca ciega el Paso del Cuervo Blanco. Diez personas quedan atrapadas en la Posada del Paso Helado, cada una con un motivo para estar aquí y un motivo mayor para que nadie lo sepa. En el centro: un cofre de hierro sellado que cuatro facciones quieren por razones incompatibles. Selvyn Drask, notario real de Neverwinter, cuarenta y cinco años y un fichero mental de todos los presentes, lleva la noche chantajeando a cuatro personas distintas con citas escalonadas en el establo. Esta noche va a morir —a manos de alguien que la sala entera tardará en mirar— y la sala entera va a reconstruir la noche equivocándose de manera espléndida.

**Cómo dirigirlo.** No hay combate obligatorio. El motor de la aventura es la deducción: cada pista revela que la explicación obvia es incorrecta, que la persona más gentil hizo algo calculado, y que la persona más temible tiene una razón que la sala entiende en silencio. Selvyn muere en la Escena 3 —en tiempo real, durante el juego— no antes. Sembrad las causas en las Escenas 1 y 2. El Máster mantiene al menos dos NPCs activamente mintiendo en cualquier momento. Nunca anunciéis temas; dejad que los jugadores los encuentren cavando.

**Pregunta central:** *¿Quién mató a Selvyn Drask —y cambia algo que alguien lo hubiera evitado?*

---

---

# 1. ESTRUCTURA DRAMÁTICA

---

## ESCENA 1 — «El Paso no perdona»
**Función dramática:** Presentación claustrofóbica. Establecer que nadie dice la verdad sobre por qué está aquí. Sembrar el cofre, la herida de Renwick, y la deuda de Tamlin como señuelos. Selvyn debe ser visible, anotando cosas en su cuadernillo.

### QUÉ DEBE OCURRIR
- Todos los PJs y NPCs llegan o ya están en la sala común cuando la tormenta bloquea toda salida.
- Wenna anuncia que nadie sale hasta el amanecer. «La tormenta no pide permiso. Vosotros tampoco vais a empezar.»
- El cofre de Caelith queda visible sobre la mesa esquinera —sello de la Alianza a la vista para quien sepa leerlo (Investigación CD 12).
- Selvyn Drask ya está instalado, cuadernillo sobre la mesa, y hace preguntas de procedimiento a los recién llegados con la amabilidad chirriante de alguien que toma nota de todo.
- Renwick baja a la barra con la mano derecha rígida y los nudillos vendados bajo el guante —alguien lo nota (Medicina CD 11).
- Lysse Mourne ofrece infusiones a quien parezca cansado. Las infusiones son exactamente lo que parecen.

### QUÉ PUEDE OCURRIR
- Un PJ intenta leer el cuadernillo de Selvyn. Selvyn lo cierra con una sonrisa de funcionario. «Documento de uso oficial. Pero si tenéis algo que declarar voluntariamente, me ahorra tiempo.»
- Borrakh Peñadiente entra mojado hasta los huesos y no mira a nadie. Pide solo agua.
- Tamlin toca la mandolina —una canción de Neverwinter que Durvis Hakk reconoce (Perspicacia CD 13 para notar que Durvis se detiene una fracción de segundo).
- Onno Grist propone una bendición de viaje. Es la segunda vez esta tarde. No deja de hablar.
- Sira Veleth no solicita habitación. Paga por una silla en la sala común y no da más explicaciones.

### CIERRE DE ESCENA (CONTROLADO POR EL MÁSTER)
La chimenea de la sala común se apaga de golpe —todas las llamas, simultáneamente, sin corriente visible. La sala queda en luz de lámpara. Del exterior, en dirección al establo, llega un grito de caballo: uno solo, agudo, sostenido, que se corta en seco. Borrakh se pone de pie a medias. Sira no levanta los ojos de su copa. Wenna dice, mirando la puerta del fondo: «Los caballos notan la tormenta antes que nosotros. Seguid bebiendo.» La chimenea se reavivia sola desde las brasas, treinta segundos después. **La jaula está cerrada.** → Avanzar a Escena 2 cuando todos los jugadores hayan establecido a quién vigilan.

---

## ESCENA 2 — «La gota en el techo»
**Función dramática:** Primer cuerpo sin cadáver. La paranoia empieza antes de que haya víctima. Revelar capas ocultas bajo la superficie social. Selvyn empieza a desaparecer y reaparecer, demasiado satisfecho consigo mismo.

### QUÉ DEBE OCURRIR
- Un líquido oscuro y viscoso gotea desde las vigas sobre la mesa central —es de Renwick, herida en la mano reabierta en la habitación 3.
- Nadie admite haber subido. Borrakh miente el horario (estaba en el establo revisando su caballo).
- Selvyn hace tres visitas breves y separadas a tres NPCs distintos —cada una en voz baja, con el mismo cuadernillo. En cada una, el NPC consultado se pone rígido. Nunca se queda con ninguno más de dos minutos.
- Lysse prepara una segunda infusión. Esta vez para sí misma. La bebe despacio, de espaldas a la sala.
- Onno anuncia que ha «bendecido el sótano» —sin que nadie se lo pidiera. Wenna lo mira como a alguien que acaba de entrar en territorio ajeno.

### QUÉ PUEDE OCURRIR
- Un PJ sube y encuentra la habitación 3 con sangre en el suelo y la puerta sin pestillo —Renwick estaba practicando con la mano herida.
- Un PJ inspecciona la cocina y encuentra la puerta oculta detrás de la estantería entreabierta (CD Investigación 12). Los goznes no crujen —están recién aceitados.
- Tamlin intenta venderle a un PJ información sobre el sello del cofre. Pide tres monedas de oro.
- Durvis le susurra algo a Caelith que la hace apretar la mano sobre el cofre. Caelith niega que ocurrió algo si se le pregunta.
- Borrakh revisa sus herramientas de herrero en la mochila. El sonido de metal es inconfundible.

### CIERRE DE ESCENA (CONTROLADO POR EL MÁSTER)
Un sonido de algo pesado arrastrado en el piso de arriba —una vez, con esfuerzo, y luego nada. Luego: drip. Drip. Drip. El líquido oscuro sigue cayendo del techo sobre la mesa, pero ahora hay más. Una tabla del techo cruje. Algo cae al suelo arriba. Silencio total desde la planta superior. Luego, con una calma pasmosa, Selvyn Drask pasa por la sala en dirección a la cocina con el cuadernillo bajo el brazo. Sonríe al pasar. Nadie sabe a dónde va. → Avanzar a Escena 3.

---

## ESCENA 3 — «El trabajo de la noche»
**Función dramática:** EL ASESINATO. Selvyn muere durante esta escena. La sala se convierte en un tribunal improvisado donde el culpable real conduce la acusación porque así cierra el círculo.

### QUÉ DEBE OCURRIR
- Un grito cortado llega del establo. Los caballos patean. No es el viento.
- Selvyn yace en el heno del tercer pesebre con el cuello marcado por una ligadura fina. Ojos abiertos. En la mano todavía aprieta el cuadernillo, abierto en una página en blanco.
- **Pista 1:** Fibra de cuerda vegetal trenzada en el cuello —no es cuerda de trabajo ni cuerda de mina. Es cuerda botánica, del tipo que usan los herbolarios para colgar manojos a secar. (Investigación CD 13.)
- **Pista 2:** La puerta oculta de la cocina al establo está ligeramente desencajada —alguien la usó para entrar y salir sin pasar por la sala común. (Investigación CD 11 en la cocina.)
- **Pista 3:** En los bolsillos de Selvyn: tres notas de chantaje dobladas, con tres nombres distintos. Una cuarta nota falta —se nota porque el cuadernillo tiene cuatro entradas y solo hay tres cartas. (Investigación CD 14 en el cadáver + cuadernillo.)
- Borrakh aparece desde la puerta principal del establo, mojado. Dice que comprobaba su caballo. La sala lo mira como a lo que parece.
- Lysse se ofrece a examinar el cadáver. Lo hace con calma metódica. Anuncia «muerte por estrangulación» sin vacilar. Correcto. Pero no menciona el olor a hierba sedante que ella misma reconocería.

### QUÉ PUEDE OCURRIR
- Un PJ con Medicina CD 13 detecta un olor residual extraño en los labios de Selvyn —herbal, no alcohólico. Lysse, si está presente, dice: «Infusión de camomila. La vendí yo. Le ayudaba con los nervios.» Verdad parcial.
- Si los PJs acusan a Borrakh, Renwick dice en voz alta: «Estuvo fuera diez minutos. Lo conté.» Borrakh lo mira. No dice gracias.
- Si los PJs inspeccionan el cuadernillo, ven tres nombres: Wenna Corren, Renwick Sorn, Durvis Hakk. Todos en la sala. La cuarta entrada está en blanco pero la página tiene la presión del bolígrafo de la hoja anterior —se puede leer con carbón (CD Investigación 15): «L.M.»
- Sira, desde el umbral del establo, sin que nadie se lo pida: «El único que salió por la cocina esta noche fue alguien que conocía la puerta. Eso recorta la lista.»

### CIERRE DE ESCENA (CONTROLADO POR EL MÁSTER)
Mientras el grupo forma sus primeras acusaciones junto al cadáver —la pared interior del establo emite un sonido de madera moviéndose. El panel oculto de la puerta del establo conectada a la cocina oscila solo, despacio, hacia adentro. El pasillo detrás está en sombras. Los goznes no crujen. Recién aceitados. Nadie visible al otro lado. → Avanzar a Escena 4.

---

## ESCENA 4 — «El precio del cofre»
**Función dramática:** Las facciones salen del armario. El cofre se convierte en el centro gravitacional de toda traición pendiente. El contenido crea dilemas morales, no solo información.

### QUÉ DEBE OCURRIR
- Durvis pone una bolsa de monedas sobre la mesa: «Ese cofre se abre esta noche o yo abro algo más. La única duda es cuántos de vosotros van a estar vivos para ver qué hay dentro.»
- Sira baja la capucha por primera vez. Sus rasgos drow quedan visibles. «He esperado suficiente a que esto se resuelva solo.» Se sienta sin pedir permiso.
- Si el cofre se abre: vial de plaga sellada + mapas de arsenales bajo el Paso + cartas de chantaje que nombran al Comandante Halvek Byrne como traidor de guerra. Renwick ve el nombre y no dice nada, pero cierra el puño bajo la mesa.
- Onno Grist se vuelve llamativamente activo —empieza a moverse hacia la cocina. Si alguien lo observa (Percepción CD 12), va directamente hacia la trampilla.

### QUÉ PUEDE OCURRIR
- Sira revela que aceptó un contrato de información sobre Caelith para saber el contenido del cofre antes de que llegara a Neverwinter. «No vine a robarlo. Vine para que nadie más lo hiciera peor.»
- Wenna confiesa el túnel si alguien la acusa directamente de encubrir el asesinato. Lo hace con calma clínica: «El túnel lleva tres años ahí. No lo construí para matar a nadie —lo construí para no morir de hambre. Durvis pagó. Yo abrí el suelo. Eso es todo lo que fue.»
- Renwick, si alguien pronuncia el nombre «Byrne» en voz alta, se levanta despacio. «Mi familia vivía en el ramal norte del paso. Seis personas. Durvis vendió las rutas. Byrne firmó el informe que decía que el ataque fue un error de navegación.» Y espera a ver qué hace la sala.
- Si Lysse es confrontada con la cuarta nota («L.M.»), sonríe con una calma que es peor que la hostilidad. «Selvyn tenía algo que me habría costado todo. Elegí qué valía más. Si eso os parece un crimen, contad los cuerpos de todos los presentes antes de pronunciar sentencia.»

### CIERRE DE ESCENA (CONTROLADO POR EL MÁSTER)
Un golpe sordo desde debajo del suelo, en dirección a la cocina. Luego un BANG —pequeño, seco, percusivo— y la trampilla oculta detrás del hogar de la cocina salta medio palmo de su encaje, escupiendo humo acre y el olor inconfundible de pólvora. Onno Grist, en el umbral de la cocina, se detiene. La cara completamente neutral. «Alguien», dice despacio, «activó mi seguro.» → Avanzar a Escena 5.

---

## ESCENA 5 — «El último trago»
**Función dramática:** Standoff final. Un trago de licor sin etiqueta. La verdad o la bala. Nadie sale limpio; la pregunta es cuántos salen vivos.

### QUÉ DEBE OCURRIR
- Wenna saca de bajo la barra una botella sin etiqueta. «Un trago por cabeza. Después que los dioses decidan.»
- Lysse, si no ha sido detenida, intenta salir por el túnel. Si el grupo lo nota (Percepción CD 11), se para. Si no, Wenna anuncia cuando ya tiene la mano en la trampilla reparada.
- Post de standoff: cada jugador en un solo post declara posición, armas, a quién apunta y qué dice en voz alta.

### QUÉ PUEDE OCURRIR
- Sira revela el legado del mentor que le debe Caelith y que la deuda de silencio pasó al nombre del cofre, no al comandante.
- Renwick, si Durvis sigue vivo, dice su nombre completo. «Durvis Hakk. Ramal Norte, invierno del año 1492 del Calendario del Dale. Mi hermano mayor tenía diecisiete años.» Y espera.
- Onno ofrece neutralizar el vial si alguien le garantiza inmunidad para sus actividades en el sótano. «Tengo los reactivos. No soy un fraile —eso ya lo sabéis. Pero sé química.»
- **Final A:** Los Harpers (Sira) se llevan el cofre —las cartas se exponen, Renwick obtiene justicia, Caelith desaparece en el archivo.
- **Final B:** El vial se destruye —Onno lo hace, Wenna cierra el túnel, el escándalo queda enterrado con la nieve.
- **Final C:** Fuga por el túnel —queda abierta la pregunta sobre Byrne y el ramal norte.
- **Final D:** Masacre.
- **Final E:** Tregua Harper con confesiones parciales —cada NPC paga un precio, ninguno el precio completo.

### CIERRE DE CAMPAÑA
Epílogo: una línea por PJ vivo. Selvyn Drask fue enterrado o no según lo que decidió el grupo. El cuervo blanco del umbral sigue en su poste. Nadie sabe si graznó durante la noche.

---

---

# 2. EL MISTERIO — GUÍA DEL MÁSTER
### 🔒 SOLO MÁSTER — NO COMPARTIR

---

## LA VERDAD COMPLETA DE LA NOCHE

### Cronología hora a hora

**Seis días antes:** Durvis Hakk envía al contacto zhentarim en Neverwinter la lista de huéspedes esperados. Entre ellos, Caelith Brynmar con el sello de la Alianza. Los Zhentarim ordenan recuperar el cofre a cualquier precio.

**Cuatro días antes:** Selvyn Drask recibe información de un informante en el archivo de Neverwinter: el notario lleva dos semanas investigando a Durvis Hakk. Esto lo sabe Durvis. También lo sabe Lysse —Selvyn se lo dijo sin querer en una conversación sobre «deudas pendientes de la guerra», creyendo que podía usarlo para presionarla. Error fatal.

**Tres días antes:** Lysse Mourne decide que Selvyn va a hablar demasiado pronto. Prepara el compuesto sedante, calcula el método, planifica la ruta de salida. No hay rabia en esto. Es aritmética.

**Dos días antes:** Sira Veleth recibe instrucción Harper: escoltar el cofre de Caelith de forma encubierta hasta que cruce el paso. Llega primero a la posada. No revela su misión a Wenna, aunque Wenna ya la sospecha.

**La mañana del día:** Selvyn llega temprano y pasa el día redactando cuatro notas de chantaje en su habitación: para Wenna (el túnel), para Durvis (sus actividades zhentarim), para Renwick (el incendio del ramal norte), y para Lysse (su identidad como Harper renegada). Entrega las tres primeras personalmente en la tarde. La de Lysse se la guarda para «el momento apropiado».

**Hora primera (llegada, tarde):** Los viajeros van llegando. La tormenta se cierra. Selvyn empieza a circular por la sala haciendo visitas breves. Tres NPCs se tensan. Lysse recibe su nota —la última— en algún momento entre la cena y las campanadas. Lee. Dobla. La destruye en la lumbre de su cuarto.

**Hora segunda (noche temprana):** Selvyn le comunica a Lysse la hora de su cita en el establo: «La segunda campanada. Venid sola. Si no venís, el informe sobre vuestra identidad Harper llega a Skullport mañana por la mañana.» Lysse no dice nada. Se va a preparar infusiones en la cocina. Entre la cocina y su cuarto, encuentra y comprueba la puerta oculta al establo: los goznes los aceitó ella misma durante la tarde con aceite de linaza de la despensa, sin que nadie la viera.

**Antes de las dos campanadas:** Lysse va a la cocina con la excusa de preparar una tisana para «el herido del tercer cuarto» —Renwick. Nadie lo verifica. En la cocina, prepara también una segunda taza con extracto de adormidera y verbena sedante. Entra al establo por la puerta oculta con las dos tazas. Pone la taza con el compuesto en el poste del tercer pesebre donde Selvyn la encontrará.

**Las dos campanadas:** Selvyn entra al establo por la puerta principal del patio. Encuentra la taza. La bebe —es amarga, pero no más que su té habitual. Lysse sale del hueco del cuarto pesebre donde esperaba. La conversación dura tres minutos. Selvyn empieza a sentir los brazos pesados en el minuto cuatro. En el minuto seis, Lysse usa la cuerda botánica. El trabajo dura noventa segundos. Los caballos se agitan. Lysse pone el cuadernillo en la mano del cadáver —abierto en la página en blanco, como si todavía estuviera tomando notas. Destruye la cuarta nota del cuadernillo. Sale por el túnel desde el tercer pesebre. Tarda doce minutos en llegar a la cocina por el subsuelo.

**Justo después:** Borrakh, que había bajado por la puerta principal del establo a revisar su yegua una hora antes, vuelve a pasar —oyó los caballos. Encuentra el cadáver. Lo toca para saber si respira. Se limpia la mano en el heno. Sale sin gritar porque no quiere ser el primer sospechoso. No grita. Se va a la sala común.

**Tres minutos después:** Tamlin sube a la cocina a buscar agua. Encuentra a Lysse lavándose las manos en el cubo de la despensa. Ella dice: «No podía dormir.» Tamlin asienta y no dice nada —todavía.

**Poco después:** El grito llega desde el establo. Alguien que salió a buscar a Selvyn encontró el cuerpo. El grupo baja.

---

## LOS ACCESOS AL ESTABLO — TRES RUTAS DOCUMENTADAS

| Ruta | Descripción | Quién la usó esta noche | Evidencia que deja |
|---|---|---|---|
| **1. Puerta principal del patio** | Puerta de madera norte del establo, da al patio interior cubierto de nieve | Selvyn (víctima), Borrakh (antes del crimen) | Barro en el umbral, huellas en el patio si hay luz; difícil con ventisca |
| **2. Puerta oculta de la cocina** | Panel de madera detrás de la estantería del corredor trasero; pasillo de 4m hasta la pared lateral del establo | Lysse (asesina, ida y vuelta esta noche) | Ligero desencaje del panel; aceite de linaza fresco en los goznes (CD 11 Investigación en cocina) |
| **3. Ventana este del piso superior** | Ventana de la habitación 5; da a la cubierta de pizarra del establo; salto de 2,5m hasta el heno interior (Atletismo CD 12) | Renwick (antes del crimen, para observar el patio) | Rasguños en el alféizar exterior; pizarras movidas en la cubierta (CD 14 Investigación) |
| **4. Túnel de contrabando** | Desde la bodega oculta bajo la cocina → conducto subterráneo de 40m → emergen en el suelo del tercer pesebre | Lysse (regreso tras el crimen) | Tierra arcillosa rojiza del túnel en el suelo del pesebre (CD 12 Investigación); rastro de la misma tierra en la cocina si se busca (CD 13) |

---

## EL CELLAR OCULTO — GUÍA DEL MÁSTER

**Acceso:** Trampilla de piedra detrás del hogar de la cocina, disimulada bajo una pila de leña. Requiere mover la leña (visible) y encontrar el mecanismo de palanca (CD 13 Investigación). Durvis Hakk tiene una llave para la cerradura inferior; sin llave, CD 14 para abrir con ganzúa.

**Contenido:**
- Veinte cajones de madera lacrada con sello zhentarim: documentos falsos, cartas de crédito, dos espadas cortas sin marcar, un frasco de veneno no identificado.
- Correspondencia entre Durvis y dos contactos en Luskan —escrita en cifra zhentarim estándar (CD Arcana 15 para descifrar sin clave).
- Mapa de las cuatro salidas del túnel: la cocina de la posada, el establo (tercer pesebre), una salida al barranco oriental (a 250m), y una entrada tapiada que apuntaba a las ruinas de un antiguo puesto del Paso.
- Rastros de cuerda botánica trenzada en el suelo del pasillo del túnel hacia el establo —del tipo de Lysse (CD 13 Investigación, confirma la ruta de regreso).
- Una pequeña carga de pólvora negra con detonador de percusión instalada por Onno Grist —trampa de seguridad que activó de forma remota durante la Escena 4 para crear distracción.

**Quién sabe que existe:**
- Durvis Hakk: lo construyó, lo usa, lo mantiene.
- Wenna Corren: consintió su construcción a cambio de dinero. Lo lamenta.
- Onno Grist: lo descubrió durante una estancia anterior y colocó su trampa sin decírselo a nadie.
- Lysse Mourne: lo usó esta noche por primera vez para escapar del establo.
- Selvyn Drask (ya muerto): tenía referencias indirectas al túnel en su cuadernillo —era parte de su expediente sobre Wenna.

**Qué revela sobre la trama mayor:** La operación zhentarim en el Paso del Cuervo Blanco no es de esta noche —lleva tres años activa, con Durvis como nodo de distribución. Los arsenales del cofre de Caelith conectan directamente con esta bodega: fueron diseñados para ser vaciados de armas a través de este mismo túnel. La bodega es la prueba de que el cofre no es solo evidencia de crímenes pasados —es evidencia de crímenes futuros planificados.

---

## EL COFRE — QUÉ CONTIENE Y POR QUÉ IMPORTA

**Contenido real:**
1. **Vial de plaga sellada** — muestra de arma biológica usada en la Guerra de la Corona. No es arma funcional: es evidencia. Su existencia prueba que la Alianza usó plaga contra civiles en tres aldeas de la Costa del Norte. Destruirlo elimina la prueba. Conservarlo es un arma política de primer orden.
2. **Mapas de arsenales** — ubicación de cuatro depósitos enterrados bajo el Paso del Cuervo Blanco. Conectan directamente con la bodega oculta de la posada. Quien los tenga puede desmantelar la operación —o completarla.
3. **Cartas de chantaje** — correspondencia entre tres oficiales de la Alianza y agentes zhentarim, vendiendo posiciones durante la guerra. Una nombra al Comandante Halvek Byrne. Renwick Sorn lleva dos años buscando esa firma.

**Por qué lo quiere cada facción:**
- **La Alianza (Caelith):** Recuperar y destruir el vial + las cartas —silenciar el escándalo.
- **Los Zhentarim (Durvis):** Vial de plaga + mapas. No les importan las cartas —ya saben lo que dicen.
- **Los Cuervos de Mirtul (Onno):** Los mapas únicamente. Venderlos en Luskan y al contacto zhentarim. Dos compradores para el mismo objeto: precio máximo.
- **Los Harpers (Sira):** Destruir el vial. Exponer las cartas —no silenciarlas, usarlas para purgar oficiales corruptos.
- **Renwick Sorn (personal):** Las cartas específicamente. El comandante que vendió el ramal norte debe comparecer ante un tribunal.

**El dilema moral central:** Abrir el cofre expone la corrupción de la Alianza —justicia para civiles que murieron— pero destruye la carrera de personas que quizá cumplían órdenes. Destruir el vial protege al mundo de que llegue al mercado negro, pero elimina la única prueba física de los crímenes. No hay salida limpia.

---

## MATRIZ DE FALSAS PISTAS

| Quién parece culpable | Por qué parece culpable | Por qué no lo es (del asesinato) |
|---|---|---|
| **Borrakh Peñadiente** | Estuvo en el establo; huellas suyas en el heno; tiene un pasado violento | Llegó antes del crimen a revisar su yegua. Lo encontró sin gritar por cobardía, no por culpa. |
| **Durvis Hakk** | Reacción demasiado calmada; tenía el motivo más obvio; conoce el túnel | Durvis quería a Selvyn controlado, no muerto —la exposición es más cara que el chantaje. |
| **Renwick Sorn** | Estuvo en la ventana este; tiene herida reciente; dos de sus nombres están en el cuadernillo | Renwick estaba vigilando el patio buscando a Durvis. Tiene coartada de visión parcial. |
| **Wenna Corren** | El túnel es suyo; Selvyn la chantajeaba; «calma excesiva» | Wenna no mató a Selvyn. Sabía que si moría, alguien investigaría la posada. Prefería pagar. |
| **Onno Grist** | Acceso al sótano; trampa explosiva propia; activo y nervioso en Escena 4 | La trampa era de seguridad general, no relacionada con Selvyn. Onno solo mata conceptos, no personas. |

---

## EL GIRO — LA REVELACIÓN QUE RECONTEXTUALIZA TODO

**La revelación:** En la Escena 4, si los jugadores presionan a Sira Veleth, esta revela que Selvyn Drask no era solo un extorsionista. Llevaba seis meses construyendo un expediente para los Harpers —un caso real, con pruebas reales, contra la red zhentarim de Durvis. El chantaje era su mecanismo de protección: si alguien lo mataba antes de entregar el expediente, las notas automáticas en el archivo de Neverwinter se abriría solas. O eso creía él. Lysse lo sabía. Y sabía que Selvyn había mentido sobre el sistema de respaldo —no existía.

**Lo que esto cambia:** Selvyn no era solo el villano de la noche. Era el único que estaba construyendo el caso que Renwick lleva dos años necesitando. Su muerte no es solo un asesinato —es el cierre de la única línea de acusación válida contra Byrne. Y Lysse lo sabía. Calculó cuánto valía el expediente versus cuánto le costaba su supervivencia. El expediente perdió.

**La pregunta que se queda en la sala:** Lysse mató a alguien despreciable que hacía algo importante. ¿Cuánto pesa eso?

---

---

# 3. NPCS

---

## WENNA CORREN — *Humana, posadera*

| Campo | Valor |
|---|---|
| **Físico** | Cuarenta y ocho años y ni uno de disculpas. Manos de alguien que ha cargado barriles, reparado tejados y enterrado a dos maridos. Los ojos grises lo cuentan todo si sabes leer a las personas que han aprendido a no contar nada. Tiene una cicatriz oblicua en el antebrazo derecho que no explica nunca. |
| **Vestimenta** | Delantal de cuero teñido oscuro sobre camisa de lino gris. Llave de la bodega colgada al cuello —no la suelta jamás. Botas con suela reforzada de acero, aunque no está de obras. |
| **Objetos** | Martillo de tablonar (herramienta, todavía). Botella sin etiqueta bajo la barra, reservada para el día que alguien diga una verdad entera. Una nota de Selvyn doblada en cuatro en el bolsillo del delantal —la chantajeaba con el túnel. |
| **Actitud inicial** | Cordial como un cuchillo limpio. Llama a todos «viajero» hasta que dan un motivo para otra cosa. No pregunta por qué estás aquí —cobra por adelantado y asume lo peor. |
| **Motivación** | Llegar al amanecer sin que la posada arda. Proteger el túnel que la salvó del hambre. Lidiar con el hecho de que Selvyn estaba muerto antes de que ella decidiera qué hacer con su nota. |
| **Secreto** | Consintió la construcción del túnel zhentarim hace tres años a cambio de dinero. Nunca la usó para nada violento —pero la existencia del túnel convierte todo lo que ocurra esta noche en su responsabilidad legal. Sabe que Lysse es una ex-Harper renegada desde un informe de hace tres años que nadie más en la sala ha leído. No dijo nada porque no tenía respaldo. |
| **Qué sabe de otros** | Sabe que Lysse figura en un informe Harper como «operativa renegada, peligrosidad máxima». Sabe que Durvis construyó el túnel con su complicidad. Sabe que Selvyn tenía notas sobre ambas cosas. |
| **Coartada** | En la barra toda la noche —múltiples testigos. Sólida. |
| **Culpabilidad** | **5/10.** No mató a Selvyn. Pero habría podido advertirle del informe sobre Lysse y eligió no hacerlo porque el problema era mutuo. |

**Diálogos preparados:**

*Coopera:*
— «La tormenta no pide permiso. Vosotros tampoco vais a empezar.»
— «Hay un túnel bajo esta posada. Lo abrieron unos hombres que pagaron bien y hacían preguntas malas. Sigo aquí. Ellos no.»

*Neutral:*
— «He visto morir a gente con menos razones que las vuestras. No me miréis así —no fue aquí.»
— «El cuervo blanco del umbral es decoración. Si creéis en presagios, pagáis doble.»

*Hostil:*
— «No abrís el sótano por curiosidad. Lo abrís cuando no quede otra —y entonces negociamos.»
— «Mis maridos murieron en esta cama. Nadie pagó en disculpas. Aprended.»

*Bajo presión:*
— «Sí. Dejé construir el túnel. Tenía deudas y tenía hambre. Eso tiene nombre —supervivencia. Lo que ocurrió esta noche tiene otro nombre. No son el mismo.»

*Si descubren su secreto:*
— «Sabía lo que era Lysse Mourne. No dije nada porque decirlo me habría puesto a mí en el centro. Me equivoqué. Eso es todo lo que tenéis de mí esta noche.»

**Comportamiento con otros NPCs:**
- *Con Sira:* La única persona de la sala de quien no recela. Coordinación sin afecto.
- *Con Durvis:* Lo contrató por referencias que resultaron falsas. Lo sospecha desde hace semanas. No actuó porque el túnel dependía de no alterarlo.
- *Con Lysse:* La única persona de la sala que sabe quién es Lysse de verdad. No la miró directamente desde que llegó.

---

## SELVYN DRASK — *Humano, víctima*

| Campo | Valor |
|---|---|
| **Físico** | Cuarenta y cinco años con cara de funcionario veterano: calvicie incipiente, papada honesta, manos de escribiente con callos en el dedo índice derecho. Nada en él señala peligro. Eso es exactamente lo que es. El cuadernillo de cuero marrón siempre bajo el brazo como una extremidad extra. |
| **Vestimenta** | Sobretodo azul marino con insignia de notario real —real, no robada. Camisa limpia. Botas buenas pero sin ostentación. El traje de alguien que quiere parecer autoridad sin parecer dinero. |
| **Objetos** | Cuadernillo de cuero con cuatro entradas (tres notas de chantaje entregadas, una destruida). Bolsa interior con cartas de acreditación real. Frasco de tinta sellado en el bolsillo. Una daga pequeña que nunca alcanzó a usar. |
| **Actitud inicial** | Amabilidad chirriante de inspector. Hace preguntas de procedimiento como si tomarlas en un registro oficial. «Solo por curiosidad burocrática» que no es curiosidad ni burocrática. |
| **Motivación (oculta al grupo)** | Llevaba seis meses construyendo un expediente sobre la red zhentarim de Durvis Hakk para entregarlo a los Harpers. El chantaje era su financiación y su protección simultáneamente. Esta noche empujó demasiado y demasiado rápido. |
| **Secreto** | Era un extorsionista funcional que estaba haciendo algo importante. Nadie en la sala lo sabe excepto Sira. |
| **Coartada** | N/A — víctima. |
| **Culpabilidad** | **1/10.** Hizo cosas malas por razones que la sala no entenderá hasta la Escena 4. Eso no lo salva. |

**Diálogos preparados** *(solo Escenas 1–2, antes de morir)*:

*Coopera:*
— «¿Cuánto tiempo lleváis en el Paso? Pregunto por el registro —es rutina. No miréis así, todo el mundo tiene rutinas.»
— «La posada tiene un historial interesante. Nada que no pueda resolverse con la documentación correcta.»

*Neutral:*
— «No soy vuestro enemigo. Soy alguien que toma notas. Diferencia fundamental.»
— «La tormenta es una excelente oportunidad para poner en orden asuntos que llevaban tiempo pendientes. Lo digo en general.»

*Nervioso (Escena 2, si alguien lo observa de cerca):*
— «Tengo que revisar algo en mi cuarto. Volveré en breve.» *(No vuelve en cinco minutos.)*
— «¿Os ha dado infusiones la herbolaria? Sí. Buenas manos. Mucho cuidado con los que tienen buenas manos.»

**Comportamiento con otros NPCs:**
- *Con Lysse:* La subestimó. Eso lo mató.
- *Con Durvis:* Sabía exactamente quién era. Lo tenía en su expediente. Cometió el error de decírselo.
- *Con Wenna:* La chantajeaba pero con cierta consideración —le gustaba la posada.

---

## BORRAKH PEÑADIENTE — *Medio-orco, herrero viajero*

| Campo | Valor |
|---|---|
| **Físico** | Medio-orco de treinta y ocho años, dos metros y anchura de puerta. Colmillos que nunca limó porque decidió que la gente que huye de su aspecto es gente con quien no vale la pena hablar. Manos marcadas de trabajo de fragua —no pueden sostener un vaso sin parecer que van a aplastarlo. Una cicatriz larga en la mejilla izquierda que termina exactamente donde empieza la mandíbula. |
| **Vestimenta** | Cuero de trabajo con marcas de chispa que no salen. Camisa de malla ligera debajo —costumbre vieja, no precaución activa. Mochila con herramientas de herrero que suenan al moverse. |
| **Objetos** | Martillo de trabajo (herramienta). Frasco de agua —solo agua, lleva ocho meses sin alcohol. Una carta sellada en el bolsillo interior que no ha abierto y no va a abrir. |
| **Actitud inicial** | Habla despacio, eligiendo palabras como si costaran algo. No ocupa más espacio del necesario. Pide agua cuando todo el mundo pide cerveza —sin explicar por qué. |
| **Motivación** | Llegar a Triboar donde lo espera trabajo honesto. Esta noche: no ser el primer sospechoso de nada. Ha aprendido que los medios-orcos son siempre el primer sospechoso. |
| **Secreto** | Hace cuatro años fue responsable de un incendio en un depósito militar que mató a tres hombres. Fue descuido, no malicia. Renwick Sorn lo cubrió. Borrakh lleva cuatro años sin saber por qué —y sin querer saberlo, porque la respuesta implica que le debe algo. |
| **Qué sabe de otros** | Vio a Renwick en la ventana este del piso superior cuando volvió del establo. Renwick estaba mirando hacia afuera, no hacia adentro. Borrakh no sabe qué buscaba. |
| **Coartada** | Estuvo en el establo revisando su yegua antes del crimen —regresó a la sala cuando los caballos se agitaron, pero no avisó porque no quería ser el primero en explicar por qué estaba allí. Frágil por omisión. |
| **Culpabilidad** | **3/10.** Encontró el cadáver y no dijo nada. Eso tiene peso moral aunque no sea el asesino. |

**Diálogos preparados:**

*Coopera:*
— «No voy... a causar problemas. No esta noche.» *(Pausa larga.)* «Estaba en el establo. Vi al hombre muerto. No grité porque gritar no cambia lo que está muerto.»
— «Si alguien quiere saber qué herramientas hay en esa bolsa, puede mirar. No tengo nada que no sea acero y cuero.»

*Neutral:*
— «Dadme agua o dadme silencio. Las dos cosas cuestan menos que lo que estáis pensando.»
— «No soy el problema de esta noche. Probablemente.»

*Hostil:*
— «Si levantáis esa acusación sin prueba, preparaos para que la próxima vez sea con prueba.»
— «Llevo cuatro años aprendiendo a no romper cosas. Esta noche no es excepción.»

*Bajo presión:*
— «Sí. Estuve en el establo. Lo encontré. No llamé porque soy un medio-orco con herramientas en la espalda en una posada cerrada por tormenta. Pensad en eso un momento antes de juzgar el instinto.»

*Si descubren su secreto:*
— «El depósito ardió. Tres hombres murieron. Fue mi error y no mi intención y eso es exactamente tan útil como suena. Renwick lo tapó. No sé por qué. Lleva cuatro años sin cobrarme.»

**Comportamiento con otros NPCs:**
- *Con Renwick:* Lo reconoció en cuanto entró. No ha cruzado ni una palabra. Lo vigila con el rabillo del ojo.
- *Con Lysse:* No la sospecha. Dejó que le pusiera un vendaje en la mano izquierda. Eso la acerca demasiado.
- *Con Wenna:* La única persona de la sala que no lo mira con recelo. Eso lo hace confiar en ella más de lo que debería.

---

## LYSSE MOURNE — *Elfa del bosque, herbolaria*
### LA ASESINA

| Campo | Valor |
|---|---|
| **Físico** | Madera élfica de ciento veintitantos años con cara que el mundo lee como treinta y cinco. Piel de color nogal claro, cabello castaño rojizo recogido con fijadores botánicos —cuerda trenzada de hierbas, del tipo que usa para colgar manojos. Los ojos avellana son cálidos hasta que se fijan en algo. Entonces son otra cosa completamente. |
| **Vestimenta** | Capa forestal sobre ropa de viaje funcional sin color. Bolsa de herbolaria de cuero marrón siempre al hombro —grande, ordenada, con olor a lavanda y algo más amargo debajo. Guantes de trabajo finos que se quita para examinar plantas o heridas. |
| **Objetos** | Kit herbolario completo: manojos secos, mortero, viales sellados, cuerdas botánicas de varios calibres. Un extracto de adormidera y verbena en un frasco sin marcar —dosis sedante, no letal. La cuerda botánica que usó como garrote no está en el kit —la tiró en el túnel. |
| **Actitud inicial** | Cálida, atenta, hace preguntas que parecen amabilidad pero son evaluación. Ofrece infusiones antes de que se las pidan. Escucha como alguien que necesita la información para curar, no para retenerla. |
| **Motivación** | Sobrevivir esta noche y salir del paso con su identidad intacta. Selvyn tenía información que la habría expuesto a los Harpers (por renegada) y a los Zhentarim (por ex-Harper). Cualquiera de los dos habría sido su muerte. Hizo el cálculo. |
| **Secreto** | Fue operativa Harper durante cuarenta años. Desertó cuando le ordenaron eliminar a un informante que tenía familia. Lleva doce años sola, trabajando en los márgenes. Selvyn encontró su historial en algún archivo de Neverwinter. Esta noche lo mató con una sedación y una cuerda de hierbas, y usó el túnel de contrabando para volver a la posada. No le temblaron las manos. Eso también lo sabe. |
| **Qué sabe de otros** | Sabe que Onno Grist le compró un compuesto explosivo hace tres años usando otro nombre —pero era él. Sabe que Sira Veleth es una Harper activa asignada a vigilarla. |
| **Coartada** | «Arriba toda la noche, sin bajar a la sala.» Tamlin la vio en la cocina de madrugada. La coartada tiene esa grieta. Además: sus cuerdas botánicas en la bolsa —¿cuántas quedan? Nadie pensó en contarlas todavía. |
| **Culpabilidad** | **10/10.** La asesina. Sin ambigüedad. La única ambigüedad es si el grupo puede probarlo —y cuánto les importa una vez que saben a quién mató. |

**Diálogos preparados:**

*Coopera:*
— «Esa herida necesita tiempo, como las raíces de invierno. ¿Os importa que eche un vistazo?»
— «Puedo examinar el cadáver. Tengo algo de conocimiento de anatomía. Más que suficiente para esto.»

*Neutral:*
— «Las plantas no mienten. Las personas sí. Prefiero las plantas, en general.»
— «No soy vuestro enemigo. Soy la única persona en esta sala que quiere que todos salgáis vivos.» *(Verdad técnica.)*

*Hostil:*
— «Podéis acusarme. Pero si lo hacéis sin prueba, perderéis el tiempo que necesitáis para encontrar la prueba real.»
— «Cuarenta años haciendo trabajo difícil en lugares oscuros enseñan una cosa: la persona que señala primero raramente es la que tiene las manos sucias.»

*Bajo presión:*
— «Selvyn tenía algo que me habría destruido. Hice lo que hice. Si queréis llamarlo crimen, llamadlo. Si queréis llamarlo aritmética, también es correcto.»

*Si descubren su secreto:*
— «Sí. Con compuesto sedante y cuerda botánica. En el establo. Volví por el túnel. Me lavé las manos en la cocina y fui a la cama. El chico de la mandolina me vio —ya lo sé. Decidid si eso me hace un monstruo o un problema de matemáticas con patas.»

**Comportamiento con otros NPCs:**
- *Con Onno:* Sabe que no es fraile. Lo observa con la misma calma con que se observa una planta potencialmente tóxica —sin miedo, con atención.
- *Con Sira:* La única persona de la sala que la pone nerviosa. Sira lo nota.
- *Con Borrakh:* Lo usa como escudo de sospecha inconsciente —cuanto más lo miren a él, menos la miran a ella. No le dijo esto; simplemente lo calcula.

---

## DURVIS HAKK — *Enano, mercader de gemas*

| Campo | Valor |
|---|---|
| **Físico** | Enano de sesenta años con barba gris corta y bien recortada —no la barba de un herrero, sino la de alguien que come bien y duerme cómodo. Manos sorprendentemente finas para un mercader. Los ojos azul acero evalúan el precio de todo lo que hay en una habitación antes de decir buenos días. |
| **Vestimenta** | Capa de viaje de paño oscuro de calidad sobre ropa de trabajo de cuero. Sin joyas —llama la atención. Un mercader de gemas sin joyas es alguien que no quiere ser un mercader de gemas. |
| **Objetos** | Libro de contabilidad con cifras en código Zhentarim. Llave del sótano de la posada (copia que nadie debería tener). Dos gemas reales como justificación de la historia si alguien registra la bolsa. |
| **Actitud inicial** | Pragmático. Pone precio a todo antes de hablar. Usa el silencio como oferta —espera a que el otro llene el vacío. |
| **Motivación** | Recuperar el cofre para los Zhentarim. Mantener el túnel operativo. Eliminar a Selvyn Drask del problema —aunque alguien se le adelantó. |
| **Secreto** | Dirigió la operación Zhentarim que vendió las posiciones del ramal norte del Paso hace cuatro años. Seis personas murieron, incluyendo la familia de Renwick Sorn. Lleva cuatro años esperando que eso no cruce el mismo pasillo que él. Esta noche cruzó. |
| **Qué sabe de otros** | Sabe que el cofre de Caelith fue abierto y reselado por su red en Neverwinter —conoce el contenido exacto. Sabe que Tamlin Pell es su peón: la deuda es un instrumento Zhentarim que él diseñó. |
| **Coartada** | En la sala común toda la noche —múltiples testigos. Sólida. Pero su reacción demasiado calmada a la noticia de la muerte de Selvyn es una pista emocional que los PJs con Perspicacia CD 13 pueden leer. |
| **Culpabilidad** | **6/10.** No mató a Selvyn esta noche. Pero construyó todas las condiciones para que alguien lo hiciera. Y lo que hizo en el ramal norte pesa más que esta noche. |

**Diálogos preparados:**

*Coopera:*
— «Un buen cofre. Sello de la Alianza. Vale más abierto que cerrado —eso ya lo sabéis.»
— «Os doy información sobre el túnel a cambio de que nadie abra ese libro de contabilidad. Es una oferta justa.»

*Neutral:*
— «El notario tenía una manera peculiar de hacer amigos. Eso le pasó.»
— «Los Zhentarim, los Harpers, la Alianza —todos cocinan en la misma grasa. Yo solo elijo la sartén.»

*Hostil:*
— «No sacáis nada acusándome sin prueba. Tengo tres testigos de que estuve aquí toda la noche.»
— «Ese cofre se abre o explota. La única variable es cuánto tiempo nos queda para elegir.»

*Bajo presión:*
— «¿El ramal norte? Eso fue hace cuatro años. Órdenes superiores, guerra activa, información incompleta.» *(Pausa.)* «No digo que esté bien. Digo que no es lo que ocurrió esta noche.»

*Si descubren su secreto:*
— «Seis personas. Sí. Las cartas tienen mi cifra, no mi nombre. Eso tiene diferente peso en un tribunal.» *(No dice más.)*

**Comportamiento con otros NPCs:**
- *Con Tamlin:* Lo usa como herramienta sin disimulo. Tamlin lo sabe. Ninguno de los dos menciona el arreglo.
- *Con Caelith:* Sabe lo que lleva. No le ha dicho que lo sabe. La observa con la paciencia de alguien que espera el momento correcto.
- *Con Renwick:* No lo reconoció al principio. En la Escena 3, cuando Renwick dice su nombre de familia, Durvis lo recuerda. Y es el único momento en que su cara cambia.

---

## ONNO GRIST — *Gnomo, «fray Onno de Ilmater»*

| Campo | Valor |
|---|---|
| **Físico** | Gnomo de cincuenta y cinco años con la energía de alguien que duerme menos horas de las que debería y se alimenta de conversación. Pelo blanco caótico que nunca está en el mismo lugar dos veces. Dedos negros en las yemas izquierdas —tinte de pólvora, no de tinta, aunque los confunde hábilmente. Sonríe con demasiados dientes para inspirar solo confianza. |
| **Vestimenta** | Hábito gris remendado de penitente de Ilmater, auténtico pero pequeño para él —heredado de alguien más alto. Símbolo de cadena rota al cuello, funcional. Una bolsa interior de cuero bajo el hábito que abombea de forma inconsistente con la vida de un fraile. |
| **Objetos** | Kit de «hierbas medicinales» que contiene tres cosas medicinales y seis que no lo son. Símbolo de Ilmater funcional. Un pequeño detonador de percusión remota que ya no tiene —lo activó en la Escena 4. Libro de deudas cifrado de los Cuervos de Mirtul bajo las costuras del hábito. |
| **Actitud inicial** | Habla en ráfagas, cambia de tema a mitad de frase, hace tres conversaciones simultáneamente. Parece inofensivo por exceso de presencia —nadie que planeara algo malo hablaría tanto. |
| **Motivación** | Los mapas del cofre. Solo los mapas. Venderlos en Luskan a dos compradores distintos antes de que alguien los reclame. Cobrar la deuda de Tamlin como pago parcial. Salir vivo de una posada cerrada con demasiada gente peligrosa. |
| **Secreto** | Es el agente de los Cuervos de Mirtul en el norte. Su «bendición del sótano» de la Escena 2 fue para instalar la trampa explosiva de seguridad. La activó remotamente en la Escena 4 para crear caos y evaluar las reacciones. No mató a Selvyn —pero tenía planificado un segundo uso para la trampa si Selvyn resultaba problemático para su misión. Alguien se adelantó. |
| **Qué sabe de otros** | Sabe que el túnel existe —lo descubrió en una visita anterior. Lo usa como palanca informal con Wenna sin haberlo mencionado explícitamente. Sabe que él mismo es el acreedor real de Tamlin Pell —la deuda es una operación de los Cuervos. |
| **Coartada** | En la sala común o en el corredor de arriba toda la noche. Sin movimientos al establo. Sólida. |
| **Culpabilidad** | **5/10.** Cómplice de las condiciones. La trampa explosiva era para «control de situación» y la activó en el peor momento posible. No es el asesino. Pero su concepto de daño colateral es flexible. |

**Diálogos preparados:**

*Coopera:*
— «¡Bendición para esta tormenta! Que es, en mi experiencia —¿habéis probado el estofado? Tiene algo que no es vaca— como os decía: los túneles de esta región son fascinantes desde un punto de vista estructural y espiritual simultáneamente—»
— «Sé quién hizo esto. Tengo parte de la evidencia. Pero la evidencia cuesta monedas, no moral.»

*Neutral:*
— «Ilmater carga el dolor del mundo. Yo cargo los mapas del dolor del mundo. Es parecido.»
— «El interés es por noche. La tormenta cuenta como dos.» *(A Tamlin, sin mirarle.)*

*Hostil:*
— «Explotar algo pequeño es una señal. Explotar algo grande es una respuesta. Espero que hayamos llegado a un entendimiento.»
— «No me acuséis de nada que no podáis probar en menos de una hora. Tengo un tren de pensamiento muy rápido y abogados en Luskan.»

*Bajo presión:*
— «La trampa era de seguridad general. Lo juro por Ilmater, que es decir mucho. No la instalé para Selvyn específicamente —la instalé para el concepto de Selvyn. Hay una diferencia.»

*Si descubren su secreto:*
— «Los Cuervos de Mirtul son una organización de comercio de información y recursos energéticos. La pólvora es un recurso energético. El fraile es un disfraz. Tamlin me debe quinientas monedas de oro que amablemente no menciono en voz alta. Todo esto es menos criminal de lo que parece si cambiáis de ángulo.»

**Comportamiento con otros NPCs:**
- *Con Tamlin:* El acreedor real. Lo trata con afecto genuino de la forma en que se trata a un instrumento favorito.
- *Con Lysse:* Sabe que ella le vendió explosivos. No lo menciona. Los dos se saben en situación de tablas.
- *Con Wenna:* El túnel le da palanca informal que usa con suavidad —no necesita decir que lo sabe; basta con que ella sepa que él sabe.

---

## CAELITH BRYNMAR — *Dracónida (plata), mensajera de la Alianza*

| Campo | Valor |
|---|---|
| **Físico** | Dracónida de escamas plateadas que en la luz de chimenea recogen el naranja y lo convierten en bronce. Treinta años —joven para su estirpe, lo que significa que alguien la envió porque era prescindible. Mandíbula cuadrada que aprieta cuando piensa. Las escamas del cuello se rizan hacia atrás involuntariamente cuando miente —solo si alguien la observa muy de cerca. |
| **Vestimenta** | Capa azul con broche de Lord —real. Cuero de viaje reforzado debajo. Botas con un compartimento sellado en el interior del muslo izquierdo que no menciona. |
| **Objetos** | Cofre de hierro con sello de lacre escarlata de la Alianza. Espada corta. Instrucciones de misión selladas en el bolsillo interior —ha dejado de releerlas porque ya sabe lo que dicen. |
| **Actitud inicial** | Formal hasta rozar la brusquedad. «Por mandato de la Alianza» como escudo. Ocupa siempre posición con la espalda a la pared. |
| **Motivación** | Completar la misión: entregar el cofre. Llegar viva. Ir a casa, si todavía sabe dónde queda. |
| **Secreto** | Abrió el cofre en Neverwinter, contra órdenes. Leyó las cartas. Su propio comandante de brigada está citado como fuente secundaria de información filtrada. No lo reportó porque reportarlo la haría desaparecer antes de que la misión terminara. Lleva cuatro días cargando esto. |
| **Qué sabe de otros** | Sospecha que Sira es Harper —su briefing la describe como «fricción tolerable.» No lo confirmó todavía. No lo ha confrontado porque no tiene instrucciones para eso. |
| **Coartada** | En la sala común con el cofre a la vista toda la noche —no puede separarse de él. Sólida. |
| **Culpabilidad** | **3/10.** Cómplice de sistema. No autor de ningún crimen esta noche. Pero lo que sabe y no dice tiene peso. |

**Diálogos preparados:**

*Coopera:*
— «Por mandato de la Alianza de los Lordes, solicito garantía de no interferencia. El cofre llega a Neverwinter intacto. Todo lo demás es negociable.»
— «Si me ayudáis a llegar al amanecer, tenéis mi palabra de que la Alianza no os debe nada. Eso vale más que una carta de agradecimiento.»

*Neutral:*
— «Lleváis tres preguntas de más en la cara. La cuarta os va a costar una explicación que no queréis dar.»
— «No soy vuestro enemigo. Vuestro enemigo es quien creéis que soy.»

*Hostil:*
— «Si abrís esto sin precaución, no moriréis heroicos. Moriréis feos y lentos. Una advertencia.»
— «El drow de la esquina lleva dos horas contando monedas encima de mi tumba. Preferiría que tuviera razón —al menos sería simple.»

*Bajo presión:*
— «No sé qué hay en el vial. Sé para qué lo usan. Eso es peor. Y aun así estoy aquí porque no tengo otro trabajo.»

*Si descubren su secreto:*
— «Sí. Lo abrí. Vi el nombre. No lo reporté porque reportarlo me habría matado antes que esta tormenta. La Alianza no perdona la inconveniencia del conocimiento. Elegid si eso me hace cómplice o superviviente.»

**Comportamiento con otros NPCs:**
- *Con Sira:* Desconfía instintivamente. No sabe que Sira es su escolta. La ironía la destruirá si alguien se lo dice.
- *Con Durvis:* No come nada que él haya servido o tocado. Sin explicación.
- *Con Lysse:* La aceptó como «la herbolaria» sin segundas lecturas. Eso la convierte en el único NPC que Lysse no tiene que manejar activamente.

---

## RENWICK SORN — *Tiefling, ex-soldado*

| Campo | Valor |
|---|---|
| **Físico** | Tiefling de treinta y dos años, cuernos en espiral larga hacia atrás —no los limó. La cicatriz en la mano derecha vendada tiene la forma exacta de una astilla de madera, no de un cuchillo. La mandíbula cuadrada mastica silencios con eficiencia. Cuando está en reposo, parece que está contando algo. |
| **Vestimenta** | Capa de viaje sin insignias. Cuero oscuro. Ballesta plegada en la mochila —desmontada pero accesible en treinta segundos. Un guantelete de cuero fino, solo en la mano izquierda. |
| **Objetos** | Ballesta desmontada. Bolsa de monedas que cuenta en voz baja como mecanismo de ansiedad. Una carta con el nombre «Durvis Hakk» escrita dentro —la lleva desde hace dos años. No la necesitaba. Ya llegó. |
| **Actitud inicial** | Pocas palabras. Frases como cuchilladas. No pide permiso para mirar a los ojos. Limpia las uñas con el cuchillo. Sardónico cuando habla, que no es frecuente. |
| **Motivación** | Durvis Hakk está en esta sala. La operación zhentarim que vendió las posiciones del ramal norte mató a su hermano mayor y a su familia. Lleva dos años siguiendo el rastro. La tormenta le regaló la jaula que buscaba. |
| **Secreto** | Cubrió a Borrakh Peñadiente después de un accidente que mató a tres hombres en un depósito militar. Lo hizo porque Borrakh le había dado su propia ración durante tres semanas cuando Renwick tenía fiebre en el campo. No se lo pidió. Renwick decidió que eso valía tres cadáveres. No está seguro de que fuera la cuenta correcta. |
| **Qué sabe de otros** | Sabe que Borrakh fue responsable del incendio del depósito —y que Borrakh lo sabe que él lo sabe. Esta es la deuda silenciosa entre ellos. |
| **Coartada** | Dice estar en la sala toda la noche. Parcialmente mentira —estuvo en la ventana este observando el patio. Llegó al establo DESPUÉS del crimen, no durante. Borrakh lo vio en la ventana (CD Perspicacia 14 para que Borrakh lo confirme si se le pregunta bien). |
| **Culpabilidad** | **4/10.** No mató a Selvyn. Pero estaba dispuesto a matar a alguien esta noche, y eso deja una huella de intención que los PJs pueden leer. |

**Diálogos preparados:**

*Coopera:*
— «Soy el tiefling de la historia. Ya sé lo que estáis pensando. Tenéis razón —sobre algunas cosas.»
— «Durvis Hakk dirigió una operación que mató a seis personas del ramal norte. Estoy aquí para hacer que lo diga en voz alta.»

*Neutral:*
— «No soy paladín. Solo soy alguien con una lista muy corta y una noche muy larga.»
— «Las monedas no son codicia. Son la cuenta atrás de alguien que todavía cree en la posibilidad de la justicia.»

*Hostil:*
— «Si me ponéis en el centro de esto sin prueba, os pido que lo hagáis bien. Porque si lo hacéis mal, os voy a demostrar que la primera vez no bastó.»
— «No busco al notario muerto. Al notario muerto me da igual. Buscad al que tiene el libro de contabilidad.»

*Bajo presión:*
— «Estaba en la ventana. Miraba el patio —buscaba a Durvis, no a Selvyn. Vi que había luz en el establo. No bajé porque la ballesta estaba en la mochila. Ese es el único motivo por el que Selvyn no fue mi problema esta noche.»

*Si descubren su secreto:*
— «Cubrí a Borrakh. Tres hombres muertos. Lo hice porque me había dado de comer cuando yo no podía darme de comer solo. Decidid si eso equilibra la cuenta. Yo llevo cuatro años sin llegar a conclusión.»

**Comportamiento con otros NPCs:**
- *Con Borrakh:* No pronuncia su nombre. Lo tiene localizado en todo momento.
- *Con Durvis:* Cuando Durvis habla, Renwick para de cualquier cosa que estuviera haciendo. Solo lo hace con él.
- *Con Lysse:* No la sospecha. Dejó que le examinara la mano herida. Error que no sabe que cometió.

---

## TAMLIN PELL — *Mediano (halfling), músico*

| Campo | Valor |
|---|---|
| **Físico** | Halfling de veinticuatro años, constitución de alguien que come irregularmente pero bien cuando puede. Ojos castaños rápidos que no se quedan quietos —hábito de apostador. Los pies descalzos dentro de las botas porque le ampollaron en las últimas dos jornadas. Toca la mandolina como si la estuviera interrogando. |
| **Vestimenta** | Jubón burdeos con tres remiendos de tela que no coinciden en color —los necesita pero no sabe coser bien. Capa corta con forro descosido. Botas que han visto más países que él. |
| **Objetos** | Mandolina con una cuerda remendada que da un tono ligeramente plano. Bolsa con menos monedas de las que hace sonar. Un documento de deuda con la firma «Onno Grist» que creyó que era de un prestamista de Luskan llamado de otra forma. |
| **Actitud inicial** | Todo banter, ninguna sustancia hasta que se le arrincona. Ofrece canciones antes de que nadie las pida. Invita a rondas que no puede pagar. Ríe antes de hablar en serio —mecanismo de defensa tan antiguo que ya no lo nota. |
| **Motivación** | Quinientas monedas de oro que debe. Onno Grist está en esta sala. La tormenta lo encerró con su peor pesadilla con hábito de fraile. Calcula si puede comprar su deuda entregando información sobre el cofre. |
| **Secreto** | Vio a Lysse Mourne salir de la cocina de madrugada con las manos mojadas. No lo dijo de inmediato porque no entendía qué significaba. En la Escena 3, cuando ve el cadáver, lo entiende. Y entonces tiene que decidir qué vale esa información. |
| **Qué sabe de otros** | Vio a Lysse en la cocina de madrugada con las manos mojadas. Sabe que Onno Grist es su acreedor real —lo descubrió comparando documentos. |
| **Coartada** | En la sala común cuando murió Selvyn —tocaba la mandolina, varios testigos. Sólida. |
| **Culpabilidad** | **4/10.** Cobarde, no asesino. Pero sabe lo que sabe desde la Escena 3 y no lo dice —ese silencio tiene peso y él lo siente. |

**Diálogos preparados:**

*Coopera:*
— «Os doy lo que sé. Gratis. Porque esa es la segunda opción más barata disponible esta noche.»
— «Dos cosas cuestan. Una: la información sobre la puerta de la cocina. Dos: que no diga a Onno que sé quién es. Precio especial si lo pagáis junto.»

*Neutral:*
— «El problema con los líos de dinero es que son como las canciones —siempre tiene más versos de los que recuerdas.»
— «No digo que confiéis en mí. Digo que soy el único en esta sala que no quiere nada del cofre.»

*Hostil:*
— «Si el gnomo sonríe cuando te explica la cláusula del contrato, revisad dónde teníais los dedos.»
— «Yo no mato. Yo... recomiendo a quién no invitar al día siguiente.»

*Bajo presión:*
— «Vi a la herbolaria salir de la cocina con las manos mojadas. Tarde. Noche. No dije nada porque no quería ser el siguiente. Eso me hace cobarde. No me hace asesino. Esa diferencia me importa más de lo que os parece.»

*Si descubren su secreto:*
— «Sí. El fraile es Onno Grist de los Cuervos de Mirtul. La deuda es su. Lo vi en el documento. No lo dije porque eso me habría hecho útil —y los útiles desaparecen deprisa en las noches así.»

**Comportamiento con otros NPCs:**
- *Con Onno:* Terror controlado. Lo llama «Hermano Grist» con una cortesía que le corta la respiración.
- *Con Lysse:* Desde la Escena 3 no puede mirarla directamente. Ella lo nota. Ella sabe que él sabe.
- *Con Durvis:* No sabe que es Zhentarim. Sospecha que es peligroso de la manera en que son peligrosas las personas que cuentan monedas ajenas.

---

## SIRA VELETH — *Drow, operativa Harper*

| Campo | Valor |
|---|---|
| **Físico** | Piel ébano, ojos violeta pálido que la luz de chimenea convierte en lavanda. Estatura media, casi delgada, pero los movimientos tienen la economía de alguien que sabe exactamente cuánta fuerza necesita cada cosa. La única señal de edad —docenas de años— son las manos: callos que no corresponden a un mercader de seda. |
| **Vestimenta** | Capa plateada sin marca de facción, capucha normalmente alta. Bajo la capa: ropa de trabajo funcional sin color. Sin equipaje ostensible en la sala común. |
| **Objetos** | Carta de tránsito Harper —encriptada, cosida en el forro de la capa. Dos cuchillos de trabajo que declararía como «instrumentos de corte de telas» (CD Percepción 16 para detectarlos). |
| **Actitud inicial** | Mínima. Mide cada palabra. Cuando habla, la gente para. Usa el silencio como puntuación. Frases enteras a veces sin sujeto. |
| **Motivación** | Escoltar el cofre de Caelith de forma encubierta hasta que cruce el paso. Destruir el vial de plaga. Exponer las cartas sobre Byrne. Y, en segundo plano, decidir qué hacer con Lysse Mourne ahora que sabe que es la asesina. |
| **Secreto** | Llegó con instrucciones secundarias de los Harpers: si encontraba a Lysse Mourne, evaluar si podía ser reincorporada o debía ser eliminada. Ahora Lysse acaba de matar a un hombre, y eso simplifica la decisión hacia un lado que Sira no estaba segura de querer tomar. |
| **Qué sabe de otros** | Sabe la identidad real de Lysse Mourne y que es la asesina de esta noche. Ha identificado a Durvis Hakk como el operativo zhentarim que los Harpers llevan tres años buscando. Sabe que Selvyn trabajaba para los Harpers, aunque Selvyn no lo supiera. |
| **Coartada** | En su silla en la sala común toda la noche. Múltiples testigos. Sólida. |
| **Culpabilidad** | **2/10.** La persona con menos sangre en las manos esta noche. La más odiada por apariencia. |

**Diálogos preparados:**

*Coopera:*
— «El hombre que abrió el cofre en Neverwinter trabajaba para los Zhentarim. Eso lo sabéis ahora. Lo que no sabéis: el notario muerto llevaba seis meses construyendo el caso para demostrarlo.»
— «Pedidme confianza mañana. Esta noche solo vendo hechos a cambio de que no me apuntéis nada.»

*Neutral:*
— «Menzoberranzan enseña que la superficie es ciega. Esta noche estáis demostrando el plan de estudios.»
— «La herbolaria salió por la cocina. Eso es un hecho.» *(Dicho en voz lo suficientemente alta para que todos oigan.)*

*Hostil:*
— «Matar un drow por el aspecto ahorra pensar. Es cómodo. Es también la razón por la que fracasan las alianzas.»
— «Acepté información sobre la dracónida. No para usarla en su contra —para que nadie más la usara peor.»

*Bajo presión:*
— «No bajé cuando oí los caballos. Calculé el coste de la cobertura antes de calcular el coste del notario. Ese orden me va a costar más que esta noche.»

*Si descubren su secreto:*
— «Sí. Sé quién mató a Selvyn. Sé por qué. Estaba evaluando si el coste de decirlo supera el beneficio. Esta sala me ayudó a decidir.»

**Comportamiento con otros NPCs:**
- *Con Caelith:* La protege sin que ella lo sepa. La ironía de que Caelith la tema no se le escapa.
- *Con Lysse:* La observa. Lysse lo sabe. Los dos esperan a ver quién parpadea primero.
- *Con Durvis:* Lo tiene identificado como objetivo primario desde hace cuatro horas. Espera el momento correcto para actuar.

---

---

# 4. UBICACIONES

---

## SALA COMÚN Y BARRA

El calor de la sala no viene de la chimenea sino de nueve cuerpos con secretos. La chimenea de piedra negra distribuye sombras que alargan todo lo que no debería alargarse —el martillo de Wenna detrás de la barra, la mochila que suena a metal de Borrakh, la bolsa demasiado abultada de Onno. La mesa de roble tiene una mancha antigua que nadie describe. La barra tiene botellas sin etiqueta que Wenna sirve con la misma cara para todo. El reloj de arena sobre la repisa lleva roto tres años; nadie lo quitó porque la posada funciona mejor sin que nadie sepa qué hora es exactamente.

**Secretos del Máster:**
- Tercera tabla del suelo: levantable (CD Investigación 15). Nicho con veneno de sombra —1 dosis, incoloro, inodoro.
- Botella sin etiqueta de Wenna: no es veneno. Es el licor del abuelo. «Para el día que alguien diga una verdad entera en este paso.»
- La nota de chantaje de Selvyn a Wenna sigue en el bolsillo del delantal si alguien la busca (CD Investigación 16 o registro físico con permiso).

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 10 Investigación | Mancha de sangre seca bajo la mesa —antigua, no de esta noche |
| CD 12 Investigación | Sello de la Alianza de los Lordes en el cofre de Caelith |
| CD 13 Perspicacia | Reacción de Durvis a la noticia de la muerte —demasiado calmada |
| CD 13 Perspicacia | Tamlin no puede mirar a Lysse directamente desde la Escena 3 |
| CD 15 Investigación | Tercera tabla del suelo, nicho con veneno |

---

## COCINA Y DESPENSA

Estrecha como un corredor de pesadilla, con ollas colgadas que oscilan sin viento visible. El fogón siempre encendido. El cubo de agua de la despensa tiene residuos de aceite de linaza en el borde —alguien se lavó las manos aquí esta noche. La estantería del corredor trasero está ligeramente desencajada, un centímetro, y los goznes de lo que hay detrás tienen aceite fresco que destella con la luz.

**Secretos del Máster:**
- La puerta oculta al establo está detrás de la estantería: mecanismo visible con CD 12 Investigación. Los goznes recién aceitados: CD 11 si se busca específicamente.
- El cubo de agua: aceite de linaza en el borde (CD 13 Investigación). Residuo que coincide con el aceite de los goznes.
- Puerta a la trampilla del sótano: al fondo de la cocina, detrás del hogar, oculta bajo leña apilada. CD 13 para encontrar el mecanismo, CD 14 para abrir sin llave.

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 11 Investigación | Goznes de la puerta oculta, recién aceitados |
| CD 12 Investigación | El panel detrás de la estantería —la puerta oculta |
| CD 13 Investigación | Aceite de linaza en el cubo de la despensa |
| CD 13 Investigación | Mecanismo de la trampilla al sótano bajo la leña |

---

## ESTABLO ANEXO

Cuatro pesebres. Heno húmedo de orina animal. El farol está apagado. Los caballos ya no se calman del todo. El cadáver de Selvyn Drask está contra la pared del tercer pesebre, los ojos abiertos, el cuadernillo todavía en la mano —abierto en una página en blanco, como si todavía tomara notas.

**Secretos del Máster:**
- Fibra de cuerda vegetal trenzada en el cuello: CD 13 Investigación. Corresponde a cuerda botánica de herbolario, no a cuerda de trabajo ni de mina.
- Olor residual herbal en los labios de Selvyn: CD 13 Medicina. «Infusión con componente sedante —camamilla de base, pero algo más amargo debajo.»
- Cuadernillo abierto en página en blanco: CD 14 Investigación para detectar la presión del bolígrafo de la hoja anterior —con carbón, puede leerse «L.M.»
- Tierras arcillosas rojizas en el suelo del tercer pesebre, distintas al barro del suelo: CD 12 Investigación. Solo se encuentran en el sistema de túneles.
- La trampilla al túnel bajo el tercer pesebre: CD 13 Investigación para encontrarla bajo el heno.
- El panel de la puerta oculta de la cocina, en la pared oeste: CD 11 Investigación para notar que está ligeramente desencajado desde dentro.

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 11 Investigación | Panel de la puerta oculta —lado establo, ligeramente desencajado |
| CD 12 Investigación | Tierra arcillosa rojiza del túnel en el suelo del tercer pesebre |
| CD 13 Investigación | Fibras de cuerda botánica en el cuello del cadáver |
| CD 13 Medicina | Olor sedante residual en los labios de Selvyn |
| CD 13 Investigación | Trampilla al túnel en el suelo del tercer pesebre |
| CD 14 Investigación | Impronta de «L.M.» en el cuadernillo (con carbón) |

---

## PISO SUPERIOR

Cinco habitaciones. Puertas que no cierran bien. Suelo de tablas que avisa de cada paso. La habitación 3 de Renwick tiene sangre en el tablón junto a la cama —de la herida en la mano, anterior al crimen. La habitación 5, al fondo este, tiene la ventana con rasguños en el alféizar exterior y pizarras movidas en la cubierta del establo (CD 14 Investigación desde dentro o desde el tejado).

**Secretos del Máster:**
- Ventana este de habitación 5: alféizar con rasguños recientes (CD 14 Investigación). Confirma uso de la ruta 3 (Renwick, antes del crimen).
- Habitación 2, Lysse: en la bolsa herbolaria, contar las cuerdas botánicas si los PJs lo piensan (CD 12 Investigación + acceso a la habitación). Falta una de calibre mediano —la que usó como garrote.
- Sangre de Renwick en habitación 3: de la herida en la mano, no relacionada con el crimen.

---

## EL SÓTANO OCULTO Y EL TÚNEL

Un nivel subterráneo completo bajo la cocina. Techo bajo, humedad de piedra, olor a pólvora y madera lacrada. La trampilla explosiva de Onno está ahora abierta y humeante. El contenido de los cajones zhentarim es visible para quien entre.

**Descripción del túnel:**
El túnel tiene 40 metros de longitud, suelo de tierra arcillosa rojiza (característica y reconocible), paredes de piedra sin acabar. Conecta la bodega de la posada con el tercer pesebre del establo (pasando por debajo) y continúa hasta una salida disimulada en la pared del barranco oriental, a 250 metros al este. Una cuarta ramificación, tapiada, apuntaba a las ruinas de un antiguo puesto del Paso.

**Evidencias en el túnel:**
- Tierra rojiza pisoteada en ambas direcciones (múltiples usuarios históricos).
- Fibra de cuerda botánica en el suelo del pasaje entre la bodega y el establo —del garrote de Lysse, caída al regresar (CD 13 Investigación).
- Un vial vacío de extracto de adormidera, tirado contra la pared —compuesto sedante que Lysse usó en la taza (CD 12 Investigación).
- El libro de deudas de Onno, escondido bajo una tabla suelta, inidentificable sin clave (CD 14 Arcana para descifrar parcialmente).

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 11 Investigación | Cajones zhentarim con sello, documentos cifrados |
| CD 12 Investigación | Vial vacío de extracto sedante de Lysse |
| CD 13 Investigación | Fibra de cuerda botánica en el pasaje establo |
| CD 14 Investigación | Mapa del sistema de túneles con cuatro salidas |
| CD 14 Arcana | Descifrado parcial del libro de deudas de Onno |
| CD 15 Investigación | Correspondencia Durvis-Luskan en los cajones |

---

---

# 5. GANCHOS DE PJ

*(Cuatro conceptos de personaje. Cada jugador elige uno o crea variante con el Máster.)*

---

## GANCHO 1 — El Testigo Incómodo

**Concepto:** Cualquier clase. Alguien que vio algo que no debería en Neverwinter y lleva semanas tratando de olvidarlo.

**Por qué está en la posada:** Huyendo hacia el norte. La tormenta lo cerró aquí antes de cruzar el paso.

**Secreto:** Vio a un oficial de la Alianza reunirse en las sombras con alguien en Neverwinter. No supo qué intercambiaron. Podría ser la transferencia de las cartas del cofre —o podría ser irrelevante. No puede saberlo sin verlas.

**Conexión oculta:** Wenna lo reconoció —el oficial que vio es Comandante Byrne, mencionado en las cartas. Wenna no lo dice de entrada, pero lo observa con más atención que al resto.

**Tentación:** Las cartas del cofre nombran al oficial. Si las usa, tiene poder sobre alguien poderoso. Si las destruye, se queda sin prueba y sin protección. Si las entrega a Renwick, alguien obtiene justicia y el PJ tiene un aliado improbable.

**Stake personal:** El oficial sabe que fue visto. Ya no es seguro para este PJ en ningún lado al sur del Paso.

---

## GANCHO 2 — El Deudor

**Concepto:** Cualquier clase con historia en el mundo criminal o político.

**Por qué está en la posada:** Transporta un paquete para los Cuervos de Mirtul —mensaje, objeto menor, promesa. Pago parcial de deuda. No sabía que su acreedor estaría aquí esta noche.

**Secreto:** La deuda es con Onno Grist. Cuando lo ve con el hábito de Ilmater, no sabe si reír o salir corriendo. Elige no hacer ninguna de las dos cosas, y eso es peor.

**Conexión oculta:** Tamlin lo reconoce de una sala de juego en Neverwinter. Tamlin nunca olvida una cara endeudada —hace que los suyos parezcan poca cosa.

**Tentación:** Onno le ofrece cancelar la deuda a cambio de los mapas del cofre. Solo los mapas. «Fácil. En realidad, bastante fácil, si pensáis en las alternativas.»

**Stake personal:** Si no paga en un mes, la deuda se activa de otra forma. Onno no dice de cuál forma. Esa vaguedad es el método.

---

## GANCHO 3 — El Soldado de la Guerra de la Corona

**Concepto:** Guerrero, paladín, explorador. Veterano con historia activa.

**Por qué está en la posada:** Viaja siguiendo un rumor sobre un arsenal enterrado bajo el Paso del Cuervo Blanco. Uno de los cuatro que marcan los mapas del cofre. No sabe que el cofre ya está aquí.

**Secreto:** Participó en la campaña donde se usó la plaga. No lo ordenó —lo vio. Y no lo reportó porque el oficial que lo ordenó le salvó la vida dos días antes. El nombre del oficial está en las cartas.

**Conexión oculta:** Renwick Sorn lo conoce —no de la guerra, sino del rumor que los trajo al mismo lugar. Renwick lo evaluó como aliado posible. La pregunta es si lo sigue siendo cuando salga el nombre del cofre.

**Tentación:** El vial de plaga es evidencia de algo que él tapó. Destruirlo lo salva. Entregarlo lo destruye. Dejarlo en manos de los Zhentarim es una tercera catástrofe.

**Stake personal:** Sira lo identificó en Neverwinter como testigo potencial de los crímenes de guerra. No lo dice, todavía.

---

## GANCHO 4 — El Mensajero Sin Mensaje

**Concepto:** Pícaro, explorador, monje. Alguien ágil con información parcial.

**Por qué está en la posada:** Llevaba un mensaje para Caelith Brynmar interceptado en Neverwinter. La destinataria ya está aquí, pero el mensaje no llega —alguien lo sustituyó por una copia falsificada. La copia la lleva este PJ sin saberlo.

**Secreto:** El mensaje real era de un alto oficial de la Alianza que avisaba a Caelith de que el cofre había sido comprometido en ruta. La copia falsa dice lo contrario. Alguien —probablemente Durvis— quería que Caelith llegara creyendo que el cofre estaba seguro.

**Conexión oculta:** Sira lo busca. Sabe que existe el mensaje original. No sabe que este PJ lleva la copia. Cuando lo descubra, la reacción de Sira dirá mucho sobre sus prioridades reales.

**Tentación:** Entregar el mensaje falso a Caelith da información sobre quién comprometió la ruta. Retener el mensaje da control del tablero. Venderlo a Durvis es oro y riesgo de muerte en ese orden exacto.

---

---

# 6. MECÁNICAS DE TENSIÓN — PBP ESPECÍFICO

---

## EL RELOJ DE SOSPECHA

**Qué es:** Una escala invisible de 0 a 10 que el Máster gestiona internamente. Cuando llega a 10, alguien hace algo que no puede deshacerse —una acusación sin prueba, una agresión, un intento de huida.

**Qué sube el reloj (+1 cada uno):**
- Un NPC miente y es sorprendido en la mentira
- Un PJ acusa a alguien sin prueba suficiente
- Alguien intenta abrir el cofre sin permiso de Caelith
- Un NPC revela información que implica a otro NPC
- El grupo se divide en dos facciones de sospecha claramente opuestas
- Cualquier acto de violencia física, aunque sea menor
- Un PJ usa Intimidación contra un NPC

**Qué baja el reloj (–1 cada uno):**
- Un PJ protege activamente a un NPC vulnerable
- Alguien consigue que dos NPCs hostiles hablen sin violencia
- Un PJ comparte información con la sala sin ventaja personal visible

**Efectos por nivel:**
- **0–3:** Hostilidad controlada. Los NPCs mienten con elegancia.
- **4–6:** Las máscaras se agrietan. Los NPCs cometen errores verbales.
- **7–8:** Dos NPCs se acusan mutuamente. La sala toma partido.
- **9:** Lysse intenta salir por la cocina hacia el túnel. Si nadie lo nota, llega al sótano.
- **10:** Standoff. Activar Escena 5 inmediatamente.

---

## SISTEMA DE ZONAS

| Zona | Tono | Quién suele estar aquí | Pistas disponibles |
|---|---|---|---|
| **Sala común** | Vigilancia mutua, tensión social | Todos los NPCs de mesa | Cofre, reloj roto, tabla del suelo, deudas visibles |
| **Cocina** | Territorio neutro con secretos propios | Wenna, Lysse (después del crimen) | Puerta oculta, cubo de agua, trampilla del sótano |
| **Piso superior** | Privado, crujidos, puertas que no cierran | Renwick, Caelith, Lysse (su habitación) | Sangre de Renwick, ventana este, bolsa herbolaria de Lysse |
| **Establo** | Oscuro, frío animal, muerte | Nadie (después del crimen) | Cadáver de Selvyn, fibras botánicas, tierra del túnel, trampilla |
| **Sótano** | Claustrofóbico, húmedo, revelaciones | Nadie hasta Escena 4 | Túnel de contrabando, vial sedante de Lysse, cajones zhentarim |

**Para posts PBP:** El Máster describe qué siente el personaje al entrar a cada zona antes de que el jugador declare acción. Esto establece ritmo y permite que el jugador reaccione al ambiente antes de actuar.

---

## CÓMO MANEJAR POSTS DE INVESTIGACIÓN

**Principio base:** El jugador que investiga bien recibe información confirmada, no solo resultado de dado. El dado determina cuánto, no si algo existe.

**Protocolo:**
1. El jugador describe la acción concreta («examino el cadáver buscando marcas en el cuello»).
2. El Máster determina la CD relevante y la declara.
3. **Éxito:** El Máster da la pista directamente como hecho narrativo. «Las marcas en el cuello son de cuerda vegetal trenzada —fibra botánica, no de trabajo. El herbolario que la vende la reconocería al primer vistazo.»
4. **Fallo:** El Máster da información incompleta o ambigua. «El cuello tiene marcas de presión, pero la iluminación del establo no permite determinar el material del instrumento.»
5. **Éxito crítico (5+ sobre CD):** El Máster añade una pista bonus no solicitada. «Además, nota un olor residual en los labios del cadáver —herbal, amargo. Como si hubiera bebido algo en los últimos minutos antes de morir.»

**Nunca:** «Fallas la tirada, no encuentras nada.» Siempre hay algo que encontrar; el dado determina qué tanto.

---

## PROTOCOLO DE STANDOFF MEXICANO — ESCENA 5

**Formato de un solo post:**

El Máster escribe la descripción del momento de silencio con todas las armas a la vista. Luego cada jugador escribe UN post con:
- **Posición:** Dónde está su personaje físicamente.
- **Arma:** Qué tiene en la mano o preparado.
- **Objetivo:** A quién apunta o vigila.
- **Línea:** Lo que dice en voz alta en este momento.

El Máster resuelve en un post de narración que toma en cuenta todas las declaraciones simultáneamente. No hay iniciativa. No hay rondas. Es cine.

**Regla de oro:** Si un jugador declara ataque, el objetivo puede declarar respuesta en réplica antes de que se resuelva el daño. Un solo intercambio. Luego resolución simultánea.

---

## RECOMPENSAR LA DEDUCCIÓN

**Cuándo un jugador conecta dos pistas correctamente:**
El Máster confirma la deducción narrativamente, no con un dado. «Sí, la fibra botánica del cuello y la cuerda que falta en la bolsa de Lysse coinciden. Eso es un hecho.»

**Cuándo un jugador llega a una conclusión incorrecta pero plausible:**
El Máster no la contradice directamente —planta una pista que la complica. El jugador llegará solo a la corrección.

**Cuándo un jugador hace la pregunta correcta al NPC equivocado:**
El NPC responde desde su perspectiva incompleta. Eso es información también. La sala tiene acceso a versiones parciales de la verdad; la deducción es ensamblar versiones.

---

---

# 7. REFERENCIA RÁPIDA — UNA PÁGINA

---

## MATRIZ DE CULPABILIDAD

| NPC | Parece culpable de… | Culpabilidad real | Coartada | Secreto clave |
|---|---|---|---|---|
| Wenna Corren | Encubrir al asesino, saber del túnel | **5/10** — Conocía la identidad de Lysse, no dijo nada | En la barra toda la noche — sólida | Consintió el túnel zhentarim; sabía que Lysse era renegada |
| Selvyn Drask | N/A — víctima | **1/10** | N/A | Trabajaba para los Harpers mientras chantajeaba |
| Borrakh Peñadiente | Asesinato; huellas en establo; pasado violento | **3/10** — Encontró el cadáver y calló | Estuvo antes del crimen — frágil por omisión | Incendio del depósito cubierto por Renwick |
| Lysse Mourne | Aparentemente nada — «solo la herbolaria» | **10/10** — **LA ASESINA** | «Arriba toda la noche» — MENTIRA; Tamlin la vio; cuerdas que faltan | Ex-Harper renegada; mató con sedante + cuerda botánica; usó el túnel |
| Durvis Hakk | Todo lo relacionado con el cofre; reacción calmada | **6/10** — Construyó las condiciones; ramal norte | En sala toda la noche — sólida | Operativo Zhentarim; ramal norte; cofre comprometido |
| Onno Grist | Trampa explosiva; identidad falsa; movimientos sospechosos | **5/10** — Cómplice indirecto; trampa era general | En sala o corredor — sólida | Cuervos de Mirtul; acreedor de Tamlin; trampa de seguridad propia |
| Caelith Brynmar | «Trajo la plaga»; tensión con todos | **3/10** — Cómplice de sistema; no crimen de esta noche | Con el cofre en sala — sólida | Abrió el cofre; su comandante está en las cartas |
| Renwick Sorn | Estuvo en zona de acceso; herida; dos nombres en el cuadernillo | **4/10** — Buscaba a Durvis, no a Selvyn; llegó después | «En sala toda la noche» — PARCIALMENTE MENTIRA; ventana este | Cubrió el incendio de Borrakh; buscaba a Durvis Hakk |
| Tamlin Pell | Vende información; en deuda; movimientos nocturnos | **4/10** — Cobarde que sabe demasiado desde la Escena 3 | En sala tocando — sólida | Vio a Lysse con las manos mojadas |
| Sira Veleth | Drow con posibles contratos; no habla; sin equipaje | **2/10** — La persona menos culpable de la sala | En silla en sala — sólida | Harper activa; sabe quién es la asesina desde la Escena 3 |

---

## RASTREADOR DE PISTAS FALSAS

| Pista | Apunta a… | Verdad |
|---|---|---|
| Borrakh en el establo antes del crimen | Borrakh como asesino | Llegó a revisar su yegua; encontró el cadáver; calló por miedo a ser primer sospechoso |
| Reacción calmada de Durvis a la muerte | Durvis como asesino o cómplice | Durvis quería a Selvyn vivo y controlado; muerto es más difícil de gestionar |
| Renwick en la ventana este | Renwick usando la ruta del tejado para el crimen | Renwick observaba el patio buscando a Durvis |
| Onno activo y nervioso en Escena 4 | Onno como cómplice del crimen | Va hacia su trampa propia, no al escenario del crimen |
| Lysse examina el cadáver voluntariamente | Lysse como persona sin nada que ocultar | Controla qué información se revela desde la «pericia médica» |
| Cuadernillo de Selvyn con tres nombres | Tres sospechosos obvios | El cuarto nombre (L.M.) fue destruido por la asesina |

---

## LISTA DE CDs CLAVE

| CD | Acción | Pista o resultado |
|---|---|---|
| CD 10 Investigación | Sala común, tabla del suelo | Mancha de sangre antigua, no de esta noche |
| CD 11 Investigación | Cocina, goznes puerta oculta | Aceite de linaza fresco —usada esta noche |
| CD 11 Medicina | Observar a Renwick | Vendajes en la mano derecha, herida reciente |
| CD 12 Investigación | Cofre de Caelith | Sello de la Alianza de los Lordes |
| CD 12 Investigación | Suelo del tercer pesebre | Tierra arcillosa rojiza del túnel |
| CD 12 Investigación | Establo, pared oeste | Panel de la puerta oculta, ligeramente desencajado |
| CD 12 Investigación | Sótano | Vial vacío de extracto sedante de Lysse |
| CD 13 Perspicacia | Observar a Tamlin desde Escena 3 | Incapaz de mirar a Lysse directamente |
| CD 13 Perspicacia | Observar a Durvis, noticia de la muerte | Reacción demasiado neutral para alguien que tiene motivo |
| CD 13 Investigación | Establo, cuello de Selvyn | Fibras de cuerda botánica herbolaria |
| CD 13 Medicina | Examinar labios de Selvyn | Olor residual sedante —bebió algo en los últimos minutos |
| CD 13 Investigación | Establo, suelo del tercer pesebre | Trampilla al túnel bajo el heno |
| CD 13 Investigación | Cocina, cubo de agua | Aceite de linaza en el borde —alguien se lavó las manos |
| CD 14 Investigación | Establo, cadáver de Selvyn | Huella de bolígrafo en cuadernillo —con carbón, «L.M.» |
| CD 14 Investigación | Ventana este, habitación 5 | Rasguños en alféizar exterior; pizarras movidas |
| CD 14 Investigación | Sótano, cajones | Mapa del sistema de túneles con cuatro salidas |
| CD 14 Arcana | Libro de Onno bajo tabla suelta | Descifrado parcial de las cuentas de los Cuervos de Mirtul |
| CD 15 Investigación | Sala común, tercera tabla del suelo | Nicho con veneno de sombra |
| CD 15 Investigación | Sótano, cajones zhentarim | Correspondencia Durvis-Luskan |
| CD 16 Perspicacia | Observar a Lysse, bolsa herbolaria | Número de cuerdas botánicas —una de calibre medio falta |

---

## INTERESES DE FACCIONES EN EL COFRE

| Facción | Quiere | No quiere que ocurra |
|---|---|---|
| **Alianza de los Lordes** (Caelith) | Recuperar vial + mapas + destruir cartas | Que las cartas se lean en voz alta |
| **Zhentarim** (Durvis) | Vial de plaga + mapas | Que el vial se destruya; que el túnel se cierre |
| **Cuervos de Mirtul** (Onno) | Solo los mapas (para revender × 2) | Que alguien abra el cofre sin él delante |
| **Harpers** (Sira) | Destruir el vial. Exponer las cartas | Que el vial llegue al mercado negro |
| **Renwick Sorn** (personal) | Las cartas específicamente —nombran a Byrne | Que las cartas desaparezcan sin proceso judicial |
| **Lysse Mourne** (personal) | Salir viva de la posada con identidad intacta | Que alguien conecte la cuerda botánica con su bolsa |

---

## ACCESOS AL ESTABLO — RESUMEN OPERATIVO

| Ruta | CD acceso | Usada por | Evidencia que deja |
|---|---|---|---|
| Puerta principal del patio | Sin CD | Selvyn (víctima), Borrakh (antes crimen) | Barro en umbral; difícil con ventisca |
| Puerta oculta cocina–establo | CD 12 Investigación para encontrar | Lysse (asesina, ida esta noche) | Goznes aceitados; panel desencajado |
| Ventana este piso superior | CD 12 Atletismo para usar | Renwick (antes crimen, solo observación) | Rasguños en alféizar; pizarras movidas |
| Túnel sótano–tercer pesebre | CD 13 Investigación para encontrar trampilla | Lysse (asesina, regreso por aquí) | Tierra arcillosa rojiza; vial sedante; fibra botánica |

---

*Fin del documento. El cuervo blanco del umbral sigue en su poste. Nadie sabe si graznó durante la noche.*
