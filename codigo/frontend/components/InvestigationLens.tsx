import EyeMark from "./EyeMark";

// An illustration of the workflow, never a representation of live findings.
export default function InvestigationLens() {
  return <div className="wb-lensScene" aria-label="Ilustração do percurso: fontes, evidências e contexto" role="img">
    <div className="wb-orbit wb-orbitOuter" /><div className="wb-orbit wb-orbitInner" /><div className="wb-radarSweep" />
    <div className="wb-lensCenter"><EyeMark /><span>OBSERVAR</span></div>
    <span className="wb-orbitLabel wb-orbitSource"><i />Fontes públicas</span><span className="wb-orbitLabel wb-orbitEvidence"><i />Evidências</span><span className="wb-orbitLabel wb-orbitContext"><i />Contexto + IA</span>
    <div className="wb-lensCaption"><span>RECOLHER</span><span>CRUZAR</span><span>COMPREENDER</span></div>
  </div>;
}
