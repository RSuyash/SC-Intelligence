import os
import sys
import time
import threading
from typing import Callable, Any

class ConsoleFormatter:
    """
    A console formatter designed with an Apple-inspired aesthetic.
    Features include fluid animations, a clean layout, and a focus on user experience.
    """

    # --- ANSI Escape Codes for Styling ---
    _COLORS = {
        "HEADER": "\033[95m",
        "BLUE": "\033[94m",
        "CYAN": "\033[96m",
        "GREEN": "\033[92m",
        "WARNING": "\033[93m",
        "FAIL": "\033[91m",
        "ENDC": "\033[0m",
        "BOLD": "\033[1m",
        "UNDERLINE": "\033[4m",
        "GRAY": "\033[90m"
    }
    
    _TICK = _COLORS['GREEN'] + '✔' + _COLORS['ENDC']
    _CROSS = _COLORS['FAIL'] + '✖' + _COLORS['ENDC']
    _WARN = _COLORS['WARNING'] + '⚠' + _COLORS['ENDC']

    def __init__(self):
        self._activity_thread = None
        self._stop_event = threading.Event()
        self._spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']

    def _format(self, style: str, text: str) -> str:
        """Applies a style to the given text."""
        return f"{self._COLORS.get(style.upper(), '')}{text}{self._COLORS['ENDC']}"

    def _clear_line(self):
        """Clears the current line in the console."""
        sys.stdout.write('\r' + ' ' * (os.get_terminal_size().columns - 1) + '\r')
        sys.stdout.flush()

    def _spinner_animation(self, message: str):
        """The animation loop for the spinner."""
        i = 0
        while not self._stop_event.is_set():
            spinner_char = self._spinner_chars[i % len(self._spinner_chars)]
            sys.stdout.write(f"\r{self._format('blue', spinner_char)} {message}")
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1

    def start_activity(self, message: str = "Processing..."):
        """
        Displays an animated spinner for a long-running process.
        This should be followed by a call to `end_activity`.
        
        Example:
            formatter.start_activity("Thinking hard...")
            # your long task here
            formatter.end_activity("Done thinking!")
        """
        self._stop_event.clear()
        self._activity_thread = threading.Thread(target=self._spinner_animation, args=(message,))
        self._activity_thread.start()

    def end_activity(self, final_message: str):
        """Stops the spinner and displays a final confirmation message."""
        if self._activity_thread and self._activity_thread.is_alive():
            self._stop_event.set()
            self._activity_thread.join()
        self._clear_line()
        sys.stdout.write(f"{self._TICK} {final_message}\n")
        sys.stdout.flush()
        
    def animate_progress(self, message: str, duration: float = 1.5):
        """Displays a message with a simple loading animation."""
        for i in range(4):
            self._clear_line()
            sys.stdout.write(f"{message}{'.' * i}")
            sys.stdout.flush()
            time.sleep(duration / 4)
        self._clear_line()

    def print_init(self):
        """Prints the initialization sequence."""
        self.animate_progress(f"{self._format('bold', '✨ Initializing Knowledge Architect')}", 1.0)
        print(f"{self._format('bold', '✨ Knowledge Architect')} {self._format('gray', 'v1.0')}")
        print("-" * 30)

    def print_loaded_notes(self, note_count: int, block_count: int):
        """Prints the number of loaded notes and blocks with a clean format."""
        print(f"📂 Knowledge Base: {self._format('bold', note_count)} notes, {self._format('bold', block_count)} blocks.")

    def print_processing_file(self, file_path: str):
        """Prints the file being processed."""
        print(f"\n📄 {self._format('bold', 'Now Processing')}\n   {self._format('gray', file_path)}")

    def get_input(self, prompt: str) -> str:
        """Gets input from the user with a styled prompt."""
        return input(f"\n{self._format('bold', '📝 ' + prompt)}\n{self._format('blue', '❯')} ").strip().replace('\\', '/')

    def print_error(self, message: str):
        """Prints a styled error message."""
        print(f"\n{self._CROSS} {self._format('bold', self._format('fail', 'Error'))}: {message}")

    def print_warning(self, message: str):
        """Prints a styled warning message."""
        print(f"{self._WARN} {self._format('bold', self._format('warning', 'Warning'))}: {message}")

    def print_connections_found(self):
        """Prints the header for found connections."""
        print(f"\n🔗 {self._format('bold', 'Connections Found')}")

    def print_connection(self, name: str, score: float):
        """Prints a single connection with its score, styled as a list item."""
        score_str = self._format('gray', f"({score:.2f})")
        print(f"  {self._format('gray', '└─')} {name} {score_str}")

    def print_connection_warning(self, name: str):
        """Prints a warning for a connection that can't be read."""
        print(f"  {self._format('gray', '└─')} {self._format('warning', f'Could not read content for "{name}". Skipping.')}")
        
    def print_finding_connections(self, file_path: str):
        """Prints a message indicating that connections are being found for the given note."""
        print(f"\n{self._format('cyan', '🔍 Finding connections for')} {self._format('gray', file_path)}...")

    def print_generating_moc(self):
        """Prints a message indicating that the MOC is being generated."""
        print(f"\n{self._format('cyan', '⚙️ Generating Map of Content with Gemini...')}")

    def print_gemini_error(self, response: Any):
        """Prints an error message from the Gemini API."""
        self.print_error("The AI model returned an error.")
        print(f"   {self._format('gray', str(response))}")
        
    def print_invalid_data(self, response: Any):
        """Prints a message for invalid data from Gemini."""
        self.print_error("The AI model returned invalid or unparsable data.")
        print(f"   {self._format('gray', str(response))}")

    def print_success(self, path: str):
        """Prints the final success message."""
        print(f"\n{self._format('green', self._format('bold', '✅ Success!'))}")
        print(f"   Map of Content saved to:\n   {self._format('underline', self._format('gray', path))}")

    def print_save_error(self, path: str, error: Exception):
        """Prints an error message for saving a file."""
        self.print_error(f"Failed to save file.")
        print(f"   Path: {self._format('gray', path)}\n   Reason: {self._format('gray', str(error))}")


# --- Example Usage ---
def run_demo():
    """A demonstration of the ConsoleFormatter in action."""
    formatter = ConsoleFormatter()

    # Initialization
    formatter.print_init()
    time.sleep(1)

    # Loading
    formatter.print_loaded_notes(127, 843)
    time.sleep(1.5)

    # Getting user input
    target_file = formatter.get_input("Enter the path to the note you want to analyze:")
    formatter.print_processing_file(target_file)
    time.sleep(1)

    # Animated activity for finding connections
    formatter.start_activity(f"Finding connections for '{os.path.basename(target_file)}'")
    time.sleep(3) # Simulate a long search
    formatter.end_activity("Search complete.")

    # Displaying results
    formatter.print_connections_found()
    formatter.print_connection("Quantum Entanglement Explained", 0.94)
    formatter.print_connection("Theoretical Physics in the 21st Century", 0.87)
    formatter.print_connection_warning("Old_Notes/broken_link.md")
    formatter.print_connection("The Spacetime Fabric", 0.75)
    time.sleep(1.5)

    # Another animated activity for AI generation
    print() # Add a newline for spacing
    formatter.start_activity("Generating Map of Content with Gemini")
    time.sleep(4) # Simulate AI thinking
    formatter.end_activity("Content generated.")
    
    # Errors and Warnings
    formatter.print_warning("The generated content may require minor edits for clarity.")
    formatter.print_gemini_error("API key invalid or expired.")
    time.sleep(2)

    # Success
    final_path = os.path.join(os.path.dirname(target_file) or '.', 'MOC - ' + os.path.basename(target_file))
    formatter.print_success(final_path)

if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n✨ Demo stopped. Goodbye!")
        # Ensure the cursor is visible and colors are reset on exit
        sys.stdout.write("\033[?25h")
        sys.stdout.write(ConsoleFormatter._COLORS['ENDC'])