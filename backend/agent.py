"""Bedrock Agent orchestration for CI/CD failure diagnosis.

Uses the Bedrock Converse API with tool_use to invoke MCP tools
and produce structured diagnoses.
"""

from __future__ import annotations

import json
from typing import Optional

import boto3

from config import BEDROCK_MODEL_ID, BEDROCK_REGION
from mcp_client import MCPClient, get_default_mcp_client
from models import DiagnosisResponse, EvidenceItem, RootCauseCategory
from prompts import DIAGNOSTIC_SYSTEM_PROMPT, DIAGNOSIS_USER_PROMPT_TEMPLATE


class DiagnosticsAgent:
    """Agent that orchestrates MCP tool calls via Bedrock Converse API."""

    def __init__(self, mcp_client: Optional[MCPClient] = None):
        self._mcp_client = mcp_client or get_default_mcp_client()
        self._bedrock = boto3.client(
            "bedrock-runtime",
            region_name=BEDROCK_REGION,
        )
        self._initialized = False

    async def initialize(self):
        """Start MCP servers and discover tools."""
        if not self._initialized:
            await self._mcp_client.start_all()
            self._initialized = True

    async def shutdown(self):
        """Stop all MCP servers."""
        await self._mcp_client.stop_all()
        self._initialized = False

    async def diagnose(self, pipeline_name: str, execution_id: str) -> DiagnosisResponse:
        """Run the diagnostic agent loop for a failed pipeline.

        Args:
            pipeline_name: Name of the failed pipeline.
            execution_id: The execution ID to diagnose.

        Returns:
            Structured diagnosis response.
        """
        await self.initialize()

        # Build tool config for Bedrock
        tool_config = {"tools": self._mcp_client.get_tool_schemas_for_bedrock()}

        # Build the user message
        user_message = DIAGNOSIS_USER_PROMPT_TEMPLATE.format(
            pipeline_name=pipeline_name,
            execution_id=execution_id,
        )

        messages = [{"role": "user", "content": [{"text": user_message}]}]

        evidence = []
        max_iterations = 10

        for _ in range(max_iterations):
            # Call Bedrock Converse API
            response = self._bedrock.converse(
                modelId=BEDROCK_MODEL_ID,
                system=[{"text": DIAGNOSTIC_SYSTEM_PROMPT}],
                messages=messages,
                toolConfig=tool_config,
            )

            # Process the response
            output = response["output"]["message"]
            messages.append(output)

            stop_reason = response["stopReason"]

            if stop_reason == "tool_use":
                # Process tool calls
                tool_results = []
                for content_block in output["content"]:
                    if "toolUse" in content_block:
                        tool_use = content_block["toolUse"]
                        tool_name = tool_use["name"]
                        tool_input = tool_use["input"]
                        tool_use_id = tool_use["toolUseId"]

                        # Call the tool via MCP client
                        result = await self._mcp_client.call_tool(tool_name, tool_input)

                        # Track evidence
                        evidence.append(EvidenceItem(
                            source=tool_name,
                            finding=json.dumps(result, default=str)[:500],
                        ))

                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_use_id,
                                "content": [{"text": json.dumps(result, default=str)}],
                            }
                        })

                # Add tool results to conversation
                messages.append({"role": "user", "content": tool_results})

            elif stop_reason == "end_turn":
                # Agent has finished - extract the diagnosis from the final message
                return self._parse_diagnosis(output, evidence)

        # If we hit max iterations, return what we have
        return DiagnosisResponse(
            root_cause_category=RootCauseCategory.CONFIGURATION,
            root_cause_description="Diagnosis incomplete - max iterations reached",
            affected_resource=pipeline_name,
            recommended_fix="Please try again or investigate manually",
            evidence=evidence,
        )

    def _parse_diagnosis(
        self, message: dict, evidence: list[EvidenceItem]
    ) -> DiagnosisResponse:
        """Parse the agent's final message into a structured diagnosis."""
        # Extract text from the message
        text = ""
        for content_block in message.get("content", []):
            if "text" in content_block:
                text += content_block["text"]

        text_lower = text.lower()

        # Try to parse as JSON first
        json_str = ""
        try:
            # Look for JSON block in the response
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text and "{" in text:
                # Sometimes model outputs ``` without json language marker
                parts = text.split("```")
                for part in parts[1:]:
                    stripped = part.strip()
                    if stripped.startswith("{"):
                        json_str = stripped
                        break
            elif "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]

            if json_str:
                data = json.loads(json_str)
                category = data.get("root_cause_category", "")
                cat = self._classify_category(category, text_lower)

                return DiagnosisResponse(
                    root_cause_category=cat,
                    root_cause_description=data.get("root_cause_description", "")[:2000],
                    affected_resource=data.get("affected_resource", "Unknown"),
                    recommended_fix=data.get("recommended_fix", "See description")[:3000],
                    evidence=evidence,
                )
        except (json.JSONDecodeError, ValueError, IndexError):
            # JSON was malformed — try to repair truncated JSON
            if json_str:
                repaired = self._repair_truncated_json(json_str)
                if repaired:
                    cat = self._classify_category(
                        repaired.get("root_cause_category", ""), text_lower
                    )
                    return DiagnosisResponse(
                        root_cause_category=cat,
                        root_cause_description=repaired.get("root_cause_description", "")[:2000],
                        affected_resource=repaired.get("affected_resource", "Unknown"),
                        recommended_fix=repaired.get("recommended_fix", "See description")[:3000],
                        evidence=evidence,
                    )

        # Fallback: extract structured fields from markdown response
        cat = self._classify_category("", text_lower)

        # Extract description (root cause description section)
        description = self._extract_section(text, "root cause description")
        if not description:
            description = self._extract_section(text, "root_cause_description")
        if not description:
            description = self._extract_section(text, "description")

        # Extract recommended_fix
        recommended_fix = self._extract_section(text, "recommended fix")
        if not recommended_fix:
            recommended_fix = self._extract_section(text, "recommended_fix")
        if not recommended_fix:
            recommended_fix = self._extract_section(text, "resolution")
        if not recommended_fix:
            recommended_fix = self._extract_section(text, "fix")

        # Extract affected_resource
        affected_resource = self._extract_section(text, "affected resource")
        if not affected_resource:
            affected_resource = self._extract_section(text, "affected_resource")

        # If we couldn't extract a description, use a cleaned-up version of the full text
        if not description:
            # Remove common prefixes the agent adds
            import re
            cleaned = re.sub(
                r'^(Perfect!|Excellent!|Great!|Based on my investigation,?)[\s\S]{0,100}?(?=##|\*\*)',
                '', text, flags=re.IGNORECASE
            ).strip()
            description = cleaned[:2000] if cleaned else text[:2000]

        # If recommended_fix is still empty, use the full text as it likely contains the fix
        if not recommended_fix:
            recommended_fix = description

        # If affected_resource is still empty, try to find ARNs or resource names
        if not affected_resource:
            import re
            arn_match = re.search(r'arn:aws:[^\s\)\"]+', text)
            if arn_match:
                affected_resource = arn_match.group(0)
            else:
                affected_resource = "See description"

        return DiagnosisResponse(
            root_cause_category=cat,
            root_cause_description=description,
            affected_resource=affected_resource,
            recommended_fix=recommended_fix,
            evidence=evidence,
        )

    def _repair_truncated_json(self, json_str: str) -> dict | None:
        """Attempt to repair a truncated JSON response by extracting known fields."""
        import re
        result = {}

        # Extract each known field using regex
        field_patterns = {
            "root_cause_category": r'"root_cause_category"\s*:\s*"([^"]*)"',
            "root_cause_description": r'"root_cause_description"\s*:\s*"((?:[^"\\]|\\.)*)"',
            "affected_resource": r'"affected_resource"\s*:\s*"((?:[^"\\]|\\.)*)"',
            "recommended_fix": r'"recommended_fix"\s*:\s*"((?:[^"\\]|\\.)*)',
        }

        for field, pattern in field_patterns.items():
            match = re.search(pattern, json_str, re.DOTALL)
            if match:
                value = match.group(1)
                # Unescape JSON string escapes
                value = value.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
                result[field] = value

        if result.get("root_cause_description"):
            return result
        return None

    def _classify_category(self, explicit_category: str, full_text_lower: str) -> RootCauseCategory:
        """Classify the root cause category from explicit label or text analysis."""
        # Check explicit category first
        if explicit_category:
            if "permission" in explicit_category.lower():
                return RootCauseCategory.PERMISSION
            if "infrastructure" in explicit_category.lower():
                return RootCauseCategory.INFRASTRUCTURE

        # Analyze full text for permission indicators
        permission_keywords = [
            "access denied", "accessdenied", "permission", "iam",
            "gitpull", "git pull", "unauthorized", "forbidden",
            "policy", "role does not have"
        ]
        if any(kw in full_text_lower for kw in permission_keywords):
            return RootCauseCategory.PERMISSION

        # Analyze for infrastructure indicators
        infra_keywords = [
            "infrastructure", "organizational unit", "ou name",
            "ou mismatch", "stack", "organization", "lza",
            "landing zone", "accounts-config"
        ]
        if any(kw in full_text_lower for kw in infra_keywords):
            return RootCauseCategory.INFRASTRUCTURE

        return RootCauseCategory.CONFIGURATION

    def _extract_section(self, text: str, section_name: str) -> str:
        """Try to extract a named section from markdown-formatted text."""
        import re

        # Multiple patterns to match different markdown heading/label styles
        patterns = [
            # ### **Section Name**\ncontent
            rf'###?\s*\*?\*?\s*{re.escape(section_name)}\s*\*?\*?\s*:?\s*\n(.*?)(?=\n###|\n##|\n\*\*[A-Z]|\Z)',
            # **Section Name:**\ncontent or **section_name:** content
            rf'\*\*\s*{re.escape(section_name)}\s*\*?\*?\s*:?\s*\n?(.*?)(?=\n\*\*[A-Z]|\n###|\n##|\Z)',
            # section_name: content (on same line or next)
            rf'{re.escape(section_name)}\s*:\s*\n?(.*?)(?=\n\*\*[A-Z]|\n###|\n##|\Z)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                # Remove trailing markdown artifacts
                result = re.sub(r'\n---\s*$', '', result).strip()
                if len(result) > 10:
                    return result[:2000]

        return ""


# Module-level agent instance
_agent: Optional[DiagnosticsAgent] = None


async def diagnose_pipeline_failure(
    pipeline_name: str, execution_id: str
) -> DiagnosisResponse:
    """Diagnose a pipeline failure using the Bedrock agent.

    This is the main entry point called by the API routes.
    """
    global _agent
    if _agent is None:
        _agent = DiagnosticsAgent()

    return await _agent.diagnose(pipeline_name, execution_id)
