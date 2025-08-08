from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
from rasa_sdk.events import *

class ActionSetCanalActual(Action):
    def name(self) -> Text:
        return "action_set_canal_actual"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        canal = tracker.get_latest_input_channel()
        print(f"[Actions.py] Canal actual: {canal}")
        
        return [SlotSet("canal_actual", canal)]