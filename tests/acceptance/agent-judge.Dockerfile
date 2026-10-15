# The pinned base release comes from releases.json; CI passes it as BASE.
ARG BASE
FROM ${BASE}

RUN npm install -g \
        @openai/codex@0.146.0 \
        @anthropic-ai/claude-code@2.1.227 \
    && codex --version \
    && claude --version
