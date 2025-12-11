# Base Agent Architecture

This module contains the core `BaseAgent` class and all its specialized managers, implementing a clean separation of concerns through dedicated manager classes.

## Components

### BaseAgent (agent.py)
Minimal orchestrator that delegates to specialized managers.

**Responsibilities:**
- Coordinate execution flow
- Initialize and wire managers
- Delegate operations to appropriate managers

**Key Methods:**
- `run(user_prompt)` - Main entry point

### LLMMessageAgentManager
Handles all LLM communication and message format conversion.

**Responsibilities:**
- Get responses from LLM
- Convert between LLM and internal message formats
- Format messages for storage
- Clean message dictionaries

**Key Methods:**
- `get_llm_response(messages)` - Get LLM response
- `format_messages_for_storage(messages)` - Format for persistence

### ToolsAgentManager
Manages tool execution and result storage.

**Responsibilities:**
- Execute tool calls via scheduler
- Store tool results in memory
- Append results to message list

**Key Methods:**
- `execute_and_store_tools(tool_calls, messages)` - Execute and store

### MemoryAgentManager
Handles all memory-related operations.

**Responsibilities:**
- Build message lists from history
- Store user and assistant turns
- Extract and collect tool data
- Manage conversation history

**Key Methods:**
- `build_message_list(user_prompt)` - Build from history
- `store_user_turn(user_prompt, messages)` - Store user input
- `store_messages_with_tools(messages)` - Store with tool data

### WorkflowManager
Manages execution lifecycle and output creation.

**Responsibilities:**
- Retrieve and validate final messages
- Create agent outputs
- Handle errors and create error outputs

**Key Methods:**
- `get_final_message(messages)` - Get final response
- `validate_final_message(message)` - Validate response
- `create_agent_output(message, messages)` - Create output
- `handle_error(error)` - Error handling

### ThinkLoopManager
Executes the core think-act-observe reasoning loop.

**Responsibilities:**
- Execute reasoning loop
- Orchestrate LLM queries and tool executions
- Yield step information for observation

**Key Methods:**
- `think(messages, max_turns)` - Core reasoning generator
- `execute_thinking_loop(messages)` - Execute full loop

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        BaseAgent                            │
│                  (Orchestrator - 118 lines)                 │
│                                                             │
│  run() → delegates to managers:                             │
│    1. MemoryAgentManager.build_message_list()               │
│    2. MemoryAgentManager.store_user_turn()                  │
│    3. ThinkLoopManager.execute_thinking_loop()              │
│    4. WorkflowManager.get_final_message()                   │
│    5. WorkflowManager.validate_final_message()              │
│    6. MemoryAgentManager.store_messages_with_tools()        │
│    7. WorkflowManager.create_agent_output()                 │
└─────────────────────────────────────────────────────────────┘
```

## Usage

```python
from agents.base_agent import BaseAgent

# BaseAgent is abstract - use DefaultAgent or create custom implementation
class MyCustomAgent(BaseAgent):
    def __init__(self, llm, tool_scheduler, prompt_builder, memory_manager, config):
        super().__init__(llm, tool_scheduler, prompt_builder, memory_manager, config)

    def run(self, user_prompt: str):
        # Add custom logic before/after base run
        return super().run(user_prompt)
```
