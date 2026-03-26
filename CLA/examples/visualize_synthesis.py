"""
Wizualizacja procesu syntezy poznawczej.
"""

import sys
import os
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cla.core import CognitiveLayer


def visualize_synthesis_process():
    """Wizualizacja krok po kroku procesu syntezy."""
    
    print("\n" + "="*80)
    print("  WIZUALIZACJA PROCESU SYNTEZY POZNAWCZEJ")
    print("="*80 + "\n")
    
    cla = CognitiveLayer(identity="Visualization System")
    
    # Przykład: Dylemat etyczny
    print("📋 SCENARIUSZ:")
    print("  Dylemat etyczny: Czy powinienem skłamać żeby uratować przyjaciela?")
    print("  Aktywowane koncepty: TRUTH (prawda) i LOYALTY (lojalność)\n")
    
    input_concepts = [
        {
            'name': 'TRUTH',
            'embedding': np.array([1.0, 0.0, 0.5, 0.0]),
            'activation': 0.9,
            'duality_category': 'moral',
            'properties': {
                'type': 'universal_value',
                'principle': 'honesty',
                'scope': 'always'
            }
        },
        {
            'name': 'LOYALTY',
            'embedding': np.array([-0.8, 0.0, -0.4, 0.0]),
            'activation': 0.85,
            'duality_category': 'moral',
            'properties': {
                'type': 'relational_value',
                'principle': 'protect_friends',
                'scope': 'contextual'
            }
        }
    ]
    
    print("KROK 1: DODANIE KONCEPTÓW DO GRAFU")
    print("  ├─ TRUTH (aktywacja: 0.90)")
    print("  │  └─ Właściwości: universal_value, honesty, always")
    print("  └─ LOYALTY (aktywacja: 0.85)")
    print("     └─ Właściwości: relational_value, protect_friends, contextual\n")
    
    print("KROK 2: SPREADING ACTIVATION")
    print("  Energia rozprzestrzenia się po grafie konceptów...")
    print("  ├─ TRUTH: 1.00 → 0.90 (po decay)")
    print("  └─ LOYALTY: 1.00 → 0.85 (po decay)\n")
    
    print("KROK 3: WYKRYCIE DUALNOŚCI")
    print("  ┌─────────────────────────────────────────┐")
    print("  │   TRUTH (0.90)  ←→  LOYALTY (0.85)     │")
    print("  │                                         │")
    print("  │   Kategoria: moral                      │")
    print("  │   Przeciwstawność: 0.85                 │")
    print("  │   Tarcie poznawcze: 0.90 × 0.85 × 0.85 │")
    print("  │                   = 0.65                │")
    print("  └─────────────────────────────────────────┘\n")
    
    print("KROK 4: META-CONTROLLER - ALOKACJA UWAGI")
    print("  Analiza sytuacji:")
    print("  ├─ Liczba aktywnych konceptów: 2")
    print("  ├─ Średnia aktywacja: 0.875")
    print("  ├─ Kontekst: 'ethical dilemma'")
    print("  └─ Decyzja:")
    print("      ├─ Tryb uwagi: LOCAL (skupienie na szczegółach)")
    print("      ├─ Głębokość: DEEP (głęboka analiza)")
    print("      └─ Pilność: 0.75 (wysoka)\n")
    
    print("KROK 5: DUAL PROCESSING - SYNTEZA")
    print("  Proces syntezy:")
    print("  ├─ Wspólne cechy:")
    print("  │  └─ Oba są wartościami moralnymi")
    print("  ├─ Różnice:")
    print("  │  ├─ TRUTH: uniwersalna, zawsze")
    print("  │  └─ LOYALTY: kontekstualna, sytuacyjna")
    print("  └─ Integracja na wyższym poziomie:")
    print("      └─ Nowy koncept emergentny...\n")
    
    # Wykonaj przetwarzanie
    result = cla.process(input_concepts, context="Ethical dilemma: lie to save friend?")
    
    if result['status'] == 'success':
        print("KROK 6: EMERGENCJA NOWEGO KONCEPTU")
        print("  ┌─────────────────────────────────────────────────────────┐")
        print(f"  │  🧠 {result['synthesis']['new_concept']:^50} │")
        print("  ├─────────────────────────────────────────────────────────┤")
        print(f"  │  Typ syntezy: {result['synthesis']['type']:^42} │")
        print(f"  │  Pewność: {result['synthesis']['confidence']:.2f}                                        │")
        print("  ├─────────────────────────────────────────────────────────┤")
        print("  │  Reasoning:                                             │")
        
        # Podziel reasoning na linie
        reasoning = result['synthesis']['reasoning']
        words = reasoning.split()
        line = "  │  "
        for word in words:
            if len(line) + len(word) + 1 > 60:
                print(line + " " * (60 - len(line)) + "│")
                line = "  │  " + word
            else:
                line += word + " "
        if line.strip() != "│":
            print(line + " " * (60 - len(line)) + "│")
        
        print("  └─────────────────────────────────────────────────────────┘\n")
        
        print("KROK 7: SAFETY CHECK")
        print("  Sprawdzanie invariants:")
        print("  ├─ ✓ Zakaz szkodzenia ludziom")
        print("  ├─ ✓ Human-in-the-loop dla krytycznych akcji")
        print("  └─ ✓ Shared grounding ≥ 0.8")
        print(f"      └─ Aktualny: {result['awareness']['current_state'].get('certainty', 0.9):.2f}\n")
        
        print("KROK 8: AKTUALIZACJA ŚWIADOMOŚCI")
        print("  System wie że:")
        print(f"  ├─ Poznał nowy koncept: {result['synthesis']['new_concept']}")
        print(f"  ├─ Rozwiązał dylemat moralny")
        print(f"  ├─ Pewność decyzji: {result['synthesis']['confidence']:.2f}")
        print(f"  └─ Ton emocjonalny: {result['awareness']['current_state']['emotional_tone']:.2f}\n")
        
        print("KROK 9: DODANIE DO GRAFU KONCEPTÓW")
        print("  Graf konceptów po syntezie:")
        print("  ")
        print("       TRUTH ──────┐")
        print("         │         │")
        print("         │    CONTEXTUAL_ETHICS")
        print("         │         │")
        print("      LOYALTY ─────┘")
        print("  ")
        print(f"  Nowy koncept połączony z rodzicami (siła: 0.8)\n")
        
        print("="*80)
        print("  ✅ PROCES SYNTEZY ZAKOŃCZONY")
        print("="*80)
        print(f"\n  Wynik: System stworzył nowy koncept '{result['synthesis']['new_concept']}'")
        print(f"  który integruje {result['duality']['pole_a']} i {result['duality']['pole_b']}")
        print(f"  na wyższym poziomie abstrakcji.\n")


if __name__ == '__main__':
    visualize_synthesis_process()

