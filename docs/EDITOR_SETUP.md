# Yellow import underlines in VS Code

These usually mean Pylance is inspecting a different Python environment from
the one running DefectRAG. They do not by themselves mean the application failed.

1. Open the project folder in VS Code.
2. Press Ctrl+Shift+P, choose Python: Select Interpreter, then Enter interpreter
   path. On this computer choose:
   C:\Users\User\Desktop\DefectRAG-Verified\.venv-defectrag\Scripts\python.exe
3. Saved .vscode/settings.json also exposes the existing workspace .test-deps
   overlay. Reload the editor window after changing the interpreter.
4. Verify with `python -m scripts.check_environment` using that environment.
   Set PYTHONPATH as shown in the README for the existing overlay.

Settings describe this workstation. On another computer select the project's
.venv\Scripts\python.exe and remove unavailable overlay paths. Do not repeatedly
install packages into random environments to silence warnings. Check the Problems
panel: unresolved imports differ from type warnings or unused imports. The runtime
and software tests are verified separately; VS Code's Problems panel was not inspected.
