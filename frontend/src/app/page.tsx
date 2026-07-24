"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, BrainCircuit, Sparkles, History, Zap, Settings, Loader2, Save } from "lucide-react";
import { Button } from "@/components/ui/button";
import { 
  sendChatMessage, 
  consolidateSession, 
  getWorkingMemory, 
  getSemanticMemory, 
  getProceduralMemory,
  MemoryItem,
  MemoryContext
} from "@/lib/api";

export default function MnemosyneChat() {
  const [sessionId] = useState(`sess_${Math.random().toString(36).substr(2, 9)}`);
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: "assistant", content: "Hello! I am Mnemosyne, an agent with episodic, semantic, working, and procedural memory. How can I help you today?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isConsolidating, setIsConsolidating] = useState(false);
  
  // Memory States
  const [workingMemory, setWorkingMemory] = useState<MemoryContext>({});
  const [semanticMemory, setSemanticMemory] = useState<MemoryItem[]>([]);
  const [proceduralMemory, setProceduralMemory] = useState<MemoryItem[]>([]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const refreshMemory = async () => {
    try {
      const [wm, sm, pm] = await Promise.all([
        getWorkingMemory(sessionId),
        getSemanticMemory(),
        getProceduralMemory()
      ]);
      setWorkingMemory(wm);
      setSemanticMemory(sm);
      setProceduralMemory(pm);
    } catch (e) {
      console.error("Failed to fetch memory", e);
    }
  };

  // Initial load
  useEffect(() => {
    refreshMemory();
  }, []);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMessage = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
    setIsTyping(true);

    try {
      const response = await sendChatMessage(sessionId, userMessage);
      setMessages((prev) => [...prev, { role: "assistant", content: response }]);
      // Refresh memory to show updated context
      await refreshMemory();
    } catch (err) {
      setMessages((prev) => [...prev, { role: "system", content: "Error communicating with Mnemosyne." }]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleConsolidate = async () => {
    setIsConsolidating(true);
    try {
      await consolidateSession(sessionId);
      await refreshMemory();
    } catch (e) {
      console.error("Consolidation failed", e);
    } finally {
      setIsConsolidating(false);
    }
  };

  return (
    <div className="flex h-screen bg-[#09090b] overflow-hidden selection:bg-indigo-500/30 font-sans">
      
      {/* Left Pane - Chat Area */}
      <div className="flex-1 flex flex-col relative z-10">
        
        {/* Header */}
        <header className="h-16 border-b border-white/5 bg-zinc-950/80 backdrop-blur-md flex items-center px-6 justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <div>
              <h1 className="font-heading font-medium text-zinc-100 text-lg leading-tight">Mnemosyne</h1>
              <p className="text-xs text-zinc-500 font-medium">Agentic Memory Engine</p>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-zinc-500">
            <span className="flex items-center gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div> Engine Online</span>
          </div>
        </header>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 space-y-6 scroll-smooth scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          <AnimatePresence initial={false}>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3, ease: "easeOut" }}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] md:max-w-[70%] rounded-2xl px-5 py-4 leading-relaxed ${
                    msg.role === "user"
                      ? "bg-indigo-600/10 border border-indigo-500/20 text-zinc-100 shadow-[0_4px_24px_-8px_rgba(99,102,241,0.2)]"
                      : "bg-zinc-900 border border-white/5 text-zinc-300"
                  }`}
                >
                  {msg.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {/* Typing Indicator */}
          {isTyping && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="bg-zinc-900 border border-white/5 rounded-2xl px-5 py-4 flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-indigo-400 animate-pulse" />
                <span className="text-sm text-zinc-500 font-medium animate-pulse">Retrieving memory...</span>
              </div>
            </motion.div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 md:p-6 bg-gradient-to-t from-zinc-950 via-zinc-950 to-transparent pt-12 shrink-0">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl blur opacity-30 group-focus-within:opacity-100 transition duration-500"></div>
            <div className="relative flex items-end gap-3 bg-zinc-900/80 backdrop-blur-xl border border-white/10 rounded-2xl p-2 shadow-2xl">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
                placeholder="Message Mnemosyne..."
                className="flex-1 max-h-32 min-h-[44px] bg-transparent resize-none border-0 focus:ring-0 text-zinc-100 placeholder:text-zinc-600 p-3 leading-relaxed"
                rows={1}
              />
              <Button 
                type="submit" 
                disabled={!input.trim() || isTyping}
                size="icon"
                className="h-11 w-11 shrink-0 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg disabled:opacity-50 transition-all duration-300"
              >
                {isTyping ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
              </Button>
            </div>
          </form>
        </div>
      </div>

      {/* Right Pane - Memory Inspector */}
      <div className="hidden lg:flex w-[400px] border-l border-white/5 bg-zinc-950/50 flex-col shrink-0">
        <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 shrink-0 bg-zinc-950">
          <div className="flex items-center gap-3">
            <BrainCircuit className="w-5 h-5 text-purple-400" />
            <h2 className="font-heading font-medium text-zinc-200">Memory Inspector</h2>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleConsolidate}
            disabled={isConsolidating}
            className="h-8 bg-zinc-900 border-zinc-800 text-xs hover:bg-zinc-800 hover:text-zinc-100"
          >
            {isConsolidating ? <Loader2 className="w-3 h-3 animate-spin mr-2" /> : <Save className="w-3 h-3 mr-2" />}
            Consolidate
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-5 space-y-8 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent">
          
          {/* Working Memory */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-amber-500 uppercase">
              <Zap className="w-4 h-4" /> Working Context
            </div>
            <div className="bg-zinc-900/50 border border-amber-500/10 rounded-xl p-4 text-sm text-zinc-400 space-y-3">
              {Object.keys(workingMemory).length === 0 ? (
                <div className="text-xs text-zinc-600 italic">No active context.</div>
              ) : (
                Object.entries(workingMemory).map(([k, v]) => (
                  <div key={k} className="space-y-1">
                    <div className="text-xs text-amber-500/70 font-mono">{k}</div>
                    <div className="text-zinc-300 font-medium">{v}</div>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Procedural Memory */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-fuchsia-500 uppercase">
              <Settings className="w-4 h-4" /> Learned Preferences
            </div>
            <div className="bg-zinc-900/50 border border-fuchsia-500/10 rounded-xl p-4 text-sm text-zinc-400 space-y-3">
              {proceduralMemory.length === 0 ? (
                <div className="text-xs text-zinc-600 italic">No patterns learned yet. Consolidate a session to extract them.</div>
              ) : (
                proceduralMemory.map(pm => (
                  <div key={pm.id} className="flex items-start gap-2">
                    <div className="mt-1 w-1.5 h-1.5 rounded-full bg-fuchsia-500 shrink-0"></div>
                    <div>
                      <span>{pm.pattern}</span>
                      <div className="text-[10px] text-fuchsia-500/50 uppercase mt-0.5">{pm.pattern_type}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>

          {/* Semantic Memory */}
          <section className="space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold tracking-wider text-blue-500 uppercase">
              <History className="w-4 h-4" /> Semantic Knowledge
            </div>
            <div className="bg-zinc-900/50 border border-blue-500/10 rounded-xl p-4 text-sm text-zinc-400 space-y-3">
              {semanticMemory.length === 0 ? (
                <div className="text-xs text-zinc-600 italic">No knowledge stored yet.</div>
              ) : (
                semanticMemory.map(sm => (
                  <div key={sm.id} className="pl-3 border-l-2 border-blue-500/30 text-zinc-300">
                    {sm.content}
                    <div className="text-[10px] text-zinc-500 flex justify-between mt-1">
                      <span>{sm.category || "general"}</span>
                      <span className="text-blue-500/50">imp: {sm.importance?.toFixed(2)}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>

        </div>
      </div>
      
    </div>
  );
}
