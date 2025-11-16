# AI-Assisted Development Guide for Agent Kit

## 🎯 Mission: Build Quality Code While Learning

This guide helps you ensure high-quality development when working with AI assistants on the ontology-driven ML framework.

---

## 📋 Pre-AI Development Checklist

### 1. **Problem Definition** (Don't Skip This!)
**Before asking AI for code:**

```markdown
PROBLEM: [Clear statement - what are we solving?]
CONTEXT: [Where does this fit in Agent Kit architecture?]
INPUTS: [What data/parameters come in?]
OUTPUTS: [What should be returned?]
CONSTRAINTS: [Performance, compatibility, business rules?]
EXAMPLES: [Concrete input/output examples]
EDGE CASES: [What could go wrong?]
```

**Example:**
```
PROBLEM: Create agent that analyzes business leverage points from ontology
CONTEXT: Extends BaseAgent for business intelligence
INPUTS: Business ontology (RDF), revenue data
OUTPUTS: LeveragePoint recommendations with confidence scores
CONSTRAINTS: Must use SPARQL queries, return Pydantic models
EXAMPLES: Input="Sunshine Bakery", Output=LeveragePoint(type="pricing", impact=0.85)
EDGE CASES: Empty ontology, malformed RDF, no revenue data
```

### 2. **Architecture Alignment**
**Check these before proceeding:**
- [ ] Does this fit Agent Kit's ontology-first architecture?
- [ ] Is this a custom agent, adapter, or tool?
- [ ] Does it use existing patterns (BaseAgent, SPARQL, FAISS)?
- [ ] Will it integrate with orchestration layer?

---

## 🤖 Working with AI Effectively

### **Prompt Engineering for Quality**

#### ❌ Bad Prompt:
```
"Write a function that does machine learning stuff"
```

#### ✅ Good Prompt:
```
"Create a LeverageAnalyzerAgent class that extends BaseAgent.

Requirements:
- Inherit from BaseAgent with proper observe/plan/act/reflect
- Use OntologyLoader to query business leverage points
- Return LeveragePoint pydantic models with confidence scores
- Handle edge case: empty ontology returns empty list
- Follow existing code patterns in agent_kit/agents/

Example usage:
agent = LeverageAnalyzerAgent(loader)
result = agent.run(AgentTask(description="Analyze Sunshine Bakery"))
# Returns: AgentResult with leverage recommendations
```

### **AI Code Review Questions**

**After AI generates code, ask yourself:**

1. **Logic Flow**: Can I trace the execution path in plain English?
2. **Error Handling**: What happens with bad inputs?
3. **Performance**: Any O(n²) loops or expensive operations?
4. **Dependencies**: Does it import correctly? Use existing patterns?
5. **Testing**: How would I write a test for this?
6. **Maintenance**: Could another developer understand this?

---

## 🔍 Quality Verification Process

### **Step 1: Automated Checks**
```bash
# Run the quality checker script
python3 scripts/code_quality_checker.py

# Or use individual make commands
make quality    # lint + format + typecheck
make test       # run test suite
make dryrun     # pre-deployment validation
```

### **Step 2: Manual Review**
**For each AI-generated code block:**

1. **Read Aloud**: Explain what each line does
2. **Trace Execution**: Walk through with sample data
3. **Check Patterns**: Does it match Agent Kit conventions?
4. **Test Edges**: Try with unusual inputs
5. **Performance Check**: Time execution, check memory

### **Step 3: Integration Testing**
```bash
# Test with existing examples
python3 examples/04_orchestrated_agents.py

# Add to existing workflow
# Does it break anything?
```

---

## 📚 Learning Verification Framework

### **Level 1: Can Explain** (Minimum Requirement)
- [ ] Explain what the code does in plain English
- [ ] Identify the main algorithm/data structure used
- [ ] Describe input validation and error handling

### **Level 2: Can Modify** (Good Progress)
- [ ] Add a new feature to the code
- [ ] Fix a bug in the logic
- [ ] Adapt to a slightly different requirement

### **Level 3: Can Extend** (Mastery)
- [ ] Create similar functionality for new use case
- [ ] Refactor to improve performance/maintainability
- [ ] Integrate with other Agent Kit components

### **Level 4: Can Design** (Expert)
- [ ] Propose architectural improvements
- [ ] Design tests before implementation
- [ ] Make trade-off decisions (performance vs complexity)

---

## 🚨 Red Flags (Stop and Reassess)

### **Code Quality Red Flags:**
- [ ] AI generates >50 lines without explanation
- [ ] Code doesn't match existing patterns
- [ ] No error handling for obvious edge cases
- [ ] Imports not following project structure
- [ ] No type hints in new Python code

### **Learning Red Flags:**
- [ ] Can't explain why a design decision was made
- [ ] Don't understand key algorithms used
- [ ] Struggle with debugging simple issues
- [ ] Fear of modifying AI-generated code

**When you see red flags: Stop, ask questions, get clarification!**

---

## 🔄 Iterative Improvement Workflow

### **The Learning Loop:**

1. **Define Problem** → Write clear requirements
2. **AI Generation** → Get initial code with good prompt
3. **Quality Check** → Run automated tests
4. **Manual Review** → Verify logic and learning
5. **Test Integration** → Ensure it works with existing code
6. **Document Learning** → Note what you learned/changed
7. **Repeat** → Build on understanding

### **Progress Tracking:**

```markdown
## Session Log: [Date]

### What I Built:
- [Component/feature name]
- [Lines of code]
- [New concepts learned]

### Quality Score:
- Automated checks: [X/Y passed]
- Manual review: [confidence level]
- Learning level: [1-4]

### Improvements Made:
- [What I changed from AI code]
- [Why I made the change]
- [Better understanding gained]

### Next Focus:
- [What to learn next]
- [How to apply this pattern]
```

---

## 🛠️ Development Environment Setup

### **Essential Tools:**
```bash
# Install development dependencies
pip install -e .[dev]

# Quality check tools
pip install ruff black mypy pytest pytest-cov

# Run quality suite
python3 scripts/code_quality_checker.py
```

### **Editor Setup:**
- Use an editor with Python linting/type checking
- Enable format-on-save with Black
- Set up test running shortcuts

---

## 🎯 Success Metrics

### **Code Quality Metrics:**
- ✅ All `make quality` checks pass
- ✅ Tests achieve >80% coverage
- ✅ `make dryrun` passes before commits
- ✅ Code follows Agent Kit patterns

### **Learning Metrics:**
- ✅ Can explain new code to another developer
- ✅ Can modify code for new requirements
- ✅ Can debug issues independently
- ✅ Can propose architectural improvements

### **Project Health Metrics:**
- ✅ New code integrates without breaking existing
- ✅ Performance doesn't degrade
- ✅ Documentation stays current
- ✅ Tests cover new functionality

---

## 🚀 Getting Help

### **When Stuck:**
1. **Check existing code** - Agent Kit has good examples
2. **Run tests** - See what's expected
3. **Read documentation** - AGENTS.md, BUSINESS_ONTOLOGY_PLAN.md
4. **Ask specific questions** - Not "how do I code this?" but "why doesn't this SPARQL query work?"

### **Mentorship Approach:**
- Focus on understanding over speed
- Build incrementally on working code
- Document decisions for future reference
- Celebrate small wins in learning

---

**Remember: Quality code is understandable code. If you can't explain it, it needs work!** 🎯
