import os
import re
from pprint import pprint

from dotenv import load_dotenv
import hydra
from omegaconf import DictConfig
import xml.etree.ElementTree as ET

from core.Client import APIClient
from postprocess import clean_xml_recursive

load_dotenv()
TOKEN = os.getenv("TOKEN")


def extract_xml(string: str):
    pattern = r"(<[a-z]+>[\s\S]*<\/[a-z]+>)"
    matches = re.findall(pattern, string)

    return " ".join(matches)


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    path = "data/Literature/Pseudo-healthy synthesis with pathology disentanglement.pdf"

    pprint(cfg)

    client = APIClient(TOKEN,
                       model=cfg.model,
                       server=cfg.server,
                       timeout=cfg.timeout)

    with open(cfg.prompt, "r") as f:
        request = f.read()

    client.upload_file(path)

    response = client.request_file(path, request)
    message = response['choices'][0]['message']['content']

    print(f"[MESSAGE]: {message}\n\n")

    print(f"[RESPONSE]:")
    pprint(response)


if __name__ == '__main__':
    main()
