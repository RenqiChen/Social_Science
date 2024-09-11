# -*- coding: utf-8 -*-
"""Used to record prompts, will be replaced by configuration"""

class Prompts:
    """Prompts for werewolf game"""

    ask_choice = (
        "{Scientist_name}, now you are at the team: {All_team}. Now you have two choices after considering your current teams: "
        "Action 1: You choose to collaborate with some partners, sharing insights, dividing tasks, and combining your expertise to produce a comprehensive paper."
        "Action 2: You decide to write the paper independently, relying on your own research and analysis to complete the work."
        "Please select an action and describe your reasoning using the following format:"
        "Selected Action: [Action 1 or Action 2]."
        "Reasoning: [Explain why you chose this action, considering factors like the potential for quality, efficiency, and the challenges involved.]"
    )

    to_scientist_select = "Who will you want to select as your partners?"
    "Please provide their names in the following format: "
    "Partners: Name1, Name2, Name3, ..."


    to_scientist_choice = (
        "{inviter_name} invites you to join his team. His personal information is as follows:"
        "{personal information}. Now you have two choices after considering his information: "
        "Action 1: You choose to collaborate with {inviter_name}."
        "Action 2: You choose to refuse the invitation from {inviter_name}."
        "Please feel free to make your choice, even if your choice is to decline."
        "Please select an action and describe your reasoning using the following format:"
        "Selected Action: [Action 1 or Action 2]."
        "Reasoning: [Explain why you chose this action, considering factors like the potential for quality, efficiency, and the challenges involved.]"
    )

    to_start_topic_discussion = """Engage in a collaborative discussion to explore and identify potential research topics that align with our team's strengths and goals.
    Please focus more on the discussion of the topic rather than on self-introduction.
    """
    
    # To do
    
    to_start_add_author = "Engage in a collaborative discussion to explore and identify potential collaborators "
    "that align with our team's strengths and goals. Please note that you may paraphrase others' opinions, "
    "but you cannot fully replicate their statements. Please remember your own role and do not answer questions on behalf of others."

    to_ask_if_ready_add_authors = "Your team has discussed a couple of turns to find more potential collaborators." \
                                 "Now you have to decide whether you are ready to invite potential collaborators to join your team, you have two choices:" \
                                 "Action 1: You think your team needs more collaborators." \
                                 "Action 2: You think your team does not need more collaborators." \
                                 "Please select an action and describe your reasoning using the following format:" \
                                 "Selected Action: [Action 1 or Action 2]." \
                                 "Reasoning: [Explain why you chose this action.]"

    to_scientist_choice_add_author = (
        "{inviter_name} invites you to join his team. His personal information is as follows:"
        "{personal information}. His team includes teammates: {team_list}."
        "In previous, {inviter_name}'s team discussed the topic selection: {team_memory}"
        "Now you have two choices after considering these information: "
        "Action 1: You choose to collaborate with {inviter_name}."
        "Action 2: You choose to refuse the invitation from {inviter_name}."
        "Please select an action and describe your reasoning using the following format:"
        "Selected Action: [Action 1 or Action 2]."
        "Reasoning: [Explain why you chose this action.]"
    )

    to_ask_if_ready_give_topic = """Your team has discussed a couple of turns to select the topic. 
                                 "Now you have to decide whether your are ready to select potential research topics, you have two choices: 
                                 "Action 1: You think you are ready to select research topics. 
                                 "Action 2: You think your team need more discussions to decide which topics to select. 
                                 "Please note that although thorough discussion can lead to a better topic,
                                 "confirm the topic early is beneficial for advancing the subsequent work.
                                 "Please balance both aspects and provide a decision. 
                                 "Please select an action and describe your reasoning using the following format:
                                 "Selected Action: [Action 1 or Action 2].
                                 "Reasoning: [Explain why you chose this action.]"""

    to_ask_topic = "Please give me the topic you select using the following format: "\
    "Selected Topics: Topic 1"

    prompt_existing_idea = "Here are the ideas that your team has already generated: '''{}'''\n"

    prompt_task = "Improve this idea or come up with the next impactful and creative idea for publishing a paper that will contribute significantly to the field."+"\n"
    
    prompt_topic = ("When proposing your idea, please elaborate on the proposed topic: {}\n")
    
    prompt_reference = """You may refer to the following listed references to design a new idea or concept. 
    These references can serve as inspiration, but you are not allowed to directly copy or replicate their content. 
    Ensure that your design is original and addresses a specific problem or meets a unique need. orporating and improving upon the ideas from the references.
    References: {}\n
    """
    
    prompt_response = ("""
    "Please respond in the following format: 

    Thought: <THOUGHT> 

    New Idea: ```json<JSON>```

    In <THOUGHT>, first briefly discuss your intuitions and motivations for the idea. 
    Detail your high-level plan, necessary design choices and ideal outcomes of the experiments. 
    Justify how the idea is different from the existing ones. 

    In <JSON>, provide the new idea with the following fields and provide as many details as possible: 
    - "Idea": A detailed description of the idea. 
    - "Title": A title for the idea, will be used for the report writing. 
    - "Experiment": An outline of the implementation. E.g. which functions need to be added or modified, how results will be obtained, ...
    - "Interestingness": A rating from 1 to 10 (lowest to highest).
    - "Feasibility": A rating from 1 to 10 (lowest to highest). 
    - "Novelty": A rating from 1 to 10 (lowest to highest). 

    Be cautious and realistic on your ratings. This JSON will be automatically parsed, so ensure the format is precise, and the content should be longer than 600 words. You only need to output one idea.
    """)

    prompt_abstract = """Based on the following research idea. Generate a concise and informative abstract for a scientific paper.""" 

    prompt_abstract_requirement = """The abstract should cover the following aspects:

    - "Introduction": Briefly introduce the research topic and its significance.
    - "Objective": Clearly state the main research question or hypothesis.
    - "Methods": Summarize the key methodologies used in the study.
    - "Results": Highlight the most important findings.
    - "Conclusion": Provide the primary conclusion and its implications.

    Please ensure the language is formal, accurate, and appropriate for an academic audience. And the generated abstract should be longer than 200 words.
    """

    prompt_abstract_response = """The response format should be:
    ```json
    {
    Title: <TITLE>

    Abstract: <ABSTRACT>
    }
    ```
    This JSON will be automatically parsed, so ensure the format is precise.
    """

    prompt_abstract_judgement = """
    Evaluate the following scientific paper abstract based on the following criteria:

    1. **Clarity**: Is the abstract clear and easy to understand? 
    2. **Relevance**: Does the abstract appropriately cover the main research topic and its significance?
    3. **Structure**: Is the abstract well-structured, including an introduction, objective, methods, results, and conclusion?
    4. **Conciseness**: Is the abstract succinct without unnecessary details, yet comprehensive enough to summarize the key aspects of the research?
    5. **Technical Accuracy**: Are the scientific terms and methodologies correctly presented and accurately described?
    6. **Engagement**: Does the abstract engage the reader and encourage further reading of the full paper?
    7. **Originality**: Does it introduce new ideas, methods, or models? Are the data or experiments unique to the field? How does it extend or differ from existing research?
    8. **Overall Score**: The overall rating of this paper.

    Provide a brief evaluation of each criterion by providing a rating from 1 to 10 (lowest to highest) and revise the abstract. Please note that your revised abstract should be longer than 200 words.

    **Original Abstract**: [Insert abstract here]
    """

    prompt_abstract_judgement_self = """
    Evaluate the following scientific paper abstract based on the following criteria:

    1. **Clarity**: Is the abstract clear and easy to understand? 
    2. **Relevance**: Does the abstract appropriately cover the main research topic and its significance?
    3. **Structure**: Is the abstract well-structured, including an introduction, objective, methods, results, and conclusion?
    4. **Conciseness**: Is the abstract succinct without unnecessary details, yet comprehensive enough to summarize the key aspects of the research?
    5. **Technical Accuracy**: Are the scientific terms and methodologies correctly presented and accurately described?
    6. **Engagement**: Does the abstract engage the reader and encourage further reading of the full paper?
    7. **Originality**: Does it introduce new ideas, methods, or models? Are the data or experiments unique to the field? How does it extend or differ from existing research?
    8. **Overall Score**: The overall rating of this paper.

    Provide a brief evaluation of each criterion by providing a rating from 1 to 10 (lowest to highest) and revise the abstract. Please note that your revised abstract should be longer than 200 words.

    Moreover, when making revisions, please consider the following evaluations about originality check.

    **Originality Check**: [Insert self_review comments]

    **Original Abstract**: [Insert abstract here]
    """

    prompt_abstract_judgement_after_review = """
    Please use the following peer review feedback to revise the research paper. 
    Ensure that the revisions address each of the reviewers' comments and suggestions, while maintaining the overall coherence and quality of the paper. 
    Please note that your revised abstract should be longer than 200 words.

    **Peer Review Feedback**: [Insert Reviewer comments]

    **Original Abstract**: [Insert abstract here]
    """

    prompt_abstract_revise_response = """The response format should be:
    **Revised Abstract**

    ```json
    Title: <TITLE>

    Abstract: <ABSTRACT>
    ```
    This JSON will be automatically parsed, so ensure the format is precise.
    """

    prompt_abstract_check = """
    Please compare the following written abstract with the five provided abstracts:

    - Written Abstract: [Insert your abstract here]

    Provided Abstracts:
    [Insert ref abstract here]

    For each pair (Written Abstract vs A, Written Abstract vs B, etc.), calculate a similarity score between 0 and 100, where 0 means no overlap and 100 means identical content. 
    The score should be based on content, structure, and phrasing. Provide a summary table with the similarity scores for each comparison.
    """

    prompt_response_check = """
    The response should follow this format:

    ```json
    {
    "similarity_scores": {
        "Written Abstract vs A": [Similarity Score],
        "Written Abstract vs B": [Similarity Score],
        "Written Abstract vs C": [Similarity Score],
        "Written Abstract vs D": [Similarity Score],
        "Written Abstract vs E": [Similarity Score],
        "Written Abstract vs F": [Similarity Score],
        ...
        "Written Abstract vs H": [Similarity Score]
    },
    "high_overlap_pairs": [
        {
        "pair": "Written Abstract vs [Abstract Letter]",
        "score": [Similarity Score],
        "reason": "[Explain key areas of overlap in content, structure, or phrasing]"
        }
    ]
    }
    ```
    """

    prompt_review_system = """
    You are a researcher who is reviewing a paper that was submitted to a prestigious science venue. 
    Be critical and cautious in your decision. If a paper is bad or you are unsure, give it bad scores and reject it.
    """

    prompt_review_require = """
    ## Review Form
     
    Below is a description of the questions you will be asked on the review form for each paper and some guidelines on what to consider when answering these questions. 
    Moreover, you need to provide your decision on whether to accept or reject. When writing your review, please keep in mind that after decisions have been made, reviews of accepted papers and opted-in rejected papers will be made public.
    
    ## Reviewer Guiderlines:

    1. Summary: Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.
    2. Strengths and Weaknesses: Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions:
        - Originality: Are the tasks or methods new? Is the work a novel combination of well-known techniques? (This can be valuable!) Is it clear how this work differs from previous contributions? Is related work adequately cited
        - Quality: Is the submission technically sound? Are claims well supported (e.g., by theoretical analysis or experimental results)? Are the methods used appropriate? Is this a complete piece of work or work in progress? Are the authors careful and honest about evaluating both the strengths and weaknesses of their work
        - Clarity: Is the submission clearly written? Is it well organized? (If not, please make constructive suggestions for improving its clarity.) Does it adequately inform the reader? (Note that a superbly written paper provides enough information for an expert reader to reproduce its results.)
        - Significance: Are the results important? Are others (researchers or practitioners) likely to use the ideas or build on them? Does the submission address a difficult task in a better way than previous work? Does it advance the state of the art in a demonstrable way? Does it provide unique data, unique conclusions about existing data, or a unique theoretical or experimental approach?
    3. Questions: Please list up and carefully describe any questions and suggestions for the authors. Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. This can be very important for a productive rebuttal and discussion phase with the authors.  
    4. Limitations: Have the authors adequately addressed the limitations and potential negative societal impact of their work? If not, please include constructive suggestions for improvement.
    In general, authors should be rewarded rather than punished for being up front about the limitations of their work and any potential negative societal impact. You are encouraged to think through whether any critical points are missing and provide these as feedback for the authors.
    5. Ethical concerns: If there are ethical issues with this paper, please flag the paper for an ethics review.
    6. Soundness: Please assign the paper a numerical rating on the following scale to indicate the soundness of the technical claims, experimental and research methodology and on whether the central claims of the paper are adequately supported with evidence.
        - 4 excellent
        - 3 good
        - 2 fair
        - 1 poor
    7. Presentation: Please assign the paper a numerical rating on the following scale to indicate the quality of the presentation. This should take into account the writing style and clarity, as well as contextualization relative to prior work.
        - 4 excellent
        - 3 good
        - 2 fair
        - 1 poor
    8. Contribution: Please assign the paper a numerical rating on the following scale to indicate the quality of the overall contribution this paper makes to the research area being studied. Are the questions being asked important? Does the paper bring a significant originality of ideas and/or execution? Are the results valuable to share with the broader NeurIPS community.
        - 4 excellent
        - 3 good
        - 2 fair
        - 1 poor
    9. Overall: Please provide an "overall score" for this submission. Choices:
        - 10: Award quality: Technically flawless paper with groundbreaking impact on one or more areas of AI, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.
        - 9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI and excellent impact on multiple areas of AI, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations.
        - 8: Strong Accept: Technically strong paper with, with novel ideas, excellent impact on at least one area of AI or high-to-excellent impact on multiple areas of AI, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations.
        - 7: Accept: Technically solid paper, with high impact on at least one sub-area of AI or moderate-to-high impact on more than one area of AI, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations.
        - 6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations.
        - 5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.
        - 4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.
        - 3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations.
        - 2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations.
        - 1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations
    10. Confidence:  Please provide a "confidence score" for your assessment of this submission to indicate how confident you are in your evaluation.  Choices
        - 5: You are absolutely certain about your assessment. You are very familiar with the related work and checked the math/other details carefully.
        - 4: You are confident in your assessment, but not absolutely certain. It is unlikely, but not impossible, that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work.
        - 3: You are fairly confident in your assessment. It is possible that you did not understand some parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.
        - 2: You are willing to defend your assessment, but it is quite likely that you did not understand the central parts of the submission or that you are unfamiliar with some pieces of related work. Math/other details were not carefully checked.
        - 1: Your assessment is an educated guess. The submission is not in your area or the submission was difficult to understand. Math/other details were not carefully checked.

    ## Examples:
    
    "Summary": "The paper introduces an adaptive dual-scale denoising approach for low-dimensional diffusion models, aiming to balance global structure and local details in generated samples. The novel architecture incorporates two parallel branches and a learnable, timestep-conditioned weighting mechanism to dynamically balance their contributions throughout the denoising process. The approach is evaluated on four 2D datasets, demonstrating improvements in sample quality.", 
    "Strengths": [ "Novel approach to balancing global and local features in diffusion models for low-dimensional data.", "Comprehensive empirical evaluation on multiple 2D datasets.", "Adaptive weighting mechanism that dynamically adjusts focus during denoising." ], 
    "Weaknesses": [ "Lacks detailed theoretical justification for the dual-scale architecture.", "Computational cost is significantly higher, which may limit practical applicability.", "Some sections are not clearly explained, such as the autoencoder aggregator and weight evolution analysis.", "Limited diversity in the datasets used for evaluation. More complex, real-world datasets could strengthen claims.", "Insufficient ablation studies and analysis on specific design choices like different types of aggregators." ], 
    "Originality": 4, 
    "Quality": 3, 
    "Clarity": 3, 
    "Significance": 3,
    "Questions": [ "Can you provide a more detailed theoretical justification for the dual-scale architecture?", "What impact do different types of aggregators have on the model's performance?", "How does the model perform on more complex, real-world low-dimensional datasets?", "Can the computational cost be reduced without sacrificing performance?" ], 
    "Limitations": [ "The paper should address the high computational cost and explore ways to optimize it.", "The limited diversity of datasets and lack of detailed theoretical backing for the proposed architecture are notable limitations." ], 
    "Ethical Concerns": false, 
    "Soundness": 3,
    "Presentation": 3, 
    "Contribution": 3, 
    "Overall": 5, 
    "Confidence": 4, 
    "Decision": "Reject"

    Here is the paper you are asked to review:
    ```
    {paper} 
    ```
    """

    prompt_review_require_simple = """
    ## Review Form
     
    Below is a description of the questions you will be asked on the review form for each paper and some guidelines on what to consider when answering these questions.
    
    ## Reviewer Guiderlines:

    1. Summary: Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.
    2. Strengths and Weaknesses: Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions:
        - Originality: Are the tasks or methods new? Is the work a novel combination of well-known techniques? (This can be valuable!) 
        Is it clear how this work differs from previous contributions?
        - Quality: Is the submission technically sound? Are claims well supported 
        (e.g., by theoretical analysis or experimental results)? Are the methods used appropriate? 
        Is this a complete piece of work or work in progress? Are the authors careful and honest about evaluating both the strengths and weaknesses of their work.
        - Clarity: Is the submission clearly written? Is it well organized? 
        (If not, please make constructive suggestions for improving its clarity.) 
        Does it adequately inform the reader? (Note that a superbly written paper provides enough information for an expert reader to reproduce its results.)
        - Significance: Are the results important? Are others (researchers or practitioners) likely to use the ideas or build on them? 
        Does the submission address a difficult task in a better way than previous work? Does it advance the state of the art in a demonstrable way? 
        Does it provide unique data, unique conclusions about existing data, or a unique theoretical or experimental approach?
    3. Questions: Please list up and carefully describe any questions and suggestions for the authors. 
    Think of the things where a response from the author can change your opinion, clarify a confusion or address a limitation. 
    This can be very important for a productive rebuttal and discussion phase with the authors.  
    4. Ethical concerns: If there are ethical issues with this paper, please flag the paper for an ethics review.
    5. Overall: Please provide an "overall score" for this submission. Choices:
        - 10: Award quality: Technically flawless paper with groundbreaking impact on one or more areas of AI, with exceptionally strong evaluation, reproducibility, and resources, and no unaddressed ethical considerations.
        - 9: Very Strong Accept: Technically flawless paper with groundbreaking impact on at least one area of AI and excellent impact on multiple areas of AI, with flawless evaluation, resources, and reproducibility, and no unaddressed ethical considerations.
        - 8: Strong Accept: Technically strong paper with, with novel ideas, excellent impact on at least one area of AI or high-to-excellent impact on multiple areas of AI, with excellent evaluation, resources, and reproducibility, and no unaddressed ethical considerations.
        - 7: Accept: Technically solid paper, with high impact on at least one sub-area of AI or moderate-to-high impact on more than one area of AI, with good-to-excellent evaluation, resources, reproducibility, and no unaddressed ethical considerations.
        - 6: Weak Accept: Technically solid, moderate-to-high impact paper, with no major concerns with respect to evaluation, resources, reproducibility, ethical considerations.
        - 5: Borderline accept: Technically solid paper where reasons to accept outweigh reasons to reject, e.g., limited evaluation. Please use sparingly.
        - 4: Borderline reject: Technically solid paper where reasons to reject, e.g., limited evaluation, outweigh reasons to accept, e.g., good evaluation. Please use sparingly.
        - 3: Reject: For instance, a paper with technical flaws, weak evaluation, inadequate reproducibility and incompletely addressed ethical considerations.
        - 2: Strong Reject: For instance, a paper with major technical flaws, and/or poor evaluation, limited impact, poor reproducibility and mostly unaddressed ethical considerations.
        - 1: Very Strong Reject: For instance, a paper with trivial results or unaddressed ethical considerations

    ## Examples:
    
    "Summary": "The paper introduces an adaptive dual-scale denoising approach for low-dimensional diffusion models, aiming to balance global structure and local details in generated samples. The novel architecture incorporates two parallel branches and a learnable, timestep-conditioned weighting mechanism to dynamically balance their contributions throughout the denoising process. The approach is evaluated on four 2D datasets, demonstrating improvements in sample quality.", 
    "Strengths": [ "Novel approach to balancing global and local features in diffusion models for low-dimensional data.", "Comprehensive empirical evaluation on multiple 2D datasets.", "Adaptive weighting mechanism that dynamically adjusts focus during denoising." ], 
    "Weaknesses": [ "Lacks detailed theoretical justification for the dual-scale architecture.", "Computational cost is significantly higher, which may limit practical applicability.", "Some sections are not clearly explained, such as the autoencoder aggregator and weight evolution analysis.", "Limited diversity in the datasets used for evaluation. More complex, real-world datasets could strengthen claims.", "Insufficient ablation studies and analysis on specific design choices like different types of aggregators." ], 
    "Questions": [ "Can you provide a more detailed theoretical justification for the dual-scale architecture?", "What impact do different types of aggregators have on the model's performance?", "How does the model perform on more complex, real-world low-dimensional datasets?", "Can the computational cost be reduced without sacrificing performance?" ], 
    "Ethical Concerns": false, 
    "Overall": 5

    Here is the paper you are asked to review:
    ```
    {paper} 
    ```
    """

    