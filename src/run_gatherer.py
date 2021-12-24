
import requests
import random
import logging
import json
from pathlib import Path
import parse_config
from image_supplier import ImageSupplier


# Account configuration file path
ACCOUNT_CONFIG_PATH = str(Path().resolve()) + "/account_configurations/"


""" Class to handle calls to Instagram Graph API """


class GraphHandler:

    def __init__(self, args):
        self.args = args
        self.info = dict()
        self.base_url = args.graph_api_base_path + args.graph_api_version

    def get_account_info(self):
        """ Fetches account information of each business account """

        logging.info("Fetching account information from Graph API.")
        # Setting extra fields for info dict
        self.info['accounts'] = []
        # Creating payload
        payload = {'access_token': self.args.graph_api_access_token}
        # Setting url to fetch information about current Graph API user
        url = self.base_url + 'me/accounts'
        # Sending request
        resp = requests.get(url, params=payload)

        # Checking that status is OK
        if resp.status_code == 200:
            resp_data = resp.json()
            # Making sure response data contains data key
            if "data" in resp_data:
                # Processing every account
                for account in resp_data['data']:
                    # Combining name and page ID into dict
                    account_dict = {
                        'name': account['name'], 'page_id': account['id']}
                    # Pushing dict into account info
                    self.info['accounts'].append(account_dict)

    def get_business_user_ids(self):
        """ Gets Instagram Business User identifiers and appends them into the dictionary """

        logging.info("Querying business account user identifiers.")
        if self.info['accounts']:
            # Setting payload to fetch Instagram business account id
            payload = {'access_token': self.args.graph_api_access_token,
                       'fields': 'instagram_business_account'}

            # Iterating over accounts
            for account in self.info['accounts']:
                url = self.base_url + account['page_id']
                logging.info('Sending GET request to url: ' + url)
                # Sending request
                resp = requests.get(url, params=payload)

                if resp.status_code == 200:
                    resp_data = resp.json()
                    if 'instagram_business_account' in resp_data:
                        logging.info(
                            "Received user id " + resp_data['instagram_business_account']['id'])
                        # Setting the received IG user id to the account's dict
                        account['user_id'] = resp_data['instagram_business_account']['id']

    def create_configuration_files(self):
        """ Creates/updates configuration files for each Instagram user. """

        # Calling function that creates dictionary of user info
        self.set_up_info()

        if self.info:
            # Iterating over each account
            for account in self.info['accounts']:
                # Constructing file name
                file_name = ACCOUNT_CONFIG_PATH + account['user_id'] + ".json"
                # If configuration file for the specific account already exists,
                # open in r+ mode to avoid overwriting.
                if Path(file_name).is_file():
                    conf_file = open(file_name, 'r+')
                    conf_data = json.load(conf_file)
                    # Updating name, since only it can be changed.
                    conf_data['name'] = account['name']
                    # Moving pointer back to the beginning of the file.
                    conf_file.seek(0)
                    # Writing updated values
                    json.dump(conf_data, conf_file, indent=4)
                else:
                    conf_file = open(file_name, 'w')
                    # Adding 2 new fields to hold hashtags and captions.
                    account['hashtags'] = []
                    account['captions'] = []
                    account['collections'] = ""
                    json.dump(account, conf_file, indent=4)
                # Closing file
                conf_file.close()

    def get_account_media_count(self):
        """ Fetches the count of posts on the accounts """

        logging.info('Fetching account post counts.')
        if self.info['accounts']:
            payload = {'access_token': self.args.graph_api_access_token}
            for account in self.info['accounts']:
                url = self.base_url + account['user_id'] + '/media'
                logging.info('Sending GET request to url: ' + url)
                # Sending request
                resp = requests.get(url, params=payload)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    logging.info(account['name'] + " has " +
                                 str(len(resp_data['data'])) + " posts.")

    def publish_image(self, creation_id, user_id):
        """ Publishes given image to Instagram account. """

        logging.info("Publishing image to account with user id: " + user_id)
        payload = {'access_token': self.args.graph_api_access_token,
                   'creation_id': creation_id}
        url = self.base_url + user_id + "/media_publish"
        logging.info("Sending POST request to url: " + url)
        resp = requests.post(url, params=payload)

        if resp.status_code == 200:
            logging.info("Post successfully published!")
        else:
            logging.warning(
                "Response from image publishing query is not OK. \n Response: " + resp.json())

    def create_media_container(self, image_info, user_id):
        """ Creates Instagram media container """

        logging.info("Creating Instagram media container.")
        # Setting image url and caption to payload
        payload = {'access_token': self.args.graph_api_access_token,
                   'image_url': image_info['image_url'],
                   'caption': "Car photo by " + image_info['author'] + "."}
        url = self.base_url + user_id + "/media"
        logging.info("Sending POST request to url: " + url + "/media")
        resp = requests.post(url, params=payload)

        if resp.status_code == 200:
            logging.info("Media container successfully created.")
            # Getting creation id as the response
            creation_id = resp.json()['id']
            # Calling publishing function
            self.publish_image(creation_id, user_id)
        else:
            logging.warning(
                "Creation of media container failed. \n Response: " + resp.json())

    def set_up_info(self):
        """ Fetches information needed for API calls and post publishing """

        self.get_account_info()
        self.get_business_user_ids()

    def construct_caption(self, acc_data):
        """ Constructs post caption from multiple strings. """

        # Getting random caption from configuration file
        caption = acc_data['captions'][random.randint(
            0, len(acc_data['captions'])) - 1]

        if acc_data['hashtags']:
            # Adding hashtags as space delimited string
            caption += '\n' * 2 + " ".join(acc_data['hashtags'])
        else:
            logging.warning('Post hashtags not found.')

        # Adding author credits
        if acc_data['author']:
            caption += '\n Photo by ' + acc_data['author']
        else:
            logging.info("Author credits are not found.")

        return caption

    def start_posting_process(self):
        """ Starts the process of posting photos to each account."""

        # Read configuration file into memory
        for p in Path(ACCOUNT_CONFIG_PATH).glob('*.json'):
            # Loading account configuration data into dictionary
            acc_data = json.loads(p.read_text())
            # Setting flag to ensure that required information exists.
            post_valid = True
            # Creating temporary dict to store individual post related information
            post_data = dict()
            post_data['user_id'] = acc_data['user_id']
            logging.info(
                "Starting posting process for account: " + acc_data['name'])

            # Getting image.
            if acc_data['collections']:
                try:
                    supplier = ImageSupplier(self.args)
                    # Passing collection ids to get random image from them.
                    image_data = supplier.get_random_image_from_collections(
                        acc_data['collections'])
                    # Merging image data to account data
                    acc_data.update(image_data)
                    # Setting image url
                    post_data['image_url'] = image_data['image_url']
                except KeyError as exc:
                    logging.error(
                        'Error happened while getting image from ImageSupplier. \n Stacktrace: ' + exc)
                    post_valid = False
            else:
                logging.warning(
                    'Account configuration file does not contain image collection identifiers.')
                post_valid = False

            # Constructing caption for the post.
            if acc_data['captions']:
                # Constructing random caption.
                post_data['caption'] = self.construct_caption(acc_data)
            else:
                logging.warning(
                    "Account configuration file does not contain captions.")
                post_valid = False

            # If post is valid, creating media container.
            if post_valid:
                self.create_media_container()


def main():
    """ Main entry point of the app """

    # Setting up logger
    logging.basicConfig(filename='photogram.log',
                        encoding='utf-8', level=logging.DEBUG)
    # Getting configuration file
    args = parse_config.get_configuration()
    # Initialize Instagram Graph API handler
    handler = GraphHandler(args)

    # Checking if accounts need to be configured.
    if args.configure_accounts:
        handler.create_configuration_files()
    else:
        handler.start_posting_process()

    #image_supplier = ImageSupplier(args)
    #image_info = supplier.get_random_image_from_collections("2102317,9254430")
    #user_id = "17841450746190808"
    #handler.create_media_container(image_info, user_id)


if __name__ == "__main__":
    """ This is executed when run from the command line """

    main()
