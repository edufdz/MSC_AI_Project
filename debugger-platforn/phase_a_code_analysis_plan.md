Phase A: Agent Code Analysis System - Technical Implementation Plan
Executive Summary
This document outlines how to build an AI-powered code analysis system that automatically discovers, understands, and maps agent architectures. The system will scan codebases to identify agentic patterns, extract tool definitions, build dependency graphs, and understand the agent's intended behavior—similar to how Cursor and Claude Code work, but specialized for agent testing platforms.

1. System Architecture Overview
1.1 High-Level Flow
User Input (Repo/Code) 
    ↓
Static Analysis Layer (AST parsing, pattern matching)
    ↓
AI Analysis Layer (LLM-powered semantic understanding)
    ↓
Graph Construction (Build agent architecture map)
    ↓
Validation & Refinement (User confirms/corrects)
    ↓
Structured Output (Agent Map JSON + Visual Diagram)
1.2 Core Components

Code Ingestion Engine: Handles repo cloning, file traversal, language detection
Static Analysis Engine: AST parsing, symbol resolution, dataflow analysis
Pattern Recognition System: Detects common agent frameworks and patterns
AI Semantic Analyzer: Uses LLM to understand intent and behavior
Graph Builder: Constructs agent architecture representation
Risk Analyzer: Identifies PII, critical operations, compliance concerns
Interactive Refinement UI: Allows user to validate and correct findings


2. Code Ingestion Engine
2.1 Multi-Source Support
GitHub/GitLab Integration
python# Pseudo-code for repo ingestion
def ingest_repository(repo_url, branch="main"):
    """
    Clone repository and prepare for analysis
    """
    # 1. Clone repo (shallow clone for speed)
    repo_path = git.clone(repo_url, depth=1, branch=branch)
    
    # 2. Detect project structure
    project_type = detect_project_type(repo_path)  # Python, JS/TS, etc.
    
    # 3. Identify entry points
    entry_points = find_entry_points(repo_path, project_type)
    
    # 4. Build file dependency graph
    file_graph = build_file_dependencies(repo_path)
    
    return {
        "path": repo_path,
        "type": project_type,
        "entry_points": entry_points,
        "file_graph": file_graph
    }
Local Upload Support

ZIP file upload with extraction
Direct folder selection (for desktop app)
Incremental re-analysis when files change

API Endpoint Mode

User provides OpenAPI spec or similar
System generates mock agent structure from API docs
Less detailed but works for black-box systems

2.2 Language Detection & Filtering
Supported Languages (Priority Order)

Python (most common for agents)

Frameworks: LangChain, LangGraph, AutoGPT, CrewAI, Haystack
Patterns: function decorators, class-based agents, OpenAI function calling


JavaScript/TypeScript

Frameworks: LangChain.js, Vercel AI SDK, Flowise
Patterns: async/await chains, middleware patterns


Go/Rust (emerging agent languages)

Pattern-based detection only



File Filtering Strategy
pythondef filter_relevant_files(repo_path):
    """
    Identify files likely to contain agent logic
    """
    include_patterns = [
        "**/agent*.py", "**/agents/*.py",
        "**/tools/*.py", "**/function*.py",
        "**/chain*.py", "**/workflow*.py",
        "**/*llm*.py", "**/*openai*.py",
        # Similar patterns for JS/TS
    ]
    
    exclude_patterns = [
        "**/tests/**", "**/test_*.py",
        "**/node_modules/**", "**/__pycache__/**",
        "**/venv/**", "**/dist/**"
    ]
    
    # Use gitignore-style matching
    files = find_files(repo_path, include_patterns, exclude_patterns)
    
    # Sort by likelihood (files with "agent" in name come first)
    return prioritize_files(files)

3. Static Analysis Engine
3.1 AST Parsing
Multi-Language Parser Strategy
Use Tree-sitter for universal parsing:

Single parser for 40+ languages
Incremental parsing (fast re-analysis)
Robust error recovery (handles incomplete code)

pythonfrom tree_sitter import Language, Parser
import tree_sitter_python
import tree_sitter_javascript

def parse_file(file_path, language):
    """
    Parse source file into AST
    """
    parser = Parser()
    
    if language == "python":
        parser.set_language(Language(tree_sitter_python.language()))
    elif language in ["javascript", "typescript"]:
        parser.set_language(Language(tree_sitter_javascript.language()))
    
    with open(file_path, 'rb') as f:
        source_code = f.read()
    
    tree = parser.parse(source_code)
    return tree, source_code
3.2 Symbol Extraction
What to Extract

Function definitions (potential tools)
Class definitions (potential agent classes)
Import statements (framework detection)
Decorator usage (LangChain @tool, @chain, etc.)
API calls (OpenAI, Anthropic, etc.)
Configuration objects (prompts, model names)

pythondef extract_symbols(ast, source_code, file_path):
    """
    Extract relevant symbols from AST
    """
    symbols = {
        "functions": [],
        "classes": [],
        "imports": [],
        "decorators": [],
        "api_calls": [],
        "config": []
    }
    
    # Query for function definitions
    function_query = """
    (function_definition
        name: (identifier) @func_name
        parameters: (parameters) @params
        body: (block) @body)
    """
    
    functions = query_ast(ast, function_query)
    
    for func in functions:
        func_info = {
            "name": get_text(func["func_name"], source_code),
            "params": extract_parameters(func["params"], source_code),
            "docstring": extract_docstring(func["body"], source_code),
            "decorators": extract_decorators(func, ast, source_code),
            "location": {
                "file": file_path,
                "line": func["func_name"].start_point[0]
            }
        }
        symbols["functions"].append(func_info)
    
    # Similar for classes, imports, etc.
    
    return symbols
3.3 Dataflow Analysis
Track Tool Dependencies
pythondef build_dataflow_graph(symbols, file_graph):
    """
    Build graph showing how functions call each other
    """
    dataflow = nx.DiGraph()
    
    # Add nodes for all functions
    for func in symbols["functions"]:
        dataflow.add_node(func["name"], type="function", **func)
    
    # Add edges for function calls
    for func in symbols["functions"]:
        called_functions = extract_function_calls(func["body_ast"])
        for called in called_functions:
            if called in dataflow:
                dataflow.add_edge(func["name"], called, type="calls")
    
    # Add cross-file dependencies
    for file_a, file_b in file_graph.edges():
        # Connect functions between files based on imports
        connect_cross_file_calls(dataflow, file_a, file_b)
    
    return dataflow

4. Pattern Recognition System
4.1 Framework Detection
Signature-Based Detection
pythonFRAMEWORK_SIGNATURES = {
    "langchain": {
        "imports": [
            "from langchain import",
            "from langchain.agents import",
            "from langchain.chains import",
            "from langchain_community import",
            "from langchain_core import"
        ],
        "decorators": ["@tool", "@chain"],
        "classes": ["BaseTool", "BaseAgent", "AgentExecutor"],
        "functions": ["initialize_agent", "create_react_agent"]
    },
    
    "langgraph": {
        "imports": [
            "from langgraph.graph import",
            "from langgraph.prebuilt import"
        ],
        "classes": ["StateGraph", "MessageGraph"],
        "functions": ["add_node", "add_edge", "compile"]
    },
    
    "openai_native": {
        "imports": ["from openai import"],
        "functions": ["chat.completions.create"],
        "config_keys": ["tools", "functions", "function_call"]
    },
    
    "anthropic_native": {
        "imports": ["from anthropic import"],
        "functions": ["messages.create"],
        "config_keys": ["tools", "tool_choice"]
    },
    
    "autogpt": {
        "imports": ["from autogpt import"],
        "classes": ["Agent", "AutoGPT"],
        "config_files": ["ai_settings.yaml"]
    },
    
    "crewai": {
        "imports": ["from crewai import"],
        "classes": ["Agent", "Task", "Crew"]
    }
}

def detect_framework(symbols, files):
    """
    Detect which agent framework is being used
    """
    scores = {framework: 0 for framework in FRAMEWORK_SIGNATURES}
    
    # Check imports
    for imp in symbols["imports"]:
        for framework, sig in FRAMEWORK_SIGNATURES.items():
            for pattern in sig.get("imports", []):
                if pattern in imp["module"]:
                    scores[framework] += 2
    
    # Check decorators
    for dec in symbols["decorators"]:
        for framework, sig in FRAMEWORK_SIGNATURES.items():
            if dec["name"] in sig.get("decorators", []):
                scores[framework] += 3
    
    # Check classes
    for cls in symbols["classes"]:
        for framework, sig in FRAMEWORK_SIGNATURES.items():
            # Check if class inherits from framework base classes
            if any(base in cls["bases"] for base in sig.get("classes", [])):
                scores[framework] += 3
    
    # Return framework with highest score
    detected = max(scores.items(), key=lambda x: x[1])
    
    if detected[1] > 0:
        return detected[0]
    else:
        return "custom"  # No known framework
4.2 Tool Extraction Patterns
LangChain Tools
pythondef extract_langchain_tools(symbols):
    """
    Extract tool definitions from LangChain code
    """
    tools = []
    
    # Pattern 1: @tool decorator
    for func in symbols["functions"]:
        if any(dec["name"] == "tool" for dec in func["decorators"]):
            tool = {
                "id": generate_id(func["name"]),
                "name": func["name"],
                "description": func["docstring"],
                "parameters": func["params"],
                "source": "langchain_decorator",
                "location": func["location"]
            }
            tools.append(tool)
    
    # Pattern 2: BaseTool subclasses
    for cls in symbols["classes"]:
        if "BaseTool" in cls["bases"]:
            # Extract _run or _arun method as the tool implementation
            run_method = find_method(cls, "_run") or find_method(cls, "_arun")
            tool = {
                "id": generate_id(cls["name"]),
                "name": cls["name"],
                "description": cls["docstring"] or run_method["docstring"],
                "parameters": run_method["params"],
                "source": "langchain_class",
                "location": cls["location"]
            }
            tools.append(tool)
    
    # Pattern 3: Tool objects in lists/arrays
    for var in symbols["variables"]:
        if "tools" in var["name"].lower():
            # Parse list/array of tool objects
            tool_list = parse_tool_list(var["value"])
            tools.extend(tool_list)
    
    return tools
OpenAI Function Calling
pythondef extract_openai_tools(symbols, source_code):
    """
    Extract tool definitions from OpenAI function calling
    """
    tools = []
    
    # Find chat.completions.create calls with tools parameter
    for api_call in symbols["api_calls"]:
        if "chat.completions.create" in api_call["function"]:
            # Extract tools parameter
            tools_param = api_call["kwargs"].get("tools")
            
            if tools_param:
                # Parse tool schema (usually JSON/dict)
                tool_schemas = parse_tool_schemas(tools_param, source_code)
                
                for schema in tool_schemas:
                    tool = {
                        "id": generate_id(schema["function"]["name"]),
                        "name": schema["function"]["name"],
                        "description": schema["function"]["description"],
                        "parameters": schema["function"]["parameters"],
                        "source": "openai_function_calling",
                        "location": api_call["location"]
                    }
                    tools.append(tool)
    
    return tools
Custom Tool Detection
pythondef detect_custom_tools(symbols, dataflow):
    """
    Heuristic detection of tools in custom implementations
    """
    tools = []
    
    # Heuristics:
    # 1. Functions that make external API calls
    # 2. Functions called from agent loop
    # 3. Functions with "tool", "action", "function" in name
    
    for func in symbols["functions"]:
        score = 0
        
        # Check if function makes API calls
        if has_http_requests(func) or has_database_calls(func):
            score += 3
        
        # Check if called from agent main loop
        callers = list(dataflow.predecessors(func["name"]))
        if any("agent" in caller.lower() or "run" in caller.lower() 
               for caller in callers):
            score += 2
        
        # Check naming patterns
        if any(keyword in func["name"].lower() 
               for keyword in ["tool", "action", "function", "execute"]):
            score += 2
        
        # Check for parameters that look like tool inputs
        if has_user_facing_params(func["params"]):
            score += 1
        
        if score >= 4:  # Threshold
            tool = {
                "id": generate_id(func["name"]),
                "name": func["name"],
                "description": func["docstring"] or "Custom tool (auto-detected)",
                "parameters": func["params"],
                "source": "custom_heuristic",
                "confidence": min(score / 7, 1.0),  # 0-1 scale
                "location": func["location"]
            }
            tools.append(tool)
    
    return tools
4.3 Prompt Extraction
pythondef extract_prompts(symbols, files):
    """
    Find system prompts, templates, and instructions
    """
    prompts = []
    
    # Pattern 1: String variables with keywords
    for var in symbols["variables"]:
        if any(keyword in var["name"].lower() 
               for keyword in ["prompt", "system", "instruction", "template"]):
            
            if is_long_string(var["value"]):  # Heuristic: >100 chars
                prompt = {
                    "type": "system_prompt",
                    "name": var["name"],
                    "content": var["value"],
                    "location": var["location"]
                }
                prompts.append(prompt)
    
    # Pattern 2: Prompt template objects (LangChain)
    for obj in symbols["objects"]:
        if obj["type"] in ["PromptTemplate", "ChatPromptTemplate"]:
            prompt = {
                "type": "template",
                "name": obj["name"],
                "template": obj["template"],
                "variables": obj["input_variables"],
                "location": obj["location"]
            }
            prompts.append(prompt)
    
    # Pattern 3: Prompt files (.txt, .md, .prompt)
    for file_path in files:
        if file_path.endswith((".txt", ".md", ".prompt")):
            if "prompt" in file_path.lower():
                with open(file_path) as f:
                    prompt = {
                        "type": "file",
                        "name": os.path.basename(file_path),
                        "content": f.read(),
                        "location": {"file": file_path, "line": 0}
                    }
                    prompts.append(prompt)
    
    return prompts
4.4 Memory & State Detection
pythondef detect_memory_systems(symbols, dataflow):
    """
    Identify conversation history, vector stores, state management
    """
    memory_systems = []
    
    # Pattern 1: ConversationBufferMemory and variants (LangChain)
    for obj in symbols["objects"]:
        if "Memory" in obj["type"]:
            memory_systems.append({
                "type": "conversation_buffer",
                "implementation": obj["type"],
                "location": obj["location"]
            })
    
    # Pattern 2: Vector store initialization
    for call in symbols["api_calls"]:
        if any(vs in call["function"] for vs in 
               ["Pinecone", "Chroma", "FAISS", "Weaviate", "Qdrant"]):
            memory_systems.append({
                "type": "vector_store",
                "implementation": extract_vector_store_type(call),
                "location": call["location"]
            })
    
    # Pattern 3: Database connections (state persistence)
    for import_stmt in symbols["imports"]:
        if any(db in import_stmt["module"] for db in 
               ["redis", "postgres", "mongodb", "sqlite"]):
            memory_systems.append({
                "type": "persistent_state",
                "implementation": import_stmt["module"],
                "location": import_stmt["location"]
            })
    
    # Pattern 4: State variables in classes
    for cls in symbols["classes"]:
        if has_state_management(cls):
            memory_systems.append({
                "type": "class_state",
                "class": cls["name"],
                "state_vars": extract_state_variables(cls),
                "location": cls["location"]
            })
    
    return memory_systems

5. AI Semantic Analyzer
This is where the real "intelligence" happens. Use an LLM to understand what the code means, not just what it says.
5.1 Context Preparation
pythondef prepare_context_for_llm(symbols, tools, prompts, memory_systems, file_contents):
    """
    Build a focused context window for LLM analysis
    """
    context = {
        "codebase_summary": {
            "total_files": len(file_contents),
            "detected_framework": symbols["framework"],
            "entry_points": symbols["entry_points"],
            "tool_count": len(tools),
            "has_memory": len(memory_systems) > 0
        },
        
        "tools": [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
                "source_snippet": get_source_snippet(tool["location"], file_contents)
            }
            for tool in tools[:20]  # Limit to first 20 to stay in context window
        ],
        
        "prompts": [
            {
                "name": prompt["name"],
                "content": prompt["content"][:500]  # Truncate long prompts
            }
            for prompt in prompts[:5]
        ],
        
        "agent_main_loop": extract_main_loop(symbols, file_contents),
        
        "key_files": get_most_important_files(symbols, file_contents, limit=3)
    }
    
    return context
5.2 LLM Analysis Prompts
Goal Understanding Prompt
pythonGOAL_UNDERSTANDING_PROMPT = """
You are analyzing an agent codebase to understand its purpose and behavior.

Based on the following code artifacts, determine:
1. What is the agent's primary job/purpose?
2. What domain does it operate in? (support, sales, scheduling, research, etc.)
3. What are the agent's main capabilities?
4. What are likely success criteria for this agent?

Code artifacts:
{context}

Provide your analysis in JSON format:
{
  "purpose": "brief description",
  "domain": "support|sales|scheduling|ops|research|custom",
  "capabilities": ["capability 1", "capability 2", ...],
  "success_criteria": ["criterion 1", "criterion 2", ...],
  "confidence": 0.0-1.0
}
"""

def understand_agent_goal(context):
    """
    Use LLM to understand what the agent is trying to achieve
    """
    prompt = GOAL_UNDERSTANDING_PROMPT.format(
        context=json.dumps(context, indent=2)
    )
    
    response = call_llm(prompt, model="claude-sonnet-4-5", response_format="json")
    
    return json.loads(response)
Tool Semantic Analysis Prompt
pythonTOOL_ANALYSIS_PROMPT = """
You are analyzing tool definitions to understand their purpose and behavior.

For each tool below, determine:
1. What does this tool actually do?
2. What are its required inputs (human-readable)?
3. What does it return/produce?
4. Is this tool read-only or does it modify state?
5. Does it handle sensitive data (PII, financial, etc.)?
6. What other tools does it logically depend on?

Tools:
{tools}

Full codebase context (for reference):
{codebase_context}

Provide analysis in JSON format:
{
  "tools": [
    {
      "name": "tool_name",
      "purpose": "what it does",
      "required_inputs": ["input1", "input2"],
      "output": "what it returns",
      "read_only": true/false,
      "handles_sensitive_data": true/false,
      "sensitive_data_types": ["email", "ssn", ...] or [],
      "dependencies": ["other_tool_name", ...],
      "risk_level": "low|medium|high|critical"
    },
    ...
  ]
}
"""

def analyze_tools_semantically(tools, context):
    """
    Use LLM to deeply understand what each tool does
    """
    # Process in batches to stay within context limits
    batch_size = 10
    analyzed_tools = []
    
    for i in range(0, len(tools), batch_size):
        batch = tools[i:i+batch_size]
        
        prompt = TOOL_ANALYSIS_PROMPT.format(
            tools=json.dumps(batch, indent=2),
            codebase_context=summarize_context(context)
        )
        
        response = call_llm(prompt, model="claude-sonnet-4-5", response_format="json")
        
        analyzed_tools.extend(json.loads(response)["tools"])
    
    return analyzed_tools
Workflow Understanding Prompt
pythonWORKFLOW_ANALYSIS_PROMPT = """
You are analyzing agent code to understand its conversation flow and decision-making.

Based on the main loop code and tool definitions, determine:
1. How does the agent decide which tool to call?
2. What is the typical conversation flow?
3. What error handling strategies are in place?
4. Are there any safety guardrails or validation checks?
5. How does the agent handle ambiguous user requests?

Code:
{agent_main_loop}

Tools available:
{tool_names}

Prompts used:
{prompts}

Provide analysis in JSON format:
{
  "decision_strategy": "react|plan-and-execute|function-calling|custom",
  "typical_flow": ["step 1", "step 2", ...],
  "error_handling": {
    "timeout": "strategy or 'none'",
    "malformed_response": "strategy or 'none'",
    "tool_failure": "strategy or 'none'"
  },
  "guardrails": ["guardrail 1", "guardrail 2", ...] or [],
  "ambiguity_handling": "how agent handles unclear requests"
}
"""

def analyze_workflow(symbols, context):
    """
    Understand the agent's decision-making and flow
    """
    prompt = WORKFLOW_ANALYSIS_PROMPT.format(
        agent_main_loop=context["agent_main_loop"],
        tool_names=[t["name"] for t in context["tools"]],
        prompts=json.dumps(context["prompts"], indent=2)
    )
    
    response = call_llm(prompt, model="claude-sonnet-4-5", response_format="json")
    
    return json.loads(response)
5.3 Dependency Resolution with AI
pythonDEPENDENCY_ANALYSIS_PROMPT = """
You are analyzing tool dependencies in an agent system.

Given these tools and their implementations, determine:
1. Which tools must be called before other tools?
2. Which tools are mutually exclusive?
3. Which tool combinations are common/expected?
4. Are there any circular dependencies or infinite loop risks?

Tools with code snippets:
{tools_with_code}

Agent workflow:
{workflow}

Provide analysis in JSON format:
{
  "dependencies": [
    {
      "tool": "tool_name",
      "requires": ["required_tool_1", ...],
      "reason": "why this dependency exists"
    },
    ...
  ],
  "mutually_exclusive": [
    ["tool_a", "tool_b"],
    ...
  ],
  "common_sequences": [
    ["tool_1", "tool_2", "tool_3"],
    ...
  ],
  "circular_dependency_risks": ["description of risk", ...] or []
}
"""

def resolve_tool_dependencies_with_ai(tools, workflow, file_contents):
    """
    Use LLM to understand logical dependencies between tools
    """
    # Add code snippets to tools
    tools_with_code = []
    for tool in tools:
        code_snippet = get_source_snippet(tool["location"], file_contents, lines=20)
        tools_with_code.append({
            **tool,
            "code": code_snippet
        })
    
    prompt = DEPENDENCY_ANALYSIS_PROMPT.format(
        tools_with_code=json.dumps(tools_with_code[:15], indent=2),  # Limit for context
        workflow=json.dumps(workflow, indent=2)
    )
    
    response = call_llm(prompt, model="claude-sonnet-4-5", response_format="json")
    
    return json.loads(response)

6. Graph Construction
6.1 Agent Architecture Graph
pythondef build_agent_architecture_graph(symbols, tools, workflow, dependencies, memory_systems):
    """
    Construct hierarchical graph of agent components
    """
    graph = nx.DiGraph()
    
    # Root node: Agent
    graph.add_node("agent", type="agent", **{
        "framework": symbols["framework"],
        "purpose": workflow["purpose"],
        "domain": workflow["domain"]
    })
    
    # Orchestrator layer
    graph.add_node("orchestrator", type="orchestrator", **{
        "strategy": workflow["decision_strategy"],
        "error_handling": workflow["error_handling"]
    })
    graph.add_edge("agent", "orchestrator")
    
    # Planner (if exists)
    if workflow["decision_strategy"] == "plan-and-execute":
        graph.add_node("planner", type="planner")
        graph.add_edge("orchestrator", "planner")
    
    # Tools layer
    for tool in tools:
        tool_node_id = f"tool_{tool['id']}"
        graph.add_node(tool_node_id, type="tool", **tool)
        graph.add_edge("orchestrator", tool_node_id)
        
        # Add dependencies between tools
        for dep in dependencies.get("dependencies", []):
            if dep["tool"] == tool["name"]:
                for required_tool in dep["requires"]:
                    required_id = f"tool_{find_tool_id(required_tool, tools)}"
                    graph.add_edge(required_id, tool_node_id, 
                                   relationship="requires",
                                   reason=dep["reason"])
    
    # Memory layer
    if memory_systems:
        graph.add_node("memory", type="memory_subsystem")
        graph.add_edge("agent", "memory")
        
        for mem_sys in memory_systems:
            mem_id = f"memory_{mem_sys['type']}"
            graph.add_node(mem_id, type="memory", **mem_sys)
            graph.add_edge("memory", mem_id)
    
    # Retrieval layer (if exists)
    retrieval_systems = [m for m in memory_systems if m["type"] == "vector_store"]
    if retrieval_systems:
        graph.add_node("retrieval", type="retrieval_subsystem")
        graph.add_edge("agent", "retrieval")
        
        for ret_sys in retrieval_systems:
            ret_id = f"retrieval_{ret_sys['implementation']}"
            graph.add_node(ret_id, type="retrieval", **ret_sys)
            graph.add_edge("retrieval", ret_id)
    
    return graph
6.2 Visual Diagram Generation
pythondef generate_visual_diagram(graph):
    """
    Generate interactive visual representation
    """
    # Use D3.js force-directed layout or similar
    # Export as JSON for web visualization
    
    vis_data = {
        "nodes": [
            {
                "id": node_id,
                "label": graph.nodes[node_id].get("name", node_id),
                "type": graph.nodes[node_id]["type"],
                "data": dict(graph.nodes[node_id])
            }
            for node_id in graph.nodes()
        ],
        "edges": [
            {
                "source": edge[0],
                "target": edge[1],
                "relationship": graph.edges[edge].get("relationship", "uses"),
                "data": dict(graph.edges[edge])
            }
            for edge in graph.edges()
        ]
    }
    
    return vis_data

7. Risk Analysis
7.1 PII Detection
pythonPII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
    "credit_card": r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    "address": [
        "address", "street", "city", "state", "zip", "postal"
    ]
}

def detect_pii_handling(tools, prompts, file_contents):
    """
    Identify tools/prompts that handle sensitive data
    """
    pii_risks = []
    
    # Check tool parameters
    for tool in tools:
        for param in tool["parameters"]:
            param_name_lower = param["name"].lower()
            
            # Check if parameter name suggests PII
            for pii_type, patterns in PII_PATTERNS.items():
                if isinstance(patterns, list):
                    if any(pattern in param_name_lower for pattern in patterns):
                        pii_risks.append({
                            "location": tool["location"],
                            "tool": tool["name"],
                            "type": "parameter",
                            "pii_type": pii_type,
                            "parameter": param["name"],
                            "severity": "high"
                        })
                else:  # regex pattern
                    # Check if parameter description/docstring contains PII examples
                    desc = param.get("description", "")
                    if re.search(patterns, desc):
                        pii_risks.append({
                            "location": tool["location"],
                            "tool": tool["name"],
                            "type": "parameter_example",
                            "pii_type": pii_type,
                            "parameter": param["name"],
                            "severity": "medium"
                        })
    
    # Check prompts for PII instructions
    for prompt in prompts:
        content = prompt["content"]
        for pii_type, patterns in PII_PATTERNS.items():
            if isinstance(patterns, str):
                if re.search(patterns, content):
                    pii_risks.append({
                        "location": prompt["location"],
                        "type": "prompt_content",
                        "pii_type": pii_type,
                        "severity": "high"
                    })
    
    return pii_risks
7.2 Critical Action Detection
pythonCRITICAL_ACTION_KEYWORDS = {
    "financial": ["payment", "charge", "refund", "purchase", "transaction", "billing"],
    "data_modification": ["delete", "remove", "update", "modify", "change"],
    "user_management": ["create_user", "delete_user", "change_password", "grant_access"],
    "communication": ["send_email", "send_sms", "notify", "alert"],
}

def detect_critical_actions(tools):
    """
    Identify tools that perform irreversible or sensitive operations
    """
    critical_tools = []
    
    for tool in tools:
        tool_name_lower = tool["name"].lower()
        tool_desc_lower = (tool.get("description") or "").lower()
        
        for category, keywords in CRITICAL_ACTION_KEYWORDS.items():
            if any(kw in tool_name_lower or kw in tool_desc_lower for kw in keywords):
                critical_tools.append({
                    "tool": tool["name"],
                    "category": category,
                    "risk_level": "critical" if category == "financial" else "high",
                    "location": tool["location"],
                    "requires_confirmation": True,
                    "sandbox_safe": False
                })
                break
    
    return critical_tools
7.3 AI-Powered Risk Assessment
pythonRISK_ASSESSMENT_PROMPT = """
You are a security analyst reviewing agent code for potential risks.

Analyze these tools and identify:
1. Operations that could cause data loss or corruption
2. Operations that could expose sensitive information
3. Operations that could have financial impact
4. Operations that could affect other users
5. Missing validation or safety checks

Tools:
{tools}

Agent workflow:
{workflow}

Provide risk assessment in JSON format:
{
  "risks": [
    {
      "tool": "tool_name",
      "risk_type": "data_loss|info_exposure|financial|user_impact|missing_validation",
      "severity": "low|medium|high|critical",
      "description": "detailed risk description",
      "mitigation": "recommended safeguard"
    },
    ...
  ]
}
"""

def assess_risks_with_ai(tools, workflow):
    """
    Use LLM to identify non-obvious security risks
    """
    prompt = RISK_ASSESSMENT_PROMPT.format(
        tools=json.dumps(tools, indent=2),
        workflow=json.dumps(workflow, indent=2)
    )
    
    response = call_llm(prompt, model="claude-sonnet-4-5", response_format="json")
    
    return json.loads(response)["risks"]

8. Interactive Refinement UI
8.1 User Confirmation Flow
javascript// React component pseudo-code

function AgentMapConfirmation({ agentMap, onConfirm, onEdit }) {
  const [editMode, setEditMode] = useState(false);
  const [localMap, setLocalMap] = useState(agentMap);
  
  return (
    <div className="agent-map-confirmation">
      <h2>Agent Architecture Map</h2>
      <p>We've analyzed your codebase. Please review and confirm:</p>
      
      {/* Visual Diagram */}
      <AgentDiagram 
        graph={localMap.graph} 
        onNodeClick={handleNodeClick}
        editable={editMode}
      />
      
      {/* Tool Catalog Table */}
      <ToolCatalogTable 
        tools={localMap.tools}
        onEdit={(toolId, changes) => updateTool(toolId, changes)}
        editable={editMode}
      />
      
      {/* Success Criteria */}
      <SuccessCriteriaEditor
        criteria={localMap.success_criteria}
        onChange={updateSuccessCriteria}
        editable={editMode}
      />
      
      {/* Risk Flags */}
      <RiskFlagsPanel risks={localMap.risks} />
      
      <div className="actions">
        {!editMode ? (
          <>
            <button onClick={() => setEditMode(true)}>
              Edit & Correct
            </button>
            <button onClick={() => onConfirm(localMap)}>
              Looks Good, Continue
            </button>
          </>
        ) : (
          <>
            <button onClick={() => setEditMode(false)}>
              Cancel
            </button>
            <button onClick={() => {
              setEditMode(false);
              onConfirm(localMap);
            }}>
              Save Changes & Continue
            </button>
          </>
        )}
      </div>
    </div>
  );
}
8.2 Targeted Follow-up Questions
pythondef generate_followup_questions(agent_map, analysis_confidence):
    """
    Generate targeted questions based on gaps in understanding
    """
    questions = []
    
    # If low confidence in goal understanding
    if analysis_confidence["purpose"] < 0.7:
        questions.append({
            "type": "clarification",
            "question": "What is your agent's primary goal?",
            "options": ["Customer Support", "Sales", "Scheduling", "Research", "Other"],
            "why": "We're not entirely sure from the code what this agent's main job is."
        })
    
    # If found unidentified tools
    uncertain_tools = [t for t in agent_map["tools"] if t.get("confidence", 1.0) < 0.6]
    if uncertain_tools:
        questions.append({
            "type": "tool_clarification",
            "question": f"We found {len(uncertain_tools)} potential tools but aren't sure what they do. Can you help?",
            "tools": [{"name": t["name"], "our_guess": t["description"]} for t in uncertain_tools],
            "why": "These functions look like tools but we need clarification."
        })
    
    # If no explicit success criteria found
    if not agent_map.get("success_criteria"):
        questions.append({
            "type": "success_criteria",
            "question": "How do you measure if this agent successfully completed its task?",
            "examples": [
                "User's issue is resolved",
                "Booking is confirmed",
                "User receives requested information"
            ],
            "why": "We'll use this to evaluate agent performance in testing."
        })
    
    # If PII detected but no validation found
    if agent_map["risks"]["pii_handling"] and not has_pii_validation(agent_map):
        questions.append({
            "type": "safety",
            "question": "We detected handling of sensitive data (emails, phone numbers). What data should the agent never reveal to users?",
            "input_type": "textarea",
            "why": "We'll create tests to ensure PII isn't leaked."
        })
    
    # If critical actions found
    critical_tools = [t for t in agent_map["tools"] if t["risk_level"] == "critical"]
    if critical_tools:
        questions.append({
            "type": "permissions",
            "question": "Which of these tools should require special permissions or confirmation?",
            "tools": [{"name": t["name"], "action": t["purpose"]} for t in critical_tools],
            "checkboxes": True,
            "why": "These tools perform sensitive operations."
        })
    
    return questions

9. Output: Structured Agent Map
9.1 Complete Data Structure
pythondef generate_agent_map_output(
    symbols, 
    tools, 
    prompts, 
    workflow, 
    dependencies, 
    memory_systems, 
    risks,
    graph,
    user_confirmations
):
    """
    Generate final Agent Map v1 structure
    """
    agent_map = {
        "version": "1.0",
        "generated_at": datetime.utcnow().isoformat(),
        "agent_id": generate_uuid(),
        
        # High-level metadata
        "metadata": {
            "name": user_confirmations.get("agent_name") or "Unnamed Agent",
            "type": workflow["domain"],
            "framework": symbols["framework"],
            "language": symbols["language"],
            "purpose": workflow["purpose"],
            "capabilities": workflow["capabilities"]
        },
        
        # Component structure
        "components": {
            "orchestrator": {
                "type": workflow["decision_strategy"],
                "error_handling": workflow["error_handling"],
                "guardrails": workflow["guardrails"]
            },
            
            "planner": {
                "exists": workflow["decision_strategy"] == "plan-and-execute",
                "implementation": extract_planner_details(symbols) if workflow["decision_strategy"] == "plan-and-execute" else None
            },
            
            "tools": [
                {
                    "id": tool["id"],
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["parameters"],
                    "dependencies": [
                        dep["tool"] for dep in dependencies["dependencies"] 
                        if dep["requires"] and tool["name"] in dep["requires"]
                    ],
                    "sandbox_safe": tool.get("sandbox_safe", True),
                    "risk_level": tool["risk_level"],
                    "source": tool["source"],
                    "location": tool["location"]
                }
                for tool in tools
            ],
            
            "memory": {
                "systems": memory_systems,
                "conversation_history": any(m["type"] == "conversation_buffer" for m in memory_systems),
                "persistent_state": any(m["type"] == "persistent_state" for m in memory_systems)
            },
            
            "retrieval": {
                "systems": [m for m in memory_systems if m["type"] == "vector_store"],
                "exists": any(m["type"] == "vector_store" for m in memory_systems)
            },
            
            "prompts": [
                {
                    "name": p["name"],
                    "type": p["type"],
                    "content": p["content"],
                    "location": p["location"]
                }
                for p in prompts
            ]
        },
        
        # Success criteria
        "success_criteria": {
            "task_completion": user_confirmations.get("success_criteria", {}).get("task_completion"),
            "max_latency_ms": user_confirmations.get("performance", {}).get("max_latency_ms", 10000),
            "max_cost_per_conversation": user_confirmations.get("performance", {}).get("max_cost", 1.00),
            "max_turns": user_confirmations.get("performance", {}).get("max_turns", 20)
        },
        
        # Risk surface
        "risk_flags": {
            "pii_handling": len([r for r in risks if "pii" in r["type"]]) > 0,
            "critical_actions": [r["tool"] for r in risks if r["severity"] == "critical"],
            "compliance_concerns": extract_compliance_concerns(risks),
            "all_risks": risks
        },
        
        # Graph representation (for visualization)
        "graph": {
            "nodes": [
                {"id": n, **graph.nodes[n]} 
                for n in graph.nodes()
            ],
            "edges": [
                {"source": e[0], "target": e[1], **graph.edges[e]} 
                for e in graph.edges()
            ]
        },
        
        # Source files reference
        "source_files": {
            "analyzed_files": symbols["files_analyzed"],
            "entry_points": symbols["entry_points"],
            "repository": symbols.get("repository_url")
        }
    }
    
    return agent_map
9.2 Visual Diagram Export
pythondef export_visual_diagram(agent_map, format="html"):
    """
    Export interactive diagram in various formats
    """
    if format == "html":
        # Generate standalone HTML with D3.js visualization
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                .node { cursor: pointer; }
                .node circle { stroke: #333; stroke-width: 2px; }
                .node text { font: 12px sans-serif; }
                .link { stroke: #999; stroke-opacity: 0.6; }
            </style>
        </head>
        <body>
            <div id="graph"></div>
            <script>
                const data = {graph_data};
                // D3.js force-directed graph code...
            </script>
        </body>
        </html>
        """
        
        return html_template.format(
            graph_data=json.dumps(agent_map["graph"])
        )
    
    elif format == "mermaid":
        # Generate Mermaid diagram syntax
        return generate_mermaid_diagram(agent_map["graph"])
    
    elif format == "svg":
        # Generate static SVG
        return generate_svg_diagram(agent_map["graph"])

10. Implementation Roadmap
Phase 1: Core Analysis (Weeks 1-2)

 Set up code ingestion (GitHub integration)
 Implement Tree-sitter AST parsing for Python
 Build symbol extraction for functions, classes, imports
 Create LangChain pattern detector
 Basic tool extraction from decorators

Phase 2: AI Intelligence (Weeks 3-4)

 Integrate Claude API for semantic analysis
 Implement goal understanding prompt
 Implement tool semantic analysis
 Build workflow analysis
 Add dependency resolution with AI

Phase 3: Graph & Visualization (Week 5)

 Build agent architecture graph construction
 Create interactive D3.js visualization
 Implement tool catalog table view
 Add export formats (JSON, HTML, Mermaid)

Phase 4: Risk Analysis (Week 6)

 Implement PII detection patterns
 Build critical action detector
 Add AI-powered risk assessment
 Create risk flags panel in UI

Phase 5: User Refinement (Week 7)

 Build confirmation UI with editable diagram
 Implement targeted follow-up questions
 Add manual tool addition/editing
 Create success criteria editor

Phase 6: Testing & Polish (Week 8)

 Test on 10+ real agent codebases
 Refine AI prompts based on results
 Optimize performance (caching, parallel processing)
 Add error handling and edge cases


11. Key Technologies
11.1 Code Analysis

Tree-sitter: Universal AST parsing
rope (Python): Refactoring and code analysis
ts-morph (TypeScript): TS/JS code manipulation
NetworkX: Graph construction and analysis

11.2 AI Integration

Anthropic Claude API: Semantic understanding (Claude Sonnet 4.5)
OpenAI (alternative): GPT-4 for comparison
Langfuse/LangSmith: LLM observability during analysis

11.3 Visualization

D3.js: Interactive graph visualization
React Flow: Alternative for node-based UI
Mermaid: Diagram generation for documentation
Graphviz: Static diagram generation

11.4 Infrastructure

FastAPI: Backend API server
Celery + Redis: Async task queue for long analyses
PostgreSQL: Store agent maps and analysis results
MinIO/S3: Store source code and artifacts


12. Differentiation from Cursor/Claude Code
What Makes This Different
Cursor/Claude Code:

General-purpose code understanding
File-by-file analysis
Optimized for developer editing workflow
No domain-specific insights

Your Platform (Agent-Specific):

Purpose-built for agent code: Understands LangChain, LangGraph, function calling patterns
Holistic view: Analyzes entire agent architecture, not just files
Tool-centric: Treats tools as first-class citizens with dependencies
Testing-focused: Maps structure to enable automated testing
Risk-aware: Identifies PII, critical actions, compliance concerns
Behavioral understanding: Doesn't just read code, understands agent's job and workflow

Competitive Advantages

Framework-Specific Patterns: Deep knowledge of agent frameworks
Tool Dependency Graphs: Understand logical tool relationships
Risk Surface Mapping: Automatic security/compliance analysis
Test-Ready Output: Agent map directly feeds into test generation
Semantic Understanding: AI-powered intent analysis, not just syntax
Interactive Refinement: Users can correct and enhance findings


13. Success Metrics
Accuracy Metrics

Tool Detection Rate: % of actual tools correctly identified
False Positive Rate: % of non-tools incorrectly flagged as tools
Dependency Accuracy: % of tool dependencies correctly identified
Risk Detection Rate: % of actual PII/critical operations found

User Experience Metrics

Time to Agent Map: <5 minutes for typical codebase
User Corrections Required: <3 edits on average
Framework Support Coverage: >80% of agent codebases use supported frameworks
Analysis Success Rate: >95% of repos successfully analyzed

Business Metrics

Onboarding Completion Rate: % of users who complete Phase A
Agent Map Quality: User ratings of generated maps
Time Saved vs Manual: 10x faster than manual documentation


14. Next Steps
Immediate Actions

Prototype Core Loop: Build end-to-end flow with one framework (LangChain)
Test on 5 Example Repos: Validate approach on real codebases
Refine AI Prompts: Iterate on semantic analysis quality
Build Minimal UI: Simple confirmation interface

Future Enhancements

Multi-language Support: Add JS/TS, Go, Rust
Real-time Analysis: Watch mode for code changes
Comparative Analysis: Compare two agent versions
Auto-documentation: Generate README from Agent Map
IDE Integration: VSCode extension for inline analysis


Appendix A: Example Agent Map JSON
json{
  "version": "1.0",
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "metadata": {
    "name": "CustomerSupportBot",
    "type": "support",
    "framework": "langchain",
    "language": "python",
    "purpose": "Handle customer support inquiries, including order tracking, refunds, and technical issues",
    "capabilities": [
      "Order tracking",
      "Initiate refunds",
      "Escalate to human agent",
      "Search knowledge base"
    ]
  },
  "components": {
    "orchestrator": {
      "type": "react",
      "error_handling": {
        "timeout": "retry with exponential backoff",
        "malformed_response": "request clarification from user",
        "tool_failure": "apologize and escalate"
      },
      "guardrails": [
        "Never disclose customer payment details",
        "Require confirmation for refunds >$100"
      ]
    },
    "tools": [
      {
        "id": "tool_001",
        "name": "track_order",
        "description": "Look up order status by order ID",
        "parameters": [
          {
            "name": "order_id",
            "type": "string",
            "required": true,
            "description": "Order identifier (e.g., ORD-12345)"
          }
        ],
        "dependencies": [],
        "sandbox_safe": true,
        "risk_level": "low",
        "source": "langchain_decorator"
      },
      {
        "id": "tool_002",
        "name": "initiate_refund",
        "description": "Process a refund for an order",
        "parameters": [
          {
            "name": "order_id",
            "type": "string",
            "required": true
          },
          {
            "name": "amount",
            "type": "number",
            "required": true
          },
          {
            "name": "reason",
            "type": "string",
            "required": false
          }
        ],
        "dependencies": ["track_order"],
        "sandbox_safe": false,
        "risk_level": "critical",
        "source": "langchain_class"
      }
    ],
    "memory": {
      "systems": [
        {
          "type": "conversation_buffer",
          "implementation": "ConversationBufferMemory"
        }
      ],
      "conversation_history": true,
      "persistent_state": false
    },
    "retrieval": {
      "systems": [
        {
          "type": "vector_store",
          "implementation": "Pinecone"
        }
      ],
      "exists": true
    }
  },
  "success_criteria": {
    "task_completion": "Customer issue resolved or escalated appropriately",
    "max_latency_ms": 5000,
    "max_cost_per_conversation": 0.50,
    "max_turns": 15
  },
  "risk_flags": {
    "pii_handling": true,
    "critical_actions": ["initiate_refund"],
    "compliance_concerns": ["PCI-DSS (payment data)", "GDPR (customer data)"]
  }
}

Appendix B: AI Prompt Templates Library
Store all prompt templates in a separate file for easy iteration:
python# prompts/analysis_prompts.py

PROMPTS = {
    "goal_understanding": {
        "system": "You are an expert at analyzing agent codebases...",
        "user": "Based on the following code artifacts...",
        "response_format": {"type": "json_object"}
    },
    
    "tool_analysis": {
        "system": "You are analyzing tool definitions...",
        "user": "For each tool below, determine...",
        "response_format": {"type": "json_object"}
    },
    
    # ... more prompts
}
This allows you to A/B test different prompts without changing code.

