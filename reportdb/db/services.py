from difflib import SequenceMatcher

from db.models import Incident


def highlight_text_from_incident(text, incident):
    """Iterate through the text and highlight any values which match the incident."""
    fields = [  # Fields to search for in the text
        "cave",
        "county",
    ]

    # Create a list of values
    incident_values = []
    for field in fields:
        value = getattr(incident, field)
        if value is not None:
            value = str(value)
            if len(value) > 2:
                incident_values.append(value)

    # Add surnames of injured cavers to the list of values
    surnames = list(incident.injured_cavers.values_list("surname", flat=True))
    incident_values = surnames + incident_values

    # Iterate through the text and highlight any values which match
    # values within any incident fields
    count = -1
    for value in incident_values:
        if text.find(value) != -1:
            count += 1
            text = text.replace(value, f'<mark id="wanted-text{count}">{value}</mark>')
    return text, count


def _get_original(
    processed_text: str,
    original_text: str,
    count_words=3,
) -> (str, str):
    """Get the original text of a field.

    This function retrieves the original text of a field by finding the first three
    words and the last three words of the field and returning the text between them.
    """
    processed_words = processed_text.split()
    processed_words = [word.strip() for word in processed_words]
    processed_words = [word for word in processed_words if word]
    processed_text = " ".join(processed_words)

    original_text = original_text.split()
    original_text = [word.strip() for word in original_text]
    original_text = [word for word in original_text if word]
    original_text = " ".join(original_text)

    first_words = " ".join(processed_words[:count_words])
    last_words = " ".join(processed_words[-count_words:])

    # Get the text between the first and last three words
    start = original_text.find(first_words)
    end = original_text.find(last_words) + len(last_words)
    return processed_text, original_text[start:end]


def similarity(incident: Incident, field: str) -> float:
    """Calculate similarity between `field` and the original text of the incident."""
    field_text = getattr(incident, field)
    if not field_text or not incident.original_text:
        return 0

    text1, text2 = _get_original(field_text, incident.original_text)

    return int(
        SequenceMatcher(
            lambda x: x in ["\n", "\t"],
            text1.lower(),
            text2.lower(),
        ).ratio()
        * 100
    )
