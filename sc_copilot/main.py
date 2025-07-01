import os
import configparser
import json
import argparse
from core.sc_reader import SmartConnectionsReader
from core.gemini_client import GeminiClient
from core.console_formatter import ConsoleFormatter
from core.moc_generator import MOCGenerator
from core.prompt_generator import generate_moc_prompt
from core.file_utils import extract_yaml_front_matter

def main():
    """Main function to run the Knowledge Architect tool."""
    parser = argparse.ArgumentParser(description="Generate a Map of Content (MOC) for a given note.")
    parser.add_argument('-p', '--process-file', type=str,
                        help="Relative path of the new note to process directly (e.g., 'UPSC/GS2/Polity.md').")
    args = parser.parse_args()

    formatter = ConsoleFormatter()

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

    # 1. Read the Smart Connections data
    formatter.print_init()
    reader = SmartConnectionsReader(vault_path)
    reader.load_data()
    formatter.print_loaded_notes(len(reader.notes), len(reader.blocks))
    
    # 2. Determine target note
    if args.process_file:
        target_note_relative = args.process_file.strip().replace('\\', '/').strip('"\'')
        formatter.print_processing_file(target_note_relative)
    else:
        target_note_relative = formatter.get_input("Enter the relative path of the new note (e.g., 'UPSC/GS2/Polity.md')")
    
    found_path = next((path for path in reader.notes if path.lower() == target_note_relative.lower()), None)
    
    if not found_path:
         formatter.print_error(f"Note '{target_note_relative}' not found in the Smart Connections database. Please ensure it's indexed.")
         return

    target_note_content = reader.read_note_content(found_path)
    if not target_note_content:
        formatter.print_error(f"Could not read content for target note '{found_path}'. Please check file permissions or path.")
        return

    # 3. Find similar notes
    formatter.print_finding_connections(found_path)
    similar_notes_metadata = reader.find_similar_notes(found_path, n=5)

    if not similar_notes_metadata:
        formatter.print_warning("No strong connections found. Consider refining your note or adding more context.")
        return

    formatter.print_connections_found()
    similar_notes_with_content = []
    for note_meta in similar_notes_metadata:
        note_content = reader.read_note_content(note_meta['path'])
        if note_content:
            similar_notes_with_content.append({
                'path': note_meta['path'],
                'score': note_meta['score'],
                'content': note_content
            })
            formatter.print_connection(os.path.basename(note_meta['path']).replace('.md', ''), note_meta['score'])
        else:
            formatter.print_connection_warning(os.path.basename(note_meta['path']).replace('.md', ''))

    if not similar_notes_with_content:
        formatter.print_warning("No readable content from connected notes. Cannot generate MOC.")
        return

    # 4. Generate the MOC with Gemini
    formatter.print_generating_moc()
    target_front_matter, _ = extract_yaml_front_matter(target_note_content)

    moc_prompt_template_path = os.path.join(script_dir, 'moc_prompt_template.txt')
    prompt = generate_moc_prompt(found_path, target_note_content, similar_notes_with_content)
    gemini = GeminiClient(api_key)
    generated_response_json_str = gemini.generate_text(prompt)
    
    if generated_response_json_str.startswith("Error:"):
        formatter.print_gemini_error(generated_response_json_str)
        return

    try:
        generated_data = json.loads(generated_response_json_str)
    except json.JSONDecodeError:
        formatter.print_invalid_data(generated_response_json_str)
        return

    # 5. Generate and save the MOC file
    moc_generator = MOCGenerator(moc_template_path)
    moc_filename, final_moc_content = moc_generator.generate_moc(found_path, target_note_content, similar_notes_with_content, generated_data, target_front_matter)

    if final_moc_content:
        moc_filepath = os.path.join(moc_save_path, moc_filename)
        try:
            with open(moc_filepath, 'w', encoding='utf-8') as f:
                f.write(final_moc_content)
            formatter.print_success(moc_filepath)
        except IOError as e:
            formatter.print_save_error(moc_filepath, e)
    else:
        formatter.print_error(f"MOC template file not found at {moc_template_path}")

if __name__ == '__main__':
    main()