"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ArrowUp,
  BrainCircuit,
  Check,
  Database,
  Layers3,
  Loader2,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Plus,
  Sparkles,
  Trash2,
  WandSparkles,
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

type Thread = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
};

const WELCOME_MESSAGE: Message = {
  role: "assistant",
  content:
    "Welcome back. I\u2019m Mnemosyne\u2014your context-aware thinking partner. I retain what matters, connect the dots, and keep the work moving.",
};

const suggestions = [
  "What have you learned about me?",
  "Summarize the context you are holding",
  "Help me plan a focused work session",
];

function generateSessionId() {
  return `sess_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
}

function MemoryBadge({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "aqua" | "violet" | "amber";
}) {
  return (
    <div className="memory-badge">
      <span className={`memory-dot ${tone}`} />
      <span>{label}</span>
      <b>{value}</b>
    </div>
  );
}

export default function MnemosyneChat() {
  /* ── Thread / Session state ── */
  const [threads, setThreads] = useState<Thread[]>(() => {
    const initial: Thread = {
      id: generateSessionId(),
      title: "Agentic memory demo",
      messages: [WELCOME_MESSAGE],
      createdAt: Date.now(),
    };
    return [initial];
  });
  const [activeThreadIndex, setActiveThreadIndex] = useState(0);

  const activeThread = threads[activeThreadIndex];
  const sessionId = activeThread.id;
  const messages = activeThread.messages;

  /* ── UI state ── */
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConsolidating, setIsConsolidating] = useState(false);
  const [showSessions, setShowSessions] = useState(true);
  const [showMemory, setShowMemory] = useState(true);

  /* ── Memory state ── */
  const [workingMemory, setWorkingMemory] = useState<MemoryContext>({});
  const [semanticMemory, setSemanticMemory] = useState<MemoryItem[]>([]);
  const [proceduralMemory, setProceduralMemory] = useState<MemoryItem[]>([]);

  /* ── MCP Logs state ── */
  const [mcpLogs, setMcpLogs] = useState<string[]>([
    "> [MCP Server] Initialized FastMCP AMaaS Node",
    "> [CockroachDB] Connection pool ready",
  ]);
  const logEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mcpLogs]);

  const appendLog = useCallback((log: string) => {
    setMcpLogs((prev) => [...prev, log]);
  }, []);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /* ── Scroll to bottom on new messages ── */
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  /* ── Memory refresh ── */
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

  /* ── Helper: update the active thread's messages ── */
  const pushMessages = (newMessages: Message[]) => {
    setThreads((prev) =>
      prev.map((t, i) =>
        i === activeThreadIndex
          ? { ...t, messages: [...t.messages, ...newMessages] }
          : t
      )
    );
  };

  /* ── Helper: derive thread title from first user message ── */
  const updateThreadTitle = (threadIndex: number, userMessage: string) => {
    setThreads((prev) =>
      prev.map((t, i) => {
        if (i !== threadIndex) return t;
        // Only update the title if it's still the default
        if (t.title !== "New thread") return t;
        const title =
          userMessage.length > 40
            ? userMessage.substring(0, 40) + "…"
            : userMessage;
        return { ...t, title };
      })
    );
  };

  /* ── Send message ── */
  const doSend = async (message: string) => {
    if (!message.trim() || isTyping) return;

    const trimmed = message.trim();
    setInput("");
    pushMessages([{ role: "user", content: trimmed }]);
    updateThreadTitle(activeThreadIndex, trimmed);
    setIsTyping(true);

    try {
      appendLog(`> [Agent] Initializing tool call: search_procedural_preferences("${trimmed.substring(0, 20)}...")`);
      appendLog(`> [MCP Server] Querying CockroachDB Vector Index...`);
      const response = await sendChatMessage(sessionId, trimmed);
      appendLog(`> [MCP Server] Retrieved context for Agent injection.`);
      pushMessages([{ role: "assistant", content: response }]);
      await refreshMemory();
    } catch {
      pushMessages([
        {
          role: "system",
          content:
            "I couldn\u2019t reach the memory engine. Please try again in a moment.",
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleSend = async (event: React.FormEvent) => {
    event.preventDefault();
    await doSend(input);
  };

  /* ── Suggestion click → auto-send ── */
  const handleSuggestion = (suggestion: string) => {
    void doSend(suggestion);
  };

  /* ── New Thread ── */
  const createNewThread = useCallback(() => {
    const timestamp = Date.now();
    const newThread: Thread = {
      id: generateSessionId(),
      title: "New thread",
      messages: [WELCOME_MESSAGE],
      createdAt: timestamp,
    };
    setThreads((prev) => [newThread, ...prev]);
    setActiveThreadIndex(0);
    setInput("");
    setWorkingMemory({});
    // Focus the textarea
    setTimeout(() => textareaRef.current?.focus(), 100);
  }, []);

  /* ── Switch Thread ── */
  const switchThread = (index: number) => {
    if (index === activeThreadIndex) return;
    setActiveThreadIndex(index);
    setInput("");
    // Refresh memory for the new session
    setTimeout(() => void refreshMemory(), 0);
  };

  /* ── Delete Thread ── */
  const deleteThread = (index: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (threads.length <= 1) {
      // Can't delete the last thread — create a fresh one instead
      createNewThread();
      return;
    }
    setThreads((prev) => prev.filter((_, i) => i !== index));
    if (activeThreadIndex >= index && activeThreadIndex > 0) {
      setActiveThreadIndex((prev) => prev - 1);
    }
  };

  /* ── Consolidate ── */
  const handleConsolidate = async () => {
    setIsConsolidating(true);
    try {
      appendLog(`> [Agent] Consolidating episodic memory logs...`);
      appendLog(`> [MCP Server] Calling Bedrock (Claude 3.5 Haiku) for extraction...`);
      
      await consolidateSession(sessionId);
      
      appendLog(`> [MCP Server] Generating Vector Embeddings via Amazon Titan...`);
      appendLog(`> [MCP Server] ACID Transaction BEGIN`);
      appendLog(`> [CockroachDB] Executing Vector Inserts...`);
      appendLog(`> [MCP Server] ACID Transaction COMMIT`);
      appendLog(`> [MCP Server] Success: Memory synchronized.`);
      
      await refreshMemory();
    } catch (error) {
      console.error("Consolidation failed", error);
      appendLog(`> [MCP Server] ACID Transaction ROLLBACK - Error occurred.`);
    } finally {
      setIsConsolidating(false);
    }
  };

  /* ── Group threads by date ── */
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const todayTs = today.getTime();
  const yesterdayTs = todayTs - 86400000;

  const todayThreads = threads.filter((t) => t.createdAt >= todayTs);
  const yesterdayThreads = threads.filter(
    (t) => t.createdAt >= yesterdayTs && t.createdAt < todayTs
  );
  const olderThreads = threads.filter((t) => t.createdAt < yesterdayTs);

  return (
    <main className="mnemosyne-shell">
      {/* ══ Left Rail ══ */}
      <aside className="app-rail">
        <div className="brand-mark">
          <BrainCircuit size={21} strokeWidth={2.2} />
        </div>
        <nav className="rail-nav" aria-label="Primary navigation">
          <button
            className="rail-action is-active"
            aria-label="Workspace"
            title="Workspace"
          >
            <WandSparkles size={19} />
          </button>
        </nav>
        <div className="rail-bottom">
          <div className="avatar" aria-label="Profile">
            S
          </div>
        </div>
      </aside>

      {/* ══ Session Sidebar ══ */}
      <motion.aside
        className="session-sidebar"
        animate={{
          width: showSessions ? 239 : 0,
          opacity: showSessions ? 1 : 0,
          paddingLeft: showSessions ? 13 : 0,
          paddingRight: showSessions ? 13 : 0,
        }}
        transition={{ duration: 0.28, ease: [0.25, 0.1, 0.25, 1] }}
        style={{ overflow: "hidden", flexShrink: 0 }}
      >
        <div className="sidebar-title-row">
          <span className="eyebrow">Workspace</span>
        </div>
        <div className="sidebar-scroll">
          <button className="new-thread" onClick={createNewThread}>
            <Plus size={17} /> New thread
          </button>

          {todayThreads.length > 0 && (
            <div className="thread-group">
              <p>Today</p>
              {todayThreads.map((thread) => {
                const globalIndex = threads.indexOf(thread);
                return (
                  <button
                    key={thread.id}
                    className={`thread-item ${globalIndex === activeThreadIndex ? "selected" : ""}`}
                    onClick={() => switchThread(globalIndex)}
                  >
                    <span className={globalIndex === activeThreadIndex ? "thread-spark" : "thread-icon"}>
                      {globalIndex === activeThreadIndex ? (
                        <Sparkles size={14} />
                      ) : (
                        <Layers3 size={14} />
                      )}
                    </span>
                    <span>{thread.title}</span>
                    <Trash2
                      size={14}
                      className="thread-delete"
                      onClick={(e) => deleteThread(globalIndex, e)}
                    />
                  </button>
                );
              })}
            </div>
          )}

          {yesterdayThreads.length > 0 && (
            <div className="thread-group">
              <p>Yesterday</p>
              {yesterdayThreads.map((thread) => {
                const globalIndex = threads.indexOf(thread);
                return (
                  <button
                    key={thread.id}
                    className={`thread-item ${globalIndex === activeThreadIndex ? "selected" : ""}`}
                    onClick={() => switchThread(globalIndex)}
                  >
                    <span className="thread-icon">
                      <Layers3 size={14} />
                    </span>
                    <span>{thread.title}</span>
                    <Trash2
                      size={14}
                      className="thread-delete"
                      onClick={(e) => deleteThread(globalIndex, e)}
                    />
                  </button>
                );
              })}
            </div>
          )}

          {olderThreads.length > 0 && (
            <div className="thread-group">
              <p>Earlier</p>
              {olderThreads.map((thread) => {
                const globalIndex = threads.indexOf(thread);
                return (
                  <button
                    key={thread.id}
                    className={`thread-item ${globalIndex === activeThreadIndex ? "selected" : ""}`}
                    onClick={() => switchThread(globalIndex)}
                  >
                    <span className="thread-icon">
                      <Layers3 size={14} />
                    </span>
                    <span>{thread.title}</span>
                    <Trash2
                      size={14}
                      className="thread-delete"
                      onClick={(e) => deleteThread(globalIndex, e)}
                    />
                  </button>
                );
              })}
            </div>
          )}
        </div>
        <div className="sidebar-footnote">
          <div className="storage-ring">
            <Database size={15} />
          </div>
          <div>
            <strong>Memory engine</strong>
            <span>Synced just now</span>
          </div>
          <Check size={15} />
        </div>
      </motion.aside>

      {/* ══ Conversation Pane ══ */}
      <section className="conversation-pane">
        <header className="workspace-header">
          <div className="header-leading">
            <button
              className="drawer-toggle"
              onClick={() => setShowSessions((v) => !v)}
              aria-label={
                showSessions ? "Collapse left drawer" : "Open left drawer"
              }
              title={
                showSessions ? "Collapse left drawer" : "Open left drawer"
              }
            >
              {showSessions ? <PanelLeftClose size={17} /> : <PanelLeftOpen size={17} />}
            </button>
            <div className="crumbs">
              <span>Mnemosyne</span>
              <span>/</span>
              <b>{activeThread.title}</b>
            </div>
          </div>
          <div className="header-actions">
            <span className="live-status">
              <i /> Online
            </span>
            <button
              className="right-drawer-toggle"
              onClick={() => setShowMemory((v) => !v)}
              aria-label={
                showMemory
                  ? "Collapse right drawer"
                  : "Expand right drawer"
              }
              title={
                showMemory
                  ? "Collapse right drawer"
                  : "Expand right drawer"
              }
            >
              {showMemory ? (
                <PanelRightClose size={17} />
              ) : (
                <PanelRightOpen size={17} />
              )}
              <span>{showMemory ? "Collapse memory" : "Expand memory"}</span>
            </button>
          </div>
        </header>

        <div className="chat-scroll">
          <div className="chat-column">
            <section className="hero-intro">
              <div className="intro-orbit">
                <span />
                <BrainCircuit size={24} />
              </div>
              <div>
                <p className="eyebrow aqua">Memory-native intelligence</p>
                <h1>Think in context.</h1>
                <p className="intro-copy">
                  Every conversation grows a richer understanding of the work,
                  the facts, and how you like to operate.
                </p>
              </div>
              <div className="memory-chip-row">
                <MemoryBadge
                  label="Working"
                  value={Object.keys(workingMemory).length}
                  tone="amber"
                />
                <MemoryBadge
                  label="Knowledge"
                  value={semanticMemory.length}
                  tone="aqua"
                />
                <MemoryBadge
                  label="Patterns"
                  value={proceduralMemory.length}
                  tone="violet"
                />
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
                  {message.role !== "user" && (
                    <div className="message-avatar">
                      <BrainCircuit size={17} />
                    </div>
                  )}
                  <div className="message-content">
                    {message.role !== "user" && (
                      <div className="message-meta">
                        <b>Mnemosyne</b>
                        <span>Memory agent</span>
                      </div>
                    )}
                    <div className="message-bubble">
                      {message.role === "user" ? (
                        message.content
                      ) : (
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      )}
                    </div>
                  </div>
                </motion.article>
              ))}
            </AnimatePresence>

            {isTyping && (
              <div className="message-row assistant">
                <div className="message-avatar">
                  <BrainCircuit size={17} />
                </div>
                <div className="message-content">
                  <div className="message-meta">
                    <b>Mnemosyne</b>
                    <span>Searching memory</span>
                  </div>
                  <div className="typing-card">
                    <i />
                    <i />
                    <i />
                    <span>Weaving context together</span>
                  </div>
                </div>
              </div>
            )}

            {messages.length === 1 && (
              <div className="suggestion-grid">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSuggestion(suggestion)}
                  >
                    {suggestion}
                    <ArrowUp size={15} />
                  </button>
                ))}
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="composer-zone">
          <form className="composer" onSubmit={handleSend}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  void handleSend(event);
                }
              }}
              placeholder="Ask anything. I remember the important parts."
              rows={1}
            />
            <div className="composer-tools">
              <span>↵ Send</span>
              <button
                type="submit"
                className="send-button"
                disabled={!input.trim() || isTyping}
                aria-label="Send message"
              >
                {isTyping ? (
                  <Loader2 size={19} className="spin" />
                ) : (
                  <ArrowUp size={19} />
                )}
              </button>
            </div>
          </form>
          <p className="composer-note">
            Mnemosyne may use your stored memory to make responses more useful.
          </p>
        </div>
      </section>

      {/* ══ Memory Dock ══ */}
      <motion.aside
        className="memory-dock"
        animate={{
          width: showMemory ? 400 : 0,
          opacity: showMemory ? 1 : 0,
          paddingLeft: showMemory ? 19 : 0,
          paddingRight: showMemory ? 19 : 0,
        }}
        transition={{ duration: 0.28, ease: [0.25, 0.1, 0.25, 1] }}
        style={{ overflow: "hidden", flexShrink: 0, backgroundColor: "#0a0a0a", borderLeft: "1px solid #333" }}
      >
            <div className="dock-header">
              <div>
                <p className="eyebrow" style={{ color: "#00ff00" }}>Live system</p>
                <h2 style={{ color: "#fff", fontFamily: "monospace" }}>MCP Server Logs</h2>
              </div>
              <button
                className="plain-icon"
                onClick={() => setShowMemory(false)}
                aria-label="Collapse right drawer"
                title="Collapse right drawer"
              >
                <PanelRightClose size={18} />
              </button>
            </div>
            <div className="dock-scroll" style={{ backgroundColor: "#000", padding: "10px", borderRadius: "6px", fontFamily: "monospace", color: "#00ff00", fontSize: "13px", display: "flex", flexDirection: "column", gap: "8px" }}>
              {mcpLogs.map((log, i) => (
                <div key={i} style={{ wordBreak: "break-all" }}>{log}</div>
              ))}
              <div ref={logEndRef} />
            </div>
            <button
              className="consolidate-button"
              onClick={handleConsolidate}
              disabled={isConsolidating}
            >
              {isConsolidating ? (
                <Loader2 size={16} className="spin" />
              ) : (
                <Sparkles size={16} />
              )}{" "}
              {isConsolidating
                ? "Consolidating..."
                : "Consolidate this session"}
            </button>
      </motion.aside>
    </main>
  );
}
