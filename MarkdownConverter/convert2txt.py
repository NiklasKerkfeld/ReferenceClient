import argparse
import glob
import os
from os.path import isfile

from marker.converters.pdf import PdfConverter
from marker.models import create_model_dict
from marker.output import text_from_rendered

from tqdm import tqdm


def to_text(path: str) -> str:
    converter = PdfConverter(
        artifact_dict=create_model_dict(),
    )
    rendered = converter(path)
    text, _, images = text_from_rendered(rendered)

    return text


def main(input: str, output: str) -> None:

    if isfile(input):
        files = [input]
    else:
        files = glob.glob(f"./{input}/*.pdf")

    for file in tqdm(files, total=len(files), desc="Converting..."):
        name = os.path.basename(file)[:-4]

        if os.path.isfile(f"./{output}/{name}.md"):
            continue

        text = to_text(file)

        os.makedirs(f"./{output}", exist_ok=True)
        with open(f"./{output}/{name}.md", "w") as text_file:
            text_file.write(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process some file paths.")

    parser.add_argument('--input', type=str, required=True, help="Path to the input file of folder with inputs files")
    parser.add_argument('--output', type=str, required=True, help="Path to the output folder")

    args = parser.parse_args()

    main(args.input, args.output)