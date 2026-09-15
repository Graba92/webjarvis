"use client";

import React, { useState, useEffect, useRef } from "react";
import dynamic from "next/dynamic";
import { GraphData, GraphNode, NodeCategory, AssistantState } from "@/lib/types";
import { INITIAL_GRAPH_DATA, CATEGORY_COLORS } from "@/lib/graphData";
import { socketManager } from "@/lib/websocket";
import { ApexOverviewPanel } from "@/components/ApexOverviewPanel";
import { AgentCockpit } from "@/components/AgentCockpit";
import { BottomDock } from "@/components/BottomDock";
import { ConfirmBanner } from "@/components/ConfirmBanner";
import { DeviceControlPanel } from "@/components/DeviceControlPanel";
import { ContentStudio } from "@/components/ContentStudio";
import { ApiKeyModal } from "@/components/ApiKeyModal";
import { SkillsModal } from "@/components/SkillsModal";
import type { ApexWorldHandle } from "@/components/ApexWorld";

// Dynamischer Import von Three.js ohne SSR
const ApexWorld = dynamic(
  () => import("@/components/ApexWorld").then((mod) => mod.ApexWorld),
  { ssr: false }
);

export default function Home() {
  const [data, setData] = useState<GraphData>(INITIAL_GRAPH_DATA);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [repelForce, setRepelForce] = useState<number>(140);
  const [linkLength, setLinkLength] = useState<number>(80);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [is2D, setIs2D] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<Set<NodeCategory>>(
    new Set(Object.keys(CATEGORY_COLORS) as NodeCategory[])
  );

  const [assistantState, setAssistantState] = useState<AssistantState>("OFFLINE");
  const [audioLevel, setAudioLevel] = useState<number>(0);

  // Modals
  const [isDevicePanelOpen, setIsDevicePanelOpen] = useState<boolean>(false);
  const [isContentStudioOpen, setIsContentStudioOpen] = useState<boolean>(false);
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState<boolean>(false);
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState<boolean>(false);

  const apexWorldRef = useRef<ApexWorldHandle>(null);

  useEffect(() => {
    // WebSocket Bridge initialisieren
    socketManager.init();

    const unsubState = socketManager.onState(setAssistantState);
    const unsubAudio = socketManager.onAudioLevel(setAudioLevel);
    const unsubGraph = socketManager.onGraphUpdate(setData);

    return () => {
      unsubState();
      unsubAudio();
      unsubGraph();
    };
  }, []);

  const handleToggleFilter = (cat: NodeCategory) => {
    setActiveFilter((prev) => {
      const next = new Set(prev);
      if (next.has(cat)) {
        next.delete(cat);
      } else {
        next.add(cat);
      }
      return next;
    });
  };

  const handleToggle2D = (to2D: boolean) => {
    setIs2D(to2D);
    apexWorldRef.current?.toggle2D(to2D);
  };

  const handleFitView = () => {
    apexWorldRef.current?.fitToView();
  };

  const handleResetTarget = () => {
    setSelectedNode(null);
    apexWorldRef.current?.resetTarget();
  };

  const handleFocusNode = (nodeId: string) => {
    apexWorldRef.current?.focusNode(nodeId);
  };

  // Zähle Knoten pro Kategorie
  const categoryCounts = Object.keys(CATEGORY_COLORS).reduce((acc, cat) => {
    acc[cat as NodeCategory] = data.nodes.filter((n) => n.category === cat).length;
    return acc;
  }, {} as Record<NodeCategory, number>);

  return (
    <main className="relative w-screen h-screen overflow-hidden bg-[#080808]">
      {/* 1. Three.js WebGL 3D Knowledge Graph Canvas (Hintergrund-Ebene z-0) */}
      <ApexWorld
        ref={apexWorldRef}
        data={data}
        repelForce={repelForce}
        linkLength={linkLength}
        activeFilter={activeFilter}
        searchQuery={searchQuery}
        audioLevel={audioLevel}
        assistantState={assistantState}
        onNodeSelect={setSelectedNode}
      />

      {/* 2. Linke Telemetrie-Sidebar & Obere Floating Toolbar */}
      <ApexOverviewPanel
        data={data}
        selectedNode={selectedNode}
        repelForce={repelForce}
        setRepelForce={setRepelForce}
        linkLength={linkLength}
        setLinkLength={setLinkLength}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        is2D={is2D}
        onToggle2D={handleToggle2D}
        onFitView={handleFitView}
        onResetTarget={handleResetTarget}
        onFocusNode={handleFocusNode}
      />

      {/* 3. Rechte Sidebar: J.A.R.V.I.S. Core, Arc Reactor & Sensor Matrix */}
      <AgentCockpit
        state={assistantState}
        audioLevel={audioLevel}
        activeFilter={activeFilter}
        onToggleFilter={handleToggleFilter}
        categoryCounts={categoryCounts}
        onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
      />

      {/* 4. Untere Steuerungsleiste: Terminal-Bubble, Prompt-Input & Tool-Dock */}
      <BottomDock
        onOpenDevicePanel={() => setIsDevicePanelOpen(true)}
        onOpenContentStudio={() => setIsContentStudioOpen(true)}
        onOpenSkillsModal={() => setIsSkillsModalOpen(true)}
      />

      {/* 5. Hardware Confirmation Gate Banner (Höchste Priorität z-50) */}
      <ConfirmBanner />

      {/* 6. Modals */}
      <DeviceControlPanel
        isOpen={isDevicePanelOpen}
        onClose={() => setIsDevicePanelOpen(false)}
        onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
      />

      <ContentStudio
        isOpen={isContentStudioOpen}
        onClose={() => setIsContentStudioOpen(false)}
      />

      <ApiKeyModal
        isOpen={isApiKeyModalOpen}
        onClose={() => setIsApiKeyModalOpen(false)}
      />

      <SkillsModal
        isOpen={isSkillsModalOpen}
        onClose={() => setIsSkillsModalOpen(false)}
      />
    </main>
  );
}
