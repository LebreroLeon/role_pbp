import re
from dataclasses import dataclass
from enum import StrEnum


class CombatCommandKind(StrEnum):
    ATTACK = "attack"
    DAMAGE = "damage"
    INITIATIVE = "initiative"


@dataclass(frozen=True)
class ParsedAttackCommand:
    attacker_ref: str
    defender_ref: str
    weapon_name: str | None = None
    kind: CombatCommandKind = CombatCommandKind.ATTACK


@dataclass(frozen=True)
class ParsedDamageCommand:
    target_ref: str
    amount: int
    damage_type: str
    kind: CombatCommandKind = CombatCommandKind.DAMAGE


@dataclass(frozen=True)
class ParsedInitiativeCommand:
    kind: CombatCommandKind = CombatCommandKind.INITIATIVE


ParsedCombatCommand = ParsedAttackCommand | ParsedDamageCommand | ParsedInitiativeCommand

_MENTION_ATTACK_PATTERN = re.compile(
    r"^\s*@(\S+)\s+(?:ataca|attacks?)\s+@(\S+)\s*$",
    re.IGNORECASE,
)
_SLASH_ATTACK_PATTERN = re.compile(
    r"^\s*/attack\s+@(\S+)(?:\s+(?!to\b|->\b)(\S+))?\s+(?:to|->)\s+@(\S+)\s*$",
    re.IGNORECASE,
)
_DAMAGE_PATTERN = re.compile(
    r"^\s*/damage\s+@(\S+)\s+(\d+)\s+(\S+)\s*$",
    re.IGNORECASE,
)
_INITIATIVE_PATTERN = re.compile(
    r"^\s*/(?:initiative|combat\s+initiative)\s*$",
    re.IGNORECASE,
)


def normalize_mention(ref: str) -> str:
    return ref.lstrip("@").strip()


def try_parse_combat_command(text: str) -> ParsedCombatCommand | None:
    if not text or not text.strip():
        return None

    initiative_match = _INITIATIVE_PATTERN.match(text)
    if initiative_match:
        return ParsedInitiativeCommand()

    damage_match = _DAMAGE_PATTERN.match(text)
    if damage_match:
        return ParsedDamageCommand(
            target_ref=normalize_mention(damage_match.group(1)),
            amount=int(damage_match.group(2)),
            damage_type=damage_match.group(3).lower(),
        )

    slash_attack_match = _SLASH_ATTACK_PATTERN.match(text)
    if slash_attack_match:
        weapon = slash_attack_match.group(2)
        return ParsedAttackCommand(
            attacker_ref=normalize_mention(slash_attack_match.group(1)),
            defender_ref=normalize_mention(slash_attack_match.group(3)),
            weapon_name=weapon.lower() if weapon else None,
        )

    mention_attack_match = _MENTION_ATTACK_PATTERN.match(text)
    if mention_attack_match:
        return ParsedAttackCommand(
            attacker_ref=normalize_mention(mention_attack_match.group(1)),
            defender_ref=normalize_mention(mention_attack_match.group(2)),
        )

    return None
