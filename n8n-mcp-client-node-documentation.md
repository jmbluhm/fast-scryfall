MCP Client Tool Node Specification for n8n

Overview

The MCP Client Tool Node in n8n enables integration with external tools via the Model Context Protocol (MCP). This allows AI agents within n8n to interact seamlessly with MCP-compliant services, enhancing automation capabilities. ￼

Key Features
	•	Protocol Support: Connects to external tools using the MCP standard.
	•	Authentication Methods: Supports Bearer Token and Generic Header authentication.
	•	Tool Exposure Control: Configure which tools are accessible to AI agents.
	•	Integration with AI Agents: Works in tandem with n8n’s AI Agent node for advanced workflows. ￼ ￼ ￼

Node Configuration

Parameters
	•	SSE Endpoint: Specify the Server-Sent Events (SSE) endpoint of the MCP server.
	•	Authentication:
	•	None: No authentication.
	•	Bearer: Use a Bearer Token for authentication.
	•	Generic Header: Define custom headers for authentication.
	•	Tools to Include:
	•	All: Expose all tools from the MCP server.
	•	Selected: Manually select tools to expose.
	•	All Except: Expose all tools except selected ones. ￼ ￼ ￼

Credentials

Configure credentials based on the chosen authentication method. For Bearer Token, provide the token value. For Generic Header, define the necessary headers. ￼

Integration with AI Agents

To utilize the MCP Client Tool Node within an AI Agent workflow: ￼
	1.	Add an AI Agent Node: Insert the AI Agent node into your workflow.
	2.	Connect MCP Client Tool Node: Attach the MCP Client Tool Node as a sub-node to the AI Agent.
	3.	Configure Parameters: Set the SSE endpoint and authentication details as per your MCP server configuration. ￼ ￼

This setup allows the AI Agent to invoke external tools via the MCP protocol. ￼

Examples and Templates

Explore practical implementations:
	•	Build an MCP Server with Google Calendar and Custom Functions: View Template
	•	AI-Powered Telegram Task Manager with MCP Server: View Template ￼ ￼

These templates demonstrate how to set up MCP servers and integrate them with n8n workflows. ￼

Troubleshooting
	•	Connection Issues: Ensure the SSE endpoint is correct and accessible. Verify authentication credentials.
	•	Tool Visibility: Confirm that the selected tools are available on the MCP server and correctly configured in the node.
	•	Workflow Activation: Make sure the workflow containing the MCP Client Tool Node is activated. ￼ ￼

Additional Resources
	•	Official Documentation: MCP Client Tool Node
	•	Community Discussions: n8n Community Forum
	•	MCP Specification: Model Context Protocol ￼

⸻

This document aims to provide a clear and concise guide to the MCP Client Tool Node in n8n, optimized for understanding and utilization by language models and developers alike.

⸻
