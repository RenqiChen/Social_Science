from datetime import datetime

import logging
import re
import ollama
import torch.nn.functional
import numpy as np
import json
import os
import sys
sys.path.append('../agentscope-main/src')

from agentscope.memory import TemporaryMemory
from agentscope.message import Msg
from utils.prompt import Prompts
from utils.scientist_utils import (
    extract_scientist_names,
    team_description,
    n2s,
    convert_you_to_other,
    team_description_detail,
    format_msg,
    formated_msg2str,
    read_txt_files_as_dict,
    extract_between_json_tags,
    extract_metrics,
    paper_search,
    strip_non_letters,
    save2database,
    count_team,
    top_three_indices,
    extract_first_number,
    most_frequent_element
)

class Team:
    def __init__(self, team_name, log_dir, info_dir):
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
            4: 'CHECK',
            5: 'ABSTRACT',
            6: 'REVIEW',
            7: 'FINISH'
        }

        # state action
        self.state_action = {
            2: self.select_topic,
            3: self.generate_idea,
            4: self.check_novelty,
            5: self.generate_abstract,
            6: self.generate_review
        }

        # init log file dir
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.info_file = f"{info_dir}/{current_time}_{self.team_name}_dialogue.json"
        self.log_file = f"{log_dir}/{current_time}_{self.team_name}_dialogue.log"

        # Check if log file exists and delete it
        if os.path.exists(self.log_file):
            os.remove(self.log_file)

        self.logger = logging.getLogger(self.team_name)
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.log_file)
        self.logger.addHandler(fh)

    # execute action based on team state
    def action_excution(self, platform):
        if self.state in self.state_log.keys():
            print(f'{"="*20} Epoch: {self.epoch} || BEGIN {self.state_log[self.state]} PROCESS {"="*20}')

        action = self.state_action.get(self.state, None)
        if action is not None:
            action(platform)
            print(f'{"="*20} Epoch: {self.epoch} || FINISH {self.state_log[self.state]} PROCESS {"="*20}')

    # general group discussion process
    def group_discuss(self, platform, prompt :str = None):
        # prompt is used to start and guide the discussion
        # for each turn, in group_discuss, all dialogue history is stored in dialogue_history but not in agent memory
        # after finishing each discussion turn, agent1 will summarize dialogue_history and add a summarization into team_history

        # get team_history
        team_history = self.memory
        # get teammate
        teammate = platform.id_to_agent(self.teammate)
        # init dialogue_history
        dialogue_history = TemporaryMemory(None)
        # init exit state
        exit = False
        # output return dialogue history, summarization of the last turn, and memory of the last turn
        output = {}
        # start discussing
        if len(teammate)==1:
            group_max_discuss_iteration = platform.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = platform.group_max_discuss_iteration

        for turn in range(group_max_discuss_iteration):
            said = []
            # init turn_memory for each turn
            turn_history = TemporaryMemory(None)
            agent_num = 0
            for agent in teammate:
                if agent.name in said:
                    continue
                else:
                    said.append(agent.name)
                agent_prompt = format_msg(
                    # current team
                    Msg(name="current team members", role="user", content=','.join(self.teammate)),
                    # team history
                    Msg(name="Summarizations of previous team discussions", role="user", content='')
                    if team_history.size()>0 else None,
                    team_history.get_memory(recent_n=platform.recent_n_team_mem_for_retrieve),
                    # prompt
                    Msg(name="user", role="user", content=prompt),
                    # dialogue history
                    Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
                    if dialogue_history.size()>0 else None,
                    dialogue_history.get_memory(recent_n=turn),
                    # turn history
                    Msg(name="Discussions in this turn", role="user", content='')
                    if turn_history.size()>0 else None,
                    turn_history.get_memory(recent_n=agent_num)
                )
                # add reply to turn_history
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False)
                if reply.content!=None and len(reply.content)>0:
                    self.log_dialogue(agent.name,reply.content)
                involved_scientist = extract_scientist_names(reply.content)
                print(involved_scientist)
                # judge whether someone is called to join the team
                for scientist_index in involved_scientist:
                    if scientist_index not in self.teammate:
                        if "by the way" in reply.content or "By the way" in reply.content:
                            hint = Msg(name=self.teammate[0],role="user",content=reply.content)
                            # invite new team member to comment
                            x = platform.id2agent[scientist_index].reply(hint, use_memory=False, use_RAG=False)
                            if x.content is not None:
                                said.append(scientist_index)
                                self.teammate.append(scientist_index)
                                self.log_dialogue(platform.id2agent[scientist_index].name, x.content)
                                teammate.append(platform.id2agent[scientist_index])

                turn_history.add(reply)
                agent_num = agent_num + 1
                # discussion is finished
                if 'exit' in reply:
                    exit = True
                    break

            # summarize this turn's discussion
            history = format_msg(
                # team history
                Msg(name="Summarizations of previous team discussions", role="user", content='')
                if team_history.size()>0 else None,
                team_history.get_memory(recent_n=platform.recent_n_team_mem_for_retrieve),
                # dialogue history
                Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
                if dialogue_history.size()>0 else None,
                dialogue_history.get_memory(recent_n=turn),
            )
            x = teammate[0].summarize(history = history, content = turn_history.get_memory(recent_n=agent_num))
            self.log_dialogue(teammate[0].name, x.content)
            turn_summarization = Msg(name="summarizations of turn{}".format(turn+1), role="user",
                                     content=x.content)

            if exit or turn==group_max_discuss_iteration-1:
                output['last_turn_summarization'] = turn_summarization
                output['last_turn_history'] = turn_history
                break
            else:
                dialogue_history.add(turn_summarization)

        output['dialogue_history'] = dialogue_history
        self.teammate = platform.agent_to_id(teammate)
        return output

    def select_topic(self, platform):
        # prompt to start discussing select_topic
        discuss_result = self.group_discuss(platform, Prompts.to_start_topic_discussion)
        team_history = self.memory
        dialogue_history = discuss_result['dialogue_history']
        last_turn_history = discuss_result['last_turn_history']
        last_turn_summarization = discuss_result['last_turn_summarization']

        answer_prompt = format_msg(
            # team history
            Msg(name="Summarizations of previous team discussions", role="user", content='')
            if team_history.size()>0 else None,
            team_history.get_memory(recent_n=platform.recent_n_team_mem_for_retrieve),
            # dialogue history
            Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
            if dialogue_history.size()>0 else None,
            dialogue_history.get_memory(recent_n=platform.group_max_discuss_iteration),
            # turn history
            Msg(name="Discussions in this turn", role="user", content='')
            if last_turn_history.size()>0 else None,
            last_turn_history.get_memory(recent_n=last_turn_history.size()),
            # answer_prompt
            Msg(name="user", role="user", content=Prompts.to_ask_if_ready_give_topic)
        )
        answer = platform.id2agent[self.teammate[0]].prompt_reply(answer_prompt, add_memory = False, use_memory=False)
        self.log_dialogue('user', platform.id2agent[self.teammate[0]].model.format(answer_prompt))
        self.log_dialogue(platform.id2agent[self.teammate[0]].name, answer.content)
        answer_pattern = re.compile(r'action\s*1', re.IGNORECASE)

        # update dialogue history
        dialogue_history.add(last_turn_summarization)
        dialogue_history.add(answer)

        # check whether agent is ready to answer
        if answer_pattern.search(answer.content) or team_history.size()>=1:
            self.state = 3
            history_prompt = format_msg(
                # team history
                Msg(name="Summarizations of previous team discussions", role="user", content='')
                if team_history.size()>0 else None,
                team_history.get_memory(recent_n=platform.recent_n_team_mem_for_retrieve),
                # dialogue history
                Msg(name="Summarizations of previous turns in current team discussion", role="user", content='')
                if dialogue_history.size()>0 else None,
                dialogue_history.get_memory(recent_n=platform.group_max_discuss_iteration),
                # turn history
                Msg(name="Discussions in this turn", role="user", content='')
                if last_turn_history.size()>0 else None,
                last_turn_history.get_memory(recent_n=last_turn_history.size()),
            )
            topic_prompt = format_msg(
                # answer,
                # topic_prompt
                Msg(name="user", role="user", content=Prompts.to_ask_topic.replace("[history_prompt]", formated_msg2str(history_prompt)))
            )
            topic = platform.id2agent[self.teammate[0]].prompt_reply(topic_prompt, add_memory = False)
            self.log_dialogue(self.teammate[0],topic.content)
            self.topic = extract_between_json_tags(topic.content,num=1)
            self.topic = strip_non_letters(self.topic.split("Topic")[1])

            # update dialogue history
            dialogue_history.add(topic)

        # update team_history
        history = format_msg(
            # team history
            Msg(name="Summarizations of previous team discussions", role="user", content='')
            if team_history.size()>0 else None,
            team_history.get_memory(recent_n=platform.recent_n_team_mem_for_retrieve)
        )
        team_history.add(Msg(name="summarizations of one topic discussion", role="user",
                             content=platform.id2agent[self.teammate[0]].summarize(history = history, content = dialogue_history.get_memory(recent_n=platform.group_max_discuss_iteration))))
        self.memory = team_history

    def generate_idea(self, platform):
        topic = self.topic
        old_idea = None
        best_idea = None
        idea_list = []
        mark_list = []
        # search related paper about the topic
        selected_topics = strip_non_letters(topic.split("Selected Topics:")[-1])
        paper_reference, cite_paper = platform.reference_paper(selected_topics, platform.cite_number)

        teammate = platform.id_to_agent(self.teammate)
        idea_judge = True

        if len(teammate)==1:
            group_max_discuss_iteration = platform.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = platform.group_max_discuss_iteration

        for turn in range(group_max_discuss_iteration):
            # discuss the idea
            for agent in teammate:
                idea_prompt = Prompts.prompt_task+Prompts.prompt_existing_idea.format(old_idea)+ \
                              Prompts.prompt_topic.format(selected_topics)+Prompts.prompt_reference.format(paper_reference)+ \
                              Prompts.prompt_response
                agent_prompt = format_msg(
                    # prompt
                    Msg(name="user", role="user", content=idea_prompt),
                )
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
                self.log_dialogue('user',idea_prompt)
                self.log_dialogue(agent.name,reply.content)
                old_idea = extract_between_json_tags(reply.content, num=1)
                if "Title" in old_idea:
                    idea_key = old_idea.split("Title")[1]
                    idea_key = strip_non_letters(idea_key.split("Experiment")[0])
                else:
                    idea_key = old_idea.split("Idea")[1]
                    idea_key = strip_non_letters(idea_key.split("Experiment")[0])
                paper_reference, cite_paper_new = platform.reference_paper(idea_key, platform.cite_number)
                cite_paper = list(set(cite_paper).union(cite_paper_new))

                # find the metric
                split_keywords = ['Clarity', 'Feasibility', 'Novelty']
                metrics = extract_metrics(old_idea, split_keywords)
                if best_idea != None:
                    if old_idea == best_idea:
                        idea_judge=True
                        print("exit early!!!!!!")
                        break
                    best_metrics = extract_metrics(best_idea, split_keywords)
                    old_count = 0
                    best_count = 0
                    for split_keywork in split_keywords:
                        if metrics[split_keyword]==None:
                            break
                        if split_keyword=='Novelty':
                            old_count = old_count + 2*metrics[split_keyword]
                        else:
                            old_count = old_count + metrics[split_keyword]
                        if best_metrics[split_keyword]==None:
                            break
                        best_count = best_count + best_metrics[split_keyword]
                    if old_count>=best_count:
                        best_idea = old_idea
                        idea_list.append(old_idea)
                        mark_list.append(old_count)
                else:
                    idea_list.append(old_idea)
                    best_idea = old_idea
                # if all metrics are larger than 8, then over
                for split_keyword in split_keywords:
                    if metrics[split_keyword]==None:
                        break
                    if metrics[split_keyword]<11:
                        idea_judge=False
                        break
                if idea_judge:
                    best_idea=old_idea
                    break
            if idea_judge:
                break
        if self.idea == None:
            if len(idea_list)>3:
                indices = top_three_indices(mark_list)
                idea_list = [idea_list[i] for i in indices]
                self.idea = idea_list
            else:
                self.idea = idea_list
        print("Candidate Idea:")
        print(self.idea)
        if platform.skip_check:
            self.state=5
        else:
            self.state=4
        self.citation_id = cite_paper
        print(len(self.citation_id))

    def check_novelty(self, platform):
        existing_idea = self.idea
        idea_choices = ""
        for idea_index in range(len(existing_idea)):
            idea = existing_idea[idea_index]
            idea_choices = idea_choices+"Idea "+str(idea_index)+":\n"+idea+"\n"
        related_papers = []
        for idea_index in existing_idea:
            title = idea_index.split("Title")[1]
            title = strip_non_letters(title.split("Experiment")[0])
            if len(existing_idea)==3:
                cite_number = 3
            else:
                cite_number = 5
            _, related_paper = platform.reference_paper(title, cite_number)

            related_papers = list(set(related_papers).union(related_paper))

        paper_reference = ""
        for id in range(len(related_papers)):
            paper_index = related_papers[id]
            paper_reference = paper_reference+"Paper {}:".format(id+1)+"\n"
            paper_reference = paper_reference+"Title: "+platform.paper_dicts[paper_index]['title']+"\n"
            paper_reference = paper_reference+"Abstract: "+platform.paper_dicts[paper_index]['abstract']+"}"+"\n"

        teammate = platform.id_to_agent(self.teammate)
        choice_list = []
        if len(teammate)==1:
            group_max_discuss_iteration = platform.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = platform.group_max_discuss_iteration
        for turn in range(group_max_discuss_iteration):
            # discuss the idea
            for agent in teammate:
                idea_novelty_prompt = Prompts.prompt_idea_check+Prompts.prompt_idea_check_response.replace("{existing_idea}", idea_choices).replace("{last_query_results}",paper_reference)
                agent_prompt = format_msg(
                    # prompt
                    Msg(name="user", role="user", content=idea_novelty_prompt),
                )
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
                self.log_dialogue('user',idea_novelty_prompt)
                self.log_dialogue(agent.name,reply.content)
                old_idea = extract_between_json_tags(reply.content, num=1)
                idea_choice = extract_first_number(old_idea)
                if idea_choice == None:
                    idea_choice = 0
                choice_list.append(int(idea_choice))

        final_choice = most_frequent_element(choice_list)
        if final_choice<0 or final_choice>=len(existing_idea):
            final_choice = len(existing_idea)-1
        try:
            self.idea = existing_idea[final_choice]
        except:
            self.idea = existing_idea[0]
        print("Final Idea:")
        print(self.idea)
        self.state=5

    def generate_abstract(self, platform):
        idea = self.idea
        old_abstract = self.abstract
        teammate = platform.id_to_agent(self.teammate)

        if len(teammate)==1:
            group_max_discuss_iteration = platform.group_max_discuss_iteration
        else:
            group_max_discuss_iteration = platform.group_max_discuss_iteration

        for turn in range(group_max_discuss_iteration):
            # discuss the abstract
            for agent in teammate:
                if old_abstract == None:
                    abstract_prompt = Prompts.prompt_abstract+"\n"+idea+ \
                                      "\n"+Prompts.prompt_abstract_requirement+"\n"+Prompts.prompt_abstract_response
                else:
                    # the paper is not reviewed by reviewer
                    if self.paper_review == None:
                        # the paper is not reviewer by the team member
                        if self.self_review == None:
                            prompt_abstract_judgement = Prompts.prompt_abstract_judgement.replace("[Insert abstract here]",old_abstract)
                            abstract_prompt = prompt_abstract_judgement+Prompts.prompt_abstract_revise_response
                        else:
                            prompt_abstract_judgement = Prompts.prompt_abstract_judgement_self.replace("[Insert abstract here]",old_abstract)
                            prompt_abstract_judgement = prompt_abstract_judgement.replace("[Insert self_review comments]", self.self_review)
                            abstract_prompt = prompt_abstract_judgement+Prompts.prompt_abstract_revise_response
                    else:
                        prompt_abstract_judgement = Prompts.prompt_abstract_judgement_after_review.replace("[Insert Reviewer comments]",self.paper_review)
                        prompt_abstract_judgement = prompt_abstract_judgement.replace("[Insert abstract here]",old_abstract)
                        abstract_prompt = prompt_abstract_judgement+Prompts.prompt_abstract_revise_response
                agent_prompt = format_msg(
                    # prompt
                    Msg(name="user", role="user", content=abstract_prompt),
                )
                reply = agent.prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
                self.log_dialogue(agent.name, reply.content)
                old_abstract = extract_between_json_tags(reply.content, num=1)
                if old_abstract == None:
                    old_abstract = reply.content

        related_papers = []

        Abstract = strip_non_letters(old_abstract.split("Abstract")[1])
        query_vector = ollama.embeddings(model="mxbai-embed-large", prompt=Abstract)
        query_vector = np.array([query_vector['embedding']])

        D_future, I_future = platform.gpu_future_index.search(query_vector, int(platform.cite_number/2))
        D, I = platform.gpu_index.search(query_vector, int(platform.cite_number/2))

        for id in range(len(I_future[0])):
            paper_title = platform.paper_future_dicts[I_future[0][id]]['title']
            paper_abstract = platform.paper_future_dicts[I_future[0][id]]['abstract']
            paper_year = platform.paper_future_dicts[I_future[0][id]]['year']
            paper_citation = platform.paper_future_dicts[I_future[0][id]]['citation']
            paper_index = {}
            paper_index['title'] = paper_title
            paper_index['abstract'] = paper_abstract
            paper_index['year'] = paper_year
            paper_index['citation'] = paper_citation
            related_papers.append(paper_index)

        for id in range(len(I[0])):
            paper_title = platform.paper_dicts[I[0][id]]['title']
            paper_abstract = platform.paper_dicts[I[0][id]]['abstract']
            paper_year = platform.paper_dicts[I[0][id]]['year']
            paper_citation = platform.paper_dicts[I[0][id]]['citation']
            paper_index = {}
            paper_index['title'] = paper_title
            paper_index['abstract'] = paper_abstract
            paper_index['year'] = paper_year
            paper_index['citation'] = paper_citation
            related_papers.append(paper_index)

        # eval with embedding similarity
        abs = []
        our_abs = strip_non_letters(old_abstract.split('Abstract')[1])
        abs.append(ollama.embeddings(model="mxbai-embed-large", prompt=our_abs)['embedding'])
        for paper_id in range(int(platform.cite_number/2), len(related_papers)):
            related_astract = related_papers[paper_id]['abstract']
            abs.append(ollama.embeddings(model="mxbai-embed-large", prompt=related_astract)['embedding'])

        sim = []
        for emb_id in range(1, len(abs)):
            sim.append(torch.nn.functional.cosine_similarity(torch.tensor(abs[0]).unsqueeze(0),
                                                             torch.tensor(abs[emb_id]).unsqueeze(0), dim=-1)[0].item())
        self.log_dialogue('embedding similarity', str(sim))

        self.log_dialogue('faiss_distance', str(D))
        self.log_dialogue('faiss_distance_future', str(D_future))

        # eval with LLM
        print('related papers:')
        print(len(related_papers))
        if len(related_papers)>0:
            self.log_dialogue('arxiv',related_papers)
        # find paper successfully
        if len(related_papers)>0:
            abstract_check_prompt = Prompts.prompt_abstract_check.replace("[Insert your abstract here]", old_abstract)
            cite_abstract = ""
            # word = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T']
            word = ['A', 'B', 'C', 'D']
            split_keywords = []
            for paper_id in range(int(platform.cite_number/2), len(related_papers)):
                cite_abstract = cite_abstract + str(paper_id-int(platform.cite_number/2)+1) + ". Abstract {}: ".format(word[paper_id-int(platform.cite_number/2)]) + "Title: " + related_papers[paper_id]['title'] + "\n" + "Abstract: " + related_papers[paper_id]['abstract'] + "\n"
                split_keywords.append('Written Abstract vs {}'.format(word[paper_id-int(platform.cite_number/2)]))
            abstract_check_prompt = abstract_check_prompt.replace("[Insert ref abstract here]", cite_abstract)
            abstract_check_prompt = abstract_check_prompt + "\n" + Prompts.prompt_response_check
            
            agent_prompt = format_msg(
                # prompt
                Msg(name="user", role="user", content=abstract_check_prompt),
            )
            reply = teammate[0].prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
            self.log_dialogue(teammate[0].name, reply.content)
            print("abstract_check:")
            print(split_keywords)
            comparison = extract_between_json_tags(reply.content)
            metric = extract_metrics(comparison, split_keywords=split_keywords)
            abstract_use = True
            for split_keyword in split_keywords:
                if metric[split_keyword]>=70:
                    abstract_use = False
                    self.abstract = old_abstract
                    break
            self.abstract = old_abstract
            print('Final Abstract:')
            print(self.abstract)
            # stop early
            self.state=7

            # do not stop early

            # if abstract_use:
            #     team.state=6
            #     team.self_review=None
            # # if the abstract is too similar one time, go to revise, otherwise back to generate idea
            # else:
            #     if team.self_review!=None:
            #         team.state=3
            #         team.idea = None
            #         team.abstract = None
            #         team.citation_id = None
            #         team.self_review = None
            #         team.paper_review = None
            #     else:
            #         team.self_review = reply.content

        else:
            print('Check Fail!!!!!!')
            if self.abstract == None:
                self.abstract = old_abstract
                print('Final Abstract:')
                print(self.abstract)
                self.state=6

    def generate_review(self, platform):
        # paper reviewer by reviewer
        print('current reviewing paper from {}'.format(self.teammate))
        old_abstract = self.abstract
        prompt = Prompts.prompt_review_require_simple.replace("{paper}", old_abstract)
        mark_sum = 0
        self.paper_review==None
        for _ in range(platform.reviewer_num):
            agent_prompt = format_msg(
                # prompt
                Msg(name="user", role="user", content=prompt),
            )
            reply = platform.reviewer_pool[_].prompt_reply(agent_prompt, add_memory = False, use_memory = False, use_RAG=False)
            self.log_dialogue(platform.reviewer_pool[_].name, reply.content)
            split_keywords = ['Overall']
            metric = extract_metrics(reply.content, split_keywords)
            if self.paper_review == None:
                self.paper_review = platform.reviewer_pool[_].name+":\n"+reply.content
            else:
                self.paper_review = self.paper_review+"\n"+platform.reviewer_pool[_].name+":\n"+reply.content
            for split_keyword in split_keywords:
                if metric[split_keyword] == None:
                    mark_sum = mark_sum + platform.default_mark
                else:
                    mark_sum = mark_sum + metric[split_keyword]
        if mark_sum>=(5*platform.reviewer_num):
            print('paper accept!!!!!!')
            self.state=platform.over_state
            title = old_abstract.split("Abstract")[0]
            title = strip_non_letters(title.split("Title")[1])
            abstract = strip_non_letters(old_abstract.split("Abstract")[1])
            file_dict={}
            file_dict['title']=title
            file_dict['abstract']=abstract
            file_dict['id'] = len(platform.paper_dicts)
            file_dict['authors'] = self.teammate
            file_dict['cite_papers'] = self.citation_id
            platform.paper_dicts.append(file_dict)
            # add embedding into list
            embedding_list = []
            response = ollama.embeddings(model="mxbai-embed-large", prompt=abstract)
            embedding_list.append(response["embedding"])
            response = np.array(embedding_list)
            platform.gpu_index.add(response)
        else:
            self.state = 5

    def log_dialogue(self, name, content):
        self.logger.info(f'Epoch:{self.epoch} | {self.state_log[self.state]} | {name}:{content}')
        self.logger.info(f'{"="*40}')

    def save_team_info(self):
        team_info = {
            'teammate':self.teammate,
            'topic':self.topic,
            'idea':self.idea,
            'abstract':self.abstract
        }
        print(f'{"="*20} SAVE TEAM INFO {"="*20}')
        with open(self.info_file, 'w') as json_file:
            json.dump(team_info, json_file, indent=4)

if __name__=='__main__':
    team1 = Team('LPL')
    team2 = Team('LCK')
    team1.log_dialogue('sam', 'LPL win!')
    team2.log_dialogue('tom', 'LCK win!')
    team1.log_dialogue('sam', 'LPL win again !')
    team2.log_dialogue('tom', 'LCK win again !')
