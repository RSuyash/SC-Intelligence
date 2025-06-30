

import os

class ConsoleFormatter:
    """Handles all console output for a cleaner and more organized presentation."""

    def __init__(self, theme='default'):
        self.theme = theme

    def print_init(self):
        """Prints the initialization message."""
        print("✨ Initializing Knowledge Architect...")

    def print_loaded_notes(self, note_count, block_count):
        """Prints the number of loaded notes and blocks."""
        print(f"📚 Loaded {note_count} notes and {block_count} blocks from Smart Connections.")

    def print_processing_file(self, file_path):
        """Prints the file being processed."""
        print(f"\n📄 Processing: {file_path}")

    def get_input(self, prompt):
        """Gets input from the user with a specific format."""
        return input(f"\n📝 {prompt}").strip().replace('\\', '/')

    def print_error(self, message):
        """Prints an error message."""
        print(f"\n❌ Error: {message}")

    def print_warning(self, message):
        """Prints a warning message."""
        print(f"\n⚠️ {message}")

    def print_finding_connections(self, path):
        """Prints the message for finding connections."""
        print(f"🔍 Finding connections for '{path}'...")

    def print_connections_found(self):
        """Prints the header for found connections."""
        print("🔗 Found connections:")

    def print_connection(self, name, score):
        """Prints a single connection with its score."""
        print(f"  - {name} (Score: {score:.2f})")

    def print_connection_warning(self, name):
        """Prints a warning for a connection that can't be read."""
        print(f"  - ⚠️ Warning: Could not read content for '{name}'. Skipping.")

    def print_generating_moc(self):
        """Prints the message for generating the MOC."""
        print("\n🧠 Generating Map of Content with Gemini...")

    def print_gemini_error(self, response):
        """Prints an error message from the Gemini API."""
        print(f"\n❌ Gemini Generation Error: {response}")

    def print_invalid_data(self, response):
        """Prints a message for invalid data from Gemini."""
        print(f"\n❌ Gemini returned invalid data. Response: {response}")

    def print_success(self, path):
        """Prints the success message with the save path."""
        print(f"\n✅ Success! Map of Content saved to: {path}")

    def print_save_error(self, path, error):
        """Prints an error message for saving a file."""
        print(f"\n❌ Error saving MOC to {path}: {error}")

