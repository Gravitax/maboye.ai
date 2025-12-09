import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from core.logger import logger
from cli.terminal import Terminal
from core.llm_wrapper import LLMWrapperConfig
from core.orchestrator import Orchestrator
from agents.config import AgentConfig


class Application:
    """Main application with an interactive terminal and an orchestrated agent system."""

    def __init__(self):
        """Initialize application."""
        self.orchestrator = None
        self.terminal = None

    def setup(self):
        """Setup all components required for the orchestrator and agent to run."""
        logger.info("APP", "Setting up application")

        # 1. Define LLM Configuration
        llm_config = LLMWrapperConfig(
            base_url="http://127.0.0.1:8000",
            model="gpt-4",
            temperature=0.1,
            timeout=120
        )

        # 2. Define Agent Configuration
        agent_config = AgentConfig(
            name="DefaultAgent",
            system_prompt="You are a helpful AI assistant. You have access to a variety of tools to help you answer questions and perform tasks. Think step-by-step and use the tools provided when necessary.",
            max_agent_turns=10,
            max_history_turns=10,
        )

        # 3. Initialize the Orchestrator with configurations
        self.orchestrator = Orchestrator(
            llm_config=llm_config,
            agent_config=agent_config,
        )
        logger.info("APP", "Orchestrator initialized and components set up.")

        # 4. Setup the terminal for user interaction
        self.terminal = Terminal()
        self._register_commands()

    def _register_commands(self):
        """Register custom commands for the terminal."""
        self.terminal.register_command(
            "reset",
            self._cmd_reset,
            "Reset the conversation history."
        )
        self.terminal.register_command(
            "memory",
            self._cmd_memory,
            "Show memory statistics."
        )
        self.terminal.register_command(
            "tools",
            self._cmd_tools,
            "List available tools."
        )
        self.terminal.register_command(
            "agent",
            self._cmd_agent_info,
            "Show agent configuration."
        )

    def _cmd_reset(self, args: list) -> bool:
        """Resets the conversation memory."""
        self.orchestrator.reset_conversation()
        print("\nConversation history has been reset.\n")
        logger.info("APP", "Conversation memory reset by user.")
        return True

    def _cmd_memory(self, args: list) -> bool:
        """Shows memory statistics."""
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

    def _cmd_tools(self, args: list) -> bool:
        """Lists available tools."""
        tools_info = self.orchestrator.get_tool_info()
        print("\nAvailable Tools:")
        print("-" * 60)
        if not tools_info:
            print("No tools registered.")
        else:
            for tool in tools_info:
                print(f"- {tool['name']}: {tool['description']} (Category: {tool['category']})")
                if tool['parameters']:
                    print("  Parameters:")
                    for param in tool['parameters']:
                        req = " (required)" if param['required'] else ""
                        default = f" (default: {param['default']})" if param['default'] is not None else ""
                        print(f"    - {param['name']} ({param['type']}){req}{default}: {param['description']}")
        print("-" * 60)
        print()
        return True

    def _cmd_agent_info(self, args: list) -> bool:
        """Shows agent configuration."""
        agent_info = self.orchestrator.get_agent_info()
        print("\nAgent Information:")
        print("-" * 60)
        for key, value in agent_info.items():
            print(f"- {key}: {value}")
        print("-" * 60)
        print()
        return True

    def handle_input(self, user_input: str):
        """
        Handle user input by passing it to the orchestrator.

        Args:
            user_input: The user's message from the terminal.
        """
        try:
            print("\nAssistant is thinking...\n", end="", flush=True)
            output = self.orchestrator.process_user_input(user_input)

            print("\r" + " " * 30 + "\r", end="")

            if output.success:
                print(f"Assistant: {output.response}\n")
            else:
                print(f"\nError: {output.error}\n")
                logger.error("APP", "Orchestrator processing failed", {"error": output.error})

        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}\n")
            logger.error("APP", "Input handling error", {"error": str(e)})

    def run(self):
        """Run the main application loop."""
        logger.separator("Application Starting")

        try:
            self.setup()



            self.terminal.run(input_handler=self.handle_input)

            logger.separator("Application Complete")
            return 0

        except KeyboardInterrupt:
            print("\nExiting...")
            logger.info("APP", "Application interrupted by user")
            return 130

        except Exception as e:
            logger.critical("APP", "Fatal application error", {"error": str(e)})
            print(f"\nA fatal error occurred: {e}\n")
            return 1


def main():
    """Main entry point"""
    app = Application()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())
