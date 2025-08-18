import json

def _topics_prompt(transcript: str) -> str:
    return (
        "You are an assistant that returns strict JSON only. "
        "Extract a list of high-quality learning topics with subtopics from the transcript. "
        "Do not create topics for the course description, instructor, or any other non-learning content. Only create topics for the learning content that is important to learn."
        "Return ONLY valid JSON matching this schema: {\n  \"topics\": [ { \n    \"title\": string,\n    \"subtopics\": [ { \n      \"title\": string, \n      \"summary\": string, \n      \"key_points\": string[] \n    } ] \n  } ] \n}\n"
        "Transcript:\n" + transcript
    )


def _flashcards_prompt(topics_json: dict, transcript: str) -> str:
    return (
        "You are an assistant that returns strict JSON. "
        "Create Anki flashcards for the given topics and subtopics. Create as many flashcards as possible for each topic and subtopic. Limit the number of flashcards to 50 for each topic."
        "Do not create flashcards for the course description, instructor, or any other non-learning content. Only create flashcards for the learning content that is important to learn."
        "Create some flashcards for the examples, exercises, questions, etc. that is not the main learning content. These are important to learn and review, but not the main learning content."
        "Card types allowed: qa, single_choice, multiple_choice, matching. "
        "For choice questions, include options and the correct index(es). "
        "Return ONLY valid JSON matching this schema: "
        "{\n  \"decks\": [\n    {\n      \"topic\": string,\n      \"subtopic\": string?,\n      \"cards\": [\n        { \n          \"type\": \"qa\", \n          \"question\": string, \n          \"answer\": string, \n          \"explanation\": string? \n        } | { \n          \"type\": \"single_choice\", \n          \"question\": string, \n          \"options\": string[], \n          \"correct_option\": number, \n          \"explanation\": string? \n        } | { \n          \"type\": \"multiple_choice\", \n          \"question\": string, \n          \"options\": string[], \n          \"correct_options\": number[], \n          \"explanation\": string? \n        } | { \n          \"type\": \"matching\", \n          \"question\": string?, \n          \"pairs\": [ { \"left\": string, \"right\": string } ] \n        }\n      ]\n    }\n  ]\n}"
        f"\nTopics JSON:\n{json.dumps(topics_json, ensure_ascii=False)}"
        f"\nTranscript:\n{transcript}"
    )