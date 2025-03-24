# PDF Processing Application Design

## Overview
A terminal-based application that processes PDFs to extract and understand content, then leverages OpenAI to generate structured YAML output based on templates.

## Phase 1: PDF Parsing and YAML Generation

### Architecture Overview
```
Input PDF → PDF Parser → Structured Data → OpenAI Processing → YAML Generation → Output YAML
```

### Modular Structure

1. **Core Modules**
   - `pdf_extractor/`: Enhanced version of existing PDFTextExtractor
   - `content_processor/`: Text processing and structuring
   - `openai_integration/`: OpenAI API interactions
   - `yaml_generator/`: Templating and YAML output
   - `config/`: Configuration settings and templates

2. **File Structure**
```
project_root/
├── main.py                # CLI entry point (handles one PDF per run)
├── pdf_extractor/
│   ├── __init__.py
│   └── extractor.py       # Enhanced PDFTextExtractor
├── content_processor/
│   ├── __init__.py
│   └── parser.py          # Content parsing and structuring
├── openai_integration/
│   ├── __init__.py
│   └── client.py          # OpenAI API interface
├── yaml_generator/
│   ├── __init__.py
│   └── templater.py       # Template application logic
├── config/
│   ├── settings.py        # Configuration settings
│   └── templates/         # YAML templates
│       └── default.yaml   # Default template
├── utils/
│   ├── __init__.py
│   └── helpers.py         # Common utilities
└── requirements.txt
```

### Implementation Plan

1. **Command-line Interface**
   - Simple argument-based interface (`python main.py input.pdf --template default.yaml`)
   - Configuration via config file or command-line arguments
   - Clear output messages with processing status

2. **PDF Extraction Enhancement**
   - Build on existing PDFTextExtractor
   - Add content structure detection (headings, sections)
   - Improve error handling for various PDF formats

3. **OpenAI Integration**
   - Build client for OpenAI API
   - Design effective prompts for content understanding
   - Implement structured data extraction

4. **YAML Generation**
   - Template-based YAML output
   - Validation against schema
   - Configurable output format

## Phase 2: Terminal-Based Agentic System with Human Validation

### Architecture Overview
```
PDF → Parse → Agent System → Terminal Human Validation → Refinement → YAML Output
```

### Technology Choices

For Phase 2, we will primarily use **LangGraph** as the agent orchestration framework:

1. **Why LangGraph:**
   - Provides a structured graph-based approach for complex workflows
   - Built-in support for human-in-the-loop validation cycles
   - Robust state management for tracking validation progress
   - Seamless integration with OpenAI components from Phase 1
   - Natural representation of multi-agent coordination

3. **Supporting Technologies:**
   - **Pydantic**: For data validation and schema enforcement
   - **Rich**: For enhanced terminal display (colors, progress bars)
   - **YAML**: For state persistence between processing steps

### Enhanced Modules

1. **Terminal-Based Human Interface**
   - `terminal_interface/`: Simple terminal interaction
     - `prompt_handler.py`: Terminal-based prompts
     - `feedback_collector.py`: User input collection
     - `display.py`: Information presentation

2. **Agent System**
   - `agents/`: LangGraph-based agent system
     - `orchestrator.py`: Main agent flow controller
     - `pdf_agent.py`: PDF understanding specialist
     - `validation_agent.py`: Data validation specialist

3. **Workflow Manager**
   - `workflow/`: Process management
     - `state.py`: Workflow state management
     - `decision.py`: Next steps decision logic

### Implementation Plan

1. **Terminal Interface**
   - Color-coded output for different message types
   - Step-by-step validation prompts
   - Simple input collection with validation
   - Progress indicators for long-running processes

2. **Agent Framework**
   - LangGraph or ReAct implementation
   - Create specialized agents for different tasks
   - Build decision flow for processing steps

3. **Human Validation Flow**
   - Present extracted information in digestible chunks
   - Allow section-by-section validation and correction
   - Implement verification prompts for key information
   - Create simple feedback mechanisms (yes/no, corrections)

4. **Single-Run Process**
   - Design process to handle exactly one PDF per execution
   - Implement clear entry and exit points
   - Create resumable state (optional) for interrupted runs

## Development Roadmap

1. **Initial Setup (1 week)**
   - Environment setup
   - Base structure implementation
   - Command-line interface

2. **Phase 1 Core (2 weeks)**
   - PDF parser enhancement
   - OpenAI integration
   - YAML template system
   - End-to-end functionality

3. **Phase 1 Testing (1 week)**
   - Testing with diverse PDFs
   - Error handling improvements
   - Performance optimization

4. **Phase 2 Framework (2 weeks)**
   - LangGraph implementation
   - Agent design and implementation
   - Terminal-based validation interface

5. **Final Integration (1 week)**
   - Complete system connection
   - End-to-end testing
   - Documentation 