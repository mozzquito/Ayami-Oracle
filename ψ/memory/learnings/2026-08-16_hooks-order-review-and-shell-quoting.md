---
pattern: Typecheck passing is not proof a React diff is safe; scan hook order explicitly, and never embed backticks in a double-quoted shell prompt
date: 2026-08-16
source: "rrr: call.md (feature sprint, blank-page bug, import-clip)"
concepts: [react, rules-of-hooks, verification, shell-quoting, delegation]
---

# Typecheck ≠ runtime-safe React, and backticks break shell prompts

Two concrete misses in the same session, both caught late (one by the user hitting a live crash, one by immediate command failure):

**1. React Rules-of-Hooks violations are invisible to `tsc`.** A delegated diff moved a `useState(title)` call to after two early `return` statements in a component. TypeScript compiled it fine — hook ordering is a runtime contract, not a type. The bug crashed the whole page to a blank screen (React detects the hook-count mismatch between renders and unmounts). The habit of "diff review + typecheck = verified" that worked well elsewhere this session wasn't sufficient here.

**Rule**: when reviewing any diff that touches a React component with early `return` statements, explicitly check — is every `useState`/`useEffect`/`useMemo`/`useRef`/`useQuery`/`useMutation` call positioned before every `return` in that component? Do this as a separate, deliberate pass; don't let "typecheck passed" stand in for it.

**2. Markdown backticks inside a double-quoted shell string are command substitution, not formatting.** Constructing a `zcode -p "..."` prompt with inline code snippets like `` `collection.uploadFile(...)` `` for readability caused zsh to interpret the backtick-wrapped text as a command to execute, corrupting the whole invocation before the delegate agent ever started (visible as "no matches found" / "command not found" errors from the *shell*, not the agent).

**Rule**: never put literal backticks in a double-quoted string passed as a CLI argument. Either write the prompt to a file first (heredoc with a quoted delimiter, `cat <<'EOF'`) and interpolate via `$(cat file)`, or strip backtick-formatting from inline code references when composing prompts inline.

Both misses share a shape worth naming: a tool (compiler, shell) gave a green light on a dimension it wasn't actually checking, and that green light got over-trusted. See [[feedback_delegate_verify_workflow]] for the broader verify-before-trusting pattern this session already established — this extends it to "verify the *kind* of check you're running actually covers the failure mode you're worried about."
