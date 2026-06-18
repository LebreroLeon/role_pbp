"""Simulate realistic scenes for CampañaTest (Prólogo and scene 2)."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete, or_, select

from app.core.database import SessionLocal
from app.models.campaign import Campaign, CampaignEntity, CampaignMemory, Scene
from app.rules.registry import get_plugin
from app.schemas.entities import EntityType
from app.schemas.scene import (
    DiceRollRequest,
    NpcPresenceEntry,
    PostMessageRequest,
    SceneCreate,
    ScenePresenceUpdate,
    SceneTurnManagementUpdate,
)
from app.services.entities import validate_entity_document
from app.services.scenes import (
    close_scene,
    create_scene,
    load_scene_state,
    post_message,
    roll_scene_dice,
    save_scene_state,
    update_scene_npc_presence,
    update_scene_turn_management,
)


CAMPAIGN_NAME = "CampañaTest"
FOREST_ENEMY_NAME = "Acechador del bosque"


async def find_campaign(db, name: str) -> Campaign:
    campaign = await db.scalar(select(Campaign).where(Campaign.name == name))
    if campaign is None:
        raise SystemExit(f"Campaign not found: {name!r}")
    return campaign


async def load_campaign_context(db, campaign_id: uuid.UUID) -> dict:
    from app.models.user import CampaignMember, User
    from app.services.combat_resolver import entity_display_name

    members = (
        await db.execute(
            select(User, CampaignMember.role)
            .join(CampaignMember, CampaignMember.user_id == User.id)
            .where(CampaignMember.campaign_id == campaign_id)
            .order_by(CampaignMember.joined_at.asc())
        )
    ).all()

    entities = (
        await db.scalars(
            select(CampaignEntity)
            .where(CampaignEntity.campaign_id == campaign_id)
            .order_by(CampaignEntity.entity_type, CampaignEntity.created_at)
        )
    ).all()

    master_id: str | None = None
    players: list[tuple[str, str]] = []
    for user, role in members:
        uid = str(user.id)
        label = user.display_name or user.email
        if role == "MASTER":
            master_id = uid
        else:
            players.append((uid, label))

    pcs: list[tuple[str, str, str]] = []
    npcs: list[tuple[str, str]] = []
    for entity in entities:
        name = entity_display_name(entity)
        if entity.entity_type == "PC":
            binding = entity.document.get("player_binding", {})
            user_id = binding.get("user_id") if isinstance(binding, dict) else None
            pcs.append((str(entity.id), name, str(user_id) if user_id else ""))
        elif entity.entity_type == "NPC":
            npcs.append((str(entity.id), name))

    return {
        "master_id": master_id,
        "players": players,
        "pcs": pcs,
        "npcs": npcs,
        "entities": entities,
    }


async def delete_scene_memories(db, campaign_id: uuid.UUID, scene_id: str) -> None:
    scene_uuid = uuid.UUID(scene_id)
    await db.execute(
        delete(CampaignMemory).where(
            CampaignMemory.campaign_id == campaign_id,
            or_(
                CampaignMemory.metadata_["scene_id"].as_string() == scene_id,
                CampaignMemory.id == scene_uuid,
            ),
        )
    )


async def delete_campaign_scenes(db, campaign_id: uuid.UUID) -> list[str]:
    scenes = (
        await db.scalars(select(Scene).where(Scene.campaign_id == campaign_id))
    ).all()
    scene_ids = [str(scene.id) for scene in scenes]
    if not scene_ids:
        return []

    for sid in scene_ids:
        await delete_scene_memories(db, campaign_id, sid)
    await db.execute(delete(Scene).where(Scene.campaign_id == campaign_id))
    await db.commit()
    return scene_ids


async def delete_scene_by_number(db, campaign_id: uuid.UUID, scene_number: int) -> str | None:
    scene = await db.scalar(
        select(Scene).where(
            Scene.campaign_id == campaign_id,
            Scene.scene_number == scene_number,
        )
    )
    if scene is None:
        return None
    scene_id = str(scene.id)
    await delete_scene_memories(db, campaign_id, scene_id)
    await db.execute(delete(Scene).where(Scene.id == scene.id))
    await db.commit()
    return scene_id


async def ensure_forest_enemy_npc(db, campaign: Campaign, ctx: dict) -> tuple[str, str]:
    from app.services.combat_resolver import entity_display_name

    for entity_id, name in ctx["npcs"]:
        if name == FOREST_ENEMY_NAME:
            return entity_id, name

    plugin = get_plugin(campaign.game_system)
    sheet = plugin.default_npc_sheet("medium")
    document = {
        "metadata": {
            "type": "NPC",
            "system_agnostic": False,
            "mechanics_enabled": True,
            "version": "2.0.0",
        },
        "identity": {
            "name": FOREST_ENEMY_NAME,
            "concept": "Emboscador del bosque norte",
            "faction_id": "00000000-0000-0000-0000-000000000002",
            "current_location_id": "00000000-0000-0000-0000-000000000002",
        },
        "ai_narrative_profile": {
            "public_description": "Figura encapuchada con hoja corta y ojos adaptados a la penumbra.",
            "secret_lore_master": "Mercenario a sueldo de quien enciende las luces verdes.",
            "personality_traits": ["sigiloso", "despiadado"],
            "voice_and_tone": "susurro rasposo",
        },
        "system_mechanics": {
            "system_id": plugin.system_id,
            "schema_version": "1.0.0",
            "sheet": sheet,
        },
        "state_flags": {
            "is_dead": False,
            "is_present_in_scene": False,
            "attitude_towards_party": "hostile",
            "has_met_party": False,
        },
    }
    validate_entity_document(EntityType.NPC, document)
    entity = CampaignEntity(
        campaign_id=campaign.id,
        entity_type=EntityType.NPC.value,
        document=document,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)
    name = entity_display_name(entity)
    ctx["npcs"].append((str(entity.id), name))
    return str(entity.id), name


def build_prologue_messages(ctx: dict) -> list[dict]:
    master_id = ctx["master_id"]
    if not master_id:
        raise SystemExit("No MASTER member found in campaign")

    pc_by_user: dict[str, tuple[str, str]] = {}
    for entity_id, name, user_id in ctx["pcs"]:
        if user_id:
            pc_by_user[user_id] = (entity_id, name)

    npc_by_name: dict[str, tuple[str, str]] = {name: (eid, name) for eid, name in ctx["npcs"]}

    def master_narrator(text: str) -> dict:
        return {
            "sender_id": master_id,
            "role": "MASTER",
            "payload": PostMessageRequest(type="ACTION", text=text, speaker_type="NARRATOR"),
        }

    def master_npc(npc_name: str, text: str, *, msg_type: str = "SPEAK") -> dict:
        eid, display = npc_by_name[npc_name]
        return {
            "sender_id": master_id,
            "role": "MASTER",
            "payload": PostMessageRequest(
                type=msg_type,
                text=text,
                speaker_type="NPC",
                speaker_entity_id=eid,
                speaker_display_name=display,
            ),
        }

    def player_speak(user_id: str, text: str, *, msg_type: str = "SPEAK") -> dict:
        return {
            "sender_id": user_id,
            "role": "PLAYER",
            "payload": PostMessageRequest(type=msg_type, text=text),
        }

    victor_id = next((uid for uid, _ in ctx["players"] if uid in pc_by_user), ctx["players"][0][0] if ctx["players"] else "")
    user_id = next((uid for uid, label in ctx["players"] if uid != victor_id), victor_id)

    norman = pc_by_user.get(victor_id, ("", "Norman"))[1]
    userildo = pc_by_user.get(user_id, ("", "Userildo"))[1]
    arturo = "Arturo"
    hijo = "Hijo de Arturo"

    return [
        master_narrator(
            "El camino serpentea entre colinas brumosas. Al amanecer, dos figuras "
            "—" + norman + " y " + userildo + "— avanzan hacia el pueblo de Las Piedras Grises, "
            "con el olor a lluvia reciente aún pegado a las capas."
        ),
        master_narrator(
            "Las murallas de piedra local están remendadas con vigas nuevas. "
            "En la plaza, un herrero ya martillea y un pregonero anuncia toque de queda al anochecer."
        ),
        player_speak(
            victor_id,
            f"«{norman} se detiene junto al cartel de la taberna El Yunque Quebrado y frunce el ceño.» "
            "«¿Oís eso? Parece que hablan de desapariciones en el bosque norte.»",
            msg_type="ACTION",
        ),
        player_speak(
            user_id,
            f"«{userildo} ajusta la correa del pack y asiente con cautela.» "
            "«Prefiero un techo y noticias calientes antes de adentrarnos en el verde. Vamos dentro.»",
        ),
        master_npc(
            arturo,
            "«Un hombre corpulento con delantal de cuero sale del mostrador y os mira de arriba abajo.» "
            "«Bienvenidos al Yunque. Soy Arturo, el tabernero. Si buscáis habitación, quedan dos alcobas arriba.»",
        ),
        master_narrator(
            "La taberna huele a estofado de raíces y cerveza oscura. En un rincón, un muchacho recoge "
            "cucharas dobladas mientras evita la mirada de los recién llegados."
        ),
        player_speak(
            user_id,
            f"«{userildo} se inclina sobre el mostrador.» "
            "«Arturo, ¿qué sabéis de las desapariciones? ¿Algún mercader ha vuelto del camino del bosque?»",
        ),
        player_speak(
            victor_id,
            f"«{norman} se apoya en la barandilla de la escalera, vigilando la puerta.» "
            "«No nos gustan los secretos cuando la noche cae pronto.»",
            msg_type="ACTION",
        ),
        master_npc(
            hijo,
            "«El muchacho —el hijo de Arturo— deja caer una cuchara y susurra sin levantar la vista.» "
            "«Anoche… vimos luces verdes entre los pinos. Mamá dice que no eran luciérnagas.»",
        ),
        master_npc(
            arturo,
            "«Arturo le pone una mano en el hombro al chico y baja la voz.» "
            "«Tres caminantes no llegaron esta semana. La milicia local no tiene hombres de sobra. "
            "Si vais al bosque, llevad hierro y no separéis el grupo.»",
        ),
        player_speak(
            victor_id,
            f"«{norman} descruza los brazos.» "
            "«Podemos echar un vistazo al menos hasta el claro marcado en el mapa del pregonero. "
            "No dejaremos que el pueblo se quede sin respuestas.»",
        ),
        master_narrator(
            "Al caer la tarde, un estrépito sacude la puerta: golpes secos, casi desesperados. "
            "Un granjero entra jadeando, con la ropa rasgada y un corte en la mejilla."
        ),
        player_speak(
            user_id,
            f"«{userildo} corre hacia la entrada y bloquea la hoja dañada con el hombro.» "
            "«¡Quietos! ¿Cuántos hay fuera?»",
            msg_type="ACTION",
        ),
        player_speak(
            victor_id,
            f"«{norman} desenvaina la espada corta y se coloca junto al marco.» "
            "«Userildo, cubro el flanco izquierdo. Arturo, apagad las lámparas del fondo.»",
            msg_type="ACTION",
        ),
        master_narrator(
            "Dos figuras encapuchadas intentan colarse tras el granjero. Una empuña un arco improvisado; "
            "la otra, un cuchillo de carnicero. No parecen una milicia: son desesperados."
        ),
        player_speak(
            user_id,
            f"«{userildo} agarra un taburete y lo lanza contra el arquero, cerrando distancias.» "
            "«¡Suelta el arco o lo lamentarás!»",
            msg_type="ACTION",
        ),
        player_speak(
            victor_id,
            f"«{norman} desarma al segundo intruso con un golpe plano de la espada y lo inmoviliza.» "
            "«Respiráis. El pueblo verá la aurora con vosotros aún con pulso.»",
            msg_type="ACTION",
        ),
        master_npc(
            arturo,
            "«Arturo ata las muñecas del asaltante con cuerda de yugo, temblando apenas.» "
            "«Gracias… si no hubierais estado aquí… Hijo, sube a avisar al alguacil. "
            "Mañana, contadme qué visteis en el bosque antes de marchar.»",
        ),
        master_narrator(
            "La taberna recupera un silencio tenso. Las velas tiemblan cuando el viento entra por la rendija. "
            "Las luces verdes del bosque siguen allí, esperando más allá del camino embarrado."
        ),
        player_speak(
            victor_id,
            f"«{norman} envaina la hoja y mira a {userildo}.» "
            "«Descansamos pocas horas. Al alba, rumbo al bosque norte.»",
        ),
    ]


def build_scene2_messages(ctx: dict, *, enemy_name: str) -> list[dict]:
    master_id = ctx["master_id"]
    if not master_id:
        raise SystemExit("No MASTER member found in campaign")

    pc_by_user: dict[str, tuple[str, str]] = {}
    for entity_id, name, user_id in ctx["pcs"]:
        if user_id:
            pc_by_user[user_id] = (entity_id, name)

    def master_narrator(text: str) -> dict:
        return {
            "sender_id": master_id,
            "role": "MASTER",
            "payload": PostMessageRequest(type="ACTION", text=text, speaker_type="NARRATOR"),
        }

    def player_msg(user_id: str, text: str, *, msg_type: str = "SPEAK") -> dict:
        return {
            "sender_id": user_id,
            "role": "PLAYER",
            "payload": PostMessageRequest(type=msg_type, text=text),
        }

    def player_dice(user_id: str, expression: str, *, skill: str | None = None) -> dict:
        return {
            "kind": "dice",
            "sender_id": user_id,
            "role": "PLAYER",
            "payload": DiceRollRequest(
                dice_expression=expression,
                skill_checked=skill,
            ),
        }

    def master_combat(text: str) -> dict:
        return {
            "sender_id": master_id,
            "role": "MASTER",
            "payload": PostMessageRequest(type="ACTION", text=text),
        }

    victor_id = next((uid for uid, _ in ctx["players"] if uid in pc_by_user), ctx["players"][0][0] if ctx["players"] else "")
    user_id = next((uid for uid, label in ctx["players"] if uid != victor_id), victor_id)

    norman = pc_by_user.get(victor_id, ("", "Norman"))[1]
    userildo = pc_by_user.get(user_id, ("", "Userildo"))[1]

    return [
        master_narrator(
            "El alba tiñe de cobre las tejas del Yunque Quebrado. "
            f"{norman} y {userildo} cruzan la puerta sur con capas aún húmedas y provisiones "
            "para medio día. El camino al bosque norte está embarrado por la lluvia nocturna."
        ),
        player_msg(
            victor_id,
            f"«{norman} marca el ritmo con la punta de la bota en el barro.» "
            "«Mantened el paso. Si las desapariciones vienen del bosque, las huellas no esperarán al mediodía.»",
            msg_type="ACTION",
        ),
        player_msg(
            user_id,
            f"«{userildo} mira hacia la línea de pinos.» "
            "«Las luces verdes que vio el hijo de Arturo… ¿creéis que aún están allí de día?»",
        ),
        master_narrator(
            "El sendero se estrecha entre helechos y raíces. El canto de los pájaros cede "
            "a un silencio denso, como si el bosque contuviera la respiración."
        ),
        player_dice(user_id, "1d20+2", skill="Perception"),
        master_narrator(
            "Entre musgo y raíces torcidas, " + userildo + " distingue huellas recientes: "
            "dos pares de botas y un arrastre irregular, como si alguien hubiera sido llevado a la fuerza."
        ),
        player_msg(
            victor_id,
            f"«{norman} se arrodilla junto a la marca más profunda.» "
            "«Tela rasgada… lana teñida. No es equipo de cazador.»",
            msg_type="ACTION",
        ),
        player_dice(victor_id, "1d20+1", skill="Investigation"),
        master_narrator(
            "Más adentro, un fulgor verdusco parpadea entre los troncos. No es fuego fatuo: "
            "late con ritmo medido, casi ritual."
        ),
        player_msg(
            victor_id,
            f"«{norman} levanta el puño cerrado.» "
            "«Alto. Oímos pasos a la izquierda.»",
            msg_type="ACTION",
        ),
        master_narrator(
            f"Una figura encapuchada —{enemy_name}— emerge del musgo con una hoja corta. "
            "Sus ojos no parpadean. La emboscada estaba preparada."
        ),
        master_combat("/initiative"),
        player_msg(
            victor_id,
            f"«{norman} avanza con la espada en guardia alta.» "
            f"«@Norman ataca @Acechador»",
            msg_type="ACTION",
        ),
        master_combat(f"@Acechador ataca @Userildo"),
        player_msg(
            user_id,
            f"«{userildo} gira el escudo y desvía el golpe hacia un tronco.» "
            "«¡No os acerquéis más!»",
            msg_type="ACTION",
        ),
        player_msg(
            user_id,
            f"«{userildo} contraataca buscando el flanco descubierto.» "
            f"«@Userildo ataca @Acechador»",
            msg_type="ACTION",
        ),
        master_narrator(
            f"El {enemy_name.lower()} retrocede tambaleándose, la capucha caída. "
            "En su cinturón cuelga un medallón con el sello de un mercader desaparecido hace tres días."
        ),
        player_msg(
            victor_id,
            f"«{norman} inmoviliza al herido con la rodilla en el pecho.» "
            "«Hablad. ¿Quién enciende las luces verdes?»",
            msg_type="ACTION",
        ),
        master_narrator(
            "El prisionero escupe sangre y sonríe sin responder. "
            "Más allá, el fulgor verde se intensifica, como respondiendo a un llamado."
        ),
        player_msg(
            user_id,
            f"«{userildo} mira el medallón y palidece.» "
            "«Conozco este sello. Pertenecía a la caravana de Mirna. Si sigue vivo, está más adentro.»",
        ),
        master_narrator(
            "Un claro circular aparece entre los pinos: piedras erguidas cubiertas de musgo "
            "y un círculo de ceniza reciente. Las luces verdes giran lentamente sobre las rocas."
        ),
        player_msg(
            victor_id,
            f"«{norman} mantiene la espada baja pero lista.» "
            "«No entramos a ciegas. Userildo, cubrid la retaguardia.»",
            msg_type="ACTION",
        ),
        master_narrator(
            "Un susurro en idioma desconocido resuena desde el centro del claro. "
            "Las piedras vibran apenas. La escena queda suspendida: el bosque aún no ha revelado su secreto."
        ),
    ]


async def set_player_turn(
    db,
    scene: Scene,
    user_id: str,
    ctx: dict,
) -> None:
    pc_entity_id = next(
        (entity_id for entity_id, _, bound_user in ctx["pcs"] if bound_user == user_id),
        None,
    )
    if pc_entity_id:
        await update_scene_turn_management(
            db,
            scene,
            SceneTurnManagementUpdate(current_turn_entity_id=pc_entity_id),
        )
    else:
        await update_scene_turn_management(
            db,
            scene,
            SceneTurnManagementUpdate(current_turn_player_id=user_id),
        )


async def post_scene_messages(
    db,
    scene: Scene,
    messages: list[dict],
    ctx: dict,
) -> int:
    count = 0
    for spec in messages:
        await db.refresh(scene)
        if spec["role"] == "PLAYER":
            await set_player_turn(db, scene, spec["sender_id"], ctx)
            await db.refresh(scene)

        if spec.get("kind") == "dice":
            await roll_scene_dice(
                db,
                scene,
                spec["sender_id"],
                spec["payload"],
                sender_role=spec["role"],
            )
        else:
            await post_message(
                db,
                scene,
                spec["sender_id"],
                spec["payload"],
                sender_role=spec["role"],
            )
        count += 1
    return count


async def setup_scene_pbp(
    db,
    scene: Scene,
    ctx: dict,
    *,
    npc_names: list[str] | None = None,
) -> None:
    state = load_scene_state(scene)
    state.memory_settings.max_chat_buffer_size = 50
    save_scene_state(scene, state)
    await db.commit()
    await db.refresh(scene)

    if npc_names:
        npc_by_name = {name: eid for eid, name in ctx["npcs"]}
        npc_entries = [
            NpcPresenceEntry(entity_id=npc_by_name[name], is_hidden_from_players=False)
            for name in npc_names
            if name in npc_by_name
        ]
        if npc_entries:
            await update_scene_npc_presence(
                db,
                scene,
                ScenePresenceUpdate(add=npc_entries, remove=[]),
            )
            await db.refresh(scene)

    player_ids = [uid for uid, _ in ctx["players"]]
    if len(player_ids) >= 2:
        await update_scene_turn_management(
            db,
            scene,
            SceneTurnManagementUpdate(
                pbp_enabled=True,
                turn_order=player_ids,
                current_turn_player_id=player_ids[0],
            ),
        )
        await db.refresh(scene)


def print_scene_report(
    *,
    campaign_id: uuid.UUID,
    scene: Scene,
    message_count: int,
    summary: str | None = None,
) -> None:
    state = load_scene_state(scene)
    type_counts = Counter(msg.type for msg in state.chat_buffer)

    print(f"\n=== Scene result ===")
    print(f"  scene_id: {scene.id}")
    print(f"  scene_number: {scene.scene_number}")
    print(f"  display_name: {scene.display_name}")
    print(f"  status: {scene.status}")
    print(f"  messages_posted: {message_count}")
    print(f"  messages_in_buffer: {len(state.chat_buffer)}")
    print(f"  message_types: {dict(type_counts)}")
    print(f"  master_url: /campaigns/{campaign_id}/chat")

    if summary:
        print(f"\n=== AI Summary ===\n{summary}\n")


async def run_prologue(*, campaign_name: str = CAMPAIGN_NAME) -> int:
    deleted_scene_ids: list[str] = []
    scene_id: str | None = None
    message_count = 0
    summary: str | None = None

    async with SessionLocal() as db:
        try:
            campaign = await find_campaign(db, campaign_name)
            campaign_id = campaign.id
            ctx = await load_campaign_context(db, campaign_id)

            print(f"=== Campaign: {campaign.name} ({campaign_id}) ===")
            print(f"  game_system: {campaign.game_system}")
            print(f"  master: {ctx['master_id']}")
            print(f"  players: {ctx['players']}")
            print(f"  PCs: {ctx['pcs']}")
            print(f"  NPCs: {ctx['npcs']}")

            deleted_scene_ids = await delete_campaign_scenes(db, campaign_id)
            print(f"\nDeleted {len(deleted_scene_ids)} scene(s): {deleted_scene_ids}")

            master_id = uuid.UUID(ctx["master_id"])
            player_ids = [uid for uid, _ in ctx["players"]]

            scene_resp = await create_scene(
                db,
                campaign_id,
                SceneCreate(
                    campaign_id=str(campaign_id),
                    display_name="Prólogo",
                    scene_objective="Presentar Las Piedras Grises, Arturo y el gancho del bosque.",
                    turn_order=player_ids or [str(master_id)],
                ),
                creator_user_id=master_id,
            )
            scene_id = scene_resp.id
            scene = await db.scalar(select(Scene).where(Scene.id == uuid.UUID(scene_id)))
            if scene is None:
                raise RuntimeError("Scene not found after creation")

            await setup_scene_pbp(
                db,
                scene,
                ctx,
                npc_names=["Arturo", "Hijo de Arturo"],
            )

            messages = build_prologue_messages(ctx)
            message_count = await post_scene_messages(db, scene, messages, ctx)

            await db.refresh(scene)
            closed = await close_scene(db, scene)
            summary = closed.summary
            scene = await db.scalar(select(Scene).where(Scene.id == uuid.UUID(scene_id)))
            print_scene_report(
                campaign_id=campaign_id,
                scene=scene,
                message_count=message_count,
                summary=summary,
            )

            verify_scenes = (
                await db.scalars(
                    select(Scene)
                    .where(Scene.campaign_id == campaign_id)
                    .order_by(Scene.scene_number)
                )
            ).all()
            print("=== Scene log (hub) ===")
            for s in verify_scenes:
                st = load_scene_state(s)
                sm = st.metadata.closure_summary if s.status == "CLOSED" else None
                label = s.display_name or f"Escena {s.scene_number}"
                print(f"  #{s.scene_number} {label} [{s.status}]")
                if sm:
                    preview = sm[:120] + ("…" if len(sm) > 120 else "")
                    print(f"    summary: {preview}")

            memory_count = await db.scalar(
                select(CampaignMemory.id)
                .where(CampaignMemory.campaign_id == campaign_id)
                .limit(1)
            )
            print(f"\nRAG memory entries present: {'yes' if memory_count else 'no (OpenAI key missing?)'}")

        except Exception as exc:
            print(f"\nERROR: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    return 0


async def run_scene2(*, campaign_name: str = CAMPAIGN_NAME, keep_open: bool = True) -> int:
    async with SessionLocal() as db:
        try:
            campaign = await find_campaign(db, campaign_name)
            campaign_id = campaign.id
            ctx = await load_campaign_context(db, campaign_id)

            print(f"=== Campaign: {campaign.name} ({campaign_id}) ===")
            print(f"  game_system: {campaign.game_system}")
            print(f"  master: {ctx['master_id']}")
            print(f"  players: {ctx['players']}")
            print(f"  PCs: {ctx['pcs']}")
            print(f"  NPCs: {ctx['npcs']}")

            scenes = (
                await db.scalars(
                    select(Scene)
                    .where(Scene.campaign_id == campaign_id)
                    .order_by(Scene.scene_number)
                )
            ).all()
            scene1 = next((s for s in scenes if s.scene_number == 1), None)
            if scene1 is None:
                raise SystemExit("Scene 1 (Prólogo) not found — run prologue simulation first.")
            if scene1.status != "CLOSED":
                raise SystemExit(
                    f"Scene 1 must remain CLOSED (current: {scene1.status}). "
                    "Close it before creating scene 2."
                )
            print(f"\nPreserved scene 1: {scene1.display_name!r} [{scene1.status}]")

            existing_s2 = next((s for s in scenes if s.scene_number == 2), None)
            if existing_s2 is not None:
                removed = await delete_scene_by_number(db, campaign_id, 2)
                print(f"Removed previous scene 2: {removed}")

            enemy_id, enemy_name = await ensure_forest_enemy_npc(db, campaign, ctx)
            print(f"Forest enemy NPC: {enemy_name} ({enemy_id})")

            master_id = uuid.UUID(ctx["master_id"])
            player_ids = [uid for uid, _ in ctx["players"]]

            scene_resp = await create_scene(
                db,
                campaign_id,
                SceneCreate(
                    campaign_id=str(campaign_id),
                    display_name="El bosque al amanecer",
                    scene_objective="Explorar el bosque norte, emboscada y claro de piedras verdes.",
                    turn_order=player_ids or [str(master_id)],
                ),
                creator_user_id=master_id,
            )
            scene = await db.scalar(select(Scene).where(Scene.id == uuid.UUID(scene_resp.id)))
            if scene is None:
                raise RuntimeError("Scene not found after creation")

            await setup_scene_pbp(db, scene, ctx)

            messages = build_scene2_messages(ctx, enemy_name=enemy_name)

            ambush_index = next(
                i for i, spec in enumerate(messages)
                if spec.get("payload") and getattr(spec["payload"], "text", "").startswith("/initiative")
            )
            pre_ambush = messages[:ambush_index]
            post_ambush = messages[ambush_index:]

            message_count = await post_scene_messages(db, scene, pre_ambush, ctx)

            await update_scene_npc_presence(
                db,
                scene,
                ScenePresenceUpdate(
                    add=[NpcPresenceEntry(entity_id=enemy_id, is_hidden_from_players=False)],
                    remove=[],
                ),
            )
            await db.refresh(scene)

            message_count += await post_scene_messages(db, scene, post_ambush, ctx)

            await db.refresh(scene)
            if not keep_open:
                closed = await close_scene(db, scene)
                await db.refresh(scene)
                print_scene_report(
                    campaign_id=campaign_id,
                    scene=scene,
                    message_count=message_count,
                    summary=closed.summary,
                )
            else:
                print_scene_report(
                    campaign_id=campaign_id,
                    scene=scene,
                    message_count=message_count,
                )

            verify_scenes = (
                await db.scalars(
                    select(Scene)
                    .where(Scene.campaign_id == campaign_id)
                    .order_by(Scene.scene_number)
                )
            ).all()
            print("=== Scene log (hub) ===")
            for s in verify_scenes:
                st = load_scene_state(s)
                sm = st.metadata.closure_summary if s.status == "CLOSED" else None
                label = s.display_name or f"Escena {s.scene_number}"
                print(f"  #{s.scene_number} {label} [{s.status}]")
                if sm:
                    preview = sm[:120] + ("…" if len(sm) > 120 else "")
                    print(f"    summary: {preview}")

            memory_count = await db.scalar(
                select(CampaignMemory.id)
                .where(CampaignMemory.campaign_id == campaign_id)
                .limit(1)
            )
            print(f"\nRAG memory entries present: {'yes' if memory_count else 'no (OpenAI key missing?)'}")

            if scene.status != "ACTIVE":
                raise SystemExit(f"Expected ACTIVE scene, got {scene.status}")

        except Exception as exc:
            print(f"\nERROR: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate CampañaTest scenes (Prólogo or scene 2)."
    )
    parser.add_argument("--campaign", default=CAMPAIGN_NAME, help="Campaign name")
    parser.add_argument(
        "--scene2",
        action="store_true",
        help="Create scene 2 (El bosque al amanecer) after closed Prólogo.",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Leave the scene ACTIVE (default with --scene2; ignored for Prólogo).",
    )
    args = parser.parse_args()

    if args.scene2:
        raise SystemExit(asyncio.run(run_scene2(campaign_name=args.campaign, keep_open=True)))
    raise SystemExit(asyncio.run(run_prologue(campaign_name=args.campaign)))


if __name__ == "__main__":
    main()
