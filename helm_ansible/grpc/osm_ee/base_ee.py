import asyncio
import logging
import yaml
import os

from osm_ee.vnf_ee import VnfEE
from dotenv import set_key


class BaseEE:

    RETURN_STATUS_LIST = ["OK", "PROCESSING", "ERROR"]
    CONFIG_FILE = "/app/storage/config.yaml"
    ENV_CONFIG_FILE = "/app/storage/config.env"
    SSH_KEY_FILE = "~/.ssh/id_rsa.pub"
    HEALTH_CHECK_ACTION = "health-check"

    def __init__(self):
        self.logger = logging.getLogger('base')

        # Check if configuration is stored and load it
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, 'r') as file:
                self.config_params = yaml.load(file, Loader=yaml.FullLoader)
                self.logger.debug("Load existing config from file: {}".format(self.config_params))
        else:
            self.config_params = {}

        self.vnf_ee = VnfEE(self.config_params)

    async def get_ssh_key(self):
        self.logger.debug("Obtain ssh key")
        filename = os.path.expanduser(self.SSH_KEY_FILE)
        with open(filename) as reader:
            ssh_key = reader.read()
        return ssh_key

    async def run_action(self, id, name, params):
        self.logger.debug("Execute action id: {}, name: {}, params: {}".format(id, name, params))

        try:
            # Health-check
            if name == self.HEALTH_CHECK_ACTION:
                yield "OK", "Health-check ok"
            else:

                # Obtain dynamically code to be executed
                method = getattr(self.vnf_ee, name)

                # Convert params from yaml format
                action_params = yaml.safe_load(params)

                if name == "config":
                    self.logger.debug("Store config info in file: {}".format(self.CONFIG_FILE))
                    self.config_params.update(action_params)
                    with open(self.CONFIG_FILE, 'w') as file:
                        config = yaml.dump(self.config_params, file)
                    with open(self.ENV_CONFIG_FILE, "w") as f:
                        for k, v in self.config_params.items():
                            k = k.replace("-","")
                            self.logger.debug(f"Writing")
                            f.write(f"{k}={v}\n")

                async for return_status, detailed_message in method(id, action_params):
                    if return_status not in self.RETURN_STATUS_LIST:
                        yield "ERROR", "Invalid return status"
                    else:
                        yield return_status, str(detailed_message)
        except AttributeError as e:
            error_msg = "Action name: {} not implemented".format(name)
            self.logger.error(error_msg)
            yield "ERROR", error_msg
        except Exception as e:
            self.logger.error("Error executing action id, name: {},{}: {}".format(id, name, str(e)), exc_info=True)
            yield "ERROR", str(e)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.get_event_loop()
    try:
        ee = BaseEE()
        id = "test1"
        name = "touch2"
        params = {"file_path": "/var/tmp/testfile1.txt"}
        action = asyncio.ensure_future(ee.run_action(id, name, params))
        loop.run_until_complete(action)
    finally:
        loop.close()
