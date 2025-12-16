"""
Manual test script for supervised workflow.
Run this with backend mock running on localhost:8000
"""
from core.orchestrator import Orchestrator
from core.llm_wrapper import LLMWrapperConfig


def test_supervised_workflow():
    """Test supervised workflow manually."""
    print("=== Testing Supervised Workflow ===\n")

    llm_config = LLMWrapperConfig(
        base_url="http://localhost:8000",
        api_service="",
        embed_service=""
    )

    orchestrator = Orchestrator(llm_config=llm_config)
    orchestrator.reset_conversation()

    print("1. Testing simple task...")
    output = orchestrator.process_user_input_supervised("simple task")
    print(f"   Success: {output.success}")
    print(f"   Response: {output.response[:100]}...\n")

    print("2. Testing analyze codebase (3 steps with dependencies)...")
    output = orchestrator.process_user_input_supervised("analyze codebase")
    print(f"   Success: {output.success}")
    print(f"   Response preview:")
    for line in output.response.split('\n')[:10]:
        print(f"   {line}")
    print("   ...\n")

    print("=== Tests Complete ===")


if __name__ == "__main__":
    test_supervised_workflow()
