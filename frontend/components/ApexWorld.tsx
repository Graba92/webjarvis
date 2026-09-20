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
  isHub: boolean;
  group?: THREE.Group;
  shaderMat?: THREE.ShaderMaterial;
  nucleusMesh?: THREE.Mesh;
  ringMesh?: THREE.Mesh;
  billboardSprite?: THREE.Sprite;
  hitMesh?: THREE.Mesh;
}

interface DataPacket {
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

// ─────────────────────────────────────────────────────────────────────────────
// 1. VOLUMETRISCHE FRESNEL SHADER (Aus preview_graph.py)
// ─────────────────────────────────────────────────────────────────────────────
const fresnelVertexShader = `
  varying vec3 vNormal;
  varying vec3 vViewPosition;

  void main() {
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    vNormal = normalize(normalMatrix * normal);
    vViewPosition = -mvPosition.xyz;
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const fresnelFragmentShader = `
  uniform vec3 uColor;
  uniform float uTime;
  uniform float uPulseRate;
  uniform float uGlowIntensity;
  uniform float uAlpha;
  varying vec3 vNormal;
  varying vec3 vViewPosition;

  void main() {
    vec3 normal = normalize(vNormal);
    vec3 viewDir = normalize(vViewPosition);
    float dotNV = max(dot(normal, viewDir), 0.0);
    float fresnel = pow(1.0 - dotNV, 2.3);
    float pulse = 0.5 + 0.5 * sin(uTime * uPulseRate);
    
    vec3 coreColor = uColor * 0.42;
    vec3 rimGlow = uColor * (fresnel * (2.2 + 1.2 * pulse) * uGlowIntensity);
    vec3 finalColor = coreColor + rimGlow;
    float alpha = clamp((0.35 + fresnel * 0.65) * uAlpha, 0.0, 0.98);
    
    gl_FragColor = vec4(finalColor, alpha);
  }
`;

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
    gradient.addColorStop(0.25, "rgba(255, 255, 255, 0.85)");
    gradient.addColorStop(0.5, "rgba(255, 255, 255, 0.35)");
    gradient.addColorStop(0.75, "rgba(255, 255, 255, 0.08)");
    gradient.addColorStop(1.0, "rgba(255, 255, 255, 0.0)");
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, 128, 128);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

/**
 * 3D-Billboard Text-Sprite Creator mit Sci-Fi Eck-Brackets (aus preview_graph.py)
 */
function createTextSprite(mainText: string, subText: string, colorHex: string): THREE.Sprite {
  const cvs = document.createElement("canvas");
  cvs.width = 512;
  cvs.height = 128;
  const ctx = cvs.getContext("2d");

  if (ctx) {
    ctx.fillStyle = "rgba(8, 12, 22, 0.82)";
    ctx.strokeStyle = colorHex;
    ctx.lineWidth = 3;
    ctx.strokeRect(10, 10, 492, 108);
    ctx.fillRect(10, 10, 492, 108);

    // Eck-Brackets im Cyberpunk-HUD-Stil
    ctx.fillStyle = colorHex;
    ctx.fillRect(10, 10, 14, 14);
    ctx.fillRect(488, 10, 14, 14);
    ctx.fillRect(10, 104, 14, 14);
    ctx.fillRect(488, 104, 14, 14);

    // Haupttext (Node-Name)
    ctx.font = "bold 32px 'Share Tech Mono', monospace";
    ctx.fillStyle = "#ffffff";
    ctx.textAlign = "center";
    ctx.shadowColor = colorHex;
    ctx.shadowBlur = 12;
    ctx.fillText(mainText.toUpperCase(), 256, 56);

    // Subtext (Kategorie // Verbindungen)
    ctx.font = "bold 18px 'Share Tech Mono', monospace";
    ctx.fillStyle = colorHex;
    ctx.shadowBlur = 6;
    ctx.fillText(subText, 256, 96);
  }

  const texture = new THREE.CanvasTexture(cvs);
  texture.needsUpdate = true;
  const spriteMat = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    blending: THREE.AdditiveBlending,
    depthTest: false
  });
  const sprite = new THREE.Sprite(spriteMat);
  sprite.scale.set(15, 3.75, 1);
  return sprite;
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
  const internalNodesRef = useRef<InternalNode[]>([]);
  const curvedLinksRef = useRef<CurvedLink[]>([]);
  const packetsRef = useRef<DataPacket[]>([]);
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
    radius: 450
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
      cameraRotationRef.current = { theta: Math.PI / 4.2, phi: Math.PI / 2.8, radius: 450 };
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

    // 1. Scene & Sci-Fi Background (#06080d)
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x06080d);
    scene.fog = new THREE.FogExp2(0x06080d, 0.0012);
    sceneRef.current = scene;

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(50, width / height, 1, 4000);
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
    renderer.setClearColor(0x06080d, 1);
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Beleuchtung
    const ambLight = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambLight);

    const pointCyan = new THREE.PointLight(0x00f0ff, 2.5, 1000);
    pointCyan.position.set(220, 240, 200);
    scene.add(pointCyan);

    const pointBlue = new THREE.PointLight(0x2979ff, 2.0, 1000);
    pointBlue.position.set(-220, 180, -220);
    scene.add(pointBlue);

    const pointEmerald = new THREE.PointLight(0x00ff88, 1.8, 1000);
    pointEmerald.position.set(0, -240, 180);
    scene.add(pointEmerald);

    // 5. Konzentrische holografische Radar-Ringe & Boden-Gitter (aus preview_graph.py)
    const radarGroup = new THREE.Group();
    radarGroup.position.y = -135;

    const groundGrid = new THREE.GridHelper(380, 38, 0x00f0ff, 0x0a1e36);
    const gridMat = groundGrid.material as THREE.Material;
    gridMat.transparent = true;
    gridMat.opacity = 0.22;
    radarGroup.add(groundGrid);

    const radarRadii = [40, 85, 140, 210, 290];
    const radarGeos: THREE.RingGeometry[] = [];
    const radarMats: THREE.MeshBasicMaterial[] = [];
    radarRadii.forEach((r, idx) => {
      const ringGeo = new THREE.RingGeometry(r - 0.6, r + 0.6, 64);
      radarGeos.push(ringGeo);
      const ringMat = new THREE.MeshBasicMaterial({
        color: idx % 2 === 0 ? 0x00f0ff : 0x00ff88,
        transparent: true,
        opacity: 0.16,
        side: THREE.DoubleSide,
        blending: THREE.AdditiveBlending
      });
      radarMats.push(ringMat);
      const ringMesh = new THREE.Mesh(ringGeo, ringMat);
      ringMesh.rotation.x = Math.PI / 2;
      radarGroup.add(ringMesh);
    });
    scene.add(radarGroup);

    // 6. Schwebende Datenpartikel / Digitaler Raumstaub (750 Partikel)
    const particleCount = 750;
    const particleGeo = new THREE.BufferGeometry();
    const particlePositions = new Float32Array(particleCount * 3);
    const particleColors = new Float32Array(particleCount * 3);
    const pColor1 = new THREE.Color(0x00f0ff);
    const pColor2 = new THREE.Color(0x00ff88);

    for (let i = 0; i < particleCount; i++) {
      particlePositions[i * 3 + 0] = (Math.random() - 0.5) * 380;
      particlePositions[i * 3 + 1] = (Math.random() - 0.5) * 220;
      particlePositions[i * 3 + 2] = (Math.random() - 0.5) * 380;
      const c = Math.random() > 0.45 ? pColor1 : pColor2;
      particleColors[i * 3 + 0] = c.r;
      particleColors[i * 3 + 1] = c.g;
      particleColors[i * 3 + 2] = c.b;
    }
    particleGeo.setAttribute("position", new THREE.BufferAttribute(particlePositions, 3));
    particleGeo.setAttribute("color", new THREE.BufferAttribute(particleColors, 3));
    const particleMat = new THREE.PointsMaterial({
      size: 1.6,
      vertexColors: true,
      transparent: true,
      opacity: 0.55,
      blending: THREE.AdditiveBlending
    });
    const particleSystem = new THREE.Points(particleGeo, particleMat);
    scene.add(particleSystem);

    // 7. Haupt-Constellation-Gruppe für globalen 3D-Drift
    const constellationGroup = new THREE.Group();
    scene.add(constellationGroup);
    constellationGroupRef.current = constellationGroup;

    // 8. Cluster-Zentren für dynamische räumliche Kohärenz
    const clusterCenters: Record<string, THREE.Vector3> = {
      Cyan: new THREE.Vector3(120, 30, 40),
      Blue: new THREE.Vector3(-95, 70, -60),
      Orange: new THREE.Vector3(-25, -80, 70)
    };

    const getGroupKey = (cat: NodeCategory): "Cyan" | "Blue" | "Orange" => {
      if (cat === "Router" || cat === "Skills" || cat === "Tools") return "Cyan";
      if (cat === "Suites" || cat === "Wiki" || cat === "Files") return "Blue";
      return "Orange";
    };

    // NUR ECHTE VORHANDENE KNOTEN (data.nodes) dynamisch abbilden!
    const internalNodes: InternalNode[] = data.nodes.map((node, i) => {
      const groupKey = getGroupKey(node.category);
      const center = clusterCenters[groupKey] || new THREE.Vector3(0, 0, 0);
      const isHub = node.id.startsWith("hub-") || node.connections >= 30;

      const angle = (i * 2.399963229728653) % (Math.PI * 2);
      const elevation = Math.sin(i * 1.7) * 0.75;
      const radius = isHub ? 36 + (i % 3) * 12 : 68 + (i % 5) * 16;

      const lx = radius * Math.cos(angle) * Math.cos(elevation);
      const ly = radius * Math.sin(elevation) * 1.2;
      const lz = radius * Math.sin(angle) * Math.cos(elevation);

      const baseX = isHub ? center.x * 0.55 + lx * 0.6 : center.x + lx;
      const baseY = isHub ? center.y * 0.55 + ly * 0.6 : center.y + ly;
      const baseZ = isHub ? center.z * 0.55 + lz * 0.6 : center.z + lz;

      const baseRadius = Math.max(3.8, Math.min(14.5, Math.sqrt(node.connections) * 2.15));

      return {
        ...node,
        baseX,
        baseY,
        baseZ,
        baseRadius,
        isHub,
        pulsePhase: i * 1.37 + Math.random() * 0.5,
        x: baseX,
        y: baseY,
        z: baseZ
      };
    });
    internalNodesRef.current = internalNodes;

    // 9. Glow-Textur für Partikel und Halos
    const glowTexture = createRadialGlowTexture();

    // 10. Node Builder: Volumetrische Fresnel Shader + Weißer Kern + Holo-Gyroskop-Ring + 3D-Billboard
    const meshesMap = new Map<string, THREE.Mesh>();
    const nodeGroups: THREE.Group[] = [];
    const sphereGeometry = new THREE.SphereGeometry(1, 32, 32);
    const nucleusGeometry = new THREE.SphereGeometry(1, 16, 16);
    const nucleusMaterial = new THREE.MeshBasicMaterial({ color: 0xffffff, blending: THREE.AdditiveBlending });

    internalNodes.forEach((node) => {
      const group = new THREE.Group();
      group.position.set(node.baseX, node.baseY, node.baseZ);

      const colorHex = CATEGORY_COLORS[node.category] || "#00f0ff";
      const colorObj = new THREE.Color(colorHex);

      // A. Volumetrische Fresnel-Shader-Sphäre
      const shaderMat = new THREE.ShaderMaterial({
        vertexShader: fresnelVertexShader,
        fragmentShader: fresnelFragmentShader,
        uniforms: {
          uColor: { value: colorObj },
          uTime: { value: 0 },
          uPulseRate: { value: 2.2 + (node.connections % 4) * 0.5 },
          uGlowIntensity: { value: node.isHub ? 1.5 : 1.1 },
          uAlpha: { value: 1.0 }
        },
        transparent: true,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });

      const sphereMesh = new THREE.Mesh(sphereGeometry, shaderMat);
      sphereMesh.scale.setScalar(node.baseRadius);
      group.add(sphereMesh);

      // B. Innerer leuchtender Energiekern (Nucleus)
      const nucleusMesh = new THREE.Mesh(nucleusGeometry, nucleusMaterial);
      nucleusMesh.scale.setScalar(node.baseRadius * 0.38);
      group.add(nucleusMesh);

      // C. Rotierender Holo-Gyroskop-Ring (für Hubs / hochvernetzte Knoten)
      let ringMesh: THREE.Mesh | undefined;
      if (node.isHub) {
        const ringGeo = new THREE.TorusGeometry(node.baseRadius * 1.38, 0.16, 8, 48);
        const ringMat = new THREE.MeshBasicMaterial({
          color: colorObj,
          wireframe: true,
          blending: THREE.AdditiveBlending,
          transparent: true,
          opacity: 0.8
        });
        ringMesh = new THREE.Mesh(ringGeo, ringMat);
        ringMesh.rotation.x = Math.PI / 3.2;
        group.add(ringMesh);
      }

      // D. 3D-Billboard Text-Sprite mit HUD Eck-Brackets für Hubs & Major Nodes
      let billboardSprite: THREE.Sprite | undefined;
      if (node.isHub) {
        const subLabel = `[ ${node.category.toUpperCase()} // ${node.connections} LINKS ]`;
        billboardSprite = createTextSprite(node.name, subLabel, colorHex);
        billboardSprite.position.y = node.baseRadius + 4.2;
        group.add(billboardSprite);
      }

      // E. Unsichtbare Hit-Sphere für pixelgenaues Raycasting
      const hitGeo = new THREE.SphereGeometry(node.baseRadius * 1.4, 16, 16);
      const hitMat = new THREE.MeshBasicMaterial({ visible: false });
      const hitMesh = new THREE.Mesh(hitGeo, hitMat);
      hitMesh.userData = { id: node.id };
      group.add(hitMesh);

      constellationGroup.add(group);
      nodeGroups.push(group);
      meshesMap.set(node.id, hitMesh);

      node.group = group;
      node.shaderMat = shaderMat;
      node.nucleusMesh = nucleusMesh;
      node.ringMesh = ringMesh;
      node.billboardSprite = billboardSprite;
      node.hitMesh = hitMesh;
    });
    nodeMeshesRef.current = meshesMap;

    // 11. Geschwungene Leuchtlinien (3D Bézier-Kurven) für reale Verbindungen (data.links)
    const curvedLinks: CurvedLink[] = [];
    const segmentsPerCurve = 24;
    const totalLineVertices = data.links.length * segmentsPerCurve * 2;
    const linePos = new Float32Array(totalLineVertices * 3);
    const lineColors = new Float32Array(totalLineVertices * 3);

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

        let normal = mid.clone().normalize();
        if (normal.lengthSq() < 0.001) normal = new THREE.Vector3(0, 1, 0);

        const side = new THREE.Vector3().crossVectors(delta, normal).normalize();
        const elevation = Math.min(dist * 0.18, 16);
        const ctrl = mid.clone().add(side.multiplyScalar(elevation * 0.45)).add(normal.multiplyScalar(elevation * 0.55));

        const curve = new THREE.QuadraticBezierCurve3(p1, ctrl, p2);
        curvedLinks.push({ sourceId: sId, targetId: tId, curve });

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

    // Neon-Farbe für Linien: Leuchtendes Cyan / Türkis mit hoher Leuchtkraft
    const baseLineColor = new THREE.Color(0x00f0ff);
    for (let c = 0; c < lineColors.length; c += 3) {
      lineColors[c] = baseLineColor.r * 0.85;
      lineColors[c + 1] = baseLineColor.g * 0.95;
      lineColors[c + 2] = baseLineColor.b;
    }

    const lineGeo = new THREE.BufferGeometry();
    lineGeo.setAttribute("position", new THREE.BufferAttribute(linePos, 3));
    lineGeo.setAttribute("color", new THREE.BufferAttribute(lineColors, 3));

    const lineMat = new THREE.LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.55,
      blending: THREE.AdditiveBlending
    });
    const linkLinesSegments = new THREE.LineSegments(lineGeo, lineMat);
    constellationGroup.add(linkLinesSegments);

    // 12. Animierte Datenfluss-Partikel / Flux-Pulse ("wie es arbeitet")
    const packetPoolSize = Math.min(72, Math.max(24, curvedLinks.length * 2));
    const packets: DataPacket[] = [];
    const packetGeo = new THREE.SphereGeometry(1.35, 12, 12);
    const flowColorHexes = [0x00f0ff, 0x00ff88, 0x2979ff, 0x00e5ff, 0x50d7ff];
    const packetMaterials: THREE.MeshBasicMaterial[] = [];
    const packetHaloMaterials: THREE.SpriteMaterial[] = [];

    for (let p = 0; p < packetPoolSize; p++) {
      const pColorHex = flowColorHexes[p % flowColorHexes.length];
      const pColor = new THREE.Color(pColorHex);
      const pMeshMat = new THREE.MeshBasicMaterial({
        color: pColor,
        transparent: true,
        opacity: 0.95,
        blending: THREE.AdditiveBlending
      });
      packetMaterials.push(pMeshMat);
      const pMesh = new THREE.Mesh(packetGeo, pMeshMat);

      const pHaloMat = new THREE.SpriteMaterial({
        map: glowTexture,
        color: pColor,
        transparent: true,
        opacity: 0.85,
        blending: THREE.AdditiveBlending,
        depthWrite: false
      });
      packetHaloMaterials.push(pHaloMat);
      const pHalo = new THREE.Sprite(pHaloMat);
      pHalo.scale.set(7.5, 7.5, 1);
      pMesh.add(pHalo);

      const linkIdx = p % Math.max(1, curvedLinks.length);
      const packet: DataPacket = {
        mesh: pMesh,
        halo: pHalo,
        linkIndex: linkIdx,
        progress: Math.random(),
        speed: 0.28 + Math.random() * 0.35,
        direction: Math.random() > 0.5 ? 1 : -1
      };
      constellationGroup.add(pMesh);
      packets.push(packet);
    }
    packetsRef.current = packets;

    // 13. Render- & Animationsloop (60-120 FPS)
    let animationFrameId: number;
    let prevTime = performance.now();

    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);
      const now = performance.now();
      const delta = Math.min(0.1, (now - prevTime) / 1000);
      prevTime = now;
      const time = now * 0.001;

      // A. Global Movement: Harmonische 3D-Präzession
      const is2D = is2DRef.current;
      if (!is2D) {
        constellationGroup.rotation.y = Math.sin(time * 0.08) * 0.1 + time * 0.02;
        constellationGroup.rotation.x = Math.sin(time * 0.06) * 0.05;
        constellationGroup.rotation.z = Math.cos(time * 0.04) * 0.04;

        constellationGroup.position.x = Math.sin(time * 0.12) * 8;
        constellationGroup.position.y = Math.cos(time * 0.15) * 10;
        constellationGroup.position.z = Math.sin(time * 0.09) * 6;

        radarGroup.rotation.y += 0.0006;
      } else {
        constellationGroup.rotation.set(0, 0, 0);
        constellationGroup.position.set(0, 0, 0);
      }

      // Schwebenden Datenstaub sanft rotieren
      particleSystem.rotation.y = time * 0.015;

      // B. Slider-Skalierung
      const scaleFactor = (linkLengthRef.current / 80) * (repelForceRef.current / 140);
      const query = searchQueryRef.current.trim().toLowerCase();
      const filter = activeFilterRef.current;
      const selected = selectedNodeRef.current;
      const pathSet = highlightedPathRef.current;

      // C. Node Shaders, Gyroskop-Ringe & Pulsation updaten
      internalNodes.forEach((node) => {
        if (!node.group || !node.shaderMat) return;

        const px = node.baseX * scaleFactor;
        const py = node.baseY * scaleFactor;
        const pz = is2D ? 0 : node.baseZ * scaleFactor;
        node.group.position.set(px, py, pz);
        node.x = px;
        node.y = py;
        node.z = pz;

        // Gyroskop-Ring rotieren
        if (node.ringMesh) {
          node.ringMesh.rotation.z += 0.012;
          node.ringMesh.rotation.y += 0.008;
        }

        // Shader-Zeit übergeben
        node.shaderMat.uniforms.uTime.value = time;

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

        if (!isVisible) {
          node.shaderMat.uniforms.uAlpha.value = 0.04;
          node.shaderMat.uniforms.uGlowIntensity.value = 0.1;
          if (node.nucleusMesh) node.nucleusMesh.visible = false;
          if (node.ringMesh) node.ringMesh.visible = false;
          if (node.billboardSprite) node.billboardSprite.visible = false;
        } else if (selected) {
          if (isSelected || isOnPath || isNeighbor) {
            node.shaderMat.uniforms.uAlpha.value = 1.0;
            node.shaderMat.uniforms.uGlowIntensity.value = isSelected ? 2.5 : 1.8;
            if (node.nucleusMesh) node.nucleusMesh.visible = true;
            if (node.ringMesh) node.ringMesh.visible = true;
            if (node.billboardSprite) node.billboardSprite.visible = true;
          } else {
            node.shaderMat.uniforms.uAlpha.value = 0.12;
            node.shaderMat.uniforms.uGlowIntensity.value = 0.2;
            if (node.nucleusMesh) node.nucleusMesh.visible = false;
            if (node.ringMesh) node.ringMesh.visible = false;
            if (node.billboardSprite) node.billboardSprite.visible = false;
          }
        } else {
          node.shaderMat.uniforms.uAlpha.value = 0.95;
          node.shaderMat.uniforms.uGlowIntensity.value = node.isHub ? 1.5 : 1.1;
          if (node.nucleusMesh) node.nucleusMesh.visible = true;
          if (node.ringMesh) node.ringMesh.visible = true;
          if (node.billboardSprite) node.billboardSprite.visible = true;
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
        const elevation = Math.min(dist * 0.18, 16);
        const ctrl = mid.clone().add(side.multiplyScalar(elevation * 0.45)).add(normal.multiplyScalar(elevation * 0.55));
        if (is2D) ctrl.z = 0;

        cLink.curve.v0.copy(p1);
        cLink.curve.v1.copy(ctrl);
        cLink.curve.v2.copy(p2);

        const pts = cLink.curve.getPoints(segmentsPerCurve);

        const isPathLink = pathSet.has(n1.id) && pathSet.has(n2.id);
        const isSelectedLink = selected && (
          (selected.id === n1.id && filter.has(n2.category)) ||
          (selected.id === n2.id && filter.has(n1.category))
        );

        let r = 0.0, g = 0.94, b = 1.0; // Neon Cyan
        if (selected) {
          if (isPathLink || isSelectedLink) {
            r = 1.0; g = 1.0; b = 1.0; // Weiß glühend
          } else {
            r = 0.03; g = 0.1; b = 0.16; // Gedimmt
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

      // E. Live-Datenfluss ("wie es arbeitet"): Datenpakete fließen sichtbar über die Nervenbahnen
      const curState = assistantStateRef.current;
      const isWorking = curState === "THINKING" || curState === "SPEAKING" || curState === "LISTENING";
      const audioPulse = Math.min(2.5, (audioLevelRef.current || 0) * 4.0);
      const activityMultiplier = (isWorking ? 2.4 : 1.0) + audioPulse;

      if (curvedLinks.length > 0) {
        packets.forEach((packet) => {
          packet.progress += delta * packet.speed * activityMultiplier;
          if (packet.progress >= 1.0) {
            packet.progress = 0.0;
            if (selected) {
              const connectedIndices = curvedLinks
                .map((cl, idx) => (cl.sourceId === selected.id || cl.targetId === selected.id ? idx : -1))
                .filter((idx) => idx !== -1);
              if (connectedIndices.length > 0 && Math.random() > 0.3) {
                packet.linkIndex = connectedIndices[Math.floor(Math.random() * connectedIndices.length)];
              } else {
                packet.linkIndex = Math.floor(Math.random() * curvedLinks.length);
              }
            } else {
              packet.linkIndex = Math.floor(Math.random() * curvedLinks.length);
            }
            packet.direction = Math.random() > 0.5 ? 1 : -1;
          }

          const targetLink = curvedLinks[packet.linkIndex % curvedLinks.length];
          if (targetLink) {
            const t = packet.direction === 1 ? packet.progress : 1.0 - packet.progress;
            const currentPos = targetLink.curve.getPoint(t);
            packet.mesh.position.copy(currentPos);

            // Halo pulsiert mit Audio/Status
            const haloScale = 7.5 * (1.0 + (isWorking ? 0.35 : 0.0) + audioPulse * 0.2);
            packet.halo.scale.set(haloScale, haloScale, 1);
          }
        });
      }

      renderer.render(scene, camera);
    };

    animate();

    // 14. Resize Handler
    const handleResize = () => {
      if (!containerRef.current || !rendererRef.current || !cameraRef.current) return;
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      cameraRef.current.aspect = w / h;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(w, h);
    };
    window.addEventListener("resize", handleResize);

    // 15. Sauberes Cleanup
    return () => {
      cancelAnimationFrame(animationFrameId);
      window.removeEventListener("resize", handleResize);
      renderer.dispose();
      glowTexture.dispose();
      sphereGeometry.dispose();
      nucleusGeometry.dispose();
      nucleusMaterial.dispose();
      radarGeos.forEach((g) => g.dispose());
      radarMats.forEach((m) => m.dispose());
      groundGrid.geometry.dispose();
      gridMat.dispose();
      particleGeo.dispose();
      particleMat.dispose();
      lineGeo.dispose();
      lineMat.dispose();
      packetGeo.dispose();
      packetMaterials.forEach((m) => m.dispose());
      packetHaloMaterials.forEach((m) => m.dispose());
      internalNodes.forEach((node) => {
        if (node.shaderMat) node.shaderMat.dispose();
        if (node.ringMesh) {
          node.ringMesh.geometry.dispose();
          (node.ringMesh.material as THREE.Material).dispose();
        }
        if (node.billboardSprite) {
          if (node.billboardSprite.material.map) node.billboardSprite.material.map.dispose();
          node.billboardSprite.material.dispose();
        }
        if (node.hitMesh) {
          node.hitMesh.geometry.dispose();
          (node.hitMesh.material as THREE.Material).dispose();
        }
      });
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
      className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing overflow-hidden bg-[#06080d]"
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
          className="absolute z-40 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-3 px-3 py-1.5 rounded-md bg-[#080d1a]/95 border border-[#00f0ff]/40 backdrop-blur-md text-xs shadow-2xl transition-all"
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
          <div className="text-[10px] text-cyan-300 mt-0.5 font-mono">
            {hoveredNode.node.category.toUpperCase()} · {hoveredNode.node.connections} CONNECTIONS
          </div>
        </div>
      )}

      {/* Rechtsklick Flyout Inspector Modal mit interaktiven Cockpit-Aktionen */}
      {modalNode && (
        <div
          className="absolute z-50 w-80 rounded-lg bg-[#060c18]/95 border border-[#00f0ff]/50 backdrop-blur-xl p-4 shadow-2xl animate-in fade-in zoom-in-95 duration-150"
          style={{
            left: Math.min(modalNode.x, window.innerWidth - 330),
            top: Math.min(modalNode.y, window.innerHeight - 290)
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-start justify-between border-b border-[#1f2d40] pb-2 mb-2">
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
              className="text-gray-400 hover:text-white text-xs px-1.5 py-0.5 rounded border border-transparent hover:border-[#1f2d40]"
            >
              ✕
            </button>
          </div>

          {modalNode.node.path && (
            <div className="mb-2 px-2 py-1 rounded bg-[#0b1424] border border-[#1f2d40] text-[10px] font-mono text-cyan-300 truncate">
              <span className="text-gray-400">PFAD: </span>{modalNode.node.path}
            </div>
          )}

          <p className="text-xs text-gray-300 leading-relaxed font-sans mb-3">
            {modalNode.node.description}
          </p>

          <div className="pt-2 border-t border-[#1f2d40]/60 flex flex-col gap-1.5">
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
