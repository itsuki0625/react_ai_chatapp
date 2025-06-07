from app.services.agents.review_agent import SmartAOCoach

agent = SmartAOCoach()
response = agent.run("志望理由書の結論をもっと深掘りして")
print(response)