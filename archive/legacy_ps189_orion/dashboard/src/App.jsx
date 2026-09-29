import React, { useState, useMemo } from 'react';
import Header from './components/Header';
import KPICards from './components/KPICards';
import NetworkGraph from './components/NetworkGraph';
import EntityDossier from './components/EntityDossier';
import TypologyStories from './components/TypologyStories';
import LinkPredictionStudio from './components/LinkPredictionStudio';
import EntityResolutionWorkbench from './components/EntityResolutionWorkbench';
import CasesView from './components/CasesView';
import PipelineWorkbench from './components/PipelineWorkbench';
import AboutView from './components/AboutView';
import BSAReportModal from './components/BSAReportModal';
import GuidedDemoModal from './components/GuidedDemoModal';

// Pre-compiled intelligence dataset
import intelligenceData from './data/intelligence_data.json';

export default function App() {
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline' | 'network' | 'typologies' | 'link_prediction' | 'entity_resolution' | 'cases'
  const [selectedNode, setSelectedNode] = useState(null);
  const [isBSAModalOpen, setIsBSAModalOpen] = useState(false);
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Default graph: Mule Fan-In (MULE_01)
  const defaultTypology = intelligenceData.typologies?.find(t => t.typology_id === 'MULE_01') || intelligenceData.typologies?.[0];

  const [currentGraph, setCurrentGraph] = useState({
    nodes: defaultTypology?.nodes || [],
    edges: defaultTypology?.edges || [],
    title: 'Mule Fan-In Ring (MULE_01)',
    subtitle: defaultTypology?.narrative || '12 source accounts converge on mule collector A00013 within 30 hours.',
    warningBanner: null,
    typologyId: 'MULE_01'
  });

  // Handle Typology Selection from TypologyStories or Guided Tour
  const handleSelectTypology = (typology) => {
    let warning = null;
    if (typology.typology_id === 'TOPOLOGICAL_BRIDGE' || typology.warning) {
      warning = typology.warning || {
        title: 'NON-CHRONOLOGICAL REACHABILITY WARNING',
        message: 'Shortest path timestamps run out of chronological order (Sep 2024 ➔ Jun 2025 ➔ Feb 2024). Inferred topological reachability, NOT a money trail.'
      };
    }

    setCurrentGraph({
      nodes: typology.nodes || [],
      edges: typology.edges || [],
      title: typology.title || `${typology.typology_id} (${typology.pattern_type})`,
      subtitle: typology.narrative,
      warningBanner: warning,
      typologyId: typology.typology_id
    });

    setActiveTab('network');
  };

  // Inspecting Evidence Subgraph from Link Prediction Studio
  const handleInspectPredictedSubgraph = (prediction, graphType) => {
    const nodes = [
      { id: prediction.src, label: prediction.src, entity_type: graphType === 'financial' ? 'Account' : 'PhoneNumber', role: 'Link Endpoint 1' },
      { id: prediction.dst, label: prediction.dst, entity_type: graphType === 'financial' ? 'Account' : 'PhoneNumber', role: 'Link Endpoint 2' }
    ];

    const edges = [
      {
        id: `PRED_${prediction.src}_${prediction.dst}`,
        source: prediction.src,
        target: prediction.dst,
        type: 'POTENTIAL_CONNECTION',
        taxonomy: 'Predicted',
        score: prediction.score,
        reason: `Model probability: ${Math.round(prediction.score * 100)}% (Adamic-Adar: ${prediction.adamic_adar})`
      }
    ];

    // Add intermediate nodes and edges from connecting paths
    if (prediction.connecting_paths && prediction.connecting_paths.length > 0) {
      const addedNodeIds = new Set([prediction.src, prediction.dst]);
      prediction.connecting_paths.slice(0, 3).forEach((path, pIdx) => {
        for (let i = 0; i < path.length; i++) {
          const nId = path[i];
          if (!addedNodeIds.has(nId)) {
            addedNodeIds.add(nId);
            nodes.push({
              id: nId,
              label: nId,
              entity_type: graphType === 'financial' ? 'Account' : 'PhoneNumber',
              role: 'Pass-Through Associate'
            });
          }
          if (i > 0) {
            edges.push({
              id: `PATH_E_${pIdx}_${i}`,
              source: path[i - 1],
              target: path[i],
              type: graphType === 'financial' ? 'TRANSACTED' : 'CALLED',
              taxonomy: 'Explicit',
              evidence_id: `EVD_PATH_${pIdx + 1}`
            });
          }
        }
      });
    }

    setCurrentGraph({
      nodes,
      edges,
      title: `Predicted Link Evidence Subgraph: ${prediction.src} ➔ ${prediction.dst}`,
      subtitle: `Discovered with Random Forest Classifier (Confidence: ${(prediction.score * 100).toFixed(1)}%, Rank #${prediction.rank || 1}). Showing shared connecting paths.`,
      warningBanner: {
        title: 'PREDICTED LINK REQUIRING CORROBORATION',
        message: 'This edge is an AI hypothesis generated from structural proximity and common paths. It constitutes an investigative lead, not judicial proof.'
      },
      typologyId: `PRED_${prediction.src}`
    });

    setActiveTab('network');
  };

  // Handle Demo Tour Step Execution
  const handleSelectDemoStep = (step) => {
    if (step.typologyId === 'BSA_REPORT') {
      setIsBSAModalOpen(true);
      return;
    }

    if (step.typologyId === 'TOPOLOGICAL_BRIDGE') {
      const bridge = intelligenceData.topological_bridge;
      handleSelectTypology({
        typology_id: 'TOPOLOGICAL_BRIDGE',
        pattern_type: 'INFERRED_TOPOLOGICAL_BRIDGE',
        title: bridge.title,
        narrative: bridge.warning_message,
        nodes: bridge.nodes,
        edges: bridge.edges,
        warning: {
          title: bridge.warning_title,
          message: bridge.warning_message
        }
      });
      return;
    }

    const t = intelligenceData.typologies?.find(item => item.typology_id === step.typologyId);
    if (t) {
      handleSelectTypology(t);
    }
  };

  // Global search match
  const filteredGraph = useMemo(() => {
    if (!searchQuery.trim()) return currentGraph;
    const q = searchQuery.toLowerCase();
    
    // Highlight or filter matching nodes
    const matchingNode = currentGraph.nodes.find(n => 
      n.id?.toLowerCase().includes(q) || 
      n.holder_name?.toLowerCase().includes(q) ||
      n.label?.toLowerCase().includes(q)
    );

    if (matchingNode && selectedNode?.id !== matchingNode.id) {
      setSelectedNode(matchingNode);
    }

    return currentGraph;
  }, [searchQuery, currentGraph, selectedNode]);

  // Handle selecting an entity candidate from Entity Resolution Workbench
  const handleSelectEntityCandidate = (cand) => {
    const node = {
      id: cand.entity_id,
      label: cand.canonical_name,
      entity_type: 'Person',
      role: 'Master Person Index (MPI)',
      holder_name: `${cand.canonical_name} (Alias: ${cand.alias_value})`,
      pan_hash: cand.pan_hash,
      status: 'Verified Identity'
    };
    setCurrentGraph(prev => ({
      ...prev,
      nodes: prev.nodes.some(n => n.id === node.id) ? prev.nodes : [...prev.nodes, node],
      title: `Resolved Identity: ${cand.canonical_name} (${cand.entity_id})`,
      subtitle: `Matched variant "${cand.alias_value}" via ${cand.alias_type} (${Math.round(cand.confidence_score * 100)}% match confidence).`
    }));
    setSelectedNode(node);
    setActiveTab('network');
  };

  // Handle selecting a case from Cases View
  const handleSelectCase = (c) => {
    const caseNode = {
      id: c.case_id,
      label: c.fir_number,
      entity_type: 'Case',
      role: c.case_category,
      status: c.case_status,
      holder_name: `${c.police_station} (${c.jurisdiction})`,
      source_document_id: c.source_document_id
    };
    const docNode = {
      id: c.source_document_id,
      label: c.source_document_id,
      entity_type: 'Document',
      role: 'CCTNS Evidence Record'
    };
    const edge = {
      id: `E_${c.case_id}_DOC`,
      source: c.case_id,
      target: c.source_document_id,
      type: 'RECORDED_IN',
      taxonomy: 'Explicit',
      evidence_id: c.source_document_id
    };
    setCurrentGraph({
      nodes: [caseNode, docNode],
      edges: [edge],
      title: `Investigation Case: ${c.fir_number} (${c.case_id})`,
      subtitle: `${c.case_type} - ${c.case_category} registered at ${c.police_station}. Provenance: ${c.source_document_id}`,
      warningBanner: null,
      typologyId: c.case_id
    });
    setSelectedNode(caseNode);
    setActiveTab('network');
  };

  // Inspect Lead Subgraph from Pipeline Workbench
  const handleInspectLeadSubgraph = (lead) => {
    const rawNodes = lead.evidence_subgraph?.nodes || [];
    const rawEdges = lead.evidence_subgraph?.edges || [];

    const formattedNodes = rawNodes.map(n => ({
      id: n.id,
      label: n.label || n.id,
      entity_type: n.entity_type || 'Account',
      role: n.role || (n.id === lead.primary_suspect?.canonical_id ? 'Primary Suspect' : 'Involved Entity'),
      holder_name: n.holder_name || '',
      bank: n.bank || ''
    }));

    const formattedEdges = rawEdges.map((e, idx) => ({
      id: e.id || `LEAD_E_${idx}`,
      source: e.source,
      target: e.target,
      type: e.type || e.edge_type || 'TRANSACTED',
      taxonomy: e.taxonomy || 'Explicit',
      amount: e.amount || 0,
      timestamp: e.timestamp || '',
      evidence_id: e.evidence_id || 'EVD_LEAD_SUBGRAPH'
    }));

    setCurrentGraph({
      nodes: formattedNodes,
      edges: formattedEdges,
      title: `${lead.title} (${lead.lead_id})`,
      subtitle: lead.narrative_summary,
      warningBanner: {
        title: 'SECTION 63 BSA INVESTIGATIVE LEAD SUBGRAPH',
        message: 'This evidence subgraph represents an investigative lead under Section 63 BSA. For human investigator verification.'
      },
      typologyId: lead.lead_id
    });

    setActiveTab('network');
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#070a13] text-slate-100 overflow-hidden select-none font-sans">
      {/* Top Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onStartDemo={() => setIsDemoModalOpen(true)}
        onOpenBSA={() => setIsBSAModalOpen(true)}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
      />

      {/* Main Content Workspace */}
      <main className="flex-1 flex overflow-hidden relative">
        {activeTab === 'pipeline' && (
          <div className="flex-1 h-full overflow-y-auto p-6">
            <PipelineWorkbench
              onInspectLeadSubgraph={handleInspectLeadSubgraph}
              onOpenBSACertificate={(lead) => {
                const targetNode = lead.evidence_subgraph?.nodes?.[0] || {
                  id: lead.primary_suspect?.canonical_id || 'SUSPECT_01',
                  label: lead.primary_suspect?.canonical_name || 'Suspect',
                  entity_type: 'Person'
                };
                setSelectedNode(targetNode);
                setIsBSAModalOpen(true);
              }}
            />
          </div>
        )}

        {activeTab === 'network' && (
          <div className="flex-1 flex relative overflow-hidden">
            <div className="flex-1 h-full p-3">
              <NetworkGraph
                graphData={filteredGraph}
                selectedNode={selectedNode}
                onSelectNode={(node) => setSelectedNode(node)}
                title={currentGraph.title}
                subtitle={currentGraph.subtitle}
                warningBanner={currentGraph.warningBanner}
              />
            </div>

            {/* Slide-out Entity Dossier */}
            {selectedNode && (
              <EntityDossier
                node={selectedNode}
                onClose={() => setSelectedNode(null)}
                onOpenBSA={(node) => {
                  setSelectedNode(node);
                  setIsBSAModalOpen(true);
                }}
              />
            )}
          </div>
        )}

        {activeTab === 'typologies' && (
          <div className="flex-1 h-full">
            <TypologyStories
              typologies={intelligenceData.typologies}
              topologicalBridge={intelligenceData.topological_bridge}
              onSelectTypology={handleSelectTypology}
              selectedTypologyId={currentGraph.typologyId}
              oddballList={intelligenceData.oddball_top}
              temporalList={intelligenceData.temporal_top}
            />
          </div>
        )}

        {activeTab === 'link_prediction' && (
          <div className="flex-1 h-full">
            <LinkPredictionStudio
              linkPredictionData={intelligenceData.link_prediction}
              onInspectSubgraph={handleInspectPredictedSubgraph}
            />
          </div>
        )}

        {activeTab === 'entity_resolution' && (
          <div className="flex-1 h-full">
            <EntityResolutionWorkbench
              entityResolutionData={intelligenceData.entity_resolution}
              onSelectCandidate={handleSelectEntityCandidate}
            />
          </div>
        )}

        {activeTab === 'cases' && (
          <div className="flex-1 h-full">
            <CasesView
              casesData={intelligenceData.cases}
              onSelectCase={handleSelectCase}
            />
          </div>
        )}

        {activeTab === 'about' && (
          <AboutView />
        )}
      </main>

      {/* Section 63 BSA Export Modal */}
      {isBSAModalOpen && (
        <BSAReportModal
          node={selectedNode}
          currentGraph={currentGraph}
          onClose={() => setIsBSAModalOpen(false)}
        />
      )}

      {/* Guided Judge Tour Modal */}
      {isDemoModalOpen && (
        <GuidedDemoModal
          onClose={() => setIsDemoModalOpen(false)}
          onSelectStep={handleSelectDemoStep}
        />
      )}
    </div>
  );
}
