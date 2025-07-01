# Knowledge Architect for UPSC Preparation

## Project Overview

The Knowledge Architect is a Python-based command-line interface (CLI) tool designed to assist UPSC aspirants in organizing and synthesizing their study notes. Leveraging the power of Google's Gemini AI and integrated with Obsidian's Smart Connections plugin, this tool automates the creation of "Maps of Content" (MOCs). These MOCs help in identifying interconnections between notes, generating concise summaries, and structuring knowledge in an exam-oriented manner, ultimately enhancing recall and understanding for UPSC preparation.

The tool aims to transform raw study notes into structured, interconnected knowledge assets, making the revision process more efficient and effective.

## Features

*   **Automated MOC Generation:** Generates comprehensive Maps of Content based on a target note and its semantically similar notes.
*   **AI-Powered Synthesis:** Utilizes the Gemini AI to synthesize core ideas, key details, and relevant UPSC-specific information for MOCs.
*   **UPSC-Centric Metadata:** Populates MOCs with crucial UPSC-related fields such as GS Paper relevance, linked Previous Year Questions (PYQs), keywords, and essay themes.
*   **Visual Concept Diagrams:** Supports the inclusion of Mermaid syntax for flowcharts or cause-effect diagrams within MOCs for better visual recall.
*   **Modular and Extensible Architecture:** Designed with a clear separation of concerns, making it easy to add new features and functionalities.
*   **Enhanced CLI Experience:** Provides clear, color-coded console output for better user feedback.

## Directory Structure

```
D:/Projects/CS-Intelligence/
├───README.md
├───.git/
├───sc_copilot/
│   ├───config.ini
│   ├───gemini_config.ini
│   ├───main.py
│   ├───moc_template_upsc.md
│   ├───requirements.txt
│   ├───__pycache__/
│   │   ├───gemini_client.cpython-313.pyc
│   │   └───sc_reader.cpython-313.pyc
│   ├───core/
│   │   ├───console_formatter.py
│   │   ├───file_utils.py
│   │   ├───gemini_client.py
│   │   ├───moc_generator.py
│   │   ├───prompt_generator.py
│   │   └───sc_reader.py
│   └───features/
```

## File-by-File Breakdown

### `sc_copilot/main.py`

*   **Role:** The main entry point of the application. It handles command-line arguments, reads configuration, and orchestrates the entire MOC generation workflow.
*   **Key Functions:**
    *   `main()`: Parses arguments, initializes components, reads Smart Connections data, finds similar notes, calls Gemini for MOC content, and saves the generated MOC.

### `sc_copilot/config.ini`

*   **Role:** Configuration file for defining paths (Obsidian vault, MOC save location, MOC template) and API keys.
*   **Key Sections:**
    *   `[Paths]`: `vault_path`, `moc_save_path`, `moc_template_path`.
    *   `[API]`: `gemini_api_key`.

### `sc_copilot/gemini_config.ini`

*   **Role:** Configuration file specifically for the Gemini API, primarily to specify the model name.
*   **Key Sections:**
    *   `[Gemini]`: `model_name` (e.g., `gemini-1.5-flash`).

### `sc_copilot/moc_template_upsc.md`

*   **Role:** The Markdown template used to structure the generated Maps of Content. It includes placeholders (e.g., `{{title}}`, `{{core_idea}}`) that are replaced with AI-generated content and metadata.
*   **Key Sections:** YAML front matter for structured metadata (UPSC-specific fields, revision tracking), and Markdown sections for `Core Idea`, `Key Details`, `Concept Diagram`, `UPSC Hooks`, `Revision Tracker`, and `Related` notes.

### `sc_copilot/requirements.txt`

*   **Role:** Lists all the Python dependencies required to run the project.

### `sc_copilot/core/console_formatter.py`

*   **Role:** Provides a styled and user-friendly console output. It handles colors, bold text, animated spinners, and structured messages for better user experience.
*   **Key Class:** `ConsoleFormatter`
*   **Key Methods:** `print_init()`, `print_loaded_notes()`, `print_processing_file()`, `get_input()`, `print_error()`, `print_warning()`, `start_activity()`, `end_activity()`, etc.

### `sc_copilot/core/file_utils.py`

*   **Role:** Contains utility functions for file operations, specifically for extracting YAML front matter from Markdown files.
*   **Key Functions:**
    *   `extract_yaml_front_matter(content)`: Parses a Markdown string to extract and return its YAML front matter as a dictionary.

### `sc_copilot/core/gemini_client.py`

*   **Role:** Manages interaction with the Google Gemini API. It configures the API client and handles text generation requests.
*   **Key Class:** `GeminiClient`
*   **Key Methods:**
    *   `__init__(api_key)`: Initializes the Gemini API client with the provided API key and model name from `gemini_config.ini`.
    *   `generate_text(prompt)`: Sends a prompt to the Gemini API and returns the generated text (expected to be JSON).

### `sc_copilot/core/moc_generator.py`

*   **Role:** Responsible for taking the AI-generated content and populating the MOC template to create the final Markdown file. It handles the complex logic of formatting YAML lists and ensuring correct wikilink syntax.
*   **Key Class:** `MOCGenerator`
*   **Key Methods:**
    *   `__init__(moc_template_path)`: Loads the MOC template.
    *   `generate_moc(...)`: Takes AI-generated data and other relevant information to construct the final MOC content, including proper YAML formatting for lists and wikilinks.

### `sc_copilot/core/prompt_generator.py`

*   **Role:** Constructs the detailed prompt that is sent to the Gemini AI. This prompt instructs the AI on the desired structure and content for the MOC, including all UPSC-specific fields.
*   **Key Functions:**
    *   `generate_moc_prompt(...)`: Assembles the prompt using the target note's content, similar notes' content, and specific instructions for the AI to generate JSON output with all required MOC fields.

### `sc_copilot/core/sc_reader.py`

*   **Role:** Reads and processes the data generated by the Obsidian Smart Connections plugin (`.ajson` files). It loads note and block embeddings into memory for similarity calculations.
*   **Key Class:** `SmartConnectionsReader`
*   **Key Methods:**
    *   `__init__(vault_path)`: Initializes the reader with the path to the Obsidian vault.
    *   `load_data()`: Scans the `.smart-env` directory, parses `.ajson` files, and loads note/block embeddings.
    *   `get_note_by_path(path)`: Retrieves note data by its path.
    *   `read_note_content(relative_path)`: Reads the raw Markdown content of a note.
    *   `find_similar_notes(...)`: Calculates cosine similarity between notes/blocks to find the most related ones.

## Pipelines and Workflow

The core workflow of the Knowledge Architect tool can be summarized as follows:

1.  **Initialization & Configuration:**
    *   `main.py` starts, parses command-line arguments.
    *   `config.ini` and `gemini_config.ini` are read to load paths and API settings.
    *   `ConsoleFormatter` is initialized for styled output.

2.  **Knowledge Graph Loading:**
    *   `SmartConnectionsReader` is initialized with the `vault_path`.
    *   `sc_reader.load_data()` reads all `.ajson` files from the Obsidian `.smart-env` directory, loading note and block embeddings into memory.

3.  **Target Note Processing:**
    *   The user provides a `target_note_path` (either via command-line argument or interactive input).
    *   The content of the target note is read using `sc_reader.read_note_content()`.
    *   `file_utils.extract_yaml_front_matter()` extracts any existing YAML front matter from the target note.

4.  **Similarity Search:**
    *   `sc_reader.find_similar_notes()` is called to identify notes semantically related to the target note, based on their embeddings.

5.  **AI Prompt Generation:**
    *   `prompt_generator.generate_moc_prompt()` constructs a detailed JSON-formatted prompt for the Gemini AI. This prompt includes the target note's content, the content of similar notes, and specific instructions for generating UPSC-centric MOC fields.

6.  **AI Content Generation:**
    *   `GeminiClient` is used to send the generated prompt to the Gemini API.
    *   The AI processes the prompt and returns a JSON object containing the MOC's title, core idea, key details, and all requested UPSC metadata (GS Paper, PYQs, keywords, etc.).

7.  **MOC File Generation:**
    *   `MOCGenerator` is initialized with the `moc_template_path`.
    *   `moc_generator.generate_moc()` takes the AI-generated JSON data and populates the `moc_template_upsc.md` template. This step includes careful formatting of YAML lists and wikilinks to ensure Obsidian compatibility.

8.  **MOC File Saving:**
    *   The final MOC content is saved as a new Markdown file in the `moc_save_path` defined in `config.ini`.
    *   `ConsoleFormatter` provides success or error messages to the user.

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/CS-Intelligence.git
    cd CS-Intelligence/sc_copilot
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure API Key and Paths:**
    *   Open `sc_copilot/config.ini`.
    *   Replace `YOUR_API_KEY` with your actual Google Gemini API key (obtainable from [Google AI Studio](https://aistudio.google.com/app/apikey)).
    *   Update `vault_path` to the absolute path of your Obsidian vault (use forward slashes `/`).
    *   Update `moc_save_path` to the desired folder within your vault where MOCs will be saved.
    *   Ensure `moc_template_path` points to `D:/Projects/CS-Intelligence/sc_copilot/moc_template_upsc.md`.

4.  **Ensure Smart Connections Data:**
    *   Make sure you have the [Smart Connections Obsidian plugin](https://github.com/brianlovin/obsidian-smart-connections) installed and configured in your Obsidian vault.
    *   The plugin should have generated the `.smart-env/multi` directory within your vault, containing `.ajson` files. This tool relies on these files for note embeddings.

## Usage

To generate a Map of Content for a specific note:

```bash
python main.py -p "Relative/Path/To/Your/Note.md"
```

**Example:**

```bash
python main.py -p "01_CONCEPTS/Kalabhra-Revolt.md"
```

If you omit the `-p` argument, the tool will prompt you to enter the relative path interactively:

```bash
python main.py
```

## Future Improvements

*   **Interactive Mode Enhancements:** More interactive prompts, auto-completion for note paths.
*   **Advanced MOC Generation Options:** Allow users to specify the number of similar notes, control MOC depth, or choose different MOC generation strategies.
*   **Data Analysis & Visualization:** Implement commands to analyze the `.ajson` data (e.g., find isolated notes, visualize note clusters).
*   **Automated MOC Triggering:** Integrate with Obsidian's events (if possible) to automatically trigger MOC generation on new note creation or significant changes.
*   **Error Handling & Logging:** More robust error handling and detailed logging for debugging.
*   **Unit Testing:** Implement comprehensive unit tests for all modules.