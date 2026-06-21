import { useEffect, useState } from "react";

import { ApiError } from "../../api/http";
import { Swords } from "../../components/icons";
import { Button, CollapsibleSection, ErrorBanner, Input } from "../../components/ui";
import { useMonsterCatalogSearchQuery, useSpawnMonstersMutation } from "../../hooks/mutations/useMonsterMutations";
import type { MonsterCatalogSummary } from "../../api/types";
import { NpcVisibilityControl } from "./NpcVisibilityControl";
import type { NpcPlayerVisibility } from "./playerVisibility";

type MonsterSpawnPanelProps = {
  campaignId: string;
  gameSystem: string;
  onSpawned: (message: string) => void;
};

function formatMonsterSource(monster: MonsterCatalogSummary): string | null {
  if (monster.source_label?.trim()) {
    return monster.source_label;
  }
  if (monster.source_document === "srd-2014") {
    return "SRD 5.1";
  }
  return monster.source_document || null;
}

export function MonsterSpawnPanel({ campaignId, gameSystem, onSpawned }: MonsterSpawnPanelProps) {
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [selected, setSelected] = useState<MonsterCatalogSummary | null>(null);
  const [count, setCount] = useState(1);
  const [playerVisibility, setPlayerVisibility] = useState<NpcPlayerVisibility>("hidden");

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  const { data: results = [], isFetching } = useMonsterCatalogSearchQuery(
    gameSystem,
    debouncedSearch,
    gameSystem === "dnd5e" && debouncedSearch.length > 0,
  );
  const spawnMutation = useSpawnMonstersMutation(campaignId);
  const selectedSource = selected ? formatMonsterSource(selected) : null;

  async function handleSpawn() {
    if (!selected) return;
    try {
      const response = await spawnMutation.mutateAsync({
        slug: selected.slug,
        count,
        player_visibility: playerVisibility,
      });
      onSpawned(`${response.count} ${selected.name}${response.count === 1 ? "" : "s"} añadido(s) al mundo.`);
      setSelected(null);
      setSearch("");
      setDebouncedSearch("");
      setCount(1);
    } catch {
      // ErrorBanner below
    }
  }

  if (gameSystem !== "dnd5e") {
    return null;
  }

  return (
    <CollapsibleSection
      icon={Swords}
      iconTone="rose"
      title="Catálogo de monstruos SRD"
      description="Busca en el bestiario SRD (CC BY 4.0) y añade NPCs con ficha D&D 5e sin abrir el editor."
      defaultOpen={false}
    >
      <div className="monster-spawn-panel">
        <div className="monster-spawn-panel__search">
          <Input
            label="Buscar monstruo"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setSelected(null);
            }}
            placeholder="Ej. goblin, orc, dragon"
          />
        </div>

        {debouncedSearch && (
          <div className="monster-spawn-panel__results" role="listbox" aria-label="Resultados del catálogo">
            {isFetching && <p className="muted">Buscando...</p>}
            {!isFetching && results.length === 0 && (
              <p className="muted">Sin resultados para «{debouncedSearch}».</p>
            )}
            {!isFetching &&
              results.map((monster) => {
                const source = formatMonsterSource(monster);
                return (
                <button
                  key={monster.slug}
                  type="button"
                  role="option"
                  aria-selected={selected?.slug === monster.slug}
                  className={`monster-spawn-panel__result${selected?.slug === monster.slug ? " is-selected" : ""}`}
                  onClick={() => setSelected(monster)}
                >
                  <span className="monster-spawn-panel__result-name">{monster.name}</span>
                  <span className="monster-spawn-panel__result-meta">
                    CR {monster.challenge_rating} · {monster.creature_type} · {monster.size}
                    {source ? ` · ${source}` : ""}
                  </span>
                </button>
              );
              })}
          </div>
        )}

        {selected && (
          <div className="monster-spawn-panel__spawn">
            <p className="muted">
              Seleccionado: <strong>{selected.name}</strong> (CR {selected.challenge_rating}
              {selectedSource ? ` · ${selectedSource}` : ""})
            </p>
            <div className="monster-spawn-panel__controls">
              <Input
                label="Cantidad"
                type="number"
                min={1}
                max={50}
                value={String(count)}
                onChange={(event) => setCount(Math.max(1, Math.min(50, Number(event.target.value) || 1)))}
              />
              <div className="monster-spawn-panel__visibility">
                <span className="monster-spawn-panel__visibility-label">Visibilidad inicial</span>
                <NpcVisibilityControl value={playerVisibility} onChange={setPlayerVisibility} compact />
              </div>
            </div>
            <Button onClick={handleSpawn} disabled={spawnMutation.isPending}>
              {spawnMutation.isPending ? "Añadiendo..." : `Añadir ${count} ${selected.name}${count === 1 ? "" : "s"}`}
            </Button>
            {spawnMutation.error && (
              <ErrorBanner
                message={
                  spawnMutation.error instanceof ApiError
                    ? spawnMutation.error.message
                    : "No se pudieron crear los monstruos."
                }
              />
            )}
          </div>
        )}

        <p className="monster-spawn-panel__attribution muted">
          Bestiario SRD vía{" "}
          <a href="https://open5e.com" target="_blank" rel="noreferrer">
            Open5e
          </a>{" "}
          (CC BY 4.0). Atribución: Wizards of the Coast SRD 5.1.
        </p>
      </div>
    </CollapsibleSection>
  );
}
