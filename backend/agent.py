"""Bedrock Agent orchestration for CI/CD failure diagnosis.

Uses the Bedrock Converse API with tool_use to invoke MCP tools
and produce structured diagnoses.
"""

import json
import boto3

from config import BEDROCK_MODEL_ID, BEDROCK_REGION
from mcp_client import MCPClient, get_default_mcp_client
from models import DiagnosisResponse, EvidenceItem, RootCauseCategory
from prompts import DIAGNOSTIC_SYSTEM_PROMPT, DIAGNOSIS_USER_PROMPT_TEMPLATE


class DiagnosticsAgent:
    """Agent that orchestrates MCP tool calls via Bedrock Converse API."""

    def __init__(self, mcp_client: MCPClient | None = None):
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

        # Try to parse as JSON first
        try:
            # Look for JSON block in the response
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
            elif "{" in text and "}" in text:
                start = text.index("{")
                end = text.rindex("}") + 1
                json_str = text[start:end]
            else:
                json_str = ""

            if json_str:
                data = json.loads(json_str)
                category = data.get("root_cause_category", "Configuration Issue")

                # Map to enum
                if "permission" in category.lower():
                    cat = RootCauseCategory.PERMISSION
                elif "infrastructure" in category.lower():
                    cat = RootCauseCategory.INFRASTRUCTURE
                else:
                    cat = RootCauseCategory.CONFIGURATION

                return DiagnosisResponse(
                    root_cause_category=cat,
                    root_cause_description=data.get("root_cause_description", text[:500]),
                    affected_resource=data.get("affected_resource", "Unknown"),
                    recommended_fix=data.get("recommended_fix", "See description"),
                    evidence=evidence,
                )
        except (json.JSONDecodeError, ValueError, IndexError):
            pass

        # Fallback: use the text as the description
        return DiagnosisResponse(
            root_cause_category=RootCauseCategory.CONFIGURATION,
            root_cause_description=text[:1000],
            affected_resource="Unknown",
            recommended_fix="See description above",
            evidence=evidence,
        )


# Module-level agent instance
_agent: DiagnosticsAgent | None = None


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
