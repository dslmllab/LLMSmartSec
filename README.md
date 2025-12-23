# LLMSmartSec

Smart contract security auditor using GPT-4 and Neo4j. Analyzes Solidity code from multiple perspectives (developer, hacker, auditor) and stores vulnerability patterns in a graph database.

## Features

- Multi-perspective audit: Developer, Ethical Hacker, Auditor views
- Neo4j knowledge graph for pattern matching
- Etherscan integration for fetching contract source
- Streamlit web UI
- PDF/JSON/Markdown report export

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit UI                              │
│                    (app.py - User Interface)                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Audit Pipeline                                │
│                  (audit_pipeline.py)                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ LLMDev   │→ │LLMeHack  │→ │ LLMAudit │→ │LLMReport │        │
│  │Developer │  │  Hacker  │  │ Auditor  │  │  Summary │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
        │                                           │
        ▼                                           ▼
┌───────────────────┐                    ┌───────────────────┐
│  Etherscan API    │                    │  LLMGraphAgent    │
│(etherscan_client) │                    │  (graph_agent.py) │
│ Fetch Contract    │                    │  Pattern Matching │
└───────────────────┘                    └───────────────────┘
                                                   │
                                                   ▼
                                         ┌───────────────────┐
                                         │    Neo4j Graph    │
                                         │  Knowledge Base   │
                                         └───────────────────┘
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/yourusername/LLMSmartSec.git
cd LLMSmartSec
pip install -r src/requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys and Neo4j password

# Start Neo4j (must be running on neo4j://127.0.0.1:7687)

# Load initial data into graph (uses GPT-4 API)
cd src
python initLoadGraphDB.py

# Run the app
streamlit run app.py
```

## Requirements

- Python 3.9+
- Neo4j 5.x
- OpenAI API key (GPT-4)
- Etherscan API key (optional)

## Setup

1. **Clone**
   ```bash
   git clone https://github.com/yourusername/LLMSmartSec.git
   cd LLMSmartSec
   ```

2. **Virtual environment** (optional)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r src/requirements.txt
   ```

4. **Neo4j**
   - Install [Neo4j Desktop](https://neo4j.com/download/)
   - Create a database
   - Start it on `neo4j://localhost:7687`

5. **Initialize graph database**
   ```bash
   cd src
   python initLoadGraphDB.py
   ```
   This pulls contracts from the [slither-audited-smart-contracts](https://huggingface.co/datasets/mwritescode/slither-audited-smart-contracts) dataset and uses GPT-4 to build the knowledge graph. Default is 10 contracts. Edit `num_examples` in `initLoadGraphDB.py` to change. Costs ~$0.05-0.10 per contract.

## Configuration

```bash
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-your-key
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
ETHERSCAN_API_KEY=your-key  # optional
```

## Usage

**Web UI:**
```bash
cd src
streamlit run app.py
```

**CLI:**
```bash
cd src
python audit_pipeline.py
```

**Add more contracts to graph:**
```bash
# Edit num_examples in initLoadGraphDB.py first
python initLoadGraphDB.py
```

## Project Structure

```
LLMSmartSec/
├── src/
│   ├── app.py                  # Streamlit UI
│   ├── audit_pipeline.py       # Multi-assistant pipeline
│   ├── etherscan_client.py     # Etherscan API
│   ├── graph_agent.py          # Neo4j queries
│   ├── vector_store.py         # Vector store for RAG
│   ├── report_generator.py     # PDF generation
│   ├── initLoadGraphDB.py      # Graph DB loader
│   ├── requirements.txt
│   └── Prompts/                # LLM prompts
├── Dataset/                    # CSV data
├── Results/                    # Output
├── .env.example
└── README.md
```

## Components

**audit_pipeline.py** - Runs 4 assistants in sequence:
- LLMDev: Developer review
- LLMeHack: Security scan
- LLMAudit: Audit report
- LLMReport: Final summary

**graph_agent.py** - Queries Neo4j for:
- Similar contracts
- Known vulnerabilities
- Cached results
- Mitigations

**etherscan_client.py** - Fetches source from Etherscan (mainnet, testnets, L2s)

## Vulnerability Types

| Type | Description |
|------|-------------|
| access-control | Permission issues |
| arithmetic | Overflow/underflow |
| reentrancy | Reentrancy attacks |
| unchecked-calls | Unchecked returns |
| front-running | TX ordering |
| denial-of-service | DoS vectors |
| logic-errors | Logic flaws |

## Troubleshooting

**Neo4j connection error:**
```
ServiceUnavailable: Unable to retrieve routing information
```
Check Neo4j is running on `neo4j://localhost:7687`.

**OpenAI error:**
```
AuthenticationError: Incorrect API key
```
Check your API key has GPT-4 access.

**Etherscan error:**
```
Contract source code not verified
```
Contract isn't verified. Paste code directly instead.

## Citation

If you use this work, please cite:

```bibtex
@INPROCEEDINGS{10664261,
  author={Mothukuri, Viraaji and Parizi, Reza M. and Massa, James L.},
  booktitle={2024 IEEE International Conference on Blockchain (Blockchain)},
  title={LLMSmartSec: Smart Contract Security Auditing with LLM and Annotated Control Flow Graph},
  year={2024},
  pages={434-441},
  doi={10.1109/Blockchain62396.2024.00064}
}
```

## License

Educational/research use.


