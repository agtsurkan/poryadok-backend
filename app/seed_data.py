"""Demo data — transcribed from the frontend's initial `this.state` (the
standalone bundle), cleaned up, plus a small `history` log to exercise the
money/touch-log seam (master §8).

`demo_bundle()` returns a wire-format `StateBundle` dict, so seeding is just a
`PUT /state`-equivalent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


def _days_ago(n: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()


def demo_bundle() -> dict[str, Any]:
    return {
        "ver": 2,
        "seq": 20,
        "hapticOn": True,
        "inbox": [
            {"id": "i1", "text": "Спросить у Веб-волны про шрифты в брендбуке", "when": "вчера", "kind": "note", "link": {"type": "client", "id": "c1"}},
            {"id": "i2", "text": "Идея: раздел «до/после» в портфолио", "when": "2 дня назад", "kind": "idea", "link": {"type": "project", "id": "p4"}},
            {"id": "i3", "text": "Может, сделать рассылку раз в месяц", "when": "3 дня назад", "kind": "idea", "link": None},
        ],
        "tasks": [
            {"id": "t1", "text": "Согласовать макет главной", "tag": "project", "effort": 2, "today": True, "done": False, "link": {"type": "project", "id": "p2"}},
            {"id": "t2", "text": "Позвонить «Кофе и точка» по правкам", "tag": "client", "effort": 1, "today": True, "done": False, "link": {"type": "client", "id": "c2"}},
            {"id": "t3", "text": "Ответить «Логомашине» по смете", "tag": "mail", "effort": 1, "today": True, "done": False, "link": {"type": "project", "id": "p3"}},
            {"id": "t4", "text": "Финальные правки по «Веб-волне»", "tag": "project", "effort": 3, "today": True, "done": False, "link": {"type": "project", "id": "p1"}},
            {"id": "t5", "text": "Собрать структуру блога", "tag": "project", "effort": 2, "today": False, "done": False, "link": {"type": "project", "id": "p1a"}},
            {"id": "r1", "text": "Разобрать входящие письма", "tag": "mail", "effort": 1, "today": False, "done": False, "link": None},
            {"id": "r2", "text": "Накидать идеи для нового лендинга", "tag": "note", "effort": 2, "today": False, "done": False, "link": {"type": "project", "id": "p4"}},
        ],
        "directions": [
            {"id": "dir1", "name": "Веб-разработка", "color": "--tag-p", "note": "Сайты и лендинги"},
            {"id": "dir2", "name": "Бренд и айдентика", "color": "--tag-n", "note": "Графика и смыслы"},
        ],
        "projects": [
            {"id": "p1", "name": "Веб-волна", "kind": "Лендинг", "progress": 0.7, "status": "active", "next": "Уточнить финальные правки по главной", "dir": "dir1", "parent": None, "contact": {"name": "Игорь Левицкий", "role": "Арт-директор", "cid": "c1"}},
            {"id": "p1a", "name": "Блог Веб-волны", "kind": "Раздел сайта", "progress": 0.3, "status": "active", "next": "Собрать структуру блога", "dir": "dir1", "parent": "p1", "contact": {"name": "Игорь Левицкий", "role": "Арт-директор", "cid": "c1"}},
            {"id": "p2", "name": "Кофе и точка", "kind": "Сайт-меню", "progress": 0.4, "status": "active", "next": "Согласовать макет главной", "dir": "dir1", "parent": None, "contact": {"name": "Марина Савва", "role": "Бренд-менеджер", "cid": "c2"}},
            {"id": "p3", "name": "Логомашина", "kind": "Айдентика", "progress": 0.9, "status": "review", "next": "Ответить по смете", "dir": "dir2", "parent": None, "contact": {"name": "Антон Гребнев", "role": "Основатель", "cid": "c3"}},
            {"id": "p4", "name": "Тихий сад", "kind": "Портфолио", "progress": 0.15, "status": "idea", "next": "Накидать структуру", "dir": "dir2", "parent": None, "contact": {"name": "Елена Рощина", "role": "Художник", "cid": "c4"}},
        ],
        "clients": [
            {"id": "c1", "name": "Веб-волна", "kind": "веб-студия", "initials": "ВВ", "last": "2 недели назад", "state": "cold",
             "person": "Игорь Левицкий", "role": "Арт-директор", "company": "Веб-волна", "phone": "+7 916 240-18-05", "email": "igor@webwave.studio", "city": "Москва",
             "intentions": "Хочет обновить имидж студии и поднять конверсию лендинга. Ценит сдержанный стиль, не любит давления и спешки.",
             "portrait": "Перфекционист, мыслит образами. Решает медленно, но основательно. Лучше один продуманный вариант, чем три сырых. Не выносит спешки и давления — даёт обратную связь, когда есть тишина подумать.",
             "brief": {"request": "Пришёл с устаревшим сайтом студии и низкой конверсией заявок.", "did": "Сделали аудит, согласовали тёплую палитру и макет главной.", "next": "Собрать блог, доработать разделы, выйти на сборку."},
             "discussed": [{"when": "2 недели назад", "text": "Созвон по брендбуку: остановились на тёплой палитре."}, {"when": "месяц назад", "text": "Договорились о редизайне главной и блога."}],
             "roadmap": [{"label": "Бриф и референсы", "done": True, "shared": True}, {"label": "Макет главной", "done": True, "shared": True}, {"label": "Блог и разделы", "done": False, "shared": True}, {"label": "Сборка и запуск", "done": False, "shared": True}, {"label": "Внутр.: пересмотреть смету", "done": False, "shared": False}],
             "access": [{"service": "Figma", "detail": "редактор"}, {"service": "Домен и хостинг", "detail": "reg.ru · доступ есть"}]},
            {"id": "c2", "name": "Кофе и точка", "kind": "сеть кофеен", "initials": "КТ", "last": "вчера", "state": "warm",
             "person": "Марина Савва", "role": "Бренд-менеджер", "company": "Кофе и точка", "phone": "+7 903 117-42-90", "email": "marina@coffeedot.ru", "city": "Санкт-Петербург",
             "intentions": "Нужен сайт-меню с доставкой к осеннему сезону. Важна скорость и мобильная версия.",
             "portrait": "Энергичная, торопит процесс, любит видеть прогресс часто. Реагирует быстро, иногда меняет вводные на ходу. Ей важно чувствовать, что дело движется.",
             "brief": {"request": "Пришла за сайтом-меню с доставкой к осеннему сезону.", "did": "Собрали прототип, обсудили меню и фотосъёмку.", "next": "Утвердить макет главной, собрать каталог меню."},
             "discussed": [{"when": "вчера", "text": "Прислала правки по макету главной."}, {"when": "4 дня назад", "text": "Обсудили меню и фотографии."}],
             "roadmap": [{"label": "Прототип", "done": True, "shared": True}, {"label": "Макет главной", "done": False, "shared": True}, {"label": "Каталог меню", "done": False, "shared": True}],
             "access": [{"service": "Instagram", "detail": "для контента"}, {"service": "Google Drive", "detail": "фото и лого"}]},
            {"id": "c3", "name": "Логомашина", "kind": "агентство", "initials": "ЛМ", "last": "3 дня назад", "state": "warm",
             "person": "Антон Гребнев", "role": "Основатель", "company": "Логомашина", "phone": "+7 925 008-71-33", "email": "anton@logomachine.ru", "city": "Казань",
             "intentions": "Хочет фирменный стиль и гайдлайны. Прямой, ценит чёткие сроки и смету.",
             "portrait": "Предприниматель-прагматик. Говорит прямо, ценит конкретику и сроки. Не любит размытых формулировок — нужны цифры и даты.",
             "brief": {"request": "Пришёл за фирменным стилем и гайдлайнами.", "did": "Сделали логотип, подготовили смету.", "next": "Получить ответ по смете, собрать гайдлайны."},
             "discussed": [{"when": "3 дня назад", "text": "Ждёт ответ по смете."}],
             "roadmap": [{"label": "Логотип", "done": True, "shared": True}, {"label": "Гайдлайны", "done": False, "shared": True}],
             "access": [{"service": "Notion", "detail": "бриф"}]},
            {"id": "c4", "name": "Тихий сад", "kind": "частный клиент", "initials": "ТС", "last": "сегодня", "state": "active",
             "person": "Елена Рощина", "role": "Художник", "company": "—", "phone": "+7 911 553-26-14", "email": "elena.roshina@mail.ru", "city": "Москва",
             "intentions": "Портфолио-сайт для живописи. Минимализм, много воздуха, без лишнего.",
             "portrait": "Художник, тонко чувствует эстетику. Немногословна, доверяет вкусу. Решения принимает интуитивно — важно показать, а не рассказать.",
             "brief": {"request": "Пришла за портфолио-сайтом для живописи.", "did": "Обсудили подачу, собрали первые работы.", "next": "Согласовать структуру, начать дизайн."},
             "discussed": [{"when": "сегодня", "text": "Прислала работы для галереи."}],
             "roadmap": [{"label": "Структура", "done": False, "shared": True}, {"label": "Дизайн", "done": False, "shared": True}],
             "access": []},
        ],
        "events2": [
            {"id": "ev1", "title": "Созвон с «Кофе и точка»", "dayRel": 0, "hour": 11, "dur": 1, "color": "--tag-p", "link": {"type": "client", "id": "c2"}},
            {"id": "ev2", "title": "Встреча с Логомашиной", "dayRel": 0, "hour": 15, "dur": 1, "color": "--tag-n", "link": {"type": "client", "id": "c3"}},
            {"id": "ev3", "title": "Глубокая работа: Веб-волна", "dayRel": 1, "hour": 10, "dur": 2, "color": "--tag-p", "link": {"type": "project", "id": "p1"}},
        ],
        "events": [
            {"id": "e1", "kind": "done", "text": "Закрыта «Отправить КП Логомашине»", "when": "вчера, 18:40"},
            {"id": "e2", "kind": "note", "text": "Мысль: попробовать новый раздел в портфолио", "when": "вчера, 16:10"},
            {"id": "e3", "kind": "add", "text": "Добавлена «Финальные правки по Веб-волне»", "when": "вчера, 11:05"},
            {"id": "e4", "kind": "client", "text": "Письмо клиенту «Кофе и точка»", "when": "2 дня назад"},
        ],
        "quickLinks": [
            {"id": "q1", "type": "project", "label": "Веб-волна"},
            {"id": "q2", "type": "note", "label": "Идеи лендинга"},
        ],
        "services": [
            {"id": "sv_mail", "name": "Почта", "hint": "igor@… и ещё 2 ящика", "connected": False},
            {"id": "sv_tg", "name": "Telegram", "hint": "личка и рабочие чаты", "connected": False},
            {"id": "sv_cal", "name": "Календарь", "hint": "встречи и созвоны", "connected": False},
            {"id": "sv_figma", "name": "Figma", "hint": "макеты проектов", "connected": False},
            {"id": "sv_notion", "name": "Notion", "hint": "брифы и база", "connected": False},
            {"id": "sv_drive", "name": "Google Drive", "hint": "файлы и материалы", "connected": False},
        ],
        "links": [
            {"id": "l1", "a": "project:p1", "b": "client:c1"},
            {"id": "l2", "a": "client:c2", "b": "thought:i1"},
        ],
        # History / money log — not in the current frontend; laid in for P1.
        "history": [
            {"id": "h1", "kind": "order", "subject": "client:c1", "amount": 180000, "note": "Редизайн сайта студии", "occurred_at": _days_ago(40)},
            {"id": "h2", "kind": "invoice", "subject": "client:c1", "amount": 90000, "note": "Предоплата 50%", "occurred_at": _days_ago(38)},
            {"id": "h3", "kind": "touch", "subject": "client:c1", "amount": None, "note": "Созвон по брендбуку", "occurred_at": _days_ago(14)},
            {"id": "h4", "kind": "order", "subject": "client:c2", "amount": 140000, "note": "Сайт-меню с доставкой", "occurred_at": _days_ago(6)},
            {"id": "h5", "kind": "session", "subject": "client:c4", "amount": 15000, "note": "Консультация по подаче", "occurred_at": _days_ago(1)},
        ],
    }
