import random
from fastmcp import FastMcp

mcp=FastMcp(name='DemoServer')

@mcp.tool
def roll_dice(rolls:int)->list[int]:
    return [random.randint(1,6) for _ in range(1,rolls)]

@mcp.tool
def add(a:float,b:float)-> float:
    return a+b


if __name__=='__main__':
    mcp.run()