"""
LLMSmartSec - Multi-Assistant Audit Pipeline

This module implements the core audit pipeline with four AI assistants:
- LLMDev: Developer perspective analysis
- LLMeHack: Ethical hacker vulnerability scanning
- LLMAudit: Auditor report generation
- LLMReport: Final report consolidation
"""

import os
import time
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class LLMSmartSecPipeline:
    """Main pipeline for smart contract security auditing using multiple LLM perspectives."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4"

        # Load prompts from files
        self.prompts = self._load_prompts()

        # Assistant IDs (will be created or retrieved)
        self.assistants = {}

    def _load_prompts(self) -> dict:
        """Load prompt templates from the Prompts directory."""
        prompts = {}
        prompts_dir = os.path.join(os.path.dirname(__file__), "Prompts")

        prompt_files = {
            "LLMDev": "LLMDev",
            "LLMeHack": "LLMeHack",
            "LLMAudit": "LLMAudit",
            "LLMReport": "Reportgen"
        }

        for key, filename in prompt_files.items():
            filepath = os.path.join(prompts_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "r") as f:
                    prompts[key] = f.read().strip()
            else:
                prompts[key] = self._get_default_prompt(key)

        return prompts

    def _get_default_prompt(self, role: str) -> str:
        """Get default prompts if file doesn't exist."""
        defaults = {
            "LLMDev": """You are an expert smart contract developer. Analyze the provided smart contract code from a developer's perspective:
1. Read each line of code and understand the execution paths
2. Assess the design patterns and architecture
3. Review functionality and business logic
4. Evaluate gas efficiency
5. Provide detailed peer review comments""",

            "LLMeHack": """You are an experienced ethical hacker. Analyze the smart contract for vulnerabilities:
1. Look for reentrancy, integer overflow/underflow, access control issues
2. Check for timestamp dependence, front-running, DoS vulnerabilities
3. Identify logic errors, insecure randomness, unchecked external calls
4. For each vulnerability: identify the failure point, explain the attack, assess impact, suggest fixes""",

            "LLMAudit": """You are a smart contract auditor. Generate a comprehensive audit report with:
1. Introduction and scope
2. Executive summary of findings
3. Contract overview
4. Findings categorized by severity (Critical, High, Medium, Low)
5. Recommendations for each finding""",

            "LLMReport": """You are a report consolidator. Combine the perspectives from the Developer, Ethical Hacker, and Auditor into a final comprehensive audit report with:
1. Executive Summary
2. Developer Analysis Summary
3. Security Vulnerabilities Found
4. Risk Assessment
5. Prioritized Recommendations
6. Conclusion"""
        }
        return defaults.get(role, "")

    def create_assistants(self, vector_store_ids: Optional[dict] = None):
        """Create or retrieve the four AI assistants."""
        assistant_configs = [
            ("LLMDev", "Smart Contract Developer Assistant", self.prompts["LLMDev"]),
            ("LLMeHack", "Ethical Hacker Assistant", self.prompts["LLMeHack"]),
            ("LLMAudit", "Smart Contract Auditor Assistant", self.prompts["LLMAudit"]),
            ("LLMReport", "Report Generator Assistant", self.prompts["LLMReport"]),
        ]

        for key, name, instructions in assistant_configs:
            tools = [{"type": "code_interpreter"}]

            # Add file search if vector store is provided
            if vector_store_ids and key in vector_store_ids:
                tools.append({"type": "file_search"})

            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=self.model,
                tools=tools
            )
            self.assistants[key] = assistant
            print(f"Created assistant: {name} (ID: {assistant.id})")

        return self.assistants

    def _run_assistant(self, assistant_key: str, content: str, context: str = "") -> str:
        """Run a single assistant and get response."""
        assistant = self.assistants.get(assistant_key)
        if not assistant:
            raise ValueError(f"Assistant {assistant_key} not found. Call create_assistants() first.")

        # Create thread with message
        full_content = content
        if context:
            full_content = f"{context}\n\n---\n\nSmart Contract Code:\n{content}"

        thread = self.client.beta.threads.create(
            messages=[{"role": "user", "content": full_content}]
        )

        # Create and poll run
        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # Wait for completion
        while run.status not in ["completed", "failed", "expired"]:
            time.sleep(2)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            print(f"  {assistant_key} status: {run.status}")

        if run.status != "completed":
            return f"Error: Assistant {assistant_key} run {run.status}"

        # Get messages
        messages = self.client.beta.threads.messages.list(
            thread_id=thread.id,
            run_id=run.id
        )

        # Extract assistant response
        for message in messages.data:
            if message.role == "assistant":
                for content_block in message.content:
                    if hasattr(content_block, 'text'):
                        return content_block.text.value

        return "No response received"

    def audit_contract(self, contract_code: str, contract_address: str = "Unknown") -> dict:
        """
        Run the full audit pipeline on a smart contract.

        Args:
            contract_code: The Solidity source code to audit
            contract_address: Optional contract address for reference

        Returns:
            Dictionary containing all perspectives and final report
        """
        results = {
            "contract_address": contract_address,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "perspectives": {},
            "final_report": ""
        }

        print(f"\n{'='*60}")
        print(f"Starting LLMSmartSec Audit for: {contract_address}")
        print(f"{'='*60}\n")

        # Step 1: Developer Review
        print("Step 1/4: Running LLMDev (Developer Perspective)...")
        dev_review = self._run_assistant("LLMDev", contract_code)
        results["perspectives"]["developer"] = dev_review
        print("  Developer review complete.\n")

        # Step 2: Ethical Hacker Scan
        print("Step 2/4: Running LLMeHack (Ethical Hacker Perspective)...")
        hack_review = self._run_assistant("LLMeHack", contract_code)
        results["perspectives"]["ethical_hacker"] = hack_review
        print("  Ethical hacker scan complete.\n")

        # Step 3: Auditor Analysis
        print("Step 3/4: Running LLMAudit (Auditor Perspective)...")
        context = f"""Developer Review:\n{dev_review}\n\nEthical Hacker Findings:\n{hack_review}"""
        audit_review = self._run_assistant("LLMAudit", contract_code, context)
        results["perspectives"]["auditor"] = audit_review
        print("  Auditor analysis complete.\n")

        # Step 4: Final Report Consolidation
        print("Step 4/4: Running LLMReport (Report Generation)...")
        all_perspectives = f"""
Contract Address: {contract_address}

=== DEVELOPER PERSPECTIVE ===
{dev_review}

=== ETHICAL HACKER PERSPECTIVE ===
{hack_review}

=== AUDITOR PERSPECTIVE ===
{audit_review}
"""
        final_report = self._run_assistant("LLMReport", all_perspectives)
        results["final_report"] = final_report
        print("  Final report generated.\n")

        print(f"{'='*60}")
        print("Audit Complete!")
        print(f"{'='*60}\n")

        return results

    def cleanup_assistants(self):
        """Delete created assistants to avoid clutter."""
        for key, assistant in self.assistants.items():
            try:
                self.client.beta.assistants.delete(assistant.id)
                print(f"Deleted assistant: {key}")
            except Exception as e:
                print(f"Error deleting {key}: {e}")


def main():
    """Example usage of the LLMSmartSec pipeline."""
    # Sample contract for testing
    sample_contract = """
pragma solidity ^0.8.0;

contract VulnerableContract {
    address public owner;
    mapping(address => uint256) private balances;

    constructor() {
        owner = msg.sender;
    }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdrawAll() public {
        uint256 amount = balances[msg.sender];
        payable(msg.sender).transfer(amount);
        balances[msg.sender] = 0;
    }

    function updateOwner(address _newOwner) public {
        if (tx.origin != msg.sender) {
            owner = _newOwner;
        }
    }
}
"""

    # Initialize pipeline
    pipeline = LLMSmartSecPipeline()

    # Create assistants
    pipeline.create_assistants()

    try:
        # Run audit
        results = pipeline.audit_contract(sample_contract, "0xSampleAddress")

        # Print final report
        print("\n" + "="*60)
        print("FINAL AUDIT REPORT")
        print("="*60)
        print(results["final_report"])

    finally:
        # Cleanup
        pipeline.cleanup_assistants()


if __name__ == "__main__":
    main()
