# Application boundaries

- `config.py`: product settings, format registry, UI copy.
- `core.py`: input validation, tool lookup, download options.
- `worker.py`: network/conversion subprocess; pipe events only.
- `controller.py`: process ownership, cancellation and Qt event delivery.
- `app.py`: widgets and local preferences; no direct network calls.

Never pass user input through a shell. Worker does not load yt-dlp user config.
Only mark complete after downloader exits successfully. Format choices are data.
Keep QLabel strings plain text since remote titles are untrusted input.
