from dotenv import dotenv_values

config = dotenv_values(".env")
DATABASE_URL = config["DATABASE_URL"]