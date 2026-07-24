"""
P2 — Agent & Memory Engine Test
Verifies the full agent loop (all 4 memory types) and the consolidation engine.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import asyncio
from app.database import initialize_schema, drop_all_tables
from app.agent import MnemosyneAgent
from app.memory import semantic, procedural

def run_test():
    print("============================================================")
    print("Phase 2 — Agent & Memory Engine Test")
    print("============================================================")

    # 1. Setup Database
    print("\n📦 Setting up fresh database schema...")
    drop_all_tables()
    initialize_schema()
    print("   ✅ Tables created")

    user_id = "test_user_p2"

    # 2. Pre-seed some semantic memory
    print("\n🧠 Seeding semantic memory...")
    semantic.store_knowledge(
        content="The user's favorite programming language is Python because it's great for AI.",
        user_id=user_id,
        category="preferences",
        importance=0.8
    )
    print("   ✅ Semantic memory stored")

    # 3. Start Agent Session 1
    print("\n🤖 Starting Agent Session 1...")
    agent1 = MnemosyneAgent(user_id=user_id)
    
    print("\n💬 User: Hi, can you remind me what my favorite language is?")
    response1 = agent1.chat("Hi, can you remind me what my favorite language is?")
    print(f"🤖 Agent: {response1}")
    
    if "Python" in response1:
        print("   ✅ SUCCESS: Agent retrieved semantic memory")
    else:
        print("   ❌ FAILED to retrieve semantic memory")

    print("\n💬 User: Please always format your answers as a single short bullet point.")
    response2 = agent1.chat("Please always format your answers as a single short bullet point.")
    print(f"🤖 Agent: {response2}")
    
    # 4. Consolidate Session 1
    print("\n🔄 Consolidating Session 1...")
    results = agent1.finish_session()
    print(f"   Created {len(results['semantic_created'])} semantic memories")
    print(f"   Created {len(results['procedural_created'])} procedural memories")

    # Verify procedural memory was created
    patterns = procedural.get_all_patterns(user_id=user_id)
    success = True
    if any("bullet" in p["pattern"].lower() or "concise" in p["pattern"].lower() for p in patterns):
         print("   ✅ SUCCESS: Consolidation extracted procedural preference")
    else:
         print("   ❌ FAILED to extract procedural preference")
         success = False

    # 5. Start Agent Session 2 (should use consolidated patterns)
    print("\n🤖 Starting Agent Session 2...")
    agent2 = MnemosyneAgent(user_id=user_id)
    
    print("\n💬 User: What is the capital of France?")
    response3 = agent2.chat("What is the capital of France?")
    print(f"🤖 Agent: {response3}")
    
    if "-" in response3 or "•" in response3 or "*" in response3:
         print("   ✅ SUCCESS: Agent applied procedural memory (bullet point formatting)")
    else:
         print("   ❌ FAILED to apply procedural memory")
         success = False

    print("\n============================================================")
    if success:
        print("✅ P2 PASSED — Full Agent & Consolidation Engine Works!")
    else:
        print("❌ P2 FAILED")
        sys.exit(1)
    print("============================================================")

if __name__ == "__main__":
    run_test()
