# WCAG Checker

This project is a tool for checking websites 
to ensure they meet WCAG (Web Content Accessibility Guidelines) requirements. 

It provides various report formats and the ability to report issues directly to YouTrack.

## Features

- Check contrast ratios on websites.
- Use Axe to check wcag rules on websites.
- Support for various report formats: JSON, Markdown, HTML.
- Integration with YouTrack for issue creation.
- Multiple sources for color extraction.
- Suggestion of alternative colors that meet the WCAG requirements.
- Debugging and simulation modes.
- Multiple inputs can be checked at once. 
- ....and more

## Installation

### Prerequisites
- Git (for cloning the repository)
- Python 3.6 or higher
- pip (Python package manager)
- Chrome Browser (to run the script, will be remote controlled by the script)

1. Clone the repository:
```bash
git clone <repository-url>
```
2. Navigate to the project directory:
```bash
cd wcag_checker
```
3. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
```
4. Activate the virtual environment:
 
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

5. Install the dependencies:
```bash
pip install -r requirements.txt
```

### Installation with `uv` (Python Package Manager)

If you are using `uv` as your Python Package Manager, you can install the dependencies as follows:

1. Install `uv` if it is not already installed:
```bash
pip install uv
```

2. Install the dependencies from the requirements.txt file:
```bash
uv install -r requirements.txt
```
3. Sync the dependencies (can be used to update the dependencies):
```bash
uv sync
```
Ensure all dependencies are correctly installed before running the project.

4. run it
```bash
uv run src/main.py
```
Follow the instructions in the "Usage" section.


### build executable
1. Install `pyinstaller` if you haven't already:
```bash
pip install pyinstaller
```
2. Build the executable:
```bash
pyinstaller contrast_checker.spec
```
The executable will be created in the `dist` folder.
 
   
## Usage
The main script is located in the `src` directory. You can run it from the command line.

Run the script (and see the help message) with:
```bash
python ./src/main.py
```
or 
```bash
uv run src/main.py
```

#### Command Line Help
To see the help message for the script, run the tool with the `-h` or `--help` option

The script will analyse the website and generate a report based on the selected format.    
It has 2 modes `axe` or `contrast`. Dependent on the mode other options are needed or not used. 

If you choose to report issues to YouTrack, follow the prompts to enter your YouTrack credentials and issue details.    
The script will create issues in YouTrack for any contrast ratio violations found on the website.
Since Youtrack does not allow more than 500 attachments per issue, the script will upload only the first 500 images found on the page.
Also the Youtrack issue text is limited to 64k characters, so the script will truncate the text if it exceeds this limit.

You can also use the `--debug` flag to enable debugging mode, which provides additional information about the script's execution.

If you want to simulate the script's behavior without actually checking a website, 
use the `--simulate` flag with a pre generated JSON file as argument.

### Examples
```bash
python .\src\main.py contrast --inputs "http://example.com" --youtrack --youtrack_api_key "your_api_key" --youtrack_project "0-2"
```
This command will check the contrast ratio on `http://example.com`, generate a JSON report, and create issues in YouTrack for any violations found.
    
```bash
python .\src\main.py axe --simulate "output/contrast_result.json"
```
This command will simulate the checking process using the predefined JSON data from `output/contrast_result.json`.    
All reports are generated for the JSON file.

```bash
python .\src\main.py axe --inputs "http://example.com"
```
This command use axe to check the page on `http://example.com`, 

```bash
python .\src\main.py contrast --inputs "config:inputs.txt" --use_antialias --color_source element
```
This command will check the contrast ratio on all inputs listed in `inputs.txt`,
use the elements as color source.

### Notes
Set the `--login` parameter to the login URL of your system or use it as a startpoint where other relative inputs base on.        
The default URL is `` (empty; which will be ignored).    
You can leverage the `--login` parameter to specify a login URL that will be called first before checking the other inputs.

The Login URL is always called first and then all processed inputs, in the same session.

The inputs you provide to scan a Page are relative to the login URL starting with '/'.    
You can specify multiple inputs in a textfile, where each URL is a separate line.    
Passing the textfile with the `--inputs` parameter and a value prefixed `config:<myfile>`.

For Example (file with inputs defined):    
```plaintext
/servlet/MenuItem
/servlet/Browse
```
If the line starts with a '#' character, it is ignored.

### Actions

You can use special actions in your config file (such as for inputs or test flows) by prefixing them with `@`.     
These actions control the tool's behavior during testing and navigation.

The actions are executed in the order they appear in the file.

The actions can be used to automate interactions with the web page, such as clicking buttons, 
waiting for elements to load, or analyzing the page for accessibility issues.

> Actions start with a `@` symbol and are followed by a command name.
> Example: `@<action_name>: <optional_parameter>`    
> Optional parameters for actions must have a : delimiter
> and must be specified in the same line (one line per action).    

**Available actions:**

you can see the available actions by running the script with the `actions` mode parameter:
```bash
python ./src/main.py actions
```

some (but not all are listed here):
- `@click: <selector>`  
- `@analyse`  
- `@wait: <seconds|loaded|[selector]>`  
- `@input: <selector>=<text>`  
- `@clear: <selector>`
- `@scroll: <direction|selector>`
- `@screenshot: <filename>`
- `@navigate: <url>`
- `@back`
- `@refresh`
- `@hover: <selector>`
- `@select: <selector>=<option_value>`
- `@resize: <size|[predefinied]|full>`

**Notes:**
- Actions can be placed in config file between or instead of inputs.
- Each action should be on its own line.
- Lines starting with `#` are treated as comments and ignored.

**Example config file:**
```
/servlet/BrowseUser
@click: #my-button
@wait: loaded
@analyse "My page Title"
```

## Troubleshooting
- If you encounter issues with the script, make sure you have all the required dependencies installed.
- Check the console output for any error messages or warnings (try the --debug option).
- Make sure your target System is configured correctly and accessible.
- If the remote control of the Browser failed, try running it again—maybe the browser was not started correctly.
- If you are using the YouTrack integration, ensure that your API key and project ID are correct.
- If you are using the `--simulate` option, make sure the JSON file exists and is in the correct format.
- You will not see the Browser window, it is silently running in the background.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Acknowledgments
- [WCAG](https://www.w3.org/WAI/WCAG21/) for providing guidelines on web accessibility.
- [YouTrack](https://www.jetbrains.com/youtrack/) for issue tracking and project management.
- [OpenCV](https://opencv.org/) for image processing capabilities.
- [NumPy](https://numpy.org/) for numerical operations.
- [Requests](https://docs.python-requests.org/en/latest/) for making HTTP requests.
- [PyInstaller](https://pyinstaller.org/) for creating executable files.
- [Axe](https://www.deque.com/axe/) for automated WCAG validation.
- [Rich](https://rich.readthedocs.io/en/stable/) for creating visually appealing console outputs.

