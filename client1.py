from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
import warnings
import os 
import asyncio
from dotenv import load_dotenv

load_dotenv()

warnings.filterwarnings('ignore')

servers={

     'math':{
        'transport':'stdio',
        'command':'/Users/divyyadav/miniforge3/bin/uv',
        'args':['run',
                'fastmcp',
                'run',
                '/Users/divyyadav/Desktop/mcp-server/server.py'
        ]
    },
    {
     "manim-server": {
      "command": "/Users/divyyadav/miniforge3/bin/uv",
      "args": [
        "/Users/divyyadav/Desktop/mcp-server/manim-mcp-server/src/manim_server.py"
      ],
      "env": {
        "MANIM_EXECUTABLE": "/Users/divyyadav/anaconda3/envs/manim2/Scripts/manim.exe"
      }
    }
  }
}



async def main(prompt:str):
    '''making a client to connect to the server'''

    client=MultiServerMCPClient(servers)

    tools=await client.get_tools()

    named_t={}

    for tool in tools:
        named_t[tool.name]=tool

    api_key=os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        raise ValueError('GEMINI_API_KEY not found')

    llm=ChatGoogleGenerativeAI(model='gemini-2.5-flash',api_key=api_key,temperature=0.5)

    llm_with_tools=llm.bind_tools(tools=tools)

    response=await llm_with_tools.ainvoke(prompt)

    if response.tool_calls:
        tool_name=response.tool_calls[0]['name']
        tool_args=response.tool_calls[0]['args']
        print(tool_name,tool_args)


if __name__ == '__main__':
    asyncio.run(main(prompt='what is 2+2'))