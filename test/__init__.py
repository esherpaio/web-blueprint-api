import os

from dotenv import load_dotenv

os.environ["CONFIG_MODULE"] = "test.config"
load_dotenv(dotenv_path="test/.env", override=True)
