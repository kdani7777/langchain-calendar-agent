import os
import subprocess
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.agents import initialize_agent, AgentType, AgentExecutor, create_react_agent, create_structured_chat_agent
from langchain_openai import ChatOpenAI
from typing import Optional, Type
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain import hub

@tool
def open_calendar():
  """Open the Calendar app"""
  calendar_app_path = "/System/Applications/Calendar.app"
  subprocess.run(["open", calendar_app_path])

class AppleScriptDate(BaseModel):
   date: str = Field(description="Date in the format of MM/DD/YYYY TT:TT")

class CheckAvailability(BaseTool):
  name = "Check availability in the Calendar app"
  description = "Use this tool to make sure there are no conflicting events on the calendar"
  args_schema: Type[BaseModel] = AppleScriptDate

  def _run(
    self, date: str, run_manager: Optional[CallbackManagerForToolRun] = None
  ) -> str:
    """Check availability in the Calendar app"""
    apple_script = f'''
        tell application "Calendar"
            set my_calendar to "Home"
            set my_date to date "{date}"
            set events_list to {{}}
            set all_day_events to (every event of calendar my_calendar whose start date ≤ my_date and end date ≥ my_date)
            repeat with an_event in all_day_events
                set end of events_list to summary of an_event
            end repeat
            events_list
        end tell
    '''

    # Execute AppleScript command
    result = subprocess.run(['osascript', '-e', apple_script], capture_output=True, text=True)

    # Check if the command executed successfully
    if result.returncode == 0:
        # Parse the output to get events list
        events_list = result.stdout.strip().split(', ')
        if events_list:
            print("Events on", date, ":", events_list)
        else:
            print("No events on", date)
    else:
        # Print error message if the command failed
        print("Error:", result.stderr)
  
  async def _arun(
    self, query: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
  ) -> str:
    """Use the tool asynchronously."""
    raise NotImplementedError("CheckAvailability does not support async")
  
availability_checker = CheckAvailability()

class CreateEventInput(BaseModel):
   summary: str = Field(description="A description of the event to create")
   start_date: str = Field(description="Start date of the event in the format of MM/DD/YYYY TT:TT")
   end_date: str = Field(description="End date of the event in the format of MM/DD/YYYY TT:TT")

def create_calendar_event(summary: str, start_date: str, end_date: str):
  """Create an event in the Calendar app"""
  # AppleScript to create a calendar event
  apple_script = f'''
    tell application "Calendar"
        tell calendar "Home"
            make new event with properties {{summary: "{summary}", start date:date "{start_date}", end date:date "{end_date}"}}
        end tell
    end tell
  '''
  # Execute AppleScript command
  result = subprocess.run(['osascript', '-e', apple_script], capture_output=True, text=True)

  # Check if the command executed successfully
  if result.returncode == 0:
    print("Event created successfully.")
  else:
    # Print error message if the command failed
    print("Error:", result.stderr)

create_event = StructuredTool.from_function(
   func=create_calendar_event,
   name="Create Event",
   description="Use this tool to create an event in the Calendar app",
   args_schema=CreateEventInput,
   return_direct=True
)

#Example usage
summary = "Meeting with John"
start_date = "3/19/2024 13:00"
end_date = "3/19/2024 14:00"

openai_api_key = os.environ.get("OPENAI_API_KEY")

# Choose the LLM to use
llm = ChatOpenAI(temperature=0)

# Define the tools that the agent has access to
tools = [open_calendar, create_event, availability_checker]

# Define or pull the prompt from langchain hub
prompt = hub.pull("hwchase17/structured-chat-agent")

# Construct the ReAct agent
agent = create_structured_chat_agent(llm, tools, prompt)

agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

agent_executor.invoke(
   {
      "input": "Schedule a meeting with Sean for 13:00 on 3/20/2024"
   }
)