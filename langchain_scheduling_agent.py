import os
import subprocess
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from langchain.agents import initialize_agent, AgentType
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from typing import Optional, Type
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

openai_api_key = os.environ.get("OPENAI_API_KEY")
llm = ChatOpenAI(temperature=0)

@tool
def open_calendar():
  """Open the Calendar app"""
  calendar_app_path = "/System/Applications/Calendar.app"
  subprocess.run(["open", calendar_app_path])

class AppleScriptDate(BaseModel):
   date: str = Field(description="Date in the format of MM/DD/YYYY TT:TT")

class CheckAvailability(BaseTool):
  name = "Check availability",
  description = "Check availability in the Calendar app"
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
   summary: str = Field(description="A description of the event")
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
   description="Create an event in the Calendar app",
   args_schema=CreateEventInput,
   return_direct=True
)


#Example usage
summary = "Meeting with John"
start_date = "3/19/2024 9:00 AM"
end_date = "3/19/2024 10:00 AM"

tools = [open_calendar, create_event, availability_checker]
agent_executor = initialize_agent(
   tools, 
   llm, 
   agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
   verbose=True
)

agent_executor.invoke(
   {
      "input": "Schedule a meeting with Sean for 1PM on 3/20/2024"
   }
)