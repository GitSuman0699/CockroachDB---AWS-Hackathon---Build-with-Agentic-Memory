"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ArrowUp,
  Bot,
  BrainCircuit,
  Check,
  ChevronDown,
  Command,
  Database,
  Gauge,
  Layers3,
  Loader2,
  MoreHorizontal,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Search,
  Settings2,
  Sparkles,
  WandSparkles,
  Zap,
} from "lucide-react";
import {
  consolidateSession,
  getProceduralMemory,
  getSemanticMemory,
  getWorkingMemory,
  MemoryContext,
  MemoryItem,
  sendChatMessage,
} from "@/lib/api";

type Message = { role: "user" | "assistant" | "system"; content: string };

const suggestions = [
  "What have you learned about me?",
  "Summarize the context you are holding",
  "Help me plan a focused work session",
];

function MemoryBadge({ label, value, tone }: { label: string; value: number; tone: "aqua" | "violet" | "amber" }) {
  return (
    <div className="memory-badge">
      <span className={`memory-dot ${tone}`} />
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

export default function MnemosyneChat() {
  const reactId = useId();
  const sessionId = `sess_${reactId.replaceAll(":", "")}`;
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Welcome back. I’m Mnemosyne—your context-aware thinking partner. I retain what matters, connect the dots, and keep the work moving.",
    },
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConsolidating, setIsConsolidating] = useState(false);
  const [showSessions, setShowSessions] = useState(true);
  const [showMemory, setShowMemory] = useState(true);
  const [workingMemory, setWorkingMemory] = useState<MemoryContext>({});
  const [semanticMemory, setSemanticMemory] = useState<MemoryItem[]>([]);
  const [proceduralMemory, setProceduralMemory] = useState<MemoryItem[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const refreshMemory = useCallback(async () => {
    try {
      const [working, semantic, procedural] = await Promise.all([
        getWorkingMemory(sessionId),
        getSemanticMemory(),
        getProceduralMemory(),
      ]);
      setWorkingMemory(working);
      setSemanticMemory(semantic);
      setProceduralMemory(procedural);
    } catch (error) {
      console.error("Failed to refresh memory", error);
    }
  }, [sessionId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void refreshMemory(), 0);
    return () => window.clearTimeout(timer);
  }, [refreshMemory]);

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault();
    const message = input.trim();
    if (!message || isTyping) return;

    setInput("");
    setMessages((current) => [...current, { role: "user", content: message }]);
    setIsTyping(true);
    try {
      const response = await sendChatMessage(sessionId, message);
      setMessages((current) => [...current, { role: "assistant", content: response }]);
      await refreshMemory();
    } catch {
      setMessages((current) => [...current, { role: "system", content: "I couldn’t reach the memory engine. Please try again in a moment." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleConsolidate = async () => {
    setIsConsolidating(true);
    try {
      await consolidateSession(sessionId);
      await refreshMemory();
    } catch (error) {
      console.error("Consolidation failed", error);
    } finally {
      setIsConsolidating(false);
    }
  };

  const startSuggestion = (suggestion: string) => setInput(suggestion);

  return (
    <main className="mnemosyne-shell">
      <aside className="app-rail">
        <div className="brand-mark"><BrainCircuit size={21} strokeWidth={2.2} /></div>
        <nav className="rail-nav" aria-label="Primary navigation">
          <button className="rail-action is-active" aria-label="Workspace"><WandSparkles size={19} /></button>
          <button className="rail-action" aria-label="Memory library"><Layers3 size={19} /></button>
          <button className="rail-action" aria-label="Search"><Search size={19} /></button>
        </nav>
        <div className="rail-bottom">
          <button className="rail-action" aria-label="Settings"><Settings2 size={19} /></button>
          <div className="avatar" aria-label="Profile">S</div>
        </div>
      </aside>

      <AnimatePresence initial={false}>
        {showSessions && (
          <motion.aside className="session-sidebar" initial={{ opacity: 0, x: -18 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -18 }} transition={{ duration: 0.2 }}>
            <div className="sidebar-title-row">
              <span className="eyebrow">Workspace</span>
              <button className="plain-icon" aria-label="More options"><MoreHorizontal size={18} /></button>
            </div>
            <div className="sidebar-scroll">
              <button className="new-thread"><Plus size={17} /> New thread <span><Command size={12} /> K</span></button>
              <div className="thread-group">
                <p>Today</p>
                <button className="thread-item selected"><span className="thread-spark"><Sparkles size={14} /></span><span>Agentic memory demo</span><MoreHorizontal size={16} /></button>
                <button className="thread-item"><span className="thread-icon"><Bot size={14} /></span><span>Product strategy notes</span></button>
                <button className="thread-item"><span className="thread-icon"><Bot size={14} /></span><span>Research workspace</span></button>
              </div>
            </div>
            <div className="sidebar-footnote">
              <div className="storage-ring"><Database size={15} /></div>
              <div><strong>Memory engine</strong><span>Synced just now</span></div>
              <Check size={15} />
            </div>
          </motion.aside>
        )}
      </AnimatePresence>

      <section className="conversation-pane">
        <header className="workspace-header">
          <div className="header-leading">
            <button className="drawer-toggle" onClick={() => setShowSessions((value) => !value)} aria-label={showSessions ? "Collapse left drawer" : "Open left drawer"} title={showSessions ? "Collapse left drawer" : "Open left drawer"}><PanelLeftOpen size={17} /></button>
            <div className="crumbs"><span>Mnemosyne</span><span>/</span><b>Agentic memory demo</b><ChevronDown size={15} /></div>
          </div>
          <div className="header-actions">
            <span className="live-status"><i /> Online</span>
            <button className="right-drawer-toggle" onClick={() => setShowMemory((value) => !value)} aria-label={showMemory ? "Collapse right drawer" : "Expand right drawer"} title={showMemory ? "Collapse right drawer" : "Expand right drawer"}>
              {showMemory ? <PanelRightClose size={17} /> : <PanelRightOpen size={17} />}
              <span>{showMemory ? "Collapse memory" : "Expand memory"}</span>
            </button>
            <button className="plain-icon" aria-label="More options"><MoreHorizontal size={20} /></button>
          </div>
        </header>

        <div className="chat-scroll">
          <div className="chat-column">
            <section className="hero-intro">
              <div className="intro-orbit"><span /><BrainCircuit size={24} /></div>
              <div>
                <p className="eyebrow aqua">Memory-native intelligence</p>
                <h1>Think in context.</h1>
                <p className="intro-copy">Every conversation grows a richer understanding of the work, the facts, and how you like to operate.</p>
              </div>
              <div className="memory-chip-row">
                <MemoryBadge label="Working" value={Object.keys(workingMemory).length} tone="amber" />
                <MemoryBadge label="Knowledge" value={semanticMemory.length} tone="aqua" />
                <MemoryBadge label="Patterns" value={proceduralMemory.length} tone="violet" />
              </div>
            </section>

            <AnimatePresence initial={false}>
              {messages.map((message, index) => (
                <motion.article
                  key={`${message.role}-${index}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.28, ease: "easeOut" }}
                  className={`message-row ${message.role}`}
                >
                  {message.role !== "user" && <div className="message-avatar"><BrainCircuit size={17} /></div>}
                  <div className="message-content">
                    {message.role !== "user" && <div className="message-meta"><b>Mnemosyne</b><span>Memory agent</span></div>}
                    <div className="message-bubble">{message.content}</div>
                  </div>
                </motion.article>
              ))}
            </AnimatePresence>

            {isTyping && (
              <div className="message-row assistant">
                <div className="message-avatar"><BrainCircuit size={17} /></div>
                <div className="message-content"><div className="message-meta"><b>Mnemosyne</b><span>Searching memory</span></div><div className="typing-card"><i /><i /><i /><span>Weaving context together</span></div></div>
              </div>
            )}

            {messages.length === 1 && (
              <div className="suggestion-grid">
                {suggestions.map((suggestion) => <button key={suggestion} onClick={() => startSuggestion(suggestion)}>{suggestion}<ArrowUp size={15} /></button>)}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="composer-zone">
          <form className="composer" onSubmit={handleSend}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void handleSend(event); } }}
              placeholder="Ask anything. I remember the important parts."
              rows={1}
            />
            <div className="composer-tools"><button type="button" className="add-context" aria-label="Add context"><Plus size={18} /></button><span>↵ Send</span><button type="submit" className="send-button" disabled={!input.trim() || isTyping} aria-label="Send message">{isTyping ? <Loader2 size={19} className="spin" /> : <ArrowUp size={19} />}</button></div>
          </form>
          <p className="composer-note">Mnemosyne may use your stored memory to make responses more useful.</p>
        </div>
      </section>

      <AnimatePresence initial={false}>
        {showMemory && (
          <motion.aside className="memory-dock" initial={{ opacity: 0, x: 18 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 18 }} transition={{ duration: 0.24 }}>
            <div className="dock-header"><div><p className="eyebrow">Live system</p><h2>Memory map</h2></div><button className="plain-icon" onClick={() => setShowMemory(false)} aria-label="Collapse right drawer" title="Collapse right drawer"><PanelRightClose size={18} /></button></div>
            <div className="dock-scroll">
              <div className="system-health"><div className="pulse-visual"><span /><BrainCircuit size={23} /></div><div><b>All systems receptive</b><p>Context updates in real time</p></div><Gauge size={18} /></div>
              <div className="memory-section">
                <div className="section-label amber"><Zap size={15} /> Active context <span>{Object.keys(workingMemory).length}</span></div>
                <div className="context-card">{Object.keys(workingMemory).length ? Object.entries(workingMemory).map(([key, value]) => <div className="context-entry" key={key}><span>{key.replaceAll("_", " ")}</span><b>{value}</b></div>) : <p>Conversation context will surface here as you work.</p>}</div>
              </div>
              <div className="memory-section">
                <div className="section-label aqua"><Database size={15} /> Knowledge <span>{semanticMemory.length}</span></div>
                <div className="memory-list">{semanticMemory.length ? semanticMemory.slice(0, 3).map((memory) => <div className="memory-entry" key={memory.id}><i /><div><b>{memory.content}</b><span>{memory.category || "general knowledge"}</span></div></div>) : <p>Facts and durable insights will collect here.</p>}</div>
              </div>
              <div className="memory-section">
                <div className="section-label violet"><Layers3 size={15} /> Learned patterns <span>{proceduralMemory.length}</span></div>
                <div className="memory-list">{proceduralMemory.length ? proceduralMemory.slice(0, 2).map((memory) => <div className="memory-entry pattern" key={memory.id}><i /><div><b>{memory.pattern}</b><span>{memory.pattern_type || "preference"}</span></div></div>) : <p>Consolidate a session to identify preferences and patterns.</p>}</div>
              </div>
            </div>
            <button className="consolidate-button" onClick={handleConsolidate} disabled={isConsolidating}>{isConsolidating ? <Loader2 size={16} className="spin" /> : <Sparkles size={16} />} {isConsolidating ? "Consolidating..." : "Consolidate this session"}</button>
          </motion.aside>
        )}
      </AnimatePresence>
    </main>
  );
}
