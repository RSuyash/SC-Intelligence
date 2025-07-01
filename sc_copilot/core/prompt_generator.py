import os

def generate_moc_prompt(target_note_path, target_note_content, similar_notes_with_content):
    """Creates the prompt for the LLM to generate a Map of Content."""
    target_title = os.path.basename(target_note_path).replace('.md', '')
    
    connections_list_for_llm = ""
    connections_list_for_moc = ""
    for note in similar_notes_with_content:
        connections_list_for_llm += f"\n### {os.path.basename(note['path']).replace('.md', '')}\n```\n{note['content']}\n```"
        connections_list_for_moc += f"- `[[{os.path.basename(note['path']).replace('.md', '')}]]`\n"
    
    prompt = f"""You are a Zettelkasten and knowledge management expert specializing in UPSC exam preparation. Your task is to generate the title and body for a "Map of Content" (MOC) note.

A new note titled "{target_title}" was just created. Its content is as follows:

```
{target_note_content}
```

Based on its semantic content, it is highly related to the the following existing notes. Their content is provided below:
{connections_list_for_llm}

Synthesize the core themes, interconnections, and significance of the new note and its related notes. Your output should be a JSON object with the following keys:
1.  `title`: A concise and descriptive title for the MOC.
2.  `core_idea`: A brief, insightful paragraph explaining the overarching concept that connects all these notes.
3.  `key_details`: A more detailed explanation, organized into bullet points or short paragraphs, covering the key facets and relationships derived from the notes. This should go beyond a simple summary and delve into the deeper implications and relationships, suitable for UPSC level understanding.
4.  `body`: (Optional) Any additional comprehensive and analytical explanation that doesn't fit into `core_idea` or `key_details`.
5.  `flowchart_or_cause_effect`: (Optional) A simple flowchart or cause-and-effect chain in Mermaid syntax to visually represent the key relationships.
6.  `gs_paper`: The relevant GS Paper (e.g., GS1, GS2, GS3, GS4, Essay).
7.  `linked_pyqs`: (Optional) A list of relevant previous year questions (PYQs).
8.  `key_terms`: A list of key terms and concepts.
9.  `use_in_essay`: (Optional) A relevant essay idea or theme.
10. `note_type`: (Optional) The type of note (e.g., concept, theme, event, rebellion).
11. `source_type`: (Optional) The source type (e.g., Book, CA, YT, Class).
12. `revision_stage`: (Optional) The revision stage (e.g., SR1-SR5).
13. `has_diagram`: (Optional) Boolean indicating if a diagram is present.

Do NOT include any YAML front matter or extra text outside the JSON object.

Here are the wikilinks to include in the `key_details` or `body` sections:
{connections_list_for_moc}
"""
    return prompt

