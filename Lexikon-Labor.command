#!/bin/zsh
cd "${0:A:h}"
if curl --silent --fail http://127.0.0.1:8765/api/words >/dev/null; then
  open http://127.0.0.1:8765
  exit 0
fi
(sleep 2; open http://127.0.0.1:8765) &
exec .venv/bin/python demo_server.py
