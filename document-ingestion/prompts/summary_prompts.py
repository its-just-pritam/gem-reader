SUMMARY_PROMPT_TEMPLATE = """
Summarize the contents of the following PDF within {response_size} words. Focus on the main points, key insights, and important details.
List out the title, authors, index, acknowledgements, conclusions, and references if available. Use the page numbers to provide accurate references in your summary.

Context: {context}
"""

QUERY_ENHANCEMENT_PROMPT_TEMPLATE = """
Enhance the following user query based on the previous conversation context. 
The previous conversation context includes the last user query and the assistant's response. Use this context to make the new query more specific, clear, and relevant to the user's intent.
Previous User Query: "{previous_query}"
Assistant's Response: "{previous_response}"
New User Query: "{new_query}"
"""