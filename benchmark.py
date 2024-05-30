from datetime import datetime
import os
from src.simulation import *
import json


def parse_application_log(filename:str) -> list[dict]:
    with open(filename, "r") as f:
        data = f.read().split("\n")
        # remove last empty line
        data.pop()

def exit_validator(data:dict) -> bool:
    if data[-1]["action_type"] == "Exit":
        return True
    return False

def goal_complete_validator(data:dict, correct_url, correct_action_type) -> bool:
    if data[-2]["action_type"] == correct_action_type and data[-2]["current_url"] in correct_url:
        return True
    return False

def parse_action_log(filename:str) -> list[dict]:
    data_list = []
    with open(filename, "r") as f:
        data = f.read().split("\n")
        # remove last empty line
        data.pop()
    for row in data:
        # split by | -> 0: action_type, 1: action data, 2: goal, 3: current url
        row = row.split("|")
        print("row", row)
        data_row = {}
        print(row)
        data_row["action_type"] = row[0].strip()
        data_row["action_data"] = eval(row[1])
        data_row["goal"] = row[2].strip()
        data_row["current_url"] = row[3].strip()
        # convert 2024-04-24 15:36:45.461417 to datetime object
        timestamp = datetime.strptime(row[4].strip(), "%Y-%m-%d %H:%M:%S.%f")
        data_row["epoch_timestamp"] = timestamp.timestamp()
        data_list.append(data_row)

    print(data_list)
    return data_list

def calculate_action_log_metrics(data:list[dict],target_urls,target_action) -> dict:
    metrics = {}
    metrics["exit"] = exit_validator(data)
    metrics["goal_complete"] = goal_complete_validator(data, target_urls, target_action)
    # metrics["time"] = calculate_time(data)
    metrics["action_count"] = len(data)
    metrics["action_per_type"] = {
        "Search": 0,
        "Click": 0,
        "Exit": 0,
        "Retrieve" : 0,
    }
    metrics["simulation_length"] = data[-1]["epoch_timestamp"] - data[0]["epoch_timestamp"]
    metrics["average_time_per_action"] = metrics["simulation_length"] / metrics["action_count"]
    for row in data:
        metrics["action_per_type"][row["action_type"]] += 1
    metrics["raw_data"] = data
    metrics["logs"] = app_log_metrics("log.txt")
    return metrics

def app_log_metrics(filename:str) -> dict:
    log_parsed = {}
    log_parsed["raw_data"] = []
    # parse log file of structure datetime | log level | message
    # raw data as list of dict
    log_parsed["count_per_level"] = {
        "DEBUG": 0,
        "INFO": 0,
        "WARNING": 0,
        "ERROR": 0
    }
    # open file and read
    with open(filename, "r") as f:
        data = f.read().split("\n")
        # remove empty lines
        data = [row for row in data if row]

        # split by | -> 0: datetime, 1: log level, 2: message
        for row in data:
            row = row.split("|")
            log_parsed["raw_data"].append({
                "datetime": row[0].strip(),
                "log_level": row[1].strip(),
                "message": row[2].strip()
            })
            log_parsed["count_per_level"][row[1].strip()] += 1

    return log_parsed

def benchmark(config):

    # create folder by benchmark name and store logs from simulation in path
    # benchmark_name/model/website_name/run_number

    main_dir_name = config["benchmark_name"]


    # create main directory

    for simulation in config["simulations"]:
        model_dir_name = simulation["model"]
        website_dir_name = simulation["website_name_short"]
        website = simulation["website"]
        goal = simulation["goal"]
        runs = simulation["runs"]
        cookie_config = simulation.get("cookie_config", None)
        web_data_config = simulation.get("web_data", None)

        llm_provider = simulation.get("llm_provider","openai")
        model_name = simulation.get("model_name","gpt-3.5-turbo")
        temperature = simulation.get("temperature",0.4)
        verbose = simulation.get("verbose",True)
        goal = simulation.get("goal", None)
        website = simulation.get("website", None)
        timeout_per_action = simulation.get("timeout_per_action", 5)

        print(f"Running simulation for {website} to {goal} {runs} times")

        sucess = 0
        error = 0
        for i in range(runs):

            # remove log.txt and actions.txt and simulation_requests.ndjson if they exist
            if os.path.exists("log.txt"):
                os.remove("log.txt")
                # create new log.txt empty file
                with open("log.txt", "w") as f:
                    pass
            if os.path.exists("actions.txt"):
                os.remove("actions.txt")
                # create new actions.txt empty file
                with open("actions.txt", "w") as f:
                    pass
            if os.path.exists("simulation_requests.ndjson"):
                os.remove("simulation_requests.ndjson")
                # create new simulation_requests.ndjson empty file
                with open("simulation_requests.ndjson", "w") as f:
                    pass

            try:
                app = App()
                app.website = website
                app.goal = goal
                app.cookies_config = cookie_config
                app.web_data = web_data_config
                app.llm_provider = llm_provider
                app.model_name = model_name
                app.temperature = temperature
                app.verbose = verbose
                app.timeout_per_action = timeout_per_action
                app.run()
            except Exception as e:
                print(f"Error running simulation for {website} to {goal} {runs} times")
                print(e)
                error += 1
                continue

            # read log file and analyze data
            # open log_actions.txt and split by lines
            output = parse_action_log("actions.txt")

            if exit_validator(output) and goal_complete_validator(output, simulation["target_urls"], simulation["final_action"]):
                sucess += 1
            # evaluate if the goal was accomplished or not to determine success or failure
            # count metrics of warnings, errors etc.


            # check if path exists
            if not os.path.exists(f"./{main_dir_name}/{model_dir_name}/{website_dir_name}"):
                os.makedirs(f"./{main_dir_name}/{model_dir_name}/{website_dir_name}")

            # create dir for requests
            if not os.path.exists(f"./{main_dir_name}_requests/{model_dir_name}/{website_dir_name}"):
                os.makedirs(f"./{main_dir_name}_requests/{model_dir_name}/{website_dir_name}")

            current_time = datetime.now().strftime("%d_%H_%M_%S")

            with open(f"./{main_dir_name}/{model_dir_name}/{website_dir_name}/{current_time}_{i}_metrics.json", "w") as f:
                # store as json
                data = calculate_action_log_metrics(output, simulation["target_urls"], simulation["final_action"])
                # convert data to json
                json.dump(data, f)
            print(f"Simulation for {website} to {goal} completed {i + 1} times")

            # copy simulation_requests.ndjson to benchmark_requests
            os.rename("simulation_requests.ndjson", f"./{main_dir_name}_requests/{model_dir_name}/{website_dir_name}/{current_time}_{i}_requests.ndjson")

        print(f"Simulation for {website} to {goal} completed {sucess} times with {error} errors percantage of {error/runs * 100}")


