def okr_status(okr: dict, measurements: dict, mvp_stories: list) -> dict:
    """
    Рахує прогрес ключових результатів, знаходить розриви у зв'язках,
    невиміряні KR, діяльність замість результатів та сироти-історії.
    """
    key_results = okr.get("key_results")
    if not key_results:
        raise ValueError("Немає ключових результатів")
    
    initiatives = okr.get("initiatives", {})
    kr_ids = set()
    
    # Перевірки по черзі
    for kr in key_results:
        kid = kr["id"]
        if kid in kr_ids:
            # Дубльований ID KR (якщо потрібно, але основне — базові правила)
            pass
        kr_ids.add(kid)
        
        baseline = kr["baseline"]
        target = kr["target"]
        if baseline == target:
            raise ValueError(f"Ціль збігається з початком: {kid}")
            
    for kr_id in initiatives:
        if kr_id not in kr_ids:
            raise ValueError(f"Ініціатива для невідомого KR: {kr_id}")

    # 1. Progress для кожного KR
    progress = {}
    for kr in key_results:
        kid = kr["id"]
        baseline = kr["baseline"]
        target = kr["target"]
        metric = kr["metric"]
        
        if metric not in measurements:
            progress[kid] = None
        else:
            current = measurements[metric]
            # Розрахунок з урахуванням того, що показник може зменшуватися
            # (current - baseline) * 100 // (target - baseline)
            num = (current - baseline) * 100
            den = target - baseline
            val = num // den
            # Обмеження діапазоном від 0 до 100
            val = max(0, min(100, val))
            progress[kid] = val

    # 2. Score та level
    measured_values = [v for v in progress.values() if v is not None]
    if not measured_values:
        score = None
        level = "немає даних"
    else:
        score = sum(measured_values) // len(measured_values)
        if score >= 70:
            level = "зелений"
        elif score >= 40:
            level = "жовтий"
        else:
            level = "червоний"

    # 3. Додаткові списки
    unmeasured = [kr["id"] for kr in key_results if progress[kr["id"]] is None]
    
    activity_fragments = ["консульт", "допомаг", "аналіз", "участь", "запуст", "провед", "провест"]
    activity_kr = []
    for kr in key_results:
        text_lower = kr["text"].lower()
        if any(frag in text_lower for frag in activity_fragments):
            activity_kr.append(kr["id"])

    unlinked_kr = [kr["id"] for kr in key_results if not initiatives.get(kr["id"])]

    # orphan_stories: історії з mvp_stories, яких немає в жодній ініціативі
    all_init_stories = set()
    for s_list in initiatives.values():
        for s in s_list:
            all_init_stories.add(s)
            
    orphan_stories = [s for s in mvp_stories if s not in all_init_stories]

    # unknown_stories: історії з ініціатив, яких немає в mvp_stories (без повторів, у порядку першої появи)
    unknown_stories_seen = []
    for s_list in initiatives.values():
        for s in s_list:
            if s not in mvp_stories and s not in unknown_stories_seen:
                unknown_stories_seen.append(s)
    unknown_stories = unknown_stories_seen

    return {
        "progress": progress,
        "score": score,
        "level": level,
        "unmeasured": unmeasured,
        "activity_kr": activity_kr,
        "unlinked_kr": unlinked_kr,
        "orphan_stories": orphan_stories,
        "unknown_stories": unknown_stories
    }