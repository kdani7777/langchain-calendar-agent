import os
import subprocess
from langchain.tools import StructuredTool, tool
from langchain.agents import initialize_agent, AgentType

@tool
def open_calendar():
  """Open the Calendar app"""
  calendar_app_path = "/System/Applications/Calendar.app"
  subprocess.run(["open", calendar_app_path])

@tool
def check_availability(date: str):
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

create_event = StructuredTool.from_function(create_calendar_event)


#Example usage
summary = "Meeting with John"
start_date = "3/19/2024 9:00 AM"
end_date = "3/19/2024 10:00 AM"

#create_calendar_event(summary, start_date, end_date)
#check_availability(start_date)

tools = [open_calendar, create_event, check_availability]