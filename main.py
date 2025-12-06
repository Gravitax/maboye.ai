#!/usr/bin/env python3
"""
Main application entry point

Interactive terminal for agent system with LLM backend integration.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from tools.logger import logger
from tools.terminal import Terminal
from LLM import LLM, LLMConfig
from agents import Agent, AgentConfig


class Application:
    """Main application with interactive terminal"""

    def __init__(self):
        """Initialize application"""
        self.llm = None
        self.agent = None
        self.terminal = None

    def setup(self):
        """Setup LLM and agent"""
        logger.info("APP", "Setting up application")

        # Configure LLM connection
        llm_config = LLMConfig(
            base_url="http://127.0.0.1:8000",
            model="gpt-4",
            temperature=0.7,
            timeout=30
        )

        # Create LLM instance
        self.llm = LLM(llm_config)
        logger.info("APP", "LLM connection established")

        # Configure agent
        agent_config = AgentConfig(
            name="Assistant",
            system_prompt="You are a helpful AI assistant.",
            enable_logging=False  # Reduce log noise
        )

        # Create agent
        self.agent = Agent(self.llm, agent_config)
        logger.info("APP", "Agent initialized")

        # Create terminal
        self.terminal = Terminal(prompt="You: ")
        self._register_commands()

    def _register_commands(self):
        """Register custom commands"""
        self.terminal.register_command(
            "stats",
            self._cmd_stats,
            "Show agent statistics"
        )

        self.terminal.register_command(
            "reset",
            self._cmd_reset,
            "Reset agent state"
        )

        self.terminal.register_command(
            "history",
            self._cmd_history,
            "Show conversation history"
        )

    def _cmd_stats(self, args: list) -> bool:
        """Show agent statistics"""
        stats = self.agent.get_stats()

        print("\nAgent Statistics:")
        print(f"  Name: {stats['name']}")
        print(f"  Executions: {stats['executions']}")
        print(f"  History size: {stats['history_size']}")
        print(f"  LLM requests: {stats['llm_requests']}")
        print()

        return True

    def _cmd_reset(self, args: list) -> bool:
        """Reset agent state"""
        self.agent.reset()
        print("\nAgent state reset\n")
        logger.info("APP", "Agent reset by user")
        return True

    def _cmd_history(self, args: list) -> bool:
        """Show conversation history"""
        history = self.agent.get_history()

        if not history:
            print("\nNo conversation history\n")
            return True

        print("\nConversation History:")
        print("-" * 60)

        for entry in history:
            print(f"\n[{entry['timestamp']}]")
            print(f"Input: {entry['input'][:100]}...")
            print(f"Response: {entry['response'][:100]}...")
            print(f"Tokens: {entry['tokens']}")

        print("-" * 60)
        print()

        return True

    def handle_input(self, user_input: str):
        """
        Handle user input and query agent

        Args:
            user_input: User's message
        """
        try:
            # Query agent
            output = self.agent.run(user_input)

            if output.success:
                print(f"\nAssistant: {output.response}\n")
            else:
                print(f"\nError: {output.error}\n")
                logger.error("APP", "Agent query failed", {
                    "error": output.error
                })

        except Exception as e:
            print(f"\nError: {e}\n")
            logger.error("APP", "Input handling error", {"error": str(e)})

    def run(self):
        """Run main application"""
        logger.separator("Application Starting")

        try:
            self.setup()

            # Show welcome message
            self.terminal.print_header("AI Assistant")
            print("Type your message and press Enter to chat")
            print("Type /help for available commands")
            print()

            # Start interactive loop
            self.terminal.run(input_handler=self.handle_input)

            logger.separator("Application Complete")
            return 0

        except KeyboardInterrupt:
            print()
            logger.info("APP", "Application interrupted by user")
            return 130

        except Exception as e:
            logger.error("APP", "Application error", {"error": str(e)})
            print(f"\nFatal error: {e}\n")
            return 1

        finally:
            # Cleanup
            if self.llm:
                self.llm.close()


def main():
    """Main entry point"""
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
