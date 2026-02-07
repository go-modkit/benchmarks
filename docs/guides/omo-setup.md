# Oh-My-OpenCode (OMO) Setup Guide

This guide provides the recommended setup for Oh-My-OpenCode (OMO) to maximize productivity with parallel agents, visual multi-agent execution, and optimized model mapping.

## Prerequisites

### Tmux Integration
To use the visual multi-agent execution (where background agents spawn in separate panes), you must meet these requirements:
1. **Run inside Tmux**: OpenCode must be executed within an active tmux session.
2. **Server Mode**: OpenCode must run with the `--port` flag (e.g., `opencode --port 4096`). This enables the subagent pane spawning mechanism.
3. **Tmux Installed**: Ensure `tmux` is available in your system PATH.

## Recommended Configuration

Create or update your `oh-my-opencode.jsonc` (or `oh-my-opencode.json`) with these recommended settings.

```jsonc
{
  "$schema": "https://raw.githubusercontent.com/code-yeongyu/oh-my-opencode/master/assets/oh-my-opencode.schema.json",

  // 1. Category Model Mapping
  // Optimizes model selection based on task type to balance cost and performance.
  "categories": {
    "quick": {
      "model": "anthropic/claude-haiku-4-5", // Fast + cheap for trivial tasks
      "description": "Trivial tasks - single file changes, typo fixes"
    },
    "ultrabrain": {
      "model": "openai/gpt-5.3-codex", // Deep logical reasoning
      "variant": "xhigh"
    },
    "writing": {
      "model": "google/gemini-3-flash-preview", // Excellent for prose and docs
      "textVerbosity": "high"
    },
    "visual-engineering": {
      "model": "google/gemini-3-pro-preview", // Best for UI/UX and styling
      "is_unstable_agent": true
    }
  },

  // 2. Background Concurrency
  // Controls how many parallel background agents can run simultaneously.
  "background_task": {
    "defaultConcurrency": 5,
    "providerConcurrency": {
      "anthropic": 3,
      "openai": 5,
      "google": 10
    }
  },

  // 3. Tmux Settings
  // Enables visual multi-agent execution in separate tmux panes.
  "tmux": {
    "enabled": true,
    "layout": "main-vertical",
    "main_pane_size": 60
  }
}
```

## Tmux Workflow (Recommended)

To simplify the tmux + server mode workflow, add this function to your shell configuration (e.g., `~/.bashrc`, `~/.zshrc`, or `~/.config/fish/config.fish`).

### Bash/Zsh
```bash
oc() {
    local base_name=$(basename "$PWD")
    local path_hash=$(echo "$PWD" | md5sum | cut -c1-4)
    local session_name="${base_name}-${path_hash}"
    
    # Find available port starting from 4096
    local port=4096
    while [ $port -lt 5096 ]; do
        if ! lsof -i :$port >/dev/null 2>&1; then
            break
        fi
        port=$((port + 1))
    done
    
    export OPENCODE_PORT=$port
    
    if [ -n "$TMUX" ]; then
        # Already inside tmux - just run with port
        opencode --port $port "$@"
    else
        # Create tmux session and run opencode
        local oc_cmd="OPENCODE_PORT=$port opencode --port $port $*; exec $SHELL"
        if tmux has-session -t "$session_name" 2>/dev/null; then
            tmux new-window -t "$session_name" -c "$PWD" "$oc_cmd"
            tmux attach-session -t "$session_name"
        else
            tmux new-session -s "$session_name" -c "$PWD" "$oc_cmd"
        fi
    fi
}
```

## Non-Tmux Fallback

If you cannot use Tmux, OMO still supports background agents, but they will run silently in the background without dedicated terminal panes. You can retrieve their output using the `background_output` tool or wait for system notifications upon completion.

To disable tmux integration explicitly:
```json
{
  "tmux": {
    "enabled": false
  }
}
```

## Official Documentation

For more detailed information, refer to the official Oh-My-OpenCode documentation:
- [Features Overview](https://github.com/code-yeongyu/oh-my-opencode/blob/dev/docs/features.md)
- [Configuration Guide](https://github.com/code-yeongyu/oh-my-opencode/blob/dev/docs/configurations.md)
