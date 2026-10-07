"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { X, Edit3, Save, Eye, AlertTriangle, Link2, BookOpen, Check, FileText } from "lucide-react";
import { GraphNode, WikiArticle } from "../lib/types";
import { socketManager } from "../lib/websocket";

interface WikiInspectorModalProps {
  node: GraphNode | null;
  onClose: () => void;
  onNavigateToNode?: (nodeIdOrTitle: string) => void;
}

export default function WikiInspectorModal({
  node,
  onClose,
  onNavigateToNode
}: WikiInspectorModalProps) {
  const [article, setArticle] = useState<WikiArticle | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [editContent, setEditContent] = useState<string>("");
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveSuccess, setSaveSuccess] = useState<boolean>(false);

  // Dirty State Tracker
  const isDirty = useMemo(() => {
    if (!article) return false;
    return editContent !== (article.content || "");
  }, [article, editContent]);

  // Artikel bei Node-Wechsel vom Backend laden
  useEffect(() => {
    if (!node) return;
    setIsLoading(true);
    setIsEditing(false);
    setSaveSuccess(false);

    // Initialen Request senden
    socketManager.getWikiArticle(node.name || node.id, node.path);

    const unsubArticle = socketManager.onWikiArticle((data) => {
      setArticle(data);
      setEditContent(data.content || "");
      setIsLoading(false);
    });

    const unsubSaved = socketManager.onWikiSaved((res) => {
      setIsSaving(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
      setIsEditing(false);
      // Neu laden
      socketManager.getWikiArticle(node.name || node.id, node.path);
    });

    return () => {
      unsubArticle();
      unsubSaved();
    };
  }, [node]);

  // Tastatur-Shortcuts (Ctrl+S zum Speichern, Esc zum Schließen)
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (isDirty) {
          if (confirm("Ungespeicherte Änderungen verwerfen?")) {
            onClose();
          }
        } else {
          onClose();
        }
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "s") {
        e.preventDefault();
        if (isEditing && isDirty) {
          handleSave();
        }
      }
    },
    [isDirty, isEditing, onClose]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  const handleSave = () => {
    if (!node) return;
    setIsSaving(true);
    const tags = article?.metadata?.tags || [];
    socketManager.saveWikiArticle(node.name, editContent, Array.isArray(tags) ? tags : []);
  };

  if (!node) return null;

  const isOrphan = !!(node.is_orphan || node.connections === 0 || node.status === "orphan");
  const hasConflict = !!(article?.has_conflict || node.status === "conflict");

  // Formatierter Parser für Markdown & [[Wiki-Links]]
  const renderFormattedContent = (text: string) => {
    if (!text) return null;

    const lines = text.split("\n");
    return (
      <div className="space-y-3 font-sans text-sm leading-relaxed text-slate-200">
        {lines.map((line, idx) => {
          // Frontmatter überspringen
          if (line.startsWith("---") || line.startsWith("title:") || line.startsWith("updated:") || line.startsWith("wiki_links_count:")) {
            return null;
          }

          // Konflikt-Alert
          if (line.startsWith("> [!WARNING]")) {
            return (
              <div
                key={idx}
                className="my-3 flex items-start gap-3 rounded-xl border border-red-500/50 bg-red-950/30 p-3.5 text-red-200 shadow-lg backdrop-blur-md"
              >
                <AlertTriangle className="h-5 w-5 shrink-0 text-red-400 animate-pulse mt-0.5" />
                <div className="font-semibold text-xs tracking-wide uppercase text-red-300">
                  {line.replace("> [!WARNING]", "").trim() || "Widerspruch im Wissensbestand erkannt"}
                </div>
              </div>
            );
          }
          if (line.startsWith(">")) {
            return (
              <blockquote
                key={idx}
                className="border-l-2 border-red-500/60 pl-3.5 py-0.5 text-xs text-red-300/90 font-mono bg-red-950/10 rounded-r"
              >
                {line.replace(/^>\s*/, "")}
              </blockquote>
            );
          }

          // Überschriften
          if (line.startsWith("# ")) {
            return (
              <h1 key={idx} className="text-xl font-bold text-cyan-300 tracking-wide pt-2 border-b border-cyan-500/20 pb-1">
                {line.replace("# ", "")}
              </h1>
            );
          }
          if (line.startsWith("## ")) {
            return (
              <h2 key={idx} className="text-base font-semibold text-cyan-200 tracking-wide pt-2">
                {line.replace("## ", "")}
              </h2>
            );
          }
          if (line.startsWith("### ")) {
            return (
              <h3 key={idx} className="text-sm font-semibold text-cyan-100/90 tracking-wide pt-1">
                {line.replace("### ", "")}
              </h3>
            );
          }

          // Listenpunkte
          if (line.startsWith("- ") || line.startsWith("• ")) {
            const rawItem = line.replace(/^[-•]\s*/, "");
            return (
              <li key={idx} className="ml-4 list-disc text-slate-300">
                {parseWikiLinks(rawItem)}
              </li>
            );
          }

          // Leere Zeile
          if (!line.trim()) return <div key={idx} className="h-1.5" />;

          // Regulärer Absatz mit [[Wiki-Links]]
          return <p key={idx}>{parseWikiLinks(line)}</p>;
        })}
      </div>
    );
  };

  // Erkennt [[Wiki-Links]] und macht sie zu anklickbaren Navigations-Pills
  const parseWikiLinks = (str: string) => {
    const parts = str.split(/(\[\[.*?\]\])/g);
    return parts.map((part, pIdx) => {
      const match = part.match(/^\[\[(.*?)\]\]$/);
      if (match) {
        const rawTarget = match[1];
        const [targetTitle, displayText] = rawTarget.split("|");
        const label = (displayText || targetTitle).trim();
        return (
          <button
            key={pIdx}
            onClick={() => onNavigateToNode?.(targetTitle.trim())}
            className="inline-flex items-center gap-1 mx-1 px-2 py-0.5 rounded-md bg-cyan-950/70 hover:bg-cyan-800/80 border border-cyan-500/40 text-cyan-300 text-xs font-mono font-medium transition-all shadow-sm hover:shadow-cyan-500/20 hover:scale-105 active:scale-95"
          >
            <Link2 className="h-3 w-3 text-cyan-400" />
            <span>{label}</span>
          </button>
        );
      }
      return <span key={pIdx}>{part}</span>;
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-in fade-in duration-200">
      <div className="relative flex flex-col w-full max-w-3xl max-h-[88vh] rounded-2xl bg-slate-950/90 border border-cyan-500/40 shadow-2xl shadow-cyan-950/80 overflow-hidden text-slate-100">
        
        {/* Hologramm-Kopfzeile */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-cyan-500/20 bg-gradient-to-r from-slate-900 via-cyan-950/40 to-slate-900">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-950/80 border border-cyan-500/50 shadow-inner">
              <BookOpen className="h-5 w-5 text-cyan-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold tracking-wide text-cyan-100 font-sans">
                  {node.name}
                </h2>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase bg-cyan-950 border border-cyan-500/40 text-cyan-300">
                  {node.category}
                </span>
                {hasConflict && (
                  <span className="flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-red-950 border border-red-500/60 text-red-300 animate-pulse">
                    <AlertTriangle className="h-3 w-3" /> Konflikt
                  </span>
                )}
                {isOrphan && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase bg-amber-950 border border-amber-500/60 text-amber-300">
                    ⚡ Orphan
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-mono mt-0.5">
                {article?.path || node.path || "Lokales Wissensnetzwerk"} &bull; {node.connections} Verbindungen
              </p>
            </div>
          </div>

          {/* Action-Buttons */}
          <div className="flex items-center gap-2">
            {saveSuccess && (
              <span className="flex items-center gap-1 text-xs text-emerald-400 font-mono bg-emerald-950/60 border border-emerald-500/40 px-2.5 py-1 rounded-lg animate-in fade-in">
                <Check className="h-3.5 w-3.5" /> Gespeichert
              </span>
            )}

            <button
              onClick={() => setIsEditing(!isEditing)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all border ${
                isEditing
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/40 hover:bg-amber-500/30"
                  : "bg-cyan-950/80 text-cyan-300 border-cyan-500/40 hover:bg-cyan-900/80"
              }`}
            >
              {isEditing ? (
                <>
                  <Eye className="h-3.5 w-3.5" /> Vorschau
                </>
              ) : (
                <>
                  <Edit3 className="h-3.5 w-3.5" /> Bearbeiten
                </>
              )}
            </button>

            {isEditing && (
              <button
                onClick={handleSave}
                disabled={isSaving || !isDirty}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white transition-all shadow-md shadow-emerald-900/40"
              >
                <Save className="h-3.5 w-3.5" />
                {isSaving ? "Speichert..." : "Speichern"}
              </button>
            )}

            <button
              onClick={() => {
                if (isDirty) {
                  if (confirm("Ungespeicherte Änderungen verwerfen?")) onClose();
                } else {
                  onClose();
                }
              }}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Modal-Inhalt */}
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-cyan-950 scrollbar-track-transparent">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 text-cyan-400/80 gap-3">
              <div className="h-8 w-8 rounded-full border-2 border-cyan-400 border-t-transparent animate-spin" />
              <p className="text-xs font-mono tracking-wider">LADE WISSENSDATEI...</p>
            </div>
          ) : isEditing ? (
            <div className="flex flex-col h-full space-y-2">
              <div className="flex items-center justify-between text-xs text-slate-400 font-mono px-1">
                <span>Markdown-Editor (POSIX Single-Writer)</span>
                {isDirty && <span className="text-amber-400 font-bold">* Ungespeichert (Ctrl+S)</span>}
              </div>
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full h-[52vh] p-4 bg-slate-900/90 border border-cyan-500/30 rounded-xl font-mono text-xs text-slate-200 focus:outline-none focus:border-cyan-400 focus:ring-1 focus:ring-cyan-400/50 resize-none leading-relaxed"
                placeholder="# Notizen eingeben... [[Verknüpfte Themen]]"
              />
            </div>
          ) : (
            <div>
              {renderFormattedContent(article?.content || node.description)}
              
              {/* Verknüpfte Wiki-Links Bar */}
              {article?.links && article.links.length > 0 && (
                <div className="mt-8 pt-4 border-t border-cyan-500/20">
                  <h4 className="text-xs font-mono uppercase tracking-wider text-cyan-400 font-semibold mb-2.5 flex items-center gap-1.5">
                    <Link2 className="h-3.5 w-3.5" /> Semantische Querverweise ({article.links.length}):
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {article.links.map((linkTarget, lIdx) => (
                      <button
                        key={lIdx}
                        onClick={() => onNavigateToNode?.(linkTarget)}
                        className="px-2.5 py-1 rounded-lg bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-500/30 text-cyan-300 text-xs font-mono transition-all hover:scale-105 active:scale-95"
                      >
                        [[{linkTarget}]]
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Fußzeile mit Shortcuts */}
        <div className="flex items-center justify-between px-6 py-2.5 bg-slate-900/80 border-t border-cyan-500/20 text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-4">
            <span><kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-slate-300">Esc</kbd> Schließen</span>
            <span><kbd className="px-1.5 py-0.5 bg-slate-800 rounded border border-slate-700 text-slate-300">Ctrl+S</kbd> Speichern</span>
          </div>
          <span className="text-cyan-400/80">J.A.R.V.I.S. Knowledge Vault</span>
        </div>

      </div>
    </div>
  );
}
