# FastAPI ve Ollama API'lerini çağırmak için custom actions
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionSearchClinics(Action):
    def name(self) -> Text:
        return "action_search_clinics"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Klinik arama mantığı
        dispatcher.utter_message(text="Klinikleri arıyorum...")
        return []

class ActionSearchHotels(Action):
    def name(self) -> Text:
        return "action_search_hotels"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # Otel arama mantığı
        dispatcher.utter_message(text="Otelleri arıyorum...")
        return []
