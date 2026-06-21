import { useMemo, useState } from "react";
import { Dices, Scroll } from "lucide-react";

import type { SheetRollRequest } from "../../../api/types";
import { Button, Tooltip } from "../../../components/ui";
import { extractSheetFromEntity } from "../../character-sheet/pcDocument";
import {
  abilityModifier,
  DND5E_ABILITIES,
  DND5E_ABILITY_LABELS,
  parseDnd5eSheet,
  type Dnd5eSheet,
} from "../../character-sheet/systems/dnd5e/schema";
import { InspirationSpendToggle } from "../../character-sheet/systems/dnd5e/InspirationBox";
import { useRollFromSheetMutation, useUpsertMySheetMutation } from "../../../hooks/mutations/useMySheetMutations";
import { useMySheetQuery } from "../../../hooks/queries/useMySheetQueries";
import { mergeAdvantageIntoContext, type AdvantageMode } from "../../systems/registry";
import { dnd5eSkillModifier } from "../../systems/dnd5e/rolls";
import { AdvantageToggle } from "../../systems/dnd5e/AdvantageToggle";
import { documentToCharacterSheetUpsert, mergeSheetIntoDocument } from "../../character-sheet/pcDocument";

type ChatMiniSheetProps = {
  campaignId: string;
  disabled?: boolean;
  onSceneRefresh?: () => void;
};

export function ChatMiniSheet({ campaignId, disabled, onSceneRefresh }: ChatMiniSheetProps) {
  const [expanded, setExpanded] = useState(false);
  const [advantageMode, setAdvantageMode] = useState<AdvantageMode>("normal");
  const [spendInspiration, setSpendInspiration] = useState(false);
  const { data: myPc } = useMySheetQuery(campaignId);
  const rollMutation = useRollFromSheetMutation(campaignId);
  const upsertMutation = useUpsertMySheetMutation(campaignId);

  const parsed = useMemo(() => {
    if (!myPc) return null;
    const extracted = extractSheetFromEntity(myPc.document);
    if (!extracted || extracted.systemId !== "dnd5e") return null;
    return {
      name: (myPc.document.identity as { name?: string } | undefined)?.name ?? "Personaje",
      sheet: parseDnd5eSheet(extracted.sheet),
    };
  }, [myPc]);

  if (!parsed) return null;

  const { name, sheet } = parsed;
  const hasInspiration = sheet.roleplay.inspiration;
  const proficientSkills = sheet.proficiency.skills.filter((skill) => skill.proficient).slice(0, 8);
  const isRolling = rollMutation.isPending;

  async function persistInspiration(nextSheet: Dnd5eSheet) {
    if (!myPc) return;
    const document = mergeSheetIntoDocument(myPc.document, "dnd5e", nextSheet as Record<string, unknown>);
    await upsertMutation.mutateAsync(documentToCharacterSheetUpsert(document));
  }

  async function roll(payload: SheetRollRequest) {
    const mode = spendInspiration ? "advantage" : advantageMode;
    const context = mergeAdvantageIntoContext(payload.context, mode);
    await rollMutation.mutateAsync({ ...payload, context });
    if (spendInspiration) {
      const nextSheet = { ...sheet, roleplay: { ...sheet.roleplay, inspiration: false } };
      await persistInspiration(nextSheet);
      setSpendInspiration(false);
    }
    onSceneRefresh?.();
  }

  function toggleSpendInspiration(active: boolean) {
    setSpendInspiration(active);
    if (active) {
      setAdvantageMode("advantage");
    }
  }

  return (
    <section className="chat-mini-sheet">
      <button
        type="button"
        className="chat-mini-sheet__toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((open) => !open)}
      >
        <Scroll size={16} aria-hidden />
        <span className="chat-mini-sheet__toggle-label">
          {name} — CA {sheet.defense.ac}, PV {sheet.defense.hp.current}/{sheet.defense.hp.max}
          {hasInspiration ? (
            <Tooltip content="Inspiración disponible">
              <span className="chat-mini-sheet__inspiration-badge" aria-label="Inspiración disponible">
                ✦
              </span>
            </Tooltip>
          ) : null}
        </span>
        <span className="chat-mini-sheet__chevron" aria-hidden>
          {expanded ? "▾" : "▸"}
        </span>
      </button>

      {expanded && (
        <div className="chat-mini-sheet__body">
          <div className="chat-mini-sheet__toolbar">
            <AdvantageToggle
              value={advantageMode}
              onChange={setAdvantageMode}
              disabled={disabled || isRolling}
              compact
            />
            {hasInspiration && (
              <InspirationSpendToggle
                active={spendInspiration}
                disabled={disabled || isRolling}
                onToggle={toggleSpendInspiration}
              />
            )}
          </div>

          <div className="chat-mini-sheet__section">
            <h4>Atributos</h4>
            <div className="chat-mini-sheet__grid">
              {DND5E_ABILITIES.map((ability) => {
                const mod = abilityModifier(sheet.abilities[ability]);
                return (
                  <Tooltip key={ability} content={`Tirar ${DND5E_ABILITY_LABELS[ability]}`}>
                    <button
                      type="button"
                      className="chat-mini-sheet__roll-chip"
                      disabled={disabled || isRolling}
                      aria-label={`Tirar ${DND5E_ABILITY_LABELS[ability]}`}
                      onClick={() =>
                        void roll({ roll_type: "ability_check", context: { ability } })
                      }
                    >
                      <span className="chat-mini-sheet__chip-label">{DND5E_ABILITY_LABELS[ability]}</span>
                      <span className="chat-mini-sheet__chip-mod">{mod >= 0 ? `+${mod}` : mod}</span>
                      <Dices size={12} aria-hidden />
                    </button>
                  </Tooltip>
                );
              })}
            </div>
          </div>

          {proficientSkills.length > 0 && (
            <div className="chat-mini-sheet__section">
              <h4>Habilidades competentes</h4>
              <div className="chat-mini-sheet__grid">
                {proficientSkills.map((skill) => {
                  const mod = dnd5eSkillModifier(sheet, skill.name, abilityModifier);
                  return (
                    <Tooltip key={skill.name} content={`Tirar ${skill.name}`}>
                      <button
                        type="button"
                        className="chat-mini-sheet__roll-chip"
                        disabled={disabled || isRolling}
                        aria-label={`Tirar ${skill.name}`}
                        onClick={() =>
                          void roll({ roll_type: "skill_check", context: { skill: skill.name } })
                        }
                      >
                        <span className="chat-mini-sheet__chip-label">{skill.name}</span>
                        <span className="chat-mini-sheet__chip-mod">{mod >= 0 ? `+${mod}` : mod}</span>
                        <Dices size={12} aria-hidden />
                      </button>
                    </Tooltip>
                  );
                })}
              </div>
            </div>
          )}

          {sheet.attacks.length > 0 && (
            <div className="chat-mini-sheet__section">
              <h4>Ataques</h4>
              <div className="chat-mini-sheet__attacks">
                {sheet.attacks.map((attack, index) => (
                  <div key={`${attack.name}-${index}`} className="chat-mini-sheet__attack-row">
                    <span>{attack.name || `Ataque ${index + 1}`}</span>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={disabled || isRolling}
                      onClick={() =>
                        void roll({
                          roll_type: "attack_roll",
                          context: { attack_index: index, attack_name: attack.name },
                        })
                      }
                    >
                      Tirar ataque
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="chat-mini-sheet__footer">
            <Button
              type="button"
              variant="secondary"
              disabled={disabled || isRolling}
              onClick={() => void roll({ roll_type: "initiative" })}
            >
              Iniciativa
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
