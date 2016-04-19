# HarkFM
An alternative Last.fm client.

## Getting Started
1. Download the latest [release](https://github.com/emmercm/HarkFM/releases).

## Building HarkFM From Source
1. Install [Python 3.4](https://www.python.org/downloads/)
2. Install [PyQt5](https://www.riverbankcomputing.com/software/pyqt/download5) for Python 3.4.
3. Install PyPi dependencies:
```
pip install genshi pypiwin32 psutil pylast jsonpickle
```
4. Build QtDesigner Python files:
```
C:\Python34\Lib\site-packages\PyQt5\pyuic5 QtDesigner.ui QtDesigner.ui -o QtDesigner.py
```
5. Configure API keys in `engine.json`.

## Developer Todo
- Last.fm love/unlove actions.
- Toast notifications on track change.
- About application popup window.
- Configurable options:
  - Enable/disable scrobbling.
  - Percent to listen to song at.
  - Percent to scrobble song at.
  - Enable/disable regex replacement.
  - Enable/disable TTS announcements.
- Application icon.
- Daydream using artist/album images.
- Display user's event history for current playing artist.