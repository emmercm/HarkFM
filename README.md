# HarkFM
An alternative Last.fm client.

## Getting Started
1. Download the latest [release](https://github.com/emmercm/HarkFM/releases).

## Building HarkFM From Source
1. Install [Python 3.4](https://www.python.org/downloads/).
2. Install [PyQt5](https://www.riverbankcomputing.com/software/pyqt/download5) for Python 3.4.
3. Install PyPi dependencies:<br/>
`pip install genshi pypiwin32 psutil pylast jsonpickle`
4. Build QtDesigner Python files:<br/>
`C:\Python34\Lib\site-packages\PyQt5\pyuic5 QtDesigner.ui -o QtDesigner.py`
5. Configure API keys in `engine.json`.

## Developer Todo
- Make Google font offline.
- Figure out how to compile into Windows binary.
- Put current Last.fm username in window title.
- Application icon.
- Put a timer on harkfm.Storage save (don't thrash HDD with multiple updates in a row).
- Toast notifications on track change.
- Ability to skip tracks based on some regex.
- Display user's event history for current playing artist (make unofficial API functions).
- Ability to tag tracks.
- Windows Aero taskbar sub-icon (if possible with Qt).
- Windows Aero taskbar hover mini icons (if possible with Qt).
- Daydream window with popular artists/tracks/albums when not playing anything.
- Front-end button for YouTube search for top music video.
