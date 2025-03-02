MCP Review

- [Capabilities Mapping](#capabilities-mapping)
- [MCP Design Basics](#mcp-design-basics)
- [Agent Catalogs](#agent-catalogs)
  - [MCP Tools as Catalog](#mcp-tools-as-catalog)
    - [Discovery - List tools:](#discovery---list-tools)
    - [Invocation - Call tools:](#invocation---call-tools)
  - [Agent Catalog Comparison](#agent-catalog-comparison)
- [Data Sources](#data-sources)
  - [Resources (MCP)](#resources-mcp)
  - [Data Source Comparison](#data-source-comparison)
- [Agent Clients](#agent-clients)
  - [Clients )MCP)](#clients-mcp)
- [Prompt Registry](#prompt-registry)
  - [MCP Prompt Registry](#mcp-prompt-registry)
- [LLM Interactions](#llm-interactions)
  - [Sampling (MCP)](#sampling-mcp)
- [Sample Sequences](#sample-sequences)
  - [MCP Simple Agent call](#mcp-simple-agent-call)
- [Sample Implementation](#sample-implementation)


# Capabilities Mapping


| Capability      |     | MCP                                                                  |
| --------------- | --- | -------------------------------------------------------------------- |
| Agent Catalogs  |     | [Tools](https://modelcontextprotocol.io/docs/concepts/tools) (?)     |
| Agent Providers |     | [Tools](https://modelcontextprotocol.io/docs/concepts/tools) (?)     |
| Data Sources    |     | [Resources](https://modelcontextprotocol.io/docs/concepts/resources) |
| Agent Clients   |     | [Clients](https://modelcontextprotocol.io/clients)                   |
| Prompt Registry |     | [Prompts](https://modelcontextprotocol.io/docs/concepts/prompts)     |
| LLM Calls       |     | [Sampling](https://modelcontextprotocol.io/docs/concepts/sampling)   |




# MCP Design Basics

```mermaid
graph TD
    subgraph Host["Host (Main Agent)"]
        A[MCP Client]
        C[MCP Client]
    end

    subgraph Server_Process_1["Server Process"]
        B[MCP Server]
    end

    subgraph Server_Process_2["Server Process"]
        D[MCP Server]
    end

    A -- Transport Layer --> B
    C -- Transport Layer --> D
```

```mermaid
graph TD
    subgraph Host_Server["Host Server"]
        Client["Host with MCP Client"]
        ServerA["MCP Server A"]
        ServerB["MCP Server B"]
        ServerC["MCP Server C"]
        
    end

    subgraph Database_Server["Database Server"]
        DataSourceA[("Data Source A")]
    end

    subgraph Database_Graph["Graph Database"]
        DataSourceB["Knowledge Graph"]
    end

    subgraph Internet["Internet"]
        RemoteServiceC["Remote Service C"]
    end

    Client -- "MCP Protocol" --> ServerA
    Client -- "MCP Protocol" --> ServerB
    Client -- "MCP Protocol" --> ServerC
    ServerA -- "SQL" --> DataSourceA
    ServerB -- "Cypher Query" --> DataSourceB
    ServerC -- "Web APIs" --> RemoteServiceC

```

MCP Servers expose 

# Agent Catalogs


## MCP Tools as Catalog

Even though MCP doesn't contain a catalog of agents per se (instead architects agents as multiple servers/clients) the tools capability allows servers to expose endpoints that allow discovery and invocation of tools that can be used by the LLM (or a "main" agent).

Tools are defined as:

```
{
  name: string;          // Unique identifier for the tool
  description?: string;  // Human-readable description
  inputSchema: {         // JSON Schema for the tool's parameters
    type: "object",
    properties: { ... }  // Tool-specific parameters
  }
}
```

Servers expose these tools via two methods:

### Discovery - List tools:

```
tools/list
```

### Invocation - Call tools:

```
tools/call
```

These tools can be the entry point for other agents called from a "main" agent.

## Agent Catalog Comparison

The main difference between 

# Data Sources


## Resources (MCP)

## Data Source Comparison

# Agent Clients



## Clients )MCP)

# Prompt Registry

## MCP Prompt Registry

MCP has a prompt type of resource that allows agents to "ask" for prompt templates to fill in an use in calls to llms (using sampling as below?). This can allow advanced agentic behavior 

# LLM Interactions

## Sampling (MCP)

Main reference: [Sampling](https://modelcontextprotocol.io/docs/concepts/sampling)

One interesting feature of MCP is the capability to directly call LLMs for completions via the same protocol.
This allows an agent to decide when to call an LLM to make decisions based on the context on what to call next (for example), generating a response, expanding on a user request or any other separate request.

# Sample Sequences

## MCP Simple Agent call

```mermaid
sequenceDiagram
    participant User
    participant Agent as Agent Client
    participant PromptServer as Prompt Server
    participant ResourceServer as Resource Server
    participant SamplingServer as Sampling Server
    participant LLM

    User ->> Agent: Send Request
    Agent ->> PromptServer: Get Prompt Template
    PromptServer -->> Agent: Return Template

    Agent ->> ResourceServer: Get Context for LLM
    ResourceServer -->> Agent: Return Context

    Agent ->> Agent: Fill in Parameters (Template + Context)

    Agent ->> SamplingServer: Request LLM Response
    SamplingServer ->> LLM: LLM Request
    LLM ->> SamplingServer: LLM Request
    SamplingServer -->> Agent: Return Generated Response

    Agent -->> User: Send Response
```

# Sample Implementation

