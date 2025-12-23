"""
Vector Store Manager for LLMSmartSec.

This module manages OpenAI Vector Stores for RAG (Retrieval-Augmented Generation)
to provide each assistant with domain-specific knowledge.
"""

import os
import time
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class VectorStoreManager:
    """Manages Vector Stores for the LLMSmartSec assistants."""

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.client = OpenAI(api_key=self.api_key)
        self.vector_stores: Dict[str, str] = {}  # Maps role to vector_store_id

    def create_vector_store(self, name: str, file_paths: List[str]) -> str:
        """
        Create a vector store and upload files to it.

        Args:
            name: Name for the vector store
            file_paths: List of file paths to upload

        Returns:
            The vector store ID
        """
        # Create vector store
        vector_store = self.client.beta.vector_stores.create(name=name)
        print(f"Created vector store: {name} (ID: {vector_store.id})")

        # Upload files
        if file_paths:
            file_ids = []
            for path in file_paths:
                if os.path.exists(path):
                    with open(path, "rb") as f:
                        file = self.client.files.create(file=f, purpose="assistants")
                        file_ids.append(file.id)
                        print(f"  Uploaded: {os.path.basename(path)}")
                else:
                    print(f"  Warning: File not found: {path}")

            # Add files to vector store
            if file_ids:
                batch = self.client.beta.vector_stores.file_batches.create(
                    vector_store_id=vector_store.id,
                    file_ids=file_ids
                )

                # Wait for processing
                while batch.status in ["in_progress", "queued"]:
                    time.sleep(1)
                    batch = self.client.beta.vector_stores.file_batches.retrieve(
                        vector_store_id=vector_store.id,
                        batch_id=batch.id
                    )

                print(f"  Files processed: {batch.file_counts.completed}/{batch.file_counts.total}")

        return vector_store.id

    def setup_assistant_stores(self, docs_dir: Optional[str] = None) -> Dict[str, str]:
        """
        Set up vector stores for all four assistants.

        Args:
            docs_dir: Base directory containing subdirectories for each assistant's docs

        Returns:
            Dictionary mapping assistant role to vector store ID
        """
        if docs_dir is None:
            docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

        # Define document categories for each assistant
        assistant_docs = {
            "LLMDev": {
                "name": "Smart Contract Development Knowledge",
                "subdirs": ["solidity_docs", "best_practices", "design_patterns"],
                "extensions": [".md", ".txt", ".sol", ".pdf"]
            },
            "LLMeHack": {
                "name": "Smart Contract Vulnerabilities Knowledge",
                "subdirs": ["vulnerabilities", "exploits", "cwe_mappings"],
                "extensions": [".md", ".txt", ".json", ".pdf"]
            },
            "LLMAudit": {
                "name": "Smart Contract Auditing Knowledge",
                "subdirs": ["audit_reports", "audit_checklists", "standards"],
                "extensions": [".md", ".txt", ".pdf"]
            },
            "LLMReport": {
                "name": "Audit Report Templates",
                "subdirs": ["report_templates", "examples"],
                "extensions": [".md", ".txt", ".pdf"]
            }
        }

        for role, config in assistant_docs.items():
            files = []

            # Collect files from subdirectories
            for subdir in config["subdirs"]:
                subdir_path = os.path.join(docs_dir, subdir)
                if os.path.exists(subdir_path):
                    for filename in os.listdir(subdir_path):
                        if any(filename.endswith(ext) for ext in config["extensions"]):
                            files.append(os.path.join(subdir_path, filename))

            # Create vector store (even if no files, for future use)
            print(f"\nSetting up vector store for {role}...")
            store_id = self.create_vector_store(config["name"], files)
            self.vector_stores[role] = store_id

        return self.vector_stores

    def create_sample_docs(self, docs_dir: Optional[str] = None):
        """
        Create sample documentation files for each assistant.
        This is useful for initial setup and testing.
        """
        if docs_dir is None:
            docs_dir = os.path.join(os.path.dirname(__file__), "..", "docs")

        # Create directory structure
        subdirs = [
            "solidity_docs", "best_practices", "design_patterns",
            "vulnerabilities", "exploits", "cwe_mappings",
            "audit_reports", "audit_checklists", "standards",
            "report_templates", "examples"
        ]

        for subdir in subdirs:
            os.makedirs(os.path.join(docs_dir, subdir), exist_ok=True)

        # Create sample vulnerability documentation
        vuln_doc = """# Common Smart Contract Vulnerabilities

## 1. Reentrancy (SWC-107)
A reentrancy attack occurs when a contract makes an external call before updating its state.

### Example Vulnerable Code:
```solidity
function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount);
    msg.sender.call{value: amount}("");  // External call before state update
    balances[msg.sender] -= amount;      // State updated after external call
}
```

### Mitigation:
- Use checks-effects-interactions pattern
- Use ReentrancyGuard from OpenZeppelin
- Update state before external calls

## 2. Integer Overflow/Underflow (SWC-101)
Prior to Solidity 0.8.0, arithmetic operations could overflow without reverting.

### Mitigation:
- Use Solidity 0.8.0+ (built-in overflow checks)
- Use SafeMath library for older versions

## 3. Access Control (SWC-105)
Missing or improper access control allows unauthorized users to execute privileged functions.

### Mitigation:
- Use OpenZeppelin's Ownable or AccessControl
- Always validate msg.sender
- Never rely on tx.origin for authorization

## 4. Unchecked External Calls (SWC-104)
Low-level calls (call, delegatecall, staticcall) don't revert on failure.

### Mitigation:
- Always check return values
- Use higher-level methods when possible
- Consider using OpenZeppelin's Address library
"""

        with open(os.path.join(docs_dir, "vulnerabilities", "common_vulnerabilities.md"), "w") as f:
            f.write(vuln_doc)

        # Create sample audit checklist
        checklist_doc = """# Smart Contract Audit Checklist

## Access Control
- [ ] Check for proper use of modifiers (onlyOwner, etc.)
- [ ] Verify no functions are unintentionally public
- [ ] Check for tx.origin usage (should use msg.sender)

## Arithmetic
- [ ] Verify Solidity version >= 0.8.0 or SafeMath usage
- [ ] Check for division by zero possibilities
- [ ] Validate user inputs for reasonable ranges

## Reentrancy
- [ ] Check for state changes after external calls
- [ ] Verify use of ReentrancyGuard where needed
- [ ] Review all external calls and callbacks

## Gas & DoS
- [ ] Check for unbounded loops
- [ ] Verify pull over push pattern for payments
- [ ] Check for gas limit issues in batch operations

## External Interactions
- [ ] Verify all external call return values are checked
- [ ] Check for proper handling of failed transfers
- [ ] Review delegatecall usage carefully

## Data Validation
- [ ] Verify input validation on all public functions
- [ ] Check for proper require/revert messages
- [ ] Validate addresses are not zero address
"""

        with open(os.path.join(docs_dir, "audit_checklists", "audit_checklist.md"), "w") as f:
            f.write(checklist_doc)

        # Create sample report template
        report_template = """# Smart Contract Audit Report Template

## 1. Executive Summary
Brief overview of the audit scope, methodology, and key findings.

## 2. Scope
- Contract Name:
- Contract Address:
- Commit Hash:
- Audit Period:

## 3. Findings Summary

| Severity | Count |
|----------|-------|
| Critical | 0     |
| High     | 0     |
| Medium   | 0     |
| Low      | 0     |
| Info     | 0     |

## 4. Detailed Findings

### [SEVERITY]-[ID]: Finding Title

**Severity:** Critical/High/Medium/Low/Informational

**Location:** `ContractName.sol:LineNumber`

**Description:**
Detailed description of the vulnerability.

**Impact:**
Potential consequences if exploited.

**Recommendation:**
Steps to fix the issue.

**Status:** Open/Acknowledged/Fixed

## 5. Recommendations
General recommendations for improving the contract.

## 6. Conclusion
Final assessment of the contract's security posture.
"""

        with open(os.path.join(docs_dir, "report_templates", "report_template.md"), "w") as f:
            f.write(report_template)

        print(f"Created sample documentation in: {docs_dir}")

    def delete_vector_store(self, store_id: str):
        """Delete a vector store."""
        try:
            self.client.beta.vector_stores.delete(store_id)
            print(f"Deleted vector store: {store_id}")
        except Exception as e:
            print(f"Error deleting vector store {store_id}: {e}")

    def cleanup_all(self):
        """Delete all created vector stores."""
        for role, store_id in self.vector_stores.items():
            self.delete_vector_store(store_id)
        self.vector_stores.clear()


def main():
    """Example usage of VectorStoreManager."""
    manager = VectorStoreManager()

    # Create sample documentation
    print("Creating sample documentation...")
    manager.create_sample_docs()

    # Set up vector stores
    print("\nSetting up vector stores...")
    stores = manager.setup_assistant_stores()

    print("\nVector Stores Created:")
    for role, store_id in stores.items():
        print(f"  {role}: {store_id}")

    # Cleanup (uncomment to delete stores after testing)
    # print("\nCleaning up...")
    # manager.cleanup_all()


if __name__ == "__main__":
    main()
