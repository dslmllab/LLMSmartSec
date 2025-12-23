"""
LLMGraphAgent - Neo4j Graph Database Agent for Smart Contract Pattern Matching.

This module queries the annotated Control Flow Graph stored in Neo4j to find
existing vulnerability patterns and insights from previous audits.
"""

import os
import re
from typing import Dict, List, Optional, Any
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


class LLMGraphAgent:
    """
    Agent for querying the Neo4j knowledge graph for smart contract patterns.

    The graph contains:
    - Contract nodes with source code and metadata
    - Vulnerability nodes with descriptions and severity
    - CodePattern nodes indicating vulnerable code patterns
    - Function and Variable nodes for code structure
    - Mitigation and Fix nodes for remediation
    - LLM_Insights nodes with AI analysis
    """

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not self.password:
            raise ValueError("NEO4J_PASSWORD not found in environment variables")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        """Close the database connection."""
        self.driver.close()

    def _run_query(self, query: str, parameters: Optional[Dict] = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def find_similar_contracts(self, code_snippet: str, limit: int = 5) -> List[Dict]:
        """
        Find contracts with similar code patterns.

        Args:
            code_snippet: A snippet of Solidity code to match
            limit: Maximum number of results

        Returns:
            List of similar contracts with their vulnerability labels
        """
        # Extract key identifiers from the code
        function_names = re.findall(r'function\s+(\w+)', code_snippet)
        variable_patterns = re.findall(r'(balances|owner|msg\.sender|tx\.origin|call|transfer|delegatecall)', code_snippet)

        query = """
        MATCH (c:Contract)-[:HAS_LABEL]->(l:Label)
        OPTIONAL MATCH (c)-[:DEFINES|PART_OF]-(f:Function)
        WHERE f.name IN $function_names OR l.name IN $patterns
        RETURN DISTINCT c.id as contract_id,
               collect(DISTINCT l.name) as labels,
               collect(DISTINCT f.name) as functions
        LIMIT $limit
        """

        return self._run_query(query, {
            "function_names": function_names,
            "patterns": variable_patterns,
            "limit": limit
        })

    def get_vulnerability_patterns(self, vulnerability_type: str) -> List[Dict]:
        """
        Get code patterns associated with a specific vulnerability type.

        Args:
            vulnerability_type: e.g., "reentrancy", "access-control", "arithmetic"

        Returns:
            List of code patterns and their descriptions
        """
        query = """
        MATCH (v:Vulnerability)-[:ASSOCIATED_WITH|INDICATES]-(cp:CodePattern)
        WHERE toLower(v.name) CONTAINS toLower($vuln_type)
           OR toLower(cp.vulnerability) CONTAINS toLower($vuln_type)
        RETURN v.name as vulnerability,
               v.description as description,
               v.severity as severity,
               cp.pattern as code_pattern,
               cp.description as pattern_description
        """

        return self._run_query(query, {"vuln_type": vulnerability_type})

    def get_mitigations(self, vulnerability_type: str) -> List[Dict]:
        """
        Get mitigation techniques for a vulnerability type.

        Args:
            vulnerability_type: The type of vulnerability

        Returns:
            List of mitigation techniques and fixes
        """
        query = """
        MATCH (v:Vulnerability)-[:MITIGATES|PREVENTS]-(m:MitigationTechnique)
        WHERE toLower(v.name) CONTAINS toLower($vuln_type)
        OPTIONAL MATCH (v)-[:FIXES|PATCHES]-(f:Fix)
        RETURN v.name as vulnerability,
               m.name as mitigation,
               f.description as fix_description,
               f.fixType as fix_type
        """

        return self._run_query(query, {"vuln_type": vulnerability_type})

    def get_contract_insights(self, contract_address: str) -> Dict[str, Any]:
        """
        Get all stored insights for a specific contract.

        Args:
            contract_address: The contract address to look up

        Returns:
            Dictionary with all related information
        """
        query = """
        MATCH (c:Contract {id: $address})
        OPTIONAL MATCH (c)-[:HAS_LABEL]->(l:Label)
        OPTIONAL MATCH (c)-[:DEFINES|PART_OF]-(f:Function)
        OPTIONAL MATCH (c)-[:HAS_VULNERABILITY|AFFECTED_BY]-(v:Vulnerability)
        OPTIONAL MATCH (c)-[:HAS_INSIGHT]-(i:LLM_Insights)
        RETURN c.id as address,
               c.name as name,
               collect(DISTINCT l.name) as labels,
               collect(DISTINCT f.name) as functions,
               collect(DISTINCT {
                   name: v.name,
                   severity: v.severity,
                   description: v.description
               }) as vulnerabilities,
               i as llm_insights
        """

        results = self._run_query(query, {"address": contract_address})
        return results[0] if results else {}

    def search_by_label(self, label: str, limit: int = 10) -> List[Dict]:
        """
        Search contracts by vulnerability label.

        Args:
            label: Vulnerability label (e.g., "reentrancy", "access-control")
            limit: Maximum results

        Returns:
            List of contracts with this label
        """
        query = """
        MATCH (c:Contract)-[:HAS_LABEL]->(l:Label)
        WHERE toLower(l.name) CONTAINS toLower($label)
        OPTIONAL MATCH (c)-[:HAS_INSIGHT]-(i:LLM_Insights)
        RETURN c.id as contract_id,
               l.name as label,
               i as insights
        LIMIT $limit
        """

        return self._run_query(query, {"label": label, "limit": limit})

    def get_all_vulnerability_types(self) -> List[str]:
        """Get all distinct vulnerability types in the database."""
        query = """
        MATCH (l:Label)
        RETURN DISTINCT l.name as label
        ORDER BY l.name
        """
        results = self._run_query(query)
        return [r["label"] for r in results]

    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics."""
        queries = {
            "contracts": "MATCH (c:Contract) RETURN count(c) as count",
            "vulnerabilities": "MATCH (v:Vulnerability) RETURN count(v) as count",
            "labels": "MATCH (l:Label) RETURN count(DISTINCT l.name) as count",
            "functions": "MATCH (f:Function) RETURN count(f) as count",
            "patterns": "MATCH (cp:CodePattern) RETURN count(cp) as count",
            "insights": "MATCH (i:LLM_Insights) RETURN count(i) as count",
        }

        stats = {}
        for name, query in queries.items():
            result = self._run_query(query)
            stats[name] = result[0]["count"] if result else 0

        return stats

    def check_pattern_match(self, code: str) -> Optional[Dict]:
        """
        Check if the code matches any known vulnerability patterns.

        This is the key function that determines if we can skip
        full LLM analysis by using cached results.

        Args:
            code: Solidity source code

        Returns:
            Matching pattern info if found, None otherwise
        """
        # Extract identifiable patterns from code
        patterns = []
        vuln_keywords = []

        # Check for reentrancy indicators
        if "call{value:" in code or "call.value(" in code or ".call(" in code:
            patterns.append("external_call")
            vuln_keywords.extend(["reentrancy", "reentrant", "nested", "external"])

        # Check for tx.origin (authentication bypass)
        if "tx.origin" in code:
            patterns.append("tx_origin")
            vuln_keywords.extend(["access", "authentication", "origin", "phishing"])

        # Check for delegatecall (proxy vulnerabilities)
        if "delegatecall" in code:
            patterns.append("delegatecall")
            vuln_keywords.extend(["delegate", "proxy", "storage", "collision"])

        # Check for balance updates (reentrancy/arithmetic)
        if re.search(r'balances\[.*\]\s*[-+]=', code):
            patterns.append("balance_update")
            vuln_keywords.extend(["balance", "arithmetic", "overflow", "underflow"])

        # Check for unchecked return values
        if re.search(r'\.(call|send|transfer)\s*\(', code) and "require" not in code:
            patterns.append("unchecked_call")
            vuln_keywords.extend(["unchecked", "return", "call"])

        # Check for selfdestruct
        if "selfdestruct" in code or "suicide" in code:
            patterns.append("selfdestruct")
            vuln_keywords.extend(["destruct", "suicide", "kill"])

        # Check for block.timestamp dependency
        if "block.timestamp" in code or "now" in code:
            patterns.append("timestamp")
            vuln_keywords.extend(["timestamp", "time", "manipulation"])

        if not patterns and not vuln_keywords:
            return None

        # Make keywords unique
        vuln_keywords = list(set(vuln_keywords))

        # Query for matching patterns - search across multiple fields
        query = """
        MATCH (v:Vulnerability)
        OPTIONAL MATCH (v)-[:ASSOCIATED_WITH|INDICATES]-(cp:CodePattern)
        OPTIONAL MATCH (v)-[:MITIGATES|PREVENTS]-(m:MitigationTechnique)
        WHERE any(kw IN $keywords WHERE
            toLower(v.name) CONTAINS kw OR
            toLower(v.description) CONTAINS kw OR
            toLower(cp.pattern) CONTAINS kw OR
            toLower(cp.description) CONTAINS kw
        )
        RETURN DISTINCT
               cp.pattern as pattern,
               v.name as vulnerability,
               v.severity as severity,
               v.description as description,
               collect(DISTINCT m.name) as mitigations
        LIMIT 10
        """

        results = self._run_query(query, {"keywords": vuln_keywords})

        # Also search by labels if no results
        if not results:
            label_query = """
            MATCH (c:Contract)-[:HAS_LABEL]->(l:Label)
            WHERE any(kw IN $keywords WHERE toLower(l.name) CONTAINS kw)
            OPTIONAL MATCH (c)-[:HAS_VULNERABILITY|AFFECTED_BY]-(v:Vulnerability)
            OPTIONAL MATCH (c)-[:HAS_INSIGHT]-(i:LLM_Insights)
            RETURN DISTINCT
                   l.name as label,
                   c.address as contract,
                   v.name as vulnerability,
                   v.severity as severity,
                   i.auditSummary as insights
            LIMIT 10
            """
            results = self._run_query(label_query, {"keywords": vuln_keywords})

        if results:
            return {
                "matched": True,
                "patterns_found": patterns,
                "keywords_searched": vuln_keywords,
                "database_matches": results
            }

        return None

    def store_audit_result(self, contract_address: str, audit_result: Dict):
        """
        Store audit results back into the graph for future reference.

        Args:
            contract_address: The audited contract address
            audit_result: The audit result dictionary
        """
        query = """
        MERGE (c:Contract {id: $address})
        MERGE (i:LLM_Insights {contract_id: $address})
        SET i.developer_review = $dev_review,
            i.hacker_review = $hack_review,
            i.auditor_review = $audit_review,
            i.final_report = $final_report,
            i.timestamp = datetime()
        MERGE (c)-[:HAS_INSIGHT]->(i)
        """

        perspectives = audit_result.get("perspectives", {})
        self._run_query(query, {
            "address": contract_address,
            "dev_review": perspectives.get("developer", ""),
            "hack_review": perspectives.get("ethical_hacker", ""),
            "audit_review": perspectives.get("auditor", ""),
            "final_report": audit_result.get("final_report", "")
        })

        print(f"Stored audit results for {contract_address}")


def main():
    """Example usage of LLMGraphAgent."""
    agent = LLMGraphAgent()

    try:
        # Get database statistics
        print("Database Statistics:")
        stats = agent.get_statistics()
        for key, value in stats.items():
            print(f"  {key}: {value}")

        # Get all vulnerability types
        print("\nVulnerability Types in Database:")
        vuln_types = agent.get_all_vulnerability_types()
        for vtype in vuln_types:
            print(f"  - {vtype}")

        # Search for reentrancy patterns
        print("\nSearching for reentrancy patterns...")
        patterns = agent.get_vulnerability_patterns("reentrancy")
        for p in patterns[:3]:
            print(f"  Pattern: {p.get('code_pattern', 'N/A')}")
            print(f"  Severity: {p.get('severity', 'N/A')}")

        # Check pattern match on sample code
        sample_code = """
        function withdraw() public {
            uint amount = balances[msg.sender];
            msg.sender.call{value: amount}("");
            balances[msg.sender] = 0;
        }
        """
        print("\nChecking sample code for patterns...")
        match = agent.check_pattern_match(sample_code)
        if match:
            print(f"  Match found! Patterns: {match['patterns_found']}")
        else:
            print("  No matching patterns found")

    finally:
        agent.close()


if __name__ == "__main__":
    main()
