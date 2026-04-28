import csv
import re
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from xml.sax.saxutils import escape
from typing import Optional, List


def extract_xml(string: str):
    pattern = r"(<[a-z]+>[\s\S]*<\/[a-z]+>)"
    matches = re.findall(pattern, string)

    return " ".join(matches)


def clean_xml_recursive(text: str) -> str:
    """
    Recursively finds tags, cleans their children, and discards
    the plain-text noise between them.
    """
    tag_pattern = r"<(content|row|author|surname|given-names|year|title|editor|source|fpage|lpage|other|publisher)>(.*?)</\1>"

    matches = list(re.finditer(tag_pattern, text, re.DOTALL))

    if not matches:
        return escape(text.strip())

    parts = []
    for match in matches:
        tag_name = match.group(1)
        inner_content = match.group(2)

        cleaned_inner = clean_xml_recursive(inner_content)
        parts.append(f"<{tag_name}>{cleaned_inner}</{tag_name}>")

    return "\n".join(parts)


def get_text(element: ET.Element, tag: str, default: str | None = None) -> str | None:
    found = element.find(tag)
    return found.text if found is not None else default


def get_autor(autor_xml: ET.Element) -> str | None:
    last_name = get_text(autor_xml, 'surname')
    first_name = get_text(autor_xml, 'given-names')

    if last_name and first_name:
        return f"{last_name}, {first_name}"

    if last_name:
        return f"{last_name}"

    if first_name:
        return f"{first_name}"

    return None


def get_pages(fpage: str | None, lpage: str | None) -> str | None:
    if fpage and lpage:
        return f"{fpage}-{lpage}"

    if fpage:
        return f"{fpage}"

    if lpage:
        return f"{lpage}"

    return None


def apa_entry(authors: List[str],
              year: str,
              title: str,
              editor: Optional[str] = None,
              fpage: Optional[str] = None,
              lpage: Optional[str] = None,
              publisher: Optional[str] = None,
              source: Optional[str] = None):
    authors = " & ".join(authors)
    reference = f"{authors} ({year}). {title}."

    if editor:
        reference += f" {editor}, "

    if source:
        reference += f" {source}"

    if fpage and lpage:
        reference += f" ({fpage}-{lpage})."

    if publisher:
        reference += f" {publisher}."

    return reference


def get_primer_author(authors: List[str]) -> str | None:
    for author in authors:
        if author is None:
            continue

        return author.split(',')[0]
    return None

def extract_entry(ref_id: str, row: Element) -> dict[str, str]:
    entry = {'Ref-id': ref_id}

    authors = [get_autor(a) for a in row.findall('author')]
    primer_author = get_primer_author(authors)
    entry['authors'] = "\n".join(authors)

    entry['title'] = get_text(row, 'title')
    entry['year'] = get_text(row, 'year')
    entry['editor'] = get_text(row, 'editor')
    entry['publisher'] = get_text(row, 'publisher')
    entry['source'] = get_text(row, 'source')

    entry['fpage'] = get_text(row, 'fpage')
    entry['lpage'] = get_text(row, 'lpage')
    entry['page'] = get_pages(entry['fpage'], entry['lpage'])

    entry['string'] = apa_entry(authors=authors,
                                year=entry['year'],
                                title=entry['title'],
                                editor=entry['editor'],
                                fpage=entry['fpage'],
                                lpage=entry['lpage'],
                                publisher=entry['publisher'],
                                source=entry['source']
                                )
    entry['id'] = f"{primer_author}{' Et al. ' if len(authors) > 1 else ' '}({entry['year']})"
    return entry


def add2csv(xml_data: str, file_path: str, ref_id: str) -> None:
    xml_data = clean_xml_recursive(xml_data)

    root = ET.fromstring(f"<root>{xml_data}</root>")
    rows = root.findall('.//row')
    if len(rows) == 0:
        raise ValueError("Could not find <row> or row like element in the XML string!")

    entries = []
    for row in rows:
        entry = extract_entry(ref_id, row)
        entries.append(entry)

    fieldnames = ['Ref-id', 'id', 'authors', 'title', 'year', 'publisher', 'source', 'page',
                  'string']

    with open(file_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')

        if f.tell() == 0:
            writer.writeheader()

        for entry in entries:
            writer.writerow(entry)
