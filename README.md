# sentient

this agent is based on our upcoming open-source framework [sentient](http://sentient.engineering) to help devs instantly build fast & reliable AI agents that can control browsers autonomously in 3 lines of code.

# jobber - apply to relevant jobs on internet autonomously

jobber is an ai agent that searches and applies for jobs on your behalf by controlling your browser. put in your resume and preferences and it does the work in background.

#### demo

checkout this [loom video](https://www.loom.com/share/2037ee751b4f491c8d2ffd472d8223bd?sid=53d08a9f-5a9b-4388-ae69-445032b31738) for a quick demo

#### setup

1. install poetry if not already installed
2. use python >=3.8 in venv
3. do poetry install

#### running the agent

1. Start a chrome instance with this command and do necessary logins `sudo /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222`
2. use the command `python -u -m jobber.main`
3. example task - `apply for a backend engineer role based in helsinki on linkedin`

#### prior work
a bunch of amazing work in the space has inspired this. see [webvoyager](https://arxiv.org/abs/2401.13919), [agent-e](https://arxiv.org/abs/2407.13032)
