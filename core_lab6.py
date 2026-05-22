import pickle
import json
import csv
import os
from enum import Enum
from dataclasses import dataclass
from datetime import time
from typing import List, Generator

# 1. ENUM TYPE
class DayOfWeek(Enum):
    MONDAY = "Понеділок"
    TUESDAY = "Вівторок"
    WEDNESDAY = "Середа"
    THURSDAY = "Четвер"
    FRIDAY = "П'ятниця"

@dataclass
class Teacher:
    name: str
    department: str

# 2. FUNCTOR
class LoadCalculator:
    def __init__(self):
        self.total_minutes = 0
        self.calls_count = 0

    def __call__(self, start: time, end: time) -> int:
        self.calls_count += 1
        duration = (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)
        self.total_minutes += duration
        return duration

# 3. BASE AND DERIVED CLASSES
@dataclass
class Event:
    subject: str
    teacher: Teacher
    room: str
    start_time: time
    end_time: time

    def __post_init__(self):
        if self.start_time >= self.end_time:
            raise ValueError("Start time cannot be later than or equal to end time!")

    def __str__(self):
        return f"{self.subject} ({self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}) | Room: {self.room}"

class Lecture(Event):
    def __str__(self):
        return f"[Lecture] {super().__str__()} | Teacher: {self.teacher.name}"

class Practice(Event):
    def __str__(self):
        return f"[Practice] {super().__str__()} ({self.teacher.department})"

# FIX: make Exam a dataclass that extends Event
@dataclass
class Exam(Event):
    assistant: str

    def __str__(self):
        return f"!!! EXAM !!! {super().__str__()} | Assistant: {self.assistant}"

# 4. CUSTOM ITERATOR
class RoomFilterIterator:
    def __init__(self, events: List[Event], target_room: str):
        self.events = events
        self.target_room = target_room
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        while self.index < len(self.events):
            event = self.events[self.index]
            self.index += 1
            if event.room == self.target_room:
                return event
        raise StopIteration

# 5. MANAGER CLASS WITH PERSISTENCE (Schedule)
class Schedule:
    def __init__(self, day: DayOfWeek):
        self.day = day
        self.items: List[Event] = []
        self.load_calc = LoadCalculator()
        
        # External configuration fields
        self.institution_name = "Default University"
        self.default_page_size = 2

    def add_event(self, event: Event):
        try:
            with self.check_collision(event):
                self.items.append(event)
                self.load_calc(event.start_time, event.end_time)
                print(f"[System] Event '{event.subject}' added successfully.")
        except ValueError as e:
            print(f"[System Error] Cannot add '{event.subject}': {e}")

    def check_collision(self, new_event: Event):
        class CollisionChecker:
            def __init__(self, schedule, event):
                self.schedule = schedule
                self.event = event

            def __enter__(self):
                for existing in self.schedule.items:
                    if existing.room == self.event.room:
                        if not (self.event.end_time <= existing.start_time or 
                                self.event.start_time >= existing.end_time):
                            raise ValueError(f"Room occupied by '{existing.subject}'")
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                return False
        
        return CollisionChecker(self, new_event)

    def paginate_schedule(self, page_size: int) -> Generator:
        sorted_items = sorted(self.items, key=lambda x: x.start_time)
        for i in range(0, len(sorted_items), page_size):
            yield sorted_items[i : i + page_size]

    def filter_by_room(self, room_number: str):
        return RoomFilterIterator(self.items, room_number)

    def __iter__(self):
        return iter(sorted(self.items, key=lambda x: x.start_time))

    # --- LAB 6 NEW METHODS ---

    def load_config(self, filepath="config.json"):
        """Task 4: Load external settings from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.institution_name = config.get("institution_name", self.institution_name)
        self.default_page_size = config.get("default_page_size", self.default_page_size)
        print(f"[JSON] Config loaded for: {self.institution_name}")

    def save_system_state(self, filepath="schedule_state.pkl"):
        """Task 2: Full system state backup using Pickle"""
        with open(filepath, 'wb') as f:
            pickle.dump(self.items, f)
        print(f"[Pickle] System state successfully saved to '{filepath}'.")

    def load_system_state(self, filepath="schedule_state.pkl"):
        """Task 2: Full system state restoration using Pickle"""
        try:
            with open(filepath, 'rb') as f:
                self.items = pickle.load(f)
            print(f"[Pickle] State restored. Loaded {len(self.items)} events.")
        except FileNotFoundError:
            print(f"[Error] Backup file '{filepath}' not found.")

    def export_to_csv(self, filepath="schedule_report.csv"):
        """Task 3: Export flat table report for Excel using UTF-16 and Tab separator"""
        with open(filepath, 'w', newline='', encoding='utf-16') as f:
            writer = csv.writer(f, delimiter='\t')
            # Writing header
            writer.writerow(["Subject", "Type", "Teacher", "Room", "Start Time", "End Time", "Specific Attribute"])
            
            # Writing rows (flattening polymorphic data)
            for item in self.items:
                item_type = item.__class__.__name__
                specific_attr = ""
                
                if isinstance(item, Practice):
                    specific_attr = f"Dept: {item.teacher.department}"
                elif isinstance(item, Exam):
                    specific_attr = f"Assistant: {item.assistant}"
                elif isinstance(item, Lecture):
                    specific_attr = "N/A"

                writer.writerow([
                    item.subject,
                    item_type,
                    item.teacher.name,
                    item.room,
                    item.start_time.strftime("%H:%M"),
                    item.end_time.strftime("%H:%M"),
                    specific_attr
                ])
        print(f"[CSV] Report successfully exported to '{filepath}'.")


# 6. DEMONSTRATION OF THE FULL LIFECYCLE
if __name__ == "__main__":
    # Helper: Create dummy config.json if missing
    if not os.path.exists("config.json"):
        with open("config.json", "w", encoding="utf-8") as dummy_f:
            json.dump({"institution_name": "ХНУРЕ (Автогенерація)", "default_page_size": 2}, dummy_f)

    print("=== КРОК 1: Ініціалізація та завантаження конфігурації (JSON) ===")
    my_schedule = Schedule(DayOfWeek.MONDAY)
    my_schedule.load_config("config.json")
    
    print(f"\nПрацюємо в інституції: {my_schedule.institution_name}")

    print("\n=== КРОК 2: Створення та додавання початкових об'єктів ===")
    t_zhukov = Teacher("Жуков С.О.", "Кафедра САІТ")
    
    my_schedule.add_event(Lecture("Програмування", t_zhukov, "322", time(8, 30), time(10, 0)))
    my_schedule.add_event(Practice("Системний аналіз", t_zhukov, "405", time(10, 15), time(11, 45)))
    my_schedule.add_event(Exam("Штучний інтелект", t_zhukov, "322", time(12, 15), time(13, 45), "Ас. Петров І.В."))

    print("\n=== КРОК 3: Повний бекап системи (Pickle) та експорт звіту (CSV) ===")
    my_schedule.save_system_state()
    my_schedule.export_to_csv()

    print("\n=== КРОК 4: Імітація перезапуску програми (Стирання даних у пам'яті) ===")
    my_schedule.items = []
    print(f"Кількість занять у пам'яті після очищення: {len(my_schedule.items)}")

    print("\n=== КРОК 5: Відновлення системи з бінарного файлу бекапу ===")
    my_schedule.load_system_state()

    print("\n=== КРОК 6: Перевірка відновлених об'єктів через пагінацію (Генератор) ===")
    # Використовуємо ліміт сторінки, зчитаний раніше з JSON файлу
    page_size_limit = my_schedule.default_page_size
    print(f"Використовується ліміт сторінки з конфігурації JSON: {page_size_limit}")
    
    for idx, page in enumerate(my_schedule.paginate_schedule(page_size_limit), 1):
        print(f"Сторінка {idx}:")
        for item in page:
            print(f"  - {item}")
