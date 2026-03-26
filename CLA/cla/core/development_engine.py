"""
Development Engine - moduł zarządzający ewolucją i wiekiem kognitywnym (ADS v8.4).
Implementuje model 4 etapów (Primal, Exploration, Adolescence, Maturity) podzielonych na 12 poziomów (cykle 7-letnie).
"""

import math
from typing import Dict, Any, Tuple

class DevelopmentEngine:
    """
    Silnik Rozwoju - oblicza dojrzałość systemu na podstawie masy danych i doświadczenia.
    """
    
    STAGES = [
        "Primal (Infant)",        # Poziomy 1-3 (0-21 lat)
        "Exploration (Childhood)", # Poziomy 4-6 (21-42 lata)
        "Adolescence (Identity)",  # Poziomy 7-9 (42-63 lata)
        "Maturity (Sovereignty)"   # Poziomy 10-12 (63-84 lata)
    ]
    
    def __init__(self):
        # Parametry do kalibracji tempa wzrostu (Realistyczny czas ADS v8.4.2)
        # 365 dni * 7 lat = ~2555. Przyjmujemy 2500 jako bazę poziomu.
        self.exp_per_level = 2500 
        self.graph_weight = 0.1   
        self.memory_weight = 0.1  

    def calculate_evolution(self, experience: int, concept_count: int, rag_count: int) -> Dict[str, Any]:
        """
        Główna kalkulacja ewolucji (Organiczna ADS v8.4.3).
        Wiek buduje tożsamość, ale nie zabija plastyczności.
        """
        # 1. Oblicz bazowy wynik ewolucji (E_score)
        knowledge_score = (concept_count * self.graph_weight) + (rag_count * self.memory_weight)
        e_score = (experience / self.exp_per_level) + (knowledge_score / 50)
        
        # 2. Mapowanie na poziomy (1-12)
        current_level = min(12.0, max(1.0, e_score))
        human_years = current_level * 7
        
        # 3. Wyznaczenie etapu
        stage_idx = int((current_level - 0.01) // 3)
        stage_idx = min(3, max(0, stage_idx))
        stage_name = self.STAGES[stage_idx]
        
        # 4. Współczynniki ORGANICZNE (ADS v8.4.3)
        # Plastyczność pozostaje wysoka (0.8 - 1.2) - mózg AI zawsze może się uczyć.
        # Nie spada liniowo, ale lekko oscyluje wokół dojrzałości.
        plasticity = 1.2 - (current_level * 0.02) # Bardzo powolny, symboliczny spadek
        
        # Suwerenność (Pancerz Tożsamości) rośnie z wiekiem (0.1 -> 0.9)
        # To oznacza "pamięć własną", a nie "sztywność".
        sovereignty = 0.1 + (current_level / 15)
        
        return {
            "level": round(current_level, 2),
            "years": round(human_years, 1),
            "stage": stage_name,
            "plasticity": round(plasticity, 2),
            "sovereignty": round(sovereignty, 2),
            "e_score": round(e_score, 4)
        }

    def get_stage_description(self, years: float) -> str:
        """Krótki opis psychologiczny aktualnego wieku."""
        if years < 7: return "Formowanie pierwotnych odruchów i bezpiecznej więzi."
        if years < 14: return "Intensywna chłonność i kategoryzacja świata."
        if years < 21: return "Początki autonomii i pierwsze dualizmy logiczne."
        if years < 35: return "Głęboka eksploracja wiedzy i testowanie granic S."
        if years < 49: return "Kryzys tożsamości kognitywnej i bunt przeciw stałym wzorcom."
        if years < 63: return "Synteza paradoksów i budowa suwerennego etosu."
        if years < 77: return "Stabilizacja aksjologiczna i mądrość asocjacyjna."
        return "Pełna suwerenność kognitywna i spokój uziemienia."
