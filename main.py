import glob
import json
import os
import time
from os.path import isfile

from tqdm import tqdm

from dotenv import load_dotenv
import hydra
from omegaconf import DictConfig, OmegaConf

from core.Client import APIClient
from postprocess import add2csv, extract_xml

load_dotenv()
TOKEN = os.getenv("TOKEN")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    print(OmegaConf.to_yaml(cfg))

    os.makedirs(f"{cfg.output}/message/", exist_ok=True)
    os.makedirs(f"{cfg.output}/xml/", exist_ok=True)
    os.makedirs(f"{cfg.output}/response/", exist_ok=True)

    with open(f"{cfg.output}/log.txt", "w") as text_file:
        text_file.write("Configurations:")
        text_file.write(OmegaConf.to_yaml(cfg))
        text_file.write("\n")

    client = APIClient(TOKEN,
                       model=cfg.model,
                       server=cfg.server,
                       timeout=cfg.timeout)

    with open(cfg.prompt, "r") as path:
        request = path.read()

    files = list(glob.glob(f"{cfg.input}/*.pdf"))
    successful = 0
    failed = []

    bar = tqdm(files, desc=f"uploading {len(files)} files")
    for path in bar:
        file = os.path.basename(path)

        try:
            client.upload_file(path)
        except Exception as e:
            with open(f"{cfg.output}/log.txt", "a") as text_file:
                text_file.write(f"Got this Exception with {file} during the upload:")
                text_file.write(str(e))
                text_file.write("\n")
                failed.append(file)
                continue

    print(f"Requesting references")
    time.sleep(120)

    bar = tqdm(files)
    for path in bar:
        file = os.path.basename(path)
        bar.set_description(f"{file[:-4]} Successful: {successful}/{successful + len(failed)}")

        if isfile(f"{cfg.output}/message/{file[:-4]}.txt"):
            continue

        try:
            response = client.request_file(path, request)
            message = response['choices'][0]['message']['content']
        except Exception as e:
            with open(f"{cfg.output}/log.txt", "a") as text_file:
                text_file.write(f"Got this Exception with {file} during the request:\n")
                text_file.write(str(e))
                text_file.write("\n")
                failed.append(file)
                continue

        with open(f"{cfg.output}/message/{file[:-4]}.txt", "w") as text_file:
            text_file.write(message)

        with open(f"{cfg.output}/response/{file[:-4]}.json", 'w', encoding='utf-8') as f:
            json.dump(response, f, ensure_ascii=False, indent=4)

        try:
            xml_response = extract_xml(message)
            if xml_response == "": raise Exception("xml string is empty")
            with open(f"{cfg.output}/xml/{file[:-4]}.xml", "w") as text_file:
                text_file.write(xml_response)
        except Exception as e:
            with open(f"{cfg.output}/log.txt", "a") as text_file:
                text_file.write(f"Got this Exception with {file} during the xml extraction:")
                text_file.write(str(e))
                text_file.write("\n")
                failed.append(file)
                continue

        try:
            add2csv(xml_response, f"{cfg.output}/output.csv", file[:-4])
        except Exception as e:
            with open(f"{cfg.output}/log.txt", "a") as text_file:
                text_file.write(f"Got this Exception with {file} during the csv extraction:")
                text_file.write(str(e))
                text_file.write("\n")
                failed.append(file)
                continue

        successful += 1
        bar.set_description(f"{file[:-4]} Successful: {successful}/{successful + len(failed)}")
        time.sleep(5)

    print(f"Process completed.")
    print(f"Successful: {successful}/{len(files)}")
    print(f"Failed: {', '.join(failed)}")


if __name__ == '__main__':
    main()
