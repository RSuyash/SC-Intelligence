import os
import configparser
import re
from datetime import datetime
import json

from sc_reader import SmartConnectionsReader
from gemini_client import GeminiClient

def extract_yaml_front_matter(content):
    """Extracts YAML front matter from a Markdown string and returns it as a dictionary."""
    yaml_pattern = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
    match = yaml_pattern.match(content)
    if not match:
        return {}, content

    yaml_str = match.group(1)
    front_matter = {}
    for line in yaml_str.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('[') and value.endswith(']'):
                front_matter[key] = [item.strip() for item in value[1:-1].split(',')]
            else:
                front_matter[key] = value
    return front_matter, content[match.end():]

def generate_moc_prompt(target_note_path, target_note_content, similar_notes_with_content):
    """Creates the prompt for the LLM to generate a Map of Content."""
    target_title = os.path.basename(target_note_path).replace('.md', '')
    
    connections_list_for_llm = ""
    connections_list_for_moc = ""
    for note in similar_notes_with_content:
        connections_list_for_llm += f"\n### {os.path.basename(note['path']).replace('.md', '')}\n```\n{note['content']}\n```"
        connections_list_for_moc += f"- `[[{os.path.basename(note['path']).replace('.md', '')}]]`\n"
    
    prompt = f"""
You are a Zettelkasten and knowledge management expert. Your task is to generate the title and body for a "Map of Content" (MOC) note.

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

Do NOT include any YAML front matter or extra text outside the JSON object.

Here are the wikilinks to include in the `key_details` or `body` sections:
{connections_list_for_moc}
"""
    return prompt

def main():
    """Main function to run the Knowledge Architect tool."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    vault_path = config['Paths']['vault_path']
    moc_save_path = config['Paths']['moc_save_path']
    moc_template_path = config['Paths']['moc_template_path']
    api_key = config['API']['gemini_api_key']

    if not os.path.exists(moc_save_path):
        os.makedirs(moc_save_path)

    # Load MOC template
    try:
        with open(moc_template_path, 'r', encoding='utf-8') as f:
            moc_template_content = f.read()
    except FileNotFoundError:
        print(f"Error: MOC template file not found at {moc_template_path}")
        return

    # 1. Read the Smart Connections data
    reader = SmartConnectionsReader(vault_path)
    reader.load_data()
    
    # 2. Get user input for the target note
    target_note_relative = input("Enter the relative path of the new note (e.g., 'UPSC/GS2/Polity.md'): ").strip()
    
    # Obsidian paths are case-insensitive on some systems, find the correctly-cased path
    found_path = next((path for path in reader.notes if path.lower() == target_note_relative.lower()), None)
    
    if not found_path:
         print(f"Error: Could not find '{target_note_relative}' in the Smart Connections database.")
         return

    target_note_content = reader.read_note_content(found_path)
    if not target_note_content:
        print(f"Error: Could not read content for target note '{found_path}'.")
        return

    # 3. Find similar notes
    print(f"\nFinding connections for '{found_path}'...")
    similar_notes_metadata = reader.find_similar_notes(found_path, n=5)

    if not similar_notes_metadata:
        print("Could not find any similar notes to generate a MOC.")
        return

    print("Found connections:")
    similar_notes_with_content = []
    for note_meta in similar_notes_metadata:
        note_content = reader.read_note_content(note_meta['path'])
        if note_content:
            similar_notes_with_content.append({
                'path': note_meta['path'],
                'score': note_meta['score'],
                'content': note_content
            })
            print(f"  - {note_meta['path']} (Score: {note_meta['score']:.2f})")
        else:
            print(f"  - Warning: Could not read content for similar note '{note_meta['path']}'. Skipping.")

    if not similar_notes_with_content:
        print("No similar notes with readable content found to generate a MOC.")
        return

    # 4. Generate the MOC with Gemini
    # First, extract YAML from the target note to inherit some fields
    target_front_matter, _ = extract_yaml_front_matter(target_note_content)

    # Update the prompt to ask for JSON output
    prompt = generate_moc_prompt(found_path, target_note_content, similar_notes_with_content)
    gemini = GeminiClient(api_key)
    generated_response_json_str = gemini.generate_text(prompt)
    
    if generated_response_json_str.startswith("Error:"):
        print(f"\n{generated_response_json_str}")
        return

    try:
        generated_data = json.loads(generated_response_json_str)
        llm_suggested_title = generated_data.get('title', f"Map of Content - {os.path.basename(found_path).replace('.md', '')}")
        core_idea = generated_data.get('core_idea', '')
        key_details = generated_data.get('key_details', '')
        moc_body = generated_data.get('body', '') # Optional additional body content

        # Ensure all content fields are strings
        if isinstance(core_idea, list): core_idea = "\n".join([str(item) for item in core_idea])
        if isinstance(key_details, list): 
            formatted_details = []
            for item in key_details:
                if isinstance(item, dict) and 'heading' in item and 'content' in item:
                    formatted_details.append(f"### {item['heading']}\n\n{item['content']}")
                else:
                    formatted_details.append(str(item))
            key_details = "\n\n".join(formatted_details)
        if isinstance(moc_body, list): moc_body = "\n".join([str(item) for item in moc_body])
    except json.JSONDecodeError:
        print(f"Error: Gemini did not return valid JSON. Response: {generated_response_json_str}")
        return

    # Construct the MOC's YAML front matter
    moc_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-MOC"
    moc_yaml_data = {
        "id": moc_id,
        "title": llm_suggested_title,
        "type": "MOC",
        "source": f"[[{os.path.basename(found_path).replace('.md', '')}]]", # Source from the target note
        "subject": target_front_matter.get('subject', ''),
        "gs-tags": target_front_matter.get('gs-tags', ["MOC"]),
        "keywords": target_front_matter.get('keywords', []),
        "status": "draft",
        "maturity": 1,
        "priority": "medium",
        "link-density": "high",
        "granularity": "index",
        "answer-utility": "high",
        "from_daily": datetime.now().strftime("%Y-%m-%d"), # Assuming MOCs are generated from daily work
        "created": datetime.now().strftime("%Y-%m-%d"),
        "updated": datetime.now().strftime("%Y-%m-%d"),
    }

    # Prepare related links for template (YAML and body)
    related_links_yaml_str = ""
    related_links_body_str = ""
    for note in similar_notes_with_content:
        link = f"[[{os.path.basename(note['path']).replace('.md', '')}]]"
        related_links_yaml_str += f"  - {link}\n"
        related_links_body_str += f"- {link}\n"

    # Populate the template
    final_moc_content = moc_template_content
    final_moc_content = final_moc_content.replace("{{id}}", moc_yaml_data["id"])
    final_moc_content = final_moc_content.replace("{{title}}", moc_yaml_data["title"])
    final_moc_content = final_moc_content.replace("{{type}}", moc_yaml_data["type"])
    final_moc_content = final_moc_content.replace("{{source}}", moc_yaml_data["source"])
    final_moc_content = final_moc_content.replace("{{subject}}", moc_yaml_data["subject"])
    final_moc_content = final_moc_content.replace("{{gs-tags}}", str(moc_yaml_data["gs-tags"]).replace("'", ""))
    final_moc_content = final_moc_content.replace("{{keywords}}", str(moc_yaml_data["keywords"]).replace("'", ""))
    final_moc_content = final_moc_content.replace("{{status}}", moc_yaml_data["status"])
    final_moc_content = final_moc_content.replace("{{maturity}}", str(moc_yaml_data["maturity"]))
    final_moc_content = final_moc_content.replace("{{priority}}", moc_yaml_data["priority"])
    final_moc_content = final_moc_content.replace("{{link-density}}", moc_yaml_data["link-density"])
    final_moc_content = final_moc_content.replace("{{granularity}}", moc_yaml_data["granularity"])
    final_moc_content = final_moc_content.replace("{{answer-utility}}", moc_yaml_data["answer-utility"])
    final_moc_content = final_moc_content.replace("{{from_daily}}", moc_yaml_data["from_daily"])
    final_moc_content = final_moc_content.replace("{{created}}", moc_yaml_data["created"])
    final_moc_content = final_moc_content.replace("{{updated}}", moc_yaml_data["updated"])
    final_moc_content = final_moc_content.replace("{{related_links_yaml}}", related_links_yaml_str.strip()) # .strip() to remove trailing newline if no links
    final_moc_content = final_moc_content.replace("{{core_idea}}", core_idea)
    final_moc_content = final_moc_content.replace("{{key_details}}", key_details)
    final_moc_content = final_moc_content.replace("{{related_links_body}}", related_links_body_str.strip())
    final_moc_content = final_moc_content.replace("{{moc_body}}", moc_body)

    # 5. Save the new MOC file
    moc_filename = f"{llm_suggested_title.replace(' ', '-').replace(':', '').replace('/', '-')}.md"
    moc_filepath = os.path.join(moc_save_path, moc_filename)
    
    with open(moc_filepath, 'w', encoding='utf-8') as f:
        f.write(final_moc_content)

    print(f"\n✅ Success! New Map of Content created at: {moc_filepath}")

if __name__ == '__main__':
    main()