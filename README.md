# BotAgente

## Project Setup with `pyproject.toml`

This project uses **Poetry** for dependency management instead of `requirements.txt`. Follow the steps below to set up and use the project.

---

## Installation

### 1. Install Poetry
First, make sure Poetry is installed. If you don’t have it, install it using:

```sh
pip install poetry
```

Or install it using the official method:
```sh
curl -sSL https://install.python-poetry.org | python3 -
```

### 2. Clone the Repository using SSH
```sh
git clone git@github.com:johnometalman/botAgente.git
cd botAgente
```

### 3. Create an activate Virtual Environment
```sh
python -m venv venv
source venv/bin/activate  # On macOS/Linux
venv\Scripts\activate    # On Windows
```

### 4. With Venv activated install Dependencies
Using Poetry:
```sh
poetry install
```
If you're using `requirements.txt`:
```sh
pip install -r requirements.txt
```

### 5. Update the core.py file
Once the dependecies are instalated, you must fund the `core.py` file 
```sh
venv > lib > pywhatkit > core > core.py
```
and **replace all the code** with code from the `toreplace_corepy.py` file
```sh
py-files > pywhatkit > toreplace_corepy.py
```


### 6. Run the Project
Once inside the virtual environment, you can run your Python scripts as usual:
After setting up the files execute them, eg. `app.py` with:
```sh
python py-files\pywhatkit\app.py
```
Or, if using Poetry:
```sh
poetry run python py-files\pywhatkit\app.py 
```

---

## Managing Dependencies

### Add a New Dependency
To install a new package and update `pyproject.toml` automatically:
```sh
poetry add package_name
```

### Remove a Dependency
```sh
poetry remove package_name
```

### Update Dependencies
To update all dependencies:
```sh
poetry update
```

To update a specific package:
```sh
poetry update package_name
```

---

## Environment Variables
This project relies on environment variables stored in a `.env` file. Create a `.env` file in the project root and add the following:

```ini
NOTION_TOKEN=your_notion_token
DATABASE_ID=your_database_id
WHATSAPP_GROUP_ID=your_whatsapp_group_id
WHATSAPP_NUMBER=your_whatsapp_number_here
```

---

## How the Project Works
- The script fetches data from a Notion database using the Notion API.
- It formats the retrieved data into a structured message.
- The message is sent to a WhatsApp group using `pywhatkit`.
- Once sent, the script updates the Notion database to mark the message as "Sent".

---

## Deploying or Sharing the Project
To ensure others can install the project easily, share your repository and let them run:
```sh
poetry install
```
This will install all dependencies listed in `pyproject.toml` and `poetry.lock`.

---

## License
This project is licensed under [MIT License](LICENSE).

---

### Author
John J Meza  
@johnometalman

