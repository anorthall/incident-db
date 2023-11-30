import json
import time
from datetime import datetime, timedelta

import humanize
import settings
from openai import OpenAI


def log(msg: str, print_msg=False) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] {msg}"
    if print_msg:
        print(msg)

    with open(settings.LOG_FILE, "a") as f:
        f.write(msg + "\n")


def fmt_delta(delta: timedelta) -> str:
    return humanize.precisedelta(
        delta,
        minimum_unit="seconds",
        format="%0.0f",
    )


def generate_output_file_name(prefix="tmp_") -> str:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    return f"output/{prefix}{timestamp}.json"


def main():
    time_now = datetime.now().strftime("%H:%M:%S")
    log(f"Starting run with chat completions API at {time_now}.", print_msg=True)
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    with open(settings.DATA_FILE, "r") as f:
        data = f.read()

    with open(settings.PROMPT_FILE, "r") as f:
        prompt = f.read()

    log(
        f"Data/prompt loaded from {settings.DATA_FILE} and {settings.PROMPT_FILE}.",
        print_msg=True,
    )
    log(f"Data length: {len(data)}.", print_msg=True)
    log(f"Prompt length: {len(prompt)}.", print_msg=True)

    data = data.split("---")
    for item in data:
        if len(item) > settings.CHAR_LIMIT:
            log(f"Item too long: {len(item)} > {settings.CHAR_LIMIT}.", print_msg=True)
            log(f"Item:\n{item}", print_msg=True)
            exit(1)

    total_duration = timedelta()
    request_count = 0
    requests_needed = len(data)
    results = []

    log(
        f"Starting chat completion loop. {requests_needed} requests will be made.",
        print_msg=True,
    )

    while data:
        request_count += 1
        report = data.pop(0)

        log(f"Starting request {request_count} of {requests_needed}.", print_msg=True)
        log(f"Request data:\n{report}")

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": report},
        ]

        try:
            start_time = datetime.now()
            response = client.chat.completions.create(
                model=settings.MODEL,
                response_format={"type": "json_object"},
                seed=1,
                messages=messages,
            )
            duration = datetime.now() - start_time
            total_duration += duration

            log(f"{response = }")

            reply = response.choices[0].message.content
            file_name = generate_output_file_name()
            with open(file_name, "a") as f:
                f.write(reply)

            parsed = json.loads(reply)
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
        log(f"Request took {fmt_delta(duration)} to complete.", print_msg=True)
        log(f"Total duration so far is {fmt_delta(total_duration)}.", print_msg=True)

    log(f"Run complete with {request_count} requests.", print_msg=True)
    log(f"Run took {fmt_delta(total_duration)} to complete.", print_msg=True)

    file_name = generate_output_file_name(prefix="results_")
    with open(file_name, "w") as f:
        json.dump(results, f, indent=2)
    log(f"Results written to {file_name}.", print_msg=True)


if __name__ == "__main__":
    main()
