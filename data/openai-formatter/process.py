#!/usr/bin/env python3
"""Process text data using the OpenAI API.

Operations:
- batch: Run the chat completions API in batch mode.
- sync: Run the chat completions API synchronously.
- check: Open a results file and check the contents conform to the expected format.

Usage:

Running operations:
- python process.py --operation batch --name "ACA 1987" --file "processed/txt-split/ACA 1987.txt"
- python process.py --operation sync --name "ACA 1987" --file "processed/txt-split/ACA 1987.txt"
- python process.py --operation check --name "ACA 1987" --file "output/aca_1987.json"

Collecting batch results:
- python process.py --operation collectbatch

"""

import argparse
from typing import Any

import orjson
import os
import re
import time
from datetime import datetime, timedelta
from timeit import default_timer

import humanize
from openai.types.batch import Batch
from openai.types.chat import ChatCompletion

from openai import OpenAI
from openai.types.file_object import FileObject

OPERATIONS = ["batch", "run", "check", "collectbatch"]
LOG_FILE = "openai.log"
PROMPT_FILE = "prompt.txt"
CHAR_LIMIT = 32768

MODEL = "gpt-4-turbo"
INPUT_TOKEN_COST = 0.00003
OUTPUT_TOKEN_COST = 0.00006

ALLOWED_MODELS = ["gpt-4-turbo", "gpt-3.5-turbo", "gpt3.5", "gpt-4"]
CHAT_COMPLETIONS_ENDPOINT = "/v1/chat/completions"


def log(msg: str, print_msg=False) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {msg}"
    if print_msg:
        print(msg)

    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")


def fmt_delta(delta: timedelta) -> str:
    return humanize.precisedelta(
        delta,
        minimum_unit="seconds",
        format="%0.0f",
    )


def generate_output_file_name(name: str, *, ext: str = "json", temp: bool = False, batches: bool = False,) -> str:
    prefix: str = normalise_file_name(name)
    timestamp = time.strftime("%Y%m%d-%H%M%S")

    if batches:
        folder: str = f"batches/{prefix}"
    else:
        folder = f"output/{prefix}"

    if not os.path.isdir(folder):
        os.mkdir(folder)

    if temp:
        folder = f"{folder}/tmp"

    if not os.path.isdir(folder):
        os.mkdir(folder)

    return f"{folder}/{prefix}-{timestamp}.{ext}"


def normalise_file_name(file_name: str) -> str:
    """Normalise a string to be used as a file name."""
    result: str = (
        file_name
        .strip()
        .replace(" ", "-")
        .replace(",", "-")
        .replace("/", "-")
        .replace("_", "-")
        .replace(":", "-")
    )

    if not re.match(r"^[\w\-.]+$", result):
        raise ValueError(f"Invalid file name: {result}")

    return result


def get_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost of a request based on the number of input and output tokens."""
    return round(
        (input_tokens * INPUT_TOKEN_COST) + (output_tokens * OUTPUT_TOKEN_COST), 2
    )


def check_args(args: argparse.Namespace) -> None:
    """Check the command line arguments."""
    if args.operation not in OPERATIONS:
        log(f"Error: Invalid operation: {args.operation}", print_msg=True)
        exit(1)

    if args.operation == "collectbatch":
        return

    error: bool = False
    if not args.name:
        log("Error: No name specified.", print_msg=True)
        error = True

    if not args.file:
        log("Error: No file specified.", print_msg=True)
        error = True

    if args.limit < 0:
        log(f"Error: Invalid limit: {args.limit}", print_msg=True)
        error = True

    try:
        normalise_file_name(args.name)
    except ValueError as e:
        log(f"Error: Invalid name: {e}", print_msg=True)
        error = True

    try:
        with open(LOG_FILE, "a"):
            pass
    except OSError:
        log(f"Error: Unable to write to log file: {LOG_FILE}", print_msg=True)
        error = True

    if error:
        exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Process text data using the OpenAI API.")
    parser.add_argument(
        "-o",
        "--operation",
        type=str,
        choices=OPERATIONS,
        help="Operation to perform.",
    )
    parser.add_argument(
        "-f",
        "--file",
        type=argparse.FileType("r"),
        help="Path to the file containing the incidents to process.",
    )
    parser.add_argument(
        "-p",
        "--prompt",
        type=argparse.FileType("r"),
        help="Path to the file containing the prompt for the LLM.",
        default=PROMPT_FILE,
    )
    parser.add_argument(
        "-n",
        "--name",
        type=str,
        help="Name of the batch of incidents being processed.",
    )
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Maximum number of incidents to process.",
        default=0,
    )
    parser.add_argument(
        "--model",
        type=str,
        help="Model to use for processing.",
        default=MODEL,
        choices=ALLOWED_MODELS,
    )
    args = parser.parse_args()

    check_args(args)

    if not os.path.isdir("output"):
        os.mkdir("output")

    if args.operation == "check":
        raise NotImplemented

    client: OpenAI = get_openai_client()

    if args.operation == "batch" or args.operation == "collectbatch":
        if not os.path.isdir("batches"):
            os.mkdir("batches")

    if args.operation == "collectbatch":
        run_collect_batch(client)
        return

    if args.operation == "batch":
        run_processing_batch(client, args)
        return

    if args.operation == "run":
        run_processing_sync(client, args)
        return

    parser.print_help()


def get_openai_client() -> OpenAI:
    """Get an OpenAI client."""
    api_key: str | None = os.getenv("OPENAI_API_KEY")

    if not api_key:
        log("Error: OPENAI_API_KEY environment variable not set.", print_msg=True)
        exit(1)

    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        log(f"Error: Unable to create OpenAI client: {e}", print_msg=True)
        exit(1)


def setup_data(args: argparse.Namespace) -> tuple[list[str], str]:
    raw_data: str = args.file.read().strip()

    prompt: str = args.prompt.read().strip()
    prompt = prompt.replace("{{ PUBLICATION_NAME }}", args.name)

    log(
        f"Data and prompt loaded.",
        print_msg=True,
    )

    queue: list[str] = []
    data: list[str] = raw_data.split("------")
    for item in data:
        if len(item) > CHAR_LIMIT:
            log(f"Item too long: {len(item)} > {CHAR_LIMIT}.", print_msg=True)
            log(f"Item:\n{item}", print_msg=True)
            exit(1)
        queue.append(item)

    data_length: int = sum(len(item) for item in data)
    log(f"Data loaded. {len(data)} items. Total length: {data_length}.", print_msg=True)

    return queue, prompt


def build_messages(report: str, prompt: str) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": report},
    ]


def get_openai_request_args(model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "model": model,
        "response_format": {"type": "json_object"},
        "seed": 1,
        "messages": messages,
    }


def limit_queue(queue: list[str], limit: int) -> list[str]:
    if limit > 0:
        stop_point: int = min(limit, len(queue))
        queue = queue[:stop_point]
    return queue


def collect_batch_results(client: OpenAI, batch: Batch) -> str | None:
    """Collect the results of a completed batch."""
    if not os.path.isdir("batches/output"):
        os.mkdir("batches/output")

    output_folder_name: str = (
        normalise_file_name(batch.metadata.get("name", batch.id))
    )

    if os.path.isdir(f"batches/output/{output_folder_name}"):
        return None

    log(f"Collecting results for batch {batch.id}.", print_msg=True)
    log(f"Output folder: {output_folder_name}", print_msg=True)

    batch_output = client.files.content(batch.output_file_id)

    with open(f"batches/output/{output_folder_name}/{output_folder_name}.raw.json", "wb") as f:
        f.write(batch_output.content)

    if not batch_output:
        log(f"Error: unable to retrieve batch output file.", print_msg=True)
        return None

    output_file_name: str = f"batches/output/{output_folder_name}/{output_folder_name}.json"

    results: list[dict[str, Any]] = [
        orjson.loads(line)
        for line in batch_output.content.decode("utf-8").split("\n")
        if line
    ]

    responses: list[str] = []
    for line in results:
        response: str = line["response"]["body"]["choices"][0]["message"]["content"]

        try:
            response_obj: dict[str, Any] = orjson.loads(response)
        except orjson.JSONDecodeError:
            error_file_name: str = f"batches/output/{output_folder_name}/errors.jsonl"
            log(f"Error decoding response. Saved to {error_file_name}.", print_msg=True)
            with open(error_file_name, "a") as f:
                f.write(response + "\n")
            continue

        response_json: str = orjson.dumps(response_obj, option=orjson.OPT_INDENT_2).decode("utf-8")
        line["response"]["body"]["choices"][0]["message"]["content"] = response_obj
        responses.append(response_json)

    response_dict: dict[str, Any] = {
        "responses": results,
    }
    formatted_responses: bytes = orjson.dumps(response_dict, option=orjson.OPT_INDENT_2)

    with open(output_file_name, "wb") as f:
        f.write(formatted_responses)

    log(f"Batch output written to {output_file_name}.", print_msg=True)

    return output_file_name


def run_collect_batch(client: OpenAI) -> None:
    """Collect completed batch results."""
    log("Collecting batch results.", print_msg=True)
    batches: list[Batch] = list(client.batches.list())

    log(f"Retrieved {len(batches)} batches from OpenAI:", print_msg=True)
    for num, batch in enumerate(batches, 1):
        name: str = batch.metadata.get("name", batch.id)
        log(f"{num}: {name} - {batch.status}", print_msg=True)

    results_collected: list[str] = []
    for batch in batches:
        if batch.status == "completed":
            if result := collect_batch_results(client, batch):
                results_collected.append(result)

    log(f"Results collected for {len(results_collected)} batches.", print_msg=True)

    for result in results_collected:
        log(f"Collected: {result}", print_msg=True)

    log("Batch results collection complete.", print_msg=True)


def run_processing_batch(client: OpenAI, args: argparse.Namespace) -> None:
    """Run the chat completions API in batch mode."""
    log("Starting batch run with chat completions API.", print_msg=True)

    queue, prompt = setup_data(args)
    report_count: int = len(queue)

    queue = limit_queue(queue, args.limit)
    num_to_process: int = len(queue)

    log(
        f"Starting to queue batch requests. {report_count} reports found. "
        f"Processing {num_to_process} reports.",
        print_msg=True,
    )

    jobs: list[bytes] = []

    # Build jobs
    log(f"Building jobs for {num_to_process} reports.", print_msg=True)

    timestamp: str = datetime.now().strftime("%Y%m%d-%H%M%S")
    for num, report in enumerate(queue, 1):
        log(f"Building job for report {num} of {num_to_process}.")

        messages: list[dict[str, str]] = build_messages(report, prompt)
        batch_args: dict[str, Any] = {
            "custom_id": f"{normalise_file_name(args.name)}-{timestamp}-{num}",
            "method": "POST",
            "url": CHAT_COMPLETIONS_ENDPOINT,
            "body": get_openai_request_args(args.model, messages),
        }
        jobs.append(orjson.dumps(batch_args) + b"\n")

    # Write jobs to file
    batch_file_name: str = generate_output_file_name(args.name, ext="jsonl", batches=True)
    with open(batch_file_name, "wb") as f:
        for job in jobs:
            f.write(job)

    log(f"Batch file written to {batch_file_name}.", print_msg=True)

    # Upload batch file to OpenAI
    log("Uploading batch file to OpenAI.", print_msg=True)
    batch_input: FileObject = client.files.create(
        file=open(batch_file_name, "rb"),
        purpose="batch",  # type: ignore
    )

    if not batch_input or batch_input.status != "processed":
        log(f"Error: unable to upload batch file.", print_msg=True)
        exit(1)

    batch_input_json: str = batch_input.model_dump_json(indent=2)

    log(f"Batch file uploaded.", print_msg=True)
    log(f"{batch_input_json = }")

    batch_input_json_file_name: str = generate_output_file_name(args.name, ext="batchinput.json", batches=True,)

    with open(batch_input_json_file_name, "w") as f:
        f.write(batch_input_json)

    log(f"Batch input details written to {batch_input_json_file_name}", print_msg=True)

    # Start batch run
    log("Starting batch run.", print_msg=True)

    batch_output: Batch = client.batches.create(
        input_file_id=batch_input.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "name": f"{args.name} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        }
    )

    if not batch_output:
        log("Error: unable to start batch run.", print_msg=True)
        exit(1)

    batch_output_json: str = batch_output.model_dump_json(indent=2)

    log(f"Batch run started.", print_msg=True)
    log(f"{batch_output_json = }")

    batch_output_json_file_name: str = generate_output_file_name(args.name, ext="batchoutput.json", batches=True,)
    with open(batch_output_json_file_name, "w") as f:
        f.write(batch_output_json)

    log(f"Batch output details written to {batch_output_json_file_name}", print_msg=True)
    log("Batch run processing complete.", print_msg=True)


def run_processing_sync(client: OpenAI, args: argparse.Namespace) -> None:
    """Run the chat completions API synchronously."""
    time_now: str = datetime.now().strftime("%H:%M:%S")
    log(f"Starting run with chat completions API at {time_now}.", print_msg=True)

    queue, prompt = setup_data(args)
    report_count: int = len(queue)

    queue = limit_queue(queue, args.limit)
    num_to_process: int = len(queue)

    log(
        f"Starting chat completion loop. {report_count} reports found. "
        f"Processing {num_to_process} reports.",
        print_msg=True,
    )

    total_duration: timedelta = timedelta()
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    request_count: int = 0
    results: list[ChatCompletion] = []

    while queue:
        request_count += 1
        report: str = queue.pop(0)

        log(f"Starting request {request_count} of {num_to_process}.", print_msg=True)
        log(f"Request data:\n{report}")

        messages: list[dict[str, str]] = build_messages(report, prompt)

        response: ChatCompletion | None = None
        reply: str = ""

        try:
            request_start_time: float = default_timer()
            response = client.chat.completions.create(
                **get_openai_request_args(args.model, messages),
            )
            request_duration: timedelta = timedelta(seconds=default_timer() - request_start_time)

            if not response or not response.choices:
                raise Exception("No response received.")

            total_duration += request_duration
            total_tokens += response.usage.total_tokens
            input_tokens += response.usage.prompt_tokens
            output_tokens += response.usage.completion_tokens

            log(f"{response = }")

            reply: str = response.choices[0].message.content
            file_name: str = generate_output_file_name(args.name, temp=True)

            with open(file_name, "a") as f:
                f.write(reply)

            parsed: dict[str, Any] = orjson.loads(reply)

            if "results" not in parsed or len(parsed["results"]) == 0:
                raise Exception("No results in response.")

            for incident in parsed["results"]:
                results.append(incident)

        except Exception as e:
            log(f"Error processing request number {request_count}.", print_msg=True)
            log(f"Exception: {e}", print_msg=True)
            log(f"Request data:\n{report}", print_msg=True)
            log(f"{response = }", print_msg=True)
            log(f"Reply:\n{reply}", print_msg=True)
            log(f"Results:\n{results}", print_msg=True)
            continue

        log(
            f"Output from request {request_count} written to {file_name}.",
            print_msg=True,
        )
        log(f"Request took {fmt_delta(request_duration)} to complete.", print_msg=True)
        log(f"Total duration: {fmt_delta(total_duration)}.", print_msg=True)
        log(f"Cumulative cost: ${get_cost(input_tokens, output_tokens)}", print_msg=True)

    log(f"Run complete with {request_count} requests.", print_msg=True)
    log(f"Run took {fmt_delta(total_duration)} to complete.", print_msg=True)
    log(
        f"Total tokens used: {total_tokens}. "
        f"Input: {input_tokens}. Output: {output_tokens} ",
        print_msg=True,
    )
    log(f"Total cost: ${get_cost(input_tokens, output_tokens)}", print_msg=True)

    file_name = generate_output_file_name(args.name)
    with open(file_name, "wb") as f:
        f.write(orjson.dumps(results, option=orjson.OPT_INDENT_2))

    log(f"Results written to {file_name}.", print_msg=True)


if __name__ == "__main__":
    main()
