# sentient

this agent is based on our upcoming open-source framework [sentient](http://sentient.engineering) to help devs instantly build fast & reliable AI agents that can control browsers autonomously in 3 lines of code.

# jobber - apply to relevant jobs on internet autonomously

jobber is an ai agent that searches and applies for jobs on your behalf by controlling your browser. put in your resume and preferences and it does the work in background.

#### demo

checkout this [loom video](https://www.loom.com/share/2037ee751b4f491c8d2ffd472d8223bd?sid=53d08a9f-5a9b-4388-ae69-445032b31738) for a quick demo

#### setup

1. Create a fork of this repository on GitHub and clone your fork
2. use python >=3.8 in venv
```bash
python3 --version # output: Python 3.8.xx
python3 -m venv .venv
source .venv/bin/activate
```
3. Copy the example env file
```bash
cp .env.example .env
```
4. Create service account API key for jobber on OpenAI (and Langsmith) and paste them in the `.env` file.
5. Install dependencies
```bash
pip3 install -r requirements.txt
```
6. Setup playwright's browser binaries:
```bash
playwright install
```

#### running the agent

1. Start a chrome instance with this command and do necessary logins `sudo /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
OR using this command for Ubuntu:
```bash
google-chrome --remote-debugging-port=9222
```
2. Update your preferences in the `./jobber/user_preferences/user_preferences.txt` file.
3. use the command `python -u -m jobber`
4. example task - `apply for a backend engineer role based in helsinki on linkedin`

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
