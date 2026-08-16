# Mnemosyne 🧠

> **Universal Agentic Memory as a Service (AMaaS) for Poly-Agent Developers — Powered by CockroachDB & AWS Bedrock**

[![CockroachDB](https://img.shields.io/badge/CockroachDB-Serverless_Vector-6933FF?logo=cockroachlabs&logoColor=white)](https://cockroachlabs.cloud)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Amazon_Bedrock-FF9900?logo=amazonaws&logoColor=white)](https://aws.amazon.com/bedrock/)
[![MCP](https://img.shields.io/badge/Protocol-Model_Context_Protocol_(MCP)-0ea5e9)](https://modelcontextprotocol.io)
[![Next.js 15](https://img.shields.io/badge/Frontend-Next.js_15-black?logo=nextdotjs&logoColor=white)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 💡 The Problem: AI Amnesia & Siloed Tools

Modern developers don't use just one AI assistant. We jump between **Antigravity IDE, Cursor, Claude Desktop, and Claude Code CLI**.

However, each AI lives in its own walled garden with **total amnesia**:
- They forget your personal coding habits and architectural standards across sessions.
- They have no shared context with your other AI tools.
- Native memory features (like ChatGPT or Claude projects) suffer from **vendor lock-in** and lack enterprise database ownership.

**Mnemosyne solves this fundamentally.** It turns **CockroachDB Serverless** into a centralized, persistent cognitive memory layer exposed over the **Model Context Protocol (MCP)**. Teach a rule or fact once, and every AI agent in your workflow shares the exact same memory in real time.

---

## ✨ Key Features

- **🧠 Biologically-Inspired 4-Tier Memory:**
  - **Working Memory:** Fast, session-scoped active context with TTL expiration.
  - **Episodic Memory:** Full chronological conversation logs across all client sessions.
  - **Semantic Memory:** Durable facts and domain knowledge indexed with high-dimensional vectors.
  - **Procedural Memory:** Learned rules, workflows, and personal developer coding conventions.
- **🛡️ Distributed ACID Transaction Resilience:**
  Memory consolidation (the "dreaming" process that extracts short-term context into long-term knowledge) runs inside atomic CockroachDB transactions with automatic `40001` serialization retry handling.
- **🔍 Native CockroachDB Vector Search:**
  Sub-millisecond semantic retrieval using CockroachDB's native vector cosine distance operator (`<=>`) over 1024-dimensional Amazon Titan V2 embeddings.
- **⚡ Universal FastMCP Integration:**
  Connects to any MCP-compatible AI client (Antigravity IDE, Claude Desktop, Cursor, Windsurf) in just 5 lines of configuration.
- **🖥️ Full-Stack Web Playground:**
  Built with Next.js 15, TailwindCSS, and Framer Motion for real-time memory monitoring, interactive chat, and live session consolidation.

---

## 🏗️ System Architecture

```mermaid
flowchart TB
    subgraph Clients["🌐 Poly-Agent Client Ecosystem (BYOA)"]
        A1["Antigravity IDE"]
        A2["Claude Desktop"]
        A3["Cursor / Windsurf"]
        A4["Claude Code CLI"]
        A5["Mnemosyne Web Playground<br/>(Next.js 15 + Tailwind)"]
    end

    subgraph Gateway["⚡ Transport & Integration Gateway"]
        MCP["Model Context Protocol (FastMCP)<br/>Remote SSE & Streamable HTTP"]
        API["FastAPI REST Backend<br/>CORS + Lifespan Manager"]
    end

    subgraph MemoryEngine["🧠 4-Tier Cognitive Memory Engine"]
        WM["1. Working Memory<br/>(Real-time Context & TTL)"]
        EM["2. Episodic Memory<br/>(Chronological Event Log)"]
        CE["Consolidation Engine<br/>('Dreaming' Pipeline)"]
        SM["3. Semantic Memory<br/>(Durable Facts & Knowledge)"]
        PM["4. Procedural Memory<br/>(Learned Rules & Conventions)"]
    end

    subgraph AWS["☁️ AWS Bedrock Intelligence"]
        TITAN["Amazon Titan Embeddings V2<br/>(1024-dimensional vectors)"]
        CLAUDE["Anthropic Claude 3.5<br/>(Autonomous Extraction)"]
    end

    subgraph CRDB["🛡️ CockroachDB Serverless Core"]
        VEC["Distributed Vector Index<br/>Native Cosine Distance (<=>)"]
        ACID["Distributed ACID Transactions<br/>(BEGIN / COMMIT Isolation)"]
        REL["Relational & JSONB Storage<br/>(Audit Logs & Metadata)"]
    end

    %% Client Connections
    A1 & A2 & A3 & A4 -->|MCP Protocol| MCP
    A5 -->|REST API| API

    %% Gateway to Engine
    MCP & API --> WM
    MCP & API --> EM
    MCP & API -->|Vector Query <=>| SM
    MCP & API -->|Preference Match <=>| PM

    %% Consolidation Pipeline
    WM & EM -->|Promote Logs| CE
    CE -->|Synthesize Memories| CLAUDE
    CE -->|Embed Text| TITAN
    TITAN -->|1024-dim Vector| SM
    TITAN -->|1024-dim Vector| PM

    %% Persistence to CockroachDB
    SM & PM -->|Store Vectors| VEC
    CE -->|Atomic Batch Updates| ACID
    EM & WM -->|Persist Records| REL

    classDef client fill:#1e293b,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef gateway fill:#1e1b4b,stroke:#818cf8,stroke-width:2px,color:#f8fafc;
    classDef engine fill:#312e81,stroke:#a855f7,stroke-width:2px,color:#f8fafc;
    classDef aws fill:#451a03,stroke:#f59e0b,stroke-width:2px,color:#f8fafc;
    classDef crdb fill:#064e3b,stroke:#10b981,stroke-width:2px,color:#f8fafc;

    class A1,A2,A3,A4,A5 client;
    class MCP,API gateway;
    class WM,EM,CE,SM,PM engine;
    class TITAN,CLAUDE aws;
    class VEC,ACID,REL crdb;
```

---

## ⚡ Quickstart: Connect Your AI Assistant in 5 Lines

You can connect **Antigravity IDE, Claude Desktop, or Cursor** directly to the live cloud memory server:

Add this snippet to your assistant's MCP configuration file (e.g. `claude_desktop_config.json` or `mcp_config.json`):

```json
{
  "mcpServers": {
    "mnemosyne": {
      "serverUrl": "https://cockroachdb-aws-hackathon-build-with.onrender.com/mcp"
    }
  }
}
```

> **Pro-Tip for Autonomous Memory Retrieval:**
> Add this rule to your AI assistant's system instructions:
> *"CRITICAL: Before answering questions or writing code, autonomously call `search_semantic_memory` and `search_procedural_preferences` to retrieve my project rules and preferences."*

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- A free [CockroachDB Serverless](https://cockroachlabs.cloud) cluster
- An AWS Account with [Amazon Bedrock](https://aws.amazon.com/bedrock/) access (`amazon.titan-embed-text-v2:0` and `anthropic.claude-3-5-sonnet`)

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:
```env
COCKROACHDB_URL=postgresql://<user>:<password>@<host>:26257/defaultdb?sslmode=require
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
BEDROCK_EMBEDDING_MODEL_ID=amazon.titan-embed-text-v2:0
```

Run the backend & MCP server:
```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend Web Playground Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser to interact with the memory console.

---

## ☁️ Production Cloud Deployment

### 1. Deploy Backend to Render
1. Connect your repository to **[Render.com](https://render.com)**.
2. Select **Web Service** with **Root Directory:** `backend`.
3. Set the environment variables (`COCKROACHDB_URL`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BEDROCK_EMBEDDING_MODEL_ID`).
4. Deploy! Render will build the Docker container and expose the MCP endpoint at `https://<your-service>.onrender.com/mcp`.

### 2. Deploy Frontend to Vercel
1. Import the repository into **[Vercel.com](https://vercel.com)**.
2. Set **Root Directory** to `frontend`.
3. Add environment variable `NEXT_PUBLIC_API_URL` = `https://<your-render-service>.onrender.com`.
4. Deploy!

---

## 📂 Repository Structure

```
├── .agents/skills/          # CockroachDB agent skills for IDE automation
├── backend/
│   ├── app/
│   │   ├── memory/          # 4-tier memory engine (working, episodic, semantic, procedural)
│   │   ├── database.py      # CockroachDB connection pooling & vector DDL
│   │   ├── embeddings.py    # AWS Titan V2 1024-dim embedding generator
│   │   └── llm.py           # AWS Bedrock Claude 3.5 client
│   ├── mcp_server.py        # FastMCP Server definition & tools
│   ├── main.py              # FastAPI REST backend & SSE router
│   └── Dockerfile           # Production container build
├── frontend/                # Next.js 15 Web Playground & Memory Dashboard
└── README.md
```

---

## 🏆 Hackathon Track Alignment

Built with pride for the **CockroachDB × AWS Hackathon — Build with Agentic Memory**.
- **CockroachDB:** Distributed Vector Indexing (`<=>`), ACID Consolidation Transactions, and Agent Skills.
- **AWS Bedrock:** Amazon Titan Embeddings V2 (`1024-dim`) & Claude 3.5 Sonnet / Haiku.

---

## 📄 License
MIT License. Open source and available for developers everywhere.
