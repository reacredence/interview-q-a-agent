# Speculative Decoding Interview Question

## The Question
Imagine you are designing a speculative decoding system for a large language model. Speculative decoding involves generating tokens speculatively and then verifying them to optimize the model's inference time while maintaining high accuracy. The system uses a draft-verify cycle, where a drafter proposes tokens, and a verifier checks their validity. How would you handle tokens that fail verification? Consider the implications of discarding versus correcting these tokens on overall system performance. What strategies could you employ to correct these tokens, such as using a secondary model or heuristic rules, and how might these strategies impact the system's efficiency and accuracy?

## Common Wrong Answer
If a token fails verification, simply discard it and continue with the next token in the sequence. This approach prioritizes speed by avoiding additional processing steps, ensuring that only verified tokens are part of the output.

## How It Actually Works
In speculative decoding, when a token fails verification, merely discarding it can lead to inefficiencies and inaccuracies in the generated sequence. A more effective approach is to attempt correction using strategies like a specialized drafter or a secondary model to propose alternative tokens likely to pass verification. Implementing heuristic rules or leveraging context from surrounding tokens can further enhance this process. By employing these methods, the system can reduce the number of iterations needed, improving both speed and accuracy during inference. This ensures that tokens are not only verified but also optimized for performance and reliability.

## Key Paper
Speculative Decoding and Specialized Drafters - Unknown (https://aclanthology.org/2024.emnlp-main.602.pdf)
