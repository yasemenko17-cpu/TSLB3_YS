"""Перевірник артефактів студента (частина Б): продуктовий концепт, прототип, план MVP, тест із користувачами, план показу.

Це готовий інструмент викладача: його не потрібно змінювати. Він читає теку artifacts/
(concept.json, board.json, board_export.json, tests.json, demo.md, prototype/) і повертає список зауважень;
порожній список означає, що форма й узгодженість артефактів прийнятні. Зміст оцінює викладач на показі.
"""
import json
import re
from collections import deque
from datetime import date, timedelta
from html.parser import HTMLParser
from pathlib import Path

PLACEHOLDER = "<ЗАПОВНІТЬ"
SCALE = (1, 2, 3, 5, 8)
SOLUTION_WORDS = ("застосунок", "додаток", "систем", "кнопк", "баз даних", "сайт", "платформ", "сервіс", "програм")
ACTIVITY = ("консульт", "допомаг", "аналіз", "участь", "запуст", "провед", "провест")
VAGUE_LINKS = {"тут", "натисніть тут", "детальніше", "докладніше", "ось", "посилання", "більше", "читати далі"}
JOB = re.compile(r"^Коли .+, я хочу .+, щоб .+$")
STORY_ID = re.compile(r"^US-\d{2}$")
ITER = re.compile(r"^Ітерація (\d+)$")
DEMO_HEADINGS = ("Проблема і сегмент", "Ціннісна пропозиція", "Показ прототипу", "Результати тесту", "Ризик і наступний крок")
VOID = {"input", "br", "img", "hr", "meta", "link"}
SKIP_TYPES = {"hidden", "submit", "button", "reset", "image"}


# ------------------------------------------------------------------ читання
def load(root):
    """Читає артефакти. Повертає (дані, помилки читання)."""
    root = Path(root)
    errors, data = [], {"raw": ""}
    raw = []
    for name, key in (("concept.json", "concept"), ("board.json", "board"), ("board_export.json", "export"),
                      ("tests.json", "tests")):
        path = root / name
        data[key] = None
        if not path.exists():
            errors.append(f"немає файлу {name}")
            continue
        text = path.read_text(encoding="utf-8")
        raw.append(text)
        try:
            data[key] = json.loads(text)
        except ValueError as exc:
            errors.append(f"{name} не є коректним JSON: {exc}")
    demo = root / "demo.md"
    data["demo"] = None
    if demo.exists():
        data["demo"] = demo.read_text(encoding="utf-8")
        raw.append(data["demo"])
    else:
        errors.append("немає файлу demo.md")
    proto = root / "prototype"
    data["html"], data["screens_json"], data["penpot_files"] = None, None, []
    if (proto / "index.html").exists():
        data["html"] = (proto / "index.html").read_text(encoding="utf-8")
        raw.append(data["html"])
    if (proto / "screens.json").exists():
        try:
            data["screens_json"] = json.loads((proto / "screens.json").read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"prototype/screens.json не є коректним JSON: {exc}")
    if (proto / "penpot").is_dir():
        data["penpot_files"] = [p.name for p in sorted((proto / "penpot").iterdir()) if p.is_file()]
    if data["html"] is None and data["screens_json"] is None:
        errors.append("немає прототипу: потрібен prototype/index.html або prototype/screens.json (з експортом Penpot)")
    data["raw"] = "\n".join(raw)
    return data, errors


# ------------------------------------------------------------------ граф екранів
class _Screens(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.screens, self.edges, self.ends = [], [], [], set()

    def _cur(self):
        for _, sid in reversed(self.stack):
            if sid:
                return sid
        return None

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        sid = None
        if "data-screen" in a:
            sid = a.get("id", "").strip()
            if sid and sid not in self.screens:
                self.screens.append(sid)
            if "data-end" in a:
                self.ends.add(sid)
        cur = sid or self._cur()
        if cur:
            target = None
            if tag == "a" and a.get("href", "").startswith("#") and len(a["href"]) > 1:
                target = a["href"][1:]
            elif a.get("data-goto"):
                target = a["data-goto"]
            if target and (cur, target) not in self.edges:
                self.edges.append((cur, target))
        if tag not in VOID:
            self.stack.append((tag, sid))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break


def graph(data):
    """Повертає (екрани {id: [цілі]}, початковий, кінцеві) з HTML або screens.json."""
    if data["html"] is not None:
        p = _Screens()
        p.feed(data["html"])
        screens = {s: [] for s in p.screens}
        for a, b in p.edges:
            screens[a].append(b)
        return screens, (p.screens[0] if p.screens else None), sorted(e for e in p.ends if e)
    sj = data["screens_json"] or {}
    screens = {k: list(v) for k, v in (sj.get("screens") or {}).items()}
    return screens, sj.get("start"), list(sj.get("end") or [])


def bfs(screens, a, b):
    if a == b:
        return [a]
    parent, queue = {a: None}, deque([a])
    while queue:
        cur = queue.popleft()
        for n in screens[cur]:
            if n in screens and n not in parent:
                parent[n] = cur
                if n == b:
                    out = [b]
                    while parent[out[-1]] is not None:
                        out.append(parent[out[-1]])
                    return out[::-1]
                queue.append(n)
    return None


# ------------------------------------------------------------------ доступність
class _A11y(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.counts, self.items, self.label_for, self.ids = [], {}, [], set(), set()
        self.lang, self.has_html = "", False

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        self.counts[tag] = self.counts.get(tag, 0) + 1
        rec = {"tag": tag, "a": a, "label": a.get("id", "").strip() or f"{tag}{self.counts[tag]}", "text": [],
               "in_label": any(r["tag"] == "label" for r in self.stack), "dup": False}
        if a.get("id", "").strip():
            rec["dup"] = a["id"].strip() in self.ids
            self.ids.add(a["id"].strip())
        if tag == "html":
            self.has_html, self.lang = True, a.get("lang", "").strip()
        if tag == "label" and a.get("for"):
            self.label_for.add(a["for"].strip())
        self.items.append(rec)
        if tag not in VOID:
            self.stack.append(rec)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i]["tag"] == tag:
                del self.stack[i:]
                break

    def handle_data(self, d):
        for r in self.stack:
            r["text"].append(d)


def a11y_issues(html):
    clean = lambda t: re.sub(r"\s+", " ", t).strip()
    p = _A11y()
    p.feed(html)
    out = []
    if not p.has_html or not p.lang:
        out.append("html без атрибута lang")
    titles = [r for r in p.items if r["tag"] == "title"]
    if not titles or not clean("".join(titles[0]["text"])):
        out.append("немає непорожнього title")
    h1 = sum(1 for r in p.items if r["tag"] == "h1")
    if h1 != 1:
        out.append(f"заголовків h1 має бути один, знайдено {h1}")
    prev = None
    for r in p.items:
        tag, a, lab = r["tag"], r["a"], r["label"]
        name = clean(a.get("aria-label", "")) or clean("".join(r["text"]))
        if r["dup"]:
            out.append(f"повторений id {a['id'].strip()}")
        if tag == "img" and "alt" not in a:
            out.append(f"img без alt: {lab}")
        elif tag == "a" and "href" in a:
            if not name:
                out.append(f"посилання без назви: {lab}")
            elif name.lower() in VAGUE_LINKS:
                out.append(f"нечітка назва посилання «{name}»: {lab}")
        elif tag == "button" and not name:
            out.append(f"кнопка без назви: {lab}")
        elif tag in ("input", "select", "textarea"):
            if tag == "input" and (a.get("type") or "text").strip().lower() in SKIP_TYPES:
                continue
            ok = bool(clean(a.get("aria-label", ""))) or r["in_label"] or \
                (a.get("id", "").strip() != "" and a["id"].strip() in p.label_for)
            if not ok:
                out.append(f"поле без підпису: {lab}")
        elif re.fullmatch(r"h[1-6]", tag):
            lvl = int(tag[1])
            if prev is not None and lvl > prev + 1:
                out.append(f"пропущено рівень заголовка: {lab}")
            prev = lvl
    return out


# ------------------------------------------------------------------ допоміжне
def _d(text):
    try:
        return date.fromisoformat(text)
    except (TypeError, ValueError):
        return None


def mvp_items(data):
    items = (data["board"] or {}).get("items") or []
    return [i for i in items if ITER.match(str(i.get("iteration", "")))]


def top_assumption(assumptions):
    ok = [a for a in assumptions if all(isinstance(a.get(k), int) for k in ("impact", "uncertainty", "cost"))]
    if not ok:
        return None
    return sorted(ok, key=lambda a: (-a["impact"] * a["uncertainty"], -a["uncertainty"], a["cost"], a["id"]))[0]["id"]


def chain_report(c):
    segs, probs = c.get("segments") or {}, c.get("problems") or {}
    props, scs = c.get("propositions") or {}, c.get("scenarios") or {}
    errs = []
    for pid, p in probs.items():
        valid = [s for s in p.get("segments", []) if s in segs]
        if not valid:
            errs.append(f"проблема {pid} не має існуючого сегмента")
        elif not any(pid in v.get("solves", []) for v in props.values()):
            errs.append(f"проблему {pid} не розв'язує жодна пропозиція")
        elif not any(pid in props[k["proposition"]].get("solves", []) and k.get("segment") in valid
                     for k in scs.values() if k.get("proposition") in props):
            errs.append(f"для проблеми {pid} немає сценарію її сегмента через пропозицію, що її розв'язує")
    for vid, v in props.items():
        for p in v.get("solves", []):
            if p not in probs:
                errs.append(f"пропозиція {vid} розв'язує невідому проблему {p}")
        if not any(p in probs for p in v.get("solves", [])):
            errs.append(f"пропозиція {vid} нічого не розв'язує")
    for kid, k in scs.items():
        if k.get("proposition") not in props:
            errs.append(f"сценарій {kid} посилається на невідому пропозицію {k.get('proposition')}")
        if k.get("segment") not in segs:
            errs.append(f"сценарій {kid} посилається на невідомий сегмент {k.get('segment')}")
    return errs


# ------------------------------------------------------------------ правила
def rule_no_placeholders(data):
    return ["незаповнені місця «<ЗАПОВНІТЬ …>» у файлах"] if PLACEHOLDER in data["raw"] else []


def rule_concept_fields(data):
    c, errs = data["concept"], []
    for k in ("name", "one_liner", "segments", "problems", "jobs", "propositions", "scenarios", "okr", "assumptions",
              "riskiest", "risks", "mvp", "prototype"):
        if k not in c:
            errs.append(f"concept.json: немає поля {k}")
    if errs:
        return errs
    m = c["mvp"]
    if not isinstance(m.get("capacity"), int) or m["capacity"] <= 0:
        errs.append("mvp.capacity має бути додатним цілим")
    if not isinstance(m.get("iteration_days"), int) or m["iteration_days"] <= 0:
        errs.append("mvp.iteration_days має бути додатним цілим")
    for k in ("start", "deadline"):
        if _d(m.get(k)) is None:
            errs.append(f"mvp.{k} має бути датою РРРР-ММ-ДД")
    if c["prototype"].get("kind") not in ("html", "penpot"):
        errs.append("prototype.kind має бути html або penpot")
    return errs


def rule_chain(data):
    c = data["concept"]
    errs = chain_report(c)
    if len(c.get("segments") or {}) < 1 or len(c.get("problems") or {}) < 2:
        errs.append("потрібні щонайменше один сегмент і дві проблеми")
    if len(c.get("scenarios") or {}) < 3:
        errs.append("ключових сценаріїв має бути щонайменше три")
    return errs


def rule_problems_not_solutions(data):
    errs = []
    for pid, p in (data["concept"].get("problems") or {}).items():
        text = str(p.get("text", "")).lower()
        hit = [w for w in SOLUTION_WORDS if w in text]
        if hit:
            errs.append(f"проблема {pid} схожа на рішення (слово «{hit[0]}»): опишіть, у кого, коли і що втрачає")
        if not re.search(r"\d", text):
            errs.append(f"проблема {pid} без числа: додайте частоту, час або втрати")
        if not str(p.get("evidence", "")).strip():
            errs.append(f"проблема {pid} без поля evidence (звідки ви це знаєте)")
    return errs


def rule_jobs(data):
    c, errs = data["concept"], []
    jobs = c.get("jobs") or []
    if len(jobs) < 2:
        errs.append("потрібні щонайменше дві job stories")
    for j in jobs:
        if not JOB.match(str(j.get("story", "")).strip()):
            errs.append(f"job {j.get('id')}: історія не за шаблоном «Коли …, я хочу …, щоб …»")
        if j.get("problem") not in (c.get("problems") or {}):
            errs.append(f"job {j.get('id')}: невідома проблема {j.get('problem')}")
    return errs


def rule_story_map(data):
    b, errs = data["board"], []
    items = b.get("items") or []
    steps = b.get("steps") or []
    if len(steps) < 3:
        errs.append("board.json: кроків карти має бути щонайменше 3")
    if len(items) < 8:
        errs.append(f"board.json: історій {len(items)}, потрібно щонайменше 8")
    ids = [i.get("id") for i in items]
    for i in items:
        iid = i.get("id")
        if not STORY_ID.match(str(iid)):
            errs.append(f"{iid}: ідентифікатор має вигляд US-01")
        if ids.count(iid) > 1:
            errs.append(f"{iid}: ідентифікатор повторюється")
        if i.get("step") not in steps:
            errs.append(f"{iid}: невідомий крок {i.get('step')}")
        if i.get("size") not in SCALE:
            errs.append(f"{iid}: розмір {i.get('size')} поза шкалою {SCALE}")
        if not isinstance(i.get("value"), int) or not 1 <= i["value"] <= 10:
            errs.append(f"{iid}: цінність має бути цілим від 1 до 10")
        for d in i.get("depends_on", []):
            if d not in ids:
                errs.append(f"{iid}: невідома залежність {d}")
        if not str(i.get("title", "")).strip():
            errs.append(f"{iid}: порожня назва")
    state = {}
    by = {i.get("id"): i for i in items}

    def visit(x):
        if state.get(x) == 1:
            return True
        if state.get(x) == 2:
            return False
        state[x] = 1
        for d in by.get(x, {}).get("depends_on", []):
            if d in by and visit(d):
                return True
        state[x] = 2
        return False

    if any(visit(x) for x in by):
        errs.append("залежності історій утворюють цикл")
    return errs


def rule_mvp_slice(data):
    b, errs = data["board"], []
    mvp = mvp_items(data)
    ids = {i["id"] for i in mvp}
    for st in b.get("steps") or []:
        if not any(i.get("step") == st for i in mvp):
            errs.append(f"у MVP немає історії для кроку «{st}» (зріз має бути наскрізним)")
    for i in mvp:
        for d in i.get("depends_on", []):
            if d not in ids:
                errs.append(f"{i['id']} у MVP, а залежність {d} ні")
    if len(mvp) < 5:
        errs.append(f"MVP містить {len(mvp)} історій, потрібно щонайменше 5")
    for i in b.get("items") or []:
        if not ITER.match(str(i.get("iteration", ""))) and i.get("iteration") != "Пізніше":
            errs.append(f"{i.get('id')}: iteration має бути «Ітерація N» або «Пізніше»")
    return errs


def rule_plan(data):
    c, errs = data["concept"], []
    m = c.get("mvp") or {}
    mvp = mvp_items(data)
    cap, days = m.get("capacity"), m.get("iteration_days")
    start, deadline = _d(m.get("start")), _d(m.get("deadline"))
    if not mvp or not isinstance(cap, int) or not isinstance(days, int) or start is None or deadline is None or cap <= 0 or days <= 0:
        return errs
    nums = sorted({int(ITER.match(i["iteration"]).group(1)) for i in mvp})
    if nums != list(range(1, nums[-1] + 1)):
        errs.append(f"номери ітерацій мають іти підряд від 1, знайдено {nums}")
    by = {i["id"]: int(ITER.match(i["iteration"]).group(1)) for i in mvp}
    for n in nums:
        load = sum(i["size"] for i in mvp if by[i["id"]] == n and isinstance(i.get("size"), int))
        if load > cap:
            errs.append(f"Ітерація {n}: навантаження {load} перевищує місткість {cap}")
    for i in mvp:
        for d in i.get("depends_on", []):
            if d in by and by[d] >= by[i["id"]]:
                errs.append(f"{i['id']} (ітерація {by[i['id']]}) не може бути не пізніше за залежність {d} (ітерація {by[d]})")
    finish = start + timedelta(days=nums[-1] * days - 1)
    if finish > deadline:
        errs.append(f"план закінчується {finish.isoformat()}, а показ призначено на {deadline.isoformat()}")
    return errs


def rule_board_export(data):
    exp, errs = data["export"], []
    items = exp.get("items") if isinstance(exp, dict) else exp
    if not isinstance(items, list) or not items:
        return ["board_export.json: очікується список items (результат gh project item-list --format json)"]
    titles = []
    for it in items:
        t = it.get("title") or (it.get("content") or {}).get("title") or ""
        titles.append(str(t))
    for i in mvp_items(data):
        if not any(t.startswith(i["id"]) for t in titles):
            errs.append(f"на дошці (board_export.json) немає картки, назва якої починається з {i['id']}")
    if not data["board"].get("project_url", "").startswith("https://github.com/"):
        errs.append("board.json: project_url має починатися з https://github.com/")
    return errs


def rule_prototype_graph(data):
    errs = []
    screens, start, ends = graph(data)
    if data["html"] is None:
        if not data["penpot_files"]:
            errs.append("для Penpot покладіть експорт екранів (png, svg або pdf) у prototype/penpot/")
        if data["concept"].get("prototype", {}).get("kind") == "html":
            errs.append("concept.prototype.kind = html, але prototype/index.html немає")
    if len(screens) < 4:
        errs.append(f"екранів {len(screens)}, потрібно щонайменше 4")
        return errs
    if start not in screens:
        errs.append(f"початковий екран {start!r} не існує")
        return errs
    for e in ends:
        if e not in screens:
            errs.append(f"кінцевий екран {e} не існує")
    for a, targets in screens.items():
        for t in targets:
            if t not in screens:
                errs.append(f"екран {a}: перехід на неіснуючий екран {t}")
    depth, queue = {start: 0}, deque([start])
    while queue:
        cur = queue.popleft()
        for t in screens[cur]:
            if t in screens and t not in depth:
                depth[t] = depth[cur] + 1
                queue.append(t)
    for s in screens:
        if s not in depth:
            errs.append(f"екран {s} недосяжний від {start}")
    can = set(e for e in ends if e in screens)
    changed = True
    while changed:
        changed = False
        for s, ts in screens.items():
            if s not in can and any(t in can for t in ts):
                can.add(s)
                changed = True
    for s in depth:
        valid = [t for t in screens[s] if t in screens and t != s]
        if s not in ends and not valid:
            errs.append(f"екран {s} — глухий кут (немає переходів і не позначений як кінцевий)")
        elif s not in ends and s not in can:
            errs.append(f"з екрана {s} не можна дійти до жодного кінцевого екрана")
    if not ends:
        errs.append("не позначено жодного кінцевого екрана (data-end або поле end у screens.json)")
    return errs


def rule_scenario_paths(data):
    errs = []
    screens, _, _ = graph(data)
    for kid, k in (data["concept"].get("scenarios") or {}).items():
        sp = k.get("screens") or {}
        pts = [sp.get("start"), *sp.get("via", []), sp.get("goal")]
        if not isinstance(sp.get("max_steps"), int) or sp["max_steps"] < 0:
            errs.append(f"сценарій {kid}: screens.max_steps має бути цілим ≥ 0")
            continue
        if any(p not in screens for p in pts):
            errs.append(f"сценарій {kid}: у шляху є екран, якого немає в прототипі: {pts}")
            continue
        full = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            leg = bfs(screens, a, b)
            if leg is None:
                full = None
                break
            full += leg[1:]
        if full is None:
            errs.append(f"сценарій {kid}: шлях {pts} у прототипі недосяжний")
        elif len(full) - 1 > sp["max_steps"]:
            errs.append(f"сценарій {kid}: потрібно {len(full) - 1} переходів, дозволено {sp['max_steps']}")
    return errs


def rule_html_a11y(data):
    if data["html"] is None:
        return []
    return a11y_issues(data["html"])


def rule_okr(data):
    c, errs = data["concept"], []
    okr = c.get("okr") or {}
    krs = okr.get("key_results") or []
    if not str(okr.get("objective", "")).strip():
        errs.append("okr.objective порожня")
    if not 2 <= len(krs) <= 5:
        errs.append(f"ключових результатів {len(krs)}, потрібно від 2 до 5")
    mvp_ids = {i["id"] for i in mvp_items(data)}
    inits = okr.get("initiatives") or {}
    for k in krs:
        kid = k.get("id")
        if not isinstance(k.get("baseline"), (int, float)) or not isinstance(k.get("target"), (int, float)) or k["baseline"] == k["target"]:
            errs.append(f"{kid}: потрібні числові baseline і target, що не збігаються")
        if any(w in str(k.get("text", "")).lower() for w in ACTIVITY):
            errs.append(f"{kid}: це діяльність, а не результат (формулюйте зміну показника)")
        if not str(k.get("metric", "")).strip():
            errs.append(f"{kid}: немає metric")
        if not inits.get(kid):
            errs.append(f"{kid}: немає жодної історії MVP, що його рухає")
    for kid, lst in inits.items():
        if kid not in {k.get("id") for k in krs}:
            errs.append(f"initiatives: невідомий ключовий результат {kid}")
        for s in lst:
            if s not in mvp_ids:
                errs.append(f"initiatives {kid}: {s} не входить до MVP")
    linked = {s for lst in inits.values() for s in lst}
    if mvp_ids and 100 * len(mvp_ids & linked) // len(mvp_ids) < 60:
        errs.append("до ключових результатів прив'язано менше 60 % історій MVP")
    return errs


def rule_assumptions(data):
    c, errs = data["concept"], []
    asm = c.get("assumptions") or []
    if len(asm) < 4:
        errs.append(f"припущень {len(asm)}, потрібно щонайменше 4")
    for a in asm:
        for f in ("impact", "uncertainty"):
            if not isinstance(a.get(f), int) or isinstance(a.get(f), bool) or not 1 <= a[f] <= 5:
                errs.append(f"{a.get('id')}: {f} має бути цілим 1..5")
        if not isinstance(a.get("cost"), int) or a["cost"] <= 0:
            errs.append(f"{a.get('id')}: cost (днів на перевірку) має бути додатним")
    top = top_assumption(asm)
    if top and c.get("riskiest") != top:
        errs.append(f"найризикованіше припущення за ваги вплив × невизначеність — {top}, а у riskiest вказано {c.get('riskiest')}")
    for a in asm:
        if a.get("id") == top and not str(a.get("experiment", "")).strip():
            errs.append(f"для найризикованішого припущення {top} не описано експеримент (поле experiment)")
    risks = c.get("risks") or []
    if len(risks) < 3:
        errs.append(f"ризиків проєкту {len(risks)}, потрібно щонайменше 3")
    for r in risks:
        if not isinstance(r.get("p"), int) or not 0 <= r["p"] <= 100 or not isinstance(r.get("loss"), int) or r["loss"] < 0:
            errs.append(f"{r.get('id')}: p — ціле 0..100, loss — ціле ≥ 0 (днів затримки)")
        elif r["p"] * r["loss"] >= 100 and not str(r.get("mitigation", "")).strip():
            errs.append(f"{r.get('id')}: ризик із очікуваною затримкою від одного дня без заходів (mitigation)")
    return errs


def rule_user_tests(data):
    t, c, errs = data["tests"], data["concept"], []
    sessions = t.get("sessions") or []
    users = {s.get("user") for s in sessions if s.get("done") is True}
    if len(users) < 3:
        errs.append(f"завершених сесій з різними користувачами {len(users)}, потрібно щонайменше 3")
    for s in sessions:
        if s.get("scenario") not in (c.get("scenarios") or {}):
            errs.append(f"сесія {s.get('user')}: невідомий сценарій {s.get('scenario')}")
    finds = t.get("findings") or []
    if not finds:
        errs.append("немає жодної знахідки: після трьох користувачів так не буває, запишіть спостереження")
    for f in finds:
        if f.get("severity") not in (1, 2, 3, 4):
            errs.append(f"знахідка {f.get('id')}: severity має бути 1..4")
        if f.get("status") not in ("відкрито", "заплановано", "виправлено"):
            errs.append(f"знахідка {f.get('id')}: status має бути відкрито, заплановано або виправлено")
        if f.get("severity") in (3, 4) and f.get("status") == "відкрито":
            errs.append(f"знахідка {f.get('id')}: серйозна (≥ 3) і досі відкрита")
    if not t.get("conclusions"):
        errs.append("tests.json: немає висновків (conclusions)")
    return errs


def rule_demo(data):
    md, errs = data["demo"], []
    heads = [h.strip() for h in re.findall(r"^##\s+(.+)$", md, re.M)]
    for h in DEMO_HEADINGS:
        if h not in heads:
            errs.append(f"demo.md: немає розділу «{h}»")
    words = len(re.findall(r"[\w'’-]+", md))
    if not 120 <= words <= 700:
        errs.append(f"demo.md: {words} слів, очікується від 120 до 700 (показ 3-7 хвилин)")
    return errs


def facts(data):
    """Факти для чекліста готовності; рахуються з артефактів тими самими правилами."""
    c = data["concept"]
    return {"chain": not rule_chain(data) and not chain_report(c), "paths": not rule_scenario_paths(data),
            "graph": not rule_prototype_graph(data), "a11y": not rule_html_a11y(data), "plan": not rule_plan(data),
            "okr": not rule_okr(data), "assumptions": not rule_assumptions(data), "tests": not rule_user_tests(data)}


def rule_readiness(data):
    f = facts(data)
    names = {"chain": "узгодженість концепту", "paths": "шляхи сценаріїв", "graph": "навігація прототипу",
             "a11y": "доступність HTML", "plan": "план MVP", "okr": "метрики успіху", "assumptions": "ризики",
             "tests": "тест із користувачами"}
    bad = [names[k] for k, v in f.items() if not v]
    return [f"перед показом залишилося виправити: {', '.join(bad)}"] if bad else []


RULES = [rule_no_placeholders, rule_concept_fields, rule_chain, rule_problems_not_solutions, rule_jobs, rule_story_map,
         rule_mvp_slice, rule_plan, rule_board_export, rule_prototype_graph, rule_scenario_paths, rule_html_a11y,
         rule_okr, rule_assumptions, rule_user_tests, rule_demo, rule_readiness]


def check_all(root):
    """Повертає список зауважень до артефактів у теці root."""
    data, errors = load(root)
    if errors:
        return errors
    out = []
    for rule in RULES:
        try:
            out.extend(rule(data))
        except (AttributeError, KeyError, TypeError, ValueError, IndexError) as exc:
            out.append(f"{rule.__name__}: структура файлу порушена ({type(exc).__name__}: {exc})")
    return out


if __name__ == "__main__":
    import sys
    problems = check_all(sys.argv[1] if len(sys.argv) > 1 else "artifacts")
    for p in problems:
        print("-", p)
    print("Зауважень:", len(problems))
    sys.exit(1 if problems else 0)
