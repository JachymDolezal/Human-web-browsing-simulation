from selenium.webdriver.common.by import By

from .logger import Logger

L = Logger()


def get_attribues(element) -> dict:
    """
    Get attributes of the element

    :param element: WebElement

    :return: dict with attributes
    """
    attributes = {}
    attributes["id"] = element.get_attribute("id")
    attributes["name"] = element.get_attribute("name")
    attributes["link_text"] = element.get_attribute("link text")
    attributes["tag_name"] = element.get_attribute("tag name")
    return attributes


def get_web_data(driver, web_config=None) -> dict:
    """
    Get all links, buttons and input fields from the website.

    :param driver: selenium driver

    :return: dict with links, buttons, input fields, search id and submit id

    dict format

    {
        "links": List[WebElement],
        "input_fields": List[WebElement],
        "buttons": List[WebElement],
        "search_id": str,
        "submit_id": str,
        "page_source": str,
        "page_markdown": str,
        "hrefs": List[str]
    }

    buttons and input fields have also id attribute, name attribute and text
    """
    # get all links and buttons

    web_data = {}

    web_data["search_id"] = None
    web_data["submit_id"] = None
    web_data["hrefs"] = []

    web_data["links"] = driver.find_elements(By.TAG_NAME, "a")

    web_data["input_fields"] = driver.find_elements(By.TAG_NAME, "input")

    web_data["input_fields_parsed"] = []

    for field in web_data["input_fields"]:
        # get element by id, name, link text, tag name, class name as dict
        field_dict = get_attribues(field)

        if "search" in field.get_attribute("id") or "q" == field.get_attribute("id"):
            # save to goal dict
            web_data["search_id"] = field.get_attribute("id")
        else:
            for field in web_data["input_fields"]:
                if "search" in field_dict["id"]:
                    # save to goal dict
                    web_data["search_id"] = field_dict["id"]

        # assign field dict to web data
        web_data["input_fields_parsed"].append(field_dict)

    # find all submit buttons

    web_data["buttons"] = driver.find_elements(By.TAG_NAME, "button")

    web_data["buttons_parsed"] = []

    for button in web_data["buttons"]:
        web_data["buttons_parsed"].append(get_attribues(button))

        button_id = button.get_attribute("id")



        if "submit" == button_id:
            # save to goal dict
            web_data["submit_id"] = button_id
        else:
            web_data["submit_id"] = None

    web_data["page_source"] = driver.page_source

    for link in web_data["links"]:
        try:
            link_text = link.text.strip()  # Strip leading and trailing whitespace
            if link_text:  # Check if the string is not empty after stripping
                web_data["hrefs"].append(link_text)  # Add non-empty strings to the list
        except:
            L.error(
                "Error while extracting hrefs from links returning empty list and continuing ..."
            )
            return web_data

    # save titles of hrefs
    if web_config is not None:
        if "type" in web_config:
            web_data["search_id"] = web_config.get("name", None)
            web_data["search_id_config"] = web_config
        if "submit_id" in web_config:
            web_data["submit_id"] = web_config.get("submit_id", None)
        if "filter_hrefs" in web_config:
            web_data["hrefs"] = []

    return web_data
