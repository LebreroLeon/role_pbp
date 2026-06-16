import { FormEvent, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../api/http";
import type { DocumentType } from "../../api/types";
import { Sparkles } from "../../components/icons";
import { Button, ErrorBanner, Input, Panel, PanelHeader, Section } from "../../components/ui";
import { useCreateCampaignMutation } from "../../hooks/mutations/useCampaignMutations";
import { useUploadDocumentMutation } from "../../hooks/queries/useDocumentQueries";
import { GAME_SYSTEM_GROUPS } from "./gameSystems";
import { InviteMemberForm } from "./InviteMemberForm";

type WizardStep = 1 | 2 | 3 | 4;

export function CreateCampaignWizard() {
  const navigate = useNavigate();
  const [step, setStep] = useState<WizardStep>(1);
  const [name, setName] = useState("");
  const [tone, setTone] = useState("");
  const [gameSystem, setGameSystem] = useState("dnd5e");
  const [campaignId, setCampaignId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const [documentType, setDocumentType] = useState<DocumentType>("RULES");
  const [uploadedCount, setUploadedCount] = useState(0);

  const createMutation = useCreateCampaignMutation();
  const uploadMutation = useUploadDocumentMutation(campaignId ?? "");

  async function handleBasicSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setError(null);
    try {
      const campaign = await createMutation.mutateAsync({
        name: name.trim(),
        tone: tone.trim() || undefined,
        game_system: gameSystem,
      });
      setCampaignId(campaign.id);
      setStep(2);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear la campaña");
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!campaignId) return;
    const file = fileRef.current?.files?.[0];
    if (!file) {
      setStep(3);
      return;
    }
    setError(null);
    try {
      await uploadMutation.mutateAsync({ file, documentType });
      setUploadedCount((count) => count + 1);
      if (fileRef.current) fileRef.current.value = "";
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo subir el archivo");
    }
  }

  function finishWizard() {
    if (campaignId) navigate(`/campaigns/${campaignId}`);
  }

  return (
    <div className="wizard-page">
      <Panel>
        <PanelHeader
          icon={Sparkles}
          iconTone="rose"
          title="Nueva campaña"
          description="Configura tu partida en unos pasos. Podrás añadir más material después."
        />

        <ol className="wizard-steps">
          <li className={step === 1 ? "is-active" : step > 1 ? "is-done" : ""}>1. Básico</li>
          <li className={step === 2 ? "is-active" : step > 2 ? "is-done" : ""}>2. Biblioteca</li>
          <li className={step === 3 ? "is-active" : step > 3 ? "is-done" : ""}>3. Jugadores</li>
          <li className={step === 4 ? "is-active" : ""}>4. Empezar</li>
        </ol>

        {error && <ErrorBanner message={error} />}

        {step === 1 && (
          <form className="auth-form" onSubmit={handleBasicSubmit}>
            <Input label="Nombre de la campaña" value={name} onChange={(e) => setName(e.target.value)} required />
            <label className="form-field">
              <span>Sistema de juego</span>
              <select value={gameSystem} onChange={(e) => setGameSystem(e.target.value)}>
                {GAME_SYSTEM_GROUPS.map((group) => (
                  <optgroup key={group.category} label={group.label}>
                    {group.systems.map((system) => (
                      <option key={system.value} value={system.value}>
                        {system.label}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </label>
            <Input
              label="Tono narrativo (opcional)"
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              placeholder="Ej. intriga urbana, horror cósmico, heroico..."
            />
            <Button type="submit" disabled={createMutation.isPending || !name.trim()}>
              {createMutation.isPending ? "Creando..." : "Continuar"}
            </Button>
          </form>
        )}

        {step === 2 && campaignId && (
          <Section tone="amber">
            <p className="muted">
              Sube manuales, el módulo de aventura o notas. Quedarán en la biblioteca de la campaña.
            </p>
            <form className="auth-form" onSubmit={handleUpload}>
              <label className="form-field">
                <span>Tipo</span>
                <select value={documentType} onChange={(e) => setDocumentType(e.target.value as DocumentType)}>
                  <option value="RULES">Reglas / manual</option>
                  <option value="ADVENTURE">Aventura / módulo</option>
                  <option value="NOTES">Notas</option>
                  <option value="OTHER">Otro</option>
                </select>
              </label>
              <label className="form-field">
                <span>Archivo (opcional)</span>
                <input ref={fileRef} type="file" accept=".pdf,.json,.txt,.md,.docx,.zip" />
              </label>
              <div className="actions">
                <Button type="submit" disabled={uploadMutation.isPending}>
                  {uploadMutation.isPending ? "Subiendo..." : "Subir otro archivo"}
                </Button>
                <Button type="button" variant="secondary" onClick={() => setStep(3)}>
                  {uploadedCount > 0 ? `Continuar (${uploadedCount} subidos)` : "Omitir por ahora"}
                </Button>
              </div>
            </form>
          </Section>
        )}

        {step === 3 && campaignId && (
          <>
            <p className="muted">Invita jugadores por email. Deben tener cuenta en RolePBP.</p>
            <InviteMemberForm campaignId={campaignId} />
            <div className="actions">
              <Button type="button" onClick={() => setStep(4)}>
                Continuar
              </Button>
            </div>
          </>
        )}

        {step === 4 && campaignId && (
          <div className="wizard-finish">
            <p>Tu campaña está lista. Desde el inicio puedes:</p>
            <ul className="wizard-finish__list">
              <li>
                <strong>Jugar</strong> — abre el chat e inicia la primera escena
              </li>
              <li>
                <strong>Mundo</strong> — crea NPCs y ubicaciones (o importa JSON)
              </li>
              <li>
                <strong>Biblioteca</strong> — añade más PDFs cuando quieras
              </li>
              <li>
                <strong>Mesa</strong> — controla la escena e invita más jugadores
              </li>
            </ul>
            <Button onClick={finishWizard}>Ir a la campaña</Button>
          </div>
        )}
      </Panel>
    </div>
  );
}
