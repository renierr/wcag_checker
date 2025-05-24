def inject_outline_css(driver):
    """
    Inject CSS styles for element into the page.

    :param driver: The Selenium WebDriver instance.
    """

    # language=CSS
    css = """
    .contrat_checker--outline {
        outline: 2px dotted red !important;
        outline-offset: 3px !important;
    }
    .contrat_checker--label {
        position: absolute;
        background-color: yellow;
        color: black;
        font-size: 10px;
        font-weight: bold;
        line-height: 12px;
        padding: 2px;
        z-index: 99999;
        pointer-events: none;
        box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.5);
        border-radius: 3px;
    }
    .contrat_checker--label::after {
        content: '';
        position: absolute;
        top: 100%;
        left: 50%;
        transform: translateX(-50%);
        width: 0;
        height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid yellow;
        filter: drop-shadow(1px 1px 2px rgba(0, 0, 0, 0.5));
    }
    """

    # language=JS
    script = f"""
    const style = document.createElement('style');
    style.type = 'text/css';
    style.appendChild(document.createTextNode(`{css}`));
    document.head.appendChild(style);
    """
    driver.execute_script(script)
