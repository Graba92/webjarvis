"use client";

import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from "react";
import * as THREE from "three";
import { GraphData, GraphNode, NodeCategory, AssistantState } from "@/lib/types";
import { CATEGORY_COLORS } from "@/lib/graphData";
import { socketManager } from "@/lib/websocket";

export interface ApexWorldHandle {
  fitToView: () => void;
  resetTarget: () => void;
  toggle2D: (is2D: boolean) => void;
  focusNode: (nodeId: string) => void;
}

interface ApexWorldProps {
  data: GraphData;
  repelForce: number;
  linkLength: number;
  activeFilter: Set<NodeCategory>;
  searchQuery: string;
  audioLevel?: number;
  assistantState?: AssistantState;
  onNodeSelect: (node: GraphNode | null) => void;
  onPathFound?: (path: string[]) => void;
}

interface InternalNode extends GraphNode {
  baseX: number;
  baseY: number;
  baseZ: number;
  baseRadius: number;
  pulsePhase: number;
}

interface DataPearl {
  mesh: THREE.Mesh;
  halo: THREE.Sprite;
  linkIndex: number;
  progress: number;
  speed: number;
  direction: 1 | -1;
}

interface CurvedLink {
  sourceId: string;
  targetId: string;
  curve: THREE.QuadraticBezierCurve3;
}

/**
 * Erzeugt eine weiche, radiale Alpha-Glow-Textur ohne externe Bilddateien.
 */
function createRadialGlowTexture(): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 128;
  canvas.height = 128;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
    gradient.addColorStop(0, "rgba(255, 255, 255, 1.0)");
    gradient.addColorStop(0.2, "rgba(255, 255, 255, 0.85)");
    gradient.addColorStop(0.45, "rgba(255, 255, 255, 0.35)");
    gradient.addColorStop(0.75, "rgba(255, 255, 255, 0.08)");
    gradient.addColorStop(1.0, "rgba(255, 255, 255, 0.0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 128, 128);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

export const ApexWorld = forwardRef<ApexWorldHandle, ApexWorldProps>(({
  data,
  repelForce,
  linkLength,
  activeFilter,
  searchQuery,
  audioLevel = 0,
  assistantState = "OFFLINE",
  onNodeSelect,
  onPathFound
}, ref) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<{ node: GraphNode; x: number; y: number } | null>(null);
  const [modalNode, setModalNode] = useState<{ node: GraphNode; x: number; y: number } | null>(null);

  // Three.js State Refs
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const constellationGroupRef = useRef<THREE.Group | null>(null);
  const nodeMeshesRef = useRef<Map<string, THREE.Mesh>>(new Map());
  const haloSpritesRef = useRef<Map<string, THREE.Sprite>>(new Map());
  const internalNodesRef = useRef<InternalNode[]>([]);
  const curvedLinksRef = useRef<CurvedLink[]>([]);
  const pearlsRef = useRef<DataPearl[]>([]);
  const is2DRef = useRef<boolean>(false);
  const selectedNodeRef = useRef<GraphNode | null>(null);
  const highlightedPathRef = useRef<Set<string>>(new Set());

  // Dynamic prop refs to avoid tearing inside the render loop
  const audioLevelRef = useRef<number>(audioLevel);
  audioLevelRef.current = audioLevel;
  const assistantStateRef = useRef<AssistantState>(assistantState);
  assistantStateRef.current = assistantState;
  const activeFilterRef = useRef<Set<NodeCategory>>(activeFilter);
  activeFilterRef.current = activeFilter;
  const searchQueryRef = useRef<string>(searchQuery);
  searchQueryRef.current = searchQuery;
  const repelForceRef = useRef<number>(repelForce);
  repelForceRef.current = repelForce;
  const linkLengthRef = useRef<number>(linkLength);
  linkLengthRef.current = linkLength;

  // Mouse Orbit Refs
  const isDraggingRef = useRef<boolean>(false);
  const previousMousePositionRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const cameraRotationRef = useRef<{ theta: number; phi: number; radius: number }>({
    theta: Math.PI / 4.2,
    phi: Math.PI / 2.8,
    radius: 440
  });

  // Shortest Path Finder (BFS Dijkstra-äquivalent für ungewichtete Graphen)
  const findShortestPath = (startId: string, endId: string): string[] => {
    const adj = new Map<string, string[]>();
    data.links.forEach((l) => {
      const s = typeof l.source === "object" ? (l.source as any).id : l.source;
      const t = typeof l.target === "object" ? (l.target as any).id : l.target;
      if (!adj.has(s)) adj.set(s, []);
      if (!adj.has(t)) adj.set(t, []);
      adj.get(s)!.push(t);
      adj.get(t)!.push(s);
    });

    const queue: string[][] = [[startId]];
    const visited = new Set<string>([startId]);

    while (queue.length > 0) {
      const path = queue.shift()!;
      const curr = path[path.length - 1];
      if (curr === endId) return path;

      const neighbors = adj.get(curr) || [];
      for (const n of neighbors) {
        if (!visited.has(n)) {
          visited.add(n);
          queue.push([...path, n]);
        }
      }
    }
    return [];
  };

  useImperativeHandle(ref, () => ({
    fitToView: () => {
      cameraRotationRef.current.radius = 450;
      updateCameraPosition();
    },
    resetTarget: () => {
      selectedNodeRef.current = null;
      highlightedPathRef.current.clear();
      onNodeSelect(null);
      cameraRotationRef.current = { theta: Math.PI / 4.2, phi: Math.PI / 2.8, radius: 440 };
      updateCameraPosition();
    },
    toggle2D: (to2D: boolean) => {
      is2DRef.current = to2D;
      if (to2D) {
        cameraRotationRef.current.phi = 0.001; // Vogelperspektive
      } else {
        cameraRotationRef.current.phi = Math.PI / 2.8;
      }
      updateCameraPosition();
    },
    focusNode: (nodeId: string) => {
      const target = internalNodesRef.current.find((n) => n.id === nodeId);
      if (target) {
        selectedNodeRef.current = target;
        onNodeSelect(target);
      }
    }
  }));

  const updateCameraPosition = () => {
    const cam = cameraRef.current;
    if (!cam) return;
    const { theta, phi, radius } = cameraRotationRef.current;
    const x = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);
    const z = radius * Math.sin(phi) * Math.cos(theta);

    cam.position.set(x, y, z);
    cam.lookAt(0, 0, 0);
  };

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || window.innerWidth;
    const height = container.clientHeight || window.innerHeight;

    // 1. Scene & Dark Background (#080808)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x080808);
    scene.fog = new THREE.FogExp2(0x080808, 0.0014);
    sceneRef.current = scene;

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(50, width / height, 1, 3500);
    cameraRef.current = camera;
    updateCameraPosition();

    // 3. High Performance WebGL Renderer
    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: "high-performance"
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x080808, 1);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Beleuchtung für leuchtende Sphären
    const ambLight = new THREE.AmbientLight(0xffffff, 0.85);
    scene.add(ambLight);

    // Lebendige Punktlichter passend zum Farbkonzept (Cyan, Blau, Warmes Orange)
    const pointCyan = new THREE.PointLight(0x00f0ff, 2.8, 900);
    pointCyan.position.set(220, 240, 200);
    scene.add(pointCyan);

    const pointBlue = new THREE.PointLight(0x2979ff, 2.2, 900);
    pointBlue.position.set(-220, 180, -220);
    scene.add(pointBlue);

    const pointOrange = new THREE.PointLight(0xff9100, 1.8, 900);
    pointOrange.position.set(0, -260, 150);
    scene.add(pointOrange);

    // 5. Dezente Raumstaub-/Sternenpartikel im Hintergrund
    const starCount = 650;
    const starGeo = new THREE.BufferGeometry();
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {
      starPos[i] = (Math.random() - 0.5) * 2200;
      starPos[i + 1] = (Math.random() - 0.5) * 2200;
      starPos[i + 2] = (Math.random() - 0.5) * 2200;
    }
    starGeo.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    const starMat = new THREE.PointsMaterial({
      color: 0x50d7ff,
      size: 1.6,
      transparent: true,
      opacity: 0.35,
      blending: THREE.AdditiveBlending
    });
    const starField = new THREE.Points(starGeo, starMat);
    scene.add(starField);

    // 6. Haupt-Constellation-Gruppe für globalen 3D-Drift & Taumeln
    const constellationGroup = new THREE.Group();
    scene.add(constellationGroup);
    constellationGroupRef.current = constellationGroup;

    // 7. Kohärente 3D-Struktur: Feste relative Positionen in 3 thematischen Clustern
    // Cluster-Zentren für Cyan (Router/Skills/Tools), Blau (Suites/Wiki/Files), Orange (Concepts/Worlds/Notes)
    const clusterCenters: Record<string, THREE.Vector3> = {
      Cyan: new THREE.Vector3(125, 35, 45),
      Blue: new THREE.Vector3(-95, 75, -65),
      Orange: new THREE.Vector3(-25, -85, 75)
    };

    const getGroupKey = (cat: NodeCategory): "Cyan" | "Blue" | "Orange" => {
      if (cat === "Router" || cat === "Skills" || cat === "Tools") return "Cyan";
      if (cat === "Suites" || cat === "Wiki" || cat === "Files") return "Blue";
      return "Orange";
    };

    // Feste Koordinaten-Generierung basierend auf Seed & Verbindungsstruktur
    const internalNodes: InternalNode[] = data.nodes.map((node, i) => {
      const groupKey = getGroupKey(node.category);
      const center = clusterCenters[groupKey];
      const isHub = node.id.startsWith("hub-");

      // Sphärische Winkelverteilung innerhalb des Clusters
      const angle = (i * 2.399963229728653) % (Math.PI * 2); // Goldener Schnitt Winkel
      const elevation = Math.sin(i * 1.7) * 0.75;
      const radius = isHub ? 35 + (i % 3) * 12 : 65 + (i % 5) * 16;

      const lx = radius * Math.cos(angle) * Math.cos(elevation);
      const ly = radius * Math.sin(elevation) * 1.2;
      const lz = radius * Math.sin(angle) * Math.cos(elevation);

      // Hubs näher am Systemursprung positionieren
      const baseX = isHub ? center.x * 0.55 + lx * 0.6 : center.x + lx;
      const baseY = isHub ? center.y * 0.55 + ly * 0.6 : center.y + ly;
      const baseZ = isHub ? center.z * 0.55 + lz * 0.6 : center.z + lz;

      // Größenvarianz: Radiant abhängig von Verbindungsanzahl (3.8 bis 14.5)
      const baseRadius = Math.max(3.8, Math.min(14.5, Math.sqrt(node.connections) * 2.15));

      return {
        ...node,
        baseX,
        baseY,
        baseZ,
        baseRadius,
        pulsePhase: i * 1.37 + Math.random() * 0.5,
        x: baseX,
        y: baseY,
        z: baseZ
      };
    });
    internalNodesRef.current = internalNodes;

    // 8. Glow-Halo-Textur für leuchtende Sphären
    const glowTexture = createRadialGlowTexture();

    // 9. Sphären-Meshes & Additive Glow-Halos erstellen
    const meshesMap = new Map<string, THREE.Mesh>();
    const halosMap = new Map<string, THREE.Sprite>();

    internalNodes.forEach((node) => {
      const colorHex = CATEGORY_COLORS[node.category] || "#00f0ff";
      const color = new THREE.Color(colorHex);

      // A. Kern-Sphäre mit hoher Eigenemission & Specular Gloss
      const sphereGeo = new THREE.SphereGeometry(node.baseRadius, 24, 24);
      const sphereMat = new THREE.MeshStandardMaterial({
        color: color,
        emissive: color,
        emissiveIntensity: 0.9,
        roughness: 0.15,
        metalness: 0.6,
        transparent: true,
        opacity: 0.95
      });
      const mesh = new THREE.Mesh(sphereGeo, sphereMat);
      mesh.position.set(node.baseX, node.baseY, node.baseZ);
      mesh.userData = { id: node.id };

      // B. Leuchtender Halo (Sprite mit additivem Blending)
      const haloMat = new THREE.SpriteMaterial({
        map: glowTexture,
        color: color,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });
      const halo = new THREE.Sprite(haloMat);
      const haloScale = node.baseRadius * 3.8;
      halo.scale.set(haloScale, haloScale, 1);
      mesh.add(halo);

      constellationGroup.add(mesh);
      meshesMap.set(node.id, mesh);
      halosMap.set(node.id, halo);
    });
    nodeMeshesRef.current = meshesMap;
    haloSpritesRef.current = halosMap;

    // 10. Geschwungene Leuchtlinien (Bézier-Kurven in Hellblau)
    const curvedLinks: CurvedLink[] = [];
    const segmentsPerCurve = 16;
    const totalLineVertices = data.links.length * segmentsPerCurve * 2;
    const linePos = new Float32Array(totalLineVertices * 3);
    const lineColors = new Float32Array(totalLineVertices * 3);

    // Initialisierung der geschwungenen Kurven
    data.links.forEach((link, lIdx) => {
      const sId = typeof link.source === "object" ? (link.source as any).id : link.source;
      const tId = typeof link.target === "object" ? (link.target as any).id : link.target;
      const n1 = internalNodes.find((n) => n.id === sId);
      const n2 = internalNodes.find((n) => n.id === tId);

      if (n1 && n2) {
        const p1 = new THREE.Vector3(n1.baseX, n1.baseY, n1.baseZ);
        const p2 = new THREE.Vector3(n2.baseX, n2.baseY, n2.baseZ);
        const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const delta = new THREE.Vector3().subVectors(p2, p1);
        const dist = delta.length();

        // Organischer Normalenvektor nach außen gekrümmt
        let normal = mid.clone().normalize();
        if (normal.lengthSq() < 0.001) normal = new THREE.Vector3(0, 1, 0);

        const side = new THREE.Vector3().crossVectors(delta, normal).normalize();
        const curvature = Math.min(30, Math.max(8, dist * 0.16));
        const ctrl = mid.clone().add(side.multiplyScalar(curvature * 0.55)).add(normal.multiplyScalar(curvature * 0.45));

        const curve = new THREE.QuadraticBezierCurve3(p1, ctrl, p2);
        curvedLinks.push({ sourceId: sId, targetId: tId, curve });

        // Punkte entlang der Kurve in den Positions-Buffer schreiben
        const points = curve.getPoints(segmentsPerCurve);
        let ptr = lIdx * segmentsPerCurve * 2 * 3;
        for (let s = 0; s < segmentsPerCurve; s++) {
          const ptA = points[s];
          const ptB = points[s + 1];

          linePos[ptr++] = ptA.x;
          linePos[ptr++] = ptA.y;
          linePos[ptr++] = ptA.z;

          linePos[ptr++] = ptB.x;
          linePos[ptr++] = ptB.y;
          linePos[ptr++] = ptB.z;
        }
      }
    });
    curvedLinksRef.current = curvedLinks;

    // Standardfarbe: Leuchtendes Hellblau (#50d7ff)
    const baseLineColor = new THREE.Color(0x50d7ff);
    for (let c = 0; c < lineColors.length; c += 3) {
      lineColors[c] = baseLineColor.r;
      lineColors[c + 1] = baseLineColor.g;
      lineColors[c + 2] = baseLineColor.b;
    }

    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute("position", new THREE.BufferAttribute(linePos, 3));
    lineGeo.setAttribute("color", new THREE.BufferAttribute(lineColors, 3));

    const lineMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.65,
      blending: THREE.AdditiveBlending,
      linewidth: 1
    });
    const linkLinesSegments = new THREE.LineSegments(lineGeo, lineMat);
    constellationGroup.add(linkLinesSegments);

    // 11. Wandernde Aktivitätsperlen ("Pearls")
    const pearlPoolSize = 24;
    const pearls: DataPearl[] = [];
    const pearlGeo = new THREE.SphereGeometry(1.6, 12, 12);
    const pearlMat = new THREE.MeshBasicMaterial({
      color: 0xffffff,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending
    });

    for (let p = 0; p < pearlPoolSize; p++) {
      const pMesh = new THREE.Mesh(pearlGeo, pearlMat.clone());
      const pHaloMat = new THREE.SpriteMaterial({
        map: glowTexture,
        color: new THREE.Color(0x50d7ff),
        transparent: true,
        opacity: 0.8,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });
      const pHalo = new THREE.Sprite(pHaloMat);
      pHalo.scale.set(6, 6, 1);
      pMesh.add(pHalo);

      const linkIdx = p % Math.max(1, curvedLinks.length);
      const pearl: DataPearl = {
        mesh: pMesh,
        halo: pHalo,
        linkIndex: linkIdx,
        progress: Math.random(),
        speed: 0.35 + Math.random() * 0.45,
        direction: Math.random() > 0.5 ? 1 : -1
      };
      constellationGroup.add(pMesh);
      pearls.push(pearl);
    }
    pearlsRef.current = pearls;

    // 12. Render- & Animationsloop
    let animationFrameId: number;
    let prevTime = performance.now();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const now = performance.now();
      const delta = Math.min(0.1, (now - prevTime) / 1000);
      prevTime = now;
      const time = now * 0.001;

      // A. Global Movement: Der gesamte Graph driftet und taumelt harmonisch im 3D-Raum
      const is2D = is2DRef.current;
      if (!is2D) {
        constellationGroup.rotation.y = Math.sin(time * 0.1) * 0.12 + time * 0.025;
        constellationGroup.rotation.x = Math.sin(time * 0.07) * 0.07;
        constellationGroup.rotation.z = Math.cos(time * 0.05) * 0.05;

        constellationGroup.position.x = Math.sin(time * 0.14) * 10;
        constellationGroup.position.y = Math.cos(time * 0.18) * 12;
        constellationGroup.position.z = Math.sin(time * 0.11) * 8;
      } else {
        constellationGroup.rotation.set(0, 0, 0);
        constellationGroup.position.set(0, 0, 0);
      }

      // Sternenfeld sanft drehen
      starField.rotation.y += 0.0002;

      // B. Skalierungsfaktor aus UI-Slidern (erhält relative Struktur perfekt)
      const scaleFactor = (linkLengthRef.current / 80) * (repelForceRef.current / 140);
      const query = searchQueryRef.current.trim().toLowerCase();
      const filter = activeFilterRef.current;
      const selected = selectedNodeRef.current;
      const pathSet = highlightedPathRef.current;

      // C. Sanfte kontinuierliche Pulsation von Helligkeit & Größe aller Knoten
      internalNodes.forEach((node) => {
        const mesh = meshesMap.get(node.id);
        const halo = halosMap.get(node.id);
        if (!mesh || !halo) return;

        // Position mit Slider-Skalierung aktualisieren
        const px = node.baseX * scaleFactor;
        const py = node.baseY * scaleFactor;
        const pz = is2D ? 0 : node.baseZ * scaleFactor;
        mesh.position.set(px, py, pz);
        node.x = px;
        node.y = py;
        node.z = pz;

        // Statusprüfung (Filterung, Suche, Selektion, Pfad)
        const matchesFilter = filter.has(node.category);
        const matchesSearch = query === "" || node.name.toLowerCase().includes(query) || node.description.toLowerCase().includes(query);
        const isVisible = matchesFilter && matchesSearch;

        const isSelected = selected?.id === node.id;
        const isOnPath = pathSet.has(node.id);
        const isNeighbor = selected
          ? data.links.some((l) => {
              const s = typeof l.source === "object" ? (l.source as any).id : l.source;
              const t = typeof l.target === "object" ? (l.target as any).id : l.target;
              return (s === selected.id && t === node.id) || (t === selected.id && s === node.id);
            })
          : true;

        // Harmonische Pulsationsberechnung
        const pulse = 1.0 + 0.12 * Math.sin(time * 2.3 + node.pulsePhase);
        mesh.scale.set(pulse, pulse, pulse);

        const sphereMat = mesh.material as THREE.MeshStandardMaterial;
        const haloMat = halo.material as THREE.SpriteMaterial;

        if (!isVisible) {
          sphereMat.opacity = 0.05;
          sphereMat.emissiveIntensity = 0.05;
          haloMat.opacity = 0.03;
        } else if (selected) {
          if (isSelected || isOnPath || isNeighbor) {
            sphereMat.opacity = 1.0;
            sphereMat.emissiveIntensity = (isSelected ? 1.4 : 1.0) * (0.85 + 0.3 * Math.sin(time * 3.0 + node.pulsePhase));
            haloMat.opacity = (isSelected ? 0.95 : 0.75) * (0.8 + 0.3 * Math.sin(time * 3.2 + node.pulsePhase));
          } else {
            sphereMat.opacity = 0.12;
            sphereMat.emissiveIntensity = 0.1;
            haloMat.opacity = 0.08;
          }
        } else {
          sphereMat.opacity = 0.95;
          sphereMat.emissiveIntensity = 0.85 * (0.85 + 0.35 * Math.sin(time * 2.5 + node.pulsePhase));
          haloMat.opacity = 0.65 * (0.8 + 0.3 * Math.sin(time * 2.7 + node.pulsePhase));
        }
      });

      // D. Aktualisierung der geschwungenen Verbindungslinien
      const posAttr = lineGeo.attributes.position as THREE.BufferAttribute;
      const colAttr = lineGeo.attributes.color as THREE.BufferAttribute;
      const positions = posAttr.array as Float32Array;
      const colors = colAttr.array as Float32Array;

      let vIdx = 0;
      curvedLinks.forEach((cLink) => {
        const n1 = internalNodes.find((n) => n.id === cLink.sourceId);
        const n2 = internalNodes.find((n) => n.id === cLink.targetId);
        if (!n1 || !n2) return;

        const p1 = new THREE.Vector3(n1.x, n1.y, n1.z);
        const p2 = new THREE.Vector3(n2.x, n2.y, n2.z);
        const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const deltaV = new THREE.Vector3().subVectors(p2, p1);
        const dist = deltaV.length();

        let normal = mid.clone().normalize();
        if (normal.lengthSq() < 0.001) normal = new THREE.Vector3(0, 1, 0);

        const side = new THREE.Vector3().crossVectors(deltaV, normal).normalize();
        const curvature = Math.min(30, Math.max(8, dist * 0.16));
        const ctrl = mid.clone().add(side.multiplyScalar(curvature * 0.55)).add(normal.multiplyScalar(curvature * 0.45));
        if (is2D) ctrl.z = 0;

        cLink.curve.v0.copy(p1);
        cLink.curve.v1.copy(ctrl);
        cLink.curve.v2.copy(p2);

        const pts = cLink.curve.getPoints(segmentsPerCurve);

        // Helligkeitsabstimmung nach Selektion / Kürzestem Pfad
        const isPathLink = (pathSet.has(n1.id) && pathSet.has(n2.id));
        const isSelectedLink = selected && (
          (selected.id === n1.id && (filter.has(n2.category))) ||
          (selected.id === n2.id && (filter.has(n1.category)))
        );

        let r = 0.31, g = 0.84, b = 1.0; // Hellblau (0x50d7ff)
        if (selected) {
          if (isPathLink || isSelectedLink) {
            r = 1.0; g = 1.0; b = 1.0; // Weißglühend bei Selektion
          } else {
            r = 0.06; g = 0.12; b = 0.18; // Stark abgedunkelt
          }
        }

        for (let s = 0; s < segmentsPerCurve; s++) {
          const ptA = pts[s];
          const ptB = pts[s + 1];

          positions[vIdx] = ptA.x;
          positions[vIdx + 1] = ptA.y;
          positions[vIdx + 2] = ptA.z;
          colors[vIdx] = r;
          colors[vIdx + 1] = g;
          colors[vIdx + 2] = b;
          vIdx += 3;

          positions[vIdx] = ptB.x;
          positions[vIdx + 1] = ptB.y;
          positions[vIdx + 2] = ptB.z;
          colors[vIdx] = r;
          colors[vIdx + 1] = g;
          colors[vIdx + 2] = b;
          vIdx += 3;
        }
      });
      posAttr.needsUpdate = true;
      colAttr.needsUpdate = true;

      // E. Network Activity: Daten-Perlen wandern schnell entlang der Verbindungen
      // Aktivitätsfaktor moduliert dynamisch über Audio & KI-Status
      const curState = assistantStateRef.current;
      const isWorking = curState === "THINKING" || curState === "SPEAKING" || curState === "LISTENING";
      const audioPulse = Math.min(3.0, (audioLevelRef.current || 0) * 4.5);
      const activityMultiplier = (isWorking ? 2.2 : 1.0) + audioPulse;

      if (curvedLinks.length > 0) {
        pearls.forEach((pearl) => {
          pearl.progress += delta * pearl.speed * activityMultiplier;
          if (pearl.progress >= 1.0) {
            pearl.progress = 0.0;
            // Neue Kurve wählen, bevorzugt aktiv verbundene Knoten
            if (selected) {
              const connectedIndices = curvedLinks
                .map((cl, idx) => (cl.sourceId === selected.id || cl.targetId === selected.id ? idx : -1))
                .filter((idx) => idx !== -1);
              if (connectedIndices.length > 0 && Math.random() > 0.3) {
                pearl.linkIndex = connectedIndices[Math.floor(Math.random() * connectedIndices.length)];
              } else {
                pearl.linkIndex = Math.floor(Math.random() * curvedLinks.length);
              }
            } else {
              pearl.linkIndex = Math.floor(Math.random() * curvedLinks.length);
            }
            pearl.direction = Math.random() > 0.5 ? 1 : -1;
          }

          const targetLink = curvedLinks[pearl.linkIndex % curvedLinks.length];
          if (targetLink) {
            const t = pearl.direction === 1 ? pearl.progress : 1.0 - pearl.progress;
            const currentPos = targetLink.curve.getPoint(t);
            pearl.mesh.position.copy(currentPos);
          }
        });
      }

      renderer.render(scene, camera);
    };

    animate();

    // 13. Fenstergrößenänderung abfangen
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      glowTexture.dispose();
      starGeo.dispose();
      starMat.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      pearlGeo.dispose();
      pearlMat.dispose();
    };
  }, [data]);

  // Interaktionen: Drag-Orbit, Zoom & Raycasting
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      isDraggingRef.current = true;
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDraggingRef.current) {
      const deltaX = e.clientX - previousMousePositionRef.current.x;
      const deltaY = e.clientY - previousMousePositionRef.current.y;

      cameraRotationRef.current.theta -= deltaX * 0.006;
      if (!is2DRef.current) {
        cameraRotationRef.current.phi = Math.max(0.1, Math.min(Math.PI - 0.1, cameraRotationRef.current.phi + deltaY * 0.006));
      }
      updateCameraPosition();
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    } else {
      // Hover Raycasting
      if (!cameraRef.current || !containerRef.current || !constellationGroupRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const mouse = new THREE.Vector2(
        ((e.clientX - rect.left) / rect.width) * 2 - 1,
        -((e.clientY - rect.top) / rect.height) * 2 + 1
      );

      const raycaster = new THREE.Raycaster();
      raycaster.setFromCamera(mouse, cameraRef.current);
      const meshes = Array.from(nodeMeshesRef.current.values());
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const id = intersects[0].object.userData.id;
        const node = internalNodesRef.current.find((n) => n.id === id);
        if (node) {
          setHoveredNode({ node, x: e.clientX, y: e.clientY });
        }
      } else {
        setHoveredNode(null);
      }
    }
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  const handleWheel = (e: React.WheelEvent) => {
    cameraRotationRef.current.radius = Math.max(120, Math.min(1100, cameraRotationRef.current.radius + e.deltaY * 0.45));
    updateCameraPosition();
  };

  const handleClick = (e: React.MouseEvent) => {
    if (!cameraRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, cameraRef.current);
    const meshes = Array.from(nodeMeshesRef.current.values());
    const intersects = raycaster.intersectObjects(meshes);

    if (intersects.length > 0) {
      const id = intersects[0].object.userData.id;
      const clickedNode = internalNodesRef.current.find((n) => n.id === id);
      if (!clickedNode) return;

      if (e.shiftKey && selectedNodeRef.current && selectedNodeRef.current.id !== clickedNode.id) {
        // Shift + Klick: Kürzester Pfad (Dijkstra)
        const path = findShortestPath(selectedNodeRef.current.id, clickedNode.id);
        highlightedPathRef.current = new Set(path);
        if (onPathFound) onPathFound(path);
      } else {
        // Normaler Klick: Fokussieren & Isolieren
        selectedNodeRef.current = clickedNode;
        highlightedPathRef.current.clear();
        onNodeSelect(clickedNode);
      }
    } else {
      // Klick in den leeren Raum -> Deselektieren
      selectedNodeRef.current = null;
      highlightedPathRef.current.clear();
      onNodeSelect(null);
      setModalNode(null);
    }
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    if (!cameraRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, cameraRef.current);
    const meshes = Array.from(nodeMeshesRef.current.values());
    const intersects = raycaster.intersectObjects(meshes);

    if (intersects.length > 0) {
      const id = intersects[0].object.userData.id;
      const node = internalNodesRef.current.find((n) => n.id === id);
      if (node) {
        setModalNode({ node, x: e.clientX, y: e.clientY });
      }
    } else {
      setModalNode(null);
    }
  };

  const handleDoubleClick = (e: React.MouseEvent) => {
    if (!cameraRef.current || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const mouse = new THREE.Vector2(
      ((e.clientX - rect.left) / rect.width) * 2 - 1,
      -((e.clientY - rect.top) / rect.height) * 2 + 1
    );

    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(mouse, cameraRef.current);
    const meshes = Array.from(nodeMeshesRef.current.values());
    const intersects = raycaster.intersectObjects(meshes);

    if (intersects.length > 0) {
      const id = intersects[0].object.userData.id;
      const clickedNode = internalNodesRef.current.find((n) => n.id === id);
      if (clickedNode) {
        socketManager.executeNodeAction(clickedNode.id, clickedNode.path, clickedNode.category, "open");
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing overflow-hidden bg-[#080808]"
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      onContextMenu={handleContextMenu}
    >
      {/* Hover HUD Tooltip */}
      {hoveredNode && !modalNode && (
        <div
          className="absolute z-40 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-3 px-3 py-1.5 rounded-md bg-[#080808]/90 border border-[#1f242d] backdrop-blur-md text-xs shadow-2xl transition-all"
          style={{ left: hoveredNode.x, top: hoveredNode.y }}
        >
          <div className="flex items-center gap-2">
            <span
              className="w-2.5 h-2.5 rounded-full shadow-[0_0_8px_currentColor]"
              style={{
                backgroundColor: CATEGORY_COLORS[hoveredNode.node.category],
                color: CATEGORY_COLORS[hoveredNode.node.category]
              }}
            />
            <span className="font-semibold text-white tracking-wide">{hoveredNode.node.name}</span>
          </div>
          <div className="text-[10px] text-gray-400 mt-0.5 font-mono">
            {hoveredNode.node.category.toUpperCase()} · {hoveredNode.node.connections} CONNECTIONS
          </div>
        </div>
      )}

      {/* Rechtsklick Flyout Inspector Modal mit interaktiven Cockpit-Aktionen */}
      {modalNode && (
        <div
          className="absolute z-50 w-80 rounded-lg bg-[#080808]/95 border border-[#00f0ff]/40 backdrop-blur-xl p-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150"
          style={{
            left: Math.min(modalNode.x, window.innerWidth - 330),
            top: Math.min(modalNode.y, window.innerHeight - 290)
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-start justify-between border-b border-[#1f242d] pb-2 mb-2">
            <div>
              <h3 className="font-bold text-sm text-white flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full inline-block shadow-[0_0_8px_currentColor]"
                  style={{
                    backgroundColor: CATEGORY_COLORS[modalNode.node.category],
                    color: CATEGORY_COLORS[modalNode.node.category]
                  }}
                />
                {modalNode.node.name}
              </h3>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-[10px] uppercase tracking-wider text-[#00f0ff] font-mono">
                  {modalNode.node.category} · {modalNode.node.connections} CONNECTIONS
                </span>
              </div>
            </div>
            <button
              onClick={() => setModalNode(null)}
              className="text-gray-400 hover:text-white text-xs px-1.5 py-0.5 rounded border border-transparent hover:border-[#1f242d]"
            >
              ✕
            </button>
          </div>

          {modalNode.node.path && (
            <div className="mb-2 px-2 py-1 rounded bg-[#161b22] border border-[#1f242d] text-[10px] font-mono text-cyan-300 truncate">
              <span className="text-gray-400">PFAD: </span>{modalNode.node.path}
            </div>
          )}

          <p className="text-xs text-gray-300 leading-relaxed font-sans mb-3">
            {modalNode.node.description}
          </p>

          <div className="pt-2 border-t border-[#1f242d]/60 flex flex-col gap-1.5">
            <div className="grid grid-cols-2 gap-1.5">
              <button
                onClick={() => {
                  socketManager.executeNodeAction(modalNode.node.id, modalNode.node.path, modalNode.node.category, "open");
                  setModalNode(null);
                }}
                className="px-2 py-1.5 text-[11px] font-mono rounded bg-[#00f0ff]/15 hover:bg-[#00f0ff]/30 text-[#00f0ff] border border-[#00f0ff]/40 transition-colors flex items-center justify-center gap-1 font-semibold"
                title="Im Standard-Editor oder Anwendungsstarter öffnen"
              >
                <span>Öffnen</span>
              </button>

              <button
                onClick={() => {
                  socketManager.executeNodeAction(modalNode.node.id, modalNode.node.path, modalNode.node.category, "terminal");
                  setModalNode(null);
                }}
                className="px-2 py-1.5 text-[11px] font-mono rounded bg-[#2979ff]/15 hover:bg-[#2979ff]/30 text-[#2979ff] border border-[#2979ff]/40 transition-colors flex items-center justify-center gap-1 font-semibold"
                title="Im Terminal (Konsole) am Pfad starten"
              >
                <span>Im Terminal</span>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-1.5">
              <button
                onClick={() => {
                  socketManager.executeNodeAction(modalNode.node.id, modalNode.node.path, modalNode.node.category, "summarize");
                  setModalNode(null);
                }}
                className="px-2 py-1.5 text-[11px] font-mono rounded bg-[#ff9100]/15 hover:bg-[#ff9100]/30 text-[#ff9100] border border-[#ff9100]/40 transition-colors flex items-center justify-center gap-1 font-semibold"
                title="Zusammenfassung durch Gemini anfordern"
              >
                <span>Zusammenfassen</span>
              </button>

              <button
                onClick={() => {
                  socketManager.deleteNode(modalNode.node.id);
                  setModalNode(null);
                }}
                className="px-2 py-1.5 text-[11px] font-mono rounded bg-red-500/15 hover:bg-red-500/30 text-red-400 border border-red-500/40 transition-colors flex items-center justify-center gap-1 font-semibold"
                title="Knoten aus Graph löschen (mit Undo-Schutz)"
              >
                <span>Löschen</span>
              </button>
            </div>

            <button
              onClick={() => {
                selectedNodeRef.current = modalNode.node;
                onNodeSelect(modalNode.node);
                setModalNode(null);
              }}
              className="mt-0.5 w-full py-1 text-[11px] font-mono rounded bg-white/5 hover:bg-white/10 text-gray-300 border border-white/15 transition-colors text-center"
            >
              Fokussieren & Isolieren
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

ApexWorld.displayName = "ApexWorld";
