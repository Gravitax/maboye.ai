#!/usr/bin/env python3
"""
Main application entry point

AI Assistant with Orchestrated Agent System
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from srcs.logger import logger
from srcs.terminal import Terminal
from srcs.orchestrator import Orchestrator
from LLM import LLM, LLMConfig
from tools.implementations import register_all_tools


class Application:
    """Main application with interactive terminal and orchestrated agents"""

    def __init__(self):
        """Initialize application"""
        self.llm = None
        self.orchestrator = None
        self.terminal = None

    def setup(self):
        """Setup LLM and orchestrator"""
        logger.info("APP", "Setting up application")

        # Register all tools
        register_all_tools()
        logger.info("APP", "Tools registered")

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

        # Create orchestrator with all agents
        self.orchestrator = Orchestrator(
            llm=self.llm,
            enable_logging=True
        )
        logger.info("APP", "Orchestrator initialized")

        # Create terminal
        self.terminal = Terminal(prompt="You: ")
        self._register_commands()

    def _register_commands(self):
        """Register custom commands"""
        self.terminal.register_command(
            "reset",
            self._cmd_reset,
            "Reset orchestrator state"
        )

        self.terminal.register_command(
            "history",
            self._cmd_history,
            "Show query history"
        )

        self.terminal.register_command(
            "memory",
            self._cmd_memory,
            "Show memory statistics"
        )

    def _cmd_reset(self, args: list) -> bool:
        """Reset orchestrator state"""
        self.orchestrator.reset()
        print("\nOrchestrator state reset\n")
        logger.info("APP", "Orchestrator reset by user")
        return True

    def _cmd_history(self, args: list) -> bool:
        """Show query history"""
        history = self.orchestrator.get_query_history(count=10)

        if not history:
            print("\nNo query history\n")
            return True

        print("\nQuery History:")
        print("-" * 60)

        for i, query in enumerate(history, 1):
            print(f"{i}. {query[:100]}{'...' if len(query) > 100 else ''}")

        print("-" * 60)
        print()

        return True

    def _cmd_memory(self, args: list) -> bool:
        """Show memory statistics"""
        stats = self.orchestrator.get_memory_stats()

        print("\nMemory Statistics:")
        print("-" * 60)

        for mem_type, data in stats.items():
            print(f"\n{mem_type.upper()}:")
            print(f"  Entries: {data['size']}")
            print(f"  Status: {'Empty' if data['is_empty'] else 'Has data'}")

        print("-" * 60)
        print()

        return True

    def handle_input(self, user_input: str):
        """
        Handle user input and process through orchestrator

        Args:
            user_input: User's message
        """
        try:
            # Process through orchestrator
            output = self.orchestrator.process_query(user_input)

            if output.success:
                print(f"\nAssistant: {output.response}\n")
            else:
                print(f"\nError: {output.error}\n")
                logger.error("APP", "Query processing failed", {
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
