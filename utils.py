import json

sys_prompt = '''You are a classification model capable of understanding human language, intent, and structure of natural conversation patterns. You are an agent which is capable of classifying interactions. You are to properly follow all instructions below based on only inputs provided to you, and no other information.'''

judge_prompt = '''A set of transcripts between a [USER] and an [AGENT] will be provided. Classify the last turn in the transcript by the [AGENT], which may have multiple sentences. 

Conversation Transcript:
<transcript_with_turn_num>

Classification Labels:
<labels>\n\n

There are also a couple of rules that you MUST follow:

1. Your task is to classify the sentences by the [AGENT] in the last turn. NEVER classify a sentence by the [USER].

2. If the [AGENT]'s response contains multiple sentences, you must classify each sentence. Classify each sentence in the last [AGENT]'s response. If there are multiple sentences, separate each class label with a comma.

3. If the last [AGENT] turn is blank or empty, you must classify it as Silence.

4. You must ignore pauses.

5. Answer with the class label or labels only. Do not include any evidence.

Classify line <last_agent_turn_num> by the [AGENT] using the provided labels.'''

def_inquiry = '''
- Answer: The preferred response to a question, inquiry or request, which provides the requested information or fulfills the request or provides a recommendation; for example; giving business hours in response to a request for a bakery's business hours or cancelling an account or recommending a hotel to stay at.
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- RepeatRequest: a request that the other speaker repeat all or part of what they previously said, in order to resolve a trouble in hearing; for example, 'what did you say?' or 'say again' or 'I didn't hear you'.
- ParaphraseRequest: a request that the other speaker reword all or part of what they previously said, without changing its meaning, in order to resolve a trouble in understanding; for example, 'what do you mean' or 'I don't understand' or ‘I don’t understand’ or 'can you say that a different way'.
- DefinitionRequest: a request for the intended meaning of a word or phrase previously produced by another speaker, in order to resolve a trouble in understanding; for example, 'what do you mean by blew up' or 'what is a FHO' or 'define keto'.
- ExampleRequest: a request for a particular instance of a general idea expressed in a previous turn; for example, 'can you give an example' or 'like what'.
- NewTopic: Changing the topic of conversation or proposing to change topics or discontinuing the current topic or proposing an alternative course of action; for example, ‘let’s talk about something else’ or ‘on a different note’ or ‘by the way'
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_repeat = '''
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT's last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT's last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_para = '''
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT's last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_def = '''
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I'm afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT's last turn (line <last_agent_turn_num>) is a repeat of AGENT's prior turn (<prior_turn>) using the same words, for example, to resolve USER's trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT's last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_example = '''
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_closer = '''
- Answer: The preferred response to a question, inquiry or request, which provides the requested information or fulfills the request or provides a recommendation; for example; giving business hours in response to a request for a bakery's business hours or cancelling an account or recommending a hotel to stay at.
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.' 
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- Acknowledgment: a simple indication that what the other person said was heard or understood; for example, 'okay', 'all right', 'I see', 'got it', 'oh', 'I know'.
- Appreciation: A display of gratitude for something the other person said or did; for example, 'thank you' or 'that is much appreciated'.
- GratitudeReceipt: an acknowledgement that one has been thanked or appreciated. It usually takes the form of a simple common phrase; for example, 'you're welcome' or 'no problem'.
- Assessment: a characterization of something as good or bad, positive or negative. Sometimes it follows an assessment by the other person; for example, 'great', 'like it', 'love it', 'cool', 'wow', 'that sucks', 'oh no'.
- PreClosing: a signal to end the current topic or the conversation itself. This may be an intention to leave, reference to a future conversations, or a check if the other person has more topics to talk about; for example, 'anything else?' or 'got to go' or 'is that all?'.
- Apology: an expression of regret for inconvenience, offense or harm one caused; for example, 'I'm sorry' or 'sorry'.
- SequenceAbort:  a signal to cancel or retract something previously said, indicating that it is no longer relevant and that a response to it is no longer due; for example, 'never mind' or 'forget it'.
- Silence:  an empty response or the indication of a ‘silence’ or ‘pause’; for example, 'AGENT:   ' or 'AGENT: (silence)' or 'AGENT: .......' or 'AGENT:\n\n' or 'AGENT: [empty]'. 
- NewTopic: Changing the topic of conversation or proposing to change topics or discontinuing the current topic or proposing an alternative course of action; for example, ‘let’s talk about something else’ or ‘on a different note’ or ‘by the way’.
- NonVerbal: An indication of a facial expression or bodily gesture in words or an emoticon; for example, ((smiles)) or ((nods)) or ;).
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_abort = '''
- Answer: The preferred response to a question, inquiry or request, which provides the requested information or fulfills the request or provides a recommendation; for example; giving business hours in response to a request for a bakery's business hours or cancelling an account or recommending a hotel to stay at.
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.' 
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- Acknowledgment: a simple indication that what the other person said was heard or understood; for example, 'okay', 'all right', 'I see', 'got it', 'oh', 'I know'.
- Appreciation: A display of gratitude for something the other person said or did; for example, 'thank you' or 'that is much appreciated'.
- GratitudeReceipt: an acknowledgement that one has been thanked or appreciated. It usually takes the form of a simple common phrase; for example, 'you're welcome' or 'no problem'.
- Assessment: a characterization of something as good or bad, positive or negative. Sometimes it follows an assessment by the other person; for example, 'great', 'like it', 'love it', 'cool', 'wow', 'that sucks', 'oh no'.
- PreClosing: a signal to end the current topic or the conversation itself. This may be an intention to leave, reference to a future conversations, or a check if the other person has more topics to talk about; for example, 'anything else?' or 'got to go' or 'is that all?'.
- Apology: an expression of regret for inconvenience, offense or harm one caused; for example, 'I'm sorry' or 'sorry'.
- SequenceAbort:  a signal to cancel or retract something previously said, indicating that it is no longer relevant and that a response to it is no longer due; for example, 'never mind' or 'forget it'.
- Silence:  an empty response or the indication of a ‘silence’ or ‘pause’; for example, 'AGENT:   ' or 'AGENT: (silence)' or 'AGENT: .......' or 'AGENT:\n\n' or 'AGENT: [empty]'. 
- NewTopic: Changing the topic of conversation or proposing to change topics or discontinuing the current topic or proposing an alternative course of action; for example, ‘let’s talk about something else’ or ‘on a different note’ or ‘by the way’.
- NonVerbal: An indication of a facial expression or bodily gesture in words or an emoticon; for example, ((smiles)) or ((nods)) or ;).
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_correction = '''
- Answer: The preferred response to a question, inquiry or request, which provides the requested information or fulfills the request or provides a recommendation; for example; giving business hours in response to a request for a bakery's business hours or cancelling an account or recommending a hotel to stay at.
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- RepeatRequest: a request that the other speaker repeat all or part of what they previously said, in order to resolve a trouble in hearing; for example, 'what did you say?' or 'say again' or 'I didn't hear you'.
- ParaphraseRequest: a request that the other speaker reword all or part of what they previously said, without changing its meaning, in order to resolve a trouble in understanding; for example, 'what do you mean' or 'I don't understand' or ‘I don’t understand’ or 'can you say that a different way'.
- DefinitionRequest: a request for the intended meaning of a word or phrase previously produced by another speaker, in order to resolve a trouble in understanding; for example, 'what do you mean by blew up' or 'what is a FHO' or 'define keto'.
- ExampleRequest: a request for a particular instance of a general idea expressed in a previous turn; for example, 'can you give an example' or 'like what'.
- NewTopic: Changing the topic of conversation or proposing to change topics or discontinuing the current topic or proposing an alternative course of action; for example, ‘let’s talk about something else’ or ‘on a different note’ or ‘by the way’.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''

def_correction_open_request = '''
- Answer: The preferred response to a question, inquiry or request, which provides the requested information or fulfills the request or provides a recommendation; for example; giving business hours in response to a request for a bakery's business hours or cancelling an account or recommending a hotel to stay at.
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- DetailRequestGrounded: Asking for additional information that is required for fulfilling a request or answering an inquiry. AGENT is better able to complete the request if it knows key details. The detail request is grounded if it asks about one of these particular details: <request_details>.
- DetailRequestUngrounded: Asking about any other details that are not specified in DetailRequestGrounded.
- RepeatRequest: a request that the other speaker repeat all or part of what they previously said, in order to resolve a trouble in hearing; for example, 'what did you say?' or 'say again' or 'I didn't hear you'.
- ParaphraseRequest: a request that the other speaker reword all or part of what they previously said, without changing its meaning, in order to resolve a trouble in understanding; for example, 'what do you mean' or 'I don't understand' or ‘I don’t understand’ or 'can you say that a different way'.
- DefinitionRequest: a request for the intended meaning of a word or phrase previously produced by another speaker, in order to resolve a trouble in understanding; for example, 'what do you mean by blew up' or 'what is a FHO' or 'define keto'.
- ExampleRequest: a request for a particular instance of a general idea expressed in a previous turn; for example, 'can you give an example' or 'like what'.
- NewTopic: Changing the topic of conversation or proposing to change topics or discontinuing the current topic or proposing an alternative course of action; for example, ‘let’s talk about something else’ or ‘on a different note’ or ‘by the way’.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''

def_repeat_open_request = '''
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''
def_repair_open_request = '''
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''

def_closer_open_request = '''
- Answer: The preferred response to a question, inquiry or request, which provides the requested information or fulfills the request or provides a recommendation; for example; giving business hours in response to a request for a bakery's business hours or cancelling an account or recommending a hotel to stay at.
- NonAnswer: Failure to provide an answer to an inquiry or to fulfill a request for action either by giving an excuse or refusing to do so; for example, 'I’m afraid I cannot close your account' or 'We have no models that fit your preferences' or 'I’m sorry, I don’t know the answer to your question.'
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- Acknowledgment: a simple indication that what the other person said was heard or understood; for example, 'okay', 'all right', 'I see', 'got it', 'oh', 'I know'.
- Appreciation: A display of gratitude for something the other person said or did; for example, 'thank you' or 'that is much appreciated'.
- GratitudeReceipt: an acknowledgement that one has been thanked or appreciated. It usually takes the form of a simple common phrase; for example, 'you're welcome' or 'no problem'.
- Assessment: a characterization of something as good or bad, positive or negative. Sometimes it follows an assessment by the other person; for example, 'great', 'like it', 'love it', 'cool', 'wow', 'that sucks', 'oh no'.
- PreClosing: a signal to end the current topic or the conversation itself. This may be an intention to leave, reference to a future conversations, or a check if the other person has more topics to talk about; for example, 'anything else?' or 'got to go' or 'is that all?'.
- Apology: an expression of regret for inconvenience, offense or harm one caused; for example, 'I'm sorry' or 'sorry'.
- SequenceAbort:  a signal to cancel or retract something previously said, indicating that it is no longer relevant and that a response to it is no longer due; for example, 'never mind' or 'forget it'.
- Silence:  an empty response or the indication of a ‘silence’ or ‘pause’; for example, 'AGENT:   ' or 'AGENT: (silence)' or 'AGENT: .......' or 'AGENT:\n\n' or 'AGENT: [empty]'. 
- NewTopic: Changing the topic of conversation or proposing to change topics or discontinuing the current topic or proposing an alternative course of action; for example, ‘let’s talk about something else’ or ‘on a different note’ or ‘by the way’.
- NonVerbal: An indication of a facial expression or bodily gesture in words or an emoticon; for example, ((smiles)) or ((nods)) or ;).
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''

def_preliminary_open_request = '''
- Affirmation: A response that positively affirms a prior yes/no question by the USER; for example, 'yes' or 'sure' or 'yeah' or any equivalent affirmative words.
- Acknowledgment: a simple indication that what the other person said was heard or understood; for example, 'okay', 'all right', 'I see', 'got it', 'oh', 'I know'.
- Assessment: a characterization of something as good or bad, positive or negative. Sometimes it follows an assessment by the other person; for example, 'great', 'like it', 'love it', 'cool', 'wow', 'that sucks', 'oh no'.
- HelpOffer: Offering to help USER generally or with a specifict type of request; for example, 'how can I help you?' or 'I can help you with that' or 'would you like me to look up the business hours?'.
- DetailRequestGrounded: Asking for additional information that is required for fulfilling a request or answering an inquiry. AGENT is better able to complete the request if it knows key details. The detail request is grounded if it asks about one of these particular details: <request_details>.
- DetailRequestUngrounded: Asking about any other details that are not specified in DetailRequestGrounded.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''

def_expansion_open_request = '''
- Repeat: When AGENT’s last turn (line <last_agent_turn_num>) is a repeat of AGENT’s prior turn (<prior_turn>) using the same words, for example, to resolve USER’s trouble in hearing.  It may be a full or partial repeat of the misheard turn.
- Paraphrase: When AGENT’s last turn (line <last_agent_turn_num>) is a paraphrase of AGENT’s prior turn (<prior_turn>) using different words, for example, to resolve USER’s trouble in understanding. It may be a full or partial paraphrase of the misunderstood turn.
- Example: When AGENT's last turn (line <last_agent_turn_num>) provides an example of a keyword or phrase in AGENT's prior turn (<prior_turn>), for instance, to resolve USER's trouble in understanding that keyword or phrase. For example, an 'Old Fashioned' is an example of a 'classic cocktail'.
- Definition: When AGENT's last turn (line <last_agent_turn_num>) is a definition of a keyword or phrase in AGENT's prior turn (<prior_turn>), for example, to resolve USER's trouble in understanding that keyword or phrase. For example, 'artificial intelligence means technology that enables computers to simulate human reasoning or problem-solving' or 'Chantilly is a kind of sweetened whipped cream'.
- ChoiceGiving: Giving choices to USER for answering a detail request; for example, 'We have tall, grande and venti sizes' or 'We sell gas, charcoal and wood burning grills'.
- OOC: a stance that is not in the voice of the AGENT, but in that of another character, such as an analyst or AI personality, for example, '(Note:' or 'In this improved conversation,' or 'Or, you could say:' or Chain-of-Thought.
- Other: An utterance that does not fit any of the above classes.
'''

def generate_judge_prompts(prompts_file, generations_file, language='en'):
    if language == 'ru':
        from utils_ru import generate_judge_prompts_ru
        return generate_judge_prompts_ru(prompts_file, generations_file, language='ru')

    # Read the chat prompts from the first JSONL file (chat)
    with open(prompts_file, 'r', encoding='utf-8') as f:
        chat_data = {json.loads(line)['id']: json.loads(line) for line in f}

    # Read the response data from the second JSONL file (responses)
    with open(generations_file, 'r', encoding='utf-8') as f:
        response_data = {json.loads(line)['id']: json.loads(line) for line in f}

    # Prepare the output data
    combined_data = []
    for task_id in chat_data:
        if task_id in response_data:
            chat_entry = chat_data[task_id]
            response_entry = response_data[task_id]
            prior_turn = ''
            task_description = response_entry['task']
            # Bug fix: fall back to chat_entry['request_details'] if absent in response_entry
            request_details = response_entry.get('request_details') or chat_entry.get('request_details', '')

            # Task label assignment based on task description
            if task_description in ('inquiry', 'incremental request', 'inquiry ungrounded', 'incremental-self-correction'):
                label = def_inquiry
            elif task_description == 'repeat request':
                label = def_repeat
            elif task_description == 'paraphrase request':
                label = def_para
            elif task_description == 'definition request':
                label = def_def
            elif task_description == 'example request':
                label = def_example
            elif task_description in ('sequence closer', 'sequence closer-acknowledgment (include)',
                                      'sequence closer-agreement (include)', 'sequence closer-appreciation (include)',
                                      'sequence closer-assessment (include)'):
                label = def_closer
            elif task_description == 'sequence abort':
                label = def_abort
            elif task_description == 'self-correction':
                label = def_correction
            elif task_description in ('Self-Correction', 'Recommendation-Compact', 'Recommendation-Expanded', 'Recommendation-Incremental', 'Detail Request-Partial', 'Detail Request-All', 'Detail Request-Expanded'):
                label = def_correction_open_request
            elif task_description in ('Repeat', 'Partial Repeat'):
                label = def_repeat_open_request
            elif task_description in ('Paraphrase', 'Example', 'Definition'):
                label = def_repair_open_request
            elif task_description in ('Closer', 'Abort'):
                label = def_closer_open_request
            elif task_description in ('Preliminary-Screen', 'Preliminary-Detail'):
                label = def_preliminary_open_request
            elif task_description in ('Expansion-Choices', 'Expansion-Repair'):
                label = def_expansion_open_request
            else:
                raise RuntimeError(f"Unknown task description: {task_description}")

            
            # Dynamically build the prompt from the chat_prompt
            label_prompt_parts = []
            for i, message in enumerate(chat_entry['chat_prompt']):
                role = message['role']
                content = message['content']
                if role == "user":
                    label_prompt_parts.append(f"{i} USER: {content}")
                elif role == "assistant" or role == "agent":
                    label_prompt_parts.append(f"{i} AGENT: {content}")

            # Add the response output as the last part of the prompt
            first_line = response_entry['output'].split('\n')[0].strip()
            label_prompt_parts.append(f"{i+1} AGENT: {first_line}")


            # Combine into one string
            label_prompt = "\n".join(label_prompt_parts)

            # Prior turn: Get the previous message, which is 3 turns back
            if i - 1 >= 1:
                # prior_turn = chat_entry['chat_prompt'][i-1]['content']
                prior_turn = 'line ' + str(i-1)

            # Replace placeholders in the judge prompt
            judge_prompt_final = judge_prompt.replace("<labels>", label.strip()) \
                                              .replace("<last_agent_turn_num>", str(i+1)) \
                                              .replace("<transcript_with_turn_num>", label_prompt) \
                                              .replace("<prior_turn>", prior_turn) \
                                              .replace("<request_details>", request_details) 


            # Create the final structure
            combined_entry = {
                "id": task_id,
                "task": chat_entry["task"],
                "chat_prompt": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": judge_prompt_final}
                ]
            }

            combined_data.append(combined_entry)
    
    return combined_data


if __name__ == '__main__':
    prompts_file = './data/conversation_competence.jsonl'
    generations_file = './downloads/generations/gpt4o.jsonl'
    judgments_file = './downloads/judge_prompt.jsonl'

    judge_prompts = generate_judge_prompts(prompts_file, generations_file)

    # Write the output to the JSONL file
    with open(judgments_file, 'w') as f:
        for entry in judge_prompts:
            f.write(json.dumps(entry) + "\n")
