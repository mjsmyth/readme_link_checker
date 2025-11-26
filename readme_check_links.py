'''Readme check links to check links in readme pages'''
# Download from github the markdown files "code" of the required version
# Put the markdown folder in the markdown folder in the project 
# Enter the dirctory name with -m mdfiles option
# Run python readme_check_links_v2.py -m mysite_vx.x.x
#
# Check links in readme pages
import requests
import csv
import json
import copy
import datetime
import sys
import getopt
import re
import os
import itertools
import glob
import re
import yaml
import copy


def check_valid_link_slug(section, slug, section_file_slugs, page_section):
    if section == "":
        print(f"Missing section")
        section = page_section[:]
    found = False
    for section_name in section_file_slugs.keys():
        if section in section_name:
            for file_info in section_file_slugs[section_name]:
                slug_match = file_info[0]
                if slug in slug_match:
                    # print(f"found slug -{section}-{slug}")
                    found = True
    return found
    # bad_doc_link_dict[page_slug].append([doc_space, doc_slug, link_page_name])
    # bad_links.append(["doc", doc_space, doc_slug, link_page_name])


def split_link(link, page_section, page_slug):
    # print(f"    Link: {link}")
    link_section = ""
    link_slug = ""
    link_text = ""
    link_stripped = link.strip(r"[)")
    link_parts = link_stripped.split(r"](")
    link_text = link_parts[0]
    link_page_parts = link_parts[1].split(r":")
    if len(link_page_parts) == 0:
        print(f"{page_slug} : Empty link with text {link_text}")
    if len(link_page_parts) == 1:
        link_section = page_section[:]
        link_slug = link_page_parts[0]
        print(f"{page_slug} : Missing link section?: {link_text} -> {link_slug}")
    if len(link_page_parts) == 2:
        link_section = link_page_parts[0]
        link_slug = link_page_parts[-1]
    return (link_text,link_section,link_slug)


def check_slug_is_title(slug, title):
    check = title.lower().replace(r" ",r"-")
    # print(check)
    # print(slug)
    if check == slug:
        return True
    else:
        print(f"{slug}: {title} NOT THE SAME AS {slug}")
        return False


def get_section_file_slugs(sections,mdfiles):
    # for f in glob.glob('/path/**/*.md', recursive=True):
    #     print(f)
    ''' Get the names and paths and slugs of the markdown files in each section'''
    section_file_slugs = {}
    for section in sections:
        section_file_slugs[section] = []
        link_dir_files = f"./markdown/{mdfiles}/{section}/**/*.md"
        files = glob.glob(link_dir_files, recursive=True)
        dir_dic = {}
        for file_path in files:
            file_split = re.split(r"[/.]", file_path)
            if file_split[-2] == "index":
                file_slug = file_split[-3]
            else:
                file_slug = file_split[-2]
            file_info = (file_slug,file_path)
            section_file_slugs[section].append(file_info)
    return section_file_slugs


def get_data_from_md(section, file_slug, file_path, section_file_slugs, page_slug_titles, page_next_links):
    # get data from the markdown
    title_format = r"title:\s([\S\s]*?)\n"
#    title_format = r"title:\s([A-Z,a-z,1-9,:,\s\?]*?)\n"
    hidden_format = r"hidden:\s([a-z]*?)\n"
    # next_link_format = r"slug:\s([a-z,1-9,:,-]*?)\n"
    next_format = r"(?<=next:\n)[\S\s]*?(?=---)"
    link_format = r"\[[A-Z,a-z,\-,\s]*?]\([a-z,1-9,\:,\-]*?\)"

    next_yaml = ""
    mdtext = ""
    page_title = ""
    next_title = ""
    next_slug = ""

    with open(file_path, 'r') as mdfile:
        mdtext = mdfile.read()

    found_title = re.search(title_format, mdtext)
    if found_title:
        page_title = found_title.group(1)
    slug_match = check_slug_is_title(file_slug, page_title) 
    # this checks slug is title
    if not slug_match:
        page_slug_titles.append([section, page_title, file_slug])
    
    found_links = re.findall(link_format, mdtext)
    for link in found_links:
        link_text_in_page,link_section,link_slug = split_link(link, section, file_slug)
        valid_link = check_valid_link_slug(link_section, link_slug, section_file_slugs, section)
        if not valid_link:
            print(f"{file_slug}: {link_text_in_page} invalid link to {link_section} : {link_slug}")
            page_next_links.append([section, file_slug, "inline", link_text_in_page, link_section, link_slug])
    found_next = re.search(next_format, mdtext)

    if found_next:
        next_yaml = found_next.group()
        next_text = yaml.safe_load(next_yaml)
        json_str = json.dumps(next_text)
        next_dict = json.loads(json_str)
        if next_dict["description"]:
            if "pages" in next_dict:
                for page in next_dict["pages"]:
                    if "slug" in page:
                        next_slug = page["slug"]
                        next_title = page["title"]
                        next_type = page["type"]
                        if "endpoint" in page["type"]:
                            next_section = "reference"
                        elif "basic" in page["type"]:
                            next_section = "docs"
                        else:
                            print(f"Unknown section type: {type}")
                        valid_next_link = check_valid_link_slug(next_section, next_slug, section_file_slugs, section)
                        if not valid_next_link:
                            print(f"{file_slug}: {next_title} invalid link to {next_section} : {next_slug}")
                            page_next_links.append([section, file_slug, "next", next_title, next_section, next_slug])
    found_hidden = re.search(hidden_format, mdtext)
    if found_hidden:
        hidden_text = found_hidden.group(1)
        if hidden_text == "true":
            hidden = True
        else:
            hidden = False

    # markdown_data["file_slug"] = file_slug
    # markdown_data["section"] = section
    # markdown_data["title"] = page_title
    # markdown_data["slug_match"] = slug_match
    # markdown_data["hidden"] = hidden


def main(argv):
    page_slug_titles = []
    page_next_links = []
    print ('argument list', sys.argv)
    mdfiles = ''
    try:
        opts, args = getopt.getopt(argv,"hm:",["mdfiles="])
    except getopt.GetoptError:
        print ('readme_doc_list.py -m <mdfiles=(site)-x.x.x>')
        sys.exit(2)
    for opt, arg in opts:
        print (opt, arg)
        if opt == '-h':
            print ('readme_check_links.py -m <mdfiles>=(site)-(x.x.x)')
            sys.exit()
        elif opt in ("-m", "--mdfiles"):
            mdfiles = arg
            mdfiles.strip()
            print ('MarkdownFiles', mdfiles)
            if not re.match(r"[\w,-]+?-[0-9,\.]", mdfiles):
                print ('readme_check_links.py --m <mdfiles>=(site)-(version))')
                sys.exit(2)

    page_slug_titles_header = ["Section", "Page title", "Page slug"]

    page_next_links_header = ["Section", "Page slug", "Type", "Link text", "Section", "Link slug" ]

    sections = ["docs", "reference"]
    # api_sections = ["guides", "reference"]

    section_file_slugs = get_section_file_slugs(sections,mdfiles)

    for section in section_file_slugs:
        # print(section_file_slugs[section])
        for file_info in section_file_slugs[section]:
            file_slug = file_info[0]
            file_path = file_info[1]

            print("--------------------------------------")
            get_data_from_md(section, file_slug, file_path, section_file_slugs, page_slug_titles, page_next_links)

    current_date = datetime.date.today()

    with open(f'./csv_reports/{mdfiles}_{current_date}_page_slug_titles.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(page_slug_titles_header)
        for page in page_slug_titles:
            writer.writerow(page)

    with open(f'./csv_reports/{mdfiles}_{current_date}_page_next_links.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(page_next_links_header)
        for page in page_next_links:
            writer.writerow(page)


if __name__ == "__main__":
    main(sys.argv[1:])
