from typing import Any, Text, Dict, List
import os, requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

class ActionSetCanalActual(Action):
    def name(self) -> Text:
        return "action_set_canal_actual"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        canal = tracker.get_latest_input_channel()
        print(f"[Actions.py] Canal actual: {canal}")
        return [SlotSet("canal_actual", canal)]

# ============================
# NUEVA CLASE PARA LLM (Ollama)
# ============================

# actions.py
from typing import Any, Text, Dict, List
import requests
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

def build_history(tracker: Tracker, max_pairs: int = 6) -> List[Dict[str, str]]:
    """
    Devuelve historial en formato chat para Ollama: [{"role":"user"|"assistant","content":...}]
    Toma los últimos `max_pairs` pares (user/bot). Omite eventos sin texto.
    """
    msgs: List[Dict[str, str]] = []
    for e in tracker.events:
        et = e.get("event")
        if et == "user":
            txt = (e.get("text") or "").strip()
            if txt:
                msgs.append({"role": "user", "content": txt})
        elif et == "bot":
            # BotUttered puede traer 'text' o 'data' con 'text'
            txt = (e.get("text") or e.get("data", {}).get("text") or "").strip()
            if txt:
                msgs.append({"role": "assistant", "content": txt})

    # Quédate con los últimos turnos
    # (cada par son 2 mensajes aprox., por eso 2*max_pairs)
    return msgs[-(2 * max_pairs):]

class ActionLlmReply(Action):
    def name(self) -> Text:
        return "action_llm_reply"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        user_msg = tracker.latest_message.get("text", "").strip()

        # Construye historial
        history = build_history(tracker, max_pairs=6)
        # Asegura que el último mensaje del usuario esté presente (por si el evento aún no estaba)
        if not history or history[-1].get("content") != user_msg:
            history.append({"role": "user", "content": user_msg})

        system_msg = {
            "role": "system",
            "content": (
                "Eres un asistente breve y preciso. Responde en español claro, en 1-3 frases. "
                "Si la pregunta requiere contexto previo, utilízalo del historial. "
                "Si no tienes la información, dilo sin inventar y sugiere cómo conseguirla."
            )
        }

        messages = [system_msg] + history

        try:
            # Chat endpoint de Ollama: mantiene coherencia de diálogo
            r = requests.post(
                "http://127.0.0.1:11434/api/chat",
                json={
                    "model": "llama3.1:8b",
                    "messages": messages,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.9}
                },
                timeout=60
            )
            r.raise_for_status()
            data = r.json()
            # /api/chat devuelve {"message": {"role":"assistant","content":"..."} , ...}
            text = (data.get("message", {}) or {}).get("content", "") or "No tengo respuesta fiable ahora mismo."
        except Exception as ex:
            text = f"No pude contactar al modelo local. Detalle: {ex}"

        dispatcher.utter_message(text=text)
        return []
