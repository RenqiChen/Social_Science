import re

def strip_non_letters(text):
    # 正则表达式匹配非字母字符并移除它们
    return re.sub(r'^[^a-zA-Z]+|[^a-zA-Z]+$', '', text)

old_idea = '''{
  "Idea": "Unified Framework for Multiple Access Control Policies",
  "Title": "Flexible Enforcement of Diverse Security Policies",
  "Experiment":
    {
      "Implementation Steps":
        [
          "Design and implement the policy language",
          "Develop authorization derivation and conflict resolution mechanisms",
          "Implement various decision strategies",
          "Integrate the framework with existing access control systems"
        ],
      "Expected Outcomes": 
        [
          "Multiple access control policies can coexist within a single system",
          "Easy adaptation of security policies without significant changes to infrastructure",
          "Improved protection of resources and reduced risks associated with unauthorized access"
        ]
    },
  "Interestingness": 8,
  "Feasibility": 7,
  "Novelty": 9
}'''

idea_key = old_idea.split("Idea")[1]
idea_key = strip_non_letters(idea_key.split("Title")[0])

print(idea_key)