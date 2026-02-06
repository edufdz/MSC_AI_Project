# Setup Instructions

## Virtual Environment

A virtual environment has been created at `venv/`. All dependencies are installed there.

## Using the Virtual Environment

### Option 1: Activate manually
```bash
source venv/bin/activate
python3 scripts/16_build_index.py
python3 chat_simulator.py
```

### Option 2: Use the run.sh helper script
```bash
./run.sh python3 scripts/16_build_index.py
./run.sh python3 chat_simulator.py
```

### Option 3: Use python3 with venv directly
```bash
venv/bin/python3 scripts/16_build_index.py
venv/bin/python3 chat_simulator.py
```

## Installed Dependencies

All dependencies from `requirements.txt` are installed:
- ✅ numpy>=1.24.0
- ✅ faiss-cpu>=1.7.4
- ✅ openai>=1.0.0
- ✅ python-dotenv>=1.0.0

## Next Steps

1. Make sure you have a `.env` file with `OPENAI_API_KEY=your_key_here`
2. Build the vector index: `./run.sh python3 scripts/16_build_index.py`
3. Run the chat simulator: `./run.sh python3 chat_simulator.py`
