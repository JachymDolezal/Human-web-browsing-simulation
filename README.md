### Installation guide

This guide will show how to install the required packages using conda and pip.

The project was developed on linux, so the installation guide is for linux.

#### Install conda

to install conda follow the guide [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/linux.html)

#### Create conda environment and install packages

conda allows for creating environments with a .yml file that contains the required packages.

to create the environment run the following command:

```bash
conda env create -f environment.yml
```
the environment.yml file is located in the root of the project and includes name of the environment and the required packages. The name of the env is `simlatorthesis`, but can be changed in the environment.yml file.

After running the command, the environment will be created and the required packages will be installed.

To activate the environment run the following command:

```bash
conda activate simulatorthesis
```

#### Run the project

The project requires API key for openai with the default LLM provider openai selected. The API key should be placed in the .env file located in the root of the project.

The example of the .env file is:

```bash
OPENAI_API_KEY=your_api_key
```

To run the project, you need to run app.py file. The file is located in the root of the project. The `config.json` is configuration file that contains the configuration for the project.

```bash
python3 app.py
```

The run the benchmarks, you can use benchmark.ipynb file located in the root of the project.


### config examples

The configuration includes the following fields:

- website: the website to be used for the simulation

- goal: the goal of the simulation

- request_rate: least amount of time between actions

- personna: the selected personna for the simulation

- llm_provider: the LLM provider to be used for the simulation (openai)

- model_name: the model name to be used for the simulation (gpt-4-turbo or gpt-3.5-turbo were tested)

- temperature: the temperature for the model

- verbose: if the verbose is set to true, the output will be printed to the console

- initial_timeout: the initial timeout for the simulation

- timeout_per_action: the timeout per action

- web_data: the web data to be used for the simulation defining search bar id or sets a setting for filtering hrefs

- cookie_config: the cookie configuration for the simulation allowing to accept or reject cookies by clicking on the buttons with the specified type and name


the type key in webdata and cookie_config can be class or id, link, tag or css.

example for u.gg

```json

{
    "website": "https://u.gg/lol/champions",
    "goal": "Find counter for a champion Ahri",
    "request_rate": 30,
    "persona": "generic",
    "llm_provider": "openai",
    "model_name": "gpt-4-turbo",
    "temperature": 0.45,
    "verbose": true,
    "initial_timeout": 3,
    "timeout_per_action": 0,
    "cookie_config": {
        "buttons": [
            {
                "type": "class",
                "name": "fc-button-label"
            }
        ]
    }
}

```

example for rottentomatoes.com

```json

{
    "website": "https://www.rottentomatoes.com/",
    "goal": "Find name of a director of a film Monty Python and the Holy Grail",
    "request_rate": 30,
    "persona": "generic",
    "llm_provider": "openai",
    "model_name": "gpt-4-turbo",
    "temperature": 0.45,
    "verbose": true,
    "initial_timeout": 3,
    "timeout_per_action": 0,
    "web_data": {
        "type": "class",
        "name": "search-text"
    },
    "cookie_config": {
        "buttons": [
            {
                "type": "id",
                "name": "onetrust-reject-all-handler"
            }
        ]
    }
}

```

example for wikipedia.org

```json

{
    "website": "https://www.wikipedia.org/",
    "goal": "Find when Vaclav Havel completed his secondary education.",
    "request_rate": 30,
    "persona": "generic",
    "llm_provider": "openai",
    "model_name": "gpt-4-turbo",
    "temperature": 0.45,
    "verbose": true,
    "initial_timeout": 3,
    "timeout_per_action": 0,
    "web_data": {
        "filter_hrefs": true
    }
}

```

example for python.org

```json

{
    "website": "https://www.python.org/",
    "goal": "Find names of upcoming events in USA",
    "request_rate": 30,
    "persona": "generic",
    "llm_provider": "openai",
    "model_name": "gpt-4-turbo",
    "temperature": 0.45,
    "verbose": true,
    "initial_timeout": 3,
    "timeout_per_action": 0
}

```

example for dictionry.cambridge.org

```json

{
    "website": "https://dictionary.cambridge.org/",
    "goal": "Find the defition of a word Fungus",
    "request_rate": 30,
    "persona": "generic",
    "llm_provider": "openai",
    "model_name": "gpt-4-turbo",
    "temperature": 0.45,
    "verbose": true,
    "initial_timeout": 3,
    "timeout_per_action": 0,
    "cookie_config": {
        "buttons": [
        {
            "type": "id",
            "name": "onetrust-accept-btn-handler"
        }]
    }
}


```