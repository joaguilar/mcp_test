# MCP Research Agent

This repository provides a minimal multi-server **Model Context Protocol (MCP)** demo that integrates:

1. **Tools** – for Brave Search API calls (via `tools_server.py`)  
2. **Prompt** – a placeholder MCP prompt server (`prompt_server.py`)  
3. **Resources** – to handle file I/O (`resource_server.py`)  
4. **Sampler** – to call an OpenAI LLM (`llm_server.py`)  
5. **Main Agent** – a Streamlit-based client (`main_agent.py`) orchestrating everything

The demo uses [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) to illustrate how you can chain multiple servers (tools, resources, prompts, samplers) under a single orchestrating agent. The agent uses:

- [Brave Search API](https://api-dashboard.search.brave.com/app/documentation/web-search/get-started) for quick web lookups  
- [OpenAI GPT-4](https://platform.openai.com/) (referred to here as `gpt-4o-mini`) for summarizing and synthesizing search results  
- A basic local file system resource server to store the resulting summaries

---

## Features

- **Tools Server**: MCP Tools server that calls the Brave Search API  
- **Prompt Server**: MCP Prompt server (placeholder) with a generic research prompt  
- **Resource Server**: MCP Resource server providing file operations (create, read, delete)  
- **LLM Sampler Server**: MCP Sampler server that calls an OpenAI ChatCompletion endpoint  
- **Main Agent**: A Streamlit app that orchestrates requests among the other servers and presents the final output to the user

---

## Prerequisites

1. **Python 3.8+**  
2. **OpenAI API Key**  
3. **Brave Search API Key**  
4. **Model Context Protocol SDK**
5. **dotenv**

---

## Installation

1. **Clone or download** this repository.  
2. Create a conda environment:

```
conda create --prefix .\mcp_env python=3.12
```

3. Activate the environment:

```
conda activate .\mcp_env
```
4. In your project folder (where `pyproject.toml` is located), install dependencies:
   ```bash
   pip install .
