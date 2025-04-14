## TO DO
# 1. knowledgebase dataclass
# 2. matcher dataclass
# 3. enforce uniqueness of name when creating matcher
# 4. ability to filter by type for particular LLM fields

def build_string_matcher(concepts):
    """
    Build a simple string matcher from selected knowledge bases
    This allows kbs to be selected that are appropriate for input

    Args:
        concepts:
            List of dicts that contain concepts with aliases

    Returns:
        Dict of mapping from source terms to canonical concept
    """
    matcher = {}

    for concept in concepts:
        ## uses canonical name as an alias - we don't actually want this
        # matcher[concept["name"].lower()] = concept

        for alias in concept.get("aliases", []):
            matcher[alias.lower()] = concept

    return matcher

def find_matches(text, matcher):
    """
    Find all exact matches in the given text, including nested matches.
    Indentifies where matches are nested, and where matches overlap

    Args:
        text:
            String from source data to search in
        matcher:
            Dict of mapping from source terms to canonical concept

    Returns:
        List of matches with their positions, canonical concept info, and relationship data
    """
    text_lower = text.lower()
    matches = []

    for term, concept in matcher.items():
        start_pos = 0

        # find all occurrences
        while True:
            pos = text_lower.find(term, start_pos)
            if pos == -1:
                break

            matches.append({
                "term": text[pos:pos+len(term)],
                "start": pos,
                "end": pos + len(term),
                "concept_id": concept["concept_id"],
                "code": concept["code"],
                "canonical_name": concept["name"],
                "vocabulary": concept["vocabulary"]
            })

            start_pos = pos + 1

    # sort by position, then by length
    matches.sort(key=lambda x: (x["start"], -len(x["term"])))

    # flag overlaps and nesting matches
    for i, match1 in enumerate(matches):
        match1["overlaps"] = []
        match1["nested_in"] = []
        match1["contains"] = []

        for j, match2 in enumerate(matches):
            if i == j:
                continue

            # 1. check if match1 and match2 are the same concept
            same_concept = match1["concept_id"] == match2["concept_id"]

            # 2. check for start and end conditions
            starts_inside = match2["start"] <= match1["start"] < match2["end"]
            ends_inside = match2["start"] < match1["end"] <= match2["end"]
            contains_match2 = match1["start"] <= match2["start"] and match1["end"] >= match2["end"]

            # 3. fully nested: match1 is completely inside match2
            if starts_inside and ends_inside and not same_concept:
                match1["nested_in"].append({
                    "index": j,
                    "term": match2["term"],
                    "concept_id": match2["concept_id"]
                })

            # 4. match1 completely contains match2
            elif contains_match2 and not same_concept:
                match1["contains"].append({
                    "index": j,
                    "term": match2["term"],
                    "concept_id": match2["concept_id"]
                })

            # 5. match1 and match2 overlap but neither fully contains the other
            elif (starts_inside or ends_inside) and not (starts_inside and ends_inside) and not contains_match2 and not same_concept:
                match1["overlaps"].append({
                    "index": j,
                    "term": match2["term"],
                    "concept_id": match2["concept_id"]
                })

    return matches