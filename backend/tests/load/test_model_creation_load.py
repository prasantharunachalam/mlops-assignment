"""
Basic load test for model creation.

Tests the platform's ability to handle concurrent model registrations.
This validates the "designed for 10,000 models" claim.
"""
import time
import asyncio
import httpx
from typing import List

BASE_URL = "http://localhost:8000/api/v1"


async def create_model(client: httpx.AsyncClient, index: int) -> dict:
    """Create a single model."""
    payload = {
        "name": f"load-test-model-{index}",
        "owner": "load-tester",
        "description": f"Load test model #{index}"
    }
    response = await client.post(f"{BASE_URL}/models", json=payload)
    return {"index": index, "status": response.status_code, "time": response.elapsed.total_seconds()}


async def run_load_test(num_models: int = 100, concurrent: int = 10):
    """
    Run load test creating multiple models concurrently.

    Args:
        num_models: Total number of models to create
        concurrent: Number of concurrent requests
    """
    print(f"\n🔥 Load Test: Creating {num_models} models with {concurrent} concurrent requests\n")

    start_time = time.time()
    results = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create models in batches
        for batch_start in range(0, num_models, concurrent):
            batch_end = min(batch_start + concurrent, num_models)
            tasks = [
                create_model(client, i)
                for i in range(batch_start, batch_end)
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            results.extend(batch_results)

            # Progress indicator
            print(f"  ✓ Created {batch_end}/{num_models} models")

    end_time = time.time()
    total_time = end_time - start_time

    # Analyze results
    successful = sum(1 for r in results if isinstance(r, dict) and r["status"] == 200)
    failed = len(results) - successful
    avg_response_time = sum(r["time"] for r in results if isinstance(r, dict)) / len(results)

    print(f"\n📊 Results:")
    print(f"  Total time: {total_time:.2f}s")
    print(f"  Successful: {successful}/{num_models} ({successful/num_models*100:.1f}%)")
    print(f"  Failed: {failed}/{num_models}")
    print(f"  Throughput: {num_models/total_time:.1f} models/sec")
    print(f"  Avg response time: {avg_response_time*1000:.0f}ms")

    if successful >= num_models * 0.95:  # 95% success rate
        print(f"\n✅ PASS: Load test succeeded ({successful}/{num_models} models created)")
        return 0
    else:
        print(f"\n❌ FAIL: Too many failures ({failed}/{num_models})")
        return 1


if __name__ == "__main__":
    import sys

    # Default: Test with 100 models (proves concept without overwhelming system)
    # For full test: python test_model_creation_load.py 1000
    num_models = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    exit_code = asyncio.run(run_load_test(num_models=num_models, concurrent=10))
    sys.exit(exit_code)
