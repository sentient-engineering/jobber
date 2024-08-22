import json
import os
from typing import Any, Dict, List

from jobber.config import PROJECT_TEST_ROOT
from test.test_utils import load_config


def validate_and_update_task_ids(tasks: List[Dict[str, Any]]) -> None:
    """Ensure that task IDs match their positions in the List and update them if necessary.

    Args:
        tasks (List[Dict[str, Any]]): The List of tasks to process.
    """
    for index, task in enumerate(tasks):
        task["task_id"] = index


def substitute_intent_templates(tasks: List[Dict[str, Any]]) -> None:
    """Substitute intent_template patterns with values from instantiation_Dict.

    Args:
        tasks (List[Dict[str, Any]]): The List of tasks to process.
    """
    for task in tasks:
        if "intent_template" in task and "instantiation_Dict" in task:
            template = task["intent_template"]
            for key, value in task["instantiation_Dict"].items():
                placeholder = "{{" + key + "}}"
                template = template.replace(placeholder, str(value))
            task["intent"] = template


def save_json_file(tasks: List[Dict[str, Any]], file_path: str) -> None:
    """Save the modified List of tasks back to a JSON file.

    Args:
        tasks (List[Dict[str, Any]]): The List of modified tasks.
        file_path (str): The path to save the JSON file.
    """
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(tasks, file, ensure_ascii=False, indent=4)


def process_tasks(file_path: str) -> None:
    """Load, process, and save tasks from/to a JSON file.

    Args:
        file_path (str): The path to the JSON file containing tasks.
    """
    tasks = load_config(file_path)
    validate_and_update_task_ids(tasks)
    substitute_intent_templates(tasks)
    save_json_file(tasks, file_path)


if __name__ == "__main__":
    file_path = os.path.join(PROJECT_TEST_ROOT, "tasks", "test.json")
    process_tasks(file_path)
