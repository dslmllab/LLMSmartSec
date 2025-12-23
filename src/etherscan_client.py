"""
Etherscan API Client for fetching smart contract source code.

This module provides functionality to retrieve verified smart contract
source code from Etherscan using their API.
"""

import os
import requests
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class EtherscanClient:
    """Client for interacting with Etherscan API to fetch contract data."""

    # Supported networks and their API endpoints
    NETWORKS = {
        "mainnet": "https://api.etherscan.io/api",
        "goerli": "https://api-goerli.etherscan.io/api",
        "sepolia": "https://api-sepolia.etherscan.io/api",
        "polygon": "https://api.polygonscan.com/api",
        "bsc": "https://api.bscscan.com/api",
        "arbitrum": "https://api.arbiscan.io/api",
        "optimism": "https://api-optimistic.etherscan.io/api",
    }

    def __init__(self, api_key: Optional[str] = None, network: str = "mainnet"):
        """
        Initialize the Etherscan client.

        Args:
            api_key: Etherscan API key. If not provided, reads from ETHERSCAN_API_KEY env var.
            network: Network to query (mainnet, goerli, sepolia, polygon, bsc, arbitrum, optimism)
        """
        self.api_key = api_key or os.getenv("ETHERSCAN_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Etherscan API key required. Set ETHERSCAN_API_KEY environment variable "
                "or pass api_key parameter."
            )

        if network not in self.NETWORKS:
            raise ValueError(f"Unsupported network: {network}. Supported: {list(self.NETWORKS.keys())}")

        self.network = network
        self.base_url = self.NETWORKS[network]

    def get_contract_source(self, address: str) -> Dict[str, Any]:
        """
        Fetch verified contract source code from Etherscan.

        Args:
            address: The contract address (with or without 0x prefix)

        Returns:
            Dictionary containing:
                - success: bool
                - source_code: str (the Solidity source code)
                - contract_name: str
                - compiler_version: str
                - optimization_used: bool
                - abi: str (JSON ABI)
                - error: str (if failed)
        """
        # Normalize address
        if not address.startswith("0x"):
            address = f"0x{address}"

        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "1":
                return {
                    "success": False,
                    "error": data.get("message", "Unknown error"),
                    "address": address
                }

            result = data["result"][0]

            # Check if contract is verified
            if not result.get("SourceCode"):
                return {
                    "success": False,
                    "error": "Contract source code not verified on Etherscan",
                    "address": address
                }

            # Handle multi-file contracts (JSON format)
            source_code = result["SourceCode"]
            if source_code.startswith("{{"):
                # Multi-file contract - extract and combine
                source_code = self._parse_multi_file_source(source_code)

            return {
                "success": True,
                "address": address,
                "source_code": source_code,
                "contract_name": result.get("ContractName", "Unknown"),
                "compiler_version": result.get("CompilerVersion", "Unknown"),
                "optimization_used": result.get("OptimizationUsed", "0") == "1",
                "runs": result.get("Runs", "200"),
                "abi": result.get("ABI", "[]"),
                "constructor_arguments": result.get("ConstructorArguments", ""),
                "evm_version": result.get("EVMVersion", "default"),
                "library": result.get("Library", ""),
                "license_type": result.get("LicenseType", ""),
                "proxy": result.get("Proxy", "0") == "1",
                "implementation": result.get("Implementation", ""),
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "address": address
            }

    def _parse_multi_file_source(self, source_json: str) -> str:
        """
        Parse multi-file source code format from Etherscan.

        Args:
            source_json: JSON string containing multiple source files

        Returns:
            Combined source code as a single string
        """
        import json

        # Remove outer braces if double-wrapped
        if source_json.startswith("{{"):
            source_json = source_json[1:-1]

        try:
            sources = json.loads(source_json)

            # Handle different JSON structures
            if "sources" in sources:
                sources = sources["sources"]

            combined = []
            for filename, content in sources.items():
                if isinstance(content, dict):
                    code = content.get("content", "")
                else:
                    code = content

                combined.append(f"// File: {filename}")
                combined.append(code)
                combined.append("")

            return "\n".join(combined)

        except json.JSONDecodeError:
            # Return as-is if not valid JSON
            return source_json

    def get_contract_abi(self, address: str) -> Dict[str, Any]:
        """
        Fetch only the ABI for a contract.

        Args:
            address: The contract address

        Returns:
            Dictionary with success status and ABI
        """
        if not address.startswith("0x"):
            address = f"0x{address}"

        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data["status"] != "1":
                return {
                    "success": False,
                    "error": data.get("message", "Unknown error"),
                    "address": address
                }

            return {
                "success": True,
                "address": address,
                "abi": data["result"]
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}",
                "address": address
            }

    def is_contract(self, address: str) -> bool:
        """
        Check if an address is a contract (has code).

        Args:
            address: The address to check

        Returns:
            True if the address is a contract, False otherwise
        """
        if not address.startswith("0x"):
            address = f"0x{address}"

        params = {
            "module": "proxy",
            "action": "eth_getCode",
            "address": address,
            "tag": "latest",
            "apikey": self.api_key
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # If result is "0x" or empty, it's not a contract
            code = data.get("result", "0x")
            return code != "0x" and len(code) > 2

        except requests.exceptions.RequestException:
            return False


def main():
    """Example usage of EtherscanClient."""
    # Example: Fetch USDT contract source
    client = EtherscanClient(network="mainnet")

    # USDT contract address on mainnet
    usdt_address = "0xdAC17F958D2ee523a2206206994597C13D831ec7"

    print(f"Fetching source code for: {usdt_address}")
    result = client.get_contract_source(usdt_address)

    if result["success"]:
        print(f"Contract Name: {result['contract_name']}")
        print(f"Compiler: {result['compiler_version']}")
        print(f"Optimization: {result['optimization_used']}")
        print(f"\nSource Code Preview (first 500 chars):")
        print(result["source_code"][:500])
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()
