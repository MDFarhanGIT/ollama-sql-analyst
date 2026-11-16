# Local AI Sales Analyst

A Streamlit app that lets you ask questions about sample sales data. It uses
Qwen 2.5 1.5B through Ollama to generate a read-only SQLite query, then
summarizes the results.

## Setup on Windows

```powershell
py -m venv .venv
ollama pull qwen2.5:1.5b
.\.venv\Scripts\python.exe -m pip install -r requirements.txt