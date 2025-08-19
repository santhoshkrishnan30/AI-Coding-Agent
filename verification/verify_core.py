from src.agent.core import Agent
agent = Agent()
print('Agent class instantiated successfully')
print('Core methods exist:')
print(f'  - perceive: {hasattr(agent, "perceive")}')
print(f'  - reason: {hasattr(agent, "reason")}')
print(f'  - act: {hasattr(agent, "act")}')
print(f'  - learn: {hasattr(agent, "learn")}')