import parse_config
import requests
from image_supplier import ImageSupplier


class GraphHandler:

    def __init__(self, args):
        self.args = args
        self.info = dict()
        self.base_url = args.graph_api_base_path + args.graph_api_version

    def get_account_info(self):
        """ Fetches account information of each business account """

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

        if self.info['accounts']:
            # Setting payload to fetch Instagram business account id
            payload = {'access_token': self.args.graph_api_access_token,
                       'fields': 'instagram_business_account'}

            # Iterating over accounts
            for account in self.info['accounts']:
                url = self.base_url + account['page_id']
                # Sending request
                resp = requests.get(url, params=payload)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    if "instagram_business_account" in resp_data:
                        # Setting the received IG user id to the account's dict
                        account['user_id'] = resp_data['instagram_business_account']['id']

    def get_account_media_count(self):
        """ Fetches the count of posts on the accounts """

        if self.info['accounts']:
            payload = {'access_token': self.args.graph_api_access_token}
            for account in self.info['accounts']:
                url = self.base_url + account['user_id'] + '/media'
                # Sending request
                resp = requests.get(url, params=payload)
                if resp.status_code == 200:
                    resp_data = resp.json()
                    print(account['name'] + " has " +
                          str(len(resp_data['data'])) + " posts.")

    def publish_image_to_account(self, creation_id, user_id):
        """ Publishes given image to Instagram account. """

        payload = {'access_token': self.args.graph_api_access_token,
                   'creation_id': creation_id}
        url = self.base_url + user_id + "/media_publish"
        resp = requests.post(url, params=payload)

        if resp.status_code == 200:
            print("Post successfully published!")
        else:
            print(resp.json())

    def create_media_container(self, image_info, user_id):
        """ Creates Instagram media container """

        # Setting image url and caption to payload
        payload = {'access_token': self.args.graph_api_access_token,
                   'image_url': image_info['image_url'],
                   'caption': "Car photo by " + image_info['author'] + "."}
        url = self.base_url + user_id + "/media"
        resp = requests.post(url, params=payload)

        if resp.status_code == 200:
            # Getting creation id as the response
            creation_id = resp.json()['id']
            # Calling publishing function
            self.publish_image_to_account(creation_id, user_id)
        else:
            print(resp.json())
            print("Creation of media container failed...")

    def set_up_info(self):
        """ Fetches information needed for API calls and post publishing """

        self.get_account_info()
        self.get_business_user_ids()


def main():
    """ Main entry point of the app """

    # Getting configuration file
    args = parse_config.get_configuration()
    # Initialize Instagram Graph API handler
    handler = GraphHandler(args)
    handler.set_up_info()

    supplier = ImageSupplier(args)
    image_info = supplier.get_random_image_from_collections("2102317,9254430")
    user_id = "17841450746190808"
    handler.create_media_container(image_info, user_id)


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()
