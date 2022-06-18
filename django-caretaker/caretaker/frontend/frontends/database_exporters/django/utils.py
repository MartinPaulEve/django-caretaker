from django.db.backends.base.client import BaseDatabaseClient


def delegate_settings_to_cmd_args(alternative_args: list | object,
                                  binary_name: str,
                                  settings_dict: dict,
                                  database_client: BaseDatabaseClient) \
        -> (list, dict):
    """
    Delegate commandline argument creation to a Django BaseDatabaseClient

    :param alternative_args: alternative arguments to pass instead
    :param binary_name: the binary name to use
    :param settings_dict: the settings dictionary
    :param database_client: the BaseDatabaseClient to use
    :return: 2-tuple of args and env
    """

    if not isinstance(alternative_args, list):
        alternative_args = [alternative_args] if alternative_args else []

    args, env = database_client.settings_to_cmd_args_env(settings_dict,
                                                         alternative_args)
    # patch the binary name
    args[0] = binary_name
    return args, env
