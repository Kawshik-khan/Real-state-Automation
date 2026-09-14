import sys
print("Step 1: Python started", flush=True)

import asyncio
print("Step 2: asyncio imported", flush=True)

from app.agents.graph import ai_graph
print("Step 3: ai_graph imported", flush=True)

from app.agents.state import AIState
print("Step 4: AIState imported", flush=True)

async def test():
    print("Step 5: Inside test()", flush=True)
    state = AIState(message='Banani te 3BHK flat er price koto?', conversation_id='test_001', channel='whatsapp')
    print("Step 6: AIState created", flush=True)
    res = await ai_graph.ainvoke(state)
    print("Step 7: ai_graph invoked successfully!", flush=True)
    print("Result intent:", getattr(res.get('intent'), 'intent', res.get('intent')), flush=True)

if __name__ == "__main__":
    asyncio.run(test())
