# HarkFM
An alternative Last.fm client.

## Getting Started
1. Download the latest [release](https://github.com/emmercm/HarkFM/releases).

## Building HarkFM From Source
1. Install [Python 3](https://www.python.org/downloads/).
2. Install PyPi dependencies:<br/>
`pip install PyQt5 genshi pypiwin32 psutil pylast jsonpickle`
3. Configure API keys in `engine.json`.

## Developer Todo
- Put current Last.fm username in window title.
- Figure out how to compile into Windows binary.
- Application icon.
- Put a timer on harkfm.Storage save (don't thrash HDD with multiple updates in a row).
- Toast notifications on track change.
- Ability to skip tracks based on some regex.
- Display user's event history for current playing artist (make unofficial API functions).
- Daydream window with popular artists/tracks/albums when not playing anything.
- Option to prevent screensaver.
- Ability to tag tracks.
- Windows Aero taskbar sub-icon (if possible with Qt).
- Windows Aero taskbar hover mini icons (if possible with Qt).
- Front-end button for YouTube search for top music video.
- Filter out tags: "seen live", artist name in track tags
