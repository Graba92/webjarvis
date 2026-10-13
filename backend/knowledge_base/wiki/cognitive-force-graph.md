---
title: "The Cognitive Force-Directed Graph Architektur"
updated: "2026-10-13 02:30:00"
tags: ["Architecture", "UI/UX", "PKM", "KnowledgeGraph", "WebGL", "Three.js"]
category: "Wiki"
connections: 45
wiki_links_count: 5
---

# [ARCHITEKTUR-DOKUMENT]: The Cognitive Force-Directed Graph
**Status:** Produktionsbereit (WebJarvis / React / Next.js / Three.js)  
**Ziel:** Transformation eines chaotischen "Haarballs" in ein semantisch geordnetes, visuell ruhiges Knowledge-Netzwerk.  
**Federführung:** Cognitive UI/UX & Second Brain Architect  

---

## 1. KERNPRINZIPIEN (Das "Warum" & "Wie")

Ein Force-Directed Graph ist keine statische Zeichnung, sondern eine physikalische Simulation. Das System ordnet sich durch ein ständiges Tauziehen zwischen zwei gegensätzlichen Kräften von selbst:

*   **Elektromagnetische Abstoßung (Charge/Repel):** Jeder Knoten stößt jeden anderen Knoten ab. Große Knoten (Hubs) haben eine massiv höhere Abstoßungskraft als kleine (`hubWeight = 2.2x`, Reichweite bis 280 Einheiten). Das verhindert Verklumpungen und zwingt Hauptkategorien dazu, sich gleichmäßig im Raum zu verteilen.
*   **Gravitation der Verbindungen (Link Distance):** Kanten (Links) wirken wie Sprungfedern. Sie ziehen verknüpfte Knoten wieder zusammen. Die Länge dieser Federn wird dynamisch berechnet: Blätter (Leaf-Nodes) werden extrem nah an ihren Hub gezogen (`springDist = 28-45`, `stiffness = 0.12`), während Verbindungen zwischen zwei großen Hubs lang bleiben (`springDist = 95`).

**Das Resultat:** Häufig verlinkte Themen (Hubs) rücken ins Zentrum und bilden "Sonnensysteme". Isolierte oder seltene Notizen driften als kleine Satelliten an den Rand. Muster und blinde Flecken werden sofort organisch sichtbar.

---

## 2. UX- & UI-REGELN (Cognitive Load Reduction)

Damit das Gehirn die Struktur lesen kann, ohne zu ermüden, gelten eiserne Rendering-Gesetze:

1.  **Semantic Zooming (Detail on Demand):** Das menschliche Auge kann maximal 5–7 Informationseinheiten gleichzeitig verarbeiten. Herausgezoomt (`cameraDist > 480`) dürfen NUR die Orbit-Ringe, Hubs und Alerts (Konflikte, Orphans) gerendert werden. Alles andere ist nur Farbe und Größe. Text-Labels von kleinen Nodes existieren erst, wenn der User tief hineinzoomt (`cameraDist <= 480`).
2.  **Focus Fading (Der Tunnelblick-Modus):** Klickt der User einen Knoten an, muss der gesamte restliche Graph (Nodes und Kanten, die nicht direkt verknüpft sind) auf 5% bis 10% Deckkraft gedimmt werden (`uAlpha = 0.10`). Keine kreuzenden Linien dürfen den Blick auf den fokussierten Pfad stören (Restglanz auf 1.5% gedimmt).
3.  **Label-Kollisions-Schutz (Pills):** Text-Labels dürfen niemals von Graphen-Kanten durchschnitten werden. Jedes Label braucht einen eigenen, leicht transparenten Hintergrund (Pill/Badge in `rgba(7, 12, 24, 0.94)`), der den Text aus dem Linien-Chaos ausstanzt.
4.  **Directional Flow (Gradienten):** Datenfluss oder semantische Richtungen (Parent zu Child) werden nicht durch plumpe Pfeile dargestellt (die bei hunderten Links das Bild zumüllen), sondern durch sanfte Farbverläufe in der Kante (Source-Color zu Target-Color) oder dezente, animierte Partikel (Photons) im Fokus-Modus.

---

## 3. TECHNISCHE ANMERKUNGEN (Implementation & Tuning)

*   **Canvas vs. SVG/HTML:** Bei über 200 Nodes und 250+ Connections ist DOM-basiertes Rendering (SVG/HTML-Divs) tot. Die Engine MUSS über das HTML5 `<canvas>`-Element via WebGL (Three.js / React) rendern. In WebJarvis operiert hierfür die dedizierte High-Performance-Komponente `ApexWorld.tsx`.
*   **Engine Abkühlung (Decay):** Ein klassischer Fehler ist es, die Simulation ewig wackeln zu lassen. Die Settle-on-Equilibrium Physik kühlt nach 90 Iterationen (`cooling = 0.965`) kontrolliert ab und friert den Graphen ein. Das spart CPU/GPU und beruhigt das Auge.

---

## 4. SYSTEM-INTEGRATION & WIKI-VERNETZUNG

- [[sentinel-architektur]]: Inter-Agenten IPC-Watchdog ohne Fake-Execution.
- [[god-mode-tui]]: 8-Panel TUI Cockpit mit verifiziertem UDS-Live-Check.
- [[uds-ipc-protokoll]]: Zero-Overhead Unix Domain Socket IPC (`/run/user/1000/friday_ipc.sock`).
- [[second-brain-fts5]]: Volltext-Wissensindexierung der 2.716 Units.
- [[system-topologie]]: Gesamttopologie von Operator, AGY und FRIDAY.
