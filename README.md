# Plantbot

*Tested with Python 3.12*

## Python libraries
- sounddevice: For real-time audio processing
- numpy: For math operations
- scipy: For saving audio files
- pydub: For audio file conversion
- webrtcvad: For voice detection
- openai: To access OpenAI

### Optional instructions

`pip install virtualenv`

(this installs the virtual environment program)

`virtualenv venv`

(this creates the virtual environment venv)

`virtualenv -p /usr/bin/python3.12 venv`

(here we set the virtual environment with python 3.12, assuming this is the version that was downloaded)

`source venv/bin/activate`

(this launches the virtual environment, ONLY THEN you should install the python libraries)

You can either replace the `openai.api_key = os.getenv("OPENAI_API_KEY")` with your own API key

or you can use `export OPENAI_API_KEY='_your_openAI_key_here_'` in the terminal.
