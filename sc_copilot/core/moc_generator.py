import os
from datetime import datetime, timedelta
import json

class MOCGenerator:
    def __init__(self, moc_template_path):
        self.moc_template_path = moc_template_path
        self.moc_template_content = self._load_template()

    def _load_template(self):
        try:
            with open(self.moc_template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None

    def generate_moc(self, target_note_path, target_note_content, similar_notes_with_content, generated_data, target_front_matter):
        if self.moc_template_content is None:
            return None, "MOC template file not found."

        llm_suggested_title = generated_data.get('title', f"Map of Content - {os.path.basename(target_note_path).replace('.md', '')}")
        core_idea = generated_data.get('core_idea', '')
        key_details = generated_data.get('key_details', '')
        moc_body = generated_data.get('body', '')
        flowchart = generated_data.get('flowchart_or_cause_effect', '')
        gs_paper_llm = generated_data.get('gs_paper', '') # From LLM
        linked_pyqs_llm = generated_data.get('linked_pyqs', [])
        key_terms_llm = generated_data.get('key_terms', [])
        relevant_essay_idea_llm = generated_data.get('use_in_essay', '')
        note_type = generated_data.get('note_type', '')
        source_type = generated_data.get('source_type', '')
        revision_stage = generated_data.get('revision_stage', 'SR1')
        has_diagram = generated_data.get('has_diagram', False)

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

        moc_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-MOC"
        moc_yaml_data = {
            "id": moc_id,
            "title": llm_suggested_title,
            "type": "MOC",
            "note_type": note_type,
            "source": [f""[[{os.path.basename(target_note_path).replace('.md', '')}]]""], # Source as a list with wikilink
            "source_type": source_type,
            "subject": target_front_matter.get('subject', ''),
            "gs_paper": gs_paper_llm,
            "gs-tags": target_front_matter.get('gs-tags', ["MOC"]),
            "status": "draft",
            "maturity": 1,
            "priority": "medium",
            "link-density": "high",
            "granularity": "index",
            "answer_utility": "high",
            "use_in_essay": relevant_essay_idea_llm,
            "from_daily": datetime.now().strftime("%Y-%m-%d"),
            "revision_stage": revision_stage,
            "has_diagram": str(has_diagram).lower(),
            "created": datetime.now().strftime("%Y-%m-%d"),
            "updated": datetime.now().strftime("%Y-%m-%d"),
            "sr1_date": datetime.now().strftime("%Y-%m-%d"),
            "sr2_due": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        }

        related_links_yaml_list = []
        related_links_body_str = ""
        for note in similar_notes_with_content:
            note_title = os.path.basename(note['path']).replace('.md', '')
            related_links_yaml_list.append(f"- \"[[{note_title}]]\"")
            related_links_body_str += f"- [[{note_title}]]\n"
        related_links_yaml_str = "\n".join(related_links_yaml_list)

        final_moc_content = self.moc_template_content

        # Explicitly replace each YAML field with correctly formatted strings
        final_moc_content = final_moc_content.replace("{{id}}", moc_yaml_data["id"])
        final_moc_content = final_moc_content.replace("{{title}}", f'"{moc_yaml_data["title"]}"')
        final_moc_content = final_moc_content.replace("{{type}}", moc_yaml_data["type"])
        final_moc_content = final_moc_content.replace("{{note_type}}", moc_yaml_data["note_type"])
        
        # Format source as a YAML block-style list with double quotes
        if moc_yaml_data["source"]:
            formatted_source = "\n  - ".join([f'\"' + item + '\"' for item in moc_yaml_data["source"]])
            final_moc_content = final_moc_content.replace("{{source}}", f"\n  - {formatted_source}")
        else:
            final_moc_content = final_moc_content.replace("{{source}}", "[]")

        final_moc_content = final_moc_content.replace("{{source_type}}", moc_yaml_data["source_type"])
        final_moc_content = final_moc_content.replace("{{subject}}", moc_yaml_data["subject"])
        final_moc_content = final_moc_content.replace("{{gs_paper}}", moc_yaml_data["gs_paper"])

        # Format gs-tags, keywords, and linked_pyqs as YAML flow-style lists
        final_moc_content = final_moc_content.replace("{{gs-tags}}", json.dumps(moc_yaml_data["gs-tags"])) 
        final_moc_content = final_moc_content.replace("{{keywords}}", json.dumps(key_terms_llm))
        final_moc_content = final_moc_content.replace("{{linked_pyqs}}", json.dumps(linked_pyqs_llm))

        final_moc_content = final_moc_content.replace("{{status}}", moc_yaml_data["status"])
        final_moc_content = final_moc_content.replace("{{maturity}}", str(moc_yaml_data["maturity"]))
        final_moc_content = final_moc_content.replace("{{priority}}", moc_yaml_data["priority"])
        final_moc_content = final_moc_content.replace("{{link-density}}", moc_yaml_data["link-density"])
        final_moc_content = final_moc_content.replace("{{granularity}}", moc_yaml_data["granularity"])
        final_moc_content = final_moc_content.replace("{{answer_utility}}", moc_yaml_data["answer_utility"])
        final_moc_content = final_moc_content.replace("{{use_in_essay}}", moc_yaml_data["use_in_essay"])
        final_moc_content = final_moc_content.replace("{{from_daily}}", moc_yaml_data["from_daily"])
        final_moc_content = final_moc_content.replace("{{revision_stage}}", moc_yaml_data["revision_stage"])
        final_moc_content = final_moc_content.replace("{{has_diagram}}", moc_yaml_data["has_diagram"])
        final_moc_content = final_moc_content.replace("{{created}}", moc_yaml_data["created"])
        final_moc_content = final_moc_content.replace("{{updated}}", moc_yaml_data["updated"])
        final_moc_content = final_moc_content.replace("{{sr1_date}}", moc_yaml_data["sr1_date"])
        final_moc_content = final_moc_content.replace("{{sr2_due}}", moc_yaml_data["sr2_due"])

        # Related Links YAML (already formatted with [[...]])
        final_moc_content = final_moc_content.replace("{{related_links_yaml}}", related_links_yaml_str.strip())

        # Other body replacements
        final_moc_content = final_moc_content.replace("{{core_idea}}", core_idea)
        final_moc_content = final_moc_content.replace("{{key_details}}", key_details)
        final_moc_content = final_moc_content.replace("{{related_links_body}}", related_links_body_str.strip())
        final_moc_content = final_moc_content.replace("{{moc_body}}", moc_body)
        final_moc_content = final_moc_content.replace("{{flowchart_or_cause_effect}}", flowchart)

        moc_filename = f"{llm_suggested_title.replace(' ', '-').replace(':', '').replace('/', '-')}.md"
        return moc_filename, final_moc_content