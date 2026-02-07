# How to Choose an Agent and Create Personas

## 🎯 Overview

The workflow is:
1. **Phase A**: Analyze your agent codebase → generates `agent_map.json`
2. **Phase B**: Use `agent_map.json` → creates personas tailored to your agent

The agent selection happens in **Phase A** - you point the analyzer at your agent's codebase.

---

## 📋 Step-by-Step Guide

### Step 1: Choose Your Agent (Phase A)

You can analyze any agent codebase by pointing the analyzer at it:

```bash
# Analyze an agent codebase
python analyze.py /path/to/your/agent/repo

# Or analyze a specific directory
python analyze.py /path/to/agent/src

# With custom output name
python analyze.py /path/to/agent/repo -o my_agent_map.json

# Skip AI analysis (faster, offline)
python analyze.py /path/to/agent/repo --skip-ai
```

**What it does:**
- Scans the codebase for agent patterns
- Detects tools, prompts, memory systems
- Analyzes agent type (support, sales, scheduling, etc.)
- Extracts agent purpose and capabilities
- Generates `agent_map.json` with all this info

**Example:**
```bash
# Analyze a customer support agent
python analyze.py ~/projects/customer-support-bot -o support_agent_map.json

# Analyze a sales agent
python analyze.py ~/projects/sales-assistant -o sales_agent_map.json
```

---

### Step 2: Create Personas Based on Agent (Phase B)

Once you have `agent_map.json`, use it to create personas:

```bash
# Create personas from agent map
python persona_builder.py agent_map.json

# With AI-generated personas
python persona_builder.py agent_map.json -g 3

# With sample messages
python persona_builder.py agent_map.json -g 2 -s 3

# Custom output file
python persona_builder.py agent_map.json -o my_personas.json
```

**What it does:**
- Reads `agent_map.json` to understand:
  - Agent type (support, sales, scheduling, etc.)
  - Agent purpose
  - Available tools
  - Risk factors
- Loads appropriate persona templates for that agent type
- Optionally generates AI personas tailored to your agent
- Creates `persona_library.json`

---

## 🔍 How Personas Are Tailored to Your Agent

The persona builder uses information from `agent_map.json`:

### 1. **Agent Type Detection**
```json
{
  "metadata": {
    "type": "sales",  // ← Used to select persona templates
    "purpose": "An automotive service/dealership AI agent..."
  }
}
```

**Persona templates by type:**
- `support` → Support personas (Frustrated Customer, Confused First-Timer, etc.)
- `sales` → Sales personas (Budget-Conscious Researcher, Impulsive Buyer, etc.)
- `scheduling` → Scheduling personas (Last-Minute Booker, Meticulous Planner, etc.)
- `custom` → Generic personas (Happy Path User, Edge-Case Explorer, etc.)

### 2. **AI Persona Generation**
When you use `-g` flag, AI generates personas based on:
- Agent type
- Agent purpose
- Available tools
- Risk factors (PII handling, critical actions)

**Example:**
```bash
# Generate 3 AI personas tailored to your agent
python persona_builder.py agent_map.json -g 3
```

This will create personas that:
- Match your agent's domain
- Test relevant edge cases
- Use appropriate communication styles
- Consider your agent's tools and capabilities

---

## 📊 Complete Workflow Example

### Example 1: Customer Support Agent

```bash
# Step 1: Analyze the support agent
python analyze.py ~/projects/support-bot -o support_agent_map.json

# Step 2: Create personas
python persona_builder.py support_agent_map.json -g 3 -s 2

# Output: persona_library.json with support-specific personas
```

**Result:**
- Personas like "Frustrated Customer", "Confused First-Timer"
- Tailored to support scenarios
- Sample messages appropriate for support interactions

---

### Example 2: Sales Agent

```bash
# Step 1: Analyze the sales agent
python analyze.py ~/projects/sales-assistant -o sales_agent_map.json

# Step 2: Create personas
python persona_builder.py sales_agent_map.json -g 3

# Output: persona_library.json with sales-specific personas
```

**Result:**
- Personas like "Budget-Conscious Researcher", "Impulsive Buyer"
- Tailored to sales scenarios
- Appropriate for product inquiries, pricing, etc.

---

### Example 3: Custom Agent Type

```bash
# Step 1: Analyze custom agent
python analyze.py ~/projects/my-custom-agent -o custom_agent_map.json

# Step 2: Create personas (will use generic templates)
python persona_builder.py custom_agent_map.json -g 5

# Output: persona_library.json with generic + AI personas
```

**Result:**
- Falls back to generic personas if type unknown
- AI generates custom personas based on agent purpose
- Still tailored to your agent's tools and capabilities

---

## 🎯 Key Points

### Agent Selection = Codebase Path
- **You choose the agent** by pointing `analyze.py` at its codebase
- Can be local directory or repo path
- Analyzer discovers agent type automatically

### Personas Are Automatic
- Personas are **automatically tailored** based on:
  - Agent type detected in Phase A
  - Agent purpose extracted from code
  - Tools available in the agent
  - Risk factors identified

### You Can Customize
- Use `-g` flag to generate AI personas (tailored to your agent)
- Use `-s` flag to generate sample messages
- Use `--skip-ai` to use only templates (faster, offline)

---

## 🔄 Full Pipeline

```bash
# 1. Analyze agent codebase (Phase A)
python analyze.py /path/to/agent/repo -o agent_map.json

# 2. Create personas (Phase B1)
python persona_builder.py agent_map.json -g 3 -o persona_library.json

# 3. Create scenarios (Phase B2)
python scenario_builder.py agent_map.json -o scenario_catalog.json

# 4. Set coverage goals (Phase B3)
python coverage_builder.py agent_map.json -o test_configuration.json

# 5. Generate test suite (Phase B4)
python testsuite_builder.py agent_map.json \
  persona_library.json \
  scenario_catalog.json \
  test_configuration.json \
  -o test_suite.json

# 6. Execute tests (Phase C)
python execute_tests.py test_suite.json agent_map.json --mock
```

---

## 💡 Tips

1. **Start with Phase A**: Always run `analyze.py` first to create `agent_map.json`
2. **Use AI personas**: The `-g` flag creates personas tailored to YOUR agent
3. **Check agent type**: Look at `agent_map.json` → `metadata.type` to see what was detected
4. **Multiple agents**: Create separate `agent_map.json` files for each agent you want to test

---

## 📝 Example: Checking Your Agent Map

After running Phase A, check what was detected:

```bash
# View agent map
cat agent_map.json | jq '.metadata'

# Output example:
# {
#   "type": "sales",
#   "purpose": "An automotive service/dealership AI agent...",
#   "framework": "custom",
#   "language": "python"
# }
```

This tells you:
- What type of personas will be loaded
- What the AI will use to generate custom personas
- What scenarios will be relevant

---

## ✅ Summary

**To choose an agent and create personas:**

1. **Point analyzer at agent codebase:**
   ```bash
   python analyze.py /path/to/agent/repo -o agent_map.json
   ```

2. **Create personas from agent map:**
   ```bash
   python persona_builder.py agent_map.json -g 3
   ```

3. **Personas are automatically tailored** based on:
   - Agent type (support/sales/scheduling)
   - Agent purpose
   - Available tools
   - Risk factors

**That's it!** The system automatically selects appropriate personas based on your agent.
