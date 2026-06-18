import { useParams } from "react-router-dom";

import { SECTION_ICONS } from "../components/icons";
import { Panel, PanelHeader } from "../components/ui";
import { DocumentLibrary } from "../features/library";
import { SystemManualsPanel } from "../features/library/SystemManualsPanel";
import { useCampaignQuery } from "../hooks/queries/useCampaignQueries";

export function LibraryPage() {
  const { campaignId = "" } = useParams();
  const { data: campaign } = useCampaignQuery(campaignId);

  return (
    <div className="library-page">
      <Panel className="page-intro">
        <PanelHeader
          icon={SECTION_ICONS.biblioteca}
          iconTone="amber"
          title="Biblioteca"
          description="Material de referencia de la campaña y reglas oficiales indexadas para la IA."
        />
      </Panel>
      <Panel>
        <SystemManualsPanel gameSystem={campaign?.game_system} />
      </Panel>
      <DocumentLibrary campaignId={campaignId} />
    </div>
  );
}
