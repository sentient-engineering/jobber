# sentient

this agent is based on our upcoming open-source framework [sentient](https://github.com/sentient-engineering/sentient) to help devs instantly build fast & reliable AI agents that can control browsers autonomously in 3 lines of code. checkout the beta sentient package on [pypi](https://pypi.org/project/sentient/) & our experiemnts to advance oss web navigating agents in the [agent-q repository](https://github.com/sentient-engineering/agent-q)

# jobber - apply to relevant jobs on internet autonomously

jobber is an ai agent that searches and applies for jobs on your behalf by controlling your browser. put in your resume and preferences and it does the work in background.

### demo

checkout this [loom video](https://www.loom.com/share/2037ee751b4f491c8d2ffd472d8223bd?sid=53d08a9f-5a9b-4388-ae69-445032b31738) for a quick demo

### jobber and jobber_fsm

you might notice two separate implementations of jobber in the repo. `jobber` folder contains a simpler approach to implementing multi-agent conversation required between a planner and a browser agent.

the `jobber_fsm` folder contains another approach based on [finite state machines](https://github.com/sentient-engineering/multi-agent-fsm). there are slight nuances and both result in similar level or performace. however, the fsm approach is more scalable, and we will be doing further improvements in it.

the downside of fsm agent is that it is dependent on [structured output](https://openai.com/index/introducing-structured-outputs-in-the-api/) from open ai. so you can't reliably use cheaper models like gpt4o-mini or other oss models which is possible in `jobber`

### setup

1. we recommend installing poetry before proceeding with the next steps. you can install poetry using these [instructions](https://python-poetry.org/docs/#installation)

2. install dependencies

```bash
poetry install
```

3. start chrome in dev mode - in a seaparate terminal, use the command to start a chrome instance and do necesssary logins to job websites like linkedin/ wellfound, etc.

for mac, use command -

```bash
sudo /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

for linux -

```bash
google-chrome --remote-debugging-port=9222
```

for windows -

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

4. set up env - add openai and [langsmith](https://smith.langchain.com) keys to .env file. you can refer .env.example. currently adding langsmith is required but if you do not want to use it for tracing - then you can comment the line `litellm.success_callback = ["langsmith"]` in the `./jobber_fsm/core/agent/base.py` file.

5. update your preferences in the `user_preferences.txt` file in the folder of agent that you are running (jobber/ jobber_fsm). provide the local file path to your resume in this file itself for the agent to be able to upload it.

6. run the agent - jobber_fsm or jobber

```bash
python -u -m jobber_fsm
```

or

```bash
python -u -m jobber
```

6. enter your task. sample task -

```bash
apply for a backend engineer role based in helsinki on linkedin
```

### Run evals

1. For Jobber

```bash
 python -m test.tests_processor --orchestrator_type vanilla
```

2. For Jobber FSM

```bash
 python -m test.tests_processor --orchestrator_type fsm
```

#### citations

a bunch of amazing work in the space has inspired this. see [webvoyager](https://arxiv.org/abs/2401.13919), [agent-e](https://arxiv.org/abs/2407.13032)

```
@article{he2024webvoyager,
  title={WebVoyager: Building an End-to-End Web Agent with Large Multimodal Models},
  author={He, Hongliang and Yao, Wenlin and Ma, Kaixin and Yu, Wenhao and Dai, Yong and Zhang, Hongming and Lan, Zhenzhong and Yu, Dong},
  journal={arXiv preprint arXiv:2401.13919},
  year={2024}
}
```

```
@misc{abuelsaad2024-agente,
      title={Agent-E: From Autonomous Web Navigation to Foundational Design Principles in Agentic Systems},
      author={Tamer Abuelsaad and Deepak Akkil and Prasenjit Dey and Ashish Jagmohan and Aditya Vempaty and Ravi Kokku},
      year={2024},
      eprint={2407.13032},
      archivePrefix={arXiv},
      primaryClass={cs.AI},
      url={https://arxiv.org/abs/2407.13032},
}
```
