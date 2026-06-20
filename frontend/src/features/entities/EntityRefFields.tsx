import { useMemo } from "react";

import { getEntityDisplayName, type CampaignEntity } from "./entityDefaults";

type EntityRefFieldsProps = {
  entities: CampaignEntity[];
  factionId: string;
  locationId: string;
  onFactionChange: (value: string) => void;
  onLocationChange: (value: string) => void;
};

export function EntityRefFields({
  entities,
  factionId,
  locationId,
  onFactionChange,
  onLocationChange,
}: EntityRefFieldsProps) {
  const factionOptions = useMemo(
    () => entities.filter((item) => item.entity_type === "FACTION"),
    [entities],
  );
  const locationOptions = useMemo(
    () => entities.filter((item) => item.entity_type === "LOCATION"),
    [entities],
  );

  return (
    <>
      <label className="form-field">
        <span>Facción (opcional)</span>
        <select value={factionId} onChange={(event) => onFactionChange(event.target.value)}>
          <option value="">Sin facción</option>
          {factionOptions.map((item) => (
            <option key={item.id} value={item.id}>
              {getEntityDisplayName(item, entities)}
            </option>
          ))}
        </select>
      </label>
      <label className="form-field">
        <span>Ubicación actual (opcional)</span>
        <select value={locationId} onChange={(event) => onLocationChange(event.target.value)}>
          <option value="">Sin ubicación</option>
          {locationOptions.map((item) => (
            <option key={item.id} value={item.id}>
              {getEntityDisplayName(item, entities)}
            </option>
          ))}
        </select>
      </label>
    </>
  );
}
