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
- Un PJ inspecciona la cocina y encuentra la puerta oculta detrás de la estantería entreabierta (CD Investigación 12). Los goznes no crujen —están recién aceitados. Si busca específicamente los goznes (CD 11 Investigación), el aceite de linaza es tan fresco que destella.
- Un PJ registra la habitación 2 (Lysse) con su permiso o por acceso independiente: en la bolsa herbolaria falta un vial pequeño (CD 12 Investigación). Lysse, si se le pregunta, explica sin vacilar: «Se lo presté a Renwick para la inflamación de la mano.» Renwick, si se le consulta directamente, lo niega con calma: «Me ofreció algo. Lo rechacé. No tomo nada de extraños.» La coartada de Lysse sobre el vial colapsa ante cualquier confrontación cara a cara.
- Tamlin intenta venderle a un PJ información sobre el sello del cofre. Pide tres monedas de oro.
- Durvis le susurra algo a Caelith que la hace apretar la mano sobre el cofre. Caelith niega que ocurrió algo si se le pregunta.
- Borrakh revisa sus herramientas de herrero en la mochila. El sonido de metal es inconfundible.
- Un PJ con CD 14 Perspicacia que observe a Wenna y Lysse en el mismo campo visual nota algo inusual: las dos mujeres nunca se dirigen la palabra ni se miran directamente, aunque Wenna pasa cerca de Lysse al repartir bebidas. La sincronía del no-contacto es demasiado ordenada para ser indiferencia natural entre desconocidas. No es evidencia —todavía. Es una nota mental.

### CIERRE DE ESCENA (CONTROLADO POR EL MÁSTER)
Un sonido de algo pesado arrastrado en el piso de arriba —una vez, con esfuerzo, y luego nada. Luego: drip. Drip. Drip. El líquido oscuro sigue cayendo del techo sobre la mesa, pero ahora hay más. Una tabla del techo cruje. Algo cae al suelo arriba. Silencio total desde la planta superior. Luego, con una calma pasmosa, Selvyn Drask pasa por la sala en dirección a la cocina con el cuadernillo bajo el brazo. Sonríe al pasar. Nadie sabe a dónde va. → Avanzar a Escena 3.

---

## ESCENA 3 — «El trabajo de la noche»
**Función dramática:** EL ASESINATO. Selvyn muere durante esta escena. La sala se convierte en un tribunal improvisado donde el culpable real conduce la acusación porque así cierra el círculo.

### QUÉ DEBE OCURRIR
- Un grito cortado llega del establo. Los caballos patean. No es el viento.
- Selvyn yace desplomado contra la pared del tercer pesebre con traumatismo contuso en la sien derecha. Ojos abiertos. En la mano todavía aprieta el cuadernillo, abierto en una página en blanco. Primer diagnóstico obvio: una coz. No debería haber estado aquí de noche.
- **Pista 1 — FÁCIL:** El ángulo de la herida no corresponde a una coz de caballo. Las coces viajan en horizontal o hacia arriba; esta herida impactó desde arriba y ligeramente por detrás, consistente con un golpe en arco descendente. Cualquiera con entrenamiento en Medicina lo nota de inmediato. (CD 10 Medicina.) → Elimina el accidente. Confirma asesinato. No apunta a nadie todavía.
- **Pista 2 — FALSA PISTA → Borrakh:** Huellas de bota grandes en el heno junto al cuerpo —talla de medio-orco. (CD 11 Investigación, heno.) → Apunta inicialmente a Borrakh. Investigando más (CD 13 Investigación): dos series de huellas distintas —las grandes son más antiguas y lineales (Borrakh, puerta↔cuerpo); las medianas son más recientes y emergen desde el panel de la pared oeste (Lysse, esta noche). Borrakh, bajo presión: «Lo encontré. Lo toqué. No lo maté.»
- Borrakh aparece desde la puerta principal del establo, mojado. Dice que comprobaba su caballo. La sala lo mira como a lo que parece.
- Lysse se ofrece a examinar el cadáver. Lo hace con calma metódica. Anuncia «traumatismo, posiblemente una coz» sin vacilar. No menciona el olor a sedante en los labios que ella misma reconocería.

### QUÉ PUEDE OCURRIR
- Un PJ con Medicina CD 13 detecta un residuo amargo y sedante en los labios de Selvyn —herbal, no alcohólico. Compuesto inductor del sueño, identificable para alguien con conocimiento herbolario o médico. (**Pista 3 — MEDIA.**) Lysse, si está presente, dice: «Infusión de camomila. La vendí yo. Le ayudaba con los nervios.» Verdad a medias.
- Si los PJs acusan a Borrakh, Renwick dice en voz alta: «Estuvo fuera diez minutos. Lo conté.» Borrakh lo mira. No dice gracias.
- Si los PJs inspeccionan el cuadernillo, ven tres nombres: Wenna Corren, Renwick Sorn, Durvis Hakk. Todos en la sala. La cuarta entrada está en blanco pero la página tiene la presión del bolígrafo de la hoja anterior. Con carbón frotado sobre la página puede leerse: «L.M. — 2ª campanada.» (**Pista real — DIFÍCIL**, CD 15 Investigación.)
- Tamlin no puede mirar a Lysse desde que entró al establo. Si un PJ construye confianza con él fuera del grupo (Persuasión CD 12, Escena 3 o posterior) o lo encuentra a solas: «Estaba en la cocina. Tarde. Antes del grito. Lavándose las manos. La cara completamente normal. Eso es lo que recuerdo.» (**Testigo clave — la pista por conversación más importante.**)
- Sira, desde el umbral del establo, sin que nadie se lo pida: «El único que salió por la cocina esta noche fue alguien que conocía la puerta. Eso recorta la lista.»
- Un PJ con CD 13 Perspicacia que observe a Wenna cuando se anuncia la muerte nota lo siguiente: no hace las preguntas que hace todo el mundo. No pregunta «¿quién lo encontró?» ni «¿cuándo fue?». Pregunta si el establo está cerrado ahora. Solo eso. Es la pregunta de alguien que ya sabe lo que pasó y quiere saber si la ruta está comprometida.
- **Falsa pista → Durvis:** La tierra arcillosa rojiza en el suelo del tercer pesebre (CD 12 Investigación) apunta al túnel —Durvis tiene la llave. Pero la tierra está seca y endurecida: tráfico histórico zhentarim, no pisadas de esta noche. Las huellas frescas llegan desde el panel de la pared oeste. Wenna, si se presiona: «Durvis lleva tres años usando ese túnel. La arcilla siempre estuvo ahí.»
- **Falsa pista → Renwick:** En el piso superior, la ventana este (hab. 5) muestra escarcha alterada en el alféizar exterior (CD 12 Investigación) y pizarras desplazadas en la cubierta del establo (CD 13 Investigación). Parece que alguien bajó al establo por esta ruta. Pero Renwick estaba allí vigilando el patio buscando a Durvis —no descendió al establo. Borrakh lo vio en la ventana antes del grito (CD 14 Perspicacia a Borrakh).

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
- Lysse, si no ha sido detenida, intenta salir por la puerta oculta de la cocina hacia el establo y de ahí al exterior. Si el grupo lo nota (Percepción CD 11), se para. Si no, Wenna anuncia cuando ya tiene la mano en el panel de la estantería.
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

**La tarde del día (después de las notas de chantaje):** Wenna Corren recibe la nota de Selvyn en el delantal —no es la primera vez que alguien la amenaza con el túnel, pero esta vez el papel tiene fecha y firma real de notario. La nota de Selvyn, escrita con la eficiencia arrogante de alguien que cree tenerlo todo bajo control, también le pide que «mantenga el establo libre esta noche para tres reuniones privadas, de la primera a la tercera campanada». Selvyn la usa como herramienta de logística mientras la chantajea. Wenna ha estado observando a Selvyn circular por la sala con su cuadernillo toda la tarde: ha visitado a Renwick, a Durvis, y le acaba de entregar la nota a ella. La única persona de la sala de la que sabe que Selvyn tiene algo —porque lleva tres años con ese informe Harper guardado— es Lysse Mourne. Ata los cabos. Selvyn está a punto de cometer el mismo error que ya cometió con ella. Bajo la excusa de revisar el corredor trasero de la cocina, Wenna unta los goznes de la puerta oculta al establo con aceite de linaza de su frasco personal —el que lleva una «W» grabada en el corcho. Después busca a Lysse con la excusa de ofrecerle más infusiones para la sala y le murmura, sin mirarla, sin parar de moverse: la hora de la cita de Selvyn en el establo («segunda campanada»), el acceso por la puerta oculta de la cocina, que los goznes ya están listos. Lysse escucha. No pregunta nada. Antes de subir a su cuarto, le pasa a Wenna una nota doblada: «Entendido. Esta noche.» Wenna la quema esa misma tarde en la chimenea de la sala común. Casi del todo.

**Hora segunda (noche temprana):** Selvyn le comunica a Lysse la hora de su cita en el establo: «La segunda campanada. Venid sola. Si no venís, el informe sobre vuestra identidad Harper llega a Skullport mañana por la mañana.» Lysse no dice nada. Se va a preparar infusiones en la cocina. Entre la cocina y su cuarto, comprueba la puerta oculta al establo —los goznes ya están lubricados, como le indicó Wenna. No tiene que hacer nada más.

**Antes de las dos campanadas:** Lysse va a la cocina con la excusa de preparar una tisana para «el herido del tercer cuarto» —Renwick. Nadie lo verifica en el momento. (Si alguien pregunta a Renwick después: ofreció, él rechazó.) En la cocina, prepara una taza con extracto de adormidera y verbena sedante usando materiales de su bolsa herbolaria. El residuo del compuesto queda en el cubo de la despensa cuando se limpia. Sale al establo por la puerta oculta de la estantería con la taza. Deja la taza en el poste del tercer pesebre donde Selvyn la encontrará. Se retira al cuarto pesebre a esperar.

**Las dos campanadas:** Selvyn entra al establo por la puerta principal del patio. Encuentra la taza. La bebe —es amarga, pero no más que su té habitual. Lysse sale del hueco del cuarto pesebre. La conversación dura tres minutos. Selvyn empieza a sentir los brazos pesados en el minuto cuatro. En el minuto seis, Lysse descuelga el cubo de madera del gancho del tercer pesebre y lo usa: golpe único, descendente, contra la sien derecha cuando Selvyn ya no puede defenderse. El trabajo dura tres segundos. Los caballos se agitan. Lysse vuelve a colgar el cubo en su gancho —queda levemente húmedo en el borde, con residuo verdoso herbal transferido de sus manos. Pone el cuadernillo en la mano del cadáver —abierto en la página en blanco, como si todavía estuviera tomando notas. Destruye la cuarta nota del cuadernillo. Sale por la puerta oculta de la estantería de vuelta a la cocina. Tarda cuatro minutos por el pasillo de 4m.

**Justo después:** Borrakh, que había bajado por la puerta principal del establo a revisar su yegua una hora antes, vuelve a pasar —oyó los caballos. Encuentra el cadáver. Lo toca para saber si respira. Se limpia la mano en el heno. Sale sin gritar porque no quiere ser el primer sospechoso. No grita. Se va a la sala común.

**Tres minutos después:** Tamlin sube a la cocina a buscar agua. Encuentra a Lysse lavándose las manos en el cubo de la despensa. Ella dice: «No podía dormir.» Tamlin asienta y no dice nada. La cara de Lysse es completamente normal. Eso es lo que Tamlin recordará.

**Poco después:** El grito llega desde el establo. Alguien que salió a buscar a Selvyn encontró el cuerpo. El grupo baja.

---

## LOS ACCESOS AL ESTABLO — CUATRO RUTAS DOCUMENTADAS

| Ruta | Descripción | Quién la usó esta noche | Evidencia que deja |
|---|---|---|---|
| **1. Puerta principal del patio** | Puerta de madera norte del establo, da al patio interior cubierto de nieve | Selvyn (víctima), Borrakh (antes del crimen) | Barro en el umbral; huellas en el patio si hay luz; difícil con ventisca |
| **2. Puerta oculta cocina–establo** *(superficie)* | Panel detrás de la estantería del corredor trasero de la cocina; pasillo de 4m a nivel de suelo hasta la pared lateral del establo. Sin subsuelo. Goznes aceitados por **Wenna Corren** durante la tarde con su frasco personal de aceite de linaza (marcado «W» en el corcho). | Lysse (asesina, ida y vuelta esta noche) | Ligero desencaje del panel (CD 11 Investigación); aceite fresco en goznes (CD 11); frasco de aceite marcado «W» en el corredor trasero (CD 13 Investigación); residuo herbáceo verdoso en cubo de la cocina (CD 13 Investigación) |
| **3. Ventana este del piso superior** | Ventana de la habitación 5; da a la cubierta de pizarra del establo; salto de 2,5m hasta el heno interior (Atletismo CD 12) | Renwick (antes del crimen, solo para observar el patio) | Escarcha alterada en alféizar exterior (CD 12 Investigación); pizarras movidas en la cubierta (CD 13 Investigación) — falsa pista; Renwick estaba observando el patio, no bajó |
| **4. Túnel de contrabando** *(subterráneo — distinto de Ruta 2)* | Desde la bodega oculta bajo la cocina → conducto subterráneo de 40m → emerge en el suelo del tercer pesebre. Infraestructura zhentarim. **No usada esta noche.** | Nadie esta noche (uso histórico de Durvis y su red) | Tierra arcillosa rojiza en el suelo del tercer pesebre (uso histórico, no de esta noche); trampilla encontrable bajo el heno (CD 13 Investigación) |

---

## EL CELLAR OCULTO — GUÍA DEL MÁSTER

**Acceso:** Trampilla de piedra detrás del hogar de la cocina, disimulada bajo una pila de leña. Requiere mover la leña (visible) y encontrar el mecanismo de palanca (CD 13 Investigación). Durvis Hakk tiene una llave para la cerradura inferior; sin llave, CD 14 para abrir con ganzúa.

**Contenido:**
- Veinte cajones de madera lacrada con sello zhentarim: documentos falsos, cartas de crédito, dos espadas cortas sin marcar, un frasco de veneno no identificado.
- Correspondencia entre Durvis y dos contactos en Luskan —escrita en cifra zhentarim estándar (CD Arcana 15 para descifrar sin clave).
- Mapa de las cuatro salidas del túnel: la cocina de la posada, el establo (tercer pesebre), una salida al barranco oriental (a 250m), y una entrada tapiada que apuntaba a las ruinas de un antiguo puesto del Paso.
- Marcas de uso histórico en el suelo del pasillo del túnel —pisadas múltiples en distintas direcciones, ninguna reciente (CD 13 Investigación).
- Una pequeña carga de pólvora negra con detonador de percusión instalada por Onno Grist —trampa de seguridad que activó de forma remota durante la Escena 4 para crear distracción.

**Quién sabe que existe:**
- Durvis Hakk: lo construyó, lo usa, lo mantiene.
- Wenna Corren: consintió su construcción a cambio de dinero. Lo lamenta.
- Onno Grist: lo descubrió durante una estancia anterior y colocó su trampa sin decírselo a nadie.
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
| **Wenna Corren** | El túnel es suyo; Selvyn la chantajeaba; «calma excesiva» | **NO es una pista falsa —es cómplice activa.** Wenna no ejecutó el asesinato, pero le dio a Lysse la hora de la cita, preparó el acceso y lubricó los goznes. Acusarla no conduce a un callejón: conduce a la segunda capa de la verdad. |
| **Onno Grist** | Acceso al sótano; trampa explosiva propia; activo y nervioso en Escena 4 | La trampa era de seguridad general, no relacionada con Selvyn. Onno solo mata conceptos, no personas. |

---

## EL GIRO — LA REVELACIÓN QUE RECONTEXTUALIZA TODO

**La revelación:** En la Escena 4, si los jugadores presionan a Sira Veleth, esta revela que Selvyn Drask no era solo un extorsionista. Llevaba seis meses construyendo un expediente para los Harpers —un caso real, con pruebas reales, contra la red zhentarim de Durvis. El chantaje era su mecanismo de protección: si alguien lo mataba antes de entregar el expediente, las notas automáticas en el archivo de Neverwinter se abrirían solas. O eso creía él. Lysse lo sabía. Y sabía que Selvyn había mentido sobre el sistema de respaldo —no existía.

**Lo que esto cambia:** Selvyn no era solo el villano de la noche. Era el único que estaba construyendo el caso que Renwick lleva dos años necesitando. Su muerte no es solo un asesinato —es el cierre de la única línea de acusación válida contra Byrne. Y Lysse lo sabía. Calculó cuánto valía el expediente versus cuánto le costaba su supervivencia. El expediente perdió.

**La pregunta que se queda en la sala:** Lysse mató a alguien despreciable que hacía algo importante. ¿Cuánto pesa eso? ¿Y cuánto pesa que una mujer que solo quería que su posada sobreviviera abrió la puerta para que pasara?

**La segunda capa de la revelación:** Lysse no actuó sola. Wenna Corren —la posadera, la mujer más neutral de la sala, la que servía copas y llamaba a todos «viajero»— fue quien le dio a Lysse las herramientas para hacerlo posible: la hora exacta de la cita, el acceso preparado, los goznes sin crujido. No dio ninguna orden. Pero las decisiones que tomó esa tarde convirtieron la posibilidad de un asesinato en su logística. Si los jugadores descubren ambas capas, la pregunta moral se duplica: no es solo si Lysse tenía razón en lo que hizo. Es si Wenna tenía razón en abrir esa puerta. Y si «abrir una puerta» y «ordenar una muerte» son la misma cosa cuando sabes exactamente qué va a pasar después.

**Cómo llegó Sira a su conclusión (parcial):** Sira no vio a Lysse desde la sala común —el establo es invisible desde allí. Lo que sabe tiene tres fuentes: (1) Lysse no estaba en la sala cuando los caballos gritaron —la ausencia es un hecho, no una suposición; (2) Tamlin la vio en la cocina de madrugada, lavándose las manos, antes de que encontraran el cadáver; (3) Sira inspeccionó la posada en silencio durante la noche y encontró la puerta oculta de la cocina con los goznes recién aceitados. Con estos tres vectores, la conclusión sobre Lysse es directa. **Lo que Sira no cierra sola:** quién preparó los goznes, quién le dio la hora a Lysse, y por qué la puerta ya estaba lista antes de que Lysse la buscara. Para llegar a Wenna, los PJs necesitan el fragmento quemado de la chimenea (Pista Cómplice A) y la nota bajo la barra (Pista Cómplice B), o bien confrontar a Wenna con la evidencia combinada hasta que la coartada de «no supe nada» no sostenga el peso. Lo que Sira no dice hasta que la presionan: también sabe que Selvyn estaba construyendo el expediente, y eso hace la ecuación moral imposible de cerrar en limpio —incluso sabiendo que hay dos culpables.

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
| **Motivación** | Llegar al amanecer sin que la posada arda. Proteger el túnel que la salvó del hambre. Lidiar con el hecho de que esta noche Selvyn murió en parte gracias a lo que ella hizo esta tarde. |
| **Secreto** | Consintió la construcción del túnel zhentarim hace tres años a cambio de dinero. Pero su secreto más profundo esta noche: cuando Selvyn le entregó su nota de chantaje en la tarde, hizo el cálculo. Reconoció a Lysse del informe Harper que lleva tres años guardado —Selvyn sabe quién es Lysse, y las dos tienen el mismo problema. Wenna se acercó a Lysse bajo la excusa de llevarle infusiones y le murmuró lo necesario: la hora de la cita en el establo («segunda campanada»), la puerta oculta de la cocina, que los goznes ya estaban listos —los aceitó ella misma esa tarde con su frasco personal de aceite de linaza, marcado con una «W» en el corcho. No dijo «mátalo». Abrió una puerta y la dejó abierta. Lysse le devolvió una nota: «Entendido. Esta noche.» Wenna la quemó en la chimenea de la sala común. Casi del todo. |
| **Qué sabe de otros** | Sabe que Lysse figura en un informe Harper como «operativa renegada, peligrosidad máxima». Sabe que Durvis construyó el túnel con su complicidad. Sabe que Selvyn tenía notas sobre ambas cosas. Y sabe —porque fue ella quien lo hizo posible— que Lysse entró al establo esta noche con la información y el acceso que ella misma proporcionó. Si Lysse cae, Wenna cae con ella. |
| **Coartada** | En la barra toda la noche —múltiples testigos. Sólida respecto al asesinato directo. Pero si los PJs conectan el fragmento quemado en la chimenea (Pista Cómplice A) con la nota bajo la barra (Pista Cómplice B), la versión de «no supe nada» se derrumba. |
| **Culpabilidad** | **7/10.** Cómplice activa. No ejecutó el crimen. Pero le dio a Lysse la hora, el lugar y la puerta preparada. La línea entre «informar» y «ordenar» es la única defensa que le queda —y lo sabe mejor que nadie. |

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
*(Si se la presiona sobre Lysse y la puerta oculta)*
— «La posada tiene muchas puertas. Yo sé cuáles crujen y cuáles no. Eso es lo que saben los posaderos.» *(Sin mirar a los ojos. Se ocupa de las copas.)*

*Si descubren la pista A (fragmento quemado) o la pista C (frasco de aceite):*
— «Ese papel era mío. Le dije la hora que Selvyn tenía apuntada para ella en el establo. La puerta ya la conocía —la posada es mía. Eso es todo lo que hice.» *(Pausa breve.)* «No di ninguna orden.»

*Si descubren ambas pistas (A y B, fragmento + nota bajo la barra):*
— «'Entendido. Esta noche.' La escribió ella, no yo. Yo abrí una puerta —los dos sentidos de esa frase.» *(Pausa. Sin disculpa.)* «Selvyn iba a destruir esta posada, este túnel, todo lo que me quedaba. Lo que hizo Lysse... no lo pedí. Pero no lo lloré.»

**Comportamiento con otros NPCs:**
- *Con Sira:* La única persona de la sala de quien no recela. Coordinación sin afecto. Si Sira conecta a Wenna con el crimen, esa coordinación se transforma en terreno minado.
- *Con Durvis:* Lo contrató por referencias que resultaron falsas. Lo sospecha desde hace semanas. No actuó porque el túnel dependía de no alterarlo.
- *Con Lysse:* Hay un pacto tácito entre ellas esta noche —ninguna habla a la otra directamente, ninguna la mira. Ese no-contacto es demasiado deliberado para dos mujeres que teóricamente no se conocen. Los PJs con CD 14 Perspicacia pueden notarlo.

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
| **Objetos** | Kit herbolario completo: manojos secos, mortero, viales sellados, cuerdas botánicas de varios calibres. Un vial sin marcar vacío en la bolsa —era el extracto de adormidera y verbena que usó para la taza de Selvyn. Si alguien pregunta por el vial vacío, Lysse afirma haberlo preparado como tisana para Renwick («el herido del tercer cuarto»). Renwick, si se le consulta directamente: «Lo ofreció. Lo rechacé.» |
| **Actitud inicial** | Cálida, atenta, hace preguntas que parecen amabilidad pero son evaluación. Ofrece infusiones antes de que se las pidan. Escucha como alguien que necesita la información para curar, no para retenerla. |
| **Motivación** | Sobrevivir esta noche y salir del paso con su identidad intacta. Selvyn tenía información que la habría expuesto a los Harpers (por renegada) y a los Zhentarim (por ex-Harper). Cualquiera de los dos habría sido su muerte. Hizo el cálculo. |
| **Secreto** | Fue operativa Harper durante cuarenta años. Desertó cuando le ordenaron eliminar a un informante que tenía familia. Lleva doce años sola, trabajando en los márgenes. Selvyn encontró su historial en algún archivo de Neverwinter. Esta noche lo mató: sedación con una taza de extracto de adormidera y verbena preparada en la cocina, golpe único descendente con el cubo de madera del gancho del tercer pesebre cuando Selvyn ya no podía defenderse, salida por la puerta oculta de la estantería —que Wenna había preparado de antemano— de vuelta a la cocina. Puso el cuadernillo en la mano del cadáver y destruyó la página de la cita. El vial faltante está en su bolsa. Volvió arriba lavándose las manos en el cubo de la despensa. No le temblaron. Eso también lo sabe. |
| **Qué sabe de otros** | Sabe que Onno Grist le compró un compuesto explosivo hace tres años usando otro nombre —pero era él. Sabe que Sira Veleth es una Harper activa asignada a vigilarla. |
| **Coartada** | «Arriba toda la noche, sin bajar a la sala.» Tamlin la vio en la cocina de madrugada. La coartada tiene esa grieta. Además: un vial vacío sin marcar en su bolsa herbolaria que afirma haber usado para Renwick —Renwick lo desmiente si alguien le pregunta. |
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
— «Sí. Con compuesto sedante en una taza y un cubo de madera. En el establo. Salí por la puerta de la cocina. Me lavé las manos en el cubo de la despensa y subí. El chico de la mandolina me vio —ya lo sé. Decidid si eso me hace un monstruo o un problema de matemáticas con patas.»

**Comportamiento con otros NPCs:**
- *Con Wenna:* Hay un acuerdo tácito entre ellas —Wenna le dio las herramientas, Lysse las usó. Ninguna la mira directamente. Ninguna le habla. Ese silencio coordinado es el único indicio externo de que algo pasó entre ellas antes del crimen.
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

*Si se le pregunta sobre Lysse o un tónico:*
— «Me ofreció algo. Para la mano.» *(Pausa breve.)* «Lo rechacé. No tomo nada de extraños.» *(Si se insiste sobre el vial:)* «No. No recibí ningún vial.» Sin dudar. Sin elaborar.

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
| **Secreto** | Vio a Lysse Mourne en la cocina antes del grito, lavándose las manos con la cara completamente tranquila. Lo entiende cuando ve el cadáver. Revela la información completa con Persuasión CD 12 en Escena 3 o posterior; antes de eso solo admite que «la herbolaria rondaba de noche». |
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

*Bajo presión (Persuasión CD 12, Escena 3 o posterior):*
— «Estaba en la cocina. Tarde. Antes del grito. Lavándose las manos.» *(Pausa.)* «La cara completamente normal. Eso es lo que recuerdo. Lo normal que tenía la cara.» *(Pausa larga.)* «No dije nada porque no quería ser el siguiente. Eso me hace cobarde. No me hace asesino. Esa diferencia me importa más de lo que os parece.»

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
| **Qué sabe de otros** | Sabe la identidad real de Lysse Mourne como ex-Harper renegada. Dedujo que Lysse es la asesina de esta noche: Lysse estaba ausente de la sala cuando los caballos gritaron; Tamlin la vio en la cocina a hora tardía; Sira inspeccionó la posada antes del amanecer y encontró la puerta oculta de la cocina con los goznes recién aceitados. Ha identificado a Durvis Hakk como el operativo zhentarim que los Harpers llevan tres años buscando. Sabe que Selvyn trabajaba para los Harpers, aunque Selvyn no lo supiera. |
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
- **Pista Cómplice A (FÁCIL/MEDIA):** En la chimenea de la sala común, entre las cenizas de la tarde, hay un fragmento de papel quemado pero no del todo consumido. Queda legible el texto: «...est. 2ª camp...» La letra es cuidadosa y ordenada —la de alguien acostumbrado a llevar libros de cuentas. No es la letra de Selvyn (más apretada y nerviosa). Solo cobra pleno significado cuando se combina con la impronta del cuadernillo («L.M. — 2ª campanada»): alguien informó por escrito a Lysse de la hora y el lugar de la cita. Quien coteje con el libro mayor de Wenna (si tiene acceso) confirma la letra con CD 14 Investigación.

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 10 Investigación | Mancha de sangre seca bajo la mesa —antigua, no de esta noche |
| CD 12 Investigación | Sello de la Alianza de los Lordes en el cofre de Caelith |
| CD 12 Investigación | **Pista Cómplice A:** Fragmento quemado en la chimenea — «...est. 2ª camp...» en letra cuidadosa distinta a la de Selvyn |
| CD 13 Perspicacia | Reacción de Durvis a la noticia de la muerte —demasiado calmada |
| CD 13 Perspicacia | Tamlin no puede mirar a Lysse directamente desde la Escena 3 |
| CD 14 Perspicacia | Wenna y Lysse nunca se miran directamente —coordinación de no-contacto inusual entre dos desconocidas |
| CD 14 Investigación | Fragmento chimenea: letra coincide con libro mayor de Wenna (si se tiene acceso a ambos) |
| CD 15 Investigación | Tercera tabla del suelo, nicho con veneno |

---

## COCINA Y DESPENSA

Estrecha como un corredor de pesadilla, con ollas colgadas que oscilan sin viento visible. El fogón siempre encendido. El cubo de la despensa tiene un rastro verdoso tenue en el fondo —herbal, no de vajilla. La estantería del corredor trasero está ligeramente desencajada, un centímetro, y los goznes de lo que hay detrás tienen aceite fresco que destella con la luz.

**Secretos del Máster — DOS ACCESOS DISTINTOS:**

**ACCESO 1 — Puerta oculta al establo** *(superficie, Ruta 2):* Panel detrás de la estantería del corredor trasero. Pasillo de 4m a nivel de suelo hasta la pared lateral del establo —nada subterráneo. Mecanismo visible con CD 12 Investigación. Goznes recién aceitados con aceite de linaza: CD 11 si se busca específicamente. **Wenna los aceitó durante la tarde con su frasco personal.** Esta es la ruta que Lysse usó esta noche, en ambas direcciones.

**ACCESO 2 — Trampilla al sótano y túnel** *(subterráneo, Ruta 4):* Al fondo de la cocina, detrás del hogar, oculta bajo leña apilada. Conduce al sótano zhentarim y de ahí al túnel subterráneo de 40m hasta el tercer pesebre del establo. CD 13 para encontrar el mecanismo, CD 14 para abrir sin llave. Infraestructura zhentarim construida hace tres años. **No usada esta noche.** Completamente distinta de la puerta oculta de la estantería.

**Otras pistas:**
- El cubo de la despensa: residuo herbáceo verdoso en el interior (CD 13 Investigación). Lysse preparó aquí la taza con extracto sedante y limpió después. El residuo es de adormidera y verbena —identificable para alguien con conocimiento herbolario. No hay aceite de cocina ni suciedad de vajilla que lo justifique.
- **Pista Cómplice C (MEDIA):** En el corredor trasero, junto al acceso oculto, hay un frasco pequeño de aceite de linaza apoyado en el segundo estante. El corcho tiene una «W» grabada —marca de inventario personal de Wenna, distinta del aceite de cocina general que guarda en el armario de la cocina principal. El frasco fue usado recientemente (está en posición vertical, no tumbado, y el cuello está pegajoso). CD 13 Investigación. Solo: Wenna usa aceite propio en zonas privadas. Combinado con los goznes recién aceitados: fue Wenna quien preparó el acceso, no Lysse.
- **Pista Cómplice B (DIFÍCIL):** Detrás de la barra, bajo el mostrador, en una tabla suelta de la segunda repisa inferior —hay un pequeño papel doblado. Texto: «Entendido. Esta noche.» Letra precisa, inclinada ligeramente a la izquierda. CD 14 Investigación (requiere acceso al área de trabajo de Wenna y búsqueda activa). Quien haya examinado las etiquetas botánicas del kit de Lysse puede comparar la letra (CD 12 Investigación) y confirmar que la escritura es de la misma mano.

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 11 Investigación | Goznes de la puerta oculta al establo (ACCESO 1), recién aceitados |
| CD 12 Investigación | Panel detrás de la estantería —puerta oculta al establo (ACCESO 1) |
| CD 13 Investigación | Residuo herbáceo verdoso en el cubo de la despensa —preparación de sedante, no suciedad habitual de cocina |
| CD 13 Investigación | **Pista Cómplice C:** Frasco de aceite con «W» grabada en el corcho —aceite de Wenna, no del stock de cocina general; usado recientemente |
| CD 13 Investigación | Mecanismo de la trampilla al sótano bajo la leña (ACCESO 2, zhentarim) |
| CD 14 Investigación | **Pista Cómplice B:** Nota «Entendido. Esta noche.» bajo tabla suelta de la repisa inferior de la barra —letra de Lysse (comparar con etiquetas de su kit herbolario) |

---

## ESTABLO ANEXO

Cuatro pesebres. Heno húmedo de orina animal. El farol está apagado. Los caballos ya no se calman del todo. El cadáver de Selvyn Drask está desplomado contra la pared del tercer pesebre, los ojos abiertos, el cuadernillo todavía en la mano —abierto en una página en blanco, como si todavía tomara notas. Traumatismo visible en la sien derecha. Primer diagnóstico obvio: una coz. No debería haber estado aquí de noche.

**Secretos del Máster:**
- **Pista 1 (FÁCIL):** Ángulo de la herida —inconsistente con coz de caballo. CD 10 Medicina. Las coces viajan horizontal o hacia arriba; esta impactó desde arriba y por detrás. Golpe deliberado en arco descendente. Elimina el accidente.
- **Falsa pista → Borrakh:** Huellas de bota grandes en el heno junto al cuerpo —talla de medio-orco. CD 11 Investigación. Apunta inicialmente a Borrakh. Con CD 13 Investigación: dos series distintas —las grandes son más antiguas y lineales (Borrakh, puerta↔cuerpo); las medianas son más recientes y emergen desde el panel de la pared oeste (Lysse, esta noche).
- **Pista 3 (MEDIA):** Residuo sedante amargo en los labios de Selvyn. CD 13 Medicina. Compuesto herbal inductor del sueño —camamilla de base, algo más amargo debajo. Bebió algo poco antes de morir. Apunta explícitamente a un herbolario.
- **Pista real (DIFÍCIL):** Cuadernillo abierto en página en blanco. CD 15 Investigación para detectar la presión del bolígrafo en la hoja anterior —con carbón frotado sobre la página, puede leerse: «L.M. — 2ª campanada.» Selvyn tenía cita de chantaje con L.M. a la segunda campanada. La asesina destruyó la página pero no la impronta.
- **Falsa pista → Durvis:** Tierras arcillosas rojizas en el suelo del tercer pesebre, distintas al barro del suelo: CD 12 Investigación. Son del sistema de túneles —tráfico histórico zhentarim, no pisadas de esta noche (tierra seca y endurecida). Las huellas frescas llegan desde el panel de la pared oeste, no desde la trampilla.
- La trampilla al túnel bajo el tercer pesebre: CD 13 Investigación para encontrarla bajo el heno. Infraestructura zhentarim.
- El panel de la puerta oculta de la cocina, en la pared oeste: CD 11 Investigación para notar que está ligeramente desencajado desde dentro —la ruta que usó Lysse esta noche.

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 10 Medicina | **Pista 1:** Ángulo de la herida —inconsistente con coz; golpe descendente deliberado |
| CD 11 Investigación | **Falsa pista → Borrakh:** Huellas de bota grandes en el heno (talla medio-orco) |
| CD 11 Investigación | Panel de la puerta oculta —lado establo, ligeramente desencajado |
| CD 12 Investigación | **Falsa pista → Durvis:** Tierra arcillosa rojiza (seca, tráfico histórico zhentarim, no de esta noche) |
| CD 13 Medicina | Residuo sedante amargo en los labios de Selvyn —compuesto herbal inductor del sueño |
| CD 13 Investigación | Dos series de huellas: grandes/antiguas (Borrakh) + medianas/recientes desde pared oeste (Lysse) |
| CD 13 Investigación | Fibras de cuerda botánica en el suelo junto al cadáver —tipo herbolario, para colgar manojos; cayeron de la bolsa de alguien al pasar |
| CD 13 Investigación | Trampilla al túnel en el suelo del tercer pesebre (infraestructura zhentarim) |
| CD 15 Investigación | Impronta «L.M. — 2ª campanada» en el cuadernillo (frotar carbón sobre la página) |

---

## PISO SUPERIOR

Cinco habitaciones. Puertas que no cierran bien. Suelo de tablas que avisa de cada paso. La habitación 3 de Renwick tiene sangre en el tablón junto a la cama —de la herida en la mano, anterior al crimen. La habitación 5, al fondo este, tiene la ventana con escarcha alterada en el alféizar exterior (CD 12 Investigación) y pizarras desplazadas en la cubierta del establo (CD 13 Investigación desde el tejado o desde dentro).

**Secretos del Máster:**
- **Falsa pista → Renwick:** Ventana este de habitación 5: escarcha alterada en el alféizar exterior (CD 12 Investigación). Las pizarras de la cubierta del establo están desplazadas (CD 13 Investigación). Parece que alguien bajó al establo por esta ruta. Disprove: Renwick estaba en la ventana vigilando el patio buscando a Durvis —no descendió. Borrakh lo vio allí antes del grito (CD 14 Perspicacia a Borrakh).
- **Pista real (DIFÍCIL) — Habitación 2, Lysse:** En la bolsa herbolaria, falta un vial pequeño sin marcar (CD 12 Investigación + acceso a la habitación). Lysse, si se le pregunta, afirma haberlo preparado como tisana para Renwick. Renwick lo niega directamente: «Me ofreció algo. Lo rechacé.» El vial no tiene justificación. También falta una cuerda botánica de calibre mediano (CD 16 Perspicacia para notar el número exacto de cuerdas). Lysse no da explicación voluntaria sobre su ausencia si se le pregunta.
- Sangre de Renwick en habitación 3: de la herida en la mano, no relacionada con el crimen.

**Puntos de interacción:**
| CD | Qué se encuentra | Tipo |
|---|---|---|
| CD 12 Investigación | Escarcha alterada en alféizar ventana este, hab. 5 | Falsa pista → Renwick |
| CD 12 Investigación | Vial pequeño faltante en bolsa herbolaria, hab. 2 (Lysse) | Pista real |
| CD 13 Investigación | Pizarras desplazadas en cubierta del establo (desde ventana/tejado) | Falsa pista → Renwick |
| CD 14 Perspicacia | Preguntar a Borrakh: confirma ver a Renwick en ventana antes del grito | Disprove Renwick |
| CD 16 Perspicacia | Número de cuerdas botánicas en bolsa de Lysse —falta calibre mediano | Pista real |

---

## EL SÓTANO OCULTO Y EL TÚNEL

Un nivel subterráneo completo bajo la cocina. Techo bajo, humedad de piedra, olor a pólvora y madera lacrada. La trampilla explosiva de Onno está ahora abierta y humeante. El contenido de los cajones zhentarim es visible para quien entre.

**Descripción del túnel:**
El túnel tiene 40 metros de longitud, suelo de tierra arcillosa rojiza (característica y reconocible), paredes de piedra sin acabar. Conecta la bodega de la posada con el tercer pesebre del establo (pasando por debajo) y continúa hasta una salida disimulada en la pared del barranco oriental, a 250 metros al este. Una cuarta ramificación, tapiada, apuntaba a las ruinas de un antiguo puesto del Paso.

**Evidencias en el túnel:**
- Tierra rojiza pisoteada en ambas direcciones (múltiples usuarios históricos; nada reciente de esta noche).
- El libro de deudas de Onno, escondido bajo una tabla suelta, inidentificable sin clave (CD 14 Arcana para descifrar parcialmente).

**Puntos de interacción:**
| CD | Qué se encuentra |
|---|---|
| CD 11 Investigación | Cajones zhentarim con sello, documentos cifrados |
| CD 13 Investigación | Marcas de uso histórico en el suelo del túnel —ninguna evidencia de esta noche |
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
- **9:** Lysse intenta salir por la puerta oculta de la cocina. Si nadie lo nota, llega al establo y de ahí al exterior.
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
El Máster confirma la deducción narrativamente, no con un dado. «Sí, la fibra botánica del cuello de Selvyn y la cuerda que falta en la bolsa de Lysse son del mismo calibre y tipo. Eso es un hecho.»

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
| Wenna Corren | Encubrir al asesino, saber del túnel | **7/10** — **CÓMPLICE ACTIVA.** Le dio a Lysse la hora de la cita, preparó el acceso, lubricó los goznes | En la barra toda la noche — sólida respecto al crimen directo; colapsa con Pistas Cómplice A+B | Consintió el túnel zhentarim; entregó a Lysse la información y el acceso que hicieron el crimen posible |
| Selvyn Drask | N/A — víctima | **1/10** | N/A | Trabajaba para los Harpers mientras chantajeaba |
| Borrakh Peñadiente | Asesinato; huellas en establo; pasado violento | **3/10** — Encontró el cadáver y calló | Estuvo antes del crimen — frágil por omisión | Incendio del depósito cubierto por Renwick |
| Lysse Mourne | Aparentemente nada — «solo la herbolaria» | **10/10** — **LA ASESINA** | «Arriba toda la noche» — MENTIRA; Tamlin la vio en cocina; vial vacío sin justificación | Ex-Harper renegada; mató con sedante + cubo de madera; salió por puerta oculta de la cocina |
| Durvis Hakk | Todo lo relacionado con el cofre; reacción calmada | **6/10** — Construyó las condiciones; ramal norte | En sala toda la noche — sólida | Operativo Zhentarim; ramal norte; cofre comprometido |
| Onno Grist | Trampa explosiva; identidad falsa; movimientos sospechosos | **5/10** — Cómplice indirecto; trampa era general | En sala o corredor — sólida | Cuervos de Mirtul; acreedor de Tamlin; trampa de seguridad propia |
| Caelith Brynmar | «Trajo la plaga»; tensión con todos | **3/10** — Cómplice de sistema; no crimen de esta noche | Con el cofre en sala — sólida | Abrió el cofre; su comandante está en las cartas |
| Renwick Sorn | Estuvo en zona de acceso; herida; dos nombres en el cuadernillo | **4/10** — Buscaba a Durvis, no a Selvyn; llegó después | «En sala toda la noche» — PARCIALMENTE MENTIRA; ventana este | Cubrió el incendio de Borrakh; buscaba a Durvis Hakk |
| Tamlin Pell | Vende información; en deuda; movimientos nocturnos | **4/10** — Cobarde que sabe demasiado desde la Escena 3 | En sala tocando — sólida | Vio a Lysse con las manos mojadas |
| Sira Veleth | Drow con posibles contratos; no habla; sin equipaje | **2/10** — La persona menos culpable de la sala | En silla en sala — sólida | Harper activa; sabe quién es la asesina desde la Escena 3 |

---

## RASTREADOR DE PISTAS FALSAS

### Falsas pistas estructuradas (con mecánica de disprove)

| Falsa pista | CD inicial | Apunta a… | Cómo se disprove | CD disprove |
|---|---|---|---|---|
| Huellas de bota grandes en el heno junto al cuerpo (talla medio-orco) | CD 11 Investigación (establo) | Borrakh | Dos series de huellas: grandes/antiguas (Borrakh, puerta→cuerpo→puerta) + medianas/recientes desde pared oeste (Lysse). Borrakh: «Lo encontré. Lo toqué. No lo maté.» | CD 13 Investigación |
| Tierra arcillosa rojiza en el suelo del tercer pesebre (túnel) | CD 12 Investigación (establo) | Durvis (tiene la llave del túnel) | La tierra está seca y endurecida: tráfico histórico zhentarim, no pisadas de esta noche. Huellas frescas vienen del panel, no de la trampilla. Wenna: «Durvis lleva tres años usando ese túnel. La arcilla siempre estuvo ahí.» | CD 13 Investigación; Wenna bajo presión |
| Escarcha alterada en alféizar ventana este (hab. 5) + pizarras desplazadas en cubierta del establo | CD 12 Investigación (piso superior) | Renwick (posible bajada al establo por tejado) | Renwick estaba en la ventana vigilando el patio buscando a Durvis —no bajó. Borrakh lo vio allí antes del grito. | CD 14 Perspicacia a Borrakh |

### Otras señales que misdirectionan

| Pista | Apunta a… | Verdad |
|---|---|---|
| Reacción demasiado calmada de Durvis a la muerte | Durvis como asesino | Durvis quería a Selvyn vivo y controlado; muerto es más difícil de gestionar |
| Onno activo y nervioso en Escena 4 | Onno como cómplice del crimen | Va hacia su trampa de seguridad propia, no relacionada con el crimen |
| Lysse examina el cadáver voluntariamente | Lysse sin nada que ocultar | Controla qué información se revela desde la «pericia médica» |
| Cuadernillo con tres nombres visibles (sin cuarto) | Tres sospechosos obvios | El cuarto nombre (L.M. — 2ª campanada) fue destruido; se recupera con carbón (CD 15) |

### Señales del cómplice (Wenna)

| Señal | CD | Lo que parece | Lo que es |
|---|---|---|---|
| Wenna solo pregunta «¿está cerrado el establo?» al saber de la muerte | CD 13 Perspicacia | Gestión de la posada | La pregunta de alguien que ya sabe lo que ocurrió y verifica si la ruta quedó comprometida |
| Wenna y Lysse nunca se miran ni se dirigen la palabra | CD 14 Perspicacia | Indiferencia entre desconocidas | No-contacto coordinado; pacto tácito de silencio |
| Frasco de aceite marcado «W» en el corredor trasero | CD 13 Investigación | Mantenimiento normal de la posada | Wenna preparó el acceso esa tarde —no Lysse |
| Fragmento «...est. 2ª camp...» en la chimenea | CD 12 Investigación | Papel quemado sin importancia | El mensaje que Wenna pasó a Lysse con la hora y el lugar |
| Nota «Entendido. Esta noche.» bajo la barra | CD 14 Investigación | — (difícil de encontrar) | La confirmación escrita de Lysse a Wenna; cierra el caso de la conspiración |

---

## LISTA DE CDs CLAVE

| CD | Acción | Pista o resultado |
|---|---|---|
| CD 10 Medicina | Examinar herida en la sien de Selvyn | **Pista 1:** Ángulo de golpe descendente —inconsistente con coz. Confirma asesinato. |
| CD 10 Investigación | Sala común, tabla del suelo | Mancha de sangre antigua, no de esta noche |
| CD 11 Investigación | Establo, heno junto al cuerpo | **Falsa pista → Borrakh:** Huellas de bota grandes (talla medio-orco) |
| CD 11 Investigación | Cocina, goznes puerta oculta al establo | Goznes recién aceitados —puerta oculta usada esta noche |
| CD 11 Investigación | Establo, pared oeste | Panel de la puerta oculta, ligeramente desencajado desde dentro |
| CD 11 Medicina | Observar a Renwick | Vendajes en la mano derecha, herida reciente |
| CD 12 Investigación | Cofre de Caelith | Sello de la Alianza de los Lordes |
| CD 12 Investigación | Establo, suelo del tercer pesebre | **Falsa pista → Durvis:** Tierra arcillosa rojiza (seca, tráfico histórico del túnel zhentarim) |
| CD 12 Investigación | Piso superior, alféizar ventana este, hab. 5 | **Falsa pista → Renwick:** Escarcha alterada —alguien estuvo en esa ventana |
| CD 12 Investigación | Piso superior, hab. 2 (Lysse), bolsa herbolaria | Vial pequeño faltante —Lysse afirma haberlo dado a Renwick; Renwick lo niega |
| CD 13 Perspicacia | Observar a Tamlin desde Escena 3 | Incapaz de mirar a Lysse directamente |
| CD 13 Perspicacia | Observar a Durvis, noticia de la muerte | Reacción demasiado neutral para alguien que tiene motivo |
| CD 13 Medicina | Examinar labios de Selvyn | **Pista 3:** Residuo sedante amargo —compuesto herbal inductor del sueño. Apunta a herbolario. |
| CD 13 Investigación | Establo, heno | Dos series de huellas: grandes/antiguas (Borrakh) + medianas/recientes desde pared oeste (Lysse) — disprove Borrakh |
| CD 13 Investigación | Establo, suelo del tercer pesebre | Trampilla al túnel bajo el heno (infraestructura zhentarim) |
| CD 13 Investigación | Tejado establo (desde ventana/tejado) | **Falsa pista → Renwick:** Pizarras desplazadas — alguien pudo haber bajado |
| CD 13 Investigación | Cocina, cubo de la despensa | Residuo herbáceo verdoso —preparación de sedante (adormidera/verbena), no suciedad habitual |
| CD 13 Investigación | Cocina, mecanismo al fondo | Trampilla al sótano bajo la leña (ACCESO 2, zhentarim, distinto de la puerta oculta) |
| CD 14 Perspicacia | Preguntar a Borrakh sobre la ventana (Escena 3+) | Confirma haber visto a Renwick en la ventana este antes del grito — disprove Renwick |
| CD 15 Investigación | Establo, cuadernillo de Selvyn | Frotar carbón sobre la página en blanco revela «L.M. — 2ª campanada» — cita de chantaje |
| CD 14 Investigación | Sótano, cajones | Mapa del sistema de túneles con cuatro salidas |
| CD 14 Arcana | Libro de Onno bajo tabla suelta | Descifrado parcial de las cuentas de los Cuervos de Mirtul |
| CD 15 Investigación | Sala común, tercera tabla del suelo | Nicho con veneno de sombra |
| CD 15 Investigación | Sótano, cajones zhentarim | Correspondencia Durvis-Luskan |
| — | Preguntar a Renwick sobre la tisana | **Pista 6:** «No. Lo ofreció. Lo rechacé.» Desmonta la coartada del vial vacío de Lysse. |
| CD 12 Persuasión | Hablar a solas con Tamlin (Escena 3+) | **Testigo clave:** «La vi en la cocina. Tarde. Lavándose las manos. Lo normal que tenía la cara.» |
| CD 12 Investigación | Sala común, chimenea, cenizas | **Pista Cómplice A (FÁCIL/MEDIA):** Fragmento quemado «...est. 2ª camp...» en letra cuidadosa distinta a la de Selvyn — alguien comunicó la cita a Lysse por escrito |
| CD 13 Investigación | Cocina, corredor trasero, frasco de aceite | **Pista Cómplice C (MEDIA):** Frasco con «W» en el corcho —aceite personal de Wenna, usado recientemente; confirma que fue Wenna quien preparó el acceso |
| CD 14 Investigación | Barra, repisa interior, tabla suelta | **Pista Cómplice B (DIFÍCIL):** Nota «Entendido. Esta noche.» —letra de Lysse; confirmación escrita del acuerdo con Wenna |
| CD 14 Investigación | Fragmento chimenea + libro mayor de Wenna | Letra del fragmento coincide con la de Wenna —confirma autoría de la nota de la cita |
| CD 12 Investigación | Nota bajo barra + etiquetas kit de Lysse | Misma letra inclinada —confirma que Lysse escribió la nota de respuesta a Wenna |
| CD 14 Perspicacia | Observar a Wenna y Lysse juntas (Escena 2+) | No-contacto deliberado entre ellas —demasiado coordinado para dos desconocidas; indicio de acuerdo previo |

---

## INTERESES DE FACCIONES EN EL COFRE

| Facción | Quiere | No quiere que ocurra |
|---|---|---|
| **Alianza de los Lordes** (Caelith) | Recuperar vial + mapas + destruir cartas | Que las cartas se lean en voz alta |
| **Zhentarim** (Durvis) | Vial de plaga + mapas | Que el vial se destruya; que el túnel se cierre |
| **Cuervos de Mirtul** (Onno) | Solo los mapas (para revender × 2) | Que alguien abra el cofre sin él delante |
| **Harpers** (Sira) | Destruir el vial. Exponer las cartas | Que el vial llegue al mercado negro |
| **Renwick Sorn** (personal) | Las cartas específicamente —nombran a Byrne | Que las cartas desaparezcan sin proceso judicial |
| **Lysse Mourne** (personal) | Salir viva de la posada con identidad intacta | Que alguien conecte el vial faltante con el residuo del cubo de la cocina, o que Renwick desmienta el préstamo del tónico |
| **Wenna Corren** (personal) | Que nadie conecte el fragmento quemado ni la nota bajo la barra con su rol; que la conversación pare en Lysse | Que los PJs combinen las Pistas Cómplice A+B y lleguen a ella —su posada y su libertad dependen de ese silencio |

---

## ACCESOS AL ESTABLO — RESUMEN OPERATIVO

| Ruta | CD acceso | Usada por | Evidencia que deja |
|---|---|---|---|
| Puerta principal del patio | Sin CD | Selvyn (víctima), Borrakh (antes crimen) | Barro en umbral; difícil con ventisca |
| Puerta oculta cocina–establo *(superficie, 4m)* | CD 12 Investigación para encontrar | Lysse (asesina, ida **y** vuelta esta noche) — goznes preparados por Wenna | Goznes aceitados con aceite de Wenna (frasco marcado «W»); panel desencajado; residuo herbal en cubo de cocina |
| Ventana este piso superior | CD 12 Atletismo para usar | Renwick (antes crimen, solo observación) | Rasguños en alféizar; pizarras movidas |
| Túnel sótano–tercer pesebre *(subterráneo, 40m — distinto de la puerta oculta)* | CD 13 Investigación para encontrar trampilla | **Nadie esta noche** (uso histórico zhentarim) | Tierra arcillosa rojiza (histórico); sin evidencia de uso esta noche |

---

*Fin del documento. El cuervo blanco del umbral sigue en su poste. Nadie sabe si graznó durante la noche.*

---

---

## SINOPSIS NARRATIVA COMPLETA (Guión de Lectura)

> *Esta sección es un resumen narrativo completo de la campaña, escrito en prosa cinematográfica. Cubre todos los personajes, secretos, pistas, cronología y finales posibles. Útil para el Máster antes de dirigir, o como referencia después de la campaña.*

---

# PRÓLOGO: LA TORMENTA QUE NO PIDE PERMISO

Hay lugares en el mundo donde la geografía convierte a las personas en rehenes. El Paso del Cuervo Blanco, en la Costa de la Espada, es uno de esos lugares. A media montaña entre Neverwinter y el interior del norte, flanqueado por paredes de roca que el invierno viste de negro húmedo, el Paso tiene una sola posada que no se cayó todavía. Se llama la Posada del Paso Helado, y su propietaria, Wenna Corren, la mantiene en pie con el mismo principio con que mantiene todo lo demás: voluntad pura y ausencia absoluta de alternativas.

La noche en cuestión comienza con una ventisca. No una tormenta ordinaria, con su advertencia de nubes y su protocolo de viento, sino el tipo de ventisca que llega ya hecha, sin aviso, como una sentencia. En cuestión de una hora, el camino al sur queda invisible. En cuestión de dos, el camino al norte queda bloqueado por tres palmos de nieve. En cuestión de tres, la única realidad que existe en el universo es esta sala común con su chimenea de piedra negra, sus lámparas de aceite que alargan las sombras de una forma que no debería ser posible, y nueve personas —diez si contamos al muerto que todavía no lo es— que tienen exactamente un motivo para estar aquí y exactamente otro motivo mayor para que nadie lo sepa.

La sala común es calor de mentira. La chimenea distribuye luz, no temperatura; el calor real viene de los cuerpos, de la tensión que los cuerpos generan cuando los secretos que cargan empiezan a rozarse los unos con los otros. La mesa de roble del centro tiene una mancha antigua que nadie describe y que todos rodean inconscientemente. Detrás de la barra, Wenna Corren llena copas con la misma cara para todo —para el vino barato, para la cerveza ácida, para la botella sin etiqueta que guarda debajo y que reserva, según ella, para el día que alguien diga una verdad entera en este paso. El reloj de arena sobre la repisa lleva tres años roto. Nadie lo quitó porque la posada funciona mejor cuando nadie sabe qué hora es exactamente.

Un cuervo blanco disecado preside el umbral de la puerta principal. O descansa. Es difícil decirlo.

Esta es la jaula. Lo que ocurre dentro de ella durante las próximas horas no es un accidente. Es la consecuencia lógica y casi matemática de seis días de movimientos de piezas que terminaron aquí, en este punto de convergencia involuntaria, en esta posada que el invierno selló sin consultar a nadie.

---

# PRIMERA PARTE: LOS QUE LLEGARON

## Wenna Corren — La Posada y Sus Precios

Cuarenta y ocho años, y ni uno de disculpas. Eso es lo primero que se percibe de Wenna Corren: la ausencia total de disculpa. Sus manos cuentan la historia sin necesidad de narrador —manos que han cargado barriles, que han reparado tejados con las uñas cuando no había herramienta, que han enterrado a dos maridos en tierra que ella misma cavó. Los ojos grises lo cuentan todo si sabes leer a las personas que aprendieron a no contar nada. Tiene una cicatriz oblicua en el antebrazo derecho que nunca explica y que nadie pregunta dos veces.

La posada es suya. La posada es ella. La distinción no existe.

Hace tres años, cuando el hambre empezó a ser un plan de negocio y no una emergencia pasajera, llegaron unos hombres que pagaron bien y hacían preguntas malas. Les alquiló el sótano. Les permitió construir. No preguntó qué construían porque la respuesta le habría costado el precio de la ignorancia, y la ignorancia era lo único que en ese momento le quedaba para vender. El túnel lleva tres años ahí, cuarenta metros de corredor subterráneo que conecta la bodega de la posada con el tercer pesebre del establo, y de ahí a una salida disimulada en el barranco oriental. Infraestructura zhentarim. Wenna lo sabe. Lo lamenta a la manera en que se lamentan las cosas que no pueden deshacerse: en silencio y hacia dentro.

El hombre que construyó el túnel se llama Durvis Hakk. Esta noche también está en la sala.

Lo que Wenna no supo hasta la tarde de hoy —hasta que un notario regordete con sobretodo azul marino le puso un papel doblado en cuatro en el bolsillo del delantal— es que su connivencia con el túnel tiene nombre y fecha y firma de notario real. La nota de Selvyn Drask está escrita con la eficiencia arrogante de alguien que cree tenerlo todo bajo control. Le exige que mantenga el establo libre esta noche para tres reuniones privadas, de la primera a la tercera campanada. Le informa, sin dramatismo, de que el incumplimiento tendría consecuencias documentadas.

Wenna leyó la nota. La dobló. Se la guardó de nuevo en el bolsillo.

Y entonces empezó a pensar.

Lleva toda la tarde pensando mientras sirve copas, mientras llama a todos «viajero», mientras observa al notario circular por la sala con su cuadernillo bajo el brazo, visitando a uno, visitando a otro, dejando a cada uno con la espalda un centímetro más rígida que antes. La herbolaria. El enano del fondo. El tiefling de los cuernos en espiral. Wenna ha visto suficiente gente con suficientes problemas como para reconocer el patrón: Selvyn Drask está chantajeando a todo el que tiene algo que perder en esta sala.

La única persona de la sala de quien Wenna sabe que Selvyn tiene algo —porque lleva tres años guardando un informe Harper sin saber muy bien qué hacer con él— es Lysse Mourne. La herbolaria élfica que llegó ayer, que hace preguntas que parecen amabilidad y son evaluación, que ofrece infusiones antes de que nadie las pida. El informe dice que Lysse Mourne es una operativa Harper renegada de peligrosidad máxima. Wenna no sabe exactamente qué significa eso. Sabe que significa que las dos tienen el mismo problema.

Lo que ocurre después forma parte del catálogo de decisiones que la gente toma cuando la alternativa es perder lo único que le queda. Bajo la excusa de revisar el corredor trasero de la cocina, Wenna unta los goznes de la puerta oculta al establo con aceite de linaza de su frasco personal —el que lleva una «W» grabada en el corcho, su marca de inventario, distinta del aceite de cocina general. Los goznes quedan mudos. La puerta, silenciosa.

Después busca a Lysse. Lo hace con tazas de infusión en las manos, repartiendo bebidas, sin detenerse, sin mirar. Le murmura al pasar. Tres cosas. La hora de la cita que Selvyn tiene anotada en su cuadernillo para Lysse: la segunda campanada. La ruta: la puerta oculta de la cocina, la estantería del corredor trasero, cuatro metros de pasillo hasta el establo. Y el estado de los goznes.

Lysse escucha. No pregunta nada. No dice nada. Antes de subir a su cuarto, le pasa a Wenna una nota doblada. Cuatro palabras: «Entendido. Esta noche.»

Wenna la quema esa misma tarde en la chimenea de la sala común.

Casi del todo.

---

## Selvyn Drask — El Funcionario Que Sabía Demasiado

Cuarenta y cinco años, cara de funcionario veterano. Calvicie incipiente, papada honesta, manos de escribiente con callos en el índice derecho. El cuadernillo de cuero marrón siempre bajo el brazo como una extremidad extra. El traje azul marino con la insignia de notario real —real, no robada— comunica autoridad sin comunicar dinero, que es exactamente la combinación que Selvyn lleva veinte años perfeccionando.

Llegó temprano esta mañana. Pasó el día en su habitación redactando cuatro notas de chantaje con la eficiencia de alguien que considera el proceso una labor burocrática. La de Wenna Corren: el túnel. La de Durvis Hakk: sus actividades zhentarim, que Selvyn lleva seis meses documentando. La de Renwick Sorn: el incendio del depósito militar, tres muertos, archivo clasificado. La de Lysse Mourne: su identidad como Harper renegada, que le costaría la vida a manos de cualquiera de las dos facciones que la buscan.

Entregó las tres primeras durante la tarde. La de Lysse se la guardó para el momento apropiado.

Lo que la sala no sabe —lo que no sabrá hasta la Escena 4— es que Selvyn Drask llevaba seis meses construyendo un expediente real sobre la red zhentarim de Durvis Hakk para entregarlo a los Harpers. El chantaje era su mecanismo de financiación y su seguro de vida simultáneamente: si alguien lo mataba antes de entregar el expediente, las notas automáticas en el archivo de Neverwinter se abrirían solas. O eso creía. Lysse lo sabía. Y sabía que Selvyn había mentido sobre el sistema de respaldo. No existía.

Selvyn Drask era un extorsionista funcional que estaba haciendo algo importante. El problema es que nadie en la sala lo sabe cuando él muere. Eso es lo que hace que la sala silencie su siguiente comentario y mire al suelo.

---

## Lysse Mourne — La Herbolaria

Madera élfica de ciento veintitantos años con cara que el mundo lee como treinta y cinco. Piel de color nogal claro, cabello castaño rojizo recogido con fijadores botánicos. Los ojos avellana son cálidos hasta que se fijan en algo. Entonces son otra cosa completamente.

Cuarenta años como operativa Harper en tres continentes. Sabe hacer cosas que no se enseñan en ninguna escuela y que no tienen nombre elegante en ningún idioma. Desertó hace doce años cuando le ordenaron eliminar a un informante que tenía familia —específicamente, cuando los Harpers esperaban que lo hiciera delante del niño de ocho años para maximizar el efecto disuasorio. Lysse tomó el expediente del niño y lo destruyó. Después tomó sus credenciales Harper y las destruyó también. Lleva doce años sola, trabajando en los márgenes como herbolaria, moviéndose antes de que nadie la encuentre.

Selvyn la encontró.

No importa cómo. Lo que importa es que encontró su historial en algún archivo de Neverwinter, y que la nota que le entregó esta noche le informaba con la amabilidad chirriante de funcionario que si no se presentaba en el establo a la segunda campanada, el informe sobre su identidad Harper llegaría a Skullport por la mañana. Los Zhentarim de Skullport tienen una lista de ex-operativos Harper renegados. La lista es un menú. Lysse sabe esto mejor que nadie.

De modo que hizo el cálculo.

No hubo rabia. No hubo drama. Aritmética. El peso del expediente que Selvyn estaba construyendo contra la red zhentarim versus el precio de la supervivencia propia. El expediente perdió.

Preparó una taza con extracto de adormidera y verbena sedante usando materiales de su bolsa herbolaria. La dejó en el poste del tercer pesebre donde Selvyn la encontraría. Se retiró al cuarto pesebre a esperar. Cuando Selvyn bebió —la taza era amarga, pero no más que su té habitual— y cuando los brazos empezaron a pesarle en el minuto cuatro, Lysse descolgó el cubo de madera del gancho del tercer pesebre y lo usó. Golpe único. Descendente. Sien derecha. El trabajo duró tres segundos.

Lo que ocurrió después es el tipo de detalle que distingue a las personas que piensan frío de las que improvisan caliente. Lysse volvió a colgar el cubo en su gancho —quedó levemente húmedo en el borde, con residuo verdoso herbal transferido de sus manos al borde del cubo. Puso el cuadernillo de Selvyn en la mano del cadáver, abierto en una página en blanco, como si todavía estuviera tomando notas. Destruyó la página de la cita, la que decía «L.M. — 2ª campanada». No se dio cuenta de que la presión del bolígrafo había impreso la escritura en la página siguiente, invisible a simple vista pero recuperable con carbón.

Salió por la puerta oculta de la estantería —la que Wenna había preparado de antemano— de vuelta a la cocina. Cuatro minutos de pasillo. Se lavó las manos en el cubo de la despensa. Subió. No le temblaron.

Eso también lo sabe. Y ese conocimiento —el de la ausencia de temblor— es lo único de la noche que la acompaña de una manera que no tiene nombre exacto.

---

## Durvis Hakk — El Enano Sin Joyas

Sesenta años de enano con barba gris corta y bien recortada. No la barba de un herrero —la de alguien que come bien y duerme cómodo. Manos sorprendentemente finas para un mercader. Los ojos azul acero evalúan el precio de todo lo que hay en una habitación antes de decir buenos días.

Viaja como mercader de gemas. No lleva joyas. Un mercader de gemas sin joyas es alguien que no quiere ser un mercader de gemas.

Durvis Hakk es el nodo de distribución zhentarim para el norte del Paso del Cuervo Blanco. Fue él quien construyó el túnel bajo la posada de Wenna, pagando lo suficiente para que la posadera cerrara los ojos y lo suficiente más para que los mantuviera cerrados. Fue él quien hace cuatro años vendió las posiciones militares del ramal norte del Paso a los Zhentarim, desencadenando un ataque que mató a seis personas, incluyendo al hermano mayor de Renwick Sorn y al resto de su familia. El informe oficial habló de «error de navegación». El oficial que firmó ese informe se llamaba Halvek Byrne. Ese nombre está en las cartas del cofre. Durvis lo sabe.

Durvis también sabe exactamente lo que hay en el cofre que lleva la dracónida. Lo sabe porque su red lo abrió y reselló en ruta, en Neverwinter, antes de que Caelith Brynmar llegara a recogerlo. Conoce el contenido. Conoce el vial de plaga. Conoce las cartas. Conoce los mapas. Esta noche quiere recuperar el cofre para los Zhentarim.

Lo que Durvis no quería es la muerte de Selvyn Drask. Un notario muerto es un problema más difícil de manejar que un notario controlado. Cuando se entera de la muerte, su reacción es demasiado calmada. No pregunta quién lo encontró ni cuándo fue. Procesa la información y la añade a su modelo del tablero. Esto, para alguien con el entrenamiento correcto, es exactamente el tipo de frialdad que señala hacia alguien que ya sabía o que ya esperaba.

---

## Renwick Sorn — El Tiefling Con Una Lista Muy Corta

Treinta y dos años, cuernos en espiral larga hacia atrás. La cicatriz en la mano derecha vendada tiene la forma exacta de una astilla de madera, no de un cuchillo. La mandíbula cuadrada mastica silencios con eficiencia. Cuando está en reposo, parece que está contando algo. Porque está contando algo.

Renwick Sorn lleva dos años siguiendo a Durvis Hakk. Lleva dos años con el nombre de Durvis escrito en un papel doblado que guarda en el bolsillo interior, como si necesitara el recordatorio, como si fuera posible olvidar el nombre del hombre responsable de que su hermano mayor —diecisiete años, el ramal norte, invierno del año 1492 del Calendario del Dale— muriera congelado en un puesto que nadie fue a evacuar porque las posiciones habían sido vendidas y el ataque llegó cuatro horas antes de lo que cualquier plan defensivo podía contemplar.

Esta noche la tormenta le regaló la jaula que llevaba dos años buscando. Durvis Hakk está en esa sala. La ballesta está en la mochila, desmontada, accesible en treinta segundos.

Renwick tiene también un secreto que pesa en dirección contraria: hace cuatro años cubrió a Borrakh Peñadiente después de un accidente que mató a tres hombres en un depósito militar. No por principio. Porque Borrakh le había dado su propia ración durante tres semanas cuando Renwick tenía fiebre en el campo. Nadie se lo pidió. Renwick decidió que eso valía tres cadáveres. No está seguro de que fuera la cuenta correcta.

Borrakh Peñadiente también está en esta sala.

---

## Borrakh Peñadiente — El Medio-Orco Que Llegó Antes

Treinta y ocho años, dos metros y anchura de puerta. Colmillos que nunca limó porque decidió que la gente que huye de su aspecto es gente con quien no vale la pena hablar. Manos marcadas de trabajo de fragua. Una cicatriz larga en la mejilla izquierda que termina exactamente donde empieza la mandíbula.

Viaja a Triboar donde lo espera trabajo honesto. Eso es todo lo que quiere: trabajo honesto y que nadie lo señale. Lleva ocho meses sin alcohol, sin que nadie lo sepa, sin que nadie necesite saberlo. Pide agua cuando todo el mundo pide cerveza y no explica por qué, porque las explicaciones son el tipo de conversación que inevitablemente termina en el lugar donde empezó.

Esta noche lleva la ventaja involuntaria de haber llegado antes que el crimen. Bajó al establo a revisar su yegua una hora antes de que ocurriera y regresó a la sala cuando los caballos se agitaron. Volvió al establo. Encontró el cadáver. Lo tocó para saber si respiraba. Se limpió la mano en el heno. Salió sin gritar porque sabe lo que es un medio-orco con herramientas en la espalda en una posada cerrada por tormenta cuando aparece un hombre muerto y alguien necesita un culpable para antes del amanecer.

Sus huellas están en el heno junto al cuerpo. Eso es todo lo que los investigadores inexpertos necesitarán para construir un caso contra él.

---

## Onno Grist — El Fraile Que No Es Fraile

Gnomo de cincuenta y cinco años con la energía de alguien que duerme menos horas de las que debería y se alimenta de conversación. Pelo blanco caótico. Dedos negros en las yemas izquierdas —tinte de pólvora, no de tinta, aunque los confunde hábilmente. Sonríe con demasiados dientes para inspirar solo confianza.

El hábito de penitente de Ilmater es auténtico pero pequeño para él, heredado de alguien más alto. El símbolo de cadena rota al cuello es funcional. Lo que hay bajo el hábito —una bolsa de cuero que abombea de forma inconsistente con la vida de un fraile— no lo es.

Onno Grist es el agente de los Cuervos de Mirtul en el norte. Esta noche quiere los mapas del cofre de Caelith —solo los mapas, nada más, para venderlos en Luskan a dos compradores distintos antes de que alguien los reclame. El precio máximo se obtiene cuando los dos compradores no saben del otro. Eso Onno lo sabe mejor que nadie.

Durante su «bendición del sótano» de la Escena 2 —anunciada sin que nadie la pidiera, ante la mirada de Wenna como a alguien que acaba de entrar en territorio ajeno— instaló una trampa explosiva de percusión remota bajo la trampilla zhentarim. La activó en el momento más caótico de la Escena 4 para crear distracción y evaluar reacciones. No mató a Selvyn Drask. Pero tenía planificado un segundo uso para la trampa si Selvyn resultaba problemático. Alguien se adelantó.

Tamlin Pell le debe quinientas monedas de oro. Onno lo llama «Hermano Tamlin» con afecto genuino del tipo que se dispensa a un instrumento favorito.

---

## Caelith Brynmar — La Mensajera Prescindible

Dracónida de escamas plateadas que en la luz de chimenea recogen el naranja y lo convierten en bronce. Treinta años —joven para su estirpe, lo que significa que alguien la envió porque era prescindible. Lleva el cofre de hierro con sello de lacre escarlata de la Alianza sobre la mesa esquinera. No se aleja de él. Nunca tiene la espalda sin pared.

El cofre es su misión. Entregarlo. Llegar viva. Ir a casa, si todavía sabe dónde queda.

Lo que Caelith no dice es que abrió el cofre, contra órdenes, en Neverwinter. Leyó las cartas. Su propio comandante de brigada aparece citado como fuente secundaria de información filtrada durante la guerra. No lo reportó porque reportarlo la habría hecho desaparecer antes de que la misión terminara. Lleva cuatro días cargando esto. Las escamas del cuello de Caelith se rizan hacia atrás involuntariamente cuando miente. Solo se nota si alguien la observa muy de cerca.

---

## Tamlin Pell — El Músico Con Demasiadas Deudas

Halfling de veinticuatro años, constitución de alguien que come irregularmente pero bien cuando puede. Ojos castaños rápidos que no se quedan quietos. Toca la mandolina como si la estuviera interrogando —una cuerda remendada, un tono ligeramente plano, todo el instrumento con el aspecto de algo que sobrevivió a demasiados inviernos bajo malos techos.

Tamlin debe quinientas monedas de oro a un prestamista de Luskan. O eso creyó hasta que reconoció la firma del documento de deuda: «Onno Grist». El fraile de Ilmater que lleva la misma bolsa abultada que el gnomo que le prestó el dinero hace dos años usando otro nombre. La tormenta lo encerró con su peor pesadilla con hábito gris. Calcula si puede comprar su deuda entregando información sobre el cofre. Eso lo tiene tan ocupado que no habla de lo que vio en la cocina.

Lo que vio en la cocina: antes del grito que anunció el cadáver, Tamlin subió a buscar agua. Encontró a la herbolaria, Lysse Mourne, lavándose las manos en el cubo de la despensa. Cara completamente normal. Eso es lo que Tamlin recordará: lo normal que tenía la cara.

Cuando llegaron al establo y vio el cadáver, Tamlin entendió lo que había visto. Y decidió callarse. Porque callarse tiene un precio conocido y hablar tiene un precio que no puede calcular.

---

## Sira Veleth — El Silencio Con Ojos Violeta

Piel ébano, ojos violeta pálido que la luz de chimenea convierte en lavanda. Estatura media, casi delgada, pero los movimientos tienen la economía de alguien que sabe exactamente cuánta fuerza necesita cada cosa. La única señal de edad —docenas de años— son las manos: callos que no corresponden a un mercader de seda.

Pagó por una silla en la sala común. No solicitó habitación. No dio más explicaciones.

Sira Veleth es operativa Harper, asignada encubierta a escoltar el cofre de Caelith hasta que cruce el paso. Llegó primero a la posada. No reveló su misión a Wenna, aunque Wenna ya la sospecha. No la reveló a Caelith, que la teme instintivamente sin saber por qué —la ironía de que Sira sea su protectora desconocida la destruirá cuando alguien se lo diga.

Pero Sira lleva instrucciones secundarias. Si encontraba a Lysse Mourne, evaluar si podía ser reincorporada a los Harpers o debía ser eliminada. Ahora Lysse acaba de matar a un hombre. Eso simplifica la decisión hacia un lado que Sira no estaba completamente segura de querer tomar.

También sabe —porque pasó silenciosa por la posada durante la noche, inspeccionando lo que otros no inspeccionaron— que la puerta oculta de la cocina tiene los goznes recién aceitados. Que Lysse no estaba en la sala cuando los caballos gritaron. Que Tamlin vio a alguien en la cocina lavándose las manos. Sira tiene tres vectores. La conclusión es directa. Lo que no cierra sola es quién preparó los goznes, quién le dio la hora a Lysse, por qué la puerta ya estaba lista antes de que Lysse la buscara.

Para llegar a Wenna, la sala necesita cavar más. Sira podría decirles hacia dónde cavar. Todavía está decidiendo si lo hará.

---

# SEGUNDA PARTE: LO QUE OCURRIÓ ANTES

## Seis Días Antes

Durvis Hakk envía al contacto zhentarim en Neverwinter la lista de huéspedes esperados para la posada. Entre ellos: Caelith Brynmar con el sello de la Alianza. Los Zhentarim ordenan recuperar el cofre a cualquier precio. «Cualquier precio» es una instrucción amplia. Durvis la interpreta con la amplitud que le conviene.

## Cuatro Días Antes

Selvyn Drask recibe información de un informante en el archivo de Neverwinter: hay un expediente sobre sus actividades de chantaje. Selvyn lleva dos semanas investigando a Durvis Hakk para los Harpers, y la coincidencia de cronologías lo pone nervioso. Más nervioso todavía cuando se entera de que Lysse Mourne —a quien mencionó en una conversación sobre «deudas pendientes de la guerra» creyendo que podía usarla para presionarla más tarde— conocía la investigación. Selvyn cometió el error de hablar antes de tiempo con la persona equivocada.

## Tres Días Antes

Lysse decide que Selvyn va a hablar demasiado pronto. Prepara el compuesto sedante, calcula el método, planifica la ruta de salida. No hay rabia en esto. Es aritmética.

## Dos Días Antes

Sira Veleth recibe instrucción Harper: escoltar el cofre de Caelith de forma encubierta. Llega primero a la posada. No revela nada a nadie.

## La Mañana Del Día

Selvyn llega temprano y pasa el día redactando sus cuatro notas de chantaje. Entrega tres durante la tarde. Guarda la cuarta.

Cada NPC que recibe una nota pasa el resto de la tarde con un centímetro menos de espalda.

## La Tarde Del Día — El Punto de Inflexión

Wenna recibe su nota. Lee. Piensa. Observa al notario circular por la sala. Ata los cabos.

Wenna unta los goznes de la puerta oculta con aceite de su frasco personal. Busca a Lysse con tazas de infusión. Le murmura tres cosas al pasar. La hora. La ruta. El estado de los goznes.

Lysse escucha. Sube a su cuarto. Le pasa a Wenna una nota de cuatro palabras.

Wenna la quema en la chimenea. Casi del todo.

## La Hora Segunda — La Hora Del Chantaje

Selvyn le comunica a Lysse la hora de la cita en el establo: la segunda campanada. «Si no venís, el informe sobre vuestra identidad Harper llega a Skullport mañana por la mañana.» Lysse no dice nada. Se va a preparar infusiones en la cocina. Entre la cocina y su cuarto, comprueba la puerta oculta al establo. Los goznes están mudos. No tiene que hacer nada más.

## Antes De Las Dos Campanadas

Lysse va a la cocina con la excusa de preparar una tisana para «el herido del tercer cuarto»: Renwick. Nadie verifica esto en el momento. En la cocina prepara la taza con extracto de adormidera y verbena. El residuo del compuesto queda en el cubo de la despensa cuando se limpia. Sale al establo por la puerta oculta de la estantería. Cuatro metros de pasillo. Sin sonido de goznes.

Deja la taza en el poste del tercer pesebre. Se retira al cuarto pesebre a esperar.

## Las Dos Campanadas

Selvyn entra al establo por la puerta principal del patio. Encuentra la taza. La bebe. Es amarga, pero no más que su té habitual.

Lysse sale del hueco del cuarto pesebre. La conversación dura tres minutos.

En el minuto cuatro, Selvyn siente los brazos pesados. En el minuto seis, Lysse descuelga el cubo de madera del gancho del tercer pesebre. Golpe único. Descendente. Sien derecha. El trabajo dura tres segundos.

Los caballos se agitan. Lysse vuelve a colgar el cubo en su gancho. Pone el cuadernillo en la mano del cadáver. Destruye la página de la cita. Sale por la puerta oculta de la estantería. Cuatro minutos de vuelta. Se lava las manos en el cubo de la despensa.

## Justo Después

Borrakh, que había bajado al establo una hora antes a revisar su yegua y se había quedado en las inmediaciones oyendo los ruidos de los caballos, vuelve a pasar. Encuentra el cadáver. Lo toca. Se limpia la mano en el heno. Sale sin gritar. Sus huellas quedan impresas en el heno.

## Tres Minutos Después

Tamlin sube a la cocina a buscar agua. Encuentra a Lysse lavándose las manos. Cara completamente normal. Tamlin asiente y no dice nada.

## Poco Después

El grito llega desde el establo. La sala baja.

---

# TERCERA PARTE: LAS CINCO ESCENAS

## Escena 1 — «El Paso No Perdona»

La jaula se cierra.

Cuando la ventisca termina de sellar las salidas y Wenna anuncia que nadie parte hasta el amanecer —«La tormenta no pide permiso. Vosotros tampoco vais a empezar»— lo que queda es la suma de todos los motivos que trajeron a cada persona aquí convertida en una ecuación de silencio y vigilancia mutua.

El cofre de Caelith está sobre la mesa esquinera, con el sello de la Alianza de los Lordes visible para quien sepa leerlo. Selvyn Drask ya está instalado, cuadernillo sobre la mesa, haciendo preguntas de procedimiento a los recién llegados con la amabilidad chirriante de alguien que toma nota de todo. Borrakh entra mojado hasta los huesos y pide solo agua. Tamlin toca la mandolina —una canción de Neverwinter que hace que Durvis Hakk se detenga una fracción de segundo en lo que sea que estuviera haciendo. Onno Grist propone una bendición de viaje. Es la segunda vez esta tarde. No deja de hablar. Sira Veleth paga por una silla y no da más explicaciones.

La chimenea de la sala común se apaga de golpe. Todas las llamas, simultáneamente. Sin corriente visible. La sala queda en luz de lámpara. Del exterior llega un grito de caballo: uno solo, agudo, sostenido, que se corta en seco. Borrakh se pone de pie a medias. Sira no levanta los ojos de su copa. Wenna dice, mirando la puerta del fondo: «Los caballos notan la tormenta antes que nosotros. Seguid bebiendo.»

La chimenea se reaviva sola treinta segundos después, desde las brasas.

La jaula está cerrada.

Hay algo bajo la chimenea que nadie ha visto todavía: entre las cenizas de la tarde, un fragmento de papel quemado pero no del todo consumido. Quien lo encuentre y lo lea verá texto en letra cuidadosa y ordenada —la de alguien acostumbrado a llevar libros de cuentas, no la de Selvyn con su escritura apretada y nerviosa: «...est. 2ª camp...» No significa nada todavía. Significará todo cuando la impronta del cuadernillo la complete.

---

## Escena 2 — «La Gota En El Techo»

La paranoia empieza antes de que haya víctima.

Un líquido oscuro y viscoso gotea desde las vigas sobre la mesa central. Es de Renwick —herida en la mano derecha reabierta en la habitación 3, donde practicaba con los vendajes cuando alguien oyó algo pesado arrastrado en el piso de arriba. Nadie admite haber subido. Borrakh miente sobre el horario.

Selvyn hace tres visitas breves y separadas a tres NPCs distintos. En cada una, el NPC consultado se pone rígido. Nunca se queda más de dos minutos. La sala lo observa y no dice nada, porque nadie quiere ser el siguiente en la lista.

Un investigador que suba al primer piso encontrará la habitación 3 con sangre en el suelo y la puerta sin pestillo. Un investigador que inspeccione la cocina encontrará la puerta oculta detrás de la estantería ligeramente desencajada. Los goznes recién aceitados. Si busca específicamente los goznes, el aceite de linaza es tan fresco que destella.

En la habitación 2 —la de Lysse— un investigador que revise la bolsa herbolaria encontrará que falta un vial pequeño sin marcar. Lysse, si se le pregunta, explica sin vacilar: «Se lo presté a Renwick para la inflamación de la mano.» Renwick, si se le consulta directamente: «Me ofreció algo. Lo rechacé. No tomo nada de extraños.» La coartada del vial colapsa ante cualquier confrontación cara a cara.

Un observador con el entrenamiento correcto que observe a Wenna y Lysse en el mismo campo visual nota algo inusual: las dos mujeres nunca se dirigen la palabra ni se miran directamente, aunque Wenna pasa cerca de Lysse al repartir bebidas. La sincronía del no-contacto es demasiado ordenada para ser indiferencia natural entre desconocidas.

El cierre de la escena: un sonido de algo pesado arrastrado en el piso de arriba. Luego: drip. Drip. Drip. El líquido oscuro sigue cayendo. Algo cae al suelo arriba. Silencio total. Y entonces, con calma pasmosa, Selvyn Drask pasa por la sala en dirección a la cocina con el cuadernillo bajo el brazo. Sonríe al pasar. Nadie sabe a dónde va.

---

## Escena 3 — «El Trabajo De La Noche»

El asesinato.

El grito llega desde el establo. Los caballos patean. No es el viento.

Selvyn Drask yace desplomado contra la pared del tercer pesebre. Ojos abiertos. En la mano aprieta todavía el cuadernillo, abierto en una página en blanco, como si todavía estuviera tomando notas. Traumatismo visible en la sien derecha. El farol está apagado. El heno tiene el olor de los caballos que no se calman.

La primera conclusión, la que se impone antes de que nadie piense: una coz. No debería haber estado aquí de noche. La primera conclusión está equivocada.

El ángulo de la herida no corresponde a una coz de caballo. Las coces viajan en horizontal o hacia arriba. Esta herida impactó desde arriba y ligeramente por detrás, consistente con un golpe en arco descendente. Asesinato. No accidente.

Las huellas de bota en el heno junto al cuerpo son de talla de medio-orco. La sala mira a Borrakh. Borrakh acaba de llegar, mojado, desde la puerta principal del establo. «Lo encontré. Lo toqué. No lo maté.» La sala sigue mirando a Borrakh. Pero un investigador más cuidadoso que encuentre las dos series de huellas en el heno verá que las huellas grandes son más antiguas y lineales —Borrakh cuando encontró el cadáver— mientras que las huellas medianas son más recientes y emergen desde el panel de la pared oeste, no desde la puerta principal.

En los labios del cadáver, un residuo amargo y herbal. Compuesto inductor del sueño. Bebió algo poco antes de morir.

El cuadernillo está abierto en una página en blanco. Pero la página tiene la presión del bolígrafo de la hoja anterior. Con carbón frotado sobre la superficie emerge: «L.M. — 2ª campanada.» Selvyn tenía cita de chantaje con alguien cuyas iniciales son L.M. a la segunda campanada. La asesina destruyó la página pero no la impronta.

Lysse Mourne se ofrece a examinar el cadáver. Lo hace con calma metódica. Anuncia «traumatismo, posiblemente una coz» sin vacilar. No menciona el olor a sedante en los labios que ella misma reconocería al instante. Está controlando qué información llega a la sala desde la posición de la «experta».

Sira, desde el umbral del establo, sin que nadie se lo pida: «El único que salió por la cocina esta noche fue alguien que conocía la puerta. Eso recorta la lista.» No elabora. No necesita elaborar.

Tamlin no puede mirar a Lysse desde que entró al establo. Si alguien construye suficiente confianza con él, si lo encuentra a solas con el ángulo correcto de conversación: «Estaba en la cocina. Tarde. Antes del grito. Lavándose las manos. La cara completamente normal. Eso es lo que recuerdo. Lo normal que tenía la cara.»

Cuando se anuncia la muerte, Wenna hace una sola pregunta: si el establo está cerrado ahora. Solo eso. Es la pregunta de alguien que ya sabe lo que ocurrió y quiere saber si la ruta quedó comprometida.

**Las falsas pistas:** La tierra arcillosa rojiza en el suelo del tercer pesebre apunta al túnel y a Durvis Hakk, pero la tierra está seca y endurecida —tráfico histórico, no de esta noche. En el piso superior, la ventana este de la habitación 5 muestra escarcha alterada en el alféizar y pizarras desplazadas en la cubierta del establo. Parece que alguien bajó al establo por esa ruta. Pero Renwick estaba allí vigilando el patio buscando a Durvis —no descendió. Borrakh lo vio en la ventana antes del grito.

La pared interior del establo emite al final de la escena un sonido de madera moviéndose. El panel oculto conectado a la cocina oscila solo, despacio, hacia adentro. Los goznes no crujen. Recién aceitados. Nadie visible al otro lado.

---

## Escena 4 — «El Precio Del Cofre»

Las facciones salen del armario.

Durvis pone una bolsa de monedas sobre la mesa. «Ese cofre se abre esta noche o yo abro algo más. La única duda es cuántos de vosotros van a estar vivos para ver qué hay dentro.»

Sira baja la capucha por primera vez. Sus rasgos drow quedan visibles. «He esperado suficiente a que esto se resuelva solo.» Se sienta sin pedir permiso.

Lo que hay en el cofre: un vial de plaga sellada que prueba que la Alianza usó armas biológicas contra civiles durante la Guerra de la Corona. Mapas de arsenales bajo el Paso —cuatro depósitos que conectan directamente con la bodega zhentarim de la posada. Cartas de chantaje entre oficiales de la Alianza y agentes zhentarim. Una nombra al Comandante Halvek Byrne.

Cuando ese nombre se lee en voz alta, Renwick para de cualquier cosa que estuviera haciendo. Dice en voz baja, sin rabia: «Mi familia vivía en el ramal norte del paso. Seis personas. Durvis vendió las rutas. Byrne firmó el informe que decía que el ataque fue un error de navegación.» Y espera a ver qué hace la sala.

Sira revela lo que sabe sobre Selvyn: no era solo un extorsionista. Llevaba seis meses construyendo el caso real contra la red zhentarim para los Harpers. La sala entiende que la muerte de Selvyn no es solo un asesinato. Es el cierre de la única línea de acusación válida contra Byrne. Y Lysse lo sabía cuando lo mató. El expediente perdió contra su supervivencia.

Wenna confiesa el túnel si alguien la acusa directamente de encubrir el asesinato. Lo hace con calma clínica: «El túnel lleva tres años ahí. No lo construí para matar a nadie —lo construí para no morir de hambre. Durvis pagó. Yo abrí el suelo. Eso es todo lo que fue.»

Si Lysse es confrontada con la cuarta nota: «Selvyn tenía algo que me habría costado todo. Elegí qué valía más. Si eso os parece un crimen, contad los cuerpos de todos los presentes antes de pronunciar sentencia.»

El cierre de la escena: un golpe sordo desde debajo del suelo, en dirección a la cocina. Luego un BANG —pequeño, seco, percusivo— y la trampilla oculta bajo la leña salta medio palmo de su encaje, escupiendo humo acre y el olor de pólvora. Onno Grist, en el umbral de la cocina, se detiene. Cara neutral. «Alguien activó mi seguro.»

---

## Escena 5 — «El Último Trago»

Standoff. Un trago de licor sin etiqueta. La verdad o la bala.

Wenna saca de bajo la barra la botella sin etiqueta. «Un trago por cabeza. Después que los dioses decidan.»

Lysse, si no ha sido detenida, intenta salir por la puerta oculta de la cocina hacia el establo y de ahí al exterior. Si nadie lo nota, Wenna anuncia cuando ya tiene la mano en el panel de la estantería.

Cada persona en la sala declara su posición. Dónde está físicamente. Qué tiene en la mano o preparado. A quién vigila. Lo que dice en voz alta en este momento. No hay iniciativa. No hay rondas. Es cine.

Renwick dice el nombre completo de Durvis Hakk. Le dice el año. Le dice el nombre de su hermano. Y espera.

Onno ofrece neutralizar el vial si alguien le garantiza inmunidad para sus actividades en el sótano. «Tengo los reactivos. No soy un fraile —eso ya lo sabéis. Pero sé química.»

---

# CUARTA PARTE: LAS CAPAS DE LA VERDAD

## La Primera Capa — Quién Mató a Selvyn

Lysse Mourne. Con compuesto sedante en una taza y un cubo de madera del gancho del tercer pesebre. En el establo. Salió por la puerta oculta de la cocina. Se lavó las manos. Subió. No le temblaron.

Eso es la superficie.

## La Segunda Capa — Quién Hizo Posible El Asesinato

Wenna Corren no ejecutó el crimen. Pero le dio a Lysse la hora exacta de la cita en el establo. Le indicó la ruta. Preparó el acceso lubricando los goznes con su aceite personal —marcado con «W» en el corcho— para que la puerta no crujiera. Y quemó la confirmación de Lysse en la chimenea de la sala común. Casi del todo.

El fragmento quemado, la nota bajo la barra, el frasco de aceite marcado «W» en el corredor trasero: tres pistas que apuntan a la misma dirección. La línea entre «informar» y «ordenar» es la única defensa que le queda a Wenna. Y lo sabe mejor que nadie.

## La Tercera Capa — Lo Que Se Perdió

Selvyn Drask era el único que estaba construyendo el caso contra la red zhentarim de Durvis Hakk. Sin ese expediente —y el sistema de respaldo que Selvyn afirmaba tener y que no existía— la única acusación formal posible contra Durvis y contra el Comandante Byrne se fue con el cadáver al establo.

Lysse calculó ese precio y decidió que valía menos que su vida. La sala tiene que decidir si le da la razón.

Wenna calculó que proteger la posada valía más que el notario que la amenazaba. La sala tiene que decidir si le da la razón también.

Dos mujeres. Dos cálculos. Los dos fríos. Los dos comprensibles de la manera en que son comprensibles las cosas que se hacen cuando no queda otra salida. Los dos irreversibles.

---

# QUINTA PARTE: EL MAPA DE LAS PISTAS

## Pistas Verdaderas

**Pista 1 — El Ángulo de la Herida** *(Fácil, CD 10 Medicina)*
Establo. El ángulo del impacto en la sien derecha de Selvyn no corresponde a una coz de caballo. Las coces viajan en horizontal o hacia arriba. Esta herida impactó desde arriba y por detrás: golpe deliberado en arco descendente. Elimina el accidente. Confirma asesinato.

**Pista 2 — El Residuo Sedante** *(Media, CD 13 Medicina)*
Labios del cadáver. Residuo amargo de compuesto herbal inductor del sueño —adormidera de base, algo más amargo debajo. Selvyn bebió algo antes de morir. Apunta explícitamente a un herbolario.

**Pista 3 — La Impronta del Cuadernillo** *(Difícil, CD 15 Investigación + carbón)*
Cuadernillo de Selvyn, página «en blanco» después de los tres nombres visibles. Con carbón frotado sobre la superficie: «L.M. — 2ª campanada.» Las iniciales y la hora. La conexión directa entre Selvyn y Lysse Mourne en el establo esta noche.

**Pista 4 — Las Dos Series de Huellas** *(Media-Difícil, CD 13 Investigación)*
Establo, heno. Las huellas grandes son más antiguas y lineales —Borrakh, que llegó antes del crimen. Las medianas son más recientes y emergen desde el panel de la pared oeste —la ruta de Lysse esta noche.

**Pista 5 — El Vial Vacío y la Coartada Imposible** *(Media, CD 12 Investigación + confrontación)*
Habitación de Lysse. Falta un vial pequeño sin marcar de la bolsa herbolaria. Lysse afirma haberlo prestado a Renwick. Renwick lo niega directamente. La coartada del vial se derrumba ante cualquier confrontación cara a cara.

**Pista 6 — Tamlin Pell, Testigo** *(Conversacional, CD 12 Persuasión)*
Cocina, tarde. Antes del grito. Tamlin vio a Lysse lavándose las manos. Cara completamente normal. La frase que lo recorre cuando la repite: «Lo normal que tenía la cara.»

**Pista 7 — El Residuo Herbal en el Cubo de la Despensa** *(Media, CD 13 Investigación)*
Cocina. Rastro verdoso en el interior del cubo de agua. Adormidera y verbena. Donde Lysse preparó la taza sedante y se limpió después.

**Pista 8 — Los Goznes y el Panel** *(Fácil-Media, CD 11 Investigación)*
Cocina, corredor trasero. Los goznes tienen aceite de linaza tan fresco que destella. El panel está ligeramente desencajado —usado esta noche, en ambas direcciones.

---

## Pistas del Cómplice — El Camino a Wenna

**Pista Cómplice A — El Fragmento Quemado** *(Fácil-Media, CD 12 Investigación)*
Chimenea de la sala común. Fragmento de papel no del todo consumido. Texto en letra cuidadosa y ordenada —no la de Selvyn: «...est. 2ª camp...» Quien compare con el libro mayor de Wenna confirma la autoría. Combinado con la impronta del cuadernillo: alguien comunicó la cita a Lysse por escrito.

**Pista Cómplice B — La Nota Bajo la Barra** *(Difícil, CD 14 Investigación)*
Detrás de la barra, bajo el mostrador, en una tabla suelta de la segunda repisa inferior. Texto: «Entendido. Esta noche.» Letra de Lysse, confirmable comparando con las etiquetas de su kit herbolario. Cierra el caso de la conspiración.

**Pista Cómplice C — El Frasco de Aceite Marcado** *(Media, CD 13 Investigación)*
Cocina, corredor trasero. Frasco pequeño de aceite de linaza con una «W» grabada en el corcho. Marca de inventario personal de Wenna, distinta del aceite de cocina general. El frasco fue usado recientemente. Fue Wenna quien preparó el acceso, no Lysse.

**Pista Cómplice D — El No-Contacto Coordinado** *(Perspicacia, CD 14 Perspicacia)*
Sala común. Wenna y Lysse nunca se miran directamente ni se dirigen la palabra, aunque Wenna pasa cerca de Lysse al repartir bebidas. La sincronía del no-contacto es demasiado ordenada para ser indiferencia natural entre dos mujeres que teóricamente no se conocen.

---

## Falsas Pistas

**Falsa Pista 1 — Las Huellas de Borrakh** *(CD 11 Investigación, disprove CD 13)*
Huellas de talla de medio-orco en el heno. Apuntan directamente a Borrakh. Pero son más antiguas que las medianas que vienen del panel oeste. Borrakh estuvo en el establo —una hora antes del crimen, a revisar su yegua. Encontró el cadáver. Tocó el cuerpo. Salió. No mató.

**Falsa Pista 2 — La Tierra Rojiza de Durvis** *(CD 12 Investigación, disprove CD 13)*
Tierra arcillosa rojiza en el suelo del tercer pesebre, distintiva del sistema de túneles zhentarim. Apunta a Durvis, que tiene la llave del túnel. Pero la tierra está seca y endurecida: tráfico histórico, no de esta noche. Las huellas frescas vienen del panel de la pared oeste.

**Falsa Pista 3 — La Ventana de Renwick** *(CD 12 Investigación, disprove CD 14 Perspicacia a Borrakh)*
Escarcha alterada en el alféizar de la ventana este del piso superior y pizarras desplazadas en la cubierta del establo. Parece que alguien bajó al establo por esa ruta. Pero Renwick estaba en la ventana vigilando el patio buscando a Durvis, no descendió. Borrakh lo vio allí antes del grito.

---

# SEXTA PARTE: LA REVELACIÓN QUE CAMBIA TODO

Hay un momento en la Escena 4 —cuando Sira baja la capucha y dice «el notario muerto llevaba seis meses construyendo el caso para demostrarlo»— en que el eje moral de la sala gira.

Selvyn Drask no era solo el villano de la noche. Era el único que estaba haciendo algo importante. Su muerte no es solo un asesinato: es el cierre de la única línea de acusación válida contra la red zhentarim de Durvis Hakk y contra el Comandante Byrne, el hombre que firmó el informe que enterró el ramal norte bajo la etiqueta de «error de navegación».

Lysse lo sabía. Calculó cuánto valía el expediente versus cuánto le costaba su supervivencia. El expediente perdió.

Y entonces la pregunta —la que no tiene respuesta limpia— es esta: Lysse mató a alguien despreciable que estaba haciendo algo necesario. ¿Cuánto pesa eso?

Y la segunda pregunta, que llega inmediatamente después: Wenna abrió una puerta para que Lysse pudiera hacerlo. ¿«Abrir una puerta» y «ordenar una muerte» son la misma cosa cuando sabes exactamente qué va a pasar después?

Wenna no dio ninguna orden. No dijo «mátalo». Lo que hizo fue construir las condiciones —la información, el acceso, el silencio de los goznes— para que el asesinato fuera posible. La distinción es real. La distinción también es exactamente el tipo de distinción que los culpables usan para dormir.

---

# SÉPTIMA PARTE: LO QUE SIRA SABE Y LO QUE NO PUEDE CERRAR SOLA

Sira Veleth sabe que Lysse es la asesina. La conclusión le llevó tres vectores.

Primero: Lysse no estaba en la sala cuando los caballos gritaron. La ausencia es un hecho, no una suposición.

Segundo: Tamlin la vio en la cocina de madrugada, lavándose las manos, antes de que encontraran el cadáver. Sira dedujo que alguien tenía que haberla visto.

Tercero: Inspeccionó la posada en silencio durante la noche y encontró la puerta oculta de la cocina con los goznes recién aceitados.

Con estos tres vectores, la conclusión sobre Lysse es directa. Lo que Sira no cierra sola es la capa de Wenna. No sabe quién preparó los goznes. No sabe quién le dio la hora a Lysse. Para llegar a Wenna, los investigadores necesitan el fragmento quemado de la chimenea, el frasco de aceite marcado «W», y la nota bajo la barra. O confrontar a Wenna con la evidencia combinada hasta que la coartada de «no supe nada» no sostenga el peso.

---

# OCTAVA PARTE: EL COFRE Y SUS CINCO DUEÑOS

El cofre de Caelith Brynmar es el eje gravitacional de todo lo que no tiene que ver directamente con el asesinato. Cinco facciones, cinco objetivos incompatibles.

La **Alianza de los Lordes** (Caelith) quiere recuperar el vial de plaga y los mapas de arsenales —y destruir las cartas. Silenciar el escándalo. Caelith sabe que el nombre de su propio comandante de brigada está en esas cartas, y sabe que reportarlo la habría hecho desaparecer.

Los **Zhentarim** (Durvis) quieren el vial y los mapas. Las cartas no les importan —ya saben lo que dicen, porque parte de la correspondencia es suya.

Los **Cuervos de Mirtul** (Onno) quieren solo los mapas. Para venderlos en Luskan a dos compradores distintos. El precio máximo requiere que los dos compradores no se enteren del otro.

Los **Harpers** (Sira) quieren destruir el vial —que no llegue al mercado negro— y exponer las cartas. No silenciarlas. Usarlas para purgar oficiales corruptos. La diferencia entre Sira y la Alianza es exactamente esa.

**Renwick Sorn** no representa ninguna facción. Solo quiere las cartas. El nombre del Comandante Byrne ante un tribunal.

El dilema moral central del cofre es el mismo que el de Selvyn: no hay salida limpia. Destruir el vial protege al mundo pero elimina la única prueba física de los crímenes. Exponer las cartas da justicia pero destruye carreras. No hay salida limpia. La sala tiene que elegir cuál suciedad puede tolerar.

---

# NOVENA PARTE: LOS GANCHOS DE LOS PERSONAJES JUGADORES

Los personajes jugadores entran a esta historia desde cuatro ángulos que no son accidentales.

**El Testigo Incómodo** lleva semanas huyendo hacia el norte después de ver en Neverwinter a un oficial de la Alianza reuniéndose en las sombras con alguien. El intercambio podría haber sido las cartas del cofre. Wenna lo reconoció: el oficial es el Comandante Byrne. No lo dice de entrada, pero lo observa con más atención que al resto. Si el testigo usa las cartas, tiene poder sobre alguien poderoso. Si las destruye, pierde su única protección. Si las entrega a Renwick, obtiene un aliado improbable. El oficial sabe que fue visto. Ya no es seguro al sur del Paso.

**El Deudor** transportaba un paquete para los Cuervos de Mirtul —pago parcial de deuda. No sabía que su acreedor estaría aquí esta noche. Cuando ve a Onno Grist con el hábito de Ilmater, el reconocimiento es un golpe frío. Tamlin lo reconoce de una sala de juego en Neverwinter —nunca olvida una cara endeudada. Onno le ofrece cancelar la deuda a cambio de los mapas del cofre. En un mes, si no paga, la deuda se activa de otra forma. Onno no dice de cuál forma. Esa vaguedad es el método.

**El Soldado de la Corona** llegó siguiendo un rumor sobre un arsenal enterrado bajo el Paso. Participó en la campaña donde se usó la plaga. No la ordenó —la vio. No la reportó porque el oficial que la ordenó le salvó la vida dos días antes. Ese nombre está en las cartas. El vial de plaga es evidencia de algo que él tapó: destruirlo lo salva, entregarlo lo destruye, dejarlo en manos zhentarim es una tercera catástrofe. Sira lo identificó en Neverwinter como testigo potencial. No lo dice todavía.

**El Mensajero Sin Mensaje** llevaba un mensaje para Caelith Brynmar interceptado en ruta y sustituido por una copia falsificada —probablemente por Durvis. La copia falsa dice que el cofre está seguro. El mensaje real avisaba a Caelith de que había sido comprometido. Sira sabe que existe el mensaje original. No sabe que este personaje lleva la copia. Cuando lo descubra, la reacción de Sira dirá mucho sobre sus prioridades reales.

---

# DÉCIMA PARTE: LOS FINALES POSIBLES

**Final A — El Archivo Abierto:** Los Harpers se llevan el cofre. Las cartas se exponen. Renwick obtiene la justicia que lleva dos años buscando. El Comandante Byrne comparecerá ante un tribunal, o morirá intentando evitarlo. Caelith desaparece en algún archivo de la Alianza.

**Final B — El Entierro:** El vial se destruye. Las cartas quedan enterradas con la nieve. El escándalo nunca sale. Renwick no obtiene nada. La red zhentarim continúa operando. Este final es el más limpio operacionalmente y el más sucio moralmente.

**Final C — La Fuga Por El Túnel:** Alguien usa el túnel para escapar. La pregunta sobre Byrne y el ramal norte queda abierta indefinidamente. El cofre podría terminar en cualquier lugar o bajo la nieve hasta la primavera.

**Final D — La Masacre:** Seis cuerpos más que enterrar cuando pare la tormenta. El cuervo blanco del umbral no dice nada. Nunca lo hace.

**Final E — La Tregua Con Precio:** Los Harpers obtienen el cofre con acceso. Sira negocia confesiones parciales —cada NPC paga un precio, ninguno el precio completo. Durvis sale sin el ramal norte sobre la mesa pero con el túnel comprometido. Wenna sale con la posada intacta pero con la connivencia documentada. Lysse sale con el crimen conocido pero con las circunstancias atenuadas. Renwick obtiene las cartas pero no el tribunal. La tregua de la nieve. El tipo de acuerdo que la gente hace cuando la alternativa es la masacre y todos lo saben.

---

# UNDÉCIMA PARTE: LA PREGUNTA QUE SE QUEDA EN LA SALA

Wenna va a seguir sirviendo copas cuando pare la tormenta. Lysse va a seguir viajando con su bolsa de herbolaria y sus ojos avellana que son cálidos hasta que se fijan en algo. Renwick va a seguir contando en silencio. El Comandante Byrne va a seguir firmando informes en Neverwinter si nadie lleva las cartas hasta su escritorio.

Selvyn Drask va a seguir muerto.

La pregunta central de la noche —la que el Máster nunca anuncia, que los jugadores encuentran solos cuando cavan suficiente— no es quién mató a Selvyn Drask. Eso es mecánica. La pregunta real es si cambia algo que alguien lo hubiera evitado.

Lysse mató a alguien que hacía algo importante. Wenna abrió una puerta para que pudiera hacerlo. Borrakh encontró el cadáver y calló. Tamlin vio a la asesina y miró para otro lado. Sira sabía y calculó el momento correcto para decirlo. Durvis construyó las condiciones para que ninguna de las personas en esa sala pudiera confiar en ninguna otra.

La tormenta no pide permiso.

Y cuando pase, la posada del Paso Helado va a seguir ahí, con su chimenea de piedra negra y su reloj de arena roto y su botella sin etiqueta bajo la barra que Wenna reserva para el día que alguien diga una verdad entera en este paso.

El cuervo blanco del umbral sigue en su poste. Nadie sabe si graznó durante la noche.

---

*Fin de la sinopsis narrativa.*
