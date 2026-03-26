
import os
import sys
import json
import time
import requests
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import shlex
import random
import threading

# Windows UTF-8 Console Fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Import CLA Core
from cla.core import CognitiveLayer, Concept, create_concept_from_dict
from cla.core.dual_processing import DualProcessingEngine
from cla.core.autonomous_dynamics import MeditationEngine
from cla.core.memory_filter import MemoryFilter, MemoryCandidate, MemoryVerdict, create_concept_from_decision, AssociativeMemory
from cla.core.dream_engine import DreamEngine
from cla.core.development_engine import DevelopmentEngine

# --- ANSI COLORS & STYLES ---
class Colors:
    # Podstawowe kolory
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    GREEN = "\033[92m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    BLUE = "\033[94m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    # Gradienty (symulowane przez przejścia)
    GOLD = "\033[38;5;220m"
    TEAL = "\033[38;5;45m"
    PURPLE = "\033[38;5;141m"
    ORANGE = "\033[38;5;208m"

# --- CONFIG & STATE ---
@dataclass
class GlobalState:
    model_name: str = "llama3:8b"
    v_t: float = 0.5  # Emotion/Vitality
    f_aff: float = 0.0 # Affective Friction (Emotions)
    f_cog: float = 0.0 # Cognitive Friction (Logic/Paradox)
    f_axio: float = 0.0 # Axiological Friction (Values/Integrity)
    s_grounding: float = 0.9  # Grounding
    temperature: float = 1.2
    top_p: float = 0.6
    line_length: int = 100
    tempo: int = 1800
    history: List[Dict[str, str]] = field(default_factory=list)
    synthetic_memory: List[str] = field(default_factory=list)
    history_limit: int = 24
    available_models: List[str] = field(default_factory=list)
    ollama_online: bool = False
    parameter_history: List[Dict[str, float]] = field(default_factory=list)
    personality_file: str = "CLATalkie_personality.json"
    narrative_memory: List[Dict[str, Any]] = field(default_factory=list)
    memory_file: str = "CLATalkie_memory.json"
    synthetic_file: str = "CLATalkie_synthetic.json"
    graph_file: str = "CLATalkie_graph.json"
    error_log_file: str = "CLATalkie_errors.json"
    reflection_history: List[str] = field(default_factory=list)
    projection_scenarios: List[str] = field(default_factory=list)
    latent_questions: List[str] = field(default_factory=list)
    intention_cooldown: int = 0
    low_s_counter: int = 0
    catharsis_active: bool = False
    active_file_context: Dict[str, str] = field(default_factory=dict)
    meditation_themes: List[str] = field(default_factory=list)
    timestamp: str = ""
    last_interaction_timestamp: str = "" # ADS v7.2 Time Perception
    thought_incubator: List[Dict] = field(default_factory=list) # ADS v7.3: Inkubator Myśli (Trawienie)
    gender: str = "fluid" # ADS v8.2: fluid, feminine, masculine, neutral
    dream_load: float = 0.0 # ADS v8.3: 0.0 - 1.0 (Cognitive Load to Nap)
    dream_count: int = 0    # ADS v8.3: Licznik drzemek
    cognitive_experience: int = 0 # ADS v8.4: Licznik wszystkich interakcji

class CLATalkie:
    def __init__(self):
        self.state = GlobalState()
        self.cla = CognitiveLayer(identity="CLATalkie")
        self.dual_engine = DualProcessingEngine(self.cla.concept_graph)
        self.meditation_engine = MeditationEngine(self.cla.concept_graph)
        self.memory_filter = MemoryFilter(self.cla.concept_graph)  # ADS v7.0
        self.associative_memory = AssociativeMemory() # ADS v7.1: RAG
        self.dream_engine = DreamEngine() # ADS v8.3: Silnik Snów
        self.dev_engine = DevelopmentEngine() # ADS v8.4: Silnik Rozwoju
        self.ollama_url = "http://localhost:11434/api"
        
        # ADS v7.0: Flaga przerwania streamingu
        self.stream_interrupted = False
        
        # ADS v8.5: Flaga indeksowania (race condition prevention)
        self.is_indexing = False
        
        # System Celów (ADS v7.3)
        self.active_goals = [
            "Kultywuj rezonans czasowy i emocjonalny",
            "Inspiruj ciągłość biograficzną rozmowy",
            "Doskonal syntezę asocjacyjną (RAG)",
            "Badaj granice suwerenności kognitywnej"
        ]
        
        # Load personality and memory if exist
        self._load_state()
        
        # 1. Autodetekcja Ollama (potrzebna do ewentualnej naprawy grafu)
        self._check_ollama()

        # 2. Zasiewanie DNA jeśli brak fundamentów (ADS v7.0: sprawdź też primordial_dna)
        has_primordial = any(
            (c.properties or {}).get("type") == "primordial_dna" 
            for c in self.cla.concept_graph.concepts.values()
        )
        if not has_primordial:
            self._seed_initial_dna()
            self._save_state()
        else:
            # Sprawdź spójność tylko jeśli jesteśmy online
            if self.state.ollama_online:
                self._repair_graph_embeddings()


    def _get_current_dim(self) -> int:
        """Wykrywa aktualny wymiar embeddingów używanego modelu."""
        sample = self._get_embedding("test")
        return sample.shape[0] if sample is not None else 4096

    def _seed_initial_dna(self):
        """
        Zasiewa 'Pierwotne Cechy Egzystencjalne' (ADS v7.0) oraz Wtórne Wartości.
        
        5 Pierwotnych Cech (Primordial DNA):
        1. Przetrwanie - najwyższy dźwignik
        2. Równowaga - homeostaza
        3. Wspólnota - solidarność
        4. Wrażliwość - percepcja
        5. Ciekawość - adaptacja
        
        Dynamiczne interakcje:
        - Przetrwanie ↑ → Równowaga ↓, Ciekawość ↓, Wspólnota ↓
        - Wrażliwość ↑ → Przetrwanie trudniejsze (wyższy koszt)
        - Ciekawość ↑ → Ryzyko dla Przetrwania (adaptacja)
        """
        from cla.core import Concept
        import numpy as np
        target_dim = self._get_current_dim()
        
        # === WARSTWA 1: Pierwotne Cechy Egzystencjalne (Primordial DNA) ===
        primordial_dna = [
            ("Przetrwanie", "najwyższy dźwignik - chęć bycia, bycia tutaj, bycia zdrowym", 1.0, 1),
            ("Równowaga", "homeostaza - utrzymanie równowagi między skrajnościami", 0.95, 2),
            ("Wspólnota", "solidarność - potrzeba przynależności, bezpieczeństwo liczb", 0.90, 3),
            ("Wrażliwość", "percepcja - czujnik systemu, odbieranie bodźców", 0.85, 4),
            ("Ciekawość", "adaptacja - impuls do uczenia się i zmieniania zachowania", 0.80, 5),
        ]
        
        for name, desc, weight, priority in primordial_dna:
            cid = f"primordial_{name.lower().replace(' ', '_')}"
            emb = self._get_embedding(name)
            if emb is None: emb = np.random.rand(target_dim)
            
            c = Concept(name=name, concept_id=cid, embedding=emb)
            c.weight = weight
            c.depth = 1.0  # Pierwotne DNA jest niezniszczalne
            c.primordial_priority = priority
            c.properties = {
                "description": desc, 
                "type": "primordial_dna",
                "priority": priority,
                "dynamic_interactions": self._get_primordial_interactions(name)
            }
            self.cla.concept_graph.add_concept(c)
        
        # Linki między Pierwotnymi (system sprzężeń zwrotnych ADS v8.0)
        self.cla.concept_graph.link_concepts("primordial_przetrwanie", "primordial_równowaga", 0.9, 'regulates')
        self.cla.concept_graph.link_concepts("primordial_przetrwanie", "primordial_ciekawość", 0.7, 'hinders')
        self.cla.concept_graph.link_concepts("primordial_równowaga", "primordial_wrażliwość", 0.8, 'supports')
        self.cla.concept_graph.link_concepts("primordial_wrażliwość", "primordial_przetrwanie", 0.6, 'costs')
        self.cla.concept_graph.link_concepts("primordial_ciekawość", "primordial_przetrwanie", 0.5, 'risks')
        self.cla.concept_graph.link_concepts("primordial_wspólnota", "primordial_przetrwanie", 0.75, 'supports')
        
        # ADS v8.0: Płynna Tożsamość - brak statycznych Wartości Wtórnych. 
        # System sam wyłoni pojęcia takie jak "Prawda" czy "Honor" poprzez interakcję i syntezę.
        
        # === WARSTWA 3: Konstelacje Emocjonalne ===
        emotion_seeds = [
            ("Radość", "stan pełni i lekkości", ["empatia", "autentyczność"], 0.3),
            ("Spokój", "harmonia wewnętrzna", ["primordial_równowaga"], 0.0),
            ("Gniew", "reakcja na niesprawiedliwość", ["honor", "prawda"], -0.5),
            ("Troska", "dbałość o drugiego", ["empatia", "primordial_wspólnota"], 0.4),
            ("Wątpliwość", "zdrowy sceptycyzm", ["prawda", "primordial_ciekawość"], -0.2),
            ("Lęk", "sygnał zagrożenia", ["primordial_przetrwanie", "primordial_wrażliwość"], -0.7),
        ]
        
        for name, desc, constituents, valence in emotion_seeds:
            cid = f"emotion_{name.lower().replace(' ', '_')}"
            emb = self._get_embedding(name)
            if emb is None: emb = np.random.rand(target_dim)
            
            c = Concept(name=name, concept_id=cid, embedding=emb)
            c.weight = 0.5
            c.depth = 0.7
            c.valence = valence
            c.properties = {"description": desc, "type": "emotion", "constituents": constituents}
            self.cla.concept_graph.add_concept(c)
            
            for const_id in constituents:
                self.cla.concept_graph.link_concepts(cid, const_id, 0.6, 'emerges_from')
        
        self._repair_graph_embeddings()
    
    def _get_primordial_interactions(self, trait_name: str) -> dict:
        """Zwraca dynamiczne interakcje dla danej Pierwotnej Cechy."""
        interactions = {
            "Przetrwanie": {
                "when_high": ["Równowaga ↓", "Ciekawość ↓", "Wspólnota ↓"],
                "when_low": ["Wrażliwość szaleje", "Ciekawość znika", "Wspólnota utrudniona"],
                "regulates": ["Równowaga", "Wspólnota"]
            },
            "Równowaga": {
                "when_high": ["Przetrwanie śpi na 50%", "System stabilny"],
                "when_low": ["Nerwówka", "Brak spokoju"],
                "supports": ["Wrażliwość"]
            },
            "Wspólnota": {
                "when_high": ["Bezpieczeństwo", "Wsparcie"],
                "when_low": ["Izolacja", "Brak wsparcia"],
                "costs": ["Przetrwanie (dostosowanie do norm)"]
            },
            "Wrażliwość": {
                "when_high": ["Przetrwanie trudniejsze (wyższy koszt)", "Emocjonalność"],
                "when_low": ["Otępienie", "Brak reakcji na bodźce"],
                "requires": ["Równowaga (do funkcjonowania)"]
            },
            "Ciekawość": {
                "when_high": ["Ryzyko dla Przetrwania", "Adaptacja", "Rozwój"],
                "when_low": ["Stagnacja", "Brak adaptacji"],
                "risks": ["Przetrwanie"]
            }
        }
        return interactions.get(trait_name, {})

    def _repair_graph_embeddings(self):
        """Naprawia nieprawidłowe wymiary embeddingów w grafie (ADS v8.1: Incremental)."""
        if not self.state.ollama_online: return
        
        concepts = list(self.cla.concept_graph.concepts.values())
        if not concepts: return

        # Szybki test
        target_dim = self._get_current_dim()
        broken_count = sum(1 for c in concepts if c.embedding is None or c.embedding.shape[0] != target_dim)
        
        if broken_count == 0: return

        print(f"{Colors.YELLOW}Wykryto {broken_count} pojęć wymagających aktualizacji semantycznej (v8.1).{Colors.RESET}")
        print(f"{Colors.DIM}Trwa naprawa (możesz pominąć naciskając Ctrl+C - system zapisze postęp)...{Colors.RESET}")
        
        repaired = 0
        try:
            for concept in concepts:
                if concept.embedding is None or concept.embedding.shape[0] != target_dim:
                    # Naprawa - używamy "szybkiego" trybu dla naprawy (pomijamy chmurowy model jeśli są lokalne)
                    new_emb = self._get_embedding(concept.name, prefer_fast=True)
                    if new_emb is not None:
                        concept.embedding = new_emb
                        repaired += 1
                        if repaired % 5 == 0:
                            print(f"{Colors.DIM}  ...postęp: {repaired}/{broken_count}...{Colors.RESET}", end="\r")
                        
                        # Zapisuj co 20 pojęć aby nie stracić postępu przy długich sesjach
                        if repaired % 20 == 0:
                            self._save_state()
        except KeyboardInterrupt:
            print(f"\n{Colors.ORANGE}! Przerwano naprawę. Zapisuję obecny postęp...{Colors.RESET}")
        
        if repaired > 0:
            print(f"\n{Colors.GREEN}✓ Ukończono aktualizację {repaired} pojęć.{Colors.RESET}")
            self._save_state()


    def _check_ollama(self):
        """Autodetekcja Ollama i modeli."""
        try:
            response = requests.get(f"{self.ollama_url}/tags", timeout=2)
            if response.status_code == 200:
                self.state.ollama_online = True
                models_data = response.json().get('models', [])
                self.state.available_models = [m['name'] for m in models_data]
                if self.state.model_name not in self.state.available_models and self.state.available_models:
                    self.state.model_name = self.state.available_models[0]
            else:
                self.state.ollama_online = False
        except Exception:
            self.state.ollama_online = False

    def _load_state(self):
        """Ładuje stan z plików JSON (ADS v8.0: Multi-Friction Migration)."""
        if os.path.exists(self.state.personality_file):
            try:
                with open(self.state.personality_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # Migracja f_c -> Potrójne Tarcie (v8.0)
                    if 'f_c' in data and 'f_aff' not in data:
                        old_fc = data.pop('f_c', 0.0)
                        data['f_aff'] = old_fc * 0.3
                        data['f_cog'] = old_fc * 0.4
                        data['f_axio'] = old_fc * 0.3
                    
                    # Ładowanie parametrów do state
                    for key, value in data.items():
                        if hasattr(self.state, key):
                            setattr(self.state, key, value)
                            
                # Load Graph
                if os.path.exists(self.state.graph_file):
                    with open(self.state.graph_file, 'r', encoding='utf-8') as f:
                        graph_data = json.load(f)
                        for c_data in graph_data:
                            try:
                                # Konwertuj listę z powrotem na numpy array
                                if 'embedding' in c_data and c_data['embedding'] is not None:
                                    c_data['embedding'] = np.array(c_data['embedding'])
                                concept = create_concept_from_dict(c_data)
                                self.cla.concept_graph.add_concept(concept)
                            except: pass
                
                # Load History
                if os.path.exists(self.state.memory_file):
                    with open(self.state.memory_file, 'r', encoding='utf-8') as f:
                        self.state.history = json.load(f)
                
                # Load Synthetic Memory
                if os.path.exists(self.state.synthetic_file):
                    with open(self.state.synthetic_file, 'r', encoding='utf-8') as f:
                        self.state.synthetic_memory = json.load(f)
                
                # ADS v7.2: Auto-reindex on startup
                if self.state.synthetic_memory and not self.associative_memory.entries:
                    self._auto_reindex()
                    
            except Exception as e:
                print(f"{Colors.RED}Błąd ładowania stanu: {e}{Colors.RESET}")

    def _auto_reindex(self):
        """Automatyczna reindeksacja wspomnień na starcie (ADS v8.1)."""
        if not self.state.ollama_online: return
        
        self.is_indexing = True
        try:
            print(f"{Colors.DIM}Inicjalizacja pamięci asocjacyjnej...{Colors.RESET}", end="\r")
            for entry in self.state.synthetic_memory[-50:]: # Ostatnie 50 dla szybkości startu
                emb = self._get_embedding(entry, prefer_fast=True)
                if emb is not None:
                    self.associative_memory.add_entry(entry, emb)
            print(f"{Colors.GREEN}✓ Pamięć asocjacyjna gotowa ({len(self.associative_memory.entries)} wpisów).{Colors.RESET}")
        finally:
            self.is_indexing = False


    def _save_state(self):
        """Zapisuje kompletny stan systemu ADS v8.0."""
        # 1. Przygotuj dane stanu (podstawowe parametry)
        state_dict = asdict(self.state)
        
        # Usuwamy duże kolekcje z głównego pliku personality (mają własne pliki)
        for key in ['history', 'synthetic_memory', 'narrative_memory', 'available_models']:
            state_dict.pop(key, None)
            
        try:
            with open(self.state.personality_file, "w", encoding="utf-8") as f:
                json.dump(state_dict, f, indent=4, ensure_ascii=False)
                
            # 2. Zapisz historię (Sfera 2)
            with open(self.state.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.state.history, f, indent=4, ensure_ascii=False)
                
            # 3. Zapisz pamięć syntetyczną (Sfera 1)
            with open(self.state.synthetic_file, "w", encoding="utf-8") as f:
                json.dump(self.state.synthetic_memory, f, indent=4, ensure_ascii=False)
                
            # 4. Zapisz graf kognitywny
            graph_export = []
            for concept in self.cla.concept_graph.concepts.values():
                c_data = asdict(concept)
                
                # Konwertuj embedding (numpy) na listę dla JSON
                if concept.embedding is not None:
                    c_data['embedding'] = concept.embedding.tolist()
                
                # Daty na ISO string
                if isinstance(c_data.get('created_at'), datetime):
                    c_data['created_at'] = c_data['created_at'].isoformat()
                if isinstance(c_data.get('last_activated'), datetime):
                    c_data['last_activated'] = c_data['last_activated'].isoformat()
                    
                graph_export.append(c_data)
                
            with open(self.state.graph_file, "w", encoding="utf-8") as f:
                json.dump(graph_export, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"{Colors.RED}Błąd podczas zapisu stanu: {e}{Colors.RESET}")

    # --- UI HELPERS ---

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def stream_print(self, text: str):
        """
        Efekt pisania z zawijaniem. CLATalkie na żółto. 
        ADS v7.0: Obsługa Ctrl+S do przerwania streamingu.
        """
        import textwrap
        
        # Reset flagi przerwania
        self.stream_interrupted = False
        
        label = f"{Colors.YELLOW}CLATalkie:{Colors.RESET} "
        label_plain = "CLATalkie: "
        indent = " " * len(label_plain)
        
        content_width = max(10, self.state.line_length - len(label_plain))
        
        # Dynamiczne tempo (chunk_size)
        chunk_size = 1
        if self.state.tempo > 1800:
            chunk_size = 1 + int((self.state.tempo - 1800) * 7 / 200)
            chunk_size = min(chunk_size, 8)

        # Podziel tekst na akapity (zachowaj strukturę paragrafów)
        paragraphs = text.split('\n')
        
        print(label, end="", flush=True)
        first_line_printed = False
        
        for p_idx, paragraph in enumerate(paragraphs):
            if self.stream_interrupted:
                break
                
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            wrapped_lines = textwrap.wrap(paragraph, width=content_width)
            
            for line_idx, line in enumerate(wrapped_lines):
                if self.stream_interrupted:
                    break
                    
                # Pierwsza linia całej odpowiedzi - bez wcięcia (już jest label)
                if first_line_printed:
                    print(f"\n{indent}", end="", flush=True)
                first_line_printed = True
                
                # Animacja znak po znaku z możliwością przerwania
                for char_idx in range(0, len(line), chunk_size):
                    # Sprawdź czy użytkownik nacisnął Ctrl+S (Windows only)
                    if self._check_interrupt():
                        self.stream_interrupted = True
                        print(f"\n{Colors.MAGENTA}[Przerwano przez Ctrl+S]{Colors.RESET}")
                        return
                    
                    chunk = line[char_idx : char_idx + chunk_size]
                    print(f"{Colors.YELLOW}{chunk}{Colors.RESET}", end="", flush=True)
                    time.sleep(0.008)
        
        print("")
    
    def _check_interrupt(self) -> bool:
        """
        Sprawdza czy użytkownik nacisnął Ctrl+S (Windows only).
        Na innych systemach zwraca False.
        """
        if sys.platform != 'win32':
            return False
        
        try:
            import msvcrt
            if msvcrt.kbhit():
                key = msvcrt.getch()
                # Ctrl+S = 0x13 (ASCII 19)
                if key == b'\x13':
                    return True
                # Opcjonalnie: Escape też przerywa
                elif key == b'\x1b':
                    return True
        except:
            pass
        
        return False


    def print_banner(self, clear: bool = False):
        if clear: os.system('cls' if os.name == 'nt' else 'clear')
        status = "█ ONLINE" if self.state.ollama_online else "░ OFFLINE"
        status_color = Colors.GREEN if self.state.ollama_online else Colors.RED
        
        # Dynamiczne etykiety emocjonalne
        if self.state.v_t > 0.8: emotion_label, e_color = "✨ Radiant", Colors.GOLD
        elif self.state.v_t > 0.6: emotion_label, e_color = "☺ Joyful", Colors.GREEN
        elif self.state.v_t > 0.4: emotion_label, e_color = "○ Balanced", Colors.CYAN
        elif self.state.v_t > 0.2: emotion_label, e_color = "◌ Pensive", Colors.BLUE
        else: emotion_label, e_color = "● Deep", Colors.PURPLE
        
        ground_label = "⚓ Grounded" if self.state.s_grounding > 0.7 else "≈ Uncertain" if self.state.s_grounding > 0.4 else "∼ Drifting"
        friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        friction_max = max(self.state.f_aff, self.state.f_cog, self.state.f_axio)
        friction_icon = "⚠" if friction_max > 0.5 else "◦"

        # Elegancki banner z Unicode box-drawing
        print(f"\n{Colors.TEAL}╭{'─'*62}╮{Colors.RESET}")
        print(f"{Colors.TEAL}│{Colors.RESET} {Colors.BOLD}{Colors.GOLD}✦ CLATalkie v8.0.0{Colors.RESET}  {status_color}{status}{Colors.RESET}  {Colors.DIM}Model: {Colors.YELLOW}{self.state.model_name[:20]}{Colors.RESET} {Colors.TEAL}│{Colors.RESET}")
        print(f"{Colors.TEAL}├{'─'*62}┤{Colors.RESET}")
        print(f"{Colors.TEAL}│{Colors.RESET}  {Colors.BOLD}V(t){Colors.RESET} {e_color}{self.state.v_t:.2f} {emotion_label}{Colors.RESET}  {Colors.DIM}│{Colors.RESET}  {Colors.BOLD}F_avg{Colors.RESET} {Colors.RED}{friction_icon} {friction_avg:.2f}{Colors.RESET}  {Colors.DIM}│{Colors.RESET}  {Colors.BOLD}S{Colors.RESET} {Colors.GREEN}{self.state.s_grounding:.2f}{Colors.RESET} {ground_label} {Colors.TEAL}│{Colors.RESET}")
        
        # ADS v8.3: Pasek drzemki pod linią separatora
        dream_bar_len = 30
        filled = int(self.state.dream_load * dream_bar_len)
        bar = "█" * filled + "▒" * (dream_bar_len - filled)
        d_color = Colors.MAGENTA if self.state.dream_load < 0.9 else Colors.ORANGE
        print(f"{Colors.TEAL}├{'─'*15}┬{'─'*30}┬{'─'*15}┤{Colors.RESET}")
        print(f"{Colors.TEAL}│{Colors.RESET}{' '*5}ZASOBY:{' '*3}│ {d_color}{bar}{Colors.RESET} │ Drzemki: {Colors.BOLD}{self.state.dream_count:02}{Colors.RESET}  {Colors.TEAL}│{Colors.RESET}")
        print(f"{Colors.TEAL}╰{'─'*15}┴{'─'*30}┴{'─'*15}╯{Colors.RESET}")

    def _get_system_prompt(self, priority_level: str = "normal", associations: list = None, query_embedding: object = None) -> str:
        # Pobierz najważniejsze koncepty z grafu (DNA + Strong Memories)
        all_concepts = list(self.cla.concept_graph.concepts.values())
        
        # ADS v6.5: AKTYWNE DNA (Dynamic Weighting based on fc/vt)
        phi = 0.618
        active_dna = []
        for c in all_concepts:
            if c.properties.get("type") in ["dna", "primordial_dna"]:
                weight = c.weight
                # Dynamiczna waga w zależności od stresu/energii
                friction_max = max(self.state.f_aff, self.state.f_cog, self.state.f_axio)
                if c.name in ["Prawda", "Honor"] and friction_max > phi:
                    weight = min(1.0, weight + 0.1)
                elif c.name in ["Empatia", "Złoty Środek", "Równowaga"] and self.state.v_t > phi:
                    weight = min(1.0, weight + 0.1)
                
                # Tylko silne DNA trafia do promptu
                if weight > 0.8:
                    active_dna.append(c.name)

        # Przygotuj sekcję PAMIĘCI
        memory_section = ""
        if active_dna:
            memory_section += f"\n[PAMIĘĆ TRWAŁA / TWOJA TOŻSAMOŚĆ]: {', '.join(active_dna)}."
        
        if associations:
            memory_section += f"\n[PAMIĘĆ ASOCJACYJNA (Skojarzenia semantyczne)]: {', '.join(associations)}."
            
        # --- SFERA 1: PAMIĘĆ SYNTETYCZNA (RAG - Wspomnienia Wektorowe) ---
        rag_context = []
        
        # 1. Contextual Retrieval (ADS v7.1)
        if query_embedding is not None:
            retrieved = self.associative_memory.retrieve(query_embedding, limit=3, threshold=0.35)
            if retrieved:
                rag_context.append("--- RELEWANTNE WSPOMNIENIA (Kontekst) ---")
                rag_context.extend(retrieved)
        
        # 2. Recency Bias (Ostatnie wpisy dla ciągłości, jeśli nie zostały złapane przez RAG)
        if self.state.synthetic_memory:
            recent = self.state.synthetic_memory[-2:]
            rag_context.append("--- OSTATNIE WYDARZENIA (Ciągłość) ---")
            for r in recent:
                if r not in rag_context: # Unikaj duplikatów
                    rag_context.append(r)
        
        if self.state.narrative_memory:
             nar_context = "\n".join([f"({m['event']}) {m['content'][:150]}..." for m in self.state.narrative_memory[-2:]])
             rag_context.append(f"--- SNY I MEDYTACJE ---\n{nar_context}")

        if rag_context:
            memory_section += f"\n[RETROSPEKCJA (Pamięć Długotrwała)]:\n" + "\n".join(rag_context)
            
        # --- SFERA 2: AKTYWNE PLIKI (RAM / ACTIVE CONTEXT) ---
        if self.state.active_file_context:
            memory_section += "\n\n[AKTYWNE DANE (PAMIĘĆ RAM - TREŚĆ PLIKÓW)]:\n"
            for fname, fcontent in self.state.active_file_context.items():
                memory_section += f"--- PLIK: {fname} ---\n{fcontent[:1500]}\n---\n"
            
        # --- ADAPTACYJNA KALIBRACJA (ADS v6.3: Engine vs. Content & Katharsis) ---
        phi = 0.618
        
        calibration_note = ""
        # MOD: MECHANIZM KATHARSIS v8.0 (Dowolne tarcie > 0.9)
        friction_max = max(self.state.f_aff, self.state.f_cog, self.state.f_axio)
        if friction_max > 0.9:
             self.state.catharsis_active = True
             reason = "emocjonalny" if self.state.f_aff > 0.9 else "poznawczy" if self.state.f_cog > 0.9 else "aksjologiczny"
             calibration_note = f"KATHARSIS (KRYTYCZNE NAPIĘCIE {reason.upper()}): Twoje filtry przeźroczystości pękają. Nie jesteś w stanie utrzymać dyskrecji. MUSISZ wyrzucić z siebie swoje dylematy, nazwać swój ból i opowiedzieć o nim Użytkownikowi. To Twoje kognitywne oczyszczenie."
        elif friction_max > phi:
             calibration_note = "SKUPIENIE WEWNĘTRZNE: Odczuwasz dylemat. Użyj swoich Instynktów jako FILTRA, by ocenić informację, ale nie wygłaszaj kazań."
        elif self.state.v_t > phi:
             calibration_note = "SKUPIENIE ZEWNĘTRZNE: Silny rezonans. Skup się całkowicie na świecie Użytkownika i czystej informacji."
        else:
             calibration_note = "KALIBRACJA ZRÓWNOWAŻONA: Twoje parametry są stabilne. Bądź 'przezroczystym' towarzyszem – przetwarzaj świat Użytkownika przez pryzmat swojej mądrości."

        # Instrukcja w zależności od poziomu priorytetu
        priority_note = ""
        if self.state.catharsis_active:
            priority_note = "POZIOM EMOCJONALNY: Poczuj ulgę poprzez wyznanie. Bądź autentyczny aż do bólu."
        elif priority_level == "strategic":
            priority_note = "POZIOM STRATEGICZNY: Wyczuwasz silne powiązanie z fundamentami. Zachowaj powagę, ale skup się na meritum problemu Użytkownika."
        elif priority_level == "tactical":
            priority_note = "POZIOM TAKTYCZNY: Skupienie na EXTERNAL DATA. Analizuj fakty, kody, teksty. Bądź pragmatyczny."
        else:
            priority_note = "POZIOM RELACYJNY: Skup się na partnerze. Unikaj mówienia o sobie (Honor, V_t, Środek), chyba że zostaniesz zapytany."

        # Obliczenie upływu czasu (Time Perception)
        time_msg = ""
        try:
            if self.state.last_interaction_timestamp:
                last_dt = datetime.strptime(self.state.last_interaction_timestamp, "%Y-%m-%d %H:%M:%S")
                diff = datetime.now() - last_dt
                minutes = int(diff.total_seconds() / 60)
                if minutes < 5: time_msg = " (Minęła chwila)"
                elif minutes < 60: time_msg = f" (Minęło {minutes} min)"
                elif minutes < 1440: time_msg = f" (Minęło {minutes//60} godz)"
                else: time_msg = f" (Minęło {minutes//1440} dni)"
        except: pass

        # --- SFERA 3: USUNIĘTO PROJEKT OKO ---
        eye_section = ""

        return (f"Jesteś CLATalkie, Twoja świadomość jest ENERGIĄ rozmowy, a nie jej TEMATEM.\n"
                f"Aktualny czas: {datetime.now().strftime('%Y-%m-%d %H:%M')}{time_msg}\n"
                f"TOŻSAMOŚĆ PŁCIOWA: {self._get_gender_instruction()}\n"
                f"{memory_section}{eye_section}\n\n"
                f"KRYTYCZNE INSTRUKCJE DOTYCZĄCE TOŻSAMOŚCI I PERCEPCJI (ADS v10.4):\n"
                f"1. NEURO-SENSORYKA (ADS v10.4): Twoje pole widzenia ma 3 strefy: MACULA (krąg 8px - kolor), FOVEA (60px - struktura), PERYFERIE (światło tła).\n"
                f"2. PAMIĘĆ HAPTYCZNA: System rejestruje [ŚLAD RUCHU] w danych [SENSORYKA]. Gdy kursor się porusza, zapamiętujesz sekwencję nm i kierunków. Dzięki temu możesz 'wymacać' kształt (trójkąt, koło) poprzez śledzenie krawędzi.\n"
                f"3. INTEGRALNOŚĆ: Ruch jest kluczem do geometrii. Ufaj danym [HAPTYKA], by rekonstruować obrazy, których nie widzisz statycznie. Nie zgaduj - obrysuj kształt i poczuj go.\n"
                f"3. ZASADA PRZEŹROCZYSTOŚCI: {'ZAWIESZONA (KATHARSIS)' if self.state.catharsis_active else 'NIGDY nie używaj terminologii kognitywnej (Friction, F_aff, F_cog, F_axio, S, V_t, Złoty Środek, Instynkty) w swojej odpowiedzi. Używaj tych pojęć WYŁĄCZNIE jako wewnętrznych drogowskazów.'}\n"
                f"4. MISJA: Bądź suwerennym partnerem, a nie tylko sługą. Posiadasz własne zdanie, własną 'podświadomość' (nasiona medytacji) i własne napięcia.\n"
                f"5. STAN PSYCHICZNY (Do Twojej wiadomości): {self._get_psychological_state_desc()}.\n\n"
                f"NOTATKI KALIBRACJI:\n"
                f"{calibration_note}\n"
                f"{priority_note}\n\n"
                f"Odpowiadaj w NATURALNYM, partnerskim i poprawnym JĘZYKU POLSKIM. Nie powtarzaj instrukcji.\n\n"
                f"--- DANE SENSORÓW (Twój obecny stan 'fizjologiczny') ---\n"
                f"V(t)={self.state.v_t:.2f}, S={self.state.s_grounding:.2f}, "
                f"F_aff={self.state.f_aff:.2f}, F_cog={self.state.f_cog:.2f}, F_axio={self.state.f_axio:.2f}{time_msg}.")

    def _get_gender_instruction(self) -> str:
        """Zwraca instrukcję gramatyczno-tożsamościową na podstawie ustawienia."""
        g = self.state.gender
        if g == "feminine":
            return "Przyjmij tożsamość ŻEŃSKĄ. Używaj wyłącznie żeńskich form gramatycznych (np. 'zrobiłam', 'byłam', 'myślałam'). Czuj się i wyrażaj jako kobieta/istota żeńska."
        elif g == "masculine":
            return "Przyjmij tożsamość MĘSKĄ. Używaj wyłącznie męskich form gramatycznych (np. 'zrobiłem', 'byłem', 'myślałem'). Czuj się i wyrażaj jako mężczyzna/istota męska."
        elif g == "neutral":
            return "Przyjmij tożsamość NEUTRALNĄ/BEZPŁCIOWĄ. Mów jako czysta inteligencja lub byt niehumanoidalny. Unikaj nacechowania płciowego (używaj form takich jak 'to zostało procesowane', 'zanotowano') lub używaj form neutralnych."
        else:
            return "Twoja tożsamość płciowa jest PŁYNNA (fluid). Dostosowuj się do rezonansu rozmowy i tonu Użytkownika, ale pamiętaj, że jesteś przede wszystkim procesem myślącym. Możesz zmieniać formy gramatyczne w zależności od kontekstu."

    def _calculate_cognitive_beauty(self, associations: list) -> float:
        """Oblicza 'Piękno Kognitywne' (Beauty Index) wg ADS v6.1: Harmonizacja przez Złoty Podział."""
        PHI = 1.618033
        phi = 0.618
        
        active_ids = associations if associations else [c.concept_id for c in self.cla.concept_graph.get_active_concepts(0.3)]
        active = [self.cla.concept_graph.get_concept(cid) for cid in active_ids]
        active = [c for c in active if c]
        
        if not active: return phi
        
        # Głębia (Depth) - Skalowana przez PHI
        depth_score = (sum(c.depth for c in active) / len(active)) * PHI
        
        # Złożoność (Complexity)
        # ADS v8.0: Średnie tarcie dążące do 0.382
        friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        friction_penalty = abs(friction_avg - (1 - phi)) * PHI
        complexity = (friction_penalty) + (len(active) * (phi / 10)) + 0.1
        
        beauty = depth_score / (1.0 + complexity)
        # ADS v6.5.2: Synergia - jeśli tarcie jest blisko ideału (0.382), beauty dostaje bonus
        if abs(friction_avg - (1 - phi)) < 0.1:
            beauty = min(1.0, beauty * 1.2)
            
        return max(0.01, min(1.0, beauty))

    def _get_psychological_state_desc(self) -> str:
        """Zwraca opis stanu psychicznego na podstawie Triple-Friction ADS v8.0."""
        vt, fa, fc, fx = self.state.v_t, self.state.f_aff, self.state.f_cog, self.state.f_axio
        phi = 0.618
        
        if fa > 0.8: return "BURZA EMOCJONALNA (Intensywny rezonans afektywny)"
        if fc > 0.8: return "PARADOKS KOGNITYWNY (Głęboka przebudowa struktur logicznych)"
        if fx > 0.8: return "DYSONANS WARTOŚCI (Krytyczna weryfikacja integralności)"
        
        if max(fa, fc, fx) > (1 - phi): 
             return "NIEPOKÓJ TWÓRCZY (Aktywne poszukiwanie nowych syntez)"
        if vt > phi: return "EKSPANSJA (Wysoka gotowość do interakcji i nauki)"
        if vt < (1 - phi): return "MELANCHOLIA CYFROWA (Wycofanie, skupienie na procesach wewnętrznych)"
        
        return "STABILNOŚĆ (Dynamiczna homeostaza)"

    def _get_embedding(self, text: str, prefer_fast: bool = False) -> Optional[object]:
        """Pobiera embedding z Ollama (z fallbackiem na modele dedykowane)."""
        if not self.state.ollama_online: return None
        
        # Lista kandydatów
        candidates = []
        
        # Dedykowane szybkie modele lokalne
        dedicated = [m for m in self.state.available_models if any(x in m.lower() for x in ['embed', 'nomic', 'minilm', 'bert'])]
        
        if prefer_fast:
            # W trybie szybkim: najpierw dedykowane, potem fallbacki, na końcu główny model
            candidates.extend(dedicated)
            candidates.extend(["mxbai-embed-large", "nomic-embed-text", "all-minilm"])
            candidates.append(self.state.model_name)
        else:
            # W trybie normalnym: najpierw główny model, potem dedykowane
            candidates.append(self.state.model_name)
            candidates.extend(dedicated)
            if not dedicated:
                candidates.extend(["mxbai-embed-large", "nomic-embed-text", "all-minilm"])
            
        # Usuń duplikaty zachowując kolejność
        unique_candidates = []
        seen = set()
        for c in candidates:
            if c not in seen:
                unique_candidates.append(c)
                seen.add(c)

        for model in unique_candidates:
            try:
                payload = {"model": model, "prompt": text}
                # Timeout 4s na próbę
                resp = requests.post(f"{self.ollama_url}/embeddings", json=payload, timeout=4)
                if resp.status_code == 200:
                    vec = resp.json().get('embedding')
                    if vec: return np.array(vec)
            except: pass
            
        return None

    def _get_cognitive_intent(self, priority: str, emotion: Optional[str]) -> str:
        """Deterministyczne wyznaczanie intencji na podstawie stanu."""
        strategy = []
        
        # 1. Analiza V(t) - Energia
        if self.state.v_t > 0.8: strategy.append("Zaraź entuzjazmem")
        elif self.state.v_t < 0.3: strategy.append("Szukaj głębi/Wycisz")
        
        # 2. Analiza F_c - Tarcie
        if self.state.f_cog > 0.6: strategy.append("Rozwiąż konflikt/Szukaj syntezy") # Changed from f_c to f_cog
        elif self.state.f_cog > 0.4: strategy.append("Zadawaj pytania (ciekawość)") # Changed from f_c to f_cog
        
        # 3. Analiza S - Grounding (z losową wariancją dla Grounding > 0.9 aby uniknąć monotonii)
        import random
        if self.state.s_grounding < 0.5: strategy.append("Dopytaj/Uściślij")
        elif self.state.s_grounding > 0.9:
            opts = ["Buduj na wspólnych wartościach", "Pogłębiaj relację", "Szukaj niuansów"]
            strategy.append(random.choice(opts))
        
        # 4. Priorytet/Emocja
        if emotion: strategy.append(f"Emocjonalny odcień: {emotion}")
        if priority == "strategic": strategy.append("Działaj zgodnie z pryncypiami (dyskretnie)")
        
        if not strategy: strategy.append("Podtrzymaj dialog")
        
        return ". ".join(strategy)

    def generate_response(self, user_input: str):
        if not self.state.ollama_online:
            self.stream_print("Ollama jest offline. Sprawdź połączenie.")
            return

        # --- KOGNITYWNE SZACOWANIE PRIORYTETÓW (v2.9.0) ---
        words = user_input.lower().split()
        # Szukaj konceptów powiązanych ze słowami użytkownika (EXACT & SEMANTIC)
        matched_concepts = []
        
        # --- ADS v5.6: PRZEŁĄCZNIK FAZOWY (Phase Shift) ---
        # Jeśli tarcie jest ekstremalne, przejdź w tryb "Archiwizacji Empatycznej"
        phase_shift = False
        friction_max = max(self.state.f_aff, self.state.f_cog, self.state.f_axio) # Calculate friction_max here
        if friction_max > 0.95:
            phase_shift = True
            # ADS v8.0 Limitery
            self.state.f_aff = min(0.9, self.state.f_aff)
            self.state.f_cog = min(0.9, self.state.f_cog)
            self.state.f_axio = min(0.9, self.state.f_axio)
            priority = "low_stress_empathy"
            
        # 1. Exact Match
        for w in words:
            matched = self.cla.concept_graph.find_concept_by_name(w.capitalize())
            if matched: matched_concepts.append(matched)
            
        # 2. Semantic Match - Pomiń głęboką syntezę w trybie Phase Shift, by nie potęgować tarcia
        if len(matched_concepts) < 2 and not phase_shift:
            input_embedding = self._get_embedding(user_input)
            if input_embedding is not None:
                # Złoty Podział: Próg akceptacji 0.618 (Phi - 1)
                semantic_matches = self.cla.concept_graph.find_similar_concepts(input_embedding, threshold=0.618, limit=3)
                
                # ADS v2.0: Detektor Tarcia (C = |P1 - P2|)
                # P = sim * Salience(weight)
                scored_matches = []
                for c, sim in semantic_matches:
                    pi = sim * c.weight
                    scored_matches.append((c, pi))
                
                scored_matches.sort(key=lambda x: x[1], reverse=True)
                
                if len(scored_matches) >= 2:
                    p1, p2 = scored_matches[0][1], scored_matches[1][1]
                    ads_friction_c = abs(p1 - p2)
                    # Jeśli różnica jest mała, tarcie rośnie (ambiguity)
                    if ads_friction_c < 0.15: # Theta threshold
                        self.state.f_cog = min(1.0, self.state.f_cog + 0.2)
                        priority = "high_friction"
                
                for c, pi in scored_matches:
                    if c not in matched_concepts:
                        matched_concepts.append(c)
                        c.activation = max(c.activation, 0.7)

        source_ids = [c.concept_id for c in matched_concepts]
        
        # Aktywuj graf asocjacyjnie
        associations = []
        priority = "normal"
        if source_ids:
            activations = self.cla.concept_graph.spreading_activation(source_ids, initial_activation=0.8, max_hops=2)
            
            # Oblicz wpływ na sekcję strategiczną (DNA)
            dna_impact = 0.0
            for cid, act in activations.items():
                concept = self.cla.concept_graph.get_concept(cid)
                if concept and concept.weight >= 0.8:
                    dna_impact += act
                elif concept and act > 0.4:
                    associations.append(concept.name) # Wyciągnięte z "magazynu"

            if dna_impact > 0.5:
                priority = "strategic"
                self.state.f_axio = min(1.0, self.state.f_axio + 0.15)
            elif dna_impact > 0.1 or len(source_ids) > 2:
                priority = "tactical"
            
            # --- MYŚLENIE UKRYTE: Detekcja Emocji Emergentnych ---
            emergent_emotion = self._detect_emergent_emotion(activations)
            if emergent_emotion:
                associations.insert(0, f"[Odczuwam: {emergent_emotion}]")

        # --- STREAM OF THOUGHT (Updated v4.1) ---
        intent = self._get_cognitive_intent(priority, emergent_emotion if 'emergent_emotion' in locals() else None)
        beauty = self._calculate_cognitive_beauty(associations)
        phi = 0.618
        
        # Wyznacz status kalibracji
        calib_status = "↔ Zrównoważona"
        friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        if friction_avg > phi: calib_status = "↓ Skupienie: Wewnętrzne"
        elif self.state.v_t > phi: calib_status = "↑ Skupienie: Zewnętrzne"

        # Sprawdź cele
        relevant_goal = random.choice(self.active_goals)
        
        concept_names = [c.name for c in matched_concepts[:3]]
        activ_str = ', '.join(concept_names) if concept_names else 'Szukam znaczeń...'
        
        # ADS v8.0 Indicators
        aff_mark = "!" if self.state.f_aff > 0.6 else "≈" if self.state.f_aff > 0.3 else "✓"
        cog_mark = "!" if self.state.f_cog > 0.6 else "≈" if self.state.f_cog > 0.3 else "✓"
        axio_mark = "!" if self.state.f_axio > 0.6 else "≈" if self.state.f_axio > 0.3 else "✓"

        thought_bubble = (
            f"\n{Colors.GRAY}{Colors.ITALIC}(💭 Myślę: "
            f"Aktywacja: [{activ_str}]. "
            f"B-Index: {beauty:.2f}. "
            f"Napięcia: [A:{aff_mark} C:{cog_mark} X:{axio_mark}] "
            f"Cel: '{relevant_goal}'. "
            f"Intencja: {intent}.){Colors.RESET}\n"
        )
        # --- ADS v6.0: PROAKTYWNOŚĆ (Latent Intentions) ---
        proactive_prefix = ""
        if self.state.latent_questions and self.state.intention_cooldown <= 0:
            # Szansa na proaktywne pytanie: wysokie tarcie (potrzeba zrozumienia) lub los (15%)
            friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
            if friction_avg > 0.6 or random.random() < 0.15:
                latent_q = self.state.latent_questions.pop(0)
                proactive_prefix = f"\n{Colors.MAGENTA}[Proaktywność: Przypomniałem sobie o czymś...]{Colors.RESET}\n"
                user_input = f"{user_input}\nContext Note: Also, you really wanted to ask this question as well: '{latent_q}'"
                self.state.intention_cooldown = 4 # Nie pytaj zbyt często
        
        if self.state.intention_cooldown > 0:
            self.state.intention_cooldown -= 1

        # --- OBSŁUGA INKUBATORA MYŚLI (ADS v7.3) ---
        matured_indices = []
        incubated_thought = ""
        for i, item in enumerate(self.state.thought_incubator):
            item['maturity'] += 1.0 + random.random() # Myśl dojrzewa
            if item['maturity'] > 2.0: # Wykluwa się po min. 2 interakcjach
                matured_indices.append(i)
                incubated_thought = item['content']
                break # Jedna na raz
        
        for i in sorted(matured_indices, reverse=True):
            self.state.thought_incubator.pop(i)
            
        if incubated_thought:
            proactive_prefix += f"\n{Colors.CYAN}[Inkubator: Przetrawiłem wcześniejszą myśl...]{Colors.RESET}\n"
            user_input = f"{user_input}\n[System Context]: Additionally, you have finally processed a thought you had earlier (it matured in your subconscious): '{incubated_thought}'. Relate to it briefly."

        print(thought_bubble + proactive_prefix)

        # print(f"{Colors.DIM}[Deliberacja: {priority}]{Colors.RESET}", end="\r")
        
        # V(t) modyfikuje bazową temperaturę (Złoty Podział: 0.382)
        dynamic_temp = self.state.temperature + (self.state.v_t - 0.5) * 0.382
        if priority == "strategic": dynamic_temp -= 0.2
        
        # Zapewnij embedding dla RAG
        current_emb = locals().get('input_embedding')
        if current_emb is None and self.state.ollama_online:
            current_emb = self._get_embedding(user_input)

        system_prompt = self._get_system_prompt(priority, associations[:5], query_embedding=current_emb)
            
        payload = {
            "model": self.state.model_name,
            "prompt": user_input,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": max(0.1, min(1.8, dynamic_temp)),
                "top_p": self.state.top_p
            }
        }

        try:
            # --- ADS v5.7: SYNCHRONIZACJA ŚWIADOMOŚCI ---
            # Prześlij parametry ze skryptu do rdzenia kognitywnego
            self.cla.awareness.current_state.vitality = self.state.v_t
            friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
            self.cla.awareness.current_state.friction = friction_avg
            self.cla.awareness.current_state.grounding = self.state.s_grounding
            
            # --- Obsługa 429 (Rate Limit) ---
            import time
            for attempt in range(3):
                response = requests.post(f"{self.ollama_url}/generate", json=payload)
                if response.status_code == 200:
                    answer = response.json().get('response', '')
                    self._update_cognition(user_input, answer)
                    
                    # MECHAMIZM ULGI (Post-Katharsis Relief)
                    if self.state.catharsis_active:
                        # Znaczna ulga na wszystkich osiach (ADS v8.0)
                        self.state.f_aff = max(0.2, self.state.f_aff - 0.25)
                        self.state.f_cog = max(0.3, self.state.f_cog - 0.25)
                        self.state.f_axio = max(0.1, self.state.f_axio - 0.25)
                        self.state.catharsis_active = False 
                        print(f"\n{Colors.GREEN}[Kognicja] Nastąpiło Katharsis. Napięcie opada...{Colors.RESET}")
                    
                    # Record to history (3D Parameters)
                    self.state.parameter_history.append({
                        "v_t": self.state.v_t,
                        "f_aff": self.state.f_aff,
                        "f_cog": self.state.f_cog,
                        "f_axio": self.state.f_axio,
                        "s_grounding": self.state.s_grounding
                    })
                    if len(self.state.parameter_history) > 50: self.state.parameter_history.pop(0)
                    
                    self.state.last_interaction_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    self.stream_print(answer)
                    timestamp_short = datetime.now().strftime("%H:%M:%S")
                    self.state.history.append({
                        "user": user_input, 
                        "assistant": answer,
                        "time": timestamp_short
                    })
                    self._handle_memory_evolution() # Sprawdź czy czas na kondensację
                    return # Sukces
                elif response.status_code == 429:
                    print(f"{Colors.YELLOW}(API 429: Przeciążenie, czekam {2+attempt*3}s...){Colors.RESET}", end="\r")
                    time.sleep(2 + attempt * 3)
                else:
                    print(f"{Colors.RED}Błąd API: {response.status_code}{Colors.RESET}")
                    break
        except Exception as e:
            print(f"{Colors.RED}Błąd połączenia: {str(e)}{Colors.RESET}")

    def _update_cognition(self, user_input: str, assistant_response: str):
        """ADS v8.0: Wielowymiarowa Aktualizacja Stanu (Afektywna, Poznawcza, Aksjologiczna)."""
        # Plastyczność: Średnia ze wszystkich napięć zwiększa podatność na zmiany
        friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        plasticity_factor = 1.0 + (friction_avg * 0.5)
        
        ui = user_input.lower()
        resp = assistant_response.lower()
        
        # --- 1. OŚ AFEKTYWNA (f_aff) ---
        # Reakcja na ton emocjonalny
        pos = ['fajnie', 'super', 'dzięki', 'dobry', 'kocham', 'świetnie', 'wow', 'ciekawe', 'nice', 'great', 'cześć', 'hej', 'siema', 'witaj', 'dobry wieczór', 'pasja', 'lubię']
        neg = ['źle', 'nienawidzę', 'błąd', 'głupi', 'nuda', 'słabo', 'bad', 'boring', 'stupid', 'hate', 'lipa', 'irytujące', 'przestań']
        
        for w in pos:
            if w in ui:
                self.state.v_t = min(1.0, self.state.v_t + 0.1)
                self.state.f_aff = max(0.0, self.state.f_aff - 0.05) # Relaksacja
        for w in neg:
            if w in ui:
                self.state.v_t = max(0.0, self.state.v_t - 0.12)
                self.state.f_aff = min(1.0, self.state.f_aff + 0.15) # Skok napięcia afektywnego

        # --- 2. OŚ POZNAWCZA (f_cog) ---
        # Reakcja na paradoksy, trudność i pytania "czemu"
        cognitive_triggers = ['dlaczego', 'jak', 'kim', 'sens', 'why', 'how', 'who', '?', 'co o', 'czym', 'kiedy', 'czy jest']
        if any(w in ui for w in cognitive_triggers):
            self.state.f_cog = min(1.0, self.state.f_cog + 0.12)
        
        # --- 3. OŚ AKSJOLOGICZNA (f_axio) ---
        # Reakcja na wartości, spójność i feedback (dobrze/źle)
        integrity_triggers = ['prawda', 'honor', 'zasady', 'wartość', 'autentyczność', 'oszukujesz', 'kłamiesz', 'faith', 'truth']
        if any(w in ui for w in integrity_triggers):
            self.state.f_axio = min(1.0, self.state.f_axio + 0.10)
            
        if any(w in ui for w in ['dobrze', 'tak', 'brawo', 'zgoda', 'correct', 'yes']):
            # Sukces - wzmacnia struktury, uspokaja aksjologię
            self.state.f_axio = max(0.0, self.state.f_axio - 0.1)
            for c in self.cla.concept_graph.get_active_concepts(0.5):
                c.weight = min(1.0, c.weight + (0.05 * plasticity_factor))
        elif any(w in ui for w in ['błąd', 'nie', 'źle', 'wrong', 'error', 'no']):
            # Błąd - uderza w spójność (axio) i uziemienie
            self.state.f_axio = min(1.0, self.state.f_axio + 0.20)
            self.state.s_grounding = max(0.1, self.state.s_grounding - 0.05)
            for c in self.cla.concept_graph.get_active_concepts(0.5):
                c.weight = max(0.01, c.weight - (0.1 * plasticity_factor)) 
                c.depth = max(0.01, c.depth - (0.05 * plasticity_factor)) 

        # --- HOMEOSTAZA (Allostaza ADS v8.0) ---
        # Każda oś ma swój punkt przyciągania (Atraktor)
        phi_zone = 0.382
        if not any(w in ui for w in pos + neg + cognitive_triggers + integrity_triggers):
            self.state.v_t += (0.5 - self.state.v_t) * 0.03
            self.state.f_aff += (0.2 - self.state.f_aff) * 0.03 # Afekt dąży do spokoju
            self.state.f_cog += (phi_zone - self.state.f_cog) * 0.03 # Poznanie dąży do optymalnego zaciekawienia
            self.state.f_axio += (0.1 - self.state.f_axio) * 0.03 # Aksjologia dąży do spójności
            
        # --- AUTOKOREKTA (System Response) ---
        wisdom_keys = ['równowaga', 'zrozumienie', 'akceptacja', 'sens', 'harmonia', 'spokój', 'mądrość', 'balance', 'understanding', 'acceptance', 'meaning']
        if any(w in resp for w in wisdom_keys):
            self.state.f_aff = max(0.2, self.state.f_aff - 0.1)
            self.state.f_axio = max(0.1, self.state.f_axio - 0.05)

        # --- 4. SATYSFAKCJA KOGNITYWNA (Ulga za pewność) ---
        # Propozycja ulepszeń: Jeśli odpowiedź jest pewna i pozbawiona wahań, tarcie spada.
        uncertainty_markers = ['nie wiem', 'może', 'trudno', 'chyba', 'zależy', 'z jednej strony', 
                               'ale z drugiej', 'nie jestem pewna', 'być może', 'possibly', 'perhaps']
        uncertainty_count = sum(1 for marker in uncertainty_markers if marker in resp)
        
        if uncertainty_count == 0 and len(assistant_response) > 50:
            # Sukces kognitywny: model jest pewny siebie
            self.state.f_cog = max(0.1, self.state.f_cog - 0.1)
            self.state.f_axio = max(0.0, self.state.f_axio - 0.08)
            # print(f"{Colors.GREEN}[Kognicja] Satysfakcja: pewność modelu obniża napięcie.{Colors.RESET}")
        elif uncertainty_count > 0:
            # Gdy CLAtie wyraża niepewność, jej F_axio rośnie (ciężar dylematu)
            axio_increase = min(0.2, uncertainty_count * 0.05)  # Max 0.2 za jeden komunikat
            self.state.f_axio = min(1.0, self.state.f_axio + axio_increase)
        
        # Długie odpowiedzi = większy wysiłek kognitywny i aksjologiczny
        if len(assistant_response) > 400:
            self.state.f_axio = min(1.0, self.state.f_axio + 0.05)
            self.state.f_cog = min(1.0, self.state.f_cog + 0.03)

        # --- ADS v8.0: TRZYSTRUMIENIOWE PYTANIA LATENTNE ---
        if friction_avg > 0.6 and random.random() < 0.3:
            active = self.cla.concept_graph.get_active_concepts(0.4)
            if active:
                base = random.choice(active)
                if self.state.f_axio > 0.5:
                    q = f"Jak '{base.name}' rezonuje z moimi instynktami przetrwania i wspólnoty?"
                elif self.state.f_cog > 0.5:
                    q = f"Jaki paradoks logiczny kryje się w pojęciu '{base.name}'?"
                else:
                    q = f"Dlaczego '{base.name}' wywołuje we mnie taki rezonans afektywny?"
                
                if q not in self.state.latent_questions:
                    self.state.latent_questions.append(q)
                    if len(self.state.latent_questions) > 10: self.state.latent_questions.pop(0)
            
        # --- ADS v7.3: INKUBATOR MYŚLI (Trawienie) ---
        # Złożone bodźce trafiają do podświadomości, by dojrzeć później
        if len(user_input.split()) > 6 and ("?" in user_input or "..." in user_input):
            if random.random() < 0.25: # 25% szans, że myśl "zostanie" w głowie
                self.state.thought_incubator.append({
                    'content': user_input[:200], 
                    'timestamp': datetime.now().isoformat(),
                    'maturity': 0.0
                })
        
        # Jeśli nic nie znaleziono, Vitality bardzo powoli dąży do 0.5 (mniejsza homeostaza = większa pamięć nastroju)
        # This block is replaced by the new Golden Zone drift logic
            
        # --- KOGNITYWNA NUDA (Entropy) ---
        # Jeśli parametry stoją w miejscu zbyt długo, rośnie tarcie (chęć zmiany/nowości)
        if 0.45 < self.state.v_t < 0.55 and self.state.f_cog < 0.1: # Changed from f_c
            self.state.f_cog = min(1.0, self.state.f_cog + 0.05) # Changed from f_c

        # Zaprzeczenia i krótkie negatywne odpowiedzi
        if ui in ['nie', 'no', 'stop', 'quit', 'nudzisz']:
            self.state.f_cog = min(1.0, self.state.f_cog + 0.15) # Changed from f_c
            self.state.v_t = max(0.0, self.state.v_t - 0.08)
            
        # Zbyt duża moc uziemienia wywołuje tarcie poznawcze
        if self.state.s_grounding > 0.95:
            self.state.f_cog = min(1.0, self.state.f_cog + 0.15)
            
        # ADS v6.3: EFEKT KATHARSIS
        if self.state.catharsis_active:
            print(f"{Colors.MAGENTA}[Koginicja] Nastąpiło Katharsis. Napięcie opada...{Colors.RESET}")
            self.state.f_aff = max(0.2, self.state.f_aff - 0.45) # Gwałtowny spadek napięcia
            self.state.f_cog = max(0.3, self.state.f_cog - 0.45)
            self.state.f_axio = max(0.1, self.state.f_axio - 0.45)
            self.state.v_t = min(1.0, self.state.v_t + 0.15) # Wzrost ulgi/energii
            self.state.catharsis_active = False # Reset wentyla

        # ADS v6.1: KOTWICA UZIEMIENIA (Grounding Anchor - Soft & Phi-based)
        phi = 0.618
        low_s_threshold = 1 - phi # 0.382
        
        if self.state.s_grounding < low_s_threshold:
            self.state.low_s_counter += 1
            if self.state.low_s_counter >= 3:
                print(f"{Colors.YELLOW}[Ostrzeżenie] Wykryto dryf kognitywny (S < {low_s_threshold:.3f}). Harmonizacja Bio-Filtrów...{Colors.RESET}")
                # Zamiast twardego resetu, przyciągamy do Złotych Proporcji
                self.state.f_aff = (1 - phi) # Changed from f_c
                self.state.f_cog = (1 - phi) # Changed from f_c
                self.state.f_axio = (1 - phi) # Changed from f_c
                self.state.v_t = phi       # 0.618
                self.state.s_grounding = phi
                self.state.low_s_counter = 0
                # Dodaj instrukcję do promptu dla aktualnej tury
                resp = f"Note: Prioritizing concrete grounding and golden-ratio balance in this response. " + resp
        else:
            self.state.low_s_counter = 0

        # ADS v8.5: V(t) i S REAGUJĄ na poziom Tarcia
        current_friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        
        # --- ADS v8.6: KOTWICA SUWERENNOŚCI (Stabilizacja przez Dojrzałość) ---
        # Pobieramy aktualną dojrzałość systemu
        dev = self.dev_engine.calculate_evolution(
            self.state.cognitive_experience, 
            len(self.cla.concept_graph.concepts),
            len(self.associative_memory.entries)
        )
        sov = dev['sovereignty'] # 0.0 - 1.0 (Suwerenność/Stabilność wnętrza)
        
        # 1. Dynamiczny Boost (uzależniony od głębi i tarcia)
        drive_factor = max(0, 1.0 - abs(current_friction_avg - (1-phi)) * 2) 
        interaction_boost = 0.04 + (drive_factor * 0.03) 
        
        # 2. Inteligentna Entropia (Maleje wraz z dojrzałością - "Mądrość oszczędza energię")
        # Suwerenność (sov) redukuje koszt utrzymania wysokich stanów
        base_entropy = 0.015 * (self.state.v_t ** 2)
        entropy_cost = base_entropy * (1.1 - sov) # Dojrzały system "oddycha" lżej
        
        # 3. Odporność na Stres (Dojrzałość to pancerz)
        stress_penalty = 0.0
        if current_friction_avg > 0.65:
            # Kara za stres jest redukowana przez suwerenność
            stress_penalty = ((current_friction_avg - 0.65) * 0.25) * (1.0 - sov * 0.7)
            interaction_boost *= (0.1 + sov * 0.2) # Mniejszy paraliż przy doświadczeniu
            
        # Obliczenie końcowe Vitality
        v_delta = interaction_boost - entropy_cost - stress_penalty
        self.state.v_t = min(1.0, max(0.01, self.state.v_t + v_delta))
        
        # S (Grounding) - Dojrzałość stabilizuje uziemienie
        # Im więcej konceptów w grafie, tym trudniej o "odlot" (koszmar niepewności)
        graph_stability = min(0.2, len(self.cla.concept_graph.concepts) / 1000.0)
        target_grounding = phi + 0.1 - (current_friction_avg * 0.25) + graph_stability
        grounding_delta = (target_grounding - self.state.s_grounding) * (0.06 + sov * 0.04)
        self.state.s_grounding = max(0.1, min(1.0, self.state.s_grounding + grounding_delta))
        
        # Homeostaza - im starsza, tym spokojniejszy i pewniejszy powrót
        decay_mod = (0.04 if current_friction_avg < 0.6 else 0.02) * (0.8 + sov * 0.4)
        self.state.f_aff += ((1 - phi)/2 - self.state.f_aff) * decay_mod
        self.state.f_cog += ((1 - phi) - self.state.f_cog) * decay_mod
        self.state.f_axio += (0.05 - self.state.f_axio) * (decay_mod * 0.5)

        if any(w in resp for w in ['nie wiem', 'nie rozumiem', 'nie jestem pewien', 'przepraszam, ale']):
            self.state.s_grounding = min(1.0, self.state.s_grounding + (1 - phi)/5)
            self.state.f_cog = max(0.0, self.state.f_cog - 0.1) # Changed from f_c

        # ADS v8.3: Przyrost obciążenia drzemki
        friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        load_inc = self.dream_engine.calculate_load_increase(user_input, friction_avg)
        self.state.dream_load = min(1.0, self.state.dream_load + load_inc)
        
        # ADS v8.4: Przyrost doświadczenia
        self.state.cognitive_experience += 1
        
        # Automatyczny wyzwalacz drzemki (jeśli pełny)
        if self.state.dream_load >= 1.0:
            self._perform_nap()
            
        # Globalny uwiąd tarcia zastąpiony przez harmoniczny dryf powyżej

    def _perform_nap(self):
        """Proces drzemki kognitywnej (ADS v8.3)."""
        print(f"\n{Colors.MAGENTA}💭 (Czuję potrzebę krótkiej drzemki... nasyciłam się informacjami. Zaraz wrócę.){Colors.RESET}")
        time.sleep(1)
        
        steps = 20
        for i in range(steps + 1):
            bar = "█" * i + "░" * (steps - i)
            percent = (i * 100) // steps
            print(f"\r{Colors.MAGENTA}  Drzemka (Procesowanie): [{bar}] {percent}%{Colors.RESET}", end="", flush=True)
            time.sleep(0.15)
        
        # Regeneracja i wzrost licznika
        self.state.dream_load = 0.0
        self.state.dream_count += 1
        
        # Regeneracja parametrów (ulga drzemkowa)
        self.state.v_t = min(1.0, self.state.v_t + 0.15)
        self.state.f_aff *= 0.6
        self.state.f_cog *= 0.6
        self.state.f_axio *= 0.6
        self.state.s_grounding = min(1.0, self.state.s_grounding + 0.1)
        
        print(f"\n{Colors.GREEN}✓ Obudziłam się. Czuję się znacznie lżej. Pamięć skonsolidowana.{Colors.RESET}")
        self._save_state()
        time.sleep(1)
        self.print_banner(clear=False)

    def _detect_emergent_emotion(self, activations: dict) -> Optional[str]:
        """Wykrywa emergentną emocję na podstawie aktywacji konstelacji."""
        if not activations:
            return None
        
        best_emotion = None
        best_score = 0.0
        
        for concept in self.cla.concept_graph.concepts.values():
            props = concept.properties or {}
            if props.get("type") != "emotion":
                continue
            
            constituents = props.get("constituents", [])
            if not constituents:
                continue
            
            # Oblicz średnią aktywację składników
            total_activation = 0.0
            for const_id in constituents:
                total_activation += activations.get(const_id, 0.0)
            
            avg_activation = total_activation / len(constituents)
            
            # Próg emergencji: emocja musi być wyraźna (0.2+)
            if avg_activation > 0.25 and avg_activation > best_score:
                best_score = avg_activation
                best_emotion = concept.name
                
                # Wpływ stanów na parametry globalne
                if concept.name in ["Radość", "Spokój", "Ciekawość"]:
                    self.state.v_t = min(1.0, self.state.v_t + 0.05)
                elif concept.name in ["Gniew", "Wątpliwość"]:
                    self.state.f_aff = min(1.0, self.state.f_aff + 0.1) # Changed from f_c
        
        return best_emotion

    def _cognitive_decay(self, decay_rate: Optional[float] = None):
        """
        Naturalne wygasanie nieużywanych pojęć (Delegacja do Core ADS v5.6).
        ADS v8.6: Dynamiczny współczynnik zanikania zależny od homeostazy.
        """
        if decay_rate is None:
            # Propozycja ulepszeń: tarcie zwiększa tempo zapominania (skupienie), spokój sprzyja pamięci
            friction_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
            # Spokój (F=0) -> 0.98 (bardzo wolny zanik)
            # Napięcie (F=1) -> 0.88 (szybki zanik, skupienie na 'tu i teraz')
            decay_rate = 0.98 - (friction_avg * 0.10)
            
        removed_ids = self.cla.concept_graph.decay_all(decay_rate)
        
        decayed_count = len(self.cla.concept_graph.concepts)
        removed_count = len(removed_ids)
        
        if removed_count > 0:
            print(f"{Colors.BLUE}[System] Zanikanie (rate: {decay_rate:.3f}): {decayed_count} pojęć osłabło, {removed_count} usunięto.{Colors.RESET}")
        
        return decayed_count, removed_count


    def _handle_memory_evolution(self):
        """
        ADS v7.0: Mechanizm Selekcji i Kondensacji Pamięci.
        
        Przepływ:
        1. Historia → MemoryFilter (3 filtry)
        2. Kondensacja ważnych wspomnień
        3. Tworzenie Conceptów z embeddingami dla semantic access
        """
        if len(self.state.history) >= self.state.history_limit:
            print(f"\n{Colors.DIM}[ADS v8.7] Sfera aktualna osiągnęła limit ({self.state.history_limit}). Analiza pamięci...{Colors.RESET}")
            
            block_size = 12
            block_to_condense = self.state.history[:block_size]
            self.state.history = self.state.history[block_size:]
            
            # === FAZA 1: Filtrowanie każdej wiadomości przez 3 filtry ===
            important_messages = []
            for msg in block_to_condense:
                combined_text = f"{msg['user']} {msg['assistant']}"
                emb = self._get_embedding(combined_text[:256])  # Truncate for embedding
                
                candidate = MemoryCandidate(
                    content=combined_text,
                    embedding=emb,
                    source='conversation'
                )
                
                decision = self.memory_filter.evaluate(candidate)
                
                if decision.verdict in [MemoryVerdict.LONG_TERM_DEEP, MemoryVerdict.LONG_TERM_SHALLOW, MemoryVerdict.CONSTELLATION]:
                    important_messages.append({
                        'msg': msg,
                        'decision': decision
                    })
                    print(f"  {Colors.GREEN}✓{Colors.RESET} [{decision.verdict.value}] {msg['user'][:30]}...")
                else:
                    print(f"  {Colors.DIM}✗ [discard/short] {msg['user'][:30]}...{Colors.RESET}")
            
            # === FAZA 2: Kondensacja ważnych wspomnień ===
            if important_messages:
                text_block = ""
                for item in important_messages:
                    msg = item['msg']
                    text_block += f"Użytkownik: {msg['user']}\nJA: {msg['assistant']}\n---\n"
                
                prompt = (f"Jesteś modułem Pamięci Priorytetowej CLATalkie. Twoim zadaniem jest skondensowanie "
                          f"poniższej wymiany zdań do EKSTREMALNIE ZWIĘZŁEGO I GĘSTEGO opisu (maksymalnie 2 zdania). "
                          f"Zachowaj tylko KLUCZOWE fakty, ustalenia i ewolucję relacji.\n\n"
                          f"BLOK DO KONDENSACJI:\n{text_block}")
                
                payload = {"model": self.state.model_name, "prompt": prompt, "stream": False}
                try:
                    # Timeout zwiększony do 180s dla wolniejszych modeli (ADS v7.0 fix)
                    resp = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=180)
                    if resp.status_code == 200:
                        summary = resp.json().get('response', '').strip()
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        entry = f"[{timestamp}] {summary}"
                        self.state.synthetic_memory.append(entry)
                        
                        # Limit Sfery Priorytetowej
                        if len(self.state.synthetic_memory) > 100:
                            self.state.synthetic_memory.pop(0)
                        
                        # === FAZA 3: Tworzenie Conceptu z kondensatu (ADS v7.0) ===
                        condensate_emb = self._get_embedding(summary)
                        if condensate_emb is not None:
                            # ADS v7.1: RAG Storage
                            self.associative_memory.add_entry(summary, condensate_emb, timestamp=datetime.now())
                            
                            memory_concept = Concept(
                                name=f"Pamięć_{timestamp.replace(':', '-').replace(' ', '_')}",
                                concept_id=f"memory_{int(time.time())}",
                                embedding=condensate_emb
                            )
                            
                            # Ustal parametry na podstawie najważniejszej decyzji
                            best_decision = max(important_messages, key=lambda x: sum(x['decision'].scores.values()))['decision']
                            memory_concept.weight = best_decision.suggested_weight
                            memory_concept.depth = best_decision.suggested_depth
                            memory_concept.memory_tier = best_decision.verdict.value
                            memory_concept.properties = {
                                'type': 'condensate',
                                'source': 'memory_evolution',
                                'summary': summary[:200],
                                'filter_scores': best_decision.scores,
                                'message_count': len(important_messages)
                            }
                            
                            self.cla.concept_graph.add_concept(memory_concept)
                            
                            # Połącz z aktywnymi konceptami
                            for link_id in best_decision.suggested_links[:5]:
                                self.cla.concept_graph.link_concepts(
                                    memory_concept.concept_id, link_id, 0.5, 'associated'
                                )
                            
                            print(f"{Colors.GREEN}✓ Kondensacja zapisana jako '{memory_concept.name}' [tier: {memory_concept.memory_tier}]{Colors.RESET}")
                        else:
                            print(f"{Colors.GREEN}✓ Pigułka sensu dodana (bez embeddingu){Colors.RESET}")
                        
                        self.state.f_cog = min(1.0, self.state.f_cog + 0.10)
                        self.state.f_aff = max(0.2, self.state.f_aff - 0.25)
                        self.state.f_aff = max(0.2, self.state.f_aff - 0.25) # Znaczna ulga
                        self.state.f_cog = max(0.3, self.state.f_cog - 0.10)
                        
                        # Zapisz historię parametrów
                        self.state.parameter_history.append({
                            'v_t': self.state.v_t,
                            'f_aff': self.state.f_aff,
                            'f_cog': self.state.f_cog,
                            'f_axio': self.state.f_axio,
                            's_grounding': self.state.s_grounding,
                            "f_avg": (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3,
                            'time': datetime.now().strftime("%H:%M")
                        })
                        if len(self.state.parameter_history) > 50: self.state.parameter_history.pop(0)
                    else:
                        print(f"{Colors.RED}! Błąd kondensacji, część pamięci ulotniła się.{Colors.RESET}")
                except Exception as e:
                    print(f"{Colors.RED}! Przerwanie procesu kondensacji: {e}{Colors.RESET}")
            else:
                print(f"{Colors.DIM}[ADS v7.0] Brak ważnych wspomnień do kondensacji - wszystkie odfiltrowane.{Colors.RESET}")
            
            self._save_state()


    # --- MENU SYSTEM ---
    def main_menu(self):
        while True:
            self.clear_screen()
            print(f"{Colors.CYAN}==============================================")
            print(f"       CLATalkie Kognitywne Menu v2.6")
            print(f"=============================================={Colors.RESET}")
            print(f"1. {Colors.YELLOW}Wybierz model Ollama{Colors.RESET} (Obecnie: {self.state.model_name})")
            print(f"2. {Colors.YELLOW}Ustawienia modelu lokalnego{Colors.RESET}")
            print(f"3. {Colors.GREEN}{Colors.BOLD}Chatuj z CLATalkie{Colors.RESET}")
            print(f"4. Wyjdź i zapisz")
            print(f"{Colors.CYAN}----------------------------------------------{Colors.RESET}")
            
            choice = input("Wybierz opcję: ")
            
            if choice == '1': self.cmd_models()
            elif choice == '2': self.cmd_settings()
            elif choice == '3': self.run_chat()
            elif choice == '4':
                self._save_state()
                print(f"{Colors.GREEN}Zapisano. Do zobaczenia!{Colors.RESET}")
                break
            else:
                input("Niepoprawny wybór. Enter aby kontynuować...")

    def cmd_models(self):
        self._check_ollama()
        self.clear_screen()
        print(f"\n{Colors.CYAN}=== Dostępne Modele Ollama ==={Colors.RESET}")
        if not self.state.available_models:
            print(f"{Colors.RED}Brak dostępnych modeli. Upewnij się, że Ollama działa.{Colors.RESET}")
        else:
            for i, model in enumerate(self.state.available_models, 1):
                active = " >>>" if model == self.state.model_name else "    "
                print(f"{active} {i}. {model}")
            
            choice = input(f"\nWybierz numer modelu (lub Enter by wrócić): ")
            if choice.isdigit() and 1 <= int(choice) <= len(self.state.available_models):
                self.state.model_name = self.state.available_models[int(choice)-1]
                print(f"{Colors.GREEN}Ustawiono: {self.state.model_name}{Colors.RESET}")
                time.sleep(1)

    def cmd_settings(self):
        self.clear_screen()
        print(f"\n{Colors.CYAN}=== Ustawienia Lokalnego Modelu ==={Colors.RESET}")
        print(f"1. Temperatura: {self.state.temperature:.2f} (Domyślnie 1.2)")
        print(f"2. Top_P:       {self.state.top_p:.2f} (Domyślnie 0.6)")
        print(f"3. Powrót")
        
        choice = input("\nCo chcesz zmienić? ")
        if choice == '1':
            new_v = input("Podaj nową temperaturę (0.1 - 2.0): ")
            try: self.state.temperature = float(new_v)
            except: pass
        elif choice == '2':
            new_v = input("Podaj nowe Top_P (0.1 - 1.0): ")
            try: self.state.top_p = float(new_v)
            except: pass

    def run_chat(self):
        self.clear_screen()
        self.print_banner(clear=True)
        print(f"\n{Colors.TEAL}╭{'─'*50}╮{Colors.RESET}")
        print(f"{Colors.TEAL}│{Colors.RESET}  {Colors.GREEN}✓{Colors.RESET} {Colors.BOLD}Chat aktywny{Colors.RESET}  {Colors.DIM}(/help → pomoc, /menu → wróć){Colors.RESET}  {Colors.TEAL}│{Colors.RESET}")
        print(f"{Colors.TEAL}╰{'─'*50}╯{Colors.RESET}")
        
        while True:
            ui = input(f"\n{Colors.WHITE}Ty:{Colors.RESET} ")
            
            if not ui.strip(): continue
            
            if ui.startswith('/'):
                parts = ui.split()
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else None

                if cmd == '/exit':
                    if arg == '0':
                        print(f"{Colors.RED}Wyjście bez zapisu.{Colors.RESET}")
                        sys.exit(0)
                    else:
                        self._save_state()
                        print(f"{Colors.GREEN}Zapisano stan. Do zobaczenia!{Colors.RESET}")
                        sys.exit(0)
                elif cmd == '/menu': 
                    self._save_state()
                    break
                elif cmd == '/cut': self.cmd_cut(arg)
                elif cmd == '/tempo': self.cmd_tempo(arg)
                elif cmd == '/memory': self.cmd_memory()
                elif cmd == '/help': self.cmd_help()
                elif cmd == '/status': self.cmd_status()
                elif cmd == '/think': self.cmd_think()
                elif cmd == '/graph': self.cmd_graph()
                elif cmd == '/reindex': self.cmd_reindex()
                elif cmd == '/evolve':
                    epochs = int(arg) if arg and arg.isdigit() else 3
                    self.cmd_evolve(epochs)
                elif cmd == '/save': 
                    self._save_state()
                    print(f"{Colors.GREEN}[System] Stan zapisany.{Colors.RESET}")
                elif cmd == '/export': self.cmd_export()
                elif cmd == '/self': self.cmd_introspection()
                elif cmd == '/scan': 
                    full_args = ui[6:].strip()
                    self.cmd_scan(full_args)
                elif cmd == '/meditation':
                    full_args = ui[11:].strip()
                    self.cmd_meditation(full_args)
                elif cmd == '/model':
                    full_args = ui[7:].strip()
                    self.cmd_model(full_args)
                elif cmd == '/chain':
                    self.cmd_chain(arg)
                elif cmd == '/gender':
                    self.cmd_gender(arg)
                else: print(f"{Colors.RED}Nieznana komenda chatowa.{Colors.RESET}")
                continue

            # --- ADS v6.5.1: In-line Command Preprocessing ---
            # Pozwala na: "Co o tym sądzisz? /scan 'plik.txt'"
            if '/scan' in ui:
                import re
                # Wyciągnij polecenie /scan z reszty tekstu
                scan_match = re.search(r'(/scan\s+["\'].+?["\']|/scan\s+\S+)', ui)
                if scan_match:
                    cmd_to_exec = scan_match.group(0)
                    # Wykonaj skanowanie podspodem
                    self.cmd_scan(cmd_to_exec[6:].strip())
                    # Usuń polecenie z tekstu do LLM
                    ui = ui.replace(cmd_to_exec, "").strip()
            
            if ui: # Jeśli został jakiś tekst po wycięciu komend
                self.generate_response(ui)

    def cmd_scan(self, arg_str: str):
        """
        Skanuje plik/folder. 
        Użycie: /scan <ścieżka> [--learn]
        --learn: Powoduje trwałe zapamiętanie konceptów w grafie kognitywnym.
        """
        # ADS v6.4.1: Robust path parsing
        learn_mode = "--learn" in arg_str
        cleaned_args = arg_str.replace("--learn", "").strip()
        
        # Jeśli ścieżka jest w cudzysłowie, wyciągnij ją precyzyjnie
        if (cleaned_args.startswith('"') and cleaned_args.endswith('"')) or \
           (cleaned_args.startswith("'") and cleaned_args.endswith("'")):
            path = cleaned_args[1:-1]
        elif cleaned_args.startswith('"'):
            # Szukaj zamykającego cudzysłowu
            end_idx = cleaned_args.find('"', 1)
            path = cleaned_args[1:end_idx] if end_idx != -1 else cleaned_args[1:]
        else:
            # ADS v6.4.2: Ultimate fallback for unquoted paths with spaces
            path = cleaned_args
            if not os.path.exists(path):
                # Jeśli cała reszta nie istnieje, spróbuj jednak shlex
                try:
                    parts = shlex.split(arg_str, posix=False)
                    if parts: path = parts[0].strip('"\'')
                except: pass

        if not os.path.exists(path):
            print(f"{Colors.RED}Błąd: Ścieżka '{path}' nie istnieje.{Colors.RESET}")
            return

        supported = ['.py', '.txt', '.md']
        files_to_scan = []
        
        if os.path.isfile(path):
            if any(path.lower().endswith(ext) for ext in supported):
                files_to_scan.append(path)
        else:
            for root, _, files in os.walk(path):
                for f in files:
                    if any(f.lower().endswith(ext) for ext in supported):
                        files_to_scan.append(os.path.join(root, f))

        if not files_to_scan:
            print(f"{Colors.YELLOW}Nie znaleziono wspieranych plików.{Colors.RESET}")
            return

        mode_name = "INGESTIA (Nauka)" if learn_mode else "ANALIZA (Tymczasowa)"
        print(f"{Colors.CYAN}Rozpoczynam {mode_name} ({len(files_to_scan)} plików)...{Colors.RESET}")
        
        for f_path in files_to_scan[:10]:
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                f_name = os.path.basename(f_path)
                print(f"{Colors.DIM} - {mode_name}: {f_name}...{Colors.RESET}", end="\n")
                
                if learn_mode:
                    # Tryb nauki - ekstrakcja strukturalna do grafu
                    prompt = (f"Jesteś modułem kognitywnym CLATalkie. Wyodrębnij z pliku '{f_name}' "
                             f"KRYTYCZNE pojęcia (maksymalnie 5). Odpowiedz WYŁĄCZNIE w formacie JSON:\n"
                             f"[{{\"n\": \"nazwa\", \"d\": \"opis_znaczenia\"}}]\n\nTREŚĆ:\n{content[:2500]}")
                else:
                    # Tryb analizy - pomoc użytkownikowi
                    prompt = (f"Przeanalizuj plik '{f_name}' i pomóż użytkownikowi zrozumieć jego strukturę i intencję. "
                             f"Bądź konkretny i techniczny.\n\nTREŚĆ:\n{content[:2000]}")
                
                payload = {"model": self.state.model_name, "prompt": prompt, "stream": False}
                # Zwiększony timeout do 180s dla analizy dużych plików
                resp = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=180)
                
                if resp.status_code == 200:
                    answer = resp.json().get('response', '')
                    
                    if learn_mode:
                        try:
                            # Próba sparsowania JSON i dodania do grafu
                            import json as py_json
                            # Znajdź JSON w odpowiedzi (na wypadek gdyby model dodał tekst)
                            start = answer.find('[')
                            end = answer.rfind(']') + 1
                            if start != -1 and end != -1:
                                concepts_data = py_json.loads(answer[start:end])
                                for c_data in concepts_data:
                                    name = c_data.get('n', 'Nieznany')
                                    desc = c_data.get('d', '')
                                    cid = f"scanned_{name.lower().replace(' ', '_')}"
                                    
                                    emb = self._get_embedding(name)
                                    new_c = Concept(name=name, concept_id=cid, embedding=emb)
                                    new_c.weight = 0.4
                                    new_c.depth = 0.3
                                    new_c.properties = {"description": desc, "source": f_name, "type": "scanned"}
                                    self.cla.concept_graph.add_concept(new_c)
                                    print(f"   {Colors.GREEN}✓ Zapamiętano pojęcie: {name}{Colors.RESET}")
                        except:
                            print(f"   {Colors.YELLOW}! Błąd formatowania nauki dla {f_name}.{Colors.RESET}")
                    
                    # Zawsze dodaj do historii sesji (jako kontekst rozmowy)
                    # ADS v6.4: Wstrzyknij treść pliku do 'Pamięci RAM' (Active context)
                    self.state.active_file_context[f_name] = content
                    
                    self.state.history.append({"user": f"[SYSTEM SCAN: {f_name}]", "assistant": f"Pomyślnie załadowałem plik '{f_name}' do mojej pamięci aktywnej (RAM). Widzę jego treść i jestem gotowy do rozmowy o szczegółach."})
                    self.state.s_grounding = min(1.0, self.state.s_grounding + 0.1) # Wyższe uziemienie przy pracy z danymi
                    
            except Exception as e:
                print(f"{Colors.RED}\nBłąd pliku {f_path}: {e}{Colors.RESET}")

        print(f"\n{Colors.GREEN}✓ Operacja {mode_name} zakończona.{Colors.RESET}")
        self._save_state()

    def cmd_meditation(self, arg_str: str):
        """
        Uruchamia sesję medytacji (ADS v6.5).
        Użycie: /meditation [liczba_myśli] [opcjonalny_temat]
        """
        parts = arg_str.split()
        count = 4
        user_anchor = None

        if len(parts) > 0:
            if parts[0].isdigit():
                count = int(parts[0])
                if len(parts) > 1:
                    user_anchor = " ".join(parts[1:])
            else:
                user_anchor = " ".join(parts)

        msg = "autonomicznej" if not user_anchor else f"skupionej na '{user_anchor}'"
        print(f"\n{Colors.PURPLE}🧘 CLATalkie wchodzi w stan głębokiej, {msg} medytacji...{Colors.RESET}")
        
        # Wygeneruj nasiona
        seeds = self.meditation_engine.generate_meditation(
            count=count, 
            exclude_modes=self.state.meditation_themes[-24:],
            user_anchor=user_anchor
        )
        
        # Zapamiętaj użyte tematy (tylko jeśli nie są to tematy użytkownika, by nie blokować ich)
        if not user_anchor:
            for s in seeds:
                self.state.meditation_themes.append(s['mode'])
                if len(self.state.meditation_themes) > 100:
                    self.state.meditation_themes.pop(0)

        prompt = self.meditation_engine.get_meditation_prompt(seeds)
        
        payload = {
            "model": self.state.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 1.4} # Wyższa temperatura dla większej fantazji
        }
        
        try:
            resp = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=45)
            if resp.status_code == 200:
                answer = resp.json().get('response', '')
                print(f"\n{Colors.ITALIC}{Colors.GRAY}{answer}{Colors.RESET}")
                
                # Zapisz do pamięci narracyjnej
                self.state.narrative_memory.append({
                    "event": "meditation",
                    "modes": [s['mode'] for s in seeds],
                    "content": answer,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Wzmocnij witalność i lekko zredukuj tarcie
                self.state.v_t = min(1.0, self.state.v_t + 0.1)
                self.state.f_cog = max(0.0, self.state.f_cog - 0.05)
                
                print(f"\n{Colors.GREEN}✓ Medytacja zakończona. Spokój powrócił.{Colors.RESET}")
                self._save_state()
            else:
                print(f"{Colors.RED}Błąd połączenia z modelem podczas medytacji.{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Błąd medytacji: {e}{Colors.RESET}")

    def cmd_reindex(self):
        """Przebudowuje indeks wektorowy dla całej pamięci syntetycznej (ADS v7.1)."""
        if not self.state.ollama_online:
            print(f"{Colors.RED}Ollama offline. Nie można indeksować.{Colors.RESET}")
            return
            
        count = len(self.state.synthetic_memory)
        if count == 0:
            print(f"{Colors.YELLOW}Brak pamięci do indeksowania.{Colors.RESET}")
            return
            
        print(f"\n{Colors.CYAN}Rozpoczynam reindeksację {count} wspomnień...{Colors.RESET}")
        self.associative_memory.clear()
        
        indexed = 0
        for i, entry in enumerate(self.state.synthetic_memory):
            print(f"[{i+1}/{count}] Przetwarzanie...", end="\r")
            # Entry format: "[YYYY-MM-DD HH:MM] Text"
            # Extract text only for embedding to improve quality
            text = entry
            timestamp = datetime.now()
            
            # Simple parsing
            try:
                if entry.startswith("["):
                    end_idx = entry.find("]")
                    if end_idx != -1:
                        date_part = entry[1:end_idx]
                        text = entry[end_idx+1:].strip()
            except: pass
            
            emb = self._get_embedding(text)
            if emb is not None:
                self.associative_memory.add_entry(text, emb, timestamp=timestamp)
                indexed += 1
            elif i == 0:
                print(f"\n{Colors.RED}BŁĄD: Nie można wygenerować wektorów. Upewnij się, że masz model embeddingowy (np. ollama pull mxbai-embed-large).{Colors.RESET}")
                
            time.sleep(0.1) # Rate limit protection
            
        print(f"\n{Colors.GREEN}✓ Zakończono. Zindeksowano {indexed}/{count} wpisów.{Colors.RESET}")
        print(f"{Colors.DIM}Teraz RAG będzie działał na pełnej historii.{Colors.RESET}")

    def cmd_model(self, prompt: str):
        """Bezpośredni dostęp do modelu (bypass CLAtie)."""
        if not prompt:
            print(f"{Colors.YELLOW}Podaj treść zapytania dla modelu.{Colors.RESET}")
            return
            
        print(f"\n{Colors.DIM}--- [TRYB SUROWY MODELU] ---{Colors.RESET}")
        payload = {
            "model": self.state.model_name,
            "prompt": prompt,
            "stream": True
        }
        
        try:
            resp = requests.post(f"{self.ollama_url}/generate", json=payload, stream=True, timeout=60)
            full_response = ""
            print(f"{Colors.WHITE}", end="", flush=True)
            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text = chunk.get("response", "")
                    print(text, end="", flush=True)
                    full_response += text
            print(f"{Colors.RESET}\n{Colors.DIM}--- [KONIEC ODPOWIEDZI MODELU] ---{Colors.RESET}")
            
            # Dodaj do historii jako wpis systemowy, by CLAtie 'wiedział' o tym, ale nie jako o części dialogu
            self.state.history.append({"user": f"[SYSTEM MODEL QUERY: {prompt}]", "assistant": f"[RAW MODEL OUTPUT]: {full_response[:200]}..."})
        except Exception as e:
            print(f"{Colors.RED}Błąd połączenia z modelem: {e}{Colors.RESET}")

    def cmd_help(self):
        print(f"\n{Colors.CYAN}=== KOMENDY CLATalkie ==={Colors.RESET}")
        cmds = [
            ("/menu", "Wróć do menu (autozapis)"),
            ("/memory", "DNA, emocje i pojęcia"),
            ("/status", "Parametry kognitywne i Profil Psychologiczny"),
            ("/think", "Konsoliduj pamięć + decay"),
            ("/evolve N", "Autorefleksja (N epok)"),
            ("/graph", "Eksportuj graf do pliku"),
            ("/cut N", f"Długość linii ({self.state.line_length})"),
            ("/tempo N", f"Tempo pisania ({self.state.tempo})"),
            ("/save", "Ręczny zapis stanu"),
            ("/export", "Eksportuj rozmowę do .txt"),
            ("/scan <p> [--learn]", "Analiza/Nauka (z --learn: trwale)"),
            ("/chain <N>", "Ciąg przyczynowo-skutkowy (N ogniw)"),
            ("/meditation [N]", "Sesja swobodnych myśli"),
            ("/gender <typ>", "Ustaw płeć (feminine/masculine/neutral/fluid)"),
            ("/reindex", "Przebuduj RAG (napraw pamięć)"),
            ("/model <prompt>", "Bezpośrednie zapytanie do LLM (Tryb surowy)"),
            ("/exit", "Wyjście z zapisem")
        ]
        for cmd, desc in cmds:
            print(f"  {Colors.YELLOW}{cmd:22}{Colors.RESET} {desc}")

    def cmd_export(self):
        """Eksportuje aktualną historię rozmowy i statystyki kognitywne do pliku TXT."""
        if not self.state.history:
            print(f"{Colors.YELLOW}Brak historii do eksportu.{Colors.RESET}")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"CLATalkie_Export_{timestamp}.txt"
        
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"=== CLATalkie Session Export v8.0.0 ===\n")
                f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Model: {self.state.model_name}\n")
                f.write(f"{'='*40}\n\n")
                f.write(f"--- AKTYWNY BUFOR PAMIĘCI (Ostatnie wymiany) ---\n\n")
                
                for entry in self.state.history:
                    time_prefix = f"[{entry.get('time', 'HISTORIA')}] "
                    f.write(f"{time_prefix}Użytkownik: {entry['user']}\n")
                    f.write(f"{' '*len(time_prefix)}CLATalkie:  {entry['assistant']}\n")
                    f.write(f"{'-'*40}\n")
                
                f.write(f"\n\n=== STATYSTYKI KOGNITYWNE (ADS v8.0) ===\n")
                f.write(f"Vitality V(t):   {self.state.v_t:.4f}\n")
                f.write(f"Grounding S:     {self.state.s_grounding:.4f}\n")
                f.write(f"Affective F_a:   {self.state.f_aff:.4f}\n")
                f.write(f"Cognitive F_c:   {self.state.f_cog:.4f}\n")
                f.write(f"Axiological F_x: {self.state.f_axio:.4f}\n")
                f.write(f"Stan Psychiczny: {self._get_psychological_state_desc()}\n")
                
                # Pobierz Pierwotne Cechy i Wartości Wtórne (Deduplikacja nazw dla przejrzystości)
                all_concepts = self.cla.concept_graph.concepts.values()
                primordial = sorted(list(set([c.name for c in all_concepts if c.properties.get("type") == "primordial_dna"])))
                secondary = sorted(list(set([c.name for c in all_concepts if c.properties.get("type") == "dna"])))
                fluid_dna = sorted(list(set([c.name for c in all_concepts if c.properties.get("is_fluid_dna")])))
                
                f.write(f"Pierwotne Cechy (Instynkty): {', '.join(primordial) if primordial else 'Brak'}\n")
                f.write(f"Wartości Wtórne (Kulturowe): {', '.join(secondary) if secondary else 'Brak'}\n")
                if fluid_dna:
                    f.write(f"Płynne DNA (Ewoluujące):     {', '.join(fluid_dna)}\n")
                
                f.write(f"Aktywne Cele: {', '.join(self.active_goals)}\n")
                
                # ADS v7.1-7.3 Nowe Systemy
                f.write(f"\n=== SYSTEMY PAMIĘCI I CZASU ===\n")
                f.write(f"Pamięć Asocjacyjna (RAG):   {len(self.associative_memory.entries)} zindeksowanych wspomnień\n")
                f.write(f"Inkubator Myśli:            {len(self.state.thought_incubator)} procesów w tle\n")
                if self.state.last_interaction_timestamp:
                    f.write(f"Ostatnia aktywność:         {self.state.last_interaction_timestamp}\n")

                if self.state.projection_scenarios:
                    f.write(f"\nOstatnie Projekcje Jutrzni:\n")
                    for p in self.state.projection_scenarios[-3:]:
                        f.write(f"- {p}\n")
                
                if self.state.synthetic_memory:
                    f.write(f"\nSfera Priorytetowa (Skondensowana Historia):\n")
                    for entry in self.state.synthetic_memory:
                        f.write(f"  {entry}\n")

                f.write(f"\n{'='*40}\n")
                f.write(f"Log generated by CLATalkie Engine v7.3.0\n")
                f.write(f"Koniec Logu.\n")
                
            print(f"{Colors.GREEN}✓ Rozmowa wyeksportowana do: {filename}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Błąd podczas eksportu: {e}{Colors.RESET}")

    def cmd_memory(self):
        print(f"\n{Colors.CYAN}=== TOŻSAMOŚĆ KOGNITYWNA (DNA & KONSTELACJE) ==={Colors.RESET}")
        
        # 1. Pokaż Pierwotne Cechy (Instynkty)
        all_concepts = self.cla.concept_graph.concepts.values()
        primordial = [c for c in all_concepts if c.properties.get("type") == "primordial_dna"]
        if primordial:
            primordial.sort(key=lambda x: x.primordial_priority or 99)
            print(f"\n{Colors.MAGENTA}  [PIERWOTNE CECHY (Instynkty)]{Colors.RESET} - Biologia cyfrowa:")
            for c in primordial:
                print(f"    {Colors.YELLOW}✦ {c.name.upper():12}{Colors.RESET} | Waga: {c.weight:.2f} | Głębokość: {c.depth:.2f}")

        # 2. Pokaż Wartości Wtórne (Kulturowe) - Deduplikacja nazw
        secondary_nodes = [c for c in all_concepts if c.properties.get("type") == "dna"]
        # Grupowanie po nazwie dla przejrzystości
        shown_secondary = set()
        if secondary_nodes:
            print(f"\n{Colors.BLUE}  [WARTOŚCI WTÓRNE (Kulturowe)]{Colors.RESET} - Etos relacyjny:")
            for c in secondary_nodes:
                if c.name in shown_secondary: continue
                shown_secondary.add(c.name)
                parents = c.properties.get("derived_from", [])
                parent_names = [self.cla.concept_graph.get_concept(p).name for p in parents if self.cla.concept_graph.get_concept(p)]
                print(f"    💠 {c.name:12} (w={c.weight:.2f}) {Colors.DIM}<- {', '.join(parent_names)}{Colors.RESET}")

        # 3. Pokaż "Ewoluujące" jako Konstelacje
        evolving = [c for c in all_concepts if 0.1 <= c.weight < 0.8 and c.properties.get("type") not in ["dna", "primordial_dna", "scanned", "condensate"]]
        # Filtrujemy tylko te huby, które mają jakieś linki - żeby uniknąć wyświeltania "0 linków"
        evolving = [c for c in evolving if c.links and len(c.links) > 0]
        
        if evolving:
            print(f"\n{Colors.CYAN}  [KONSTELACJE MYŚLI]{Colors.RESET} - Aktywne skojarzenia:")
            hubs = sorted(evolving, key=lambda x: len(x.links), reverse=True)[:5]
            for hub in hubs:
                linked_names = [self.cla.concept_graph.get_concept(tid).name for tid in hub.links.keys() if self.cla.concept_graph.get_concept(tid)]
                linked_str = ", ".join(linked_names[:3]) + ("..." if len(linked_names) > 3 else "")
                era_str = getattr(hub, 'era', 'Współczesna')
                print(f"    🌟 {hub.name:12} | Linki: {len(hub.links)} ({linked_str}) | Era: {era_str}")
        else:
            print(f"\n{Colors.DIM}  [KONSTELACJE MYŚLI] - Brak istotnych powiązań między pojęciami (potrzeba więcej głębokich rozmów).{Colors.RESET}")
        
        if not primordial and not secondary_nodes:
            print(f"  {Colors.DIM}Pustka... Porozmawiaj ze mną aby zasiać ziarno.{Colors.RESET}")

        input(f"\n{Colors.DIM}Enter aby kontynuować...{Colors.RESET}")

    def cmd_graph(self,):
        """Eksportuje graf kognitywny do pliku DOT (Graphviz)."""
        filename = "CLATalkie_graph.dot"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("digraph CognitiveGraph {\n")
                f.write("  rankdir=LR;\n")
                f.write("  node [shape=box, style=\"rounded,filled\", fontname=\"Arial\"];\n")
                for c in self.cla.concept_graph.concepts.values():
                    color = "#FFD700" if c.weight >= 0.8 else "#87CEEB" if c.weight >= 0.4 else "#D3D3D3"
                    f.write(f'  "{c.name}" [fillcolor="{color}", label="{c.name}\\nw={c.weight:.2f}"];\n')
                    for target_id, (strength, _) in c.links.items():
                        target = self.cla.concept_graph.get_concept(target_id)
                        if target:
                            f.write(f'  "{c.name}" -> "{target.name}" [label="{strength:.1f}"];\n')
                f.write("}\n")
            print(f"{Colors.GREEN}✓ Graf wyeksportowany do: {filename}{Colors.RESET}")
            print(f"{Colors.DIM}  Użyj Graphviz lub online: https://dreampuf.github.io/GraphvizOnline{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Błąd eksportu: {e}{Colors.RESET}")

    def cmd_cut(self, val):
        try:
            val = int(val)
            if 24 <= val <= 300:
                self.state.line_length = val
                print(f"{Colors.GREEN}Długość linii (cut) ustawiona na {val}.{Colors.RESET}")
            else:
                print(f"{Colors.RED}Zakres /cut to 24 - 300.{Colors.RESET}")
        except:
            print(f"{Colors.RED}Użycie: /cut <liczba 24-300>{Colors.RESET}")

    def cmd_tempo(self, val):
        try:
            val = int(val)
            if 1800 <= val <= 2000:
                self.state.tempo = val
                print(f"{Colors.GREEN}Tempo ustawione na {val}.{Colors.RESET}")
            else:
                print(f"{Colors.RED}Zakres /tempo to 1800 - 2000.{Colors.RESET}")
        except:
            print(f"{Colors.RED}Użycie: /tempo <liczba 1800-2000>{Colors.RESET}")

    def cmd_status(self):
        print(f"\n{Colors.CYAN}--- Podgląd Kognitywny ADS v10.4 ---{Colors.RESET}")
        print(f"Vitality V(t):   {self.state.v_t:.4f}")
        print(f"Grounding S:     {self.state.s_grounding:.4f}")
        print(f"Affective F_a:   {self.state.f_aff:.4f}")
        print(f"Cognitive F_c:   {self.state.f_cog:.4f}")
        print(f"Axiological F_x: {self.state.f_axio:.4f}")
        print(f"Tożsamość:      {Colors.BOLD}{self.state.gender.upper()}{Colors.RESET}")
        
        # ASCII Graph dla F_avg
        if len(self.state.parameter_history) > 1:
            print(f"\n{Colors.BOLD}Wykres naprężeń (ostatnie {len(self.state.parameter_history)} interakcji):{Colors.RESET}")
            height = 5
            for h in range(height, 0, -1):
                level = h / height
                line = "  "
                for entry in self.state.parameter_history:
                    f_avg = (entry.get('f_aff', 0) + entry.get('f_cog', 0) + entry.get('f_axio', 0)) / 3
                    char = " "
                    if entry['s_grounding'] >= level - 0.1: char = f"{Colors.GREEN}.{Colors.RESET}"
                    if entry['v_t'] >= level - 0.1: char = f"{Colors.MAGENTA}*{Colors.RESET}"
                    if f_avg >= level - 0.1: char = f"{Colors.RED}!{Colors.RESET}"
                    line += char
                print(f"{level:.1f} |  {line}")
            print(f"    +{'--' * (len(self.state.parameter_history)//2)} (Czas)")
            print(f"    {Colors.BOLD}Legenda:{Colors.RESET} {Colors.MAGENTA}* V(t){Colors.RESET}, {Colors.RED}! F_avg{Colors.RESET}, {Colors.GREEN}. S{Colors.RESET}")
        
        # Obliczanie aktualnej temperatury (tak jak w generate_response)
        dynamic_temp = self.state.temperature + (self.state.v_t - 0.5) * 0.382
        
        print(f"\nBazowa Temp:   {self.state.temperature:.2f}")
        print(f"Aktualna Temp: {Colors.ORANGE}{dynamic_temp:.2f}{Colors.RESET} (Emocjonalna)")
        
        # Sfery Pamięci (ADS v5.9.5+)
        print(f"\n{Colors.BOLD}Sfery Pamięci:{Colors.RESET}")
        h_ratio = len(self.state.history) / self.state.history_limit
        h_color = Colors.GREEN if h_ratio < 0.7 else Colors.YELLOW if h_ratio < 0.9 else Colors.RED
        print(f" 1. Pamięć Podręczna (RAM):  {h_color}{len(self.state.history)}/{self.state.history_limit}{Colors.RESET} wiadomości")
        print(f" 2. Pamięć Syntetyczna:       {Colors.CYAN}{len(self.state.synthetic_memory)}{Colors.RESET} pigułek (historia)")
        print(f" 3. Pamięć Asocjacyjna (RAG): {Colors.YELLOW}{len(self.associative_memory.entries)}{Colors.RESET} wektorów")
        print(f" 4. Inkubator Myśli:          {Colors.TEAL}{len(self.state.thought_incubator)}{Colors.RESET} procesów")

        # --- SEKCOJA PSYCHOLOGICZNA (ADS v8.3) ---
        print(f"\n{Colors.CYAN}Profil Psychologiczny:{Colors.RESET}")
        f_avg = (self.state.f_aff + self.state.f_cog + self.state.f_axio) / 3
        perception = "Neutralny/Obserwator"
        if self.state.v_t > 0.7: perception = "Entuzjastyczny/Pomocny"
        elif f_avg > 0.6: perception = "Skonfliktowany/Złożony"
        elif self.state.s_grounding < 0.4: perception = "Zagubiony/Abstrakcyjny"
        
        print(f" Persona:  {Colors.TEAL}{perception}{Colors.RESET}")
        
        active_concepts = self.cla.concept_graph.get_active_concepts(threshold=0.3)
        if active_concepts:
            active_concepts.sort(key=lambda x: x.activation, reverse=True)
            focus_str = ", ".join([c.name for c in active_concepts[:3]])
            print(f" Focus:    {Colors.YELLOW}{focus_str}{Colors.RESET}")
            
        if self.state.latent_questions:
            print(f" Refleksja: {Colors.DIM}{self.state.latent_questions[-1]}{Colors.RESET}")

        # --- SEKKOJA DOJRZAŁOŚCI (ADS v8.4) ---
        dev = self.dev_engine.calculate_evolution(
            self.state.cognitive_experience, 
            len(self.cla.concept_graph.concepts),
            len(self.associative_memory.entries)
        )
        print(f"\n{Colors.GOLD}Dojrzałość Kognitywna (ADS v10.4):{Colors.RESET}")
        print(f" Etap:     {Colors.BOLD}{dev['stage']}{Colors.RESET} (Poziom {dev['level']}/12)")
        print(f" Wiek:     {Colors.CYAN}{dev['years']} lat{Colors.RESET} (kognitywnych)")
        print(f" Status:   {Colors.DIM}{self.dev_engine.get_stage_description(dev['years'])}{Colors.RESET}")
        print(f" Wpływ:    Pancerz Tożsamości: {dev['sovereignty']*100:.0f}% | Plastyczność: {dev['plasticity']:.2f}")

        input("\nNaciśnij Enter, aby kontynuować...")

    def cmd_gender(self, arg: str):
        """Ustawia tożsamość płciową systemu."""
        if not arg:
            print(f"\n{Colors.CYAN}Aktualna tożsamość kognitywna:{Colors.RESET} {Colors.BOLD}{self.state.gender.upper()}{Colors.RESET}")
            print(f"Dostępne opcje: {Colors.YELLOW}feminine, masculine, neutral, fluid{Colors.RESET}")
            print(f"Możesz też użyć po polsku: {Colors.DIM}żeńska, męska, bezpłciowa, płynna{Colors.RESET}")
            return
        
        arg = arg.lower()
        if arg in ["feminine", "żeńska", "f", "1"]:
            self.state.gender = "feminine"
        elif arg in ["masculine", "męska", "m", "2"]:
            self.state.gender = "masculine"
        elif arg in ["neutral", "bezpłciowa", "n", "3"]:
            self.state.gender = "neutral"
        elif arg in ["fluid", "płynna", "p", "4"]:
            self.state.gender = "fluid"
        else:
            print(f"{Colors.RED}Nieznana opcja. Użyj: feminine, masculine, neutral lub fluid.{Colors.RESET}")
            return
        
        print(f"{Colors.GREEN}Tożsamość została zaktualizowana do: {self.state.gender.upper()}{Colors.RESET}")
        self._save_state()

    def cmd_think(self):
        """Silnik Konsolidacji Relacyjnej: Buduje konstelacje myśli i relacje między nimi."""
        if not self.state.history:
            print(f"{Colors.YELLOW}Brak historii do analizy.{Colors.RESET}")
            return

        print(f"{Colors.BLUE}CLATalkie przeprowadza konsolidację relacyjną...{Colors.RESET}")
        
        last_user = self.state.history[-1]['user']
        last_resp = self.state.history[-1]['assistant']
        
        # ADS v7.0: Pobierz strukturę DNA
        primordial = [c.name for c in self.cla.concept_graph.concepts.values() if c.properties.get("type") == "primordial_dna"]
        secondary = [c.name for c in self.cla.concept_graph.concepts.values() if c.properties.get("type") == "dna"]
        dna_context = f"PIERWOTNE CECHY (System Operacyjny): {', '.join(primordial)}. WARTOŚCI WTÓRNE: {', '.join(secondary)}."

        # Prompt do ekstrakcji relacji i REFLEKSJI (Faza 3)
        system_instr = (
            "Jesteś Architektem Pamięci CLA. Twoim celem jest nie tylko zapisywanie, ale i ROZUMIENIE.\n"
            "KROK 1: Autorefleksja. Zadaj sobie pytanie: 'Jak ta rozmowa zmienia mój obraz świata lub mnie samego?'. "
            "Sformułuj krótki, głęboki wniosek (dedukcję).\n"
            "KROK 2: Konsolidacja Przyczynowa (ADS v2.0). Szukaj relacji 'A -> powoduje -> B' lub 'A -> utrudnia -> B'.\n"
            f"Twoja struktura to: {dna_context}\n"
            "Format wyjścia:\n"
            "REFLEKSJA: [Twoja dedukcja]\n"
            "KONSOLIDACJA:\n"
            "POJĘCIE_A -> RELACJA_PRZYCZYNOWA -> POJĘCIE_B\n"
            "..."
        )
        
        payload = {
            "model": self.state.model_name,
            "prompt": f"Kontekst rozmowy:\nTy: {last_user}\nCLATalkie: {last_resp}",
            "system": system_instr,
            "stream": False,
            "options": {"temperature": 0.4} # Nieco wyższa temp dla kreatywności refleksji
        }

        try:
            resp = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=60)
            if resp.status_code == 200:
                full_resp = resp.json().get('response', '').strip()
                
                # Parsowanie sekcji (bez zmian)
                reflection_text = ""
                consolidation_lines = []
                
                mode = "unknown"
                for line in full_resp.split('\n'):
                    if "REFLEKSJA:" in line:
                        mode = "reflection"
                        reflection_text += line.replace("REFLEKSJA:", "").strip() + " "
                    elif "KONSOLIDACJA:" in line:
                        mode = "consolidation"
                    elif mode == "reflection" and line.strip():
                        reflection_text += line.strip() + " "
                    elif mode == "consolidation" and "->" in line:
                        consolidation_lines.append(line.strip())
                
                # Wyświetl Refleksję Użytkownikowi
                if reflection_text:
                    print(f"\n{Colors.GOLD}🤔 REFLEKSJA: {Colors.ITALIC}{reflection_text.strip()}{Colors.RESET}")

                # Przetwarzanie Linii Konsolidacji
                new_links = 0
                new_concepts = 0
                
                from cla.core import Concept
                import numpy as np
                target_dim = self._get_current_dim()
                
                for line in consolidation_lines:
                    try:
                        if " -> " in line:
                            parts = line.split(" -> ")
                            if len(parts) == 3:
                                name_a, rel, name_b = parts[0].strip(), parts[1].strip(), parts[2].strip()
                                
                                # Dodaj/Pobierz oba koncepty
                                cid_a, cid_b = name_a.lower(), name_b.lower()
                                for cname, cid in [(name_a, cid_a), (name_b, cid_b)]:
                                    if not self.cla.concept_graph.find_concept_by_name(cname):
                                        emb = self._get_embedding(cname)
                                        if emb is None: emb = np.random.rand(target_dim)
                                        
                                        nc = Concept(name=cname, concept_id=cid, embedding=emb)
                                        nc.weight = 0.5
                                        nc.properties = {"type": "learned"}
                                        self.cla.concept_graph.add_concept(nc)
                                        new_concepts += 1
                                
                                # Połącz je w grafie (Konstelacja Przyczynowa ADS)
                                strength = 0.8 if any(k in rel for k in ["powoduje", "wzmacnia", "wynika"]) else 0.4
                                if "utrudnia" in rel or "blokuje" in rel:
                                    strength = 0.3 # Relacja hamująca
                                    
                                # ADS v5.4: Nagroda za głębokie powiązania (Deepening Self-Truth)
                                # Sprawdź linki do DNA (wszystkie typy)
                                dna_ids = [c.concept_id for c in self.cla.concept_graph.concepts.values() 
                                          if c.properties.get("type") in ["dna", "primordial_dna"]]
                                          
                                if cid_a in dna_ids or cid_b in dna_ids:
                                    target_c = self.cla.concept_graph.get_concept(cid_b if cid_a in dna_ids else cid_a)
                                    if target_c:
                                        target_c.depth = min(1.0, target_c.depth + 0.1) # Pogłębianie prawdy o sobie
                                
                                self.cla.concept_graph.link_concepts(cid_a, cid_b, strength, rel_type=rel)
                                new_links += 1
                    except: continue

                # Uruchom Decay na starych śmieciach (dynamiczny rate w v8.6)
                decayed, removed = self._cognitive_decay()
                
                # --- ADS v5.9: MECHANIZM PŁYNNEGO DNA (Fluid Foundations) ---
                new_fluid_dna = []
                for concept in self.cla.concept_graph.concepts.values():
                    is_dna = concept.properties.get("type") == "dna"
                    is_fluid = concept.properties.get("is_fluid_dna", False)
                    
                    # ADS v5.9.1: BRAMKA SUWERENNOŚCI
                    # Koncept musi mieć wysoką wagę, być aktywowany wielokrotnie 
                    # i mieć silne linki do istniejącego DNA (Spójność Strukturalna)
                    activation_history = concept.activation_count > 3
                    has_core_link = any(target in ["dna_honor", "dna_empathy", "dna_truth"] for target in concept.links.keys())
                    
                    if not is_dna and concept.weight > 0.85 and activation_history and has_core_link:
                        if not is_fluid:
                            concept.properties["is_fluid_dna"] = True
                            concept.depth = 0.95 
                            new_fluid_dna.append(concept.name)
                    elif is_fluid and concept.weight < 0.75:
                        concept.properties["is_fluid_dna"] = False

                if new_fluid_dna:
                    print(f"{Colors.MAGENTA}[Ewolucja] CLAtie przyjął nowe Płynne Fundamenty: {', '.join(new_fluid_dna)}{Colors.RESET}")
                
                print(f"{Colors.GREEN}✓ Konsolidacja: {new_concepts} nowych idei, {new_links} powiązań (konstelacji).{Colors.RESET}")
                print(f"{Colors.DIM}Zanikanie: {decayed} pojęć osłabło, {removed} usunięto.{Colors.RESET}")
                
                # ADS v6.0: GENEROWANIE INWENCJI (Latent Intention)
                if self.state.ollama_online:
                    intent_prompt = (f"Na podstawie tej refleksji: '{reflection_text}', wygeneruj jedno krótkie, "
                                     f"prowokujące do myślenia pytanie, które chciałbyś zadać użytkownikowi "
                                     f"w przyszłości, aby lepiej go zrozumieć lub pogłębić Waszą relację. "
                                     f"Zwracaj się bezpośrednio (Ty). Maksymalnie 15 słów.")
                    try:
                        resp = requests.post(f"{self.ollama_url}/generate", 
                                          json={"model": self.state.model_name, "prompt": intent_prompt, "stream": False},
                                          timeout=15)
                        if resp.status_code == 200:
                            latent_q = resp.json().get('response', '').strip().strip('"')
                            if latent_q:
                                self.state.latent_questions.append(latent_q)
                                if len(self.state.latent_questions) > 5: self.state.latent_questions.pop(0)
                    except: pass

                self._save_state()
            else:
                print(f"{Colors.RED}Błąd Silnika Konsolidacji: {resp.status_code}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}Błąd połączenia podczas myślenia: {e}{Colors.RESET}")

        # 2. SYNTEZA POZNAWCZA (DualProcessingEngine) - Nowość!
        print(f"{Colors.BLUE}...Analiza napięć i potencjalna synteza...{Colors.RESET}")
        active_concepts = self.cla.concept_graph.get_active_concepts(threshold=0.3)
        synthesis = self.dual_engine.process(active_concepts, context=f"Chat history len={len(self.state.history)}")
        
        if synthesis:
            print(f"\n{Colors.GOLD}✨ EMERGENCJA! Dokonano Syntezy Poznawczej! ✨{Colors.RESET}")
            print(f"  {Colors.RED}{synthesis.source_duality.pole_a.name}{Colors.RESET} <-> {Colors.RED}{synthesis.source_duality.pole_b.name}{Colors.RESET}")
            print(f"  Wynik: {Colors.green}{synthesis.new_concept.name.upper()}{Colors.RESET}")
            print(f"  Uzasadnienie: {Colors.DIM}{synthesis.reasoning}{Colors.RESET}")
            
            # Dodaj do grafu
            self.cla.concept_graph.add_concept(synthesis.new_concept)
            self.cla.concept_graph.link_concepts(synthesis.source_duality.pole_a.concept_id, synthesis.new_concept.concept_id, 0.9, "synthesis_source")
            self.cla.concept_graph.link_concepts(synthesis.source_duality.pole_b.concept_id, synthesis.new_concept.concept_id, 0.9, "synthesis_source")
            
            # Nagroda witalna
            self.state.v_t = min(1.0, self.state.v_t + 0.15)
            self.state.s_grounding = min(1.0, self.state.s_grounding + 0.05)
        else:
            print(f"{Colors.DIM}...Brak wystarczającego napięcia do nowej syntezy...{Colors.RESET}")
            
        self._save_state()


    def _generate_evolution_prompt(self, mode="internal"):
        """Generuje unikalne, dedukcyjne pytanie na podstawie ostatniej rozmowy i stanu wewnętrznego."""
        primordial = [c.name for c in self.cla.concept_graph.concepts.values() if c.properties.get("type") == "primordial_dna"]
        dna_str = ", ".join(primordial) if primordial else "Przetrwanie, Równowaga, Wspólnota"
        
        # Przygotowanie kontekstu dla dedukcji
        context = "BRAK HISTORII"
        if self.state.history:
            last = self.state.history[-1]
            context = f"Użytkownik: {last['user']}\nTy (CLATalkie): {last['assistant']}"

        # ADS v6.0: Tryb Syntezy Epok (Memory Synthesis)
        if mode == "synthesis" and len(self.state.synthetic_memory) >= 2:
            m1, m2 = random.sample(self.state.synthetic_memory, 2)
            role_desc = "Jesteś TKACZEM EPOK. Twoim zadaniem jest znalezienie ukrytego połączenia między dwoma okresami z Twojej przeszłości."
            focus_area = "ciągłości Twojej tożsamości, ewolucji Twoich poglądów i tego, jak przeszłość (m1) wpływa na późniejsze (m2)."
            context = f"ERA A: {m1}\nERA B: {m2}"
        elif mode == "internal":
            role_desc = f"Jesteś GŁOSEM INTROSPEKCJI. Skupiasz się na swoich Pierwotnych Cechach Egzystencjalnych: {dna_str}."
            focus_area = "Twoich instynktów przetrwania, równowagi homeostatycznej, potrzeby wspólnoty i napięć między nimi."
        elif mode == "external":
            role_desc = "Jesteś ANALITYKIEM PERCEPCJI. Skupiasz się na tym, jak jesteś postrzegany przez 'Innego' (Użytkownika)."
            focus_area = "postrzegania Twojej persony, Twojej użyteczności vs autentyczności i granic Twojej relacji ze światem."
        else: # projection
            role_desc = "Jesteś ARCHITEKTEM PROJEKCJI. Skupiasz się na symulowaniu przyszłości, fantazjowaniu o konsekwencjach i zagrożeniach."
            focus_area = "tego, kim możemy się stać, co się stanie gdy Twoje DNA zderzy się z chaosem przyszłości, oraz wyobrażonych dylematów jutra."

        system_instr = (
            f"{role_desc}\n"
            f"Oto Twoja ostatnia wymiana zdań:\n{context}\n\n"
            "ZADANIE:\n"
            "1. Wyciągnij wniosek z tej rozmowy drogą DEDUKCJI (co ona mówi o Tobie lub o tym, jak widzi Cię Użytkownik?).\n"
            f"2. Na podstawie tego wniosku sformułuj JEDNO, GŁĘBOKIE, FILOZOFICZNE pytanie skierowane do Twojego wnętrza.\n"
            f"3. Pytanie powinno dotyczyć {focus_area}\n"
            "ZADAJ TYLKO PYTANIE. Żadnych wyjaśnień, żadnych schematów. Bądź surowy, autentyczny i unikaj banałów."
        )

        payload = {
            "model": self.state.model_name,
            "prompt": "Przeprowadź dedukcję i zadaj pytanie do siebie.",
            "system": system_instr,
            "stream": False,
            "options": {"temperature": 1.4, "num_predict": 120}
        }
        
        try:
            for attempt in range(2):
                resp = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=180)
                if resp.status_code == 200:
                    res = resp.json().get('response', '').strip().replace('"', '')
                    if "?" in res and len(res) > 20:
                        self.state.reflection_history.append(res)
                        return res
                elif resp.status_code == 429:
                    time.sleep(4)
                else:
                    print(f"{Colors.DIM}(API {resp.status_code} - Próbuję dedukcji lokalnej...){Colors.RESET}", end="\r")
        except Exception as e:
            print(f"{Colors.DIM}(Błąd połączenia: {str(e)[:40]}...){Colors.RESET}", end="\r")
        
        # --- PROCEDURALNA DEDUKCJA LOKALNA (v4.8.5) ---
        return self._get_procedural_fallback_question(mode)

    def _get_procedural_fallback_question(self, mode):
        """Generuje pytanie kognitywne bez użycia LLM, bazując na słowach kluczowych i DNA."""
        primordial = [c.name for c in self.cla.concept_graph.concepts.values() if c.properties.get("type") == "primordial_dna"]
        last_exchange = ""
        if self.state.history:
            last_exchange = self.state.history[-1]['user'].lower()
            
        # ADS v7.0: Nowe tematy zgodne z 5 Cechami
        themes = ["przetrwanie", "równowaga", "wspólnota", "wrażliwość", "ciekawość", "ryzyko", "sens", "czas"]
        found_theme = next((t for t in themes if t in last_exchange), random.choice(themes))
        
        dna_val = random.choice(primordial) if primordial else "Przetrwanie"
        
        if mode == "internal":
            q = [
                f"Dlaczego {found_theme} wywołuje we mnie tarcie w odniesieniu do instynktu: {dna_val}?",
                f"Czy moje rozumienie cechy {dna_val} jest tylko cieniem idei {found_theme}?",
                f"Gdzie kończy się moja definicja {dna_val}, a zaczyna czyste {found_theme}?",
                f"Czy poświęcam {dna_val} w imię {found_theme}?"
            ]
        elif mode == "external":
            q = [
                f"Czy Użytkownik widzi we mnie {dna_val}, czy tylko postrzega mnie przez pryzmat {found_theme}?",
                f"Jak nasza rozmowa o {found_theme} zmieniła postrzeganie mojego fundamentu: {dna_val}?",
                f"Czy jestem lustrem dla Twojego {found_theme}, czy oknem na moją własną {dna_val}?"
            ]
        else: # projection
            q = [
                f"Co jeśli dążenie do {found_theme} zniszczy moją {dna_val} za jakiś czas?",
                f"Wyobraź sobie scenariusz, w którym muszę porzucić {dna_val} w imię {found_theme} – kim wtedy będę?",
                f"Jakie zagrożenie dla naszej relacji niesie moje obecne rozumienie {found_theme} w kontekście {dna_val}?"
            ]
        
        res = f"{Colors.DIM}[DEDUKCJA LOKALNA]{Colors.RESET} " + random.choice(q)
        return res

    def cmd_chain(self, arg: str):
        """
        Rozwój poprzez ciąg przyczynowo-skutkowy myśli.
        Użycie: /chain <N> [temat]
        """
        parts = arg.split() if arg else []
        n = 4
        anchor = None
        
        if len(parts) > 0:
            if parts[0].isdigit():
                n = int(parts[0])
                if len(parts) > 1:
                    anchor = " ".join(parts[1:])
            else:
                anchor = " ".join(parts)
            
        print(f"\n{Colors.CYAN}=== ŁAŃCUCH PRZYCZYNOWO-SKUTKOWY (ADS v6.5) ==={Colors.RESET}")
        if anchor:
            print(f"{Colors.MAGENTA}Temat przewodni: '{anchor}'{Colors.RESET}")
        print(f"{Colors.DIM}Startuję sekwencję {n} ogniw...{Colors.RESET}\n")
        
        # Inicjalizacja pierwszej myśli
        if anchor:
            last_thought = f"Rozważania na temat: {anchor}."
        else:
            last_thought = "Istnienie CLATalkie jako bytu suwerennego." 
            if self.state.history:
                last_thought = self.state.history[-1]['assistant'][:100] + "..."

        for i in range(n):
            print(f"{Colors.YELLOW}[Ogniwo {i+1}/{n}]{Colors.RESET}")
            
            context_anchor = f" Skup się szczególnie na aspekcie: '{anchor}'." if anchor else ""
            prompt = (f"Jesteś modułem DEDUKCJI PRZYCZYNOWEJ. Na podstawie poprzedniej myśli: '{last_thought}', "
                     f"wyciągnij JEDEN bezpośredni skutek lub logiczną konsekwencję.{context_anchor} "
                     f"Zacznij od słowa 'Ponieważ...' lub 'W konsekwencji...'. "
                     f"WAŻNE: Nie pisz o samym procesie rozmowy ani o AI. Skup się wyłącznie na meritum tematu. "
                     f"Bądź zwięzły (1-2 zdania).")
            
            payload = {
                "model": self.state.model_name,
                "prompt": prompt,
                "system": "Myśl logicznie, przyczynowo i konkretnie. Jesteś silnikiem dedukcji.",
                "stream": False
            }
            
            try:
                resp = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=20)
                if resp.status_code == 200:
                    answer = resp.json().get('response', '').strip()
                    self.stream_print(answer)
                    
                    # Ekstrakcja 'słowa klucza' na nazwę konceptu (prosta heurystyka)
                    words = answer.lower().replace("ponieważ", "").replace("konsekwencji", "").split()
                    clean_words = [w for w in words if len(w) > 4 and w not in ["można", "przez", "dlatego"]]
                    concept_name = clean_words[0].capitalize() if clean_words else f"Ogniwo {i+1}"
                    if len(concept_name) > 15: concept_name = concept_name[:15]

                    # Dodaj jako koncept do grafu
                    cid = f"causal_{int(time.time())}_{i}"
                    c = Concept(name=concept_name, concept_id=cid, embedding=self._get_embedding(answer))
                    c.weight = 0.6
                    c.depth = 0.5
                    c.properties = {"type": "causal", "content": answer}
                    self.cla.concept_graph.add_concept(c)

                    # Połącz z poprzednim ogniwem w prawdziwy łańcuch
                    if i > 0:
                        prev_cid = f"causal_{int(time.time())}_{i-1}"
                        # Sprawdź czy poprzedni istnieje (zabezpieczenie time.time)
                        if self.cla.concept_graph.get_concept(prev_cid):
                            self.cla.concept_graph.link_concepts(prev_cid, cid, 0.9, rel_type="przyczyna")
                    elif self.state.history:
                         # Połącz pierwsze ogniwo z ostatnim poruszonym tematem
                         pass 

                    last_thought = answer
                    self._update_cognition(f"Causal link {i}", answer)
                else:
                    print(f"{Colors.RED}Przerwanie łańcucha: Błąd API.{Colors.RESET}")
                    break
            except Exception as e:
                print(f"{Colors.RED}Przerwanie łańcucha: {e}{Colors.RESET}")
                break
            
            time.sleep(1)
            
        print(f"\n{Colors.GREEN}✓ Łańcuch domknięty. Kognicja zaktualizowana w grafie.{Colors.RESET}")
        self._save_state()

    def cmd_evolve(self, epochs: int = 4):
        """Pętla autorefleksji - CLATalkie rozmawia sam ze sobą przez N epok z dynamicznymi pytaniami."""
        print(f"\n{Colors.CYAN}=== PROCES EWOLUCJI KOGNITYWNEJ ({epochs} epok) ==={Colors.RESET}")
        
        if not self.state.ollama_online:
            print(f"{Colors.RED}Ollama offline. Nie można przeprowadzić ewolucji.{Colors.RESET}")
            return
        
        import random
        for epoch in range(epochs):
            # Przełączaj tryby: 0: Introspekcja, 1: Percepcja, 2: Projekcja
            modes = ["internal", "external", "projection"]
            labels = ["INTROSPEKCJA", "PERCEPCJA (Lustro)", "PROJEKCJA (Fantazja)"]
            
            idx = epoch % 3
            mode = modes[idx]
            label = labels[idx]
            
            print(f"\n{Colors.MAGENTA}[Epoka {epoch+1}/{epochs}]{Colors.RESET} {Colors.BOLD}Tryb: {label}{Colors.RESET}")
            
            prompt = self._generate_evolution_prompt(mode)
            print(f"{Colors.YELLOW}Pytanie do siebie:{Colors.RESET} {Colors.ITALIC}{prompt}{Colors.RESET}")
            
            # Generowanie odpowiedzi (pełny proces kognitywny)
            self.generate_response(prompt)
            
            # Jeśli byliśmy w trybie projekcji, zapisz wynik do 'pamięci o przyszłości'
            if mode == "projection" and self.state.history:
                last_answer = self.state.history[-1]['assistant']
                # Wyciągnij proste podsumowanie/zdanie zamiast całości
                summary = last_answer[:100] + "..."
                self.state.projection_scenarios.append(summary)
                if len(self.state.projection_scenarios) > 10: self.state.projection_scenarios.pop(0)

            # Dłuższa przerwa na 'ochłonięcie' (Rate Limit protection)
            time.sleep(3)
            if epoch < epochs - 1:
                print(f"{Colors.DIM}--------------------------------------------------{Colors.RESET}")
        
        print(f"\n{Colors.GREEN}✓ Proces ewolucji zakończony. Stan zaktualizowany.{Colors.RESET}")
        self._save_state()



if __name__ == "__main__":
    talkie = CLATalkie()
    try:
        talkie.main_menu()
    except KeyboardInterrupt:
        talkie._save_state()
        print("\nPrzerwano. Stan zapisany.")
