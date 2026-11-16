# Local AI Sales Analyst

A Streamlit app that lets you ask questions about sample sales data. It uses
Qwen 2.5 1.5B through Ollama to generate a read-only SQLite query, then
summarizes the results.

## Setup on Windows

``powershell
py -m venv .venv
ollama pull qwen2.5:1.5b
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

<img width="1917" height="971" alt="image" src="https://github.com/user-attachments/assets/1bd17228-a064-48a7-a12d-18ac9e7b1b25" />

<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/83f25029-6574-4b3a-8434-fcd2e411076f" />
