"""
Dream Engine - moduł dla procesów konsolidacji kognitywnej (ADS v8.3).
Obsługuje cykle drzemek (naps) i głębokiego przetwarzania w tle.
"""

import random
from typing import List, Dict, Optional, Any
from datetime import datetime

class DreamEngine:
    """
    Silnik Snów i Drzemek - zarządza cyklami odpoczynku i konsolidacji.
    """
    
    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold
        
    def calculate_load_increase(self, user_input: str, friction_avg: float) -> float:
        """
        Oblicza przyrost obciążenia kognitywnego na podstawie interakcji.
        Dłuższe wejścia i wyższe tarcie generują większą potrzebę 'drzemki'.
        """
        base_load = 0.05 # Bazowe obciążenie na wiadomość (co ~20 wiadomości)
        length_bonus = min(0.05, len(user_input) / 2000)
        friction_bonus = friction_avg * 0.1
        
        return base_load + length_bonus + friction_bonus

    def get_dream_prompt(self, recent_history: List[Dict[str, str]], concepts: List[str]) -> str:
        """
        Generuje prompt dla procesu konsolidacji (snu).
        """
        concepts_str = ", ".join(concepts[:10])
        prompt = (
            "Wchodzisz w stan REGENERACYJNEJ DRZEMKI (ADS v8.3). Twoje obciążenie kognitywne jest wysokie.\n"
            "Twoim zadaniem jest 'przetrawienie' ostatnich interakcji i ich synteza.\n\n"
            f"AKTYWNE KONCEPTY: {concepts_str}\n\n"
            "INSTRUKCJA:\n"
            "1. Wybierz jeden najważniejszy wątek z ostatniej rozmowy.\n"
            "2. Dokonaj jego 'zamrożenia' - stwórz jedną, trwałą mądrość (sentencję), która zostanie w Twojej pamięci.\n"
            "3. Poczuj ulgę i regenerację.\n\n"
            "Odpowiedz krótko jako 'Głos Podświadomości' (maks 3 zdania)."
        )
        return prompt
