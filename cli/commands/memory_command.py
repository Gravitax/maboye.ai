"""
Memory Command

Display and inspect conversation memory.
"""

from typing import List
from .base_command import BaseCommand


class MemoryCommand(BaseCommand):
    """Command to display memory statistics and content."""

    @property
    def description(self) -> str:
        """Command description."""
        return "Show memory statistics or content. Usage: /memory [ID|clean]"

    def execute(self, args: List[str]) -> bool:
        """Execute memory command."""
        memory_id_map = self._get_memory_id_map()

        if not args:
            self._display_memory_stats(memory_id_map)
        elif args[0].lower() == "clean":
            self._clean_memory()
        else:
            self._display_memory_content(args[0], memory_id_map)

        return True

    def _get_memory_id_map(self) -> dict:
        """
        Get the memory ID mapping.

        Returns:
            Dictionary mapping memory IDs to memory types.
        """
        return {1: "conversation"}

    def _clean_memory(self) -> None:
        """Clean all conversation memory."""
        try:
            self._orchestrator.reset_conversation()
            print("\n✓ Memory cleaned successfully.")
            print("All conversation history has been cleared.\n")
        except Exception as e:
            print(f"\n✗ Error cleaning memory: {e}\n")

    def _display_memory_stats(self, id_map: dict) -> None:
        """Display memory statistics with IDs."""
        stats = self._orchestrator.get_memory_stats()

        self._print_stats_header()
        self._print_memory_sections(id_map, stats)
        self._print_stats_footer()

    def _print_stats_header(self) -> None:
        """Print statistics section header."""
        print("\nMemory Statistics:")
        print("-" * 60)

    def _print_memory_sections(self, id_map: dict, stats: dict) -> None:
        """
        Print statistics for each memory section.

        Args:
            id_map: Dictionary mapping IDs to memory types.
            stats: Statistics dictionary from orchestrator.
        """
        for mem_id, mem_type in id_map.items():
            data = stats.get(mem_type, {})
            self._print_single_section(mem_id, mem_type, data)

    def _print_single_section(self, mem_id: int, mem_type: str, data: dict) -> None:
        """
        Print statistics for a single memory section.

        Args:
            mem_id: The memory section ID.
            mem_type: The memory section type.
            data: The statistics data for this section.
        """
        status = self._get_section_status(data)
        entries_count = data.get('size', 0)

        print(f"\n[{mem_id}] {mem_type.upper()}:")
        print(f"    Entries: {entries_count}")
        print(f"    Status: {status}")

    def _get_section_status(self, data: dict) -> str:
        """
        Get the status string for a memory section.

        Args:
            data: The statistics data for the section.

        Returns:
            Status string (Empty or Has data).
        """
        is_empty = data.get('is_empty', True)
        return 'Empty' if is_empty else 'Has data'

    def _print_stats_footer(self) -> None:
        """Print statistics section footer."""
        print("-" * 60)
        print("\nUsage:")
        print("  /memory <ID>    - View content of a specific section")
        print("  /memory clean   - Clear all conversation history")
        print()

    def _display_memory_content(self, mem_id_str: str, id_map: dict) -> None:
        """Display content of a specific memory section."""
        mem_id = self._parse_memory_id(mem_id_str)
        if mem_id is None:
            return

        if not self._validate_memory_id(mem_id, id_map):
            return

        mem_type = id_map[mem_id]
        content = self._orchestrator.get_memory_content(mem_type)

        self._print_content_section(mem_id, mem_type, content)

    def _parse_memory_id(self, mem_id_str: str) -> int:
        """
        Parse memory ID from string.

        Args:
            mem_id_str: String representation of memory ID.

        Returns:
            Parsed memory ID or None if invalid.
        """
        try:
            return int(mem_id_str)
        except ValueError:
            print(f"\nError: Invalid memory ID '{mem_id_str}'. Must be 1.\n")
            return None

    def _validate_memory_id(self, mem_id: int, id_map: dict) -> bool:
        """
        Validate that memory ID exists in the map.

        Args:
            mem_id: The memory ID to validate.
            id_map: Dictionary of valid memory IDs.

        Returns:
            True if valid, False otherwise.
        """
        if mem_id not in id_map:
            print(f"\nError: Memory ID {mem_id} not found. Valid ID: 1.\n")
            return False
        return True

    def _print_content_section(self, mem_id: int, mem_type: str, content: list) -> None:
        """
        Print the content section for a memory type.

        Args:
            mem_id: The memory section ID.
            mem_type: The memory section type.
            content: The memory content entries.
        """
        print(f"\n[{mem_id}] {mem_type.upper()} Content:")
        print("-" * 60)

        if self._is_content_empty(content):
            print("No entries found.")
        else:
            self._display_conversation_pairs(content)

        print("-" * 60)
        print()

    def _is_content_empty(self, content: list) -> bool:
        """
        Check if content is empty.

        Args:
            content: The content list to check.

        Returns:
            True if empty, False otherwise.
        """
        return not content or len(content) == 0

    def _display_conversation_pairs(self, entries: list) -> None:
        """Display conversation entries grouped by question-answer pairs."""
        pair_id = 1
        idx = 0

        while idx < len(entries):
            entry = entries[idx]

            if self._is_user_entry(entry):
                idx = self._display_conversation_pair(entries, idx, pair_id)
                pair_id += 1

            idx += 1

    def _is_user_entry(self, entry: dict) -> bool:
        """
        Check if entry is a user message.

        Args:
            entry: The entry to check.

        Returns:
            True if entry is from user, False otherwise.
        """
        data = entry.get("data", {})
        role = data.get("role", "unknown")
        return role == "user"

    def _display_conversation_pair(self, entries: list, idx: int, pair_id: int) -> int:
        """
        Display a single conversation pair (user input and assistant output).

        Args:
            entries: List of all entries.
            idx: Current index of the user entry.
            pair_id: The pair identifier number.

        Returns:
            Updated index after processing the pair.
        """
        self._print_pair_header(pair_id)
        self._display_input(entries[idx])

        if self._has_assistant_response(entries, idx):
            idx += 1
            self._display_output(entries[idx])

        return idx

    def _print_pair_header(self, pair_id: int) -> None:
        """
        Print header for a conversation pair.

        Args:
            pair_id: The pair identifier number.
        """
        print(f"\n{'='*60}")
        print(f"MESSAGE {pair_id}")
        print(f"{'='*60}")

    def _has_assistant_response(self, entries: list, user_idx: int) -> bool:
        """
        Check if there is an assistant response after the user entry.

        Args:
            entries: List of all entries.
            user_idx: Index of the user entry.

        Returns:
            True if assistant response exists, False otherwise.
        """
        next_idx = user_idx + 1
        if next_idx >= len(entries):
            return False

        next_entry = entries[next_idx]
        next_role = next_entry.get("data", {}).get("role")
        return next_role == "assistant"

    def _display_input(self, entry: dict) -> None:
        """Display INPUT section."""
        timestamp = entry.get("timestamp", "N/A")
        data = entry.get("data", {})

        self._print_input_header(timestamp)
        self._print_input_agent(data)
        self._print_user_query(data)
        self._print_input_context(data)
        self._print_input_prompt(data)

    def _print_input_header(self, timestamp: str) -> None:
        """
        Print INPUT section header.

        Args:
            timestamp: The timestamp of the input.
        """
        print(f"\n--- INPUT ---")
        print(f"Timestamp: {timestamp}")

    def _print_input_agent(self, data: dict) -> None:
        """
        Print agent name from input data.

        Args:
            data: The input data dictionary.
        """
        context = data.get("context", {})
        agent_name = context.get("agent_name", "Unknown")
        print(f"Agent: {agent_name}")

    def _print_user_query(self, data: dict) -> None:
        """
        Print user query from input data.

        Args:
            data: The input data dictionary.
        """
        content = data.get("content", "")
        print(f"\nUser Query:")
        print(content)

    def _print_input_context(self, data: dict) -> None:
        """
        Print context information if available.

        Args:
            data: The input data dictionary.
        """
        context = data.get("context", {})
        if context:
            print(f"\nContext:")
            for key, value in context.items():
                print(f"  - {key}: {value}")

    def _print_input_prompt(self, data: dict) -> None:
        """
        Print complete prompt if available.

        Args:
            data: The input data dictionary.
        """
        prompt = data.get("prompt", "")
        if prompt:
            print(f"\nComplete Message Sent to LLM:")
            print(prompt)

    def _display_output(self, entry: dict) -> None:
        """Display OUTPUT section."""
        timestamp = entry.get("timestamp", "N/A")
        data = entry.get("data", {})
        metadata = entry.get("metadata", {})

        self._print_output_header(timestamp)
        self._print_output_agent()
        self._print_llm_response(data, metadata)
        self._print_output_prompt(data)
        self._print_tool_calls(data)
        self._print_tool_results(data)

    def _print_output_header(self, timestamp: str) -> None:
        """
        Print OUTPUT section header.

        Args:
            timestamp: The timestamp of the output.
        """
        print(f"\n--- OUTPUT ---")
        print(f"Timestamp: {timestamp}")

    def _print_output_agent(self) -> None:
        """Print agent name for output section."""
        agent_name = "DefaultAgent"
        print(f"Agent: {agent_name}")

    def _print_llm_response(self, data: dict, metadata: dict) -> None:
        """
        Print LLM response.

        Args:
            data: The output data dictionary.
            metadata: The output metadata dictionary.
        """
        content = data.get("content", "")
        full_message = metadata.get("content", content)

        print(f"\nLLM Response:")
        print(full_message)

    def _print_output_prompt(self, data: dict) -> None:
        """
        Print prompt received by LLM if available.

        Args:
            data: The output data dictionary.
        """
        prompt = data.get("prompt", "")
        if prompt:
            print(f"\nPrompt Received by LLM:")
            print(prompt)

    def _print_tool_calls(self, data: dict) -> None:
        """
        Print tool calls if available.

        Args:
            data: The output data dictionary.
        """
        tool_calls = data.get("tool_calls")
        if not tool_calls:
            return

        print(f"\nTool Calls ({len(tool_calls)}):")
        for tc_idx, tc in enumerate(tool_calls, 1):
            self._print_single_tool_call(tc_idx, tc)

    def _print_single_tool_call(self, tc_idx: int, tc: dict) -> None:
        """
        Print a single tool call.

        Args:
            tc_idx: The tool call index.
            tc: The tool call dictionary.
        """
        tool_name = tc.get('name', 'unknown')
        tool_id = tc.get('id', 'N/A')
        args = tc.get('args', {})

        print(f"  [{tc_idx}] {tool_name}")
        print(f"      ID: {tool_id}")
        print(f"      Args: {args}")

    def _print_tool_results(self, data: dict) -> None:
        """
        Print tool results if available.

        Args:
            data: The output data dictionary.
        """
        tool_results = data.get("tool_results")
        if not tool_results:
            return

        print(f"\nTool Results ({len(tool_results)}):")
        for tr_idx, tr in enumerate(tool_results, 1):
            self._print_single_tool_result(tr_idx, tr)

    def _print_single_tool_result(self, tr_idx: int, tr: dict) -> None:
        """
        Print a single tool result.

        Args:
            tr_idx: The tool result index.
            tr: The tool result dictionary.
        """
        tool_name = tr.get('tool_name', 'unknown')
        success = tr.get('success', False)
        execution_time = tr.get('execution_time', 0)
        result = str(tr.get("result", ""))

        print(f"  [{tr_idx}] {tool_name}")
        print(f"      Success: {success}")
        print(f"      Execution Time: {execution_time:.3f}s")
        print(f"      Result: {result}")
