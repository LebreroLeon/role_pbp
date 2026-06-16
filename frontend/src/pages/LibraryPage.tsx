import { useParams } from "react-router-dom";

import { SECTION_ICONS } from "../components/icons";
import { Panel, PanelHeader } from "../components/ui";
import { DocumentLibrary } from "../features/library";

export function LibraryPage() {
  const { campaignId = "" } = useParams();

  return (
    <div className="library-page">
      <Panel className="page-intro">
        <PanelHeader
          icon={SECTION_ICONS.biblioteca}
          iconTone="amber"
          title="Biblioteca"
          description="Material de referencia de la campaña: manuales, módulos y notas. Más adelante la IA consultará estos archivos."
        />
      </Panel>
      <DocumentLibrary campaignId={campaignId} />
    </div>
  );
}
