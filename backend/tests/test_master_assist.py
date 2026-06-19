import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import Campaign
from app.schemas.master import MasterAssistRequest
from app.services.master import (
    apply_language_instruction,
    build_entity_flags_snapshot,
    build_manual_search_query,
    build_master_assist_response,
    build_shadow_master_system_prompt,
    build_sandwich_prompt,
    is_narrative_query,
    is_rules_query,
    query_language_is_spanish,
    resolve_query_kind,
    sanitize_narrative_suggestion,
)


class TestExplicitAssistMode:
    def test_explicit_narrative_mode_uses_narrative_prompt(self):
        prompt, query_kind = build_shadow_master_system_prompt(
            "cuanto vale la armadura?",
            mode="narrative",
        )
        assert query_kind == "narrative"
        assert "NARRATIVE MODE" in prompt
        assert "copy-paste ready" in prompt

    def test_explicit_rules_mode_uses_rules_prompt(self):
        prompt, query_kind = build_shadow_master_system_prompt(
            "Que complicacion encaja con la escena actual?",
            mode="rules",
        )
        assert query_kind == "rules"
        assert "rules consultant" in prompt
        assert "Do NOT answer with scene suggestions" in prompt

    def test_explicit_campaign_mode_uses_campaign_prompt(self):
        prompt, query_kind = build_shadow_master_system_prompt(
            "competencias luchador arquero arcano",
            mode="campaign",
        )
        assert query_kind == "campaign"
        assert "campaign memory consultant" in prompt
        assert "Do NOT answer with rulebook mechanics" in prompt
        assert "rules consultant" not in prompt

    def test_campaign_sandwich_prioritizes_state_and_campaign_rag(self):
        prompt = build_sandwich_prompt(
            scene_flags={"combat_active": False},
            scene_context={"objective": "Find the relic"},
            entities_snapshot=[{"entity_id": "npc-1", "entity_type": "NPC"}],
            rag_chunks=["The party met the baron last session."],
            manual_rag_chunks=["Plate armor costs 1500 gp."],
            chat_buffer=[{"text": "We enter the hall."}],
            query="Que sabe el baron de la reliquia?",
            campaign_query=True,
        )
        state_index = prompt.index("ABSOLUTE STATE")
        rag_index = prompt.index("HISTORICAL CONTEXT")
        manual_index = prompt.index("SYSTEM RULEBOOKS")
        assert state_index < rag_index < manual_index
        assert "PRIMARY FOR THIS QUERY" in prompt
        assert "baron" in prompt


class TestRulesQueryDetection:
    def test_detects_spanish_subclass_question(self):
        assert is_rules_query("que competencias tiene el luchador arquero arcano?")

    def test_detects_english_features_question(self):
        assert is_rules_query("Arcane Archer features")

    def test_ignores_narrative_scene_question(self):
        assert not is_rules_query("Que complicacion encaja con la escena actual?")

    def test_detects_narrative_opening_question(self):
        assert is_narrative_query("Como podria empezar la narracion en la tercera escena?")

    def test_ignores_rules_price_question_for_narrative(self):
        assert not is_narrative_query("cuanto vale en el mercado una armadura pesada completa?")

    def test_detects_spanish_armor_price_question(self):
        assert is_rules_query("cuanto vale en el mercado una armadura pesada completa?")

    def test_detects_equipment_and_market_terms(self):
        assert is_rules_query("precio del equipamiento en la tienda")
        assert is_rules_query("market price for heavy armor")

    def test_scene_complication_stays_creative_not_narrative(self):
        query = "Que complicacion encaja con la escena actual?"
        assert not is_narrative_query(query)
        assert resolve_query_kind(query) == "creative"

    def test_continue_story_is_narrative_not_creative(self):
        query = "continuar la historia"
        assert is_narrative_query(query)
        assert resolve_query_kind(query) == "narrative"

    def test_detects_continue_story_in_current_scene_as_narrative(self):
        query = (
            "como podría continuar la historia en la escena actual? "
            "mandalo como si fueras el master."
        )
        assert is_narrative_query(query)
        assert resolve_query_kind(query) == "narrative"

    def test_narrator_prose_request_forces_narrative(self):
        assert is_narrative_query("escribe como el narrador la llegada al puerto")
        assert resolve_query_kind("mandalo como si fueras el master") == "narrative"


class TestSpanishQueryDetection:
    def test_detects_spanish_price_question(self):
        assert query_language_is_spanish("cuanto vale en el mercado una armadura pesada completa?")

    def test_ignores_english_features_question(self):
        assert not query_language_is_spanish("Arcane Archer features")

    def test_apply_language_instruction_for_spanish(self):
        prompt = apply_language_instruction("Base prompt.", "cuanto vale la armadura?")
        assert "LANGUAGE (mandatory)" in prompt
        assert "entirely in Spanish" in prompt


class TestManualSearchQuery:
    def test_expands_spanish_terms_for_manual_rag(self):
        query = "competencias luchador arquero arcano"
        expanded = build_manual_search_query(query)
        assert "Arcane Archer" in expanded
        assert "Fighter" in expanded
        assert "proficiencies" in expanded
        assert "official rules manual" in expanded

    def test_expands_heavy_armor_price_query(self):
        query = "cuanto vale en el mercado una armadura pesada completa?"
        expanded = build_manual_search_query(query)
        assert "heavy armor" in expanded.lower()
        assert "price" in expanded.lower()
        assert "official rules manual" in expanded


class TestNarrativeSuggestions:
    def test_sanitize_strips_master_meta_prefix(self):
        raw = "El maestro podría comenzar describiendo el silencio del claro."
        cleaned = sanitize_narrative_suggestion(raw)
        assert "maestro" not in cleaned.lower()
        assert "silencio" in cleaned.lower()

    def test_narrative_prompt_includes_copy_paste_rules(self):
        prompt, query_kind = build_shadow_master_system_prompt(
            "Como podria empezar la narracion en la tercera escena?"
        )
        assert query_kind == "narrative"
        assert "NARRATIVE MODE" in prompt
        assert "copy-paste ready" in prompt
        assert "El maestro podría" in prompt

    def test_narrative_prompt_includes_campaign_grounding_rules(self):
        prompt, query_kind = build_shadow_master_system_prompt(
            "Como podria empezar la narracion en la tercera escena?"
        )
        assert query_kind == "narrative"
        assert "Campaign grounding" in prompt
        assert "ABSOLUTE STATE" in prompt
        assert "Do NOT invent plot" in prompt
        assert "which lore/context elements each suggestion draws from" in prompt

    def test_narrative_sandwich_prioritizes_state_and_campaign_rag(self):
        prompt = build_sandwich_prompt(
            scene_flags={"combat_active": False},
            scene_context={"objective": "Reach the forest clearing"},
            entities_snapshot=[{"entity_id": "npc-arturo", "entity_type": "NPC", "document": {"name": "Arturo"}}],
            rag_chunks=["Prólogo: the party entered the bosque after Arturo's warning."],
            manual_rag_chunks=["Plate armor costs 1500 gp."],
            chat_buffer=[{"text": "Arturo points toward the dark trees."}],
            query="Como podria empezar la narracion en la tercera escena?",
            narrative_query=True,
        )
        state_index = prompt.index("ABSOLUTE STATE")
        rag_index = prompt.index("HISTORICAL CONTEXT")
        chat_index = prompt.index("RECENT CHAT")
        manual_index = prompt.index("SYSTEM RULEBOOKS")
        assert state_index < rag_index < chat_index < manual_index
        assert "PRIMARY FOR THIS QUERY" in prompt
        assert "Prólogo" in prompt
        assert "Arturo" in prompt
        assert "narrative / scene description" in prompt
        assert "atmosphere/setting tone only" in prompt

    def test_continue_story_prompt_uses_narrative_mode(self):
        query = (
            "como podría continuar la historia en la escena actual? "
            "mandalo como si fueras el master."
        )
        prompt, query_kind = build_shadow_master_system_prompt(query)
        assert query_kind == "narrative"
        assert "NARRATIVE MODE" in prompt


class TestSandwichPrompt:
    def test_rules_query_prioritizes_manual_section(self):
        prompt = build_sandwich_prompt(
            scene_flags={},
            scene_context={},
            entities_snapshot=[],
            rag_chunks=["Party entered the tavern."],
            manual_rag_chunks=["Arcane Archer: you learn Arcane Shot at 3rd level."],
            chat_buffer=[],
            query="competencias luchador arquero arcano",
            rules_query=True,
        )
        manual_index = prompt.index("SYSTEM RULEBOOKS")
        state_index = prompt.index("ABSOLUTE STATE")
        assert manual_index < state_index
        assert "PRIMARY FOR THIS QUERY" in prompt
        assert "Arcane Shot" in prompt


@pytest.mark.asyncio
async def test_build_master_assist_rules_query_uses_manual_rag_and_rules_prompt():
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    campaign = Campaign(id=campaign_id, name="Test", game_system="dnd5e")
    scene = MagicMock()
    scene.campaign_id = campaign_id
    scene.id = scene_id

    payload = MasterAssistRequest(
        campaign_id=str(campaign_id),
        scene_id=str(scene_id),
        query="competencias luchador arquero arcano",
    )

    manual_chunk = (
        "Arcane Archer (Fighter subclass): At 3rd level you learn Arcane Shot. "
        "You gain proficiency in one skill from the fighter list."
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=campaign)
    db.scalars = AsyncMock(return_value=[])

    mock_state = MagicMock()
    mock_state.memory_settings.rag_top_k_matches = 3
    mock_state.memory_settings.max_chat_buffer_size = 20
    mock_state.state_flags.model_dump.return_value = {}
    mock_state.context.model_dump.return_value = {}
    mock_state.chat_buffer = []

    with (
        patch("app.services.scenes.load_scene_state", return_value=mock_state),
        patch(
            "app.services.master.rag_service.search",
            new=AsyncMock(return_value=[]),
        ) as mock_campaign_search,
        patch(
            "app.services.master.rag_service.search_system_manuals",
            new=AsyncMock(return_value=[manual_chunk]),
        ) as mock_manual_search,
        patch(
            "app.services.master.chat_completion",
            new=AsyncMock(
                return_value='{"context_summary": "Arcane Archer proficiencies from manual.", '
                '"suggestions": ["Arcane Shot at 3rd level", "One extra skill proficiency"]}'
            ),
        ) as mock_chat,
    ):
        response = await build_master_assist_response(db, payload, scene=scene)

    mock_manual_search.assert_awaited_once()
    manual_call = mock_manual_search.await_args.kwargs
    assert manual_call["game_system"] == "dnd5e"
    assert manual_call["top_k"] == 5
    assert "Arcane Archer" in manual_call["query"]

    mock_campaign_search.assert_awaited_once()
    mock_chat.assert_awaited_once()
    system_message = mock_chat.await_args.args[0][0]["content"]
    assert "rules consultant" in system_message
    assert "Do NOT answer with scene suggestions" in system_message

    assert "Arcane Archer" in response.context_summary or "manual" in response.context_summary.lower()
    assert response.suggestions
    assert "Arcane Shot" in response.suggestions[0] or "skill" in response.suggestions[1].lower()


@pytest.mark.asyncio
async def test_build_master_assist_rules_query_fallback_without_llm():
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    campaign = Campaign(id=campaign_id, name="Test", game_system="dnd5e")
    scene = MagicMock()
    scene.campaign_id = campaign_id

    payload = MasterAssistRequest(
        campaign_id=str(campaign_id),
        scene_id=str(scene_id),
        query="Arcane Archer features",
    )

    manual_chunk = "Arcane Archer: Arcane Shot, Magic Arrow, Curving Shot."

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=campaign)
    db.scalars = AsyncMock(return_value=[])

    mock_state = MagicMock()
    mock_state.memory_settings.rag_top_k_matches = 3
    mock_state.memory_settings.max_chat_buffer_size = 20
    mock_state.state_flags.model_dump.return_value = {}
    mock_state.context.model_dump.return_value = {}
    mock_state.chat_buffer = []

    from app.services.llm import LLMNotConfiguredError

    with (
        patch("app.services.scenes.load_scene_state", return_value=mock_state),
        patch("app.services.master.rag_service.search", new=AsyncMock(return_value=[])),
        patch(
            "app.services.master.rag_service.search_system_manuals",
            new=AsyncMock(return_value=[manual_chunk]),
        ),
        patch(
            "app.services.master.chat_completion",
            new=AsyncMock(side_effect=LLMNotConfiguredError("no key")),
        ),
    ):
        response = await build_master_assist_response(db, payload, scene=scene)

    assert manual_chunk in response.context_summary
    assert manual_chunk in response.suggestions
    assert response.note == "no key"


@pytest.mark.asyncio
async def test_build_master_assist_heavy_armor_price_uses_rules_prompt_in_spanish():
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    campaign = Campaign(id=campaign_id, name="Test", game_system="dnd5e")
    scene = MagicMock()
    scene.campaign_id = campaign_id
    scene.id = scene_id

    query = "cuanto vale en el mercado una armadura pesada completa?"
    payload = MasterAssistRequest(
        campaign_id=str(campaign_id),
        scene_id=str(scene_id),
        query=query,
    )

    manual_chunk = (
        "Plate armor (heavy armor): Cost 1,500 gp; AC 18; Stealth disadvantage; "
        "Strength 15 required. Plate is the heaviest common heavy armor."
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=campaign)
    db.scalars = AsyncMock(return_value=[])

    mock_state = MagicMock()
    mock_state.memory_settings.rag_top_k_matches = 3
    mock_state.memory_settings.max_chat_buffer_size = 20
    mock_state.state_flags.model_dump.return_value = {}
    mock_state.context.model_dump.return_value = {}
    mock_state.chat_buffer = []

    with (
        patch("app.services.scenes.load_scene_state", return_value=mock_state),
        patch("app.services.master.rag_service.search", new=AsyncMock(return_value=[])),
        patch(
            "app.services.master.rag_service.search_system_manuals",
            new=AsyncMock(return_value=[manual_chunk]),
        ) as mock_manual_search,
        patch(
            "app.services.master.chat_completion",
            new=AsyncMock(
                return_value='{"context_summary": "La armadura de placas cuesta 1.500 po.", '
                '"suggestions": ["CA 18; requiere Fuerza 15", "Desventaja en Sigilo"]}'
            ),
        ) as mock_chat,
    ):
        response = await build_master_assist_response(db, payload, scene=scene)

    mock_manual_search.assert_awaited_once()
    manual_call = mock_manual_search.await_args.kwargs
    assert "heavy armor" in manual_call["query"].lower()

    mock_chat.assert_awaited_once()
    system_message = mock_chat.await_args.args[0][0]["content"]
    assert "rules consultant" in system_message
    assert "merchant introductions" in system_message
    assert "LANGUAGE (mandatory)" in system_message
    assert "Spanish" in system_message

    assert "1.500" in response.context_summary or "1500" in response.context_summary
    assert response.suggestions
    assert not any("merchant" in s.lower() or "introduce" in s.lower() for s in response.suggestions)


@pytest.mark.asyncio
async def test_build_master_assist_narrative_query_uses_narrative_prompt_and_sanitizes():
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    campaign = Campaign(id=campaign_id, name="Test", game_system="dnd5e")
    scene = MagicMock()
    scene.campaign_id = campaign_id
    scene.id = scene_id

    query = "Como podria empezar la narracion en la tercera escena?"
    payload = MasterAssistRequest(
        campaign_id=str(campaign_id),
        scene_id=str(scene_id),
        query=query,
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=campaign)
    db.scalars = AsyncMock(return_value=[])

    mock_state = MagicMock()
    mock_state.memory_settings.rag_top_k_matches = 3
    mock_state.memory_settings.max_chat_buffer_size = 20
    mock_state.state_flags.model_dump.return_value = {}
    mock_state.context.model_dump.return_value = {}
    mock_state.chat_buffer = []

    meta_suggestion = (
        "El maestro podría comenzar describiendo el silencio del claro como un sudario húmedo."
    )
    good_suggestion = (
        "El silencio cae sobre el claro como un sudario húmedo. "
        "Desde el centro, un susurro en lengua desconocida raspa la garganta del bosque."
    )
    llm_payload = {
        "context_summary": "La tercera escena puede abrir con tensión ambiental.",
        "suggestions": [meta_suggestion, good_suggestion],
    }

    with (
        patch("app.services.scenes.load_scene_state", return_value=mock_state),
        patch("app.services.master.rag_service.search", new=AsyncMock(return_value=["Past battle in the forest."])) as mock_campaign_search,
        patch("app.services.master.rag_service.search_system_manuals", new=AsyncMock(return_value=["Manual chunk should not be fetched."])) as mock_manual_search,
        patch(
            "app.services.master.chat_completion",
            new=AsyncMock(return_value=json.dumps(llm_payload, ensure_ascii=False)),
        ) as mock_chat,
    ):
        response = await build_master_assist_response(db, payload, scene=scene)

    mock_campaign_search.assert_awaited_once()
    mock_manual_search.assert_not_awaited()

    mock_chat.assert_awaited_once()
    system_message = mock_chat.await_args.args[0][0]["content"]
    assert "NARRATIVE MODE" in system_message
    assert "copy-paste ready" in system_message
    assert "Campaign grounding" in system_message
    assert "Do NOT invent plot" in system_message

    user_message = mock_chat.await_args.args[0][1]["content"]
    assert "PRIMARY FOR THIS QUERY" in user_message
    assert user_message.index("ABSOLUTE STATE") < user_message.index("HISTORICAL CONTEXT")
    assert user_message.index("HISTORICAL CONTEXT") < user_message.index("SYSTEM RULEBOOKS")
    assert "forest" in user_message.lower()

    assert response.query_kind == "narrative"
    assert response.suggestions
    assert "maestro" not in response.suggestions[0].lower()
    assert "silencio" in response.suggestions[0].lower()
    assert "susurro" in response.suggestions[1].lower()


@pytest.mark.asyncio
async def test_build_master_assist_continue_story_query_uses_narrative_prompt():
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    campaign = Campaign(id=campaign_id, name="Test", game_system="dnd5e")
    scene = MagicMock()
    scene.campaign_id = campaign_id
    scene.id = scene_id

    query = (
        "como podría continuar la historia en la escena actual? "
        "mandalo como si fueras el master."
    )
    payload = MasterAssistRequest(
        campaign_id=str(campaign_id),
        scene_id=str(scene_id),
        query=query,
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=campaign)
    db.scalars = AsyncMock(return_value=[])

    mock_state = MagicMock()
    mock_state.memory_settings.rag_top_k_matches = 3
    mock_state.memory_settings.max_chat_buffer_size = 20
    mock_state.state_flags.model_dump.return_value = {}
    mock_state.context.model_dump.return_value = {}
    mock_state.chat_buffer = []

    llm_payload = {
        "context_summary": "La escena puede avanzar con tensión creciente.",
        "suggestions": [
            "Las antorchas parpadean mientras el grupo avanza por el pasillo.",
            "Un crujido lejano interrumpe el silencio y todos se detienen.",
        ],
    }

    with (
        patch("app.services.scenes.load_scene_state", return_value=mock_state),
        patch("app.services.master.rag_service.search", new=AsyncMock(return_value=["Earlier fight in the hall."])),
        patch("app.services.master.rag_service.search_system_manuals", new=AsyncMock(return_value=[])),
        patch(
            "app.services.master.chat_completion",
            new=AsyncMock(return_value=json.dumps(llm_payload, ensure_ascii=False)),
        ) as mock_chat,
    ):
        response = await build_master_assist_response(db, payload, scene=scene)

    mock_chat.assert_awaited_once()
    system_message = mock_chat.await_args.args[0][0]["content"]
    assert "NARRATIVE MODE" in system_message

    assert response.query_kind == "narrative"
    assert len(response.suggestions) == 2


@pytest.mark.asyncio
async def test_build_master_assist_campaign_mode_uses_campaign_prompt_and_skips_manual_rag():
    campaign_id = uuid.uuid4()
    scene_id = uuid.uuid4()
    campaign = Campaign(id=campaign_id, name="Test", game_system="dnd5e")
    scene = MagicMock()
    scene.campaign_id = campaign_id
    scene.id = scene_id

    query = "Que complicacion encaja con la escena actual?"
    payload = MasterAssistRequest(
        campaign_id=str(campaign_id),
        scene_id=str(scene_id),
        query=query,
        mode="campaign",
    )

    db = AsyncMock()
    db.scalar = AsyncMock(return_value=campaign)
    db.scalars = AsyncMock(return_value=[])

    mock_state = MagicMock()
    mock_state.memory_settings.rag_top_k_matches = 3
    mock_state.memory_settings.max_chat_buffer_size = 20
    mock_state.state_flags.model_dump.return_value = {}
    mock_state.context.model_dump.return_value = {}
    mock_state.chat_buffer = []

    with (
        patch("app.services.scenes.load_scene_state", return_value=mock_state),
        patch(
            "app.services.master.rag_service.search",
            new=AsyncMock(return_value=["Earlier ambush in the forest."]),
        ) as mock_campaign_search,
        patch(
            "app.services.master.rag_service.search_system_manuals",
            new=AsyncMock(return_value=["Manual chunk should not be fetched."]),
        ) as mock_manual_search,
        patch(
            "app.services.master.chat_completion",
            new=AsyncMock(
                return_value='{"context_summary": "La escena puede complicarse con el eco del emboscada previa.", '
                '"suggestions": ["El grupo reconoce el claro del ataque anterior.", '
                '"Un NPC herido entonces podría reaparecer."]}'
            ),
        ) as mock_chat,
    ):
        response = await build_master_assist_response(db, payload, scene=scene)

    mock_campaign_search.assert_awaited_once()
    mock_manual_search.assert_not_awaited()

    mock_chat.assert_awaited_once()
    system_message = mock_chat.await_args.args[0][0]["content"]
    assert "campaign memory consultant" in system_message
    assert "NARRATIVE MODE" not in system_message

    user_message = mock_chat.await_args.args[0][1]["content"]
    assert "PRIMARY FOR THIS QUERY" in user_message
    assert "forest" in user_message.lower()

    assert response.query_kind == "campaign"
    assert response.suggestions


class TestEntityFlagsSnapshot:
    def _entity(self, entity_type: str, document: dict, entity_id: str = "e1"):
        entity = MagicMock()
        entity.id = entity_id
        entity.entity_type = entity_type
        entity.document = document
        return entity

    def test_snapshot_includes_world_lore_entity_types(self):
        entities = [
            self._entity(
                "LOCATION",
                {
                    "identity": {"name": "Puerto Gris"},
                    "narrative_profile": {"public_description": "Un muelle lluvioso"},
                    "state_flags": {"is_accessible_to_party": True},
                },
                "loc-1",
            ),
            self._entity(
                "FACTION",
                {
                    "identity": {"name": "Gremio de ladrones"},
                    "narrative_profile": {"public_description": "Controlan el mercado negro"},
                    "state_flags": {"is_active": True},
                },
                "fac-1",
            ),
            self._entity(
                "RELATIONSHIP",
                {
                    "connection": {"source_id": "npc-1", "target_id": "fac-1"},
                    "narrative_bond": {"bond_type": "rivalidad", "public_status": "tensa"},
                    "state_flags": {"is_active": True},
                },
                "rel-1",
            ),
        ]

        snapshot = build_entity_flags_snapshot(entities, include_secrets=True)
        types = {item["entity_type"] for item in snapshot}

        assert types == {"LOCATION", "FACTION", "RELATIONSHIP"}
        assert snapshot[0]["document"]["identity"]["name"] == "Puerto Gris"
        assert snapshot[2]["document"]["narrative_bond"]["bond_type"] == "rivalidad"

    def test_focus_entity_id_filters_snapshot(self):
        entities = [
            self._entity("NPC", {"identity": {"name": "Arturo"}}, "npc-a"),
            self._entity("NPC", {"identity": {"name": "Bruna"}}, "npc-b"),
        ]

        snapshot = build_entity_flags_snapshot(entities, include_secrets=True, focus_entity_id="npc-b")

        assert len(snapshot) == 1
        assert snapshot[0]["entity_id"] == "npc-b"
