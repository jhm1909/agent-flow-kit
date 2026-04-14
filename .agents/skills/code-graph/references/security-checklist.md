# Security Review Checklist

Use during code review when risk level is MEDIUM or higher.

## Red Flag Patterns (immediate investigation)

| Pattern | What to look for | Why it's dangerous |
|---------|------------------|--------------------|
| Removed validation | `if` checks deleted, input sanitization removed | Opens injection vectors |
| Removed auth checks | `require_auth`, `@login_required`, role checks removed | Unauthorized access |
| Hardcoded secrets | API keys, passwords, tokens in source code | Credential exposure |
| SQL string concatenation | `f"SELECT * FROM {table}"`, `"...WHERE id=" + id` | SQL injection |
| Eval/exec usage | `eval()`, `exec()`, `Function()`, `new Function` | Code injection |
| Disabled security | `verify=False`, `secure=False`, `--no-verify` | Bypasses security |
| Changed crypto | Modified hashing, encryption, token generation | Weakened security |
| Broadened permissions | `*` wildcards, `0.0.0.0` bindings, `chmod 777` | Over-permissive access |

## Language-Specific Checks

### Python
- SQL injection: look for f-strings or `.format()` in database queries
- Deserialization: `pickle.loads()`, `yaml.unsafe_load()` on user input
- Path traversal: `open(user_input)` without sanitization
- Command injection: `os.system()`, `subprocess.run(shell=True)`

### JavaScript/TypeScript
- XSS: `innerHTML`, `dangerouslySetInnerHTML`, unescaped template literals
- Prototype pollution: `Object.assign()` with user-controlled input
- Path traversal: `path.join(base, userInput)` without validation
- Regex DoS: complex regex on user input without timeout

### Go
- SQL injection: string concatenation in SQL queries (use `?` placeholders)
- Race conditions: shared state without mutex in goroutines
- Integer overflow: unchecked arithmetic on user-provided numbers

## Review Priority by Risk

| Risk Level | Review Depth | Time Budget |
|------------|-------------|-------------|
| LOW | Skim changed files, check test existence | 2-5 minutes |
| MEDIUM | Read changed + callers, run security checklist | 10-15 minutes |
| HIGH | Full blast radius + security checklist + hub check | 20-30 minutes |
| CRITICAL | All of above + recommend blocking merge until addressed | 30+ minutes |
