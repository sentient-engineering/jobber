import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from playwright.async_api import Page
from tabulate import tabulate
from termcolor import colored

from jobber.config import PROJECT_TEST_ROOT
from jobber.core.system_orchestrator import SystemOrchestrator
from jobber.utils.logger import logger
from test.evaluators import evaluator_router
from test.test_utils import (
    get_formatted_current_timestamp,
    load_config,
    task_config_validator,
)

TEST_TASKS = os.path.join(PROJECT_TEST_ROOT, "tasks")
TEST_LOGS = os.path.join(PROJECT_TEST_ROOT, "logs")
TEST_RESULTS = os.path.join(PROJECT_TEST_ROOT, "results")


def check_top_level_test_folders():
    for folder in [TEST_LOGS, TEST_RESULTS]:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"Created folder at: {folder}")


def create_test_results_id(test_results_id: Optional[str], test_file: str) -> str:
    prefix = "test_results_for_"
    if test_results_id:
        return f"{prefix}{test_results_id}"
    test_file_base = os.path.basename(test_file)
    test_file_name = os.path.splitext(test_file_base)[0]
    return f"{prefix}{test_file_name}"


def create_task_log_folders(task_id: str, test_results_id: str) -> Dict[str, str]:
    task_log_dir = os.path.join(
        TEST_LOGS, f"{test_results_id}", f"logs_for_task_{task_id}"
    )
    task_screenshots_dir = os.path.join(task_log_dir, "snapshots")
    for directory in [task_log_dir, task_screenshots_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory at: {directory}")
    return {
        "task_log_folder": task_log_dir,
        "task_screenshots_folder": task_screenshots_dir,
    }


def create_results_dir(test_file: str, test_results_id: Optional[str]) -> str:
    if test_results_id:
        results_dir = os.path.join(TEST_RESULTS, f"results_for_{test_results_id}")
    else:
        test_file_base = os.path.basename(test_file)
        test_file_name = os.path.splitext(test_file_base)[0]
        results_dir = os.path.join(
            TEST_RESULTS, f"results_for_test_file_{test_file_name}"
        )
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
        logger.info(f"Created results directory: {results_dir}")
    return results_dir


def dump_log(task_id: str, messages: Dict[str, Any], logs_dir: str):
    file_name = os.path.join(logs_dir, f"execution_logs_{task_id}.json")
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=4)


def save_test_results(test_results: List[Dict[str, Any]], test_results_id: str):
    file_name = os.path.join(TEST_RESULTS, f"test_results_{test_results_id}.json")
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(test_results, f, ensure_ascii=False, indent=4)
    logger.info(f"Test results dumped to: {file_name}")


def save_individual_test_result(test_result: Dict[str, Any], results_dir: str):
    task_id = test_result["task_id"]
    file_name = os.path.join(results_dir, f"test_result_{task_id}.json")
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(test_result, f, ensure_ascii=False, indent=4)
    logger.info(f"Test result for task {task_id} dumped to: {file_name}")


def print_progress_bar(current: int, total: int, bar_length: int = 50) -> None:
    percent = float(current) * 100 / total
    arrow = "-" * int(percent / 100 * bar_length - 1) + ">"
    spaces = " " * (bar_length - len(arrow))
    print(f"\rProgress: [{arrow}{spaces}] {current}/{total} ({percent:.2f}%)", end="")


def determine_status_and_color(score: float) -> Tuple[str, str]:
    if score == 1:
        return "Pass", "green"
    elif score < 0:
        return "Skip", "yellow"
    else:
        return "Fail", "red"


def print_test_result(task_result: Dict[str, Any], index: int, total: int) -> None:
    status, color = determine_status_and_color(task_result["score"])
    result_table = [
        ["Test Index", "Task ID", "Intent", "Status", "Time Taken (s)"],
        [
            index,
            task_result["task_id"],
            task_result["intent"],
            colored(status, color),
            round(task_result["tct"], 2),
        ],
    ]
    print("\n" + tabulate(result_table, headers="firstrow", tablefmt="grid"))


async def execute_single_task(
    task_config: Dict[str, Any],
    orchestrator: SystemOrchestrator,
    page: Page,
    logs_dir: str,
) -> Dict[str, Any]:
    task_config_validator(task_config)
    command = task_config.get("intent", "")
    task_id = task_config.get("task_id")
    task_index = task_config.get("task_index")
    start_url = task_config.get("start_url")
    logger.info(f"Intent: {command}, Task ID: {task_id}")

    if start_url:
        await page.goto(start_url, wait_until="load", timeout=30000)

    start_time = time.time()
    # current_url = await orchestrator.playwright_manager.get_current_url()
    command_exec_result = await orchestrator.execute_command(command)
    end_time = time.time()

    single_task_result = {
        "task_id": task_id,
        "task_index": task_index,
        "start_url": start_url,
        "intent": str(command),
        "last_url": page.url,
        "tct": end_time - start_time,
        "start_ts": get_formatted_current_timestamp(),
        "completion_ts": get_formatted_current_timestamp(),
    }

    logger.info(f'Command "{command}" took: {round(end_time - start_time, 2)} seconds.')
    logger.info(f"Task {task_id} completed.")

    single_task_result["last_statement"] = command_exec_result

    dump_log(
        str(task_id), {"command": command, "result": command_exec_result}, logs_dir
    )

    evaluator = evaluator_router(task_config)
    cdp_session = await page.context.new_cdp_session(page)
    evaluator_result = await evaluator(
        task_config=task_config,
        page=page,
        client=cdp_session,
        answer=command_exec_result,
    )

    single_task_result["score"] = evaluator_result["score"]
    single_task_result["reason"] = evaluator_result["reason"]

    return single_task_result


async def run_tests(
    orchestrator: SystemOrchestrator,
    min_task_index: int,
    max_task_index: int,
    test_file: str = "",
    test_results_id: str = "",
    wait_time_non_headless: int = 5,
    take_screenshots: bool = True,
) -> List[Dict[str, Any]]:
    check_top_level_test_folders()

    if not test_file:
        test_file = os.path.join(TEST_TASKS, "test.json")

    logger.info(f"Loading test configurations from: {test_file}")
    test_configurations = load_config(test_file)
    test_results_id = create_test_results_id(test_results_id, test_file)
    results_dir = create_results_dir(test_file, test_results_id)

    if orchestrator is None:
        orchestrator = SystemOrchestrator(eval_mode=True)
        await orchestrator.start()

    page = await orchestrator.playwright_manager.get_current_page()
    test_results = []
    max_task_index = len(test_configurations) if not max_task_index else max_task_index
    total_tests = max_task_index - min_task_index

    for index, task_config in enumerate(
        test_configurations[min_task_index:max_task_index], start=min_task_index
    ):
        task_id = str(task_config.get("task_id"))
        log_folders = create_task_log_folders(task_id, test_results_id)

        orchestrator.playwright_manager.set_take_screenshots(take_screenshots)
        if take_screenshots:
            orchestrator.playwright_manager.set_screenshots_dir(
                log_folders["task_screenshots_folder"]
            )

        print_progress_bar(index - min_task_index, total_tests)
        task_result = await execute_single_task(
            task_config, orchestrator, page, log_folders["task_log_folder"]
        )
        test_results.append(task_result)
        save_individual_test_result(task_result, results_dir)
        print_test_result(task_result, index + 1, total_tests)

        if not orchestrator.playwright_manager.isheadless:
            await asyncio.sleep(wait_time_non_headless)

        await orchestrator.playwright_manager.take_screenshots("final", None)
        await orchestrator.playwright_manager.close_except_specified_tab(page)

    print_progress_bar(total_tests, total_tests)
    print("\n\nAll tests completed.")

    print("\nDetailed Test Results:")
    detailed_results_table = [
        ["Test Index", "Task ID", "Intent", "Status", "Time Taken (s)"]
    ]
    for idx, result in enumerate(test_results, 1):
        status, color = determine_status_and_color(result["score"])
        detailed_results_table.append(
            [
                idx,
                result["task_id"],
                result["intent"],
                colored(status, color),
                round(result["tct"], 2),
            ]
        )

    print(tabulate(detailed_results_table, headers="firstrow", tablefmt="grid"))

    passed_tests = [result for result in test_results if result["score"] == 1]
    skipped_tests = [result for result in test_results if result["score"] < 0]
    failed_tests = [result for result in test_results if 0 <= result["score"] < 1]

    summary_table = [
        [
            "Total Tests",
            "Passed",
            "Failed",
            "Skipped",
            "Average Time Taken (s)",
            "Total Time Taken (s)",
        ],
        [
            total_tests,
            len(passed_tests),
            len(failed_tests),
            len(skipped_tests),
            round(sum(test["tct"] for test in test_results) / total_tests, 2),
            round(sum(test["tct"] for test in test_results), 2),
        ],
    ]

    print("\nSummary Report:")
    print(tabulate(summary_table, headers="firstrow", tablefmt="grid"))

    return test_results


# Main execution function (if needed)
async def main():
    orchestrator = SystemOrchestrator()
    await orchestrator.start()
    test_results = await run_tests(orchestrator, 0, 5)  # Example: Run first 5 tests
    await orchestrator.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
