import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Layers, 
  Eye, 
  Info,
  Maximize2,
  FileText,
  ShieldCheck
} from 'lucide-react';
import { formatINR, formatDateTime } from '../utils/crypto';

export default function NetworkGraph({ 
  graphData, 
  selectedNode, 
  onSelectNode,
  title,
  subtitle,
  warningBanner
}) {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const zoomBehaviorRef = useRef(null);

  // Filter toggles
  const [showExplicit, setShowExplicit] = useState(true);
  const [showInferred, setShowInferred] = useState(true);
  const [showPredicted, setShowPredicted] = useState(true);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [hoveredEdge, setHoveredEdge] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || !graphData) return;

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 550;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Defs for markers and filters
    const defs = svg.append('defs');

    // Arrow markers for Explicit (Emerald)
    defs.append('marker')
      .attr('id', 'arrow-explicit')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#10b981');

    // Arrow marker for Inferred (Amber)
    defs.append('marker')
      .attr('id', 'arrow-inferred')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#f59e0b');

    // Arrow marker for Predicted (Purple)
    defs.append('marker')
      .attr('id', 'arrow-predicted')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#a855f7');

    // Glow filter
    const glowFilter = defs.append('filter')
      .attr('id', 'glow')
      .attr('x', '-50%')
      .attr('y', '-50%')
      .attr('width', '200%')
      .attr('height', '200%');
    glowFilter.append('feGaussianBlur')
      .attr('stdDeviation', '4')
      .attr('result', 'coloredBlur');
    const feMerge = glowFilter.append('feMerge');
    feMerge.append('feMergeNode').attr('in', 'coloredBlur');
    feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

    const g = svg.append('g').attr('class', 'main-group');

    // Zoom setup
    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    zoomBehaviorRef.current = zoom;
    svg.call(zoom);

    // Deep clone data for D3 mutation
    const nodes = (graphData.nodes || []).map(d => ({ ...d }));
    let edges = (graphData.edges || []).map(d => ({ ...d }));

    // Filter edges according to taxonomy toggle
    edges = edges.filter(e => {
      const tax = (e.taxonomy || 'Explicit').toLowerCase();
      if (tax === 'explicit' && !showExplicit) return false;
      if (tax === 'inferred' && !showInferred) return false;
      if (tax === 'predicted' && !showPredicted) return false;
      return true;
    });

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(edges).id(d => d.id).distance(d => {
        if (d.taxonomy === 'Inferred') return 180;
        if (d.taxonomy === 'Predicted') return 160;
        return 120;
      }))
      .force('charge', d3.forceManyBody().strength(-380))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(32));

    // Render Edges
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(edges)
      .enter()
      .append('line')
      .attr('stroke', d => {
        if (d.taxonomy === 'Inferred') return '#f59e0b';
        if (d.taxonomy === 'Predicted') return '#a855f7';
        return '#10b981';
      })
      .attr('stroke-width', d => {
        if (d.amount) {
          return Math.max(2, Math.min(6, Math.log10(d.amount)));
        }
        return 2.5;
      })
      .attr('stroke-dasharray', d => {
        if (d.taxonomy === 'Inferred') return '6,4';
        if (d.taxonomy === 'Predicted') return '3,3';
        return 'none';
      })
      .attr('marker-end', d => {
        if (d.taxonomy === 'Inferred') return 'url(#arrow-inferred)';
        if (d.taxonomy === 'Predicted') return 'url(#arrow-predicted)';
        return 'url(#arrow-explicit)';
      })
      .attr('opacity', 0.85)
      .style('cursor', 'pointer')
      .on('mouseenter', (event, d) => {
        setHoveredEdge(d);
        const [x, y] = d3.pointer(event, containerRef.current);
        setTooltipPos({ x: x + 15, y: y + 15 });
      })
      .on('mouseleave', () => setHoveredEdge(null));

    // Render Edge Labels (for amounts or relationship types)
    const edgeLabels = g.append('g')
      .attr('class', 'edge-labels')
      .selectAll('text')
      .data(edges)
      .enter()
      .append('text')
      .attr('fill', d => d.taxonomy === 'Inferred' ? '#fbbf24' : (d.taxonomy === 'Predicted' ? '#c084fc' : '#6ee7b7'))
      .attr('font-size', '9px')
      .attr('font-family', 'var(--font-mono)')
      .attr('text-anchor', 'middle')
      .text(d => {
        if (d.amount) return formatINR(d.amount);
        if (d.call_duration_sec) return `${Math.round(d.call_duration_sec)}s call`;
        return d.type || '';
      });

    // Render Nodes
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }))
      .on('click', (event, d) => {
        event.stopPropagation();
        onSelectNode(d);
      })
      .on('mouseenter', (event, d) => {
        setHoveredNode(d);
        const [x, y] = d3.pointer(event, containerRef.current);
        setTooltipPos({ x: x + 15, y: y + 15 });
      })
      .on('mouseleave', () => setHoveredNode(null));

    // Node Outer Glow / Highlight if selected
    node.append('circle')
      .attr('r', d => (selectedNode?.id === d.id ? 24 : 18))
      .attr('fill', d => {
        if (d.role === 'Mule Collector' || d.role === 'Scatter Source') return 'rgba(239, 68, 68, 0.2)';
        if (d.entity_type === 'Person') return 'rgba(56, 189, 248, 0.15)';
        if (d.entity_type === 'PhoneNumber') return 'rgba(6, 182, 212, 0.15)';
        return 'rgba(16, 185, 129, 0.15)';
      })
      .attr('stroke', d => {
        if (selectedNode?.id === d.id) return '#38bdf8';
        if (d.role === 'Mule Collector' || d.role === 'Scatter Source') return '#ef4444';
        if (d.entity_type === 'Person') return '#38bdf8';
        if (d.entity_type === 'PhoneNumber') return '#06b6d4';
        return '#10b981';
      })
      .attr('stroke-width', d => (selectedNode?.id === d.id ? 3 : 1.8))
      .attr('filter', d => (selectedNode?.id === d.id || d.role?.includes('Mule') ? 'url(#glow)' : 'none'));

    // Inner icon / letter representation
    node.append('circle')
      .attr('r', 11)
      .attr('fill', d => {
        if (d.role === 'Mule Collector' || d.role === 'Scatter Source') return '#b91c1c';
        if (d.entity_type === 'Person') return '#0369a1';
        if (d.entity_type === 'PhoneNumber') return '#0e7490';
        return '#047857';
      });

    node.append('text')
      .attr('dy', 3.5)
      .attr('text-anchor', 'middle')
      .attr('fill', '#ffffff')
      .attr('font-size', '9px')
      .attr('font-weight', 'bold')
      .text(d => {
        if (d.entity_type === 'Person') return 'P';
        if (d.entity_type === 'PhoneNumber') return '☎';
        return '₹';
      });

    // Node Labels
    node.append('text')
      .attr('dy', 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#f1f5f9')
      .attr('font-size', '10px')
      .attr('font-weight', '600')
      .attr('font-family', 'var(--font-mono)')
      .text(d => d.label || d.id);

    // Role Sub-label
    node.append('text')
      .attr('dy', 42)
      .attr('text-anchor', 'middle')
      .attr('fill', d => d.role?.includes('Collector') || d.role?.includes('Source') ? '#fca5a5' : '#94a3b8')
      .attr('font-size', '8.5px')
      .text(d => d.role || d.entity_type);

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      edgeLabels
        .attr('x', d => (d.source.x + d.target.x) / 2)
        .attr('y', d => (d.source.y + d.target.y) / 2 - 4);

      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });

    return () => simulation.stop();
  }, [graphData, selectedNode, showExplicit, showInferred, showPredicted]);

  const handleZoomIn = () => {
    if (svgRef.current && zoomBehaviorRef.current) {
      d3.select(svgRef.current).transition().call(zoomBehaviorRef.current.scaleBy, 1.3);
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current && zoomBehaviorRef.current) {
      d3.select(svgRef.current).transition().call(zoomBehaviorRef.current.scaleBy, 0.7);
    }
  };

  const handleResetZoom = () => {
    if (svgRef.current && zoomBehaviorRef.current) {
      d3.select(svgRef.current).transition().call(zoomBehaviorRef.current.transform, d3.zoomIdentity);
    }
  };

  return (
    <div className="relative w-full h-full flex flex-col bg-[#080d1a] overflow-hidden rounded-xl border border-slate-800" ref={containerRef}>
      {/* Graph Header / Subgraph Banner */}
      <div className="absolute top-3 left-3 z-10 max-w-lg bg-[#0e1629]/90 backdrop-blur-md p-3 rounded-xl border border-slate-700/60 shadow-xl pointer-events-auto">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-sky-400" />
          <h3 className="text-sm font-bold text-white tracking-tight">{title || 'Interactive Criminal Knowledge Graph'}</h3>
        </div>
        <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{subtitle || 'Explore entities, cash flows, and communication links.'}</p>
      </div>

      {/* Warning Banner (e.g. for Non-Chronological Shortest Path) */}
      {warningBanner && (
        <div className="absolute top-3 right-3 z-10 max-w-md bg-amber-950/80 backdrop-blur-md p-3 rounded-xl border border-amber-500/50 shadow-xl pointer-events-auto flex items-start gap-2.5">
          <div className="w-5 h-5 rounded-full bg-amber-500/20 flex items-center justify-center shrink-0 mt-0.5 text-amber-400 font-bold text-xs">
            !
          </div>
          <div>
            <h4 className="text-xs font-bold text-amber-300 uppercase tracking-wide">{warningBanner.title}</h4>
            <p className="text-[11px] text-amber-200/90 mt-1 leading-normal">{warningBanner.message}</p>
          </div>
        </div>
      )}

      {/* Floating Toolbar Controls */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-wrap items-center gap-2 bg-[#0e1629]/90 backdrop-blur-md px-3 py-2 rounded-xl border border-slate-700/60 shadow-xl pointer-events-auto">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mr-1">Taxonomy:</span>
        <button
          onClick={() => setShowExplicit(!showExplicit)}
          className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
            showExplicit ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-slate-800 text-slate-500 border border-transparent opacity-60'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>Explicit (Documented)</span>
        </button>

        <button
          onClick={() => setShowInferred(!showInferred)}
          className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
            showInferred ? 'bg-amber-500/20 text-amber-400 border border-amber-500/40' : 'bg-slate-800 text-slate-500 border border-transparent opacity-60'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-amber-400"></span>
          <span>Inferred (Topological)</span>
        </button>

        <button
          onClick={() => setShowPredicted(!showPredicted)}
          className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
            showPredicted ? 'bg-purple-500/20 text-purple-400 border border-purple-500/40' : 'bg-slate-800 text-slate-500 border border-transparent opacity-60'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-purple-400"></span>
          <span>Predicted (ML Link)</span>
        </button>
      </div>

      {/* Zoom / Navigation Widget */}
      <div className="absolute bottom-4 right-4 z-10 flex items-center gap-1 bg-[#0e1629]/90 backdrop-blur-md p-1 rounded-xl border border-slate-700/60 shadow-xl pointer-events-auto">
        <button onClick={handleZoomIn} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white" title="Zoom In">
          <ZoomIn className="w-4 h-4" />
        </button>
        <button onClick={handleZoomOut} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white" title="Zoom Out">
          <ZoomOut className="w-4 h-4" />
        </button>
        <button onClick={handleResetZoom} className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-300 hover:text-white" title="Reset View">
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Main SVG Graph */}
      <svg ref={svgRef} className="w-full h-full cursor-grab active:cursor-grabbing" />

      {/* Hover Node Tooltip */}
      {hoveredNode && (
        <div 
          className="absolute z-30 pointer-events-none bg-slate-900/95 border border-sky-500/50 p-3 rounded-lg shadow-2xl max-w-xs text-xs"
          style={{ left: tooltipPos.x, top: tooltipPos.y }}
        >
          <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1 mb-1.5">
            <span className="font-bold text-sky-400 mono">{hoveredNode.id}</span>
            <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
              {hoveredNode.entity_type}
            </span>
          </div>
          {hoveredNode.holder_name && (
            <div className="text-slate-300 mb-1">
              <span className="text-slate-500">Holder:</span> <strong className="text-white">{hoveredNode.holder_name}</strong>
            </div>
          )}
          {hoveredNode.bank && (
            <div className="text-slate-400 text-[11px] mb-1">
              <span className="text-slate-500">Institution:</span> {hoveredNode.bank}
            </div>
          )}
          {hoveredNode.oddball && (
            <div className="mt-1.5 pt-1.5 border-t border-slate-800/60 text-amber-400 text-[11px] flex items-center justify-between">
              <span>OddBall Score:</span>
              <strong className="mono">{hoveredNode.oddball.score} (Rank {hoveredNode.oddball.rank})</strong>
            </div>
          )}
          {hoveredNode.temporal && (
            <div className="mt-0.5 text-purple-400 text-[11px] flex items-center justify-between">
              <span>Temporal Burst:</span>
              <strong className="mono">{hoveredNode.temporal.temporal_score}</strong>
            </div>
          )}
        </div>
      )}

      {/* Hover Edge Tooltip */}
      {hoveredEdge && (
        <div 
          className="absolute z-30 pointer-events-none bg-slate-900/95 border border-emerald-500/50 p-3 rounded-lg shadow-2xl max-w-xs text-xs"
          style={{ left: tooltipPos.x, top: tooltipPos.y }}
        >
          <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1 mb-1.5">
            <span className="font-bold text-emerald-400 mono">{hoveredEdge.type || 'RELATIONSHIP'}</span>
            <span className={`text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded ${
              hoveredEdge.taxonomy === 'Inferred' ? 'badge-inferred' : (hoveredEdge.taxonomy === 'Predicted' ? 'badge-predicted' : 'badge-explicit')
            }`}>
              {hoveredEdge.taxonomy || 'Explicit'}
            </span>
          </div>
          <div className="text-slate-300 mb-1 mono">
            {typeof hoveredEdge.source === 'object' ? hoveredEdge.source.id : hoveredEdge.source} ➔ {typeof hoveredEdge.target === 'object' ? hoveredEdge.target.id : hoveredEdge.target}
          </div>
          {hoveredEdge.amount && (
            <div className="text-slate-200 text-sm font-bold text-emerald-400 mono my-1">
              {formatINR(hoveredEdge.amount)}
            </div>
          )}
          {hoveredEdge.timestamp && (
            <div className="text-slate-400 text-[11px]">
              <span className="text-slate-500">Timestamp:</span> {formatDateTime(hoveredEdge.timestamp)}
            </div>
          )}
          {hoveredEdge.evidence_id && (
            <div className="text-slate-400 text-[11px] mt-1 pt-1 border-t border-slate-800">
              <span className="text-slate-500">Evidence ID:</span> <span className="mono text-sky-400">{hoveredEdge.evidence_id}</span>
            </div>
          )}
          {hoveredEdge.reason && (
            <div className="text-amber-300 text-[11px] mt-1 italic">
              {hoveredEdge.reason}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
