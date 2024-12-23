import collections
from github import Github, InputGitTreeElement
import os
from dotenv import load_dotenv
import logging
from logging.config import dictConfig
from logging_file import LOGGING

dictConfig(LOGGING)
logger = logging.getLogger("dev_logger")

load_dotenv()
email_address = os.getenv("EMAIL")
token = os.getenv("GIT_TOKEN")
base_url = os.getenv("GIT_URL")


def search_code_in_github(keyword, extension):
    try:
        g = Github(base_url=base_url, login_or_token=token)
        user = g.get_user().login
        return perform_search(g, keyword, extension)
    except Exception as e:
        logger.error(f"Failed to authenticate or connect to GitHub: {e}")
        return str(e)


def perform_search(g, keyword, extension):
    try:
        extensionlist = [
            "All relevant matches",
            "all relevant matches",
            "all",
            "All",
            "",
        ]
        if extension not in extensionlist:
            return search_with_extension(g, keyword, extension)
        else:
            return search_without_extension(g, keyword)
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return str(e)


def search_with_extension(g, keyword, extension):
    try:
        extensionsearchlist = []
        query = f"{keyword} in:file extension:{extension}"
        repositories = g.search_code(query, highlight=True)
        max_size = 20
        if repositories.totalCount > max_size:
            repositories = repositories[:max_size]
        for repo in repositories:
            extensionsearchlist.append(repo.html_url)
        if not extensionsearchlist:
            return "No results found"
        else:
            extensionsearchlist = [
                item
                for item, count in collections.Counter(extensionsearchlist).items()
                if count >= 1
            ]
            list_data = extensionsearchlist[:10]
            logger.info(list_data)
            return list_data
    except Exception as e:
        logger.error(f"Error during search with extension: {e}")
        return str(e)


def search_without_extension(g, keyword):
    try:
        query = keyword
        storeresults = []
        repositories = g.search_code(query, highlight=True)
        max_size = 100
        if repositories.totalCount > max_size:
            repositories = repositories[:max_size]
        for repo in repositories:
            storeresults.append(repo.html_url)
        file_filter = [
            file
            for file in storeresults
            if not file.endswith((".txt", ".csv", "README.md", ".gitignore", "."))
        ]
        res1 = [
            item
            for item, count in collections.Counter(file_filter).items()
            if count >= 1
        ]
        list_data = res1[:10]
        logger.info(list_data)
        return list_data
    except Exception as e:
        logger.error(f"Error during search without extension: {e}")
        return str(e)
