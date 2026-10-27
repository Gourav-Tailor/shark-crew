import os

from crewai import Agent, Task, Crew, LLM
from pydantic import BaseModel, Field


API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

if not API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set")


class PitchValidation(BaseModel):
    is_valid_pitch: bool = Field(
        description=(
            "True if the input describes a startup business, product, "
            "problem, solution, market, or traction. False for greetings, "
            "casual chat, random text, or irrelevant content."
        )
    )
    reason: str = Field(
        description="Brief explanation for the validation decision."
    )


llm = LLM(
    model=MODEL,
    provider="openai",
    base_url="https://api.groq.com/openai/v1",
    api_key=API_KEY,
)


validator_agent = Agent(
    role="Pitch Validator",
    goal="Determine whether the user's input is a genuine startup pitch.",
    backstory=(
        "You are a strict startup gatekeeper. Reject greetings, casual "
        "conversation, random text, and unrelated questions."
    ),
    llm=llm,
    allow_delegation=False,
)


numbers = Agent(
    role="Numbers Shark",
    goal="Judge the pitch's unit economics and financial viability.",
    backstory="A ruthless CFO-turned-investor.",
    llm=llm,
    allow_delegation=False,
    max_iter=3,
)

visionary = Agent(
    role="Visionary Shark",
    goal="Judge the size and potential of the vision.",
    backstory="A founder who backs bold bets.",
    llm=llm,
    allow_delegation=False,
    max_iter=3,
)

skeptic = Agent(
    role="Skeptic Shark",
    goal="Find the most dangerous flaw in the pitch.",
    backstory="A contrarian investor who has seen almost everything fail.",
    llm=llm,
    allow_delegation=False,
    max_iter=3,
)


validation_task = Task(
    description="""
Analyze the following user input:

{pitch}

Determine whether it is a legitimate startup pitch.

A valid pitch can describe:
- a startup/business
- a product or service
- a customer problem
- a proposed solution
- a business model
- a target market
- traction or growth

Reject casual greetings, random conversation, generic questions,
and unrelated text.
""",
    expected_output="A structured PitchValidation result.",
    agent=validator_agent,
    output_pydantic=PitchValidation,
)

validation_crew = Crew(
    agents=[validator_agent],
    tasks=[validation_task],
    verbose=False,
)


evaluation_tasks = [
    Task(
        description="Evaluate this startup pitch: {pitch}",
        agent=agent,
        expected_output="A concise verdict: offer or pass, with reasoning.",
    )
    for agent in (numbers, visionary, skeptic)
]

evaluation_crew = Crew(
    agents=[numbers, visionary, skeptic],
    tasks=evaluation_tasks,
    tracing=False,
    verbose=False,
)


def validator(text: str) -> PitchValidation:
    result = validation_crew.kickoff(inputs={"pitch": text})

    output = result.tasks_output[0]

    if output.pydantic is None:
        raise RuntimeError("Pitch validation did not return structured output.")

    return output.pydantic


def pitch(text: str):
    validation = validator(text)

    if not validation.is_valid_pitch:
        return validation.reason

    return evaluation_crew.kickoff(inputs={"pitch": text})