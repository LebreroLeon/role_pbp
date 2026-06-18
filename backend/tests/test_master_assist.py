import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.campaign import Campaign
from app.schemas.master import MasterAssistRequest
from app.services.master import (
    apply_language_instruction,
    build_manual_search_query,
    build_master_assist_response,
    build_sandwich_prompt,
    is_rules_query,
    query_language_is_spanish,
)


class TestRulesQueryDetection:
    def test_detects_spanish_subclass_question(self):
        assert is_rules_query("que competencias tiene el luchador arquero arcano?")

    def test_detects_english_features_question(self):
        assert is_rules_query("Arcane Archer features")

    def test_ignores_narrative_scene_question(self):
        assert not is_rules_query("Que complicacion encaja con la escena actual?")

    def test_detects_spanish_armor_price_question(self):
        assert is_rules_query("cuanto vale en el mercado una armadura pesada completa?")

    def test_detects_equipment_and_market_terms(self):
        assert is_rules_query("precio del equipamiento en la tienda")
        assert is_rules_query("market price for heavy armor")


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
