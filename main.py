# main.py
from datetime import time
from typing import Optional
import os
import json

from core_lab6 import DayOfWeek, Teacher, Schedule, Lecture, Practice, Exam


def prompt_time(label: str) -> time:
    """Безпечне введення часу HH:MM з повторенням до коректного формату."""
    while True:
        raw = input(f"{label} (HH:MM): ").strip()
        try:
            h, m = map(int, raw.split(":"))
            if not (0 <= h < 24 and 0 <= m < 60):
                raise ValueError
            return time(h, m)
        except Exception:
            print("[Input Error] Час має бути у форматі HH:MM, напр. 08:30.")


def prompt_nonempty(label: str) -> str:
    """Безпечне введення непорожнього рядка."""
    while True:
        s = input(f"{label}: ").strip()
        if s:
            return s
        print("[Input Error] Поле не може бути порожнім.")


def choose_event_type() -> str:
    """Вибір типу події з валідацією."""
    while True:
        print("Оберіть тип події: 1 - Lecture, 2 - Practice, 3 - Exam")
        ch = input("Ваш вибір (1/2/3): ").strip()
        if ch in ("1", "2", "3"):
            return {"1": "Lecture", "2": "Practice", "3": "Exam"}[ch]
        print("[Input Error] Дозволені значення: 1, 2 або 3.")


def add_event_flow(sch: Schedule, teacher_cache: Optional[Teacher] = None) -> Teacher:
    """Діалог додавання події. Повертає останнього використаного викладача."""
    print("\n=== Додавання нової події ===")
    subject = prompt_nonempty("Предмет")
    room = prompt_nonempty("Аудиторія")
    start_t = prompt_time("Час початку")
    end_t = prompt_time("Час завершення")

    use_prev = ""
    if teacher_cache:
        use_prev = input(
            f"Використати попереднього викладача ({teacher_cache.name}, {teacher_cache.department})? [y/N]: "
        ).strip().lower()
    if use_prev == "y" and teacher_cache:
        teacher = teacher_cache
    else:
        t_name = prompt_nonempty("ПІБ викладача")
        t_dept = prompt_nonempty("Кафедра")
        teacher = Teacher(t_name, t_dept)

    kind = choose_event_type()
    if kind == "Lecture":
        ev = Lecture(subject, teacher, room, start_t, end_t)
    elif kind == "Practice":
        ev = Practice(subject, teacher, room, start_t, end_t)
    else:
        assistant = prompt_nonempty("Асистент (для Exam)")
        ev = Exam(subject, teacher, room, start_t, end_t, assistant)

    sch.add_event(ev)
    return teacher


def print_all_events(sch: Schedule):
    print("\n=== Перелік подій (відсортовано за часом) ===")
    empty = True
    for item in sch:
        print(" -", item)
        empty = False
    if empty:
        print(" (порожньо)")


def print_menu():
    print("\n================= Меню =================")
    print("1) Показати всі події")
    print("2) Додати подію")
    print("3) Зберегти стан (Pickle)")
    print("4) Завантажити стан (Pickle)")
    print("5) Експортувати звіт (CSV)")
    print("6) Фільтр за аудиторією")
    print("7) Пагінація")
    print("0) Вихід (з автозбереженням)")
    print("========================================")


def pagination_flow(sch: Schedule):
    print("\n=== Пагінація ===")
    print(f"Поточний ліміт із config.json: {sch.default_page_size}")
    raw = input("Вкажіть розмір сторінки або Enter для поточного: ").strip()
    page_size = sch.default_page_size
    if raw:
        try:
            page_size = max(1, int(raw))
        except ValueError:
            print("[Input Warning] Некоректне число — використовую значення з конфігурації.")
    for idx, page in enumerate(sch.paginate_schedule(page_size), 1):
        print(f"Сторінка {idx}:")
        for it in page:
            print(" -", it)


def room_filter_flow(sch: Schedule):
    room = prompt_nonempty("Введіть номер аудиторії для фільтру")
    print(f"\nПодії в аудиторії {room}:")
    itr = sch.filter_by_room(room)
    found = False
    for ev in itr:
        print(" -", ev)
        found = True
    if not found:
        print(" (нічого не знайдено)")


def main():
    # Ініціалізація конфігурації
    if not os.path.exists("config.json"):
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump({"institution_name": "ХНУРЕ (Автогенерація)", "default_page_size": 2}, f)

    schedule = Schedule(DayOfWeek.MONDAY)
    schedule.load_config("config.json")
    print(f"\nПрацюю для інституції: {schedule.institution_name}")

    last_teacher: Optional[Teacher] = None

    # Нескінченний цикл з fault-tolerance
    while True:
        print_menu()
        try:
            cmd = input("Оберіть пункт меню: ").strip()
            match cmd:
                case "1":
                    print_all_events(schedule)
                case "2":
                    last_teacher = add_event_flow(schedule, last_teacher)
                case "3":
                    schedule.save_system_state()
                case "4":
                    schedule.load_system_state()
                case "5":
                    schedule.export_to_csv()
                case "6":
                    room_filter_flow(schedule)
                case "7":
                    pagination_flow(schedule)
                case "0":
                    print("[System] Автозбереження перед виходом...")
                    schedule.save_system_state()
                    print("[System] Завершення роботи. Bye!")
                    break
                case _:
                    print("[Menu] Невідома команда. Оберіть пункт із переліку.")
        except Exception as e:
            print(f"[Error] Некоректне введення або помилка виконання: {e}")
            print("[Info] Повертаюся у головне меню...")

if __name__ == "__main__":
    main()
