# chunker
Web Scraper + Chunker leveraging GPT model

Dear people who will read and use this,

Setting this up is easy:
- `python3 -m venv chuncker-env` to create virtual env
- `source chuncker-env/bin/activate` to activate virtual env
- `pip3 install requirements.txt` to install dependencies
- `python3 chunker.py` to run chunker

Notes:
- OpenAI key is exposed, but hopefully it is not abused
- `MAX_SOUPS` can be set to `None` to perform full scraping
