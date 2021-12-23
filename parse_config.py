import configargparse


def get_configuration():
    p = configargparse.ArgParser(
        default_config_files=['/etc/app/conf.d/*.conf', '~/.my_settings'])
    p.add('-c', '--my-config', required=True,
          is_config_file=True, help='config file path')
    p.add('--graph_api_access_token', required=True, help='Access Token')
    p.add('--graph_api_version', required=True,
          help='Version of the Instagram Graph API')
    p.add('--graph_api_base_path', required=True,
          help='Base path for Instagram Graph API')
    p.add('--unsplash_access_token', required=True,
          help='Access Key for Unsplash API')
    p.add('--unsplash_api_base_path', required=True,
          help='Base path for Unsplash API')
    p.add('--unsplash_api_version', required=True,
          help='Version of the Unsplash API')

    options = p.parse_args()

    return options
