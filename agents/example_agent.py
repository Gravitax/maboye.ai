"""
Example agent implementation

Demonstrates how to extend the base Agent class for specific use cases.
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.logger import logger
from agents.agent import Agent
from LLM import LLM, LLMConfig
from agents.config import AgentConfig
from agents.types import AgentInput, AgentOutput


class CodeReviewAgent(Agent):
    """
    Agent specialized for code review tasks

    Extends base Agent with code-specific prompts and validation.
    """

    def __init__(self, llm: LLM, config: Optional[AgentConfig] = None):
        """
        Initialize code review agent

        Args:
            llm: LLM instance
            config: Agent configuration
        """
        if config is None:
            config = AgentConfig(
                name="CodeReviewAgent",
                system_prompt="You are an expert code reviewer. "
                             "Analyze code for bugs, security issues, "
                             "performance problems, and style violations. "
                             "Provide clear, actionable feedback."
            )

        super().__init__(llm, config)

    def review_code(
        self,
        code: str,
        language: str = "python",
        focus_areas: Optional[list] = None
    ) -> AgentOutput:
        """
        Review code and provide feedback

        Args:
            code: Code to review
            language: Programming language
            focus_areas: Specific areas to focus on

        Returns:
            Review output
        """
        context = {
            "language": language,
            "code_length": len(code)
        }

        if focus_areas:
            context["focus_areas"] = ", ".join(focus_areas)

        prompt = f"Review the following {language} code:\n\n```{language}\n{code}\n```"

        if focus_areas:
            prompt += f"\n\nFocus on: {', '.join(focus_areas)}"

        input_data = AgentInput(
            prompt=prompt,
            context=context,
            metadata={"task": "code_review", "language": language}
        )

        return self.run(input_data)


class SummaryAgent(Agent):
    """
    Agent specialized for text summarization

    Extends base Agent with summarization-specific prompts.
    """

    def __init__(self, llm: LLM, config: Optional[AgentConfig] = None):
        """
        Initialize summary agent

        Args:
            llm: LLM instance
            config: Agent configuration
        """
        if config is None:
            config = AgentConfig(
                name="SummaryAgent",
                system_prompt="You are an expert at summarizing text. "
                             "Create clear, concise summaries that capture "
                             "key points and main ideas."
            )

        super().__init__(llm, config)

    def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        style: str = "bullet_points"
    ) -> AgentOutput:
        """
        Summarize text

        Args:
            text: Text to summarize
            max_length: Maximum summary length
            style: Summary style (bullet_points, paragraph, key_points)

        Returns:
            Summary output
        """
        context = {
            "text_length": len(text),
            "style": style
        }

        if max_length:
            context["max_length"] = max_length

        prompt = f"Summarize the following text"

        if style == "bullet_points":
            prompt += " as bullet points"
        elif style == "paragraph":
            prompt += " as a single paragraph"
        elif style == "key_points":
            prompt += " highlighting the key points"

        if max_length:
            prompt += f" (max {max_length} words)"

        prompt += f":\n\n{text}"

        input_data = AgentInput(
            prompt=prompt,
            context=context,
            metadata={"task": "summarization", "style": style}
        )

        return self.run(input_data)


def main():
    """Example usage of agents"""

    # Initialize LLM
    llm_config = LLMConfig(
        base_url="http://127.0.0.1:8000",
        model="gpt-4",
        temperature=0.7
    )
    llm = LLM(llm_config)

    # Example 1: Code Review Agent
    print("\n" + "="*80)
    print("CODE REVIEW AGENT EXAMPLE")
    print("="*80 + "\n")

    code_agent = CodeReviewAgent(llm)

    sample_code = """
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item['price']
    return total
"""

    try:
        result = code_agent.review_code(
            code=sample_code,
            language="python",
            focus_areas=["performance", "style"]
        )

        print(f"Success: {result.success}")
        print(f"Review:\n{result.response}")
        print(f"\nStats: {code_agent.get_stats()}")

    except Exception as e:
        logger.error("EXAMPLE", "Code review failed", {"error": str(e)})

    # Example 2: Summary Agent
    print("\n" + "="*80)
    print("SUMMARY AGENT EXAMPLE")
    print("="*80 + "\n")

    summary_agent = SummaryAgent(llm)

    sample_text = """
    Artificial intelligence is transforming software development.
    AI-powered tools can now write code, review pull requests,
    debug issues, and even suggest architectural improvements.
    However, human oversight remains critical to ensure quality,
    security, and alignment with business requirements.
    """

    try:
        result = summary_agent.summarize(
            text=sample_text,
            style="bullet_points",
            max_length=50
        )

        print(f"Success: {result.success}")
        print(f"Summary:\n{result.response}")
        print(f"\nStats: {summary_agent.get_stats()}")

    except Exception as e:
        logger.error("EXAMPLE", "Summarization failed", {"error": str(e)})

    # Cleanup
    llm.close()


if __name__ == "__main__":
    main()
