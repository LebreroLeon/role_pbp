import { buildNpcDocument, buildLocationDocument } from "./entityDefaults";

export const NPC_TEMPLATE = buildNpcDocument({
  name: "Nombre del NPC",
  concept: "Rol en la historia",
  publicDescription: "Lo que los jugadores pueden saber a simple vista.",
  secretLore: "Motivaciones ocultas, secretos y planes del Máster.",
  voiceAndTone: "Seco, irónico, formal...",
  personalityTraits: "cauteloso, leal, sarcástico",
});

export const LOCATION_TEMPLATE = buildLocationDocument({
  name: "Nombre del lugar",
  locationType: "taberna",
  publicDescription: "Descripción que los jugadores perciben al llegar.",
  secretLore: "Pasadizos, trampas o lore oculto.",
  ambientTone: "Tenso, acogedor, decadente...",
});

export const EXPORT_FORMAT_HINT = `Formato de importación RolePBP:
{
  "version": "1.0",
  "campaign_id": "...",
  "entities": [
    { "entity_type": "NPC", "document": { ... } },
    { "entity_type": "LOCATION", "document": { ... } }
  ]
}`;

export function downloadJson(filename: string, data: unknown) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
