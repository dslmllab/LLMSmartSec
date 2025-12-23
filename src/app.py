"""
LLMSmartSec - Streamlit Web Application

This is the main user interface for the LLMSmartSec smart contract auditing system.
Users can input a contract address or paste code directly for security analysis.
"""

import streamlit as st
import time
import json
from typing import Optional

# Import our modules
from audit_pipeline import LLMSmartSecPipeline
from etherscan_client import EtherscanClient
from graph_agent import LLMGraphAgent
from report_generator import ReportGenerator


def init_session_state():
    """Initialize session state variables."""
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = None
    if "assistants_created" not in st.session_state:
        st.session_state.assistants_created = False
    if "audit_results" not in st.session_state:
        st.session_state.audit_results = None
    if "graph_agent" not in st.session_state:
        st.session_state.graph_agent = None


def create_pipeline():
    """Create and initialize the audit pipeline."""
    if st.session_state.pipeline is None:
        with st.spinner("Initializing LLMSmartSec pipeline..."):
            st.session_state.pipeline = LLMSmartSecPipeline()

    if not st.session_state.assistants_created:
        with st.spinner("Creating AI Assistants..."):
            st.session_state.pipeline.create_assistants()
            st.session_state.assistants_created = True


def get_graph_agent():
    """Get or create the graph agent."""
    if st.session_state.graph_agent is None:
        try:
            st.session_state.graph_agent = LLMGraphAgent()
        except Exception as e:
            st.warning(f"Could not connect to Neo4j: {e}")
            return None
    return st.session_state.graph_agent


def fetch_contract_code(address: str, network: str) -> Optional[str]:
    """Fetch contract source code from Etherscan."""
    try:
        client = EtherscanClient(network=network)
        result = client.get_contract_source(address)

        if result["success"]:
            return result["source_code"]
        else:
            st.error(f"Error fetching contract: {result['error']}")
            return None
    except Exception as e:
        st.error(f"Etherscan API error: {e}")
        return None


def check_existing_patterns(code: str) -> Optional[dict]:
    """Check if code matches existing patterns in the knowledge graph."""
    agent = get_graph_agent()
    if agent:
        try:
            return agent.check_pattern_match(code)
        except Exception as e:
            st.warning(f"Pattern matching unavailable: {e}")
    return None


def run_audit(code: str, address: str):
    """Run the full audit pipeline."""
    create_pipeline()

    # Check for existing patterns first
    pattern_match = check_existing_patterns(code)

    if pattern_match and pattern_match.get("matched"):
        st.info("Found matching patterns in knowledge base!")
        with st.expander("View Cached Pattern Matches"):
            st.json(pattern_match)

    # Run full audit
    progress_bar = st.progress(0)
    status_text = st.empty()

    try:
        status_text.text("Starting audit...")
        progress_bar.progress(10)

        # Create a placeholder for real-time updates
        results_placeholder = st.empty()

        status_text.text("Running Developer Analysis (LLMDev)...")
        progress_bar.progress(25)

        status_text.text("Running Security Scan (LLMeHack)...")
        progress_bar.progress(50)

        status_text.text("Running Audit Analysis (LLMAudit)...")
        progress_bar.progress(75)

        # Run the actual audit
        results = st.session_state.pipeline.audit_contract(code, address)

        status_text.text("Generating Final Report...")
        progress_bar.progress(90)

        # Store results in graph database
        agent = get_graph_agent()
        if agent:
            try:
                agent.store_audit_result(address, results)
            except Exception as e:
                st.warning(f"Could not store results in graph database: {e}")

        progress_bar.progress(100)
        status_text.text("Audit Complete!")

        st.session_state.audit_results = results

    except Exception as e:
        st.error(f"Audit failed: {e}")
        progress_bar.empty()
        status_text.empty()


def display_results():
    """Display audit results."""
    results = st.session_state.audit_results

    if not results:
        return

    st.success("Audit Complete!")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Final Report",
        "Developer View",
        "Hacker View",
        "Auditor View"
    ])

    with tab1:
        st.markdown("## Final Audit Report")
        st.markdown(results.get("final_report", "No report generated"))

    with tab2:
        st.markdown("## Developer Perspective (LLMDev)")
        st.markdown(results["perspectives"].get("developer", "No analysis available"))

    with tab3:
        st.markdown("## Ethical Hacker Perspective (LLMeHack)")
        st.markdown(results["perspectives"].get("ethical_hacker", "No analysis available"))

    with tab4:
        st.markdown("## Auditor Perspective (LLMAudit)")
        st.markdown(results["perspectives"].get("auditor", "No analysis available"))

    # Export options
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Download as PDF"):
            try:
                generator = ReportGenerator()
                pdf_path = generator.generate_pdf(results)
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Download PDF",
                        f,
                        file_name="audit_report.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"PDF generation failed: {e}")

    with col2:
        st.download_button(
            "Download as JSON",
            json.dumps(results, indent=2),
            file_name="audit_report.json",
            mime="application/json"
        )

    with col3:
        markdown_report = f"""# Smart Contract Audit Report

**Contract:** {results.get('contract_address', 'Unknown')}
**Date:** {results.get('timestamp', 'Unknown')}

## Final Report
{results.get('final_report', '')}

## Developer Analysis
{results['perspectives'].get('developer', '')}

## Security Analysis
{results['perspectives'].get('ethical_hacker', '')}

## Auditor Analysis
{results['perspectives'].get('auditor', '')}
"""
        st.download_button(
            "Download as Markdown",
            markdown_report,
            file_name="audit_report.md",
            mime="text/markdown"
        )


def main():
    """Main application."""
    st.set_page_config(
        page_title="LLMSmartSec",
        page_icon="🔒",
        layout="wide"
    )

    init_session_state()

    # Header
    st.title("🔒 LLMSmartSec")
    st.markdown("**AI-Powered Smart Contract Security Auditing**")
    st.markdown("---")

    # Sidebar
    with st.sidebar:
        st.header("Settings")

        network = st.selectbox(
            "Blockchain Network",
            ["mainnet", "goerli", "sepolia", "polygon", "bsc", "arbitrum", "optimism"],
            index=0
        )

        st.markdown("---")
        st.header("About")
        st.markdown("""
        LLMSmartSec uses multiple AI perspectives to audit smart contracts:
        - **LLMDev**: Developer perspective
        - **LLMeHack**: Ethical hacker perspective
        - **LLMAudit**: Professional auditor perspective
        - **LLMReport**: Report consolidation
        """)

        # Graph database stats
        st.markdown("---")
        st.header("Knowledge Base")
        agent = get_graph_agent()
        if agent:
            try:
                stats = agent.get_statistics()
                st.metric("Contracts Analyzed", stats.get("contracts", 0))
                st.metric("Known Patterns", stats.get("patterns", 0))
                st.metric("Vulnerability Types", stats.get("labels", 0))
            except:
                st.info("Graph database not available")
        else:
            st.info("Graph database not connected")

    # Main content
    input_method = st.radio(
        "How would you like to provide the smart contract?",
        ["Enter Contract Address", "Paste Code Directly"],
        horizontal=True
    )

    if input_method == "Enter Contract Address":
        col1, col2 = st.columns([3, 1])
        with col1:
            address = st.text_input(
                "Contract Address",
                placeholder="0x...",
                help="Enter a verified contract address from Etherscan"
            )
        with col2:
            fetch_button = st.button("Fetch Code", type="primary")

        if fetch_button and address:
            with st.spinner("Fetching contract source code..."):
                code = fetch_contract_code(address, network)
                if code:
                    st.session_state.contract_code = code
                    st.session_state.contract_address = address
                    st.success("Contract code fetched successfully!")

        # Show fetched code
        if hasattr(st.session_state, 'contract_code') and st.session_state.contract_code:
            with st.expander("View Contract Code", expanded=False):
                st.code(st.session_state.contract_code[:5000] + "..." if len(st.session_state.contract_code) > 5000 else st.session_state.contract_code, language="solidity")

            if st.button("🔍 Run Security Audit", type="primary"):
                run_audit(st.session_state.contract_code, st.session_state.contract_address)

    else:  # Paste Code Directly
        code = st.text_area(
            "Paste Solidity Code",
            height=300,
            placeholder="pragma solidity ^0.8.0;\n\ncontract MyContract {\n    // Your code here\n}"
        )

        if code and st.button("🔍 Run Security Audit", type="primary"):
            run_audit(code, "Direct Input")

    # Display results if available
    if st.session_state.audit_results:
        st.markdown("---")
        display_results()

    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: gray;'>"
        "LLMSmartSec - Smart Contract Security Auditing powered by AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
