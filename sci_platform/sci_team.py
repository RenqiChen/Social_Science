import os
import sys
sys.path.append('../agentscope-main/src')
import logging
from agentscope.memory import TemporaryMemory
class Team:
    def __init__(self, team_name):
        # attrs
        self.team_name = team_name
        self.state = 1
        self.epoch = -1
        self.teammate = []
        self.memory = TemporaryMemory(None)
        self.topic = None
        self.idea = None
        self.abstract = None
        self.citation_id = None
        self.self_review = None
        self.paper_review = None

        # state log
        self.state_log = {
            1: 'WAIT',
            2: 'TOPIC',
            3: 'IDEA',
            4: 'ABSTRACT',
            5: 'REVIEW',
            6: 'FINISH'
        }

        # init log file
        self.log_file = f"logs/{self.team_name}_dialogue.log"
        os.makedirs("logs", exist_ok=True)

        # Check if log file exists and delete it
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

        self.logger = logging.getLogger(self.team_name)
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(self.log_file)
        self.logger.addHandler(fh)

    def log_dialogue(self, name, content):
        self.logger.info(f'Epoch:{self.epoch} | {self.state_log[self.state]} | {name}:{content}')

if __name__=='__main__':
    team1 = Team('LPL')
    team2 = Team('LCK')
    team1.log_dialogue('sam', 'LPL win!')
    team2.log_dialogue('tom', 'LCK win!')
    team1.log_dialogue('sam', 'LPL win again !')
    team2.log_dialogue('tom', 'LCK win again !')
