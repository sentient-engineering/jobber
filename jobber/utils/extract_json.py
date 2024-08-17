import json
from typing import Any, Dict

from jobber.utils.logger import logger


def extract_json(message: str) -> Dict[str, Any]:
    """
    Parse the response from the browser agent and return the response as a dictionary.
    """
    json_response = {}
    # Remove Markdown code block delimiters if present
    message = message.strip()
    if message.startswith("```"):
        message = message.split("\n", 1)[1]  # Remove the first line
    if message.endswith("```"):
        message = message.rsplit("\n", 1)[0]  # Remove the last line

    # Remove any leading "json" tag
    if message.lstrip().startswith("json"):
        message = message.lstrip()[4:].lstrip()

    try:
        return json.loads(message)
    except json.JSONDecodeError as e:
        logger.warn(
            f"LLM response was not properly formed JSON. Error: {e}. "
            f'LLM response: "{message}"'
        )
        message = message.replace("\\n", "\n")
        message = message.replace("\n", " ")  # type: ignore
        if "plan" in message and "next_step" in message:
            start = message.index("plan") + len("plan")
            end = message.index("next_step")
            json_response["plan"] = message[start:end].replace('"', "").strip()
        if "next_step" in message and "terminate" in message:
            start = message.index("next_step") + len("next_step")
            end = message.index("terminate")
            json_response["next_step"] = message[start:end].replace('"', "").strip()
        if "terminate" in message and "final_response" in message:
            start = message.index("terminate") + len("terminate")
            end = message.index("final_response")
            matched_string = message[start:end].replace('"', "").strip()
            if "yes" in matched_string:
                json_response["terminate"] = "yes"
            else:
                json_response["terminate"] = "no"

            start = message.index("final_response") + len("final_response")
            end = len(message) - 1
            json_response["final_response"] = (
                message[start:end].replace('"', "").strip()
            )

        elif "terminate" in message:
            start = message.index("terminate") + len("terminate")
            end = len(message) - 1
            matched_string = message[start:end].replace('"', "").strip()
            if "yes" in matched_string:
                json_response["terminate"] = "yes"
            else:
                json_response["terminate"] = "no"

    return json_response
