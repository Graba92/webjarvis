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
import { DevConsole } from "@/components/DevConsole";
import { JarvisChatWindow } from "@/components/JarvisChatWindow";
import { PersonalityWizardModal } from "@/components/PersonalityWizardModal";
import { CalendarModal } from "@/components/CalendarModal";
import { BackupModal } from "@/components/BackupModal";
import { SandboxModal } from "@/components/SandboxModal";
import { BacklogDrawer } from "@/components/BacklogDrawer";
import WikiInspectorModal from "@/components/WikiInspectorModal";
import { GuideOverlayModal } from "@/components/GuideOverlayModal";
import { GuideOverlayData } from "@/lib/types";
import type { ApexWorldHandle } from "@/components/ApexWorld";

// Dynamischer Import von Three.js ohne SSR
const ApexWorld = dynamic(
  () => import("@/components/ApexWorld").then((mod) => mod.ApexWorld),
  { ssr: false }
);

export default function Home() {
  const [data, setData] = useState<GraphData>(INITIAL_GRAPH_DATA);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [inspectorNode, setInspectorNode] = useState<GraphNode | null>(null);
  const [repelForce, setRepelForce] = useState<number>(140);
  const [linkLength, setLinkLength] = useState<number>(80);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [is2D, setIs2D] = useState<boolean>(false);
  const [activeFilter, setActiveFilter] = useState<Set<NodeCategory>>(
    new Set(Object.keys(CATEGORY_COLORS) as NodeCategory[])
  );

  const [assistantState, setAssistantState] = useState<AssistantState>("OFFLINE");
  const [audioLevel, setAudioLevel] = useState<number>(0);

  // Modals & Panels
  const [isDevicePanelOpen, setIsDevicePanelOpen] = useState<boolean>(false);
  const [isContentStudioOpen, setIsContentStudioOpen] = useState<boolean>(false);
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState<boolean>(false);
  const [isSkillsModalOpen, setIsSkillsModalOpen] = useState<boolean>(false);
  const [isDevConsoleOpen, setIsDevConsoleOpen] = useState<boolean>(false);
  const [isChatWindowOpen, setIsChatWindowOpen] = useState<boolean>(false);
  const [isPersonalityWizardOpen, setIsPersonalityWizardOpen] = useState<boolean>(false);
  const [isCalendarOpen, setIsCalendarOpen] = useState<boolean>(false);
  const [isBackupModalOpen, setIsBackupModalOpen] = useState<boolean>(false);
  const [isSandboxModalOpen, setIsSandboxModalOpen] = useState<boolean>(false);
  const [isBacklogOpen, setIsBacklogOpen] = useState<boolean>(false);
  const [activeGuide, setActiveGuide] = useState<GuideOverlayData | null>(null);

  const apexWorldRef = useRef<ApexWorldHandle>(null);

  useEffect(() => {
    // WebSocket Bridge initialisieren
    socketManager.init();

    const unsubState = socketManager.onState(setAssistantState);
    const unsubAudio = socketManager.onAudioLevel(setAudioLevel);
    const unsubGraph = socketManager.onGraphUpdate(setData);
    const unsubGuide = socketManager.onGuide(setActiveGuide);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && (e.key === "c" || e.key === "C")) {
        e.preventDefault();
        setIsCalendarOpen((prev) => !prev);
      }
      if (e.altKey && (e.key === "t" || e.key === "T" || e.key === "b" || e.key === "B")) {
        e.preventDefault();
        setIsBacklogOpen((prev) => !prev);
      }
      if (e.altKey && (e.key === "g" || e.key === "G" || e.key === "h" || e.key === "H")) {
        e.preventDefault();
        socketManager.triggerGuide("interactive_tutorial");
      }
    };
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      unsubState();
      unsubAudio();
      unsubGraph();
      unsubGuide();
      window.removeEventListener("keydown", handleKeyDown);
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
        onNodeInspect={(node) => setInspectorNode(node)}
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
        onOpenInspector={(node) => setInspectorNode(node)}
      />

      {/* 3. Rechte Sidebar: J.A.R.V.I.S. Core, Arc Reactor, Killswitch & Sensor Matrix */}
      <AgentCockpit
        state={assistantState}
        audioLevel={audioLevel}
        activeFilter={activeFilter}
        onToggleFilter={handleToggleFilter}
        categoryCounts={categoryCounts}
        onOpenApiKeyModal={() => setIsApiKeyModalOpen(true)}
        onOpenCalendarModal={() => setIsCalendarOpen(true)}
        onOpenSandboxModal={() => setIsSandboxModalOpen(true)}
      />

      {/* 4. Untere Steuerungsleiste: Terminal-Bubble, Prompt-Input & Tool-Dock */}
      <BottomDock
        onOpenDevicePanel={() => setIsDevicePanelOpen(true)}
        onOpenContentStudio={() => setIsContentStudioOpen(true)}
        onOpenSkillsModal={() => setIsSkillsModalOpen(true)}
        onOpenDevConsole={() => setIsDevConsoleOpen((prev) => !prev)}
        onOpenChatWindow={() => setIsChatWindowOpen((prev) => !prev)}
        onOpenPersonalityWizard={() => setIsPersonalityWizardOpen(true)}
        onOpenCalendarModal={() => setIsCalendarOpen(true)}
        onOpenBackupModal={() => setIsBackupModalOpen(true)}
        onOpenSandboxModal={() => setIsSandboxModalOpen(true)}
        onOpenBacklog={() => setIsBacklogOpen(true)}
        onOpenGuide={() => socketManager.triggerGuide("interactive_tutorial")}
        orphanCount={data.nodes ? data.nodes.filter((n) => n.connections === 0 || n.is_orphan || n.status === "orphan").length : 0}
        onFocusOrphan={() => {
          const firstOrphan = data.nodes?.find((n) => n.connections === 0 || n.is_orphan || n.status === "orphan");
          if (firstOrphan && apexWorldRef.current) {
            apexWorldRef.current.focusNode(firstOrphan.id);
          }
        }}
      />

      {/* 5. Jarvis Live Chat Window (verschiebbar & in der Größe anpassbar) */}
      <JarvisChatWindow
        isOpen={isChatWindowOpen}
        onClose={() => setIsChatWindowOpen(false)}
        onOpenDevConsole={() => setIsDevConsoleOpen(true)}
      />

      {/* 6. Live Dev-Console Floating Drawer (verschiebbar & in der Größe anpassbar) */}
      <DevConsole
        isOpen={isDevConsoleOpen}
        onClose={() => setIsDevConsoleOpen(false)}
      />

      {/* 6. Personality Wizard Modal */}
      <PersonalityWizardModal
        isOpen={isPersonalityWizardOpen}
        onClose={() => setIsPersonalityWizardOpen(false)}
      />

      {/* 7. Terminkalender & Tagesbriefing Modal */}
      <CalendarModal
        isOpen={isCalendarOpen}
        onClose={() => setIsCalendarOpen(false)}
      />

      {/* 8. Brain Vault: Backup & Restore Modal */}
      <BackupModal
        isOpen={isBackupModalOpen}
        onClose={() => setIsBackupModalOpen(false)}
      />

      {/* 9. Sandbox & OS-Vollzugriff Modal */}
      <SandboxModal
        isOpen={isSandboxModalOpen}
        onClose={() => setIsSandboxModalOpen(false)}
      />

      {/* 9.5 Task Matrix / Backlog Drawer (Single Source of Truth) */}
      {isBacklogOpen && (
        <BacklogDrawer onClose={() => setIsBacklogOpen(false)} />
      )}

      {/* 9.6 Wissens- & Node-Inspektor Modal */}
      {inspectorNode && (
        <WikiInspectorModal
          node={inspectorNode}
          onClose={() => setInspectorNode(null)}
          onNavigateToNode={(target) => {
            const found = data.nodes?.find(
              (n) =>
                n.name.toLowerCase() === target.toLowerCase() ||
                n.id.toLowerCase() === target.toLowerCase() ||
                n.id.toLowerCase() === `wiki-${target.toLowerCase().replace(/[^a-z0-9_-]/g, "-")}`
            );
            if (found) {
              setInspectorNode(found);
              setSelectedNode(found);
              if (apexWorldRef.current) {
                apexWorldRef.current.focusNode(found.id);
              }
            } else {
              setInspectorNode({
                id: `wiki-${target.toLowerCase().replace(/[^a-z0-9_-]/g, "-")}`,
                name: target,
                category: "Wiki",
                connections: 0,
                description: `Kuratierter Artikel zu ${target}`
              });
            }
          }}
        />
      )}

      {/* 9.7 Interaktive Schritt-für-Schritt Bild-Anleitung mit Pfeilen & Slideshow */}
      {activeGuide && (
        <GuideOverlayModal
          guide={activeGuide}
          onClose={() => socketManager.closeGuide()}
        />
      )}

      {/* 10. Hardware Confirmation Gate Banner (Höchste Priorität z-50) */}
      <ConfirmBanner />

      {/* 11. Modals */}
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
