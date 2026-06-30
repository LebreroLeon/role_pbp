import { damageTypeLabel } from "./damageTypes";
import { DND5E_SPELL_LEVEL_LABELS, type Dnd5eSpellEntry } from "./schema";

function line(label: string, value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  return `${label}: ${trimmed}`;
}

function joinParts(parts: Array<string | null>, separator: string): string | null {
  const filtered = parts.filter((part): part is string => Boolean(part));
  return filtered.length > 0 ? filtered.join(separator) : null;
}

export function formatSpellChatMessage(spell: Dnd5eSpellEntry): string {
  const name = spell.name.trim() || "Conjuro sin nombre";
  const levelLabel = DND5E_SPELL_LEVEL_LABELS[spell.level] ?? `Nivel ${spell.level}`;
  const headerParts = [levelLabel];
  if (spell.school.trim()) headerParts.push(spell.school.trim());
  const header = `**${name}** (${headerParts.join(" · ")})`;

  const metaLine = joinParts(
    [
      spell.casting_time.trim() ? spell.casting_time.trim() : null,
      line("Alcance", spell.range),
      spell.area.trim() ? `Área: ${spell.area.trim()}` : null,
      spell.components.trim() ? spell.components.trim() : null,
    ],
    " · ",
  );

  const durationParts: Array<string | null> = [];
  if (spell.concentration) durationParts.push("Concentración");
  if (spell.duration.trim()) durationParts.push(spell.duration.trim());
  const durationLine =
    durationParts.length > 0 ? durationParts.join(" · ") : spell.concentration ? "Concentración" : null;

  const resolutionParts: Array<string | null> = [];
  if (spell.resolution.trim() && spell.resolution !== "Ninguna") {
    resolutionParts.push(spell.resolution.trim());
  }
  if (spell.damage_type.trim()) {
    const damageLabel = damageTypeLabel(spell.damage_type) || spell.damage_type.trim();
    resolutionParts.push(`Daño: ${damageLabel}`);
  }
  const resolutionLine =
    resolutionParts.length > 0 ? resolutionParts.join(" · ") : null;

  const flags: string[] = [];
  if (spell.level > 0 && spell.prepared) flags.push("Preparado");
  if (spell.ritual) flags.push("Ritual");
  const flagsLine = flags.length > 0 ? flags.join(" · ") : null;

  const bodyLines = [
    header,
    metaLine,
    durationLine,
    resolutionLine,
    flagsLine,
    spell.notes.trim() || null,
    spell.higher_levels.trim() ? `A niveles superiores: ${spell.higher_levels.trim()}` : null,
    spell.end_conditions.trim() ? `Finaliza si: ${spell.end_conditions.trim()}` : null,
  ].filter((part): part is string => Boolean(part));

  return bodyLines.join("\n");
}
