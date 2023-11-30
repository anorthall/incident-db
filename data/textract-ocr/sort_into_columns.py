"""
A script to sort the raw text from AWS Textract into two equal columns.

It is designed to take the JSON output from AWS Textract for a document where there are
two (and only two) columns of text per page. It crudely splits the page from the exact
middle and outputs the text when reading from left to right.

It also attempts (crudely) to mark dates and page numbers using very basic syntax.
"""

import json
import os
import re

JSON_DIR = "json/"
RESULTS_DIR = "results/"


class Line:
    def __init__(self, text, top, left, width, height, page):
        self.text = text
        self.top = top
        self.left = left
        self.width = width
        self.height = height
        self.page = page

    def __repr__(self):
        return self.text


class Page:
    def __init__(self, number, lines=None):
        self.number = number

        if lines is None:
            self.lines = []
        else:
            self.lines = lines

    def __repr__(self):
        return f"Page {self.number}"


class Column:
    def __init__(self, page, name):
        self.page = page
        self.name = name
        self.lines = []

    def __repr__(self):
        return f"Page {self.page} {self.name} column"


# def get_average_spacing(blocks, page):
#     """Get the average spacing between the previous and next line on the same page"""
#     total_spacing = 0
#     num_lines = 0
#     for i, block in enumerate(blocks):
#         if block["BlockType"] == "LINE" and block["Page"] == page:
#             if i > 0 and blocks[i - 1]["BlockType"] == "LINE":
#                 total_spacing += (
#                     block["Geometry"]["BoundingBox"]["Top"]
#                     - blocks[i - 1]["Geometry"]["BoundingBox"]["Top"]
#                 )
#                 num_lines += 1
#     return total_spacing / num_lines


# def get_spacing_for_line(blocks, line):
#     """Get the spacing for a specific line on a page"""
#     for i, block in enumerate(blocks):
#         if block["BlockType"] == "LINE":
#             if block["Text"] == line.text:
#                 if i > 0 and blocks[i - 1]["BlockType"] == "LINE":
#                     return (
#                         block["Geometry"]["BoundingBox"]["Top"]
#                         - blocks[i - 1]["Geometry"]["BoundingBox"]["Top"]
#                     )
#     return 0


def filter_line(line):
    """Apply various filters to lines"""

    # Remove lines that are just numbers
    match = re.search(r"^\d*$", line.text)
    if match:
        return None

    # Remove lines that begin with "NSS News"
    match = re.search(r"^NSS News", line.text, re.IGNORECASE)
    if match:
        return None

    # Highlight lines that begin with a date
    date_highlight = "\n\n********** "
    # Matches type: December 27, 1983
    match = re.search(r"^\w+ \d{1,2}, \d{4}$", line.text)
    if match:
        line.text = date_highlight + line.text
        return line

    # Matches type: Sunday, 3 December 1972
    match = re.search(r"^\w+, \d{1,2} \w+ \d{4}$", line.text)
    if match:
        line.text = date_highlight + line.text
        return line

    # Matches type: 23 December
    match = re.search(r"^\d{1,2} \w+$", line.text)
    if match:
        line.text = date_highlight + line.text
        return line

    # Matches type: 11 July 2020
    match = re.search(r"^\d{1,2} \w+ \d{4}$", line.text)
    if match:
        line.text = date_highlight + line.text
        return line

    # Match old report start types
    # e.g. "West Virginia, Bat Cave:"
    match = re.search(r"^\w+\s?\w*, [a-zA-Z]+( [a-zA-Z]+)*:", line.text)
    if match:
        line.text = date_highlight + line.text
        return line

    return line


def process_lines(json_response):
    """Generate a list of Line objects from the JSON response"""
    lines = []
    # page_spacing = {}
    # blocks = json_response["Blocks"]

    for item in json_response["Blocks"]:
        if item["BlockType"] == "LINE":
            line = Line(
                text=item["Text"],
                top=item["Geometry"]["BoundingBox"]["Top"],
                left=item["Geometry"]["BoundingBox"]["Left"],
                width=item["Geometry"]["BoundingBox"]["Width"],
                height=item["Geometry"]["BoundingBox"]["Height"],
                page=item["Page"],
            )

            line = filter_line(line)
            if line:
                lines.append(line)

    return lines


def sort_lines_into_pages(lines):
    """Generate a list of Page objects from the list of Line objects"""
    pages = {}
    for line in lines:
        if line.page in pages:
            pages[line.page].lines.append(line)
        else:
            pages[line.page] = Page(line.page)
            pages[line.page].lines.append(line)
    return pages.values()


def sort_pages_into_columns(pages):
    """Sort the pages into one left and one right column"""
    pages_with_cols = []
    for page in pages:
        left_col_lines = []
        right_col_lines = []
        for line in page.lines:
            if line.left < 0.5:
                left_col_lines.append(line)
            else:
                right_col_lines.append(line)

        pages_with_cols.append(Page(page.number, (left_col_lines + right_col_lines)))
    return pages_with_cols


def process_file(report_name, file):
    with open(file) as f:
        response = json.load(f)

    lines = process_lines(response)
    pages = sort_lines_into_pages(lines)
    pages = sort_pages_into_columns(pages)

    # for page in pages:
    #     results_name = f"{result_dir}{page.number}.txt"
    #     with open(results_name, "w") as f:
    #         for line in page.lines:
    #             f.write(line.text + "\n")

    full_text_name = f"{RESULTS_DIR}{report_name}.txt"
    with open(full_text_name, "w") as f:
        for page in pages:
            f.write("\n---------- Page " + str(page.number) + " ----------\n")
            for line in page.lines:
                f.write(line.text + "\n")


def main():
    """Get a list of files and process them"""
    files = os.listdir(JSON_DIR)
    for file in files:
        report_name = file.split(".")[0]
        print(f"Processing {report_name}...")
        process_file(report_name, JSON_DIR + file)
    print("Done!")


if __name__ == "__main__":
    main()
