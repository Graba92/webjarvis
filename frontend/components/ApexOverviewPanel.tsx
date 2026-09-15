"use client";

import React, { useState } from "react";
import { GraphData, GraphNode, NodeCategory } from "@/lib/types";
import { CATEGORY_COLORS } from "@/lib/graphData";
import { Search, Maximize2, Crosshair, Layers, Sliders, Info } from "lucide-react";

interface ApexOverviewPanelProps {
  data: GraphData;
  selectedNode: GraphNode | null;
  repelForce: number;
  setRepelForce: (val: number) => void;
  linkLength: number;
  setLinkLength: (val: number) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  is2D: boolean;
  onToggle2D: (is2D: boolean) => void;
  onFitView: () => void;
  onResetTarget: () => void;
  onFocusNode: (nodeId: string) => void;
}

export const ApexOverviewPanel: React.FC<ApexOverviewPanelProps> = ({
  data,
  selectedNode,
  repelForce,
  setRepelForce,
  linkLength,
  setLinkLength,
  searchQuery,
  setSearchQuery,
  is2D,
  onToggle2D,
  onFitView,
  onResetTarget,
  onFocusNode,
}) => {
  const [showPhysics, setShowPhysics] = useState(true);

  // Top 8 Hubs nach Vernetzungsgrad sortiert
  const topHubs = [...data.nodes]
    .sort((a, b) => b.connections - a.connections)
    .slice(0, 8);

  return (
    <>
      {/* 1. Obere Floating Toolbar (Zentriert) */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-30 flex items-center gap-1.5 px-3 py-1.5 rounded-full glass-panel border border-[#1f242d] shadow-lg">
        <button
          onClick={onFitView}
          className="flex items-center gap-1 px-3 py-1 rounded-full text-xs text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
          title="Gesamten Graphen einpassen"
        >
          <Maximize2 className="w-3.5 h-3.5 text-[#00d4ff]" />
          <span>Fit</span>
        </button>
        <div className="w-[1px] h-4 bg-[#1f242d]" />
        <button
          onClick={onResetTarget}
          className="p-1.5 rounded-full text-gray-300 hover:text-white hover:bg-white/10 transition-colors"
          title="Fokus auf Ursprung zurücksetzen"
        >
          <Crosshair className="w-3.5 h-3.5 text-[#22c55e]" />
        </button>
        <div className="w-[1px] h-4 bg-[#1f242d]" />
        <button
          onClick={() => onToggle2D(!is2D)}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-full text-xs transition-colors ${
            is2D ? "bg-[#a855f7]/20 text-[#a855f7] border border-[#a855f7]/40" : "text-gray-300 hover:text-white"
          }`}
          title="Zwischen 2D-Projektion und 3D-Raum wechseln"
        >
          <Layers className="w-3.5 h-3.5" />
          <span>{is2D ? "2D Mode" : "3D Space"}</span>
        </button>
      </div>

      {/* 2. Linke Sidebar: Telemetrie & Graph Physics (280px) */}
      <div className="absolute top-4 left-4 z-30 w-72 max-h-[calc(100vh-2rem)] flex flex-col gap-3 rounded-xl glass-panel p-4 overflow-y-auto">
        {/* Header */}
        <div className="border-b border-[#1f242d] pb-2.5">
          <div className="flex items-center justify-between">
            <h1 className="text-sm font-black tracking-wider text-white flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#00d4ff] animate-ping" />
              AI WORKSHOP OS
            </h1>
            <button
              onClick={() => onToggle2D(!is2D)}
              className="text-[10px] text-gray-400 hover:text-[#00d4ff] transition-colors"
            >
              {is2D ? "→ switch to 3D" : "← back to 2D"}
            </button>
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">
            {data.nodes.length} nodes · {data.links.length} connections
          </div>
        </div>

        {/* Suchfeld */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-gray-500" />
          <input
            type="text"
            placeholder="Search the brain..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[#080a0f]/80 border border-[#1f242d] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-[#00d4ff]/60 transition-colors"
          />
        </div>

        {/* Inspector Box */}
        <div className="rounded-lg bg-[#080a0f]/50 border border-[#1f242d] p-2.5 text-xs text-gray-300">
          {selectedNode ? (
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="font-bold text-white flex items-center gap-1.5">
                  <span
                    className="w-2 h-2 rounded-full inline-block"
                    style={{ backgroundColor: CATEGORY_COLORS[selectedNode.category] }}
                  />
                  {selectedNode.name}
                </span>
                <span className="text-[10px] text-[#00d4ff]">{selectedNode.category}</span>
              </div>
              <p className="text-[11px] text-gray-400 leading-normal">
                {selectedNode.description}
              </p>
            </div>
          ) : (
            <div className="flex items-start gap-2 text-gray-400 text-[11px] leading-relaxed">
              <Info className="w-3.5 h-3.5 text-[#00d4ff] shrink-0 mt-0.5" />
              <span>
                Knoten anklicken zum Fokussieren. <kbd className="px-1 py-0.5 rounded bg-white/10 text-[9px] text-white">Shift</kbd> + Klick auf zweiten Knoten berechnet den kürzesten Pfad.
              </span>
            </div>
          )}
        </div>

        {/* Top Hubs Ranking */}
        <div>
          <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-1.5">
            Top Hubs
          </div>
          <div className="flex flex-col gap-1">
            {topHubs.map((hub) => (
              <button
                key={hub.id}
                onClick={() => onFocusNode(hub.id)}
                className={`flex items-center justify-between px-2 py-1.5 rounded-md text-xs transition-colors text-left ${
                  selectedNode?.id === hub.id
                    ? "bg-[#00d4ff]/20 text-white border border-[#00d4ff]/40"
                    : "hover:bg-white/5 text-gray-300"
                }`}
              >
                <div className="flex items-center gap-2 truncate">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ backgroundColor: CATEGORY_COLORS[hub.category] }}
                  />
                  <span className="truncate">{hub.name}</span>
                </div>
                <span className="text-[10px] text-gray-500 font-mono ml-2 shrink-0">
                  {hub.connections}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Forces (Physik-Slider) */}
        <div className="border-t border-[#1f242d] pt-2.5">
          <div
            className="flex items-center justify-between text-[11px] font-bold text-gray-400 uppercase tracking-wider cursor-pointer mb-2"
            onClick={() => setShowPhysics(!showPhysics)}
          >
            <span className="flex items-center gap-1.5">
              <Sliders className="w-3 h-3 text-[#22c55e]" />
              Forces
            </span>
            <span className="text-[10px]">{showPhysics ? "▲" : "▼"}</span>
          </div>

          {showPhysics && (
            <div className="flex flex-col gap-2.5 text-xs text-gray-300">
              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span>Repel (Abstoßung)</span>
                  <span className="text-[#22c55e] font-mono">{repelForce}</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="300"
                  value={repelForce}
                  onChange={(e) => setRepelForce(Number(e.target.value))}
                  className="w-full accent-[#22c55e] bg-gray-700 h-1 rounded"
                />
              </div>

              <div>
                <div className="flex justify-between text-[11px] mb-1">
                  <span>Link Length (Kantenlänge)</span>
                  <span className="text-[#22c55e] font-mono">{linkLength}</span>
                </div>
                <input
                  type="range"
                  min="30"
                  max="160"
                  value={linkLength}
                  onChange={(e) => setLinkLength(Number(e.target.value))}
                  className="w-full accent-[#22c55e] bg-gray-700 h-1 rounded"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};
