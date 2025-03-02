import os
import openai
from mcp import MCPServer, Sampler, SampleRequest, SampleResponse
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY", "")

MODEL_NAME = "gpt-4o-mini"  # Replace with your actual GPT-4 or GPT-3.5 model name

def openai_chat_sampler(request: SampleRequest) -> SampleResponse:
    """
    Handler for the Sampler endpoint.
    We'll interpret request.prompt and request.settings for temperature, etc.
    """
    # request.prompt might have 'system', 'user', or might just have a single text prompt.
    # The MCP "sampling" concept is fairly open; we'll do a chat-based approach here.
    
    system_prompt = request.prompt.get("system", "")
    user_prompt = request.prompt.get("user", "")
    
    # Retrieve temperature or default to 0.7
    temperature = request.settings.get("temperature", 0.7)
    
    # Construct chat messages:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})
    
    # Call OpenAI ChatCompletion
    try:
        response = openai.ChatCompletion.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=temperature
        )
        text_out = response.choices[0].message["content"].strip()
        return SampleResponse(text=text_out)
    
    except Exception as e:
        return SampleResponse(text=f"[ERROR calling OpenAI] {str(e)}")

if __name__ == "__main__":
    # Create an MCP server with the Sampler
    server = MCPServer(
        name="openai-llm-sampler",
        samplers=[
            Sampler(
                name="openai-chat",
                handler=openai_chat_sampler,
                description="Sampler that calls OpenAI GPT-4 or GPT-3.5 via ChatCompletion"
            )
        ]
    )
    # Default to port 5004 (adjust as needed)
    server.run(host="0.0.0.0", port=5004)
