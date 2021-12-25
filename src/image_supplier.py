import requests

""" Fetches images from application programming interfaces """


class ImageSupplier:

    def __init__(self, args):
        self.info = dict()
        self.args = args
        self.base_url = args.unsplash_api_base_path

    def get_random_image_from_collections(self, collections):
        """ Fetches random image from Unsplash API by given collection """

        image_info = dict()
        # Setting payload
        payload = {"collections": collections, 
                   "content_filter": "high"}
        # Setting headers (Authorization and version)
        headers = {"Authorization": "Client-ID " + self.args.unsplash_access_token,
                   "Accept-Version": self.args.unsplash_api_version}
        # Setting url to get random photo
        url = self.base_url + "photos/random"
        # Sending GET request
        resp = requests.get(url, params=payload, headers=headers)

        if resp.status_code == 200:
            resp_data = resp.json()
            # Constructing fitting image url with custom dimensions
            image_url = resp_data['urls']['raw'] + '&fit=crop&w=1080&h=1350'
            image_id = image_url.partition("photo-")[2].partition("?")[0]
            # Inserting needed information into dict.
            image_info.update(
                {'author': resp_data['user']['name'],
                 'image_url': image_url,
                 'image_id': image_id})
        else:
            print(resp)
        return image_info
