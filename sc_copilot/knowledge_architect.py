import os
import configparser
import re
from datetime import datetime
import json
import argparse

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

def generate_moc_prompt(target_note_path, target_note_content, similar_notes_with_content, template_path):
    """Creates the prompt for the LLM to generate a Map of Content."""
    target_title = os.path.basename(target_note_path).replace('.md', '')
    
    connections_list_for_llm = ""
    connections_list_for_moc = ""
    for note in similar_notes_with_content:
        connections_list_for_llm += f"\n### {os.path.basename(note['path']).replace('.md', '')}\n```\n{note['content']}\n```"
        connections_list_for_moc += f"- `[[{os.path.basename(note['path']).replace('.md', '')}]]`\n"
    
    with open(template_path, 'r', encoding='utf-8') as f:
        prompt_template = f.read()

    prompt = prompt_template.format(
        target_title=target_title,
        target_note_content=target_note_content,
        connections_list_for_llm=connections_list_for_llm,
        connections_list_for_moc=connections_list_for_moc
    )
    return prompt

def main():
    """Main function to run the Knowledge Architect tool."""
    parser = argparse.ArgumentParser(description="Generate a Map of Content (MOC) for a given note.")
    parser.add_argument('-p', '--process-file', type=str,
                        help="Relative path of the new note to process directly (e.g., 'UPSC/GS2/Polity.md').")
    args = parser.parse_args()

    config = configparser.ConfigParser()
    script_dir = os.path.dirname(__file__)
    config_path = os.path.join(script_dir, 'config.ini')
    config.read(config_path)

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
    # 1. Initialize Smart Connections Reader and load data
    print("✨ Initializing Knowledge Architect...")
    reader = SmartConnectionsReader(vault_path)
    reader.load_data()
    print(f"📚 Loaded {len(reader.notes)} notes and {len(reader.blocks)} blocks from Smart Connections.")
    
    # 2. Determine target note
    if args.process_file:
        target_note_relative = args.process_file.strip().replace('\\', '/').strip('"\'')
        print(f"\n📄 Processing: {target_note_relative}")
    else:
        target_note_relative = input("\n📝 Enter the relative path of the new note (e.g., 'UPSC/GS2/Polity.md'): ").strip().replace('\\', '/')
    
    # Find the correctly-cased path in the database
    found_path = next((path for path in reader.notes if path.lower() == target_note_relative.lower()), None)
    
    if not found_path:
         print(f"\n❌ Error: Note '{target_note_relative}' not found in the Smart Connections database. Please ensure it's indexed.")
         return

    target_note_content = reader.read_note_content(found_path)
    if not target_note_content:
        print(f"❌ Error: Could not read content for target note '{found_path}'. Please check file permissions or path.")
        return

    # 3. Find similar notes
    print(f"🔍 Finding connections for '{found_path}'...")
    similar_notes_metadata = reader.find_similar_notes(found_path, n=5)

    if not similar_notes_metadata:
        print("\n⚠️ No strong connections found. Consider refining your note or adding more context.")
        return

    print("🔗 Found connections:")
    similar_notes_with_content = []
    for note_meta in similar_notes_metadata:
        note_content = reader.read_note_content(note_meta['path'])
        if note_content:
            similar_notes_with_content.append({
                'path': note_meta['path'],
                'score': note_meta['score'],
                'content': note_content
            })
            print(f"  - {os.path.basename(note_meta['path']).replace('.md', '')} (Score: {note_meta['score']:.2f})")
        else:
            print(f"  - ⚠️ Warning: Could not read content for '{os.path.basename(note_meta['path']).replace('.md', '')}'. Skipping.")

    if not similar_notes_with_content:
        print("\n⚠️ No readable content from connected notes. Cannot generate MOC.")
        return

    # 4. Generate the MOC with Gemini
    print("\n🧠 Generating Map of Content with Gemini...")
    # First, extract YAML from the target note to inherit some fields
    target_front_matter, _ = extract_yaml_front_matter(target_note_content)

    moc_prompt_template_path = os.path.join(script_dir, 'moc_prompt_template.txt')

    # Update the prompt to ask for JSON output
    prompt = generate_moc_prompt(found_path, target_note_content, similar_notes_with_content, moc_prompt_template_path)
    gemini = GeminiClient(api_key)
    generated_response_json_str = gemini.generate_text(prompt)
    
    if generated_response_json_str.startswith("Error:"):
        print(f"❌ Gemini Generation Error: {generated_response_json_str}")
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
        print(f"\n❌ Gemini returned invalid data. Response: {generated_response_json_str}")
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
        note_title = os.path.basename(note['path']).replace('.md', '')
        related_links_yaml_str += f"  - {note_title}\n"
        related_links_body_str += f"- [[{note_title}]]\n"

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
    
    try:
        with open(moc_filepath, 'w', encoding='utf-8') as f:
            f.write(final_moc_content)
        print(f"\n✅ Success! Map of Content saved to: {moc_filepath}")
    except IOError as e:
        print(f"\n❌ Error saving MOC to {moc_filepath}: {e}")

if __name__ == '__main__':
    main()