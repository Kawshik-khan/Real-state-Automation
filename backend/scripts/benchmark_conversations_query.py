"""Performance Benchmark: N+1 Query Elimination in Conversations API

This script benchmarks the legacy N+1 query pattern against the optimized single-pass
window function join (ROW_NUMBER() OVER ...) for the list_conversations endpoint.

Usage:
    python backend/scripts/benchmark_conversations_query.py
"""

import asyncio
import time
from typing import Dict, List, Any


def simulate_legacy_n_plus_one(num_conversations: int, simulated_rtt_ms: float = 2.0) -> Dict[str, Any]:
    """Simulates the legacy N+1 query pattern:
    1 query for conversations, then 1 query per conversation for latest message.
    """
    start_time = time.perf_counter()
    
    # Query 1: Fetch conversations
    time.sleep(simulated_rtt_ms / 1000.0)
    conversations = [{"id": f"conv_{i}", "user_id": f"usr_{i}"} for i in range(num_conversations)]
    
    # N Queries: Fetch latest message for each conversation
    messages = []
    for conv in conversations:
        time.sleep(simulated_rtt_ms / 1000.0)
        messages.append({
            "conv_id": conv["id"],
            "text": f"Latest message for {conv['id']}",
            "created_at": "2026-09-27T12:00:00Z"
        })
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    queries_issued = 1 + num_conversations
    return {
        "num_conversations": num_conversations,
        "queries_issued": queries_issued,
        "elapsed_ms": elapsed_ms,
        "network_wait_ms": queries_issued * simulated_rtt_ms,
    }


def simulate_optimized_single_query(num_conversations: int, simulated_rtt_ms: float = 2.0) -> Dict[str, Any]:
    """Simulates the optimized single query with window function join:
    1 unified query fetches conversation, user, and latest message in a single round-trip.
    """
    start_time = time.perf_counter()
    
    # Single Query: 1 network round-trip + minor DB-side sorting/windowing
    time.sleep(simulated_rtt_ms / 1000.0)
    # Simulated DB row unpacking overhead
    results = [
        {
            "id": f"conv_{i}",
            "user_id": f"usr_{i}",
            "lastMessage": f"Latest message for conv_{i}"
        }
        for i in range(num_conversations)
    ]
    
    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    queries_issued = 1
    return {
        "num_conversations": num_conversations,
        "queries_issued": queries_issued,
        "elapsed_ms": elapsed_ms,
        "network_wait_ms": queries_issued * simulated_rtt_ms,
    }


def run_benchmark():
    test_sizes = [10, 25, 50, 100, 250]
    rtt_ms = 2.5  # Typical cloud DB connection pool latency (e.g. Supabase pooler)
    
    print("\n" + "=" * 80)
    print("  GLG ASSETS CONVERSATIONS API: N+1 QUERY PERFORMANCE BENCHMARK")
    print(f"  Simulated Network Latency per Query: {rtt_ms:.1f}ms")
    print("=" * 80)
    print(f"{'Page Size (N)':<15} | {'Legacy Queries':<15} | {'Optimized Queries':<17} | {'Legacy Latency':<15} | {'Optimized Latency':<17} | {'Speedup':<10}")
    print("-" * 88)
    
    for n in test_sizes:
        legacy = simulate_legacy_n_plus_one(n, simulated_rtt_ms=rtt_ms)
        optimized = simulate_optimized_single_query(n, simulated_rtt_ms=rtt_ms)
        
        speedup = legacy["elapsed_ms"] / max(optimized["elapsed_ms"], 0.001)
        print(f"{n:<15} | {legacy['queries_issued']:<15} | {optimized['queries_issued']:<17} | {legacy['elapsed_ms']:>10.2f} ms   | {optimized['elapsed_ms']:>12.2f} ms   | {speedup:>7.1f}x")
        
    print("-" * 88)
    print("Summary:")
    print("  - Algorithmic Complexity: Reduced from O(N) queries to O(1) query.")
    print("  - At standard page limit (50 conversations): 51 queries -> 1 query (~98% round-trip reduction).")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_benchmark()
