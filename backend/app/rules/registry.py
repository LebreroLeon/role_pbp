from app.rules.base import GameSystemPlugin
from app.rules.generic_fallback import GenericFallbackPlugin

_REGISTRY: dict[str, GameSystemPlugin] = {}
_FALLBACK = GenericFallbackPlugin()


def register_plugin(plugin: GameSystemPlugin) -> None:
    _REGISTRY[plugin.system_id] = plugin


def get_plugin(game_system: str | None) -> GameSystemPlugin:
    if not game_system:
        return _FALLBACK
    return _REGISTRY.get(game_system, _FALLBACK)


def list_registered_systems() -> list[str]:
    return sorted(_REGISTRY.keys())


def _bootstrap() -> None:
    from app.rules.dnd5e.plugin import Dnd5ePlugin
    from app.rules.cyberpunk_red.plugin import CyberpunkRedPlugin
    from app.rules.vtm_v5.plugin import VtmV5Plugin

    register_plugin(Dnd5ePlugin())
    register_plugin(CyberpunkRedPlugin())
    register_plugin(VtmV5Plugin())


_bootstrap()
