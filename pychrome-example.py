#!/usr/bin/env python3
"""
Extensive example script for using pychrome.

In order to use this script, you have to start Google Chrome/Chromium
with remote debugging as follows:
    google-chrome --remote-debugging-port=9222 --enable-automation

You can also run in headless mode, which doesn't require a graphical
user interface by supplying --headless.
"""
import json
import pprint
from typing import List

import pychrome
import csv


def read_from_file() -> List[str]:
    # Reading from file
    rows = []
    with open("input_urls.txt", 'r') as file:
        for line in file:
            rows.append(line)
    return rows


# output_header_fields = ['page-url', 'google-analytics-enabled','anonymize-ip']
output_filename = "output.csv"


def write_to_file(page_url: str, ga_enabled: bool, anonymize_ip: bool):
    with open(output_filename, 'a') as csvfile:
        # creating a csv writer object
        csvwriter = csv.writer(csvfile)

        # writing the fields
        csvwriter.writerow([page_url, ga_enabled, anonymize_ip])


class Crawler:
    def __init__(self, debugger_url='http://0.0.0.0:9222'):
        # Create a browser instance which controls Google Chrome/Chromium.
        self.browser = pychrome.Browser(url=debugger_url)

    def crawl_page(self, url):
        # Initialize _is_loaded variable to False. It will be set to True
        # when the loadEventFired event occurs.
        self._is_loaded = False

        # Create a tab
        self.tab = self.browser.new_tab()

        # Set callbacks for request in response logging.
        self.tab.Network.requestWillBeSent = self._event_request_will_be_sent
        self.tab.Network.responseReceived = self._event_response_received
        self.tab.Page.loadEventFired = self._event_load_event_fired

        # Start our tab after callbacks have been registered.
        self.tab.start()

        # Enable network notifications for all request/response so our
        # callbacks actually receive some data.
        self.tab.Network.enable()

        # Enable page domain notifications so our load_event_fired
        # callback is called when the page is loaded.
        self.tab.Page.enable()

        # Navigate to a specific page
        self.tab.Page.navigate(url=url, _timeout=15)

        # We wait for our load event to be fired (see `_event_load_event_fired`)
        while not self._is_loaded:
            self.tab.wait(1)

        # Wait some time for events, after the page has been loaded to look
        # for further requests from JavaScript
        self.tab.wait(10)

        # Run a JavaScript expression on the page.
        # If Google Analytics is included in the page, this expression will tell you
        # whether the site owner's wanted to enable anonymize IP. The expression will
        # fail with a JavaScript exception if Google Analytics is not in use.
        result = self.tab.Runtime.evaluate(expression="ga.getAll()[0].get('anonymizeIp')")
        print(result)
        if result is True:
            print("anonymizeIp enabled")
            write_to_file(page_url=url, ga_enabled=True, anonymize_ip=True)

        else:
            if result['result']['type'] == "undefined":
                print("Google analytics enabled but anonymizeIp was not in use")
                write_to_file(page_url=url, ga_enabled=True, anonymize_ip=False)
            else:
                print("Google analytics was not in use")
                write_to_file(page_url=url, ga_enabled=False, anonymize_ip=False)



        # Stop the tab
        self.tab.stop()

        # Close tab
        self.browser.close_tab(self.tab)

    def _event_request_will_be_sent(self, request, **kwargs):
        """Will be called when a request is about to be sent.

        Those requests can still be blocked or intercepted and modified.
        This example script does not use any blocking or intercepting.

        Note: It does not say anything about the request being sucessful,
        there can still be connection issues.
        """
        pprint.pprint(request)

    def _event_response_received(self, response, **kwargs):
        """Will be called when a response is received.

        This includes the originating request which resulted in the
        response being received.
        """
        pprint.pprint(response)

    def _event_load_event_fired(self, timestamp, **kwargs):
        """Will be called when the page sends an load event.

        Note that this only means that all resources are loaded, the
        page may still processes some JavaScript.
        """
        self._is_loaded = True


def main():
    c = Crawler()

    urls = read_from_file()
    # Crawling for each url
    for url in urls:
        c.crawl_page(url)


if __name__ == '__main__':
    main()
